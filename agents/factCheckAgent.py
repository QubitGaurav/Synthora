import json
from typing import Any, Dict, List

from services.ollamaService import ollama_service

_MAX_CLAIMS = 8
_MAX_SOURCE_CONTENT = 1200


class FactCheckAgent:
    def __init__(self) -> None:
        self.llm = ollama_service

    async def fact_check_claims(
        self, sources: List[Dict[str, Any]], summary: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        claims: List[str] = []
        for key in ["keyInsights", "statistics", "arguments", "risks", "opportunities"]:
            claims.extend(summary.get(key, []))

        # Limit to avoid excessive LLM calls
        claims = [c for c in claims if c and len(c) > 10][:_MAX_CLAIMS]

        results = []
        for claim in claims:
            results.append(await self._verify_claim(claim, sources))
        return results

    async def _verify_claim(
        self, claim: str, sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        evidence = [
            {
                "title": s.get("title"),
                "url": s.get("url"),
                "content": s.get("content", "")[:_MAX_SOURCE_CONTENT],
            }
            for s in sources
        ]
        prompt = f"""
Verify the following claim using ONLY the provided source excerpts.
Return ONLY valid JSON with these keys:
  claim (string), status (one of: verified|partially_verified|contradicted|unverified),
  confidence (float 0-1), supporting_sources (array of URLs), explanation (string).

Claim: {claim}
Sources: {json.dumps(evidence, indent=2)}
"""
        try:
            response = await self.llm.generate_content(prompt, model="flash", max_tokens=1024)
            data = self.llm.extract_json(response)
            if isinstance(data, dict):
                data.setdefault("claim", claim)
                data.setdefault("supporting_sources", [])
                # Coerce status to valid enum value
                valid_statuses = {"verified", "partially_verified", "contradicted", "unverified"}
                if data.get("status") not in valid_statuses:
                    data["status"] = "unverified"
                return data
        except Exception as exc:
            print(f"[FactCheckAgent] Verification failed for claim '{claim[:60]}': {exc}")

        return {
            "claim": claim,
            "status": "unverified",
            "confidence": 0.1,
            "supporting_sources": [],
            "explanation": "Model verification failed or source evidence was insufficient.",
        }


fact_check_agent = FactCheckAgent()