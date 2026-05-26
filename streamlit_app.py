import requests
import streamlit as st

st.set_page_config(
    page_title="Synthora",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Synthora")

# ======================
# BACKEND URL
# ======================

API_BASE = st.secrets["API_BASE"]

# ======================
# HEALTH CHECK
# ======================

try:
    health = requests.get(
        f"{API_BASE}/health",
        timeout=10
    )

    if health.ok:
        st.success("Backend Connected ✅")
    else:
        st.error("Backend Error")

except Exception as e:
    st.error(f"Backend not reachable:\n{e}")
    st.stop()

# ======================
# INPUT
# ======================

query = st.text_area(
    "Enter Research Query"
)

# ======================
# GENERATE
# ======================

if st.button("Generate Research"):

    if not query.strip():
        st.warning("Enter query first")

    else:

        with st.spinner("Researching..."):

            try:

                response = requests.post(
                    f"{API_BASE}/research",
                    json={
                        "query": query,
                        "user_id": "local_user"
                    },
                    timeout=300
                )

                if response.ok:

                    data = response.json()

                    st.success("Research Complete")

                    st.json(data)

                else:

                    st.error(
                        f"""
                        Backend Error:
                        {response.status_code}

                        {response.text}
                        """
                    )

            except Exception as e:

                st.error(f"Error:\n{e}")
