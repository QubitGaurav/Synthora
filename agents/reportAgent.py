import json
from typing import Any, Dict, List

from services.ollamaService import ollama_service


class ReportAgent:
    def __init__(self) -> None:
        self.llm = ollama_service

    async def generate_report(
        self,
        query: str,
        sources: List[Dict[str, Any]],
        summary: Dict[str, Any],
        fact_checks: List[Dict[str, Any]],
    ) -> str:
        source_list = [
            {
                "title": source.get("title"),
                "url": source.get("url"),
                "credibility": source.get("credibility"),
                "relevance_score": source.get("relevance_score"),
            }
            for source in sources
        ]
        prompt = f"""
You are a professional research report writer.
Create a polished Markdown research report.

Research query: {query}
Summary: {json.dumps(summary, indent=2)}
Fact checks: {json.dumps(fact_checks, indent=2)}
Sources: {json.dumps(source_list, indent=2)}

Required structure:
# Research Report: {query}
## Executive Summary
## Key Findings
## Detailed Analysis
## Risks and Opportunities
## Fact-Checking Results
## Sources and References

Use citations by naming source titles and URLs. Be objective. Do not invent facts.
"""
        try:
            return await self.llm.generate_content(prompt, model="pro", max_tokens=3000)
        except Exception as exc:
            print(f"Report generation failed: {exc}")
            return f"""# Research Report: {query}

## Status
Report generation failed with local Ollama.

## Error
{exc}

## Sources
{chr(10).join(f'- {s.get("title", "Unknown")}: {s.get("url", "")}' for s in sources)}
"""


report_agent = ReportAgent()
