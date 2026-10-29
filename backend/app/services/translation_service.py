from abc import ABC, abstractmethod
from typing import List
import time
import logging
import httpx

logger = logging.getLogger(__name__)


class Translator(ABC):
    @abstractmethod
    def translate(self, texts: List[str]) -> List[str]:
        pass


class GeminiTranslator(Translator):
    def __init__(self, api_url: str = None, api_key: str = None, retries: int = 3, backoff: float = 1.0):
        self.api_url = api_url
        self.api_key = api_key
        self.retries = retries
        self.backoff = backoff

    def _call_api(self, text: str) -> str:
        # Placeholder implementation — replace with real Gemini/OpenAI call
        # Here we simulate via echoing the input with a prefix for demo purposes
        return f"[VI] {text}"

    def translate(self, texts: List[str]) -> List[str]:
        results = []
        for t in texts:
            attempt = 0
            while True:
                try:
                    res = self._call_api(t)
                    results.append(res)
                    break
                except Exception as exc:
                    attempt += 1
                    if attempt > self.retries:
                        logger.exception("Translation failed after retries")
                        raise
                    sleep_time = self.backoff * (2 ** (attempt - 1))
                    time.sleep(sleep_time)
        return results


class DummyTranslator(Translator):
    def translate(self, texts: List[str]) -> List[str]:
        return [f"[VI] {t}" for t in texts]
import os
import logging
import time
from typing import List, Dict, Optional

try:
    # Prefer v2 client if available
    from google.cloud import translate_v2 as translate_client
    _HAS_GCLOUD = True
except Exception:
    translate_client = None
    _HAS_GCLOUD = False

import httpx

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class TranslationService:
    """Translate Simplified Chinese segments to Vietnamese.

    Requirements addressed:
    - Keep timestamps unchanged
    - Batch translation for performance
    - Retry on API failures
    - Return translated segments
    """

    def __init__(self, api_key: Optional[str] = None, retries: int = 3, backoff: float = 1.0):
        self.api_key = api_key or settings.GOOGLE_TRANSLATE_API_KEY
        self.retries = retries
        self.backoff = backoff

        if _HAS_GCLOUD and not self.api_key:
            # Use google cloud client (requires GOOGLE_APPLICATION_CREDENTIALS env)
            try:
                self.client = translate_client.Client()
                logger.info("Using google.cloud translate client")
            except Exception:
                logger.exception("Failed to initialize google cloud translate client")
                self.client = None
        else:
            self.client = None

    def _translate_batch_gcloud(self, texts: List[str], source: str = "zh", target: str = "vi") -> List[str]:
        """Translate list of texts using google.cloud translate_v2 client."""
        assert self.client is not None
        return [res["translatedText"] for res in self.client.translate(texts, source_language=source, target_language=target)]

    def _translate_batch_rest(self, texts: List[str], source: str = "zh", target: str = "vi") -> List[str]:
        """Translate list of texts using Google Translate REST API with API key."""
        if not self.api_key:
            raise RuntimeError("No Google Translate API key available for REST fallback")

        url = "https://translation.googleapis.com/language/translate/v2"
        params = {"key": self.api_key}

        data = []
        for t in texts:
            data.append(("q", t))
        data.append(("source", source))
        data.append(("target", target))
        data.append(("format", "text"))

        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        # POST with retries
        attempt = 0
        while True:
            try:
                resp = httpx.post(url, params=params, data=data, headers=headers, timeout=30.0)
                resp.raise_for_status()
                payload = resp.json()
                translations = [item["translatedText"] for item in payload.get("data", {}).get("translations", [])]
                if len(translations) != len(texts):
                    logger.warning("REST translate returned %d translations for %d texts", len(translations), len(texts))
                return translations
            except Exception as e:
                attempt += 1
                logger.warning("REST translate attempt %d failed: %s", attempt, e)
                if attempt >= self.retries:
                    logger.exception("REST translate failed after %d attempts", attempt)
                    raise
                time.sleep(self.backoff * (2 ** (attempt - 1)))

    def translate_segments(self, segments: List[Dict], batch_size: int = 16) -> List[Dict]:
        """Translate input segments (list of {start,end,text}) and return same structure with 'translated_text'.

        - Batches text for performance
        - Retries on transient failures
        - Preserves timestamps
        """
        if not segments:
            return []

        texts = [s.get("text", "") for s in segments]
        translated_texts: List[Optional[str]] = [None] * len(texts)

        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            attempt = 0
            while True:
                try:
                    if self.client:
                        logger.debug("Translating batch %d-%d via gcloud", i, i + len(batch_texts) - 1)
                        batch_trans = self._translate_batch_gcloud(batch_texts)
                    else:
                        logger.debug("Translating batch %d-%d via REST", i, i + len(batch_texts) - 1)
                        batch_trans = self._translate_batch_rest(batch_texts)

                    # assign results
                    for j, t in enumerate(batch_trans):
                        translated_texts[i + j] = t
                    break
                except Exception:
                    attempt += 1
                    logger.exception("Translation batch %d-%d failed (attempt %d)", i, i + len(batch_texts) - 1, attempt)
                    if attempt >= self.retries:
                        raise
                    time.sleep(self.backoff * (2 ** (attempt - 1)))

        # Build result segments keeping timestamps
        results: List[Dict] = []
        for idx, seg in enumerate(segments):
            translated = translated_texts[idx] or ""
            results.append({
                "start": seg.get("start"),
                "end": seg.get("end"),
                "original_text": seg.get("text"),
                "translated_text": translated,
            })

        return results
