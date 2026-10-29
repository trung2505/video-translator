#!/usr/bin/env python3
"""
Manual verification of OmniVoice TTS integration.
Generates audio samples for all 5 voices using the integrated service.

Run from project root:
  python backend/app/services/tts/verify_omnivoice.py
"""

import sys
import os
from pathlib import Path
import time
import json

# Add backend to path
backend_path = str(Path(__file__).parent.parent.parent.parent)
sys.path.insert(0, backend_path)

from app.services.tts.omnivoice_service import OmniVoiceService, OmniVoiceError


def verify_omnivoice():
    """Run verification of OmniVoice service."""
    print("=" * 80)
    print("OMNIVOICE TTS SERVICE - MANUAL VERIFICATION")
    print("=" * 80)
    print()

    # Test text (same as POC)
    test_text = "Buổi tối hôm đó, khi mọi người đã ngủ, cô gái vẫn ngồi bên cửa sổ và lặng lẽ nhìn ra ngoài trời."

    # Output directory
    output_dir = Path("C:/temp/vietnamese_tts_poc/voice_comparison/step4")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Test text: {test_text}")
    print(f"Text length: {len(test_text)} chars")
    print(f"Output directory: {output_dir}")
    print()

    # Initialize service
    print("[1/4] Initializing OmniVoiceService...")
    try:
        service = OmniVoiceService()
        print("✅ Service initialized")
        print()
    except Exception as e:
        print(f"❌ Failed to initialize service: {e}")
        return False

    # List available voices
    print("[2/4] Available voices:")
    for voice_name in service.VOICE_MAPPING.keys():
        print(f"  - {voice_name}")
    print()

    # Synthesize each voice
    print("[3/4] Synthesizing all 5 voices...")
    print("-" * 80)

    results = {}
    total_start = time.time()

    for voice in [
        "female_young_adult",
        "male_young_adult",
        "female_elderly",
        "male_deep_voice",
        "female_child",
    ]:
        output_path = output_dir / f"{voice}.wav"

        print(f"  {voice}...", end=" ", flush=True)
        start = time.time()

        try:
            path = service.synthesize_vietnamese(test_text, job_id="verify", voice=voice)
            elapsed = time.time() - start
            file_size = os.path.getsize(path)

            print(f"✅ {elapsed:.1f}s ({file_size:,} bytes)")

            results[voice] = {
                "path": path,
                "file_size": file_size,
                "duration_seconds": elapsed,
                "status": "SUCCESS",
            }

        except OmniVoiceError as e:
            print(f"❌ OmniVoiceError: {e}")
            results[voice] = {"status": "FAILED", "error": str(e)}
        except Exception as e:
            print(f"❌ Error: {e}")
            results[voice] = {"status": "FAILED", "error": str(e)}

    total_elapsed = time.time() - total_start
    print()
    print(f"Total time: {total_elapsed:.1f}s")
    print()

    # Verify output
    print("[4/4] Verification results:")
    print("-" * 80)

    success_count = 0
    failure_count = 0

    for voice, result in results.items():
        status = result.get("status")
        if status == "SUCCESS":
            print(f"  ✅ {voice}")
            print(f"     Path: {result['path']}")
            print(f"     Size: {result['file_size']:,} bytes")
            print(f"     Generation time: {result['duration_seconds']:.1f}s")
            success_count += 1
        else:
            print(f"  ❌ {voice}")
            print(f"     Error: {result.get('error')}")
            failure_count += 1

    print()
    print("=" * 80)
    print(f"SUMMARY: {success_count}/5 voices synthesized successfully")
    print("=" * 80)

    # Save results to JSON
    results_file = output_dir / "verification_results.json"
    with open(results_file, "w") as f:
        json.dump(
            {
                "timestamp": time.time(),
                "test_text": test_text,
                "output_directory": str(output_dir),
                "results": results,
                "summary": {"success": success_count, "failure": failure_count, "total": 5},
            },
            f,
            indent=2,
        )
    print(f"Results saved to: {results_file}")

    return success_count == 5


if __name__ == "__main__":
    try:
        success = verify_omnivoice()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
