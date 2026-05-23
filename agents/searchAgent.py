import requests
from bs4 import BeautifulSoup
import json
from typing import List, Dict, Any
from services.openaiService import openai_service

class SearchAgent:
    def __init__(self):
        self.openai = openai_service

    async def search_web(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search the web and extract content from relevant sources"""
        # For MVP, we'll use a simple approach with some predefined URLs
        # In production, you'd integrate with a search API like Google Custom Search,
        # Bing Search API, or DuckDuckGo Search API

        # For now, return some example AI-related sources
        example_sources = [
            {
                "title": "Artificial Intelligence - Wikipedia",
                "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
                "content": "Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to natural intelligence displayed by animals including humans. AI research has been defined as the field of study of intelligent agents, which refers to any system that perceives its environment and takes actions that maximize its chance of achieving its goals.",
                "credibility": 0.9
            },
            {
                "title": "What is AI? - MIT Technology Review",
                "url": "https://www.technologyreview.com/topic/artificial-intelligence/",
                "content": "Artificial intelligence is a field of science concerned with building computers and machines that can reason, learn, and act in ways that would normally require human intelligence or that involve data whose scale exceeds what humans can analyze.",
                "credibility": 0.85
            },
            {
                "title": "Google AI Blog",
                "url": "https://ai.googleblog.com/",
                "content": "The Google AI Blog covers the latest research and developments in artificial intelligence from Google. Topics include machine learning, deep learning, natural language processing, computer vision, and more.",
                "credibility": 0.9
            }
        ]

        # Filter and limit results
        results = example_sources[:max_results]

        # Try to extract real content if newspaper is available
        for source in results:
            if "content" not in source or len(source["content"]) < 100:
                extracted = await self.extract_content(source["url"])
                if extracted:
                    source["content"] = extracted.get("text", source.get("content", ""))
                    if extracted.get("title"):
                        source["title"] = extracted["title"]

        return results

    async def extract_content(self, url: str) -> Dict[str, str]:
        """Extract clean content from a URL"""
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()

            text = soup.get_text()
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            return {
                "title": soup.title.string if soup.title else "Unknown",
                "text": text[:5000],  # Limit length
                "authors": [],
                "publish_date": None
            }
        except Exception as e:
            print(f"Failed to extract content from {url}: {e}")
            return {}

    async def rank_sources(self, sources: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Rank sources based on relevance to query using the local Ollama model"""
        if not sources:
            return sources

        prompt = f"""
        Rank the following sources based on their relevance to the query: "{query}"

        Sources:
        {json.dumps(sources, indent=2)}

        Return a JSON array of sources sorted by relevance (most relevant first).
        Include a relevance_score (0-1) for each source.
        """

        try:
            response = await self.gemini.generate_content(prompt, model="flash")
            # Parse the JSON response
            import json
            ranked_sources = json.loads(response.strip())
            return ranked_sources
        except Exception as e:
            print(f"Error ranking sources: {e}")
            # Return original sources with default scores
            for source in sources:
                source["relevance_score"] = 0.5
            return sources

search_agent = SearchAgent()