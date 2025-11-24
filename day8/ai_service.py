"""
AI Service module for Day 8 AI Application
Handles AI response generation and MCP command processing
"""
import re
import logging
from typing import Dict, Any, Tuple
from openai import OpenAI
from mcp_client import mcp_client
from config import (
    OPENAI_MODEL,
    OPENAI_TEMPERATURE,
    OPENAI_MAX_TOKENS,
    MODEL_CONTEXT_LIMIT,
    DEFAULT_COMPRESSION_THRESHOLD,
    DEFAULT_RECENT_KEEP,
    RESPONSE_PROMPTS
)
from compression import (
    count_tokens,
    count_messages_tokens,
    get_conversation_state,
    build_context,
    add_message_to_conversation
)

# OpenAI client (will be set by app.py)
client = None

# Module logger
logger = logging.getLogger(__name__)


def generate_dynamic_prompt(response_format, fields=None, intelligent_mode=False):
    """Generate system prompt based on format and mode"""
    if response_format == "plain" and intelligent_mode:
        return RESPONSE_PROMPTS.get("plain_intelligent", RESPONSE_PROMPTS["plain"])

    return RESPONSE_PROMPTS.get(response_format, RESPONSE_PROMPTS["plain"])


def process_mcp_commands(text, intelligent_mode=False):
    """
    Process MCP commands in AI response (search, list files, read files)

    Args:
        text (str): AI response text
        intelligent_mode (bool): Whether intelligent mode is enabled

    Returns:
        tuple: (processed_text, used_mcp_flag)
    """
    if not intelligent_mode:
        return text, False

    used_mcp = False

    # Process MCP_SEARCH commands
    search_pattern = r'\[MCP_SEARCH:\s*([^\]]+)\]'
    search_matches = re.findall(search_pattern, text)

    if search_matches:
        used_mcp = True
        logger.info(f"Found {len(search_matches)} MCP search commands")

        for query in search_matches:
            query = query.strip()
            logger.info(f"Executing MCP search: {query}")

            try:
                result = mcp_client.call_tool(
                    server_name="brave_search",
                    tool_name="search",
                    arguments={"query": query, "max_results": 5}
                )

                if result.get("success"):
                    search_results = result.get("result", {}).get("content", "")
                    replacement = f"\n\n🔍 **Web Search Results for '{query}':**\n\n{search_results}\n"
                    text = text.replace(f"[MCP_SEARCH: {query}]", replacement)
                else:
                    error_msg = result.get("error", "Unknown error")
                    replacement = f"\n\n⚠️ Search failed for '{query}': {error_msg}\n"
                    text = text.replace(f"[MCP_SEARCH: {query}]", replacement)

            except Exception as e:
                logger.error(f"Error executing MCP search: {str(e)}")
                replacement = f"\n\n❌ Error searching for '{query}': {str(e)}\n"
                text = text.replace(f"[MCP_SEARCH: {query}]", replacement)

    # Process MCP_LIST_FILES commands
    list_pattern = r'\[MCP_LIST_FILES:\s*([^\]]+)\]'
    list_matches = re.findall(list_pattern, text)

    if list_matches:
        used_mcp = True
        logger.info(f"Found {len(list_matches)} MCP list_files commands")

        for path in list_matches:
            path = path.strip()
            logger.info(f"Executing MCP list_files: {path}")

            try:
                result = mcp_client.call_tool(
                    server_name="filesystem",
                    tool_name="list_files",
                    arguments={"path": path}
                )

                if result.get("success"):
                    file_list = result.get("result", {}).get("content", "")
                    replacement = f"\n\n📁 **Files in '{path}':**\n\n{file_list}\n"
                    text = text.replace(f"[MCP_LIST_FILES: {path}]", replacement)
                else:
                    error_msg = result.get("error", "Unknown error")
                    replacement = f"\n\n⚠️ Failed to list files in '{path}': {error_msg}\n"
                    text = text.replace(f"[MCP_LIST_FILES: {path}]", replacement)

            except Exception as e:
                logger.error(f"Error executing MCP list_files: {str(e)}")
                replacement = f"\n\n❌ Error listing files in '{path}': {str(e)}\n"
                text = text.replace(f"[MCP_LIST_FILES: {path}]", replacement)

    # Process MCP_READ_FILE commands
    read_pattern = r'\[MCP_READ_FILE:\s*([^\]]+)\]'
    read_matches = re.findall(read_pattern, text)

    if read_matches:
        used_mcp = True
        logger.info(f"Found {len(read_matches)} MCP read_file commands")

        for path in read_matches:
            path = path.strip()
            logger.info(f"Executing MCP read_file: {path}")

            try:
                result = mcp_client.call_tool(
                    server_name="filesystem",
                    tool_name="read_file",
                    arguments={"path": path}
                )

                if result.get("success"):
                    file_content = result.get("result", {}).get("content", "")
                    replacement = f"\n\n📄 **Content of '{path}':**\n\n{file_content}\n"
                    text = text.replace(f"[MCP_READ_FILE: {path}]", replacement)
                else:
                    error_msg = result.get("error", "Unknown error")
                    replacement = f"\n\n⚠️ Failed to read file '{path}': {error_msg}\n"
                    text = text.replace(f"[MCP_READ_FILE: {path}]", replacement)

            except Exception as e:
                logger.error(f"Error executing MCP read_file: {str(e)}")
                replacement = f"\n\n❌ Error reading file '{path}': {str(e)}\n"
                text = text.replace(f"[MCP_READ_FILE: {path}]", replacement)

    return text, used_mcp


def get_ai_response(user_message, response_format="plain", fields=None, temperature=OPENAI_TEMPERATURE,
                   intelligent_mode=False, max_tokens=OPENAI_MAX_TOKENS, compression_enabled=True,
                   threshold=DEFAULT_COMPRESSION_THRESHOLD, keep_recent=DEFAULT_RECENT_KEEP):
    """
    Get AI response with compression support and MCP integration

    Args:
        user_message (str): User's message
        response_format (str): Response format
        fields (list): Fields configuration
        temperature (float): Temperature
        intelligent_mode (bool): Intelligent mode (enables MCP search)
        max_tokens (int): Max tokens
        compression_enabled (bool): Enable compression
        threshold (int): Compression threshold
        keep_recent (int): Recent messages to keep

    Returns:
        dict: Response with compression stats and MCP usage info
    """
    try:
        # Get system prompt
        system_prompt = generate_dynamic_prompt(response_format, fields, intelligent_mode)

        # Get conversation state
        state = get_conversation_state()

        # Build context from compressed history
        context_messages = build_context(state)

        # Build full message list
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(context_messages)
        messages.append({"role": "user", "content": user_message})

        # Count tokens
        input_tokens = count_messages_tokens(messages)

        # Check context limit
        if input_tokens + max_tokens > MODEL_CONTEXT_LIMIT:
            available = MODEL_CONTEXT_LIMIT - input_tokens
            if available <= 0:
                raise Exception(f"Context too long ({input_tokens} tokens)")
            max_tokens = min(max_tokens, available)

        # Get initial response
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )

        ai_response = response.choices[0].message.content

        # Process MCP commands if in intelligent mode
        ai_response, used_mcp = process_mcp_commands(ai_response, intelligent_mode)

        # If MCP was used, do a second pass to let AI synthesize the search results
        if used_mcp:
            logger.info("MCP search completed, getting final AI synthesis...")

            # Add the search results to context and ask AI to synthesize
            messages.append({"role": "assistant", "content": ai_response})
            messages.append({"role": "user", "content": "Based on the search results above, please provide a comprehensive answer to my original question."})

            # Get final synthesized response
            final_response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            ai_response = final_response.choices[0].message.content

        # Add messages to conversation
        add_message_to_conversation("user", user_message, compression_enabled, threshold, keep_recent)
        add_message_to_conversation("assistant", ai_response, compression_enabled, threshold, keep_recent)

        # Get token usage
        output_tokens = response.usage.completion_tokens
        actual_input_tokens = response.usage.prompt_tokens
        total_tokens = response.usage.total_tokens

        # Get updated stats
        updated_state = get_conversation_state()

        # Calculate what input tokens would be without compression (for this specific request)
        # If we have summaries, calculate what the original messages would have been
        summaries_tokens = sum(count_tokens(s) for s in updated_state['summaries'])
        recent_tokens = count_messages_tokens(updated_state['recent_messages'])

        # Calculate tokens saved in this request
        tokens_saved_this_request = 0
        if compression_enabled and len(updated_state['summaries']) > 0:
            # What we're using: summaries + recent
            compressed_context = summaries_tokens + recent_tokens
            # What it would be: original compressed messages + recent
            uncompressed_context = updated_state['stats']['original_tokens'] + recent_tokens
            tokens_saved_this_request = uncompressed_context - compressed_context

        return {
            'response': ai_response,
            'tokens': {
                'input': actual_input_tokens,
                'output': output_tokens,
                'total': total_tokens,
                'max_output': max_tokens,
                'limit': MODEL_CONTEXT_LIMIT,
                'percentage': round((total_tokens / MODEL_CONTEXT_LIMIT) * 100, 2),
                'saved_this_request': tokens_saved_this_request  # New field
            },
            'compression_stats': {
                'enabled': compression_enabled,
                'total_messages': updated_state['total_messages'],
                'summaries_count': len(updated_state['summaries']),
                'recent_messages_count': len(updated_state['recent_messages']),
                'original_tokens': updated_state['stats']['original_tokens'],
                'compressed_tokens': updated_state['stats']['compressed_tokens'],
                'savings_percent': updated_state['stats']['savings_percent']
            },
            'truncated': response.choices[0].finish_reason == 'length'
        }

    except Exception as e:
        logger.error(f"Error in get_ai_response: {str(e)}", exc_info=True)
        raise
