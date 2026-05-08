import json
import os
import glob

import streamlit as st
import requests
import time

API_BASE = "http://localhost:8000/api"
DATA_DIR = "data/projects"

st.set_page_config(page_title="Multi-Agent Research Assistant", layout="wide")

st.title("Multi-Agent Research Assistant")
st.markdown(
    "Use this Streamlit app to send research queries to the Gemini-powered research API and inspect project status and reports. "
    "You can also load saved project JSON directly from the local `data/projects/` folder."
)


def list_local_projects():
    project_files = sorted(glob.glob(os.path.join(DATA_DIR, "*.json")))
    return [os.path.basename(path) for path in project_files]


def load_local_project(filename: str):
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def render_list_section(title: str, items: list):
    st.subheader(title)
    if items:
        for item in items:
            st.markdown(f"- {item}")
    else:
        st.info(f"No {title.lower()} available.")


def render_sources(sources: list):
    st.subheader("Sources")
    if not sources:
        st.info("No sources available.")
        return

    rows = []
    for source in sources:
        rows.append({
            "Title": source.get("title", "Unknown"),
            "URL": source.get("url", ""),
            "Credibility": source.get("credibility", "N/A"),
            "Relevance": source.get("relevance_score", "N/A")
        })
    st.table(rows)

    for source in sources:
        with st.expander(source.get("title", source.get("url", "Source"))):
            st.markdown(f"**URL:** {source.get('url', '')}")
            st.markdown(f"**Credibility:** {source.get('credibility', 'N/A')}")
            content = source.get("content", "No extracted content available.")
            st.write(content)


user_id = st.text_input("User ID", value="user_001")
query = st.text_area("Research Query", value="Impact of AI agents on startup productivity")

use_local = st.checkbox("Load from local data folder instead of API")
local_project_file = None
if use_local:
    local_projects = list_local_projects()
    if local_projects:
        local_project_file = st.selectbox("Select a saved project file", local_projects)
        if st.button("Load local project"):
            project = load_local_project(local_project_file)
            if project:
                st.session_state["project"] = project
                st.session_state["project_id"] = project.get("projectId", "")
                st.success(f"Loaded local project: {local_project_file}")
            else:
                st.error("Could not load the selected local project file.")
    else:
        st.warning("No local project JSON files found in `data/projects/`.")

if st.button("Start Research") and not use_local:
    if not user_id or not query.strip():
        st.error("Please provide both a User ID and a research query.")
    else:
        try:
            response = requests.post(
                f"{API_BASE}/research",
                json={"user_id": user_id.strip(), "query": query.strip()},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            project_id = data.get("project_id")
            st.success(f"Research project started: {project_id}")
            st.session_state["project_id"] = project_id
            st.session_state["status"] = "started"
        except requests.RequestException as err:
            st.error(f"Unable to start research: {err}")

project_id = st.text_input("Project ID", value=st.session_state.get("project_id", ""))
if project_id and not use_local:
    if st.button("Refresh Project Status"):
        try:
            project_resp = requests.get(f"{API_BASE}/project/{project_id}", timeout=30)
            project_resp.raise_for_status()
            project = project_resp.json()
            st.session_state["project"] = project
            st.success(f"Project status: {project.get('status')}")
        except requests.RequestException as err:
            st.error(f"Unable to fetch project: {err}")

project = st.session_state.get("project")
if project:
    st.subheader("Project Overview")
    left, right = st.columns(2)
    with left:
        st.markdown(f"**Project ID:** {project.get('projectId', 'Unknown')}")
        st.markdown(f"**User ID:** {project.get('userId', 'Unknown')}")
        st.markdown(f"**Query:** {project.get('query', 'No query provided')}")
    with right:
        st.markdown(f"**Status:** {project.get('status', 'Unknown')}")
        st.markdown(f"**Created At:** {project.get('createdAt', project.get('_created_at', 'Unknown'))}")
        st.markdown(f"**Updated At:** {project.get('_updated_at', 'Unknown')}")

    if project.get("status") == "failed":
        st.error("Project execution failed. Check the JSON project file for details.")
        if project.get("error"):
            st.markdown(f"**Error:** {project.get('error')}")
    else:
        if project.get("status") != "completed":
            st.info("Project is still processing. Refresh again to update the status.")

        summary = project.get("summary", {})
        if summary:
            st.subheader("Summary")
            render_list_section("Key Insights", summary.get("keyInsights", []))
            render_list_section("Important Statistics", summary.get("statistics", []))
            render_list_section("Major Arguments", summary.get("arguments", []))
            render_list_section("Risks", summary.get("risks", []))
            render_list_section("Opportunities", summary.get("opportunities", []))
        else:
            st.info("Summary is not available yet.")

        render_sources(project.get("sources", []))

        fact_checks = project.get("factChecks", [])
        st.subheader("Fact Checks")
        if fact_checks:
            st.table([
                {
                    "Claim": fc.get("claim", ""),
                    "Status": fc.get("status", ""),
                    "Confidence": fc.get("confidence", ""),
                    "Sources": ", ".join(fc.get("supporting_sources", []))
                }
                for fc in fact_checks
            ])
        else:
            st.info("Fact check results are not available yet.")

        if project.get("status") == "completed":
            st.subheader("Final Report")
            st.markdown(project.get("finalReport", "No report available"))

st.markdown("---")
st.write("Backend API endpoint: `http://localhost:8000/api/research`")
