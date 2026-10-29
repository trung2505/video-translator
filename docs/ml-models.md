ML Models and Offline Usage

This project prefers local/offline-first models to avoid API costs and latency.

- OCR: PaddleOCR (lang=ch). Lightweight, offline, good for Chinese OCR. Install via `pip install paddleocr`.
- Translation: `facebook/m2m100_418M` using Hugging Face `transformers` and `sentencepiece`. The model is large; ensure `HF_HOME` points to a persistent cache directory and provide sufficient disk.
- TTS: No local TTS implementation in Step 1. Provide `app.services.tts` interfaces; implementers may use VITS, Coqui TTS, or other libs later.

Deployment notes

- Set `HF_HOME` to a persistent volume mounted into the backend and worker containers (example: `/cache/huggingface`).
- `TRANSLATOR_MODEL` env var controls the model id loaded by the local translator.
- GPU acceleration: if available, the translation model can be moved to CUDA for performance; update the translator implementation accordingly.

Limitations

- `m2m100_418M` is multilingual but still large; translation quality for Chinese->Vietnamese should be validated against small test sets.
- PaddleOCR installation may require platform-specific dependencies; see PaddleOCR docs.
- TTS is intentionally left as an abstraction (stub) in this step.
