import pytest
from app.services.text_service import normalize_text, chunk_text, TextChunker


# ============================================================================
# normalize_text tests
# ============================================================================

def test_normalize_text():
    assert normalize_text("  foo\nbar \t baz  ") == "foo bar baz"


def test_normalize_text_empty():
    assert normalize_text("") == ""


def test_normalize_text_none():
    assert normalize_text(None) == ""


def test_normalize_text_multiple_newlines():
    assert normalize_text("line1\n\n\nline2") == "line1 line2"


# ============================================================================
# chunk_text convenience function tests
# ============================================================================

def test_chunk_text_short():
    """Text shorter than max_chars should return as single chunk."""
    assert chunk_text("short text", max_chars=50) == ["short text"]


def test_chunk_text_long():
    """Long text should be chunked."""
    text = "word " * 60
    chunks = chunk_text(text, max_chars=50)
    assert all(len(c) <= 50 for c in chunks)
    assert len(chunks) > 1


def test_chunk_text_empty():
    """Empty text should return empty list."""
    assert chunk_text("") == []


def test_chunk_text_whitespace_only():
    """Whitespace-only text should return empty list."""
    assert chunk_text("   \n\t   ") == []


# ============================================================================
# TextChunker class tests
# ============================================================================

class TestTextChunkerBasic:
    """Test basic chunking behavior."""
    
    def test_init_default(self):
        """Default max_chars should be 500."""
        chunker = TextChunker()
        assert chunker.max_chars == 500
    
    def test_init_custom(self):
        """Should accept custom max_chars."""
        chunker = TextChunker(max_chars=300)
        assert chunker.max_chars == 300
    
    def test_empty_text(self):
        """Empty text should return empty list."""
        chunker = TextChunker()
        assert chunker.chunk_text("") == []
    
    def test_none_text(self):
        """None text should be handled gracefully."""
        chunker = TextChunker()
        # normalize_text will convert None to empty string
        result = chunker.chunk_text(normalize_text(None))
        assert result == []
    
    def test_whitespace_only(self):
        """Whitespace-only text should return empty list."""
        chunker = TextChunker()
        assert chunker.chunk_text("   \n\t   ") == []
    
    def test_single_short_sentence(self):
        """Short text should return as single chunk."""
        chunker = TextChunker(max_chars=500)
        text = "This is a short sentence."
        result = chunker.chunk_text(text)
        assert result == ["This is a short sentence."]


class TestTextChunkerSentences:
    """Test sentence-aware chunking."""
    
    def test_multiple_sentences_fit_in_chunk(self):
        """Multiple sentences that fit should stay together."""
        chunker = TextChunker(max_chars=200)
        text = "First sentence. Second sentence. Third sentence."
        result = chunker.chunk_text(text)
        assert len(result) == 1
        assert "First sentence" in result[0]
        assert "Third sentence" in result[0]
    
    def test_multiple_sentences_dont_fit(self):
        """Sentences that exceed max_chars should be split."""
        text = "First sentence. " * 20  # Create many repetitions
        chunker = TextChunker(max_chars=100)
        result = chunker.chunk_text(text)
        assert len(result) > 1
        assert all(len(chunk) <= 100 for chunk in result)
    
    def test_exclamation_mark(self):
        """Should respect exclamation marks as sentence endings."""
        chunker = TextChunker(max_chars=500)
        text = "What a day! This is great!"
        result = chunker.chunk_text(text)
        # Should be treated as 2 sentences but fit in one chunk
        assert len(result) == 1
    
    def test_question_mark(self):
        """Should respect question marks as sentence endings."""
        chunker = TextChunker(max_chars=500)
        text = "How are you? I am fine."
        result = chunker.chunk_text(text)
        assert len(result) == 1
    
    def test_ellipsis(self):
        """Should respect ellipsis (…) as sentence ending."""
        chunker = TextChunker(max_chars=500)
        text = "Wait a minute… Something is wrong."
        result = chunker.chunk_text(text)
        assert len(result) >= 1


class TestTextChunkerParagraphs:
    """Test paragraph-aware chunking."""
    
    def test_multiple_paragraphs_short(self):
        """Short paragraphs that fit should stay grouped."""
        chunker = TextChunker(max_chars=300)
        text = "Paragraph one.\nParagraph two.\nParagraph three."
        result = chunker.chunk_text(text)
        # Should be combined into one or two chunks
        assert len(result) >= 1
        assert all(len(chunk) <= 300 for chunk in result)
    
    def test_multiple_paragraphs_long(self):
        """Long paragraphs should be chunked separately."""
        para1 = "First paragraph. " * 10
        para2 = "Second paragraph. " * 10
        text = para1 + "\n" + para2
        chunker = TextChunker(max_chars=100)
        result = chunker.chunk_text(text)
        assert len(result) > 2


class TestTextChunkerVietnamese:
    """Test Vietnamese-specific cases."""
    
    def test_vietnamese_unicode(self):
        """Should handle Vietnamese Unicode correctly."""
        text = "Xin chào. Đây là tiếng Việt. Thế nào?"
        chunker = TextChunker(max_chars=500)
        result = chunker.chunk_text(text)
        assert len(result) >= 1
        assert "Xin chào" in result[0]
    
    def test_vietnamese_long_text(self):
        """Should chunk Vietnamese text intelligently."""
        text = """Ngày hôm đó trời mưa rất lớn. Tôi đứng trước cửa và chờ anh.
Khoảng mười phút sau, anh mới xuất hiện. Chúng tôi bước ra ngoài cùng nhau.
Mưa vẫn rơi ào ào, nhưng tôi cảm thấy ấm áp vì có anh bên cạnh."""
        chunker = TextChunker(max_chars=150)
        result = chunker.chunk_text(text)
        assert len(result) >= 2
        assert all(len(chunk) <= 150 for chunk in result)
        assert all(chunk.strip() for chunk in result)  # No empty chunks
    
    def test_vietnamese_dialogue(self):
        """Should handle dialogue properly."""
        text = "\"Bạn khỏe không?\" anh hỏi. \"Tôi khỏe, cảm ơn bạn.\" tôi trả lời."
        chunker = TextChunker(max_chars=500)
        result = chunker.chunk_text(text)
        assert len(result) >= 1
        assert "Bạn khỏe không?" in result[0]


class TestTextChunkerLongContent:
    """Test handling of very long or problematic content."""
    
    def test_single_long_word(self):
        """Single word longer than max_chars should be hard-broken."""
        chunker = TextChunker(max_chars=10)
        text = "supercalifragilisticexpialidocious"
        result = chunker.chunk_text(text)
        assert len(result) >= 2
        assert all(len(chunk) <= 10 for chunk in result)
        # Concatenated result should equal original
        assert ''.join(result) == text
    
    def test_long_sentence(self):
        """Long sentence should be chunked by words."""
        chunker = TextChunker(max_chars=50)
        text = "The quick brown fox jumps over the lazy dog. " * 3
        result = chunker.chunk_text(text)
        assert all(len(chunk) <= 50 for chunk in result)
    
    def test_mixed_long_short(self):
        """Mixed content with long and short sentences."""
        text = "Short. " + "This is a much longer sentence that goes on and on. " * 5
        chunker = TextChunker(max_chars=100)
        result = chunker.chunk_text(text)
        assert all(len(chunk) <= 100 for chunk in result)
        assert all(chunk.strip() for chunk in result)


class TestTextChunkerEdgeCases:
    """Test edge cases and special characters."""
    
    def test_multiple_spaces(self):
        """Multiple consecutive spaces should be normalized."""
        chunker = TextChunker()
        text = "Word1    word2    word3"
        result = chunker.chunk_text(text)
        assert "    " not in result[0]  # Should be normalized
    
    def test_tabs_and_newlines(self):
        """Tabs and newlines should be normalized."""
        chunker = TextChunker()
        text = "Line1\t\tLine2\nLine3"
        result = chunker.chunk_text(text)
        assert "\t" not in result[0]
    
    def test_special_characters(self):
        """Should preserve special characters."""
        text = "Email: user@example.com. Price: $100 & 50%."
        chunker = TextChunker()
        result = chunker.chunk_text(text)
        assert "@" in result[0]
        assert "$" in result[0]
        assert "%" in result[0]
    
    def test_punctuation_without_space(self):
        """Punctuation without space after should be handled."""
        text = "Hello.World.Test"
        chunker = TextChunker(max_chars=500)
        result = chunker.chunk_text(text)
        assert len(result) >= 1


class TestTextChunkerContentPreservation:
    """Test that content is preserved correctly."""
    
    def test_no_text_loss(self):
        """All content should be preserved in chunks."""
        text = "The quick brown fox jumps over the lazy dog. " * 10
        chunker = TextChunker(max_chars=100)
        result = chunker.chunk_text(text)
        
        # Rejoin and normalize for comparison
        rejoin = ' '.join(result)
        assert rejoin.replace('  ', ' ').strip() == text.replace('  ', ' ').strip()
    
    def test_no_duplicate_content(self):
        """No content should be duplicated in chunks."""
        text = "Word " * 50
        chunker = TextChunker(max_chars=50)
        result = chunker.chunk_text(text)
        
        # Count occurrences of "Word" should match original
        original_count = text.count("Word")
        result_count = ' '.join(result).count("Word")
        assert result_count == original_count
    
    def test_chunk_order_preserved(self):
        """Chunks should maintain original order."""
        text = "First. Second. Third. Fourth. Fifth."
        chunker = TextChunker(max_chars=50)
        result = chunker.chunk_text(text)
        
        joined = ' '.join(result)
        assert joined.index("First") < joined.index("Second")
        assert joined.index("Second") < joined.index("Third")
    
    def test_no_empty_chunks(self):
        """No chunk should be empty or whitespace-only."""
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        chunker = TextChunker(max_chars=100)
        result = chunker.chunk_text(text)
        
        assert all(chunk.strip() for chunk in result), "Found empty chunk"


class TestTextChunkerChunkSizes:
    """Test that chunks respect max_chars limit."""
    
    def test_all_chunks_within_limit(self):
        """All chunks should be <= max_chars."""
        text = "The quick brown fox. " * 100
        for max_chars in [50, 100, 200, 500]:
            chunker = TextChunker(max_chars=max_chars)
            result = chunker.chunk_text(text)
            assert all(len(chunk) <= max_chars for chunk in result), \
                f"Found chunk exceeding {max_chars}: {[len(c) for c in result]}"
    
    def test_reasonable_chunk_count(self):
        """Chunking should be reasonably efficient."""
        text = "Sentence. " * 100
        chunker = TextChunker(max_chars=200)
        result = chunker.chunk_text(text)
        
        # Should have multiple chunks but not excessive ones
        assert len(result) > 1
        assert len(result) < len(text) / 10  # Not too fragmented
