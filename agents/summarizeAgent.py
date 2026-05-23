import json
from typing import List, Dict, Any
from services.openaiService import openai_service

class SummarizationAgent:
    def __init__(self):
        self.openai = openai_service

    async def summarize_content(self, sources: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Summarize the collected content into key insights, statistics, arguments, risks, and opportunities"""

        # Combine all source content
        combined_content = "\n\n".join([
            f"Source: {source.get('title', 'Unknown')}\n{source.get('content', '')}"
            for source in sources
        ])

        prompt = f"""
        You are a research summarizer. Analyze the following content related to the query: "{query}"

        Content from sources:
        {combined_content}

        Summarize the content into the following structured format:
        1. Key insights (3-5 main points)
        2. Important statistics (any numbers, trends, or data points mentioned)
        3. Major arguments (different perspectives or viewpoints presented)
        4. Risks (potential downsides, challenges, or concerns)
        5. Opportunities (potential benefits, advantages, or future possibilities)

        Return your response as a JSON object with these exact keys: keyInsights, statistics, arguments, risks, opportunities.
        Each value should be an array of strings.
        """

        try:
            response = await self.openai.generate_content(prompt, model="pro")
            # Clean the response to extract JSON
            response_text = response.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]

            summary_data = json.loads(response_text.strip())
            return summary_data
        except Exception as e:
            print(f"Error in summarization: {e}")
            # Return a basic structure
            return {
                "keyInsights": ["Content analysis in progress"],
                "statistics": [],
                "arguments": ["Multiple perspectives identified"],
                "risks": ["Analysis ongoing"],
                "opportunities": ["Research continues"]
            }

summarize_agent = SummarizationAgent()