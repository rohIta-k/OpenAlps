"""OpenAI-compatible client for BASE_URL (CSCS in dev, token-counting proxy at evaluation)."""
import logging
import time
from dataclasses import dataclass

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
    RateLimitError,
)

from src.schemas import TASK_A_SCHEMA, TASK_B_SCHEMA, response_format

log = logging.getLogger("track2a")
TASK_MODELS = {
    "A": "swiss-ai/Apertus-v1.5-70B",
    "B": "swiss-ai/Apertus-v1.5-8B",
}

@dataclass
class LLMResult:
    text: str
    input_tokens: int
    output_tokens: int   # completion tokens (providers normally include reasoning tokens )

class LLMClient:
    def __init__(self, st):
        self.st = st
        self.client = None
        if st.mock:
            log.warning("MOCK_LLM=1: returning FAKE neutral predictions (CI only, never for real numbers)")
            if st.api_key:
                log.error("MOCK_LLM=1 but an API key is set: every answer is FAKE. Unset MOCK_LLM for real runs!")
        else:
            if not st.api_key:
                raise RuntimeError("API_KEY (or LLM_API_KEY) is not set")
            self.client = OpenAI(base_url=st.base_url, api_key=st.api_key,
                                 timeout=st.timeout_s, max_retries=0)

    def chat(self, messages, task="A", max_tokens=None) -> LLMResult:
        max_tokens = max_tokens or self.st.max_output_tokens
        if task == "A":
          schema = TASK_A_SCHEMA
          schema_name = "task_a_response"
        elif task == "B":
          schema = TASK_B_SCHEMA
          schema_name = "task_b_response"
        else:
          raise ValueError(f"Unknown task: {task}")
        model = TASK_MODELS[task]
        if self.st.mock:
            n = sum(len(m["content"]) for m in messages) // 4
            return LLMResult('{"label": "neutral", "evidence": []}', n, 8)

        last = None
        for attempt in range(6):
            try:
                r = self.client.chat.completions.create(
                    model=model, messages=messages, temperature=0,
                    max_tokens=max_tokens,response_format=response_format(schema, schema_name),)
                text = (r.choices[0].message.content or "") if r.choices else ""
                choice = r.choices[0] if r.choices else None
                log.info(
                    "task=%s finish_reason=%s output_tokens=%s",
                    task,
                    choice.finish_reason if choice else None,
                    r.usage.completion_tokens if r.usage else 0,
                )
                u = r.usage
                res = LLMResult(text, u.prompt_tokens if u else 0, u.completion_tokens if u else 0)
                return res
            except (RateLimitError, APIConnectionError, APITimeoutError) as e:
                last = e
            except APIStatusError as e:
                last = e
                # 5xx and a transient 401 under load are retryable; other 4xx (e.g. context too long) are not
                if e.status_code < 500 and e.status_code != 401:
                    raise
                if e.status_code == 401 and attempt >= 2:
                    raise
            time.sleep(min(2 ** attempt, 30))
        raise RuntimeError(f"LLM call failed after retries: {last!r}")
