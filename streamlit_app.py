"""
Synthora — AI Research Agent
Single-file Streamlit application. No backend server required.

Pipeline:
  1. search_agent()      — DuckDuckGo → decode redirect URLs → extract page text → LLM rank
  2. summarize_agent()   — LLM structured JSON summary
  3. fact_check_agent()  — LLM per-claim verification with confidence score
  4. report_agent()      — LLM full markdown report with citations
  5. Persistence         — flat JSON files under data/projects/ and data/reports/

All LLM calls go directly to the Ollama Cloud /generate endpoint.
"""

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import requests
import streamlit as st
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG — must be first Streamlit call
# ──────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Synthora · AI Research Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# CONFIG — Streamlit Secrets → .env → hardcoded default
# Must come AFTER set_page_config so st.secrets is accessible
# ──────────────────────────────────────────────────────────────────────────────

def _cfg(key: str, default: str = "") -> str:
    """Read config from Streamlit Secrets first, then .env, then default."""
    try:
        val = st.secrets.get(key)
        if val:
            return str(val)
    except Exception:
        pass
    return os.getenv(key, default)


OLLAMA_API_KEY  = _cfg("OLLAMA_API_KEY")
OLLAMA_BASE_URL = _cfg("OLLAMA_BASE_URL", "https://ollama.com/api").rstrip("/")
OLLAMA_MODEL    = _cfg("OLLAMA_MODEL",    "gpt-oss:120b-cloud")
OLLAMA_TIMEOUT  = int(_cfg("OLLAMA_TIMEOUT", "300"))
DATA_DIR        = Path(_cfg("DATA_DIR", "data"))

# ──────────────────────────────────────────────────────────────────────────────
# OLLAMA CLIENT
# ──────────────────────────────────────────────────────────────────────────────

def ollama_generate(prompt: str, max_tokens: int = 2048) -> str:
    """
    POST to Ollama Cloud /generate endpoint.
    Raises on HTTP errors or missing API key.
    Streamlit is single-threaded — synchronous requests are correct here.
    """
    if not OLLAMA_API_KEY:
        raise ValueError(
            "OLLAMA_API_KEY is not set. "
            "Add it to .env (local) or Streamlit Secrets (cloud)."
        )
    payload = {
        "model":   OLLAMA_MODEL,
        "prompt":  prompt,
        "stream":  False,
        "options": {"num_predict": max_tokens},
    }
    headers = {
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "Content-Type":  "application/json",
    }
    resp = requests.post(
        f"{OLLAMA_BASE_URL}/generate",
        json=payload,
        headers=headers,
        timeout=OLLAMA_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json().get("response", "")


def extract_json(text: str) -> Any:
    """
    Robustly parse JSON from LLM output.
    Strategy 1: direct json.loads
    Strategy 2: strip markdown ```json … ``` fences then parse
    Strategy 3: regex-extract first {...} or [...] block
    Returns None if all strategies fail.
    """
    if not text:
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    stripped = re.sub(r"```(?:json)?\s*", "", text).replace("```", "").strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    return None


def test_api_connection() -> Dict[str, Any]:
    """
    Verify the Ollama Cloud API is reachable by sending a minimal prompt.
    Returns a dict with 'ok' (bool) and 'detail' (str).
    """
    try:
        result = ollama_generate("Reply with the single word: OK", max_tokens=10)
        return {"ok": True, "detail": f"Response: {result.strip()[:50]}"}
    except Exception as exc:
        return {"ok": False, "detail": str(exc)}


# ──────────────────────────────────────────────────────────────────────────────
# SEARCH AGENT
# ──────────────────────────────────────────────────────────────────────────────

def _decode_ddg_url(url: str) -> str:
    """
    DuckDuckGo wraps result links as:
        //duckduckgo.com/l/?uddg=<percent-encoded destination URL>
    Decode to the real destination. Non-DDG URLs are returned unchanged.
    """
    if not url:
        return url
    if url.startswith("//"):
        url = "https:" + url
    parsed = urlparse(url)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        uddg = parse_qs(parsed.query).get("uddg", [None])[0]
        if uddg:
            return unquote(uddg)
    return url


def _ddg_search(query: str, max_results: int) -> List[Dict]:
    """Scrape DuckDuckGo HTML results. Returns list of {title, url, snippet}."""
    search_url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    headers    = {"User-Agent": "Mozilla/5.0 (compatible; SynthoraBot/1.0)"}
    try:
        resp = requests.get(search_url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as exc:
        st.warning(f"DuckDuckGo search failed: {exc}")
        return []

    soup    = BeautifulSoup(resp.text, "html.parser")
    results = []
    for item in soup.select(".result"):
        link    = item.select_one(".result__a")
        snippet = item.select_one(".result__snippet")
        if not link:
            continue
        href  = _decode_ddg_url(link.get("href", ""))
        title = link.get_text(" ", strip=True)
        if href and title:
            results.append({
                "title":   title,
                "url":     href,
                "snippet": snippet.get_text(" ", strip=True) if snippet else "",
            })
        if len(results) >= max_results:
            break
    return results


def _extract_page(url: str) -> Dict[str, str]:
    """
    Fetch a URL and extract clean body text + page title.
    Strips script/style/nav/footer/header/aside tags.
    Truncates text to 6000 characters to keep LLM prompts manageable.
    Returns {} on any fetch or parse error.
    """
    if not url or url.startswith("local://"):
        return {}
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; SynthoraBot/1.0)"},
            timeout=15,
            allow_redirects=True,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.extract()
        title = soup.title.get_text(" ", strip=True) if soup.title else "Untitled"
        text  = " ".join(soup.get_text(" ", strip=True).split())
        return {"title": title, "text": text[:6000]}
    except Exception:
        return {}


def _estimate_credibility(url: str) -> float:
    """
    Heuristic credibility score based on domain.
    Academic / government / well-known research domains → 0.9, else 0.65.
    """
    trusted = [
        ".edu", ".gov", "nature.com", "arxiv.org", "who.int",
        "ieee.org", "acm.org", "science.org", "mit.edu", "nih.gov",
        "pubmed.ncbi", "researchgate.net",
    ]
    return 0.9 if any(d in url.lower() for d in trusted) else 0.65


def search_agent(
    query: str,
    status_placeholder,
    max_results: int = 5,
) -> List[Dict]:
    """
    Full search pipeline:
      DDG scrape → decode redirect URLs → extract page content → LLM relevance ranking
    Returns list of enriched source dicts sorted by relevance_score descending.
    """
    status_placeholder.write("🔍 Searching DuckDuckGo…")
    raw = _ddg_search(query, max_results)

    if not raw:
        return [{
            "title":          "No live sources found",
            "url":            "local://fallback",
            "snippet":        "",
            "content":        f"No live web results found for: {query}",
            "credibility":    0.2,
            "relevance_score": 0.2,
        }]

    enriched: List[Dict] = []
    for i, item in enumerate(raw):
        status_placeholder.write(
            f"📄 Extracting {i + 1}/{len(raw)}: {item['title'][:65]}…"
        )
        page           = _extract_page(item["url"])
        item["content"]     = page.get("text") or item.get("snippet", "")
        item["title"]       = page.get("title") or item["title"]
        item["credibility"] = _estimate_credibility(item["url"])
        enriched.append(item)

    # LLM relevance ranking — trim content to keep prompt small
    status_placeholder.write("📊 Ranking sources by relevance…")
    trimmed = [
        {k: (v[:400] if k == "content" else v) for k, v in s.items()}
        for s in enriched
    ]
    prompt = (
        f'Rank these sources by relevance to the research query.\n'
        f'Return ONLY a JSON array. Include every source object unchanged '
        f'and add a "relevance_score" field (float 0–1) to each one.\n'
        f'No text outside the JSON array.\n\n'
        f'Query: {query}\n'
        f'Sources:\n{json.dumps(trimmed, indent=2)}'
    )
    try:
        ranked = extract_json(ollama_generate(prompt, max_tokens=2048))
        if isinstance(ranked, list) and len(ranked) == len(enriched):
            score_map = {r.get("url"): r.get("relevance_score", 0.5) for r in ranked}
            for s in enriched:
                s["relevance_score"] = score_map.get(s["url"], 0.5)
            return sorted(enriched, key=lambda x: x["relevance_score"], reverse=True)
    except Exception:
        pass

    for s in enriched:
        s.setdefault("relevance_score", 0.5)
    return enriched


# ──────────────────────────────────────────────────────────────────────────────
# SUMMARIZE AGENT
# ──────────────────────────────────────────────────────────────────────────────

_SUMMARY_KEYS = ["keyInsights", "statistics", "arguments", "risks", "opportunities"]


def summarize_agent(sources: List[Dict], query: str) -> Dict:
    """
    Send source content to the LLM and extract a structured JSON summary.
    Falls back to an error dict if the LLM call or JSON parse fails.
    """
    combined = "\n\n".join(
        f"Source: {s.get('title', 'Unknown')}\n"
        f"URL: {s.get('url', '')}\n"
        f"{s.get('content', '')[:2500]}"
        for s in sources
    )
    prompt = (
        f'You are a strict research summarizer.\n'
        f'Analyze the following sources for this query: "{query}"\n\n'
        f'Sources:\n{combined[:15000]}\n\n'
        f'Return ONLY valid JSON (no markdown fences, no commentary) '
        f'with exactly these keys:\n'
        f'  keyInsights   — array of 3–5 concise insight strings\n'
        f'  statistics    — array of strings with numbers/percentages where available\n'
        f'  arguments     — array of key argument strings\n'
        f'  risks         — array of risk strings\n'
        f'  opportunities — array of opportunity strings\n'
    )
    try:
        data = extract_json(ollama_generate(prompt, max_tokens=2048))
        if isinstance(data, dict):
            return {k: data.get(k, []) for k in _SUMMARY_KEYS}
        raise ValueError(f"LLM returned {type(data).__name__}, expected dict")
    except Exception as exc:
        return {
            "keyInsights":   ["Summarization failed — check model availability."],
            "statistics":    [],
            "arguments":     [],
            "risks":         [str(exc)],
            "opportunities": ["Verify OLLAMA_API_KEY and OLLAMA_MODEL, then retry."],
        }


# ──────────────────────────────────────────────────────────────────────────────
# FACT CHECK AGENT
# ──────────────────────────────────────────────────────────────────────────────

_VALID_STATUSES = {"verified", "partially_verified", "contradicted", "unverified"}
_MAX_CLAIMS     = 8
_MAX_EVIDENCE   = 1200  # chars per source for fact-check prompt


def fact_check_agent(sources: List[Dict], summary: Dict) -> List[Dict]:
    """
    Verify up to _MAX_CLAIMS claims from the summary against the source excerpts.
    Each claim is sent to the LLM individually to keep prompts focused.
    """
    claims: List[str] = []
    for key in _SUMMARY_KEYS:
        claims.extend(summary.get(key, []))
    # Filter trivial/error strings and cap count
    claims = [c for c in claims if isinstance(c, str) and len(c) > 15][:_MAX_CLAIMS]

    results: List[Dict] = []
    for claim in claims:
        evidence = [
            {
                "title":   s.get("title"),
                "url":     s.get("url"),
                "content": s.get("content", "")[:_MAX_EVIDENCE],
            }
            for s in sources
        ]
        prompt = (
            f'Verify the following claim using ONLY the provided source excerpts.\n'
            f'Return ONLY valid JSON with these exact keys:\n'
            f'  claim              — the claim text (string)\n'
            f'  status             — one of: verified | partially_verified | contradicted | unverified\n'
            f'  confidence         — float between 0 and 1\n'
            f'  supporting_sources — array of URLs that support the claim\n'
            f'  explanation        — one sentence explaining the verdict\n\n'
            f'Claim: {claim}\n'
            f'Sources:\n{json.dumps(evidence, indent=2)}'
        )
        try:
            data = extract_json(ollama_generate(prompt, max_tokens=1024))
            if isinstance(data, dict):
                data["claim"] = claim  # always use original claim text
                data.setdefault("supporting_sources", [])
                data.setdefault("confidence", 0.5)
                if data.get("status") not in _VALID_STATUSES:
                    data["status"] = "unverified"
                results.append(data)
                continue
        except Exception:
            pass

        results.append({
            "claim":              claim,
            "status":             "unverified",
            "confidence":         0.1,
            "supporting_sources": [],
            "explanation":        "Model verification failed or evidence was insufficient.",
        })

    return results


# ──────────────────────────────────────────────────────────────────────────────
# REPORT AGENT
# ──────────────────────────────────────────────────────────────────────────────

def report_agent(
    query: str,
    sources: List[Dict],
    summary: Dict,
    fact_checks: List[Dict],
) -> str:
    """
    Generate a full markdown research report.
    Returns a fallback error report string if the LLM call fails.
    """
    source_list = [
        {
            "title":          s.get("title"),
            "url":            s.get("url"),
            "credibility":    s.get("credibility"),
            "relevance_score": s.get("relevance_score"),
        }
        for s in sources
    ]
    prompt = (
        f'You are a professional research report writer.\n'
        f'Write a polished Markdown research report. '
        f'Be objective and do not fabricate facts. '
        f'Use only the data provided below.\n\n'
        f'Research query: {query}\n'
        f'Summary:\n{json.dumps(summary, indent=2)}\n\n'
        f'Fact checks:\n{json.dumps(fact_checks, indent=2)}\n\n'
        f'Sources:\n{json.dumps(source_list, indent=2)}\n\n'
        f'Use this exact heading structure:\n'
        f'# Research Report: {query}\n'
        f'## Executive Summary\n'
        f'## Key Findings\n'
        f'## Detailed Analysis\n'
        f'## Risks and Opportunities\n'
        f'## Fact-Checking Results\n'
        f'## Sources and References\n\n'
        f'Cite each source by title with a markdown link to its URL. '
        f'Keep the report concise and professional.'
    )
    try:
        return ollama_generate(prompt, max_tokens=3000)
    except Exception as exc:
        source_lines = "\n".join(
            f"- [{s.get('title', 'Unknown')}]({s.get('url', '')})"
            for s in sources
        )
        return (
            f"# Research Report: {query}\n\n"
            f"## Status\nReport generation failed — check model availability.\n\n"
            f"## Error\n```\n{exc}\n```\n\n"
            f"## Sources Collected\n{source_lines}\n"
        )


# ──────────────────────────────────────────────────────────────────────────────
# JSON PERSISTENCE
# ──────────────────────────────────────────────────────────────────────────────

for _d in ["projects", "reports"]:
    (DATA_DIR / _d).mkdir(parents=True, exist_ok=True)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_project(data: Dict) -> str:
    """Persist a project dict to data/projects/<id>.json. Returns the project ID."""
    pid = f"project_{uuid.uuid4().hex[:12]}"
    record = {
        **data,
        "_id":         pid,
        "_created_at": _now(),
        "_updated_at": _now(),
    }
    (DATA_DIR / "projects" / f"{pid}.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return pid


def save_report(data: Dict) -> str:
    """Persist a report dict to data/reports/<id>.json. Returns the report ID."""
    rid = f"report_{uuid.uuid4().hex[:12]}"
    record = {
        **data,
        "_id":         rid,
        "_created_at": _now(),
        "_updated_at": _now(),
    }
    (DATA_DIR / "reports" / f"{rid}.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return rid


def load_history(limit: int = 30) -> List[Dict]:
    """Return the most recently created projects across all users."""
    projects: List[Dict] = []
    for p in (DATA_DIR / "projects").glob("*.json"):
        try:
            projects.append(json.loads(p.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            continue
    return sorted(projects, key=lambda x: x.get("_created_at", ""), reverse=True)[:limit]


# ──────────────────────────────────────────────────────────────────────────────
# PIPELINE ORCHESTRATOR
# ──────────────────────────────────────────────────────────────────────────────

def run_pipeline(query: str, user_id: str, max_sources: int = 5) -> Dict:
    """
    Run all four pipeline stages with live Streamlit progress feedback.
    Persists the result and returns the complete project dict.
    """
    progress = st.progress(0, text="Starting pipeline…")
    status   = st.empty()

    try:
        # Stage 1 — Search
        sources = search_agent(query, status, max_results=max_sources)
        progress.progress(20, text="✅ Sources gathered")

        # Stage 2 — Summarize
        status.write("🧠 Summarizing sources…")
        summary = summarize_agent(sources, query)
        progress.progress(45, text="✅ Summary complete")

        # Stage 3 — Fact check
        status.write("✅ Fact-checking claims…")
        fact_checks = fact_check_agent(sources, summary)
        progress.progress(70, text="✅ Fact checks complete")

        # Stage 4 — Report
        status.write("📄 Generating final report…")
        final_report = report_agent(query, sources, summary, fact_checks)
        progress.progress(88, text="✅ Report generated")

        # Stage 5 — Persist
        status.write("💾 Saving results…")
        project = {
            "userId":       user_id,
            "query":        query,
            "status":       "completed",
            "sources":      sources,
            "summary":      summary,
            "factChecks":   fact_checks,
            "finalReport":  final_report,
        }
        pid = save_project(project)
        rid = save_report({
            "projectId":   pid,
            "query":       query,
            "report":      final_report,
            "sources":     sources,
            "summary":     summary,
            "factChecks":  fact_checks,
        })
        project["_id"]      = pid
        project["reportId"] = rid

        progress.progress(100, text="🎉 Research complete!")

    finally:
        status.empty()
        progress.empty()

    return project


# ──────────────────────────────────────────────────────────────────────────────
# UI RENDER HELPERS
# ──────────────────────────────────────────────────────────────────────────────

_STATUS_ICON: Dict[str, str] = {
    "completed":        "🟢",
    "failed":           "🔴",
    "searching":        "🟡",
    "summarizing":      "🟡",
    "fact_checking":    "🟡",
    "generating_report":"🟡",
    "created":          "⚪",
}

_FC_ICON: Dict[str, str] = {
    "verified":           "✅",
    "partially_verified": "🔶",
    "contradicted":       "❌",
    "unverified":         "❓",
}


def _badge(status: str) -> str:
    return f"{_STATUS_ICON.get(status, '⚪')} {status}"


def _card(text: str, icon: str = "•") -> None:
    st.markdown(
        f'<div style="padding:12px 16px;border-radius:8px;margin-bottom:8px;'
        f'border:1px solid rgba(128,128,128,0.25);'
        f'background:rgba(128,128,128,0.04);line-height:1.5">'
        f'{icon}&nbsp; {text}</div>',
        unsafe_allow_html=True,
    )


def render_report(data: Dict) -> None:
    md = data.get("finalReport", "")
    if not md:
        st.info("No report generated yet.")
        return
    # Detect failure report
    if "Report generation failed" in md and "## Key Findings" not in md:
        st.error("Report generation failed — model may be unavailable. See Summary tab for data.")
        with st.expander("Error details"):
            st.code(md)
        return
    st.markdown(md)
    st.download_button(
        label="⬇️ Download report (.md)",
        data=md.encode("utf-8"),
        file_name=f"synthora_report_{data.get('_id','unknown')}.md",
        mime="text/markdown",
    )


def render_summary(data: Dict) -> None:
    summary = data.get("summary", {})
    if not summary:
        st.warning("No summary available.")
        return

    c1, c2 = st.columns(2)
    with c1:
        insights = summary.get("keyInsights", [])
        if insights:
            st.subheader("⭐ Key Insights")
            for item in insights:
                _card(item, "💡")

        risks = summary.get("risks", [])
        if risks:
            st.subheader("⚠️ Risks")
            for item in risks:
                _card(item, "⚠️")

    with c2:
        stats = summary.get("statistics", [])
        if stats:
            st.subheader("📈 Statistics")
            for item in stats:
                _card(item, "📊")

        opps = summary.get("opportunities", [])
        if opps:
            st.subheader("🚀 Opportunities")
            for item in opps:
                _card(item, "🚀")

    args = summary.get("arguments", [])
    if args:
        st.subheader("🧩 Arguments")
        for item in args:
            _card(item, "→")


def render_fact_checks(data: Dict) -> None:
    checks = data.get("factChecks", [])
    if not checks:
        st.info("No fact checks available.")
        return

    # Summary counts
    counts: Dict[str, int] = {}
    for fc in checks:
        counts[fc.get("status", "unverified")] = counts.get(fc.get("status", "unverified"), 0) + 1

    cols = st.columns(len(counts))
    for col, (status, count) in zip(cols, counts.items()):
        col.metric(f"{_FC_ICON.get(status, '❓')} {status}", count)

    st.divider()

    for fc in checks:
        icon = _FC_ICON.get(fc.get("status", "unverified"), "❓")
        label = fc.get("claim", "")[:100]
        with st.expander(f"{icon} {label}"):
            conf = fc.get("confidence", 0)
            st.markdown(
                f"**Status:** `{fc.get('status')}` &nbsp;|&nbsp; "
                f"**Confidence:** {conf:.0%}"
            )
            if fc.get("explanation"):
                st.write(fc["explanation"])
            srcs = fc.get("supporting_sources", [])
            if srcs:
                st.markdown("**Supporting sources:**")
                for src in srcs:
                    st.markdown(f"- {src}")


def render_sources(data: Dict) -> None:
    sources = data.get("sources", [])
    if not sources:
        st.warning("No sources found.")
        return

    for i, s in enumerate(sources, 1):
        cred = s.get("credibility",    0.0)
        rel  = s.get("relevance_score", 0.0)
        with st.expander(f"{i}. {s.get('title', 'Untitled')}"):
            c1, c2 = st.columns(2)
            c1.metric("Credibility", f"{cred:.0%}")
            c2.metric("Relevance",   f"{rel:.0%}")
            preview = (s.get("snippet") or s.get("content", ""))[:400]
            if preview:
                st.write(preview)
            url = s.get("url", "")
            if url and not url.startswith("local://"):
                st.markdown(f"[🌐 Open source]({url})")


# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("🧠 Synthora")
    st.caption("AI Research Agent")
    st.divider()

    # Config status
    key_ok = bool(OLLAMA_API_KEY)
    st.markdown("**Configuration**")
    st.markdown(f"{'🟢' if key_ok else '🔴'} API Key: `{'set' if key_ok else 'MISSING'}`")
    st.markdown(f"🤖 Model: `{OLLAMA_MODEL}`")
    st.markdown(f"🌐 Endpoint: `{OLLAMA_BASE_URL}`")

    if not key_ok:
        st.error("OLLAMA_API_KEY is missing. Add it to `.env` or Streamlit Secrets.")

    st.divider()

    if st.button("🔍 Test API connection", use_container_width=True):
        with st.spinner("Testing…"):
            result = test_api_connection()
            if result["ok"]:
                st.success(f"Connected · {result['detail']}")
            else:
                st.error(f"Failed: {result['detail']}")

    st.divider()
    st.markdown("**Pipeline**")
    st.markdown(
        "1. 🔍 DuckDuckGo search\n"
        "2. 📄 Page content extraction\n"
        "3. 📊 LLM source ranking\n"
        "4. 🧠 LLM summarization\n"
        "5. ✅ LLM fact-checking\n"
        "6. 📄 LLM report generation\n"
        "7. 💾 JSON persistence"
    )

    st.divider()
    st.markdown("**Settings**")
    max_sources = st.slider(
        "Max sources to fetch",
        min_value=3,
        max_value=10,
        value=5,
        help="More sources = better coverage but slower pipeline",
    )

# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

st.title("🧠 Synthora Research Agent")
st.caption("Search → Summarise → Fact-check → Report · Powered by Ollama Cloud")

if "user_id" not in st.session_state:
    st.session_state.user_id = "local_user"

col_q, col_u = st.columns([4, 1])
with col_q:
    query = st.text_area(
        "Research query",
        height=120,
        placeholder="e.g. Impact of AI on software engineering jobs in 2025",
    )
with col_u:
    st.session_state.user_id = st.text_input(
        "User ID", value=st.session_state.user_id
    )

if st.button(
    "🚀 Generate Research Report",
    type="primary",
    use_container_width=True,
    disabled=not key_ok,
):
    if not query.strip():
        st.error("Please enter a research query.")
    else:
        try:
            result = run_pipeline(
                query.strip(),
                st.session_state.user_id,
                max_sources=max_sources,
            )
            st.session_state.latest_report = result
            # Refresh history so new entry appears immediately
            st.session_state.history = load_history()
            st.success(f"Research complete · Project `{result['_id']}`")
        except Exception as exc:
            st.error(f"Pipeline failed: {exc}")

# ──────────────────────────────────────────────────────────────────────────────
# RESULTS
# ──────────────────────────────────────────────────────────────────────────────

if "latest_report" in st.session_state:
    data = st.session_state.latest_report
    st.divider()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Project ID",  str(data.get("_id", "—"))[-12:])
    m2.metric("Status",      _badge(data.get("status", "—")))
    m3.metric("Sources",     len(data.get("sources",    [])))
    m4.metric("Fact Checks", len(data.get("factChecks", [])))
    st.info(f"**Query:** {data.get('query', '—')}")

    t1, t2, t3, t4, t5 = st.tabs([
        "📄 Report",
        "📊 Summary",
        "✅ Fact Checks",
        "🔗 Sources",
        "🧾 Raw JSON",
    ])
    with t1: render_report(data)
    with t2: render_summary(data)
    with t3: render_fact_checks(data)
    with t4: render_sources(data)
    with t5: st.json(data)

# ──────────────────────────────────────────────────────────────────────────────
# HISTORY
# ──────────────────────────────────────────────────────────────────────────────

st.divider()
st.header("📚 Research History")

col_r, col_clear = st.columns([1, 5])
with col_r:
    if st.button("🔄 Refresh"):
        st.session_state.history = load_history()

if "history" not in st.session_state:
    st.session_state.history = load_history()

history: List[Dict] = st.session_state.history

if not history:
    st.info("No history yet. Run a query above to get started.")
else:
    for i, item in enumerate(history, 1):
        status = item.get("status", "unknown")
        with st.expander(
            f"{i}. {item.get('query', 'Untitled')} — {_badge(status)}"
        ):
            hc1, hc2 = st.columns(2)
            hc1.write(f"**User:** {item.get('userId', '—')}")
            hc2.write(f"**Created:** {item.get('_created_at', '—')[:19]}")
            if item.get("reportId"):
                st.markdown(f"Report ID: `{item['reportId']}`")
            if st.button("Load report", key=f"load_{item.get('_id', i)}"):
                st.session_state.latest_report = item
                st.rerun()