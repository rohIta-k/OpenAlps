"""Smoke-test the CSCS API, model access, and Structured Outputs.
Run:
    set -a; source .env; set +a
    uv run python scripts/smoke_test_api.py
"""
import os
import sys
import time

from openai import OpenAI

BASE_URL = os.getenv("BASE_URL","https://api.inference.cscs.ch/v1",)
API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("LLM_NAME", "swiss-ai/Apertus-v1.5-8B")
TIMEOUT = float(os.getenv("TIMEOUT_S", "60"))

if not API_KEY:
    sys.exit("Missing API_KEY. Load it from .env first.")

client = OpenAI(base_url=BASE_URL,api_key=API_KEY,timeout=TIMEOUT,max_retries=0,)

def report_response(response, elapsed_ms):
    """Print the completion, usage, and latency."""
    print("Reply:", response.choices[0].message.content)
    print("Usage:", response.usage)
    print(f"Latency: {elapsed_ms} ms")

print(f"Endpoint: {BASE_URL}")
print(f"Configured model: {MODEL}")
print("\n 1. Available models")
try:
    models = client.models.list()
    model_ids = [model.id for model in models.data]
    for model_id in model_ids:
        print(" -", model_id)
    if MODEL in model_ids:
        print(f"Configured model appears in the list: {MODEL}")
    else:
        print("WARNING: configured model was not found in the list. ""The completion test will check whether it is usable anyway.")
except Exception as exc:
    print(f"Model listing failed: {type(exc).__name__}: {exc}")

print("\n 2. Standard chat completion")
try:
    start = time.perf_counter()
    response = client.chat.completions.create(model=MODEL, max_tokens=10, temperature=0, messages=[{"role": "user", "content": "Reply with OK only."}],)
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    report_response(response, elapsed_ms)
except Exception as exc:
    print(f"Standard completion failed: {type(exc).__name__}: {exc}")
    sys.exit(1)

print("\n 3. Structured Outputs (strict JSON Schema)")
schema = {
    "type": "object",
    "properties": {
        "label": {
            "type": "string",
            "enum": ["entailment", "neutral", "contradiction"],
        },
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "page": {"type": "integer"},
                    "text": {"type": "string"},
                },
                "required": ["page", "text"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["label", "evidence"],
    "additionalProperties": False,
}
try:
    start = time.perf_counter()
    response = client.chat.completions.create(model=MODEL, max_tokens=100, temperature=0,messages=[{"role": "system","content": ("Classify the claim against the reference. ""Return a neutral label and an empty evidence array."),},{"role": "user","content": "Claim: It may rain tomorrow. Reference: No information.",},],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "classification",
                "strict": True,
                "schema": schema,
            },
        },
    )
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    report_response(response, elapsed_ms)
    print("Structured Outputs request accepted.")
except Exception as exc:
    print( "Structured Outputs test failed: " f"{type(exc).__name__}: {exc}")
    print("The endpoint/model may not support strict JSON Schema output. ""Check the error before deciding whether to use this feature.")
