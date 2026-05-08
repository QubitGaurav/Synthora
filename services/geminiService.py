import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class GeminiService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        genai.configure(api_key=api_key)
        self.models = {
            "pro": genai.GenerativeModel("gemini-2.5-pro"),
            "flash": genai.GenerativeModel("gemini-1.5-flash")
        }

    async def generate_content(self, prompt: str, model: str = "flash") -> str:
        """Generate content using Gemini model"""
        try:
            response = self.models[model].generate_content(prompt)
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")

gemini_service = GeminiService()