import os
from dotenv import load_dotenv
import httpx

load_dotenv()

class OllamaService:
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
        self.models = {
            "pro": os.getenv("OLLAMA_MODEL_PRO", "qwen2.5:3b"),
            "flash": os.getenv("OLLAMA_MODEL_FLASH", "qwen2.5:3b")
        }
        self.timeout = float(os.getenv("OLLAMA_TIMEOUT", "60"))

    async def generate_content(self, prompt: str, model: str = "flash") -> str:
        """Generate content using a local Ollama model"""
        model_name = self.models.get(model, self.models["flash"])
        endpoint = f"{self.ollama_url}/v1/chat/completions"
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 1024
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(endpoint, json=payload)
                response.raise_for_status()
                data = response.json()

                choices = data.get("choices", [])
                if not choices:
                    raise Exception(f"No completion choices returned by Ollama: {data}")

                first_choice = choices[0]
                message = first_choice.get("message", {})
                if isinstance(message, dict):
                    content = message.get("content")
                else:
                    content = first_choice.get("content")

                if content is None:
                    raise Exception(f"Missing text in Ollama response: {data}")

                return content
        except httpx.HTTPStatusError as e:
            raise Exception(f"Ollama request failed ({e.response.status_code}): {e.response.text}") from e
        except Exception as e:
            raise Exception(f"Ollama request error: {str(e)}") from e

ollama_service = OllamaService()
gemini_service = ollama_service
