import re
from typing import List


def normalize_text(text: str) -> str:
    """Normalize whitespace and control characters."""
    if text is None:
        return ""
    # collapse whitespace
    t = re.sub(r"\s+", " ", text)
    return t.strip()


class TextChunker:
    """
    Splits Vietnamese text into chunks respecting paragraphs, sentences, and word boundaries.
    
    Splitting priority:
    1. Paragraph boundaries
    2. Sentence boundaries (., !, ?, …)
    3. Word boundaries (spaces)
    4. Hard break if necessary (fallback)
    """
    
    # Vietnamese sentence-ending punctuation
    SENTENCE_ENDINGS = r'[.!?…]+'
    # Vietnamese phrase separators
    PHRASE_SEPARATORS = r'[,;:]'
    
    def __init__(self, max_chars: int = 500):
        """
        Args:
            max_chars: Maximum characters per chunk (default 500 for OmniVoice)
        """
        self.max_chars = max_chars
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks respecting structure.
        
        Args:
            text: Input text (Vietnamese or general)
            
        Returns:
            List of non-empty chunks, each <= max_chars
        """
        if not text:
            return []
        
        # Normalize whitespace
        text = normalize_text(text)
        
        # After normalization, check again if empty
        if not text:
            return []
        
        if len(text) <= self.max_chars:
            return [text]
        
        # Try to split by paragraphs first
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
        
        if len(paragraphs) > 1:
            return self._chunk_multiple_paragraphs(paragraphs)
        
        # Single paragraph: split by sentences
        return self._chunk_by_sentences(text)
    
    def _chunk_multiple_paragraphs(self, paragraphs: List[str]) -> List[str]:
        """Chunk multiple paragraphs while respecting paragraph boundaries."""
        result = []
        current_chunk = []
        current_len = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            para_len = len(para)
            
            # If paragraph itself is small, try to group with current chunk
            if current_len + para_len + 2 <= self.max_chars:  # +2 for space/newline
                if current_chunk:
                    current_chunk.append(para)
                    current_len += para_len + 1
                else:
                    current_chunk = [para]
                    current_len = para_len
            else:
                # Paragraph doesn't fit: flush current, then handle new paragraph
                if current_chunk:
                    result.append(' '.join(current_chunk))
                    current_chunk = []
                    current_len = 0
                
                # If paragraph itself is too long, chunk it
                if para_len > self.max_chars:
                    para_chunks = self._chunk_by_sentences(para)
                    result.extend(para_chunks)
                else:
                    current_chunk = [para]
                    current_len = para_len
        
        if current_chunk:
            result.append(' '.join(current_chunk))
        
        # Filter out any empty chunks
        return [chunk for chunk in result if chunk and chunk.strip()]
    
    def _chunk_by_sentences(self, text: str) -> List[str]:
        """Chunk text by sentence boundaries."""
        # Split by sentence endings, keeping the punctuation
        sentences = re.split(r'(?<=[.!?…])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return self._chunk_by_words(text)
        
        result = []
        current_chunk = []
        current_len = 0
        
        for sentence in sentences:
            sent_len = len(sentence)
            
            # If sentence fits in current chunk
            if current_len + sent_len + (1 if current_chunk else 0) <= self.max_chars:
                current_chunk.append(sentence)
                current_len += sent_len + (1 if len(current_chunk) > 1 else 0)
            else:
                # Flush current chunk
                if current_chunk:
                    result.append(' '.join(current_chunk))
                    current_chunk = []
                    current_len = 0
                
                # If sentence itself is too long, chunk it by words
                if sent_len > self.max_chars:
                    sentence_chunks = self._chunk_by_words(sentence)
                    result.extend(sentence_chunks)
                else:
                    current_chunk = [sentence]
                    current_len = sent_len
        
        if current_chunk:
            result.append(' '.join(current_chunk))
        
        # Filter out any empty chunks
        return [chunk for chunk in result if chunk and chunk.strip()]
    
    def _chunk_by_words(self, text: str) -> List[str]:
        """Chunk text by word boundaries (fallback)."""
        words = text.split(' ')
        
        if not words:
            return []
        
        result = []
        current = []
        current_len = 0
        
        for word in words:
            if not word:  # Skip empty strings from multiple spaces
                continue
            
            word_len = len(word)
            sep_len = 1 if current else 0
            
            if current_len + word_len + sep_len <= self.max_chars:
                current.append(word)
                current_len += word_len + sep_len
            else:
                if current:
                    result.append(' '.join(current))
                    current = []
                    current_len = 0
                
                # If single word is too long, hard break it
                if word_len > self.max_chars:
                    # Split long word into chunks
                    for i in range(0, word_len, self.max_chars):
                        result.append(word[i:i + self.max_chars])
                else:
                    current = [word]
                    current_len = word_len
        
        if current:
            result.append(' '.join(current))
        
        # Filter out any empty chunks
        return [chunk for chunk in result if chunk and chunk.strip()]


def chunk_text(text: str, max_chars: int = 500) -> List[str]:
    """
    Convenience function to chunk text with default settings.
    
    For more control, use TextChunker class directly.
    
    Args:
        text: Input text
        max_chars: Maximum characters per chunk
        
    Returns:
        List of chunks
    """
    chunker = TextChunker(max_chars=max_chars)
    return chunker.chunk_text(text)
