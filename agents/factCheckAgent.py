import json
from typing import List, Dict, Any
from services.geminiService import gemini_service

class FactCheckAgent:
    def __init__(self):
        self.gemini = gemini_service

    async def fact_check_claims(self, sources: List[Dict[str, Any]], summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fact-check key claims from the summary against sources"""

        # Extract potential claims from summary
        claims = []
        claims.extend(summary.get("keyInsights", []))
        claims.extend(summary.get("statistics", []))
        claims.extend(summary.get("arguments", []))
        claims.extend(summary.get("risks", []))
        claims.extend(summary.get("opportunities", []))

        fact_checks = []

        for claim in claims[:10]:  # Limit to first 10 claims for MVP
            verification = await self.verify_claim(claim, sources)
            fact_checks.append({
                "claim": claim,
                "status": verification["status"],
                "confidence": verification["confidence"],
                "supporting_sources": verification["sources"],
                "explanation": verification["explanation"]
            })

        return fact_checks

    async def verify_claim(self, claim: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify a single claim against sources"""

        # Count how many sources mention this claim or related content
        supporting_sources = []
        contradicting_sources = []

        for source in sources:
            content = source.get("content", "").lower()
            claim_lower = claim.lower()

            # Simple text matching - in production, use more sophisticated NLP
            if any(word in content for word in claim_lower.split()):
                supporting_sources.append(source.get("url", ""))
            # For contradictions, we'd need more complex logic

        source_count = len(supporting_sources)

        # Determine confidence based on source count
        if source_count >= 3:
            confidence = 0.87  # High confidence
            status = "verified"
        elif source_count >= 2:
            confidence = 0.65  # Medium confidence
            status = "partially_verified"
        elif source_count >= 1:
            confidence = 0.35  # Low confidence
            status = "weak_evidence"
        else:
            confidence = 0.1   # Very low confidence
            status = "unverified"

        # Use Gemini for more sophisticated verification
        prompt = f"""
        Verify the following claim against the provided sources:

        Claim: "{claim}"

        Sources content:
        {json.dumps([{"url": s.get("url"), "content": s.get("content", "")[:1000]} for s in sources], indent=2)}

        Based on the sources, determine:
        1. Is the claim supported, contradicted, or neither?
        2. Confidence level (0.0 to 1.0)
        3. Brief explanation

        Return as JSON with keys: status, confidence, explanation
        Status should be: "verified", "contradicted", "unverified", or "partially_verified"
        """

        try:
            response = await self.gemini.generate_content(prompt, model="flash")
            verification_data = json.loads(response.strip())
            verification_data["sources"] = supporting_sources
            return verification_data
        except Exception as e:
            print(f"Error in fact-checking: {e}")
            return {
                "status": status,
                "confidence": confidence,
                "sources": supporting_sources,
                "explanation": f"Automated verification based on {source_count} supporting sources"
            }

fact_check_agent = FactCheckAgent()