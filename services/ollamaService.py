import os
import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com/api")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")


def generate_response(prompt: str) -> str:
    if not OLLAMA_API_KEY:
        raise ValueError("OLLAMA_API_KEY missing. Add it in your .env file.")

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }

    headers = {
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{OLLAMA_BASE_URL}/generate",
        json=payload,
        headers=headers,
        timeout=300
    )

    response.raise_for_status()

    data = response.json()
    return data.get("response", "")


def ollama_service(prompt: str) -> str:
    return generate_response(prompt)