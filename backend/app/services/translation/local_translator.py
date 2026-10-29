import logging
from typing import List
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
from threading import Lock
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LocalM2M100Translator:
    """Local translator using facebook/m2m100_418M.

    - Loads model/tokenizer once and reuses them across calls.
    - Supports batch translation.
    - CPU-first; GPU optional later.
    """

    _model = None
    _tokenizer = None
    _lock = Lock()

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or settings.TRANSLATOR_MODEL
        self._ensure_loaded()

    def _ensure_loaded(self):
        if LocalM2M100Translator._model is None:
            with LocalM2M100Translator._lock:
                if LocalM2M100Translator._model is None:
                    logger.info("Loading M2M100 model %s", self.model_name)
                    LocalM2M100Translator._tokenizer = M2M100Tokenizer.from_pretrained(self.model_name, cache_dir=settings.HF_HOME)
                    LocalM2M100Translator._model = M2M100ForConditionalGeneration.from_pretrained(self.model_name, cache_dir=settings.HF_HOME)

    def translate(self, texts: List[str], batch_size: int = 8) -> List[str]:
        results: List[str] = []
        tokenizer = LocalM2M100Translator._tokenizer
        model = LocalM2M100Translator._model
        if not tokenizer or not model:
            raise RuntimeError("M2M100 model not loaded")

        # Use tokenizer and model; set src_lang and tgt_lang accordingly
        # For M2M100, set tokenizer.src_lang and use forced_bos_token_id for target language
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            # set source language to Chinese
            tokenizer.src_lang = "zh"
            # set target language to Vietnamese
            try:
                tokenizer.tgt_lang = "vi"
                forced_bos = tokenizer.get_lang_id("vi")
            except Exception:
                forced_bos = None

            # Call the tokenizer normally; the explicit fallback also supports lightweight
            # tokenizer doubles that expose `__call__` only on the instance.
            if callable(tokenizer):
                encoded = tokenizer(batch, return_tensors="pt", padding=True)
            else:
                encoded = tokenizer.__call__(batch, return_tensors="pt", padding=True)
            if forced_bos is not None:
                generated = model.generate(**encoded, forced_bos_token_id=forced_bos)
            else:
                generated = model.generate(**encoded)
            decoded = [tokenizer.decode(g, skip_special_tokens=True) for g in generated]
            results.extend(decoded)

        return results


