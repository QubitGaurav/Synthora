import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8000/api"

st.set_page_config(
    page_title="Synthora Research Agent",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 ResearchForge")
st.caption("AI Research Agent using Ollama Cloud API + FastAPI + Streamlit")


def render_card(title, items, icon, bg_color, border_color):

    st.markdown(f"## {icon} {title}")

    if not items:
        st.warning(f"No {title.lower()} found.")
        return

    for item in items:
        st.markdown(
            f"""
            <div style="
                background-color:{bg_color};
                padding:16px;
                border-radius:14px;
                margin-bottom:12px;
                border-left:6px solid {border_color};
                box-shadow:0 2px 8px rgba(0,0,0,0.08);
            ">
                <div style="
                    font-size:16px;
                    line-height:1.7;
                ">
                    {item}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


def render_report(data):

    st.markdown("## 📊 Research Report")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Project ID",
            str(data.get("_id", "N/A"))[:12]
        )

    with col2:
        st.metric(
            "Status",
            data.get("status", "N/A")
        )

    with col3:
        st.metric(
            "Sources",
            len(data.get("sources", []))
        )

    st.divider()

    st.markdown("### 🔍 Query")
    st.info(data.get("query", "No query found"))

    summary = data.get("summary", {})

    st.divider()

    render_card(
        "Key Insights",
        summary.get("keyInsights", []),
        "⭐",
        "#eef6ff",
        "#1f77b4"
    )

    render_card(
        "Statistics",
        summary.get("statistics", []),
        "📈",
        "#f2fff2",
        "#2ca02c"
    )

    col_left, col_right = st.columns(2)

    with col_left:
        render_card(
            "Risks",
            summary.get("risks", []),
            "⚠️",
            "#fff4f4",
            "#d62728"
        )

    with col_right:
        render_card(
            "Opportunities",
            summary.get("opportunities", []),
            "🚀",
            "#f4fff4",
            "#2ca02c"
        )

    render_card(
        "Arguments",
        summary.get("arguments", []),
        "🧩",
        "#faf5ff",
        "#9467bd"
    )


def render_sources(data):

    st.markdown("## 🔗 Research Sources")

    sources = data.get("sources", [])

    if not sources:
        st.warning("No sources found.")
        return

    for index, source in enumerate(sources, start=1):

        title = source.get("title", "Untitled Source")

        with st.expander(f"{index}. {title}"):

            st.markdown("### 📝 Snippet")
            st.write(
                source.get(
                    "snippet",
                    "No snippet available"
                )
            )

            if source.get("content"):
                st.markdown("### 📄 Content")
                st.write(source.get("content"))

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Credibility",
                    source.get("credibility", "N/A")
                )

            with col2:
                st.metric(
                    "Relevance",
                    source.get("relevance_score", "N/A")
                )

            url = source.get("url", "")

            if url:
                st.markdown(f"[🌐 Open Source]({url})")


def check_backend(api_base):

    try:
        response = requests.get(
            f"{api_base}/health",
            timeout=15
        )

        return response

    except requests.RequestException as exc:
        return exc


def generate_research(api_base, query, user_id):

    response = requests.post(
        f"{api_base}/research",
        json={
            "query": query.strip(),
            "user_id": user_id.strip()
        },
        timeout=300
    )

    return response


def get_history(api_base):

    try:
        response = requests.get(
            f"{api_base}/research/history",
            timeout=30
        )

        if response.ok:
            return response.json()

        return []

    except requests.RequestException:
        return []


with st.sidebar:

    st.header("⚙️ Backend")

    api_base = st.text_input(
        "API Base URL",
        value=API_BASE
    )

    if st.button("🔍 Check Backend Health"):

        result = check_backend(api_base)

        if isinstance(result, requests.Response):

            if result.ok:
                st.success("Backend Connected")
                st.json(result.json())

            else:
                st.error(result.text)

        else:
            st.error(f"Backend not reachable: {result}")

    st.divider()

    st.markdown("### ☁️ Model")

    st.success("Using Ollama Cloud API")


query = st.text_area(
    "Research Topic / Question",
    height=180,
    placeholder="Example: How AI affects the software market?"
)

user_id = st.text_input(
    "User ID",
    value="local_user"
)


if st.button(
    "🚀 Generate Research Report",
    type="primary",
    use_container_width=True
):

    if not query.strip():

        st.error(
            "Enter a research query first."
        )

    else:

        with st.spinner(
            "Researching using Ollama Cloud API..."
        ):

            try:

                response = generate_research(
                    api_base,
                    query,
                    user_id
                )

                if not response.ok:

                    st.error(
                        f"""
                        Backend error
                        {response.status_code}:
                        {response.text}
                        """
                    )

                else:

                    data = response.json()

                    st.session_state[
                        "latest_report"
                    ] = data

                    st.success(
                        f"""
                        Research completed:
                        {data.get('_id', 'No ID')}
                        """
                    )

            except requests.RequestException as exc:

                st.error(
                    f"Unable to reach backend: {exc}"
                )


if "latest_report" in st.session_state:

    data = st.session_state["latest_report"]

    tab_report, tab_sources, tab_raw = st.tabs(
        [
            "📊 Report",
            "🔗 Sources",
            "🧾 Raw JSON"
        ]
    )

    with tab_report:
        render_report(data)

    with tab_sources:
        render_sources(data)

    with tab_raw:
        st.json(data)


st.divider()

st.markdown("## 📚 Research History")

history = get_history(api_base)

if not history:

    st.info("No research history found.")

else:

    for index, item in enumerate(history, start=1):

        title = item.get(
            "query",
            "Untitled Research"
        )

        status = item.get(
            "status",
            "N/A"
        )

        with st.expander(
            f"{index}. {title} | {status}"
        ):

            tab1, tab2, tab3 = st.tabs(
                [
                    "📊 Report",
                    "🔗 Sources",
                    "🧾 Raw JSON"
                ]
            )

            with tab1:
                render_report(item)

            with tab2:
                render_sources(item)

            with tab3:
                st.json(item)
