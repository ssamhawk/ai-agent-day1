"""
Citation Manager - Enforces and validates source citations in RAG responses
Ensures LLM provides proper citations to source documents
"""
import logging
import re
from typing import List, Dict, Set

logger = logging.getLogger(__name__)


class CitationManager:
    """
    Manages citation formatting and validation for RAG responses

    Ensures that:
    1. Context includes numbered citations [1], [2], etc.
    2. LLM uses these citations in responses
    3. All sources are properly referenced
    """

    def __init__(self):
        """Initialize citation manager"""
        pass

    def build_context_with_citations(
        self,
        chunks: List[Dict],
        include_rerank: bool = False
    ) -> tuple:
        """
        Build context string with citation markers

        Args:
            chunks: List of retrieved document chunks
            include_rerank: Whether chunks have rerank scores

        Returns:
            Tuple of (context_string, citation_map, source_files)

        Example output:
            "[1] docker_basics.md\nTo stop a container, use docker stop...\n\n"
            "[2] kubernetes_intro.md\nPods are the smallest deployable...\n\n"
        """
        context_parts = []
        citation_map = {}  # {citation_number: chunk_metadata}
        source_files = set()

        for i, chunk in enumerate(chunks, 1):
            text = chunk.get('text', '')
            source_file = chunk.get('source_file', 'unknown')
            chunk_index = chunk.get('chunk_index', 0)
            chunk_id = chunk.get('chunk_id', f'chunk_{i}')
            similarity = chunk.get('similarity', 0.0)

            source_files.add(source_file)

            # Build citation entry
            if include_rerank and 'rerank_score' in chunk:
                rerank_score = chunk['rerank_score']
                rank_change = chunk.get('rank_change', 0)

                context_parts.append(
                    f"[{i}] Source: {source_file} (chunk {chunk_index})\n"
                    f"Relevance: similarity={similarity:.2%}, rerank={rerank_score:.3f}, "
                    f"rank_change={rank_change:+d}\n"
                    f"{text}\n"
                )
            else:
                context_parts.append(
                    f"[{i}] Source: {source_file} (chunk {chunk_index})\n"
                    f"Relevance: {similarity:.2%}\n"
                    f"{text}\n"
                )

            # Store citation metadata
            citation_map[i] = {
                'citation_number': i,
                'source_file': source_file,
                'chunk_id': chunk_id,
                'chunk_index': chunk_index,
                'similarity': similarity,
                'text_preview': text[:100] + '...' if len(text) > 100 else text,
                'rerank_score': chunk.get('rerank_score'),
                'rank_change': chunk.get('rank_change', 0)
            }

        context_string = "\n".join(context_parts)

        logger.info(f"Built context with {len(chunks)} citations from {len(source_files)} files")

        return context_string, citation_map, list(source_files)

    def create_citation_prompt(
        self,
        question: str,
        context: str,
        num_sources: int
    ) -> str:
        """
        Create prompt that enforces citation usage

        Args:
            question: User's question
            context: Context with numbered citations
            num_sources: Number of source documents

        Returns:
            Prompt string that requires citations
        """
        prompt = f"""You are a helpful assistant that answers questions based on provided context.

IMPORTANT RULES:
1. You MUST cite your sources using the citation numbers provided: [1], [2], [3], etc.
2. Every factual claim should include a citation to the source where you found that information
3. Use inline citations like: "Docker containers can be stopped with docker stop [1]"
4. If information comes from multiple sources, cite all of them: [1][2]
5. Do NOT make up information not found in the provided context
6. If you cannot answer based on the context, say so clearly

Context with {num_sources} sources:

{context}

Question: {question}

Answer (remember to cite sources using [1], [2], etc.):"""

        return prompt

    def validate_citations(
        self,
        response_text: str,
        num_sources: int,
        strict: bool = False
    ) -> Dict:
        """
        Validate that response includes proper citations

        Args:
            response_text: LLM's response
            num_sources: Number of sources provided
            strict: If True, require ALL sources to be cited

        Returns:
            Validation result dictionary
        """
        # Extract all citation numbers from response
        citation_pattern = r'\[(\d+)\]'
        found_citations = set(re.findall(citation_pattern, response_text))
        found_citations = {int(c) for c in found_citations}

        expected_citations = set(range(1, num_sources + 1))

        # Check coverage
        cited = found_citations & expected_citations
        missing = expected_citations - found_citations
        invalid = found_citations - expected_citations

        has_citations = len(cited) > 0
        all_cited = len(missing) == 0
        no_invalid = len(invalid) == 0

        # Calculate citation rate
        citation_rate = len(cited) / num_sources if num_sources > 0 else 0.0

        # Determine if valid
        if strict:
            is_valid = all_cited and no_invalid
        else:
            is_valid = has_citations and no_invalid

        result = {
            'is_valid': is_valid,
            'has_citations': has_citations,
            'all_cited': all_cited,
            'no_invalid': no_invalid,
            'citation_rate': citation_rate,
            'num_sources': num_sources,
            'num_cited': len(cited),
            'num_missing': len(missing),
            'num_invalid': len(invalid),
            'cited': sorted(list(cited)),
            'missing': sorted(list(missing)),
            'invalid': sorted(list(invalid))
        }

        if not has_citations:
            logger.warning("Response has NO citations!")
        elif not all_cited:
            logger.info(f"Response cited {len(cited)}/{num_sources} sources (missing: {missing})")
        else:
            logger.info(f"✅ All {num_sources} sources cited")

        if invalid:
            logger.warning(f"Invalid citation numbers found: {invalid}")

        return result

    def format_sources_section(
        self,
        citation_map: Dict[int, Dict]
    ) -> str:
        """
        Format sources section for display

        Args:
            citation_map: Map of citation numbers to metadata

        Returns:
            Formatted sources section string
        """
        if not citation_map:
            return ""

        lines = ["\n" + "="*60]
        lines.append("📚 SOURCES")
        lines.append("="*60 + "\n")

        for num in sorted(citation_map.keys()):
            meta = citation_map[num]
            source = meta['source_file']
            chunk_idx = meta['chunk_index']
            similarity = meta['similarity']
            preview = meta['text_preview']

            lines.append(f"[{num}] {source} (chunk {chunk_idx})")
            lines.append(f"    Relevance: {similarity:.2%}")

            if meta.get('rerank_score') is not None:
                rerank = meta['rerank_score']
                change = meta['rank_change']
                change_icon = "⬆️" if change > 0 else ("⬇️" if change < 0 else "➡️")
                lines.append(f"    Rerank: {rerank:.3f} {change_icon} ({change:+d})")

            lines.append(f'    Preview: "{preview}"')
            lines.append("")

        return "\n".join(lines)


# Singleton instance
_citation_manager = None


def get_citation_manager() -> CitationManager:
    """Get or create citation manager singleton"""
    global _citation_manager

    if _citation_manager is None:
        _citation_manager = CitationManager()

    return _citation_manager
