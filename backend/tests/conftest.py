import sys
import types
import os

# Provide a lightweight fake for app.core.config.get_settings to avoid
# importing Pydantic BaseSettings during tests in environments where
# pydantic/pydantic-settings may be incompatible.
mod_name = "app.core.config"
if mod_name not in sys.modules:
    fake = types.ModuleType(mod_name)

    class _S:
        TRANSLATOR_API_FALLBACK = False
        TRANSLATOR_MODEL = os.environ.get("TRANSLATOR_MODEL", "facebook/m2m100_418M")
        HF_HOME = os.environ.get("HF_HOME", os.path.join(os.path.expanduser("~"), ".cache", "huggingface"))
        TRANSLATOR_PROVIDER = os.environ.get("TRANSLATOR_PROVIDER", "local")

    def get_settings():
        return _S()

    fake.get_settings = get_settings
    sys.modules[mod_name] = fake
