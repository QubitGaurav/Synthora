"""
Ollama Cloud API service.

The original code defined `ollama_service` as a plain function, which caused
`'function' object has no attribute 'generate_content'` errors throughout every
agent. This module exposes a proper OllamaService class instance that all agents
depend on.
"""

import json
import os
import re
import asyncio
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "https://ollama.com/api")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "300"))


class OllamaService:
    """
    Thin wrapper around the Ollama Cloud /generate endpoint.

    The `model` parameter accepted by `generate_content` is an internal alias
    ("flash" / "pro") that maps to the single configured OLLAMA_MODEL.
    """

    def __init__(self) -> None:
        self.api_key = OLLAMA_API_KEY
        self.base_url = OLLAMA_BASE_URL.rstrip("/")
        self.model = OLLAMA_MODEL
        self.timeout = OLLAMA_TIMEOUT

    async def generate_content(
        self,
        prompt: str,
        model: str = "pro",
        max_tokens: int = 2048,
    ) -> str:
        """
        Generate a response from the Ollama Cloud API.
        Runs the blocking HTTP call in a thread to avoid blocking the event loop.
        """
        return await asyncio.to_thread(self._sync_generate, prompt, max_tokens)

    def extract_json(self, text: str) -> Any:
        """
        Robustly extract JSON from a model response.
        Tries three strategies: direct parse, strip markdown fences, regex extraction.
        """
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        stripped = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            pass
        match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        return None

    async def health_check(self) -> dict:
        try:
            await asyncio.to_thread(self._ping)
            return {"status": "ok", "model": self.model, "base_url": self.base_url}
        except Exception as exc:
            return {"status": "error", "detail": str(exc)}

    def _sync_generate(self, prompt: str, max_tokens: int) -> str:
        if not self.api_key:
            raise ValueError("OLLAMA_API_KEY is not set. Add it to your .env file.")
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens},
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(
            f"{self.base_url}/generate",
            json=payload,
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")

    def _ping(self) -> None:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        requests.get(self.base_url, headers=headers, timeout=10).raise_for_status()


ollama_service = OllamaService()