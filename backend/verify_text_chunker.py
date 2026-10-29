#!/usr/bin/env python3
"""
Manual verification of TextChunker for STEP 5A.
Demonstrates sentence/paragraph-aware chunking with Vietnamese text.
"""

from app.services.text_service import TextChunker, normalize_text


# Test text: Combined Vietnamese paragraphs from POC
TEST_TEXT = """
Ngày hôm đó trời mưa rất lớn. Tôi đứng trước cửa và chờ anh. Khoảng mười phút sau, anh mới xuất hiện. Chúng tôi bước ra ngoài cùng nhau.

Mưa vẫn rơi ào ào, nhưng tôi cảm thấy ấm áp vì có anh bên cạnh. "Bạn khỏe không?" anh hỏi. "Tôi khỏe, cảm ơn bạn," tôi trả lời. Chúng tôi đi dọc theo con đường quen thuộc.

Cây cối lủi thủi trong mưa. Những chiếc lá xanh bị nước mưa làm ướt sũng. Từng giọt nước rơi từ các cành, tạo thành nhừng dòng nhỏ trên mặt đất. 

"Này, anh có nhớ hôm chúng ta tới đây lần đầu không?" tôi nói. Anh cười. "Tất nhiên là nhớ. Hôm đó cũng mưa y vậy."

Chúng tôi tiếp tục đi. Tiếng mưa là tiếng nhạc dẫn dắt chúng tôi. Mọi thứ dường như lặng lẽ hơn, thoải mái hơn. Chỉ có tiếng chân chúng tôi và tiếng mưa rơi.
""".strip()


def verify_chunker():
    """Verify TextChunker functionality."""
    print("=" * 80)
    print("TEXT CHUNKER VERIFICATION — STEP 5A")
    print("=" * 80)
    print()
    
    print("Test text:")
    print("-" * 80)
    print(TEST_TEXT)
    print()
    print("-" * 80)
    print()
    
    # Test with different max_chars
    for max_chars in [200, 500, 1000]:
        print()
        print(f"[TEST] max_chars = {max_chars}")
        print("=" * 80)
        
        chunker = TextChunker(max_chars=max_chars)
        chunks = chunker.chunk_text(TEST_TEXT)
        
        print(f"Original length: {len(TEST_TEXT)} chars")
        print(f"Number of chunks: {len(chunks)}")
        print()
        
        total_len = 0
        for i, chunk in enumerate(chunks, 1):
            chunk_len = len(chunk)
            total_len += chunk_len
            status = "✅" if chunk_len <= max_chars else "❌"
            print(f"{status} Chunk {i:02d}: {chunk_len:4d} chars")
            print(f"   {repr(chunk[:100])}")
            if len(chunk) > 100:
                print(f"   ...{repr(chunk[-50:])}")
            print()
        
        print(f"Total chars in all chunks: {total_len}")
        print(f"Matches original? {total_len == len(TEST_TEXT)}")
        print()
    
    # Specific test: max_chars = 500 (default for OmniVoice)
    print()
    print("=" * 80)
    print("[FINAL TEST] Default max_chars = 500 (OmniVoice optimized)")
    print("=" * 80)
    
    chunker = TextChunker(max_chars=500)
    chunks = chunker.chunk_text(TEST_TEXT)
    
    print(f"Number of chunks: {len(chunks)}")
    print()
    
    for i, chunk in enumerate(chunks, 1):
        print(f"[CHUNK {i}] ({len(chunk)} chars)")
        print(f"  Content: {chunk}")
        print()
    
    # Verify no empty chunks
    print("=" * 80)
    print("VERIFICATION CHECKS")
    print("=" * 80)
    
    # Normalize both for comparison (since chunker normalizes whitespace)
    normalized_text = normalize_text(TEST_TEXT)
    reconstructed = ' '.join(chunks)
    
    # Check word order preservation
    original_words = normalized_text.split()
    reconstructed_words = reconstructed.split()
    word_order_preserved = original_words == reconstructed_words
    
    checks = {
        "✅ No empty chunks": all(chunk.strip() for chunk in chunks),
        "✅ All chunks <= max_chars": all(len(chunk) <= 500 for chunk in chunks),
        "✅ Content preserved (after normalization)": reconstructed == normalized_text,
        "✅ Word order preserved": word_order_preserved,
    }
    
    for check, result in checks.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {check}")
    
    print()
    all_pass = all(checks.values())
    if all_pass:
        print("🎉 ALL CHECKS PASSED")
    else:
        print("⚠️  SOME CHECKS FAILED")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    verify_chunker()
