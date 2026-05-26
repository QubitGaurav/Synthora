import requests
import streamlit as st

# ==============================
# STREAMLIT CONFIG
# ==============================

st.set_page_config(
    page_title="Synthora Research Agent",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Synthora Research Agent")
st.caption("AI Research Agent using FastAPI + Streamlit")


# ==============================
# SECRETS
# ==============================

try:
    API_BASE = st.secrets["API_BASE"]

except Exception:

    st.error("""
    API_BASE not found.

    Add this inside Streamlit Secrets:

    API_BASE = "https://synthora-ynr2.onrender.com"
    """)

    st.stop()


# ==============================
# BACKEND FUNCTIONS
# ==============================

def check_backend():

    try:

        response = requests.get(
            f"{API_BASE}/health",
            timeout=15
        )

        return response

    except requests.RequestException as exc:

        return exc


def generate_research(query, user_id):

    response = requests.post(
        f"{API_BASE}/research",
        json={
            "query": query.strip(),
            "user_id": user_id.strip()
        },
        timeout=300
    )

    return response


def get_history():

    try:

        response = requests.get(
            f"{API_BASE}/research/history",
            timeout=30
        )

        if response.ok:
            return response.json()

        return []

    except requests.RequestException:

        return []


# ==============================
# UI HELPERS
# ==============================

def render_card(title, items):

    st.subheader(title)

    if not items:

        st.warning(f"No {title.lower()} found.")
        return

    for item in items:

        st.markdown(
            f"""
            <div style="
                padding:16px;
                border-radius:12px;
                margin-bottom:10px;
                border:1px solid #ddd;
            ">
                {item}
            </div>
            """,
            unsafe_allow_html=True
        )


def render_report(data):

    st.header("📊 Research Report")

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

    st.subheader("🔍 Query")
    st.info(data.get("query", "No query found"))

    summary = data.get("summary", {})

    render_card(
        "⭐ Key Insights",
        summary.get("keyInsights", [])
    )

    render_card(
        "📈 Statistics",
        summary.get("statistics", [])
    )

    render_card(
        "⚠️ Risks",
        summary.get("risks", [])
    )

    render_card(
        "🚀 Opportunities",
        summary.get("opportunities", [])
    )

    render_card(
        "🧩 Arguments",
        summary.get("arguments", [])
    )


def render_sources(data):

    st.header("🔗 Sources")

    sources = data.get("sources", [])

    if not sources:

        st.warning("No sources found.")
        return

    for index, source in enumerate(sources, start=1):

        with st.expander(
            f"{index}. {source.get('title', 'Untitled')}"
        ):

            st.write(
                source.get(
                    "snippet",
                    "No snippet available"
                )
            )

            if source.get("url"):

                st.markdown(
                    f"[🌐 Open Source]({source.get('url')})"
                )


# ==============================
# SIDEBAR
# ==============================

with st.sidebar:

    st.header("⚙️ Backend")

    st.success("Backend Configured")

    if st.button("🔍 Check Backend Health"):

        result = check_backend()

        if isinstance(result, requests.Response):

            if result.ok:

                st.success("Backend Connected")

                st.json(result.json())

            else:

                st.error(result.text)

        else:

            st.error(
                f"Backend not reachable:\n{result}"
            )


# ==============================
# MAIN INPUTS
# ==============================

query = st.text_area(
    "Research Topic / Question",
    height=180,
    placeholder="""
Example:
How AI will affect software jobs in next 5 years?
"""
)

user_id = st.text_input(
    "User ID",
    value="local_user"
)


# ==============================
# GENERATE REPORT
# ==============================

if st.button(
    "🚀 Generate Research Report",
    type="primary",
    use_container_width=True
):

    if not query.strip():

        st.error(
            "Please enter a research query."
        )

    else:

        with st.spinner(
            "Researching..."
        ):

            try:

                response = generate_research(
                    query,
                    user_id
                )

                if not response.ok:

                    st.error(
                        f"""
                        Backend Error:
                        {response.status_code}

                        {response.text}
                        """
                    )

                else:

                    data = response.json()

                    st.session_state[
                        "latest_report"
                    ] = data

                    st.success(
                        "Research Completed Successfully"
                    )

            except requests.RequestException as exc:

                st.error(
                    f"Unable to connect backend:\n{exc}"
                )


# ==============================
# SHOW REPORT
# ==============================

if "latest_report" in st.session_state:

    data = st.session_state["latest_report"]

    tab1, tab2, tab3 = st.tabs(
        [
            "📊 Report",
            "🔗 Sources",
            "🧾 Raw JSON"
        ]
    )

    with tab1:
        render_report(data)

    with tab2:
        render_sources(data)

    with tab3:
        st.json(data)


# ==============================
# HISTORY
# ==============================

st.divider()

st.header("📚 Research History")

history = get_history()

if not history:

    st.info("No history found.")

else:

    for index, item in enumerate(history, start=1):

        with st.expander(
            f"{index}. {item.get('query', 'Untitled')}"
        ):

            st.json(item)
