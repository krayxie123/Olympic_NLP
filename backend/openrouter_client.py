import os
import requests
from dotenv import load_dotenv
load_dotenv()
OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"]
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "ibm-granite/granite-4.0-h-micro")
OPENROUTER_APP_URL = os.environ.get("OPENROUTER_APP_URL", "http://localhost:3000")
OPENROUTER_APP_NAME = os.environ.get("OPENROUTER_APP_NAME", "Olympics Analytics MVP")

def chat(messages, temperature=0.1, max_tokens=300):
    """
    OpenRouter is OpenAI-compatible.
    Endpoint: https://openrouter.ai/api/v1/chat/completions
    """
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            # Optional but recommended by OpenRouter:
            "HTTP-Referer": OPENROUTER_APP_URL,
            "X-Title": OPENROUTER_APP_NAME,
        },
        json={
            "model": OPENROUTER_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]