import json
from typing import Any, Dict, List
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from services.ollamaService import ollama_service


class SearchAgent:
    def __init__(self) -> None:
        self.llm = ollama_service

    async def search_web(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Lightweight search using DuckDuckGo HTML results plus page extraction."""
        results = self._duckduckgo_search(query, max_results=max_results)

        if not results:
            return [
                {
                    "title": "No live sources found",
                    "url": "local://fallback",
                    "content": f"No live web results were found for: {query}",
                    "credibility": 0.2,
                    "relevance_score": 0.2,
                }
            ]

        enriched: List[Dict[str, Any]] = []
        for item in results:
            extracted = await self.extract_content(item["url"])
            item["content"] = extracted.get("text") or item.get("snippet", "")
            item["title"] = extracted.get("title") or item.get("title", "Untitled")
            item["credibility"] = self._estimate_credibility(item["url"])
            enriched.append(item)

        return await self.rank_sources(enriched, query)

    def _duckduckgo_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
        except Exception as exc:
            print(f"Search failed: {exc}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        results: List[Dict[str, Any]] = []
        for result in soup.select(".result"):
            link = result.select_one(".result__a")
            snippet = result.select_one(".result__snippet")
            if not link:
                continue
            href = link.get("href", "")
            title = link.get_text(" ", strip=True)
            if href and title:
                results.append(
                    {
                        "title": title,
                        "url": href,
                        "snippet": snippet.get_text(" ", strip=True) if snippet else "",
                    }
                )
            if len(results) >= max_results:
                break
        return results

    async def extract_content(self, url: str) -> Dict[str, str]:
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.extract()
            title = soup.title.get_text(" ", strip=True) if soup.title else "Untitled"
            text = " ".join(soup.get_text(" ", strip=True).split())
            return {"title": title, "text": text[:6000]}
        except Exception as exc:
            print(f"Content extraction failed for {url}: {exc}")
            return {}

    async def rank_sources(self, sources: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        prompt = f"""
Rank these sources for relevance to the research query.
Return only a JSON array. Keep every source object and add relevance_score from 0 to 1.

Query: {query}
Sources: {json.dumps(sources, indent=2)[:12000]}
"""
        try:
            response = await self.llm.generate_content(prompt, model="flash", max_tokens=2048)
            ranked = self.llm.extract_json(response)
            if isinstance(ranked, list):
                return ranked
        except Exception as exc:
            print(f"Ranking failed, using default ordering: {exc}")

        for source in sources:
            source["relevance_score"] = source.get("relevance_score", 0.5)
        return sources

    @staticmethod
    def _estimate_credibility(url: str) -> float:
        trusted = [".edu", ".gov", "nature.com", "science.org", "arxiv.org", "who.int", "mit.edu"]
        if any(domain in url.lower() for domain in trusted):
            return 0.9
        return 0.65


search_agent = SearchAgent()
