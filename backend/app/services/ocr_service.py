import threading
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class OCRInitializationError(RuntimeError):
    pass


class PaddleOCRWrapper:
    """Singleton wrapper for PaddleOCR model loading and inference.

    - Loads PaddleOCR once and reuses the model.
    - Provides `ocr_image(path)` returning list of dicts: text, bbox, confidence, order_index
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        try:
            from paddleocr import PaddleOCR
        except Exception as e:
            raise OCRInitializationError("PaddleOCR package is not installed: %s" % e)

        # Use chinese OCR model; enable GPU later via config if needed
        try:
            # use default det/rec models; set use_angle_cls=False for speed
            self._ocr = PaddleOCR(use_angle_cls=False, lang="ch")
        except Exception as e:
            raise OCRInitializationError(f"Failed to initialize PaddleOCR: {e}")

    @classmethod
    def instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = PaddleOCRWrapper()
        return cls._instance

    def ocr_image(self, image_path: str) -> List[Dict]:
        """Run OCR on the given image file and return structured results.

        Returns list of {text, bbox, confidence, order_index}
        """
        try:
            result = self._ocr.ocr(image_path, cls=False)
        except Exception as e:
            logger.exception("PaddleOCR inference failed: %s", e)
            raise

        structured = []
        for idx, line in enumerate(result):
            # PaddleOCR returns list of [bbox, (text, confidence)] per line
            try:
                bbox = line[0]
                text, conf = line[1]
            except Exception:
                continue
            structured.append({
                "text": str(text).strip(),
                "bbox": bbox,
                "confidence": float(conf),
                "order_index": idx,
            })

        return structured


def ocr_image(image_path: str) -> List[Dict]:
    """Convenience function: get singleton and run ocr."""
    wrapper = PaddleOCRWrapper.instance()
    return wrapper.ocr_image(image_path)
