import pytest

import types


def test_local_translator_init_monkeypatched(monkeypatch):
    # Prevent heavy model download by monkeypatching transformers.from_pretrained
    dummy_tokenizer = types.SimpleNamespace()
    def dummy_tokenizer_from_pretrained(name, cache_dir=None):
        # Return an object whose class defines __call__ so it's callable
        class DummyTokenizer:
            def __init__(self):
                self.src_lang = None
                self.tgt_lang = None
                self.get_lang_id_calls = []

            def get_lang_id(self, x):
                self.get_lang_id_calls.append(x)
                return 0

            def __call__(self, texts, return_tensors=None, padding=None):
                return {"input_ids": [[1,2,3] for _ in texts]}

            def decode(self, x, skip_special_tokens=True):
                return "decoded"

        return DummyTokenizer()

    class DummyModel:
        def generate(self, **kwargs):
            return [b"dummy"]

    def dummy_model_from_pretrained(name, cache_dir=None):
        return DummyModel()

    # Inject a fake `transformers` module into sys.modules so importing the translator
    # does not attempt to import real Transformers and download models.
    import sys
    fake_transformers = types.SimpleNamespace()
    # Provide classes with from_pretrained factory functions
    class FakeTokenizerClass:
        @staticmethod
        def from_pretrained(name, cache_dir=None):
            return dummy_tokenizer_from_pretrained(name, cache_dir=cache_dir)

    class FakeModelClass:
        @staticmethod
        def from_pretrained(name, cache_dir=None):
            return dummy_model_from_pretrained(name, cache_dir=cache_dir)

    # Provide a tokenizer factory and ensure the returned tokenizer is callable
    class TokenizerFactory:
        @staticmethod
        def from_pretrained(name, cache_dir=None):
            return dummy_tokenizer_from_pretrained(name, cache_dir=cache_dir)

    class ModelFactory:
        @staticmethod
        def from_pretrained(name, cache_dir=None):
            return dummy_model_from_pretrained(name, cache_dir=cache_dir)

    fake_transformers.M2M100Tokenizer = TokenizerFactory
    fake_transformers.M2M100ForConditionalGeneration = ModelFactory
    # insert into sys.modules under the expected name
    sys.modules["transformers"] = fake_transformers

    # Now import the class and instantiate
    from app.services.translation.local_translator import LocalM2M100Translator
    t = LocalM2M100Translator(model_name="facebook/m2m100_418M")
    # exercise translate path to ensure src/tgt settings used
    out = t.translate(["测试文本"], batch_size=1)
    assert out == ["decoded"]
    # Ensure tokenizer src_lang was set to zh and get_lang_id called for vi
    tok = type(LocalM2M100Translator._tokenizer)
    # Access the actual tokenizer object used
    tokenizer_obj = LocalM2M100Translator._tokenizer
    assert tokenizer_obj.src_lang == "zh"
    assert "vi" in tokenizer_obj.get_lang_id_calls
