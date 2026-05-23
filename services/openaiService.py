import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

class OpenAIService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.models = {
            "pro": os.getenv("OPENAI_MODEL_PRO", "gpt-4-turbo"),
            "flash": os.getenv("OPENAI_MODEL_FLASH", "gpt-3.5-turbo")
        }

    async def generate_content(self, prompt: str, model: str = "flash") -> str:
        """Generate content using OpenAI API"""
        model_name = self.models.get(model, self.models["flash"])
        
        try:
            response = await self.client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=2048
            )
            
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content is None:
                    raise Exception("No content in OpenAI response")
                return content
            else:
                raise Exception(f"No completion choices returned by OpenAI")
        except Exception as e:
            raise Exception(f"OpenAI request error: {str(e)}") from e

openai_service = OpenAIService()
gemini_service = openai_service
