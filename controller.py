from typing import Dict, Any
from agents.searchAgent import search_agent
from agents.summarizeAgent import summarize_agent
from agents.factCheckAgent import fact_check_agent
from agents.reportAgent import report_agent
from utils.jsonDB import json_db

class ResearchController:
    def __init__(self):
        self.search_agent = search_agent
        self.summarize_agent = summarize_agent
        self.fact_check_agent = fact_check_agent
        self.report_agent = report_agent
        self.db = json_db

    async def process_research_request(self, user_id: str, query: str) -> str:
        """Main orchestration method for research requests"""

        # 1. Create project
        project_id = await self.db.create_project(user_id, query)
        print(f"Created project: {project_id}")

        try:
            # 2. Search Agent - Gather sources
            await self.db.update_project(project_id, {"status": "searching"})
            sources = await self.search_agent.search_web(query)
            await self.db.update_project(project_id, {"sources": sources, "status": "summarizing"})
            print(f"Found {len(sources)} sources")

            # 3. Summarization Agent - Analyze content
            summary = await self.summarize_agent.summarize_content(sources, query)
            await self.db.update_project(project_id, {"summary": summary, "status": "fact_checking"})
            print("Summary completed")

            # 4. Fact-Check Agent - Verify claims
            fact_checks = await self.fact_check_agent.fact_check_claims(sources, summary)
            await self.db.update_project(project_id, {"factChecks": fact_checks, "status": "generating_report"})
            print("Fact-checking completed")

            # 5. Report Agent - Generate final report
            final_report = await self.report_agent.generate_report(query, sources, summary, fact_checks)
            await self.db.update_project(project_id, {"finalReport": final_report, "status": "completed"})
            print("Report generated")

            # 6. Save report separately for easy access
            report_data = {
                "projectId": project_id,
                "query": query,
                "report": final_report,
                "sources": sources,
                "summary": summary,
                "factChecks": fact_checks
            }
            report_id = await self.db.save_report(report_data)

            return project_id

        except Exception as e:
            await self.db.update_project(project_id, {"status": "failed", "error": str(e)})
            raise e

controller = ResearchController()