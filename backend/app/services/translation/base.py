from abc import ABC, abstractmethod
from typing import List
from app.core.config import get_settings


_settings = get_settings()


class Translator(ABC):
    @abstractmethod
    def translate(self, texts: List[str], batch_size: int = 8) -> List[str]:
        """Translate a list of texts and return list of translated strings."""
        pass


class LocalTranslator(Translator):
    """Interface marker for local translator implementations."""
    pass


class APITranslator(Translator):
    """Interface marker for cloud/API translator implementations."""
    pass


class HybridTranslator(Translator):
    """Combines LocalTranslator and APITranslator.

    Default behavior: try local translator first; only call API translator if explicitly enabled.
    """

    def __init__(self, local: Translator, api: Translator | None = None, api_enabled: bool | None = None):
        self.local = local
        self.api = api
        # If api_enabled is not provided, read from settings
        if api_enabled is None:
            try:
                self.api_enabled = bool(_settings.TRANSLATOR_API_FALLBACK)
            except Exception:
                self.api_enabled = False
        else:
            self.api_enabled = api_enabled

    def translate(self, texts: List[str], batch_size: int = 8) -> List[str]:
        # Attempt local translation
        local_results = self.local.translate(texts, batch_size=batch_size)
        # If API fallback disabled or no api configured, return local results
        if not self.api_enabled or self.api is None:
            return local_results

        # If API enabled, call API translator only for items where local_results produced empty/None
        to_call = []
        indices = []
        for i, r in enumerate(local_results):
            if not r or str(r).strip() == "":
                to_call.append(texts[i])
                indices.append(i)

        if not to_call:
            return local_results

        api_results = self.api.translate(to_call, batch_size=batch_size)
        for idx, res in zip(indices, api_results):
            local_results[idx] = res

        return local_results
