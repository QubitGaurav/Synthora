"""
SearchAgent — DuckDuckGo scraping + content extraction + LLM-based ranking.

Key fix: DuckDuckGo HTML results return redirect URLs like
  //duckduckgo.com/l/?uddg=<encoded_real_url>
The original code tried to fetch these redirect URLs directly, which always
failed. We now decode the real URL from the `uddg` query parameter before
attempting content extraction.
"""

import asyncio
import json
from typing import Any, Dict, List
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import requests
from bs4 import BeautifulSoup

from services.ollamaService import ollama_service


def _decode_ddg_redirect(url: str) -> str:
    """
    Extract the real destination URL from a DuckDuckGo redirect.

    DuckDuckGo wraps links as:  //duckduckgo.com/l/?uddg=<percent-encoded URL>
    We decode the `uddg` parameter to get the actual destination.
    If it is already a normal URL, return it unchanged.
    """
    if not url:
        return url
    # Normalise scheme-relative URLs
    if url.startswith("//"):
        url = "https:" + url
    parsed = urlparse(url)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        qs = parse_qs(parsed.query)
        uddg = qs.get("uddg", [None])[0]
        if uddg:
            return unquote(uddg)
    return url


class SearchAgent:
    def __init__(self) -> None:
        self.llm = ollama_service

    async def search_web(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search DuckDuckGo and enrich each result with extracted page content."""
        raw_results = await asyncio.to_thread(
            self._duckduckgo_search, query, max_results
        )

        if not raw_results:
            return [
                {
                    "title": "No live sources found",
                    "url": "local://fallback",
                    "content": f"No live web results were found for: {query}",
                    "credibility": 0.2,
                    "relevance_score": 0.2,
                }
            ]

        # Decode redirect URLs before extraction
        for item in raw_results:
            item["url"] = _decode_ddg_redirect(item["url"])

        # Extract page content concurrently (bounded by semaphore to avoid hammering)
        sem = asyncio.Semaphore(3)

        async def _enrich(item: Dict[str, Any]) -> Dict[str, Any]:
            async with sem:
                extracted = await asyncio.to_thread(self._extract_content, item["url"])
            item["content"] = extracted.get("text") or item.get("snippet", "")
            item["title"] = extracted.get("title") or item.get("title", "Untitled")
            item["credibility"] = self._estimate_credibility(item["url"])
            return item

        enriched = await asyncio.gather(*[_enrich(r) for r in raw_results])
        return await self._rank_sources(list(enriched), query)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _duckduckgo_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; SynthoraBot/1.0)"}
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
        except Exception as exc:
            print(f"[SearchAgent] DuckDuckGo request failed: {exc}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        results: List[Dict[str, Any]] = []
        for result in soup.select(".result"):
            link = result.select_one(".result__a")
            snippet_tag = result.select_one(".result__snippet")
            if not link:
                continue
            href = link.get("href", "")
            title = link.get_text(" ", strip=True)
            if href and title:
                results.append(
                    {
                        "title": title,
                        "url": href,
                        "snippet": snippet_tag.get_text(" ", strip=True) if snippet_tag else "",
                    }
                )
            if len(results) >= max_results:
                break
        return results

    def _extract_content(self, url: str) -> Dict[str, str]:
        if not url or url.startswith("local://"):
            return {}
        try:
            response = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; SynthoraBot/1.0)"},
                timeout=15,
                allow_redirects=True,
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.extract()
            title = soup.title.get_text(" ", strip=True) if soup.title else "Untitled"
            text = " ".join(soup.get_text(" ", strip=True).split())
            return {"title": title, "text": text[:6000]}
        except Exception as exc:
            print(f"[SearchAgent] Content extraction failed for {url}: {exc}")
            return {}

    async def _rank_sources(
        self, sources: List[Dict[str, Any]], query: str
    ) -> List[Dict[str, Any]]:
        """Ask the LLM to score each source for relevance and return sorted list."""
        # Trim content before sending to LLM to stay within token limits
        trimmed = [
            {k: (v[:800] if k == "content" else v) for k, v in s.items()}
            for s in sources
        ]
        prompt = f"""
Rank these sources by relevance to the research query.
Return ONLY a JSON array. Keep every source object and add a "relevance_score"
field (float 0–1) to each one. Do not add commentary outside the JSON array.

Query: {query}
Sources: {json.dumps(trimmed, indent=2)}
"""
        try:
            response = await self.llm.generate_content(prompt, model="flash", max_tokens=2048)
            ranked = self.llm.extract_json(response)
            if isinstance(ranked, list) and len(ranked) == len(sources):
                # Merge relevance_score back into the full (non-trimmed) source dicts
                score_map = {r.get("url"): r.get("relevance_score", 0.5) for r in ranked}
                for s in sources:
                    s["relevance_score"] = score_map.get(s["url"], 0.5)
                return sorted(sources, key=lambda x: x["relevance_score"], reverse=True)
        except Exception as exc:
            print(f"[SearchAgent] Ranking failed, using default order: {exc}")

        for s in sources:
            s.setdefault("relevance_score", 0.5)
        return sources

    @staticmethod
    def _estimate_credibility(url: str) -> float:
        trusted = [
            ".edu", ".gov", "nature.com", "science.org", "arxiv.org",
            "who.int", "mit.edu", "ieee.org", "acm.org",
        ]
        if any(domain in url.lower() for domain in trusted):
            return 0.9
        return 0.65


search_agent = SearchAgent()