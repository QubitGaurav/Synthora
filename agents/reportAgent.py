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
                "title": s.get("title"),
                "url": s.get("url"),
                "credibility": s.get("credibility"),
                "relevance_score": s.get("relevance_score"),
            }
            for s in sources
        ]
        prompt = f"""
You are a professional research report writer. Create a polished Markdown research report.
Be objective. Do not invent facts. Use only the provided data.

Research query: {query}
Summary: {json.dumps(summary, indent=2)}
Fact checks: {json.dumps(fact_checks, indent=2)}
Sources: {json.dumps(source_list, indent=2)}

Required structure (use exactly these headings):
# Research Report: {query}
## Executive Summary
## Key Findings
## Detailed Analysis
## Risks and Opportunities
## Fact-Checking Results
## Sources and References

Cite sources by title and URL inline. Be concise and professional.
"""
        try:
            return await self.llm.generate_content(prompt, model="pro", max_tokens=3000)
        except Exception as exc:
            print(f"[ReportAgent] Report generation failed: {exc}")
            source_lines = "\n".join(
                f"- [{s.get('title', 'Unknown')}]({s.get('url', '')})" for s in sources
            )
            return f"""# Research Report: {query}

## Status
Report generation failed — check model availability.

## Error
```
{exc}
```

## Sources Collected
{source_lines}
"""


report_agent = ReportAgent()