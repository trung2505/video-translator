import pytest
from app.services.ocr_service import PaddleOCRWrapper, ocr_image, OCRInitializationError


def test_ocr_missing_package(monkeypatch):
    # Simulate missing paddleocr import
    monkeypatch.setitem(__import__("builtins").__dict__, "paddleocr", None)
    # We can't easily simulate import failure of paddleocr without more invasive patching.
    # Instead, check that instance creation raises if paddleocr is absent by patching import
    try:
        PaddleOCRWrapper._instance = None
        with pytest.raises(OCRInitializationError):
            # Temporarily rename paddleocr in sys.modules
            import sys

            saved = sys.modules.pop("paddleocr", None)
            try:
                PaddleOCRWrapper()
            finally:
                if saved is not None:
                    sys.modules["paddleocr"] = saved
    finally:
        PaddleOCRWrapper._instance = None


def test_ocr_monkeypatched(monkeypatch):
    # Provide a fake paddleocr.PaddleOCR with predictable output
    class FakePaddleOCR:
        def __init__(self, use_angle_cls=False, lang=None):
            self.lang = lang

        def ocr(self, image_path, cls=False):
            # return list of [bbox, (text, confidence)]
            return [([[0, 0], [10, 0], [10, 10], [0, 10]], ("你好", 0.95)),
                    ([[0, 12], [10, 12], [10, 22], [0, 22]], ("世界", 0.9))]

    import sys

    saved = sys.modules.get("paddleocr")
    fake_mod = type("M", (), {"PaddleOCR": FakePaddleOCR})
    sys.modules["paddleocr"] = fake_mod

    try:
        PaddleOCRWrapper._instance = None
        wrapper = PaddleOCRWrapper()
        res = wrapper.ocr_image("dummy.png")
        assert isinstance(res, list)
        assert res[0]["text"] == "你好"
        assert res[0]["order_index"] == 0
    finally:
        PaddleOCRWrapper._instance = None
        if saved is not None:
            sys.modules["paddleocr"] = saved
        else:
            del sys.modules["paddleocr"]
