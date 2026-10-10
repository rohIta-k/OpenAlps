"""FIRST thing to run against the real API: which models can my key use, does a call work?
    set -a; source .env; set +a
    python scripts/smoke_test_api.py
"""
import os
import sys
import time

from openai import OpenAI

base = os.getenv("BASE_URL") 
key = os.getenv("API_KEY") 
model = os.getenv("LLM_NAME") or "swiss-ai/Apertus-v1.5-8B"
if not key:
    sys.exit("Set API_KEY first:  set -a; source .env; set +a")
c = OpenAI(base_url=base, api_key=key, max_retries=0)

print("models:", [m.id for m in c.models.list().data])     
t = time.time()
raw = c.chat.completions.with_raw_response.create(
    model=model, max_tokens=5, temperature=0, messages=[{"role": "user", "content": "Say OK"}])
r = raw.parse()
print("reply:", r.choices[0].message.content, "| usage:", r.usage, "| ms:", int((time.time() - t) * 1000))