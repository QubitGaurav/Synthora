import json
from typing import Any, Dict, List

from services.ollamaService import ollama_service


class SummarizationAgent:
    def __init__(self) -> None:
        self.llm = ollama_service

    async def summarize_content(self, sources: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        combined_content = "\n\n".join(
            f"Source: {source.get('title', 'Unknown')}\nURL: {source.get('url', '')}\n{source.get('content', '')[:2500]}"
            for source in sources
        )

        prompt = f"""
You are a strict research summarizer.
Analyze the sources for this query: "{query}"

Sources:
{combined_content[:15000]}

Return only valid JSON with exactly these keys:
- keyInsights: array of 3-5 strings
- statistics: array of strings
- arguments: array of strings
- risks: array of strings
- opportunities: array of strings

Do not use markdown. Do not add commentary outside JSON.
"""
        try:
            response = await self.llm.generate_content(prompt, model="pro", max_tokens=2048)
            data = self.llm.extract_json(response)
            if not isinstance(data, dict):
                raise ValueError("Expected JSON object")
            return {
                "keyInsights": data.get("keyInsights", []),
                "statistics": data.get("statistics", []),
                "arguments": data.get("arguments", []),
                "risks": data.get("risks", []),
                "opportunities": data.get("opportunities", []),
            }
        except Exception as exc:
            print(f"Summarization failed: {exc}")
            return {
                "keyInsights": ["Unable to generate structured summary from the local model."],
                "statistics": [],
                "arguments": [],
                "risks": [str(exc)],
                "opportunities": ["Check Ollama model availability and retry."],
            }


summarize_agent = SummarizationAgent()
