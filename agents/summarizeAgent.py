import json
from typing import Any, Dict, List

from services.ollamaService import ollama_service

_REQUIRED_KEYS = ["keyInsights", "statistics", "arguments", "risks", "opportunities"]


class SummarizationAgent:
    def __init__(self) -> None:
        self.llm = ollama_service

    async def summarize_content(
        self, sources: List[Dict[str, Any]], query: str
    ) -> Dict[str, Any]:
        combined_content = "\n\n".join(
            f"Source: {s.get('title', 'Unknown')}\nURL: {s.get('url', '')}\n{s.get('content', '')[:2500]}"
            for s in sources
        )

        prompt = f"""
You are a strict research summarizer. Analyze the following sources for this query: "{query}"

Sources:
{combined_content[:15000]}

Return ONLY valid JSON with exactly these keys — no markdown, no commentary:
- keyInsights: array of 3-5 strings
- statistics: array of strings (include numbers/percentages where available)
- arguments: array of strings
- risks: array of strings
- opportunities: array of strings
"""
        try:
            response = await self.llm.generate_content(prompt, model="pro", max_tokens=2048)
            data = self.llm.extract_json(response)
            if not isinstance(data, dict):
                raise ValueError(f"Expected JSON object, got {type(data)}")
            return {key: data.get(key, []) for key in _REQUIRED_KEYS}
        except Exception as exc:
            print(f"[SummarizationAgent] Failed: {exc}")
            return {
                "keyInsights": ["Summarization failed — check model availability."],
                "statistics": [],
                "arguments": [],
                "risks": [str(exc)],
                "opportunities": ["Verify OLLAMA_API_KEY and model name in .env and retry."],
            }


summarize_agent = SummarizationAgent()