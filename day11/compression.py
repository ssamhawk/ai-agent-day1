"""
Compression module for Day 8 AI Application
Handles conversation compression and token management
"""
import logging
from threading import Lock
from typing import Dict, List, Any
from flask import session
from openai import OpenAI
from config import (
    OPENAI_MODEL,
    COMPRESSION_SYSTEM_PROMPT,
    encoding
)

# Global lock for session state synchronization (imported from app)
# Will be set by app.py after initialization
session_lock = None

# OpenAI client (will be set by app.py)
client = None

# Memory storage (will be set by app.py)
memory = None

# Module logger
logger = logging.getLogger(__name__)


def count_tokens(text: str) -> int:
    """Count tokens in text"""
    return len(encoding.encode(text))


def count_messages_tokens(messages: List[Dict[str, Any]]) -> int:
    """Count tokens for message list"""
    tokens = 0
    for message in messages:
        tokens += 4  # Message overhead
        tokens += count_tokens(message.get('content', ''))
    tokens += 2
    return tokens


def get_conversation_state() -> Dict[str, Any]:
    """
    Get conversation state from session

    Returns:
        dict: Conversation state with summaries and recent messages
    """
    if 'conversation_state' not in session:
        session['conversation_state'] = {
            'summaries': [],
            'recent_messages': [],
            'total_messages': 0,
            'stats': {
                'original_tokens': 0,
                'compressed_tokens': 0,
                'savings_percent': 0
            }
        }
    return session['conversation_state']


def compress_messages(messages: List[Dict[str, Any]], threshold: int) -> str:
    """
    Compress a batch of messages into a summary

    Args:
        messages (list): Messages to compress
        threshold (int): Number of messages to compress

    Returns:
        str: Summary of the messages
    """
    if not client:
        raise RuntimeError("OpenAI client not initialized! Call app.py first.")
    try:
        # Adaptive max_tokens based on number of messages - more aggressive
        num_messages = len(messages)
        if num_messages <= 4:
            max_tokens = 60  # Short: ultra-compact
        elif num_messages <= 10:
            max_tokens = 80  # Medium: very brief
        else:
            max_tokens = 100  # Long: still concise

        # Build conversation text
        conversation_text = "\n".join([
            f"{msg['role']}: {msg['content']}" for msg in messages
        ])

        compress_prompt = f"""Compress to essential facts only:

{conversation_text}

Output: Single compact sentence listing key topics/facts discussed."""

        messages_to_send = [
            {"role": "system", "content": COMPRESSION_SYSTEM_PROMPT},
            {"role": "user", "content": compress_prompt}
        ]

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages_to_send,
            temperature=0.3,  # Lower temperature for consistent summaries
            max_tokens=max_tokens
        )

        summary = response.choices[0].message.content
        logger.info(f"Compressed {len(messages)} messages into summary ({max_tokens} max tokens)")
        return summary

    except Exception as e:
        logger.error(f"Error compressing messages: {str(e)}")
        # Fallback: create simple summary
        return f"Discussion covering {len(messages)} messages about various topics."


def should_compress(state, threshold):
    """Check if compression should be triggered"""
    return len(state['recent_messages']) >= threshold


def perform_compression_internal(state, threshold, keep_recent):
    """
    Internal compression function WITHOUT lock (assumes lock is already held)

    Args:
        state (dict): Current conversation state
        threshold (int): Compression threshold
        keep_recent (int): Number of recent messages to keep
    """
    recent = state['recent_messages']

    if len(recent) < threshold:
        return  # Not enough messages to compress

    # Messages to compress
    to_compress = recent[:-keep_recent] if keep_recent > 0 else recent
    # Messages to keep
    to_keep = recent[-keep_recent:] if keep_recent > 0 else []

    if not to_compress:
        return

    # Calculate original tokens
    original_tokens = count_messages_tokens(to_compress)

    # Create summary
    summary = compress_messages(to_compress, threshold)
    summary_tokens = count_tokens(summary)

    # Update state
    state['summaries'].append(summary)
    state['recent_messages'] = to_keep

    # Update stats
    state['stats']['original_tokens'] += original_tokens
    state['stats']['compressed_tokens'] += summary_tokens

    # Calculate savings
    total_original = state['stats']['original_tokens']
    total_compressed = state['stats']['compressed_tokens']
    if total_original > 0:
        state['stats']['savings_percent'] = round(
            ((total_original - total_compressed) / total_original) * 100, 1
        )

    # Save summary to memory if available
    if memory:
        try:
            memory.save_summary(
                summary_text=summary,
                messages_compressed=len(to_compress),
                original_tokens=original_tokens,
                compressed_tokens=summary_tokens
            )
        except Exception as e:
            logger.error(f"Failed to save summary to memory: {e}")

    # Compress summaries if too many (recursive compression)
    MAX_SUMMARIES = 3
    if len(state['summaries']) > MAX_SUMMARIES:
        compress_summaries(state)

    session.modified = True
    logger.info(f"Compression: {original_tokens} → {summary_tokens} tokens ({state['stats']['savings_percent']}% savings)")


def compress_summaries(state):
    """
    Compress multiple summaries into one when there are too many

    Args:
        state (dict): Conversation state
    """
    try:
        # Join all summaries
        all_summaries = "\n\n".join([
            f"Summary {i+1}: {summary}"
            for i, summary in enumerate(state['summaries'])
        ])

        compress_prompt = f"""Merge these summaries into ONE ultra-compact summary:

{all_summaries}

Output: Single sentence with all critical facts."""

        messages_to_send = [
            {"role": "system", "content": COMPRESSION_SYSTEM_PROMPT},
            {"role": "user", "content": compress_prompt}
        ]

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages_to_send,
            temperature=0.3,
            max_tokens=60  # Very aggressive compression
        )

        combined_summary = response.choices[0].message.content

        # Calculate token changes
        old_tokens = sum(count_tokens(s) for s in state['summaries'])
        new_tokens = count_tokens(combined_summary)

        # Save count BEFORE modifying summaries array (issue #10 fix)
        old_summaries_count = len(state['summaries'])

        # Update stats - we're re-compressing, so adjust the compressed tokens
        state['stats']['compressed_tokens'] = state['stats']['compressed_tokens'] - old_tokens + new_tokens

        # Replace all summaries with the combined one
        state['summaries'] = [combined_summary]

        logger.info(f"Compressed {old_summaries_count} summaries into 1: {old_tokens} → {new_tokens} tokens")

    except Exception as e:
        logger.error(f"Error compressing summaries: {str(e)}")


def perform_compression_internal(state, threshold, keep_recent):
    """
    Perform compression WITHOUT acquiring lock (assumes lock is already held)

    Args:
        state (dict): Current conversation state
        threshold (int): Compression threshold
        keep_recent (int): Number of recent messages to keep
    """
    recent = state['recent_messages']

    if len(recent) < threshold:
        return  # Not enough messages to compress

    # Messages to compress
    to_compress = recent[:-keep_recent] if keep_recent > 0 else recent
    # Messages to keep
    to_keep = recent[-keep_recent:] if keep_recent > 0 else []

    if not to_compress:
        return

    # Calculate original tokens
    original_tokens = count_messages_tokens(to_compress)

    # Create summary
    summary = compress_messages(to_compress, threshold)
    summary_tokens = count_tokens(summary)

    # Save count BEFORE modifying summaries array (issue #10 fix)
    old_summaries_count = len(state['summaries'])

    # Update state
    state['summaries'].append(summary)
    state['recent_messages'] = to_keep

    # Update stats
    state['stats']['original_tokens'] += original_tokens
    state['stats']['compressed_tokens'] += summary_tokens

    # Calculate savings
    total_original = state['stats']['original_tokens']
    total_compressed = state['stats']['compressed_tokens']
    if total_original > 0:
        state['stats']['savings_percent'] = round(
            ((total_original - total_compressed) / total_original) * 100, 1
        )

    # Compress summaries if too many (recursive compression)
    MAX_SUMMARIES = 3
    if len(state['summaries']) > MAX_SUMMARIES:
        compress_summaries(state)

    session.modified = True
    logger.info(f"Compression: {original_tokens} → {summary_tokens} tokens ({state['stats']['savings_percent']}% savings)")


def perform_compression(state, threshold, keep_recent):
    """
    Perform compression on conversation state with thread safety

    Args:
        state (dict): Current conversation state
        threshold (int): Compression threshold
        keep_recent (int): Number of recent messages to keep
    """
    if not session_lock:
        raise RuntimeError("session_lock not initialized! Call app.py first.")

    with session_lock:
        perform_compression_internal(state, threshold, keep_recent)


def build_context(state):
    """
    Build conversation context from compressed state

    Args:
        state (dict): Conversation state

    Returns:
        list: Messages for API (summaries + recent messages)
    """
    messages = []

    # Add summaries as system messages
    if state['summaries']:
        summaries_text = "\n\n".join([
            f"Previous conversation summary {i+1}:\n{summary}"
            for i, summary in enumerate(state['summaries'])
        ])
        messages.append({
            "role": "system",
            "content": f"Context from previous conversation:\n\n{summaries_text}"
        })

    # Add recent messages
    messages.extend(state['recent_messages'])

    return messages


def add_message_to_conversation(role, content, compression_enabled, threshold, keep_recent):
    """
    Add message to conversation with optional compression (thread-safe)

    Args:
        role (str): Message role
        content (str): Message content
        compression_enabled (bool): Whether compression is enabled
        threshold (int): Compression threshold
        keep_recent (int): Number of recent messages to keep
    """
    if not session_lock:
        raise RuntimeError("session_lock not initialized! Call app.py first.")

    with session_lock:
        state = get_conversation_state()

        # Add message to recent
        state['recent_messages'].append({
            "role": role,
            "content": content
        })
        state['total_messages'] += 1

        session['conversation_state'] = state
        session.modified = True

        # Check if compression needed - only compress after assistant messages
        # Perform compression INSIDE the lock to prevent race conditions
        if compression_enabled and role == "assistant" and should_compress(state, threshold):
            perform_compression_internal(state, threshold, keep_recent)
