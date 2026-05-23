import streamlit as st
import requests

API_BASE = "http://localhost:8000/api"

st.set_page_config(page_title="OpenAI Research Agent", layout="centered")
st.title("OpenAI Research Agent")
st.write("Enter a topic or research question and get a structured response from OpenAI.")

query = st.text_area("Topic / Query", value="", height=180)

if st.button("Generate"):
    if not query.strip():
        st.error("Please enter a query.")
    else:
        try:
            response = requests.post(
                f"{API_BASE}/research",
                json={"query": query.strip()},
                timeout=60,
            )
            if response.status_code == 200:
                data = response.json()
                st.subheader("Structured Output")
                st.json(data.get("structured_output", {}))
                st.subheader("Raw Model Output")
                st.code(data.get("raw_output", ""), language="text")
            else:
                st.error(f"Backend error {response.status_code}: {response.text}")
        except requests.RequestException as err:
            st.error(f"Unable to reach backend: {err}")
