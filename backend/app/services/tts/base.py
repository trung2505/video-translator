from abc import ABC, abstractmethod
from typing import List


class TTS(ABC):
    @abstractmethod
    def synthesize(self, texts: List[str], out_dir: str) -> List[str]:
        """Synthesize each text to an audio file in out_dir. Return list of file paths."""
        pass


class LocalTTS(TTS):
    """Local TTS stub: not implemented in Step 1; provide interface only."""

    def synthesize(self, texts: List[str], out_dir: str) -> List[str]:
        raise NotImplementedError("Local TTS is not implemented. This is a stub.")
