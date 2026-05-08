import json
from typing import Dict, Any, List
from services.geminiService import gemini_service

class ReportAgent:
    def __init__(self):
        self.gemini = gemini_service

    async def generate_report(self, query: str, sources: List[Dict[str, Any]],
                            summary: Dict[str, Any], fact_checks: List[Dict[str, Any]]) -> str:
        """Generate a comprehensive research report"""

        # Prepare data for the report
        report_data = {
            "query": query,
            "sources": sources,
            "summary": summary,
            "fact_checks": fact_checks
        }

        prompt = f"""
        You are a professional research report writer. Create a comprehensive, well-structured research report based on the following data:

        Research Query: {query}

        Summary Data:
        {json.dumps(summary, indent=2)}

        Fact Checks:
        {json.dumps(fact_checks, indent=2)}

        Sources Used:
        {json.dumps([{"title": s.get("title"), "url": s.get("url"), "credibility": s.get("credibility")} for s in sources], indent=2)}

        Generate a polished research report in Markdown format that includes:

        # Research Report: [Query Title]

        ## Executive Summary
        [Brief overview of findings]

        ## Key Findings
        [Main insights and conclusions]

        ## Detailed Analysis
        [Break down of key insights, statistics, arguments]

        ## Risks and Opportunities
        [Balanced view of challenges and potential]

        ## Sources and References
        [List of sources with credibility scores]

        ## Fact-Checking Results
        [Summary of verification status]

        Make the report professional, objective, and well-cited. Use clear headings and bullet points where appropriate.
        """

        try:
            report_markdown = await self.gemini.generate_content(prompt, model="pro")
            return report_markdown
        except Exception as e:
            print(f"Error generating report: {e}")
            # Fallback basic report
            return f"""# Research Report: {query}

## Executive Summary
Research conducted on the topic. Analysis in progress.

## Key Findings
- Content analysis completed
- Multiple sources reviewed
- Fact-checking performed

## Sources
{chr(10).join([f"- {s.get('title', 'Unknown')}: {s.get('url', '')}" for s in sources])}

## Status
Report generation encountered technical issues. Raw data available in project files.
"""

report_agent = ReportAgent()