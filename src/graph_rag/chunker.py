"""
Text Chunking Module
Splits text into sentence-based chunks respecting maximum word count
"""

import re
from typing import List
import logging

logger = logging.getLogger(__name__)


def chunk_text(text: str, max_length: int = 512) -> List[str]:
    """
    Split text into chunks by sentences, respecting max word count.

    Pattern adapted from graph_rag.py lines 40-53.

    Args:
        text: Input text to chunk
        max_length: Maximum number of words per chunk (default: 512)

    Returns:
        List of text chunks, each containing <= max_length words

    Example:
        >>> text = "First sentence. Second sentence. Third sentence."
        >>> chunks = chunk_text(text, max_length=10)
        >>> len(chunks) >= 1
        True
    """
    if not text or not text.strip():
        logger.warning("Empty text provided to chunk_text")
        return []

    # Split on sentence boundaries: periods, exclamation marks, question marks
    # followed by whitespace
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    chunks: List[str] = []
    current_chunk: List[str] = []
    current_length: int = 0

    for sentence in sentences:
        if not sentence.strip():
            continue

        sentence_word_count = len(sentence.split())

        # If adding this sentence would exceed max_length, save current chunk
        if current_length + sentence_word_count > max_length and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_length = sentence_word_count
        else:
            current_chunk.append(sentence)
            current_length += sentence_word_count

    # Don't forget the last chunk
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    logger.info(f"Chunked text into {len(chunks)} chunks (max_length={max_length} words)")
    return chunks
