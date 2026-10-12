"""Runtime configuration. Environment variables always win."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _first(*names, default=None):
    for n in names:
        v = os.getenv(n)
        if v:
            return v
    return default

@dataclass(frozen=True)
class Settings:
    base_url: str
    api_key: str | None
    model: str
    workers: int
    max_output_tokens: int
    max_input_chars: int
    timeout_s: float
    data_dir: str
    cache_dir: str
    use_cache: bool
    mock: bool


def get_settings() -> Settings:
    return Settings(
        base_url=_first("BASE_URL", "LLM_BASE_URL", default="https://api.inference.cscs.ch/v1"),
        api_key=_first("API_KEY", "LLM_API_KEY"),
        model=_first("LLM_NAME", "MODEL", default="swiss-ai/Apertus-v1.5-8B"),
        workers=int(_first("WORKERS", default="1")),
        max_output_tokens=int(_first("MAX_OUTPUT_TOKENS", default="300")),
        max_input_chars=int(_first("MAX_INPUT_CHARS", default="600000")),  # ~190k tokens guard (context 262k)
        timeout_s=float(_first("TIMEOUT_S", default="300")),
        data_dir=_first("DATA_DIR", default="/data/sample"),
        cache_dir=_first("CACHE_DIR", default="/tmp/llm_cache"),
        use_cache=_first("USE_CACHE", default="0") == "1",
        mock=_first("MOCK_LLM", default="0") == "1",
    )
