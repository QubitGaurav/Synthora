import json
from typing import Any, Dict, List

from services.ollamaService import ollama_service


class FactCheckAgent:
    def __init__(self) -> None:
        self.llm = ollama_service

    async def fact_check_claims(
        self, sources: List[Dict[str, Any]], summary: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        claims: List[str] = []
        for key in ["keyInsights", "statistics", "arguments", "risks", "opportunities"]:
            claims.extend(summary.get(key, []))

        fact_checks: List[Dict[str, Any]] = []
        for claim in claims[:8]:
            fact_checks.append(await self.verify_claim(claim, sources))
        return fact_checks

    async def verify_claim(self, claim: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        evidence = [
            {
                "title": source.get("title"),
                "url": source.get("url"),
                "content": source.get("content", "")[:1200],
            }
            for source in sources
        ]
        prompt = f"""
Verify the claim using only the provided source excerpts.
Return only valid JSON with keys: claim, status, confidence, supporting_sources, explanation.
Status must be one of: verified, partially_verified, contradicted, unverified.
Confidence must be between 0 and 1.

Claim: {claim}
Sources: {json.dumps(evidence, indent=2)}
"""
        try:
            response = await self.llm.generate_content(prompt, model="flash", max_tokens=1024)
            data = self.llm.extract_json(response)
            if isinstance(data, dict):
                data.setdefault("claim", claim)
                data.setdefault("supporting_sources", [])
                return data
        except Exception as exc:
            print(f"Fact check failed: {exc}")

        return {
            "claim": claim,
            "status": "unverified",
            "confidence": 0.1,
            "supporting_sources": [],
            "explanation": "Local model verification failed or source evidence was insufficient.",
        }


fact_check_agent = FactCheckAgent()
