"""Probe two CapCut voices only when authorized to use the unofficial endpoint."""

import argparse
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

for key in list(os.environ):
    if key.startswith(("CAPCUT_", "LYRA_TTS_")):
        del os.environ[key]

import requests
from capcut_tts_api import CapCutAPIError, CapCutClient, CapCutError


TEXT = (
    "Xin ch\u00e0o, h\u00f4m nay tr\u1eddi r\u1ea5t \u0111\u1eb9p. "
    "Ch\u00fang ta c\u00f9ng \u0111i d\u1ea1o v\u00e0 k\u1ec3 cho nhau nghe "
    "nh\u1eefng c\u00e2u chuy\u1ec7n vui nh\u00e9."
)
VOICES = ("BV421_vivn_streaming", "BV074_streaming")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--confirm-authorized",
        action="store_true",
        help="Confirm you have permission to automate requests to this endpoint.",
    )
    args = parser.parse_args()
    if not args.confirm_authorized:
        parser.error("The unofficial endpoint must not be used without authorization.")

    output_dir = Path(tempfile.gettempdir()) / "capcut_tts_probe"
    output_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.trust_env = False
    client = CapCutClient(session=session, timeout=20)
    failed = False

    for voice in VOICES:
        start = time.monotonic()
        try:
            result = client.generate_speech(TEXT, voice=voice, timeout=60)
            audio_path = client.download_tts_audio(result, output_dir / f"{voice}.mp3")
            elapsed = time.monotonic() - start
            print(f"{voice}: saved {audio_path} in {elapsed:.2f}s", flush=True)
            try:
                subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration,size",
                     "-of", "default=noprint_wrappers=1", str(audio_path)],
                    check=True,
                )
            except (FileNotFoundError, subprocess.CalledProcessError) as exc:
                print(f"{voice}: ffprobe failed: {type(exc).__name__}", flush=True)
                failed = True
        except CapCutAPIError as exc:
            failed = True
            code = exc.response_data.get("ret")
            print(f"{voice}: {type(exc).__name__} HTTP={exc.status_code} ret={code}", flush=True)
            print("Stopping after API error.", flush=True)
            break
        except (CapCutError, requests.RequestException) as exc:
            failed = True
            print(f"{voice}: {type(exc).__name__}", flush=True)

    session.close()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())