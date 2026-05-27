"""
Synthora – Streamlit frontend.

Key fixes vs original:
1. `/research/history` → `/api/research/history`  (routes are prefixed /api)
2. `/health`           → `/api/health`
3. `/research`         → `/api/research`
4. Added rendering of `finalReport` (Markdown) – this was built by the backend
   but never displayed in the UI.
5. Fact-check results rendered with colour-coded status badges.
6. History now shows real data from the fixed endpoint.
7. Removed the `.strip()` call on user_id inside generate_research
   (it's passed as-is; strip is done in the backend).
"""

import requests
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Synthora Research Agent",
    page_icon="🧠",
    layout="wide",
)

# ─────────────────────────────────────────────────────────────────────────────
# API base URL from secrets
# ─────────────────────────────────────────────────────────────────────────────

try:
    API_BASE = st.secrets["API_BASE"].rstrip("/")
except Exception:
    st.error(
        "**API_BASE not configured.**\n\n"
        "Add this to your Streamlit secrets:\n\n"
        "```toml\nAPI_BASE = \"http://127.0.0.1:8000\"\n```"
    )
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# Backend helpers
# ─────────────────────────────────────────────────────────────────────────────

def api_get(path: str, timeout: int = 30) -> requests.Response:
    return requests.get(f"{API_BASE}{path}", timeout=timeout)


def api_post(path: str, payload: dict, timeout: int = 300) -> requests.Response:
    return requests.post(f"{API_BASE}{path}", json=payload, timeout=timeout)


def check_health() -> dict:
    try:
        resp = api_get("/api/health", timeout=10)
        if resp.ok:
            return resp.json()
        return {"status": "error", "detail": resp.text}
    except requests.RequestException as exc:
        return {"status": "unreachable", "detail": str(exc)}


def run_research(query: str, user_id: str) -> tuple[bool, dict | str]:
    try:
        resp = api_post("/api/research", {"query": query, "user_id": user_id})
        if resp.ok:
            return True, resp.json()
        return False, f"HTTP {resp.status_code}: {resp.text}"
    except requests.RequestException as exc:
        return False, str(exc)


def get_history(limit: int = 20) -> list[dict]:
    try:
        resp = api_get(f"/api/research/history?limit={limit}")
        if resp.ok:
            return resp.json()
        return []
    except requests.RequestException:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# UI helpers
# ─────────────────────────────────────────────────────────────────────────────

STATUS_COLOUR = {
    "verified": "#22c55e",
    "partially_verified": "#f59e0b",
    "contradicted": "#ef4444",
    "unverified": "#94a3b8",
}


def badge(status: str) -> str:
    colour = STATUS_COLOUR.get(status, "#94a3b8")
    label = status.replace("_", " ").title()
    return (
        f'<span style="background:{colour};color:#fff;padding:2px 8px;'
        f'border-radius:4px;font-size:0.78rem;font-weight:600">{label}</span>'
    )


def render_card_list(title: str, items: list[str], icon: str = "•") -> None:
    if not items:
        return
    st.subheader(title)
    for item in items:
        st.markdown(
            f"""<div style="padding:12px 16px;border-radius:8px;margin-bottom:8px;
            background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.1)">
            {icon} {item}</div>""",
            unsafe_allow_html=True,
        )


def render_summary(summary: dict) -> None:
    col1, col2 = st.columns(2)
    with col1:
        render_card_list("⭐ Key Insights", summary.get("keyInsights", []), "💡")
        render_card_list("📈 Statistics", summary.get("statistics", []), "📊")
        render_card_list("🧩 Arguments", summary.get("arguments", []), "💬")
    with col2:
        render_card_list("⚠️ Risks", summary.get("risks", []), "⚠️")
        render_card_list("🚀 Opportunities", summary.get("opportunities", []), "✅")


def render_fact_checks(fact_checks: list[dict]) -> None:
    st.subheader("🔎 Fact-Check Results")
    if not fact_checks:
        st.info("No fact-checks were performed.")
        return
    for fc in fact_checks:
        status = fc.get("status", "unverified")
        confidence = int(fc.get("confidence", 0) * 100)
        with st.expander(f"{fc.get('claim', 'Unknown claim')[:100]}…"):
            st.markdown(
                f"{badge(status)} &nbsp; **Confidence:** {confidence}%",
                unsafe_allow_html=True,
            )
            st.markdown(f"**Explanation:** {fc.get('explanation', 'N/A')}")
            srcs = fc.get("supporting_sources", [])
            if srcs:
                st.markdown("**Supporting sources:** " + ", ".join(srcs))


def render_sources(sources: list[dict]) -> None:
    st.subheader("🔗 Sources")
    real_sources = [s for s in sources if s.get("url") != "local://fallback"]
    if not real_sources:
        st.warning("No live sources were retrieved for this query.")
        return
    for i, s in enumerate(real_sources, 1):
        with st.expander(f"{i}. {s.get('title', 'Untitled')}"):
            cols = st.columns([3, 1, 1])
            cols[1].metric("Credibility", f"{s.get('credibility', 0):.0%}")
            cols[2].metric("Relevance", f"{s.get('relevance_score', 0):.0%}")
            snippet = s.get("content", s.get("snippet", ""))[:500]
            if snippet:
                st.caption(snippet + ("…" if len(snippet) == 500 else ""))
            st.markdown(f"[🌐 Open source]({s.get('url')})")


def render_report(data: dict) -> None:
    """Top-level renderer for a completed project."""
    # Header metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Project", str(data.get("_id", "N/A"))[-8:])
    col2.metric("Status", data.get("status", "N/A"))
    col3.metric("Sources", len(data.get("sources", [])))
    col4.metric("Fact-checks", len(data.get("factChecks", [])))

    st.divider()
    st.subheader("🔍 Query")
    st.info(data.get("query", "No query found"))

    tab_report, tab_summary, tab_fact, tab_sources, tab_raw = st.tabs(
        ["📄 Full Report", "📊 Summary", "🔎 Fact Checks", "🔗 Sources", "🧾 Raw JSON"]
    )

    with tab_report:
        final_report = data.get("finalReport", "")
        if final_report:
            st.markdown(final_report)
        else:
            st.warning(
                "Full report not yet available. "
                "The pipeline may still be running or report generation failed."
            )

    with tab_summary:
        render_summary(data.get("summary", {}))

    with tab_fact:
        render_fact_checks(data.get("factChecks", []))

    with tab_sources:
        render_sources(data.get("sources", []))

    with tab_raw:
        st.json(data)


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Configuration")
    st.code(API_BASE, language=None)

    if st.button("🔍 Check Backend Health", use_container_width=True):
        with st.spinner("Checking…"):
            health = check_health()
        status = health.get("status", "unknown")
        if status == "ok":
            st.success("✅ Backend online")
        elif status == "degraded":
            st.warning("⚠️ Backend running, Ollama unreachable")
        else:
            st.error(f"❌ {status}")
        st.json(health)

    st.divider()
    st.caption("Synthora v2.1 · FastAPI + Streamlit + Ollama")


# ─────────────────────────────────────────────────────────────────────────────
# Main UI
# ─────────────────────────────────────────────────────────────────────────────

st.title("🧠 Synthora Research Agent")
st.caption("Multi-agent pipeline: search → summarise → fact-check → report")

query = st.text_area(
    "Research Topic / Question",
    height=140,
    placeholder="E.g. How will AI affect software engineering jobs in the next 5 years?",
)

user_id = st.text_input("User ID", value="local_user")

if st.button("🚀 Generate Research Report", type="primary", use_container_width=True):
    if not query.strip():
        st.error("Please enter a research query.")
    else:
        with st.spinner("Running research pipeline… this may take 1–3 minutes."):
            ok, result = run_research(query.strip(), user_id.strip())

        if ok:
            st.session_state["latest_report"] = result
            status = result.get("status", "unknown")
            if status == "completed":
                st.success("✅ Research completed successfully.")
            else:
                st.warning(f"Pipeline finished with status: **{status}**")
                if result.get("error"):
                    st.error(result["error"])
        else:
            st.error(f"Backend error: {result}")

# ─────────────────────────────────────────────────────────────────────────────
# Report display
# ─────────────────────────────────────────────────────────────────────────────

if "latest_report" in st.session_state:
    st.divider()
    render_report(st.session_state["latest_report"])

# ─────────────────────────────────────────────────────────────────────────────
# History
# ─────────────────────────────────────────────────────────────────────────────

st.divider()
st.header("📚 Research History")

with st.spinner("Loading history…"):
    history = get_history()

if not history:
    st.info("No research history yet. Run a query above to get started.")
else:
    for i, item in enumerate(history, 1):
        status_icon = {"completed": "✅", "failed": "❌"}.get(item.get("status", ""), "⏳")
        label = f"{i}. {status_icon} {item.get('query', 'Untitled')[:80]}"
        with st.expander(label):
            cols = st.columns(3)
            cols[0].markdown(f"**User:** {item.get('userId', '—')}")
            cols[1].markdown(f"**Status:** {item.get('status', '—')}")
            cols[2].markdown(f"**Sources:** {item.get('source_count', '—')}")
            st.caption(f"Created: {item.get('_created_at', '—')}")
            if item.get("reportId"):
                if st.button(f"Load report", key=f"load_{item['_id']}"):
                    try:
                        resp = api_get(f"/api/project/{item['_id']}")
                        if resp.ok:
                            st.session_state["latest_report"] = resp.json()
                            st.rerun()
                    except Exception as exc:
                        st.error(str(exc))