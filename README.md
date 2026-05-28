# 🧠 Synthora — AI Research Agent

A fully self-contained AI research agent in a **single Streamlit file**.
No FastAPI. No separate server. No local GPU. One command to run.

Submit a research query → get ranked sources, a structured summary, fact-checked
claims, and a full downloadable markdown report — powered by the
**Ollama Cloud API** (`gpt-oss:120b-cloud`).

---

## 🖼️ Output Preview

<img width="1919" height="957" alt="Synthora UI" src="https://github.com/user-attachments/assets/6ad085ec-a6fe-48d7-8016-2c38284786a7" />

---

## 📊 Sample Output

<img width="1906" height="964" alt="Report tab" src="https://github.com/user-attachments/assets/c5fab23c-3e0a-4c26-88d2-b757fcec661b" />
<img width="1910" height="967" alt="Summary tab" src="https://github.com/user-attachments/assets/8833dd5a-37bb-4768-af5d-876d9a0a6d84" />
<img width="1915" height="964" alt="Sources tab" src="https://github.com/user-attachments/assets/6646c098-a107-444e-a010-1d45947a34a8" />
<img width="1918" height="972" alt="Fact Checks tab" src="https://github.com/user-attachments/assets/f0bb54b3-3b1d-4dba-9326-8d2c61684e08" />
<img width="1916" height="964" alt="Raw JSON tab" src="https://github.com/user-attachments/assets/f30d33c4-3967-4539-8f21-03ea55464d5a" />

---

## 🚀 Features

| Feature | Detail |
|---|---|
| ☁️ Ollama Cloud API | Direct HTTP integration — `gpt-oss:120b-cloud` or any configured model |
| 🔍 Web search | DuckDuckGo scraping with automatic redirect URL decoding |
| 📄 Content extraction | Full page text via BeautifulSoup (noise-stripped) |
| 📊 LLM source ranking | Relevance-scored (0–1) and sorted |
| 🧠 Structured summary | Key insights, statistics, arguments, risks, opportunities |
| ✅ Fact-checking | Per-claim LLM verification with confidence score + status badge |
| 📄 Report generation | Full markdown report: executive summary, findings, analysis, citations |
| ⬇️ Report download | One-click `.md` download button |
| 🎛️ Source count control | Sidebar slider — 3 to 10 sources |
| 💾 JSON persistence | Flat file storage under `data/` — no database required |
| 📚 Research history | All past reports loadable from the history panel |
| ⚡ Single file | Entire app in `streamlit_app.py` |

---

## 🏗️ Architecture

Everything runs in one Python process.
The Ollama Cloud API is called directly — no intermediate server layer.

```
streamlit_app.py
│
├── ollama_generate()       — POST to Ollama Cloud /generate
├── extract_json()          — robust JSON parser for LLM output
├── test_api_connection()   — verify API key + connectivity
│
├── search_agent()
│   ├── _ddg_search()       — DuckDuckGo HTML scrape
│   ├── _decode_ddg_url()   — decode ?uddg= redirect to real URL
│   ├── _extract_page()     — fetch + BeautifulSoup content extract
│   └── LLM ranking call    — relevance_score per source
│
├── summarize_agent()       — LLM → keyInsights/statistics/arguments/risks/opportunities
├── fact_check_agent()      — LLM per-claim: status + confidence + explanation
├── report_agent()          — LLM → full markdown report with citations
│
├── run_pipeline()          — orchestrates all stages + live progress bar
│
├── save_project()          — data/projects/project_*.json
├── save_report()           — data/reports/report_*.json
└── load_history()          — reads all project files, sorted by created_at
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| UI + App | Streamlit ≥ 1.35 |
| LLM | Ollama Cloud API (`gpt-oss:120b-cloud`) |
| Web search | DuckDuckGo HTML (no API key needed) |
| HTML parsing | BeautifulSoup4 |
| HTTP client | requests |
| Storage | JSON files (`data/projects/`, `data/reports/`) |
| Language | Python 3.11 |

**Removed from previous version:** FastAPI, Uvicorn, Pydantic, python-multipart, openai SDK, asyncio, separate backend process.

---

## ⚙️ Installation

```bash
git clone https://github.com/QubitGaurav/AI_Research_Agent.git
cd AI_Research_Agent

python -m venv venv
# Windows
venv\Scripts\activate
# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

---

## 🔑 Configuration

Copy the example and fill in your Ollama Cloud credentials:

```bash
cp .env.example .env
```

`.env`:

```env
OLLAMA_API_KEY=your_ollama_api_key_here
OLLAMA_BASE_URL=https://ollama.com/api
OLLAMA_MODEL=gpt-oss:120b-cloud
OLLAMA_TIMEOUT=300
DATA_DIR=data
```

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_API_KEY` | — | **Required.** Your Ollama Cloud API key |
| `OLLAMA_BASE_URL` | `https://ollama.com/api` | Ollama Cloud base URL |
| `OLLAMA_MODEL` | `gpt-oss:120b-cloud` | Model for all LLM calls |
| `OLLAMA_TIMEOUT` | `300` | Request timeout in seconds |
| `DATA_DIR` | `data` | Where project/report JSON files are stored |

---

## ▶️ Run

```bash
streamlit run streamlit_app.py
```

Open [http://localhost:8501](http://localhost:8501).

That's it. One process, one terminal.

---

## 🚀 Deploy to Streamlit Cloud

1. Push repo to GitHub (`.env` and `data/` are in `.gitignore` — they won't be pushed).
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app → connect your repo.
3. Under **App settings → Secrets**, paste:

```toml
OLLAMA_API_KEY  = "your_ollama_api_key_here"
OLLAMA_BASE_URL = "https://ollama.com/api"
OLLAMA_MODEL    = "gpt-oss:120b-cloud"
OLLAMA_TIMEOUT  = "300"
```

No backend deployment needed. Streamlit Cloud talks directly to Ollama Cloud.

---

## 📁 Project Structure

```
.
├── streamlit_app.py          # entire application
├── requirements.txt          # 4 dependencies
├── runtime.txt               # python-3.11
├── .env.example              # copy to .env and fill in
├── .gitignore
│
└── .streamlit/
    └── secrets.toml          # Streamlit Cloud secrets (do not commit)

data/                         # auto-created at runtime
├── projects/                 # project_<id>.json — full pipeline state
└── reports/                  # report_<id>.json  — generated reports
```

---

## 🔄 Pipeline Stages

| # | Stage | What happens |
|---|---|---|
| 1 | **Search** | DuckDuckGo HTML scrape → decode `?uddg=` redirect → fetch real page → extract body text |
| 2 | **Rank** | LLM scores each source for relevance (0–1); sorted descending |
| 3 | **Summarize** | LLM extracts key insights, statistics, arguments, risks, opportunities as JSON |
| 4 | **Fact-check** | LLM verifies each claim against source excerpts; returns status + confidence |
| 5 | **Report** | LLM writes full markdown report: executive summary → findings → analysis → citations |
| 6 | **Persist** | Project + report saved to `data/` as JSON; visible in history panel |

---

## ⚠️ Known Limitations

| Limitation | Notes |
|---|---|
| DuckDuckGo rate limiting | If you get CAPTCHA or empty results, wait a few minutes. For production volume, use a paid search API (Serper, SerpAPI). |
| Single model for all stages | All calls use `OLLAMA_MODEL`. To use different models per stage, add a `model` parameter to `ollama_generate()`. |
| No streaming | Ollama `/generate` is called with `stream: false` — the UI updates only after each full stage completes. |
| File storage not concurrent-safe | Fine for personal/single-user use. For multi-user production, replace `save_project`/`save_report` with SQLite. |
| Fact-check quality | Per-claim verification is only as good as the source content extracted. Paywalled pages return empty content. |

---

## 👨‍💻 Author

**Gaurav Sharma**
GitHub: [QubitGaurav](https://github.com/QubitGaurav)