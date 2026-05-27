# 🧠 Synthora

An AI-powered research agent built using **FastAPI**, **Streamlit**, and **Ollama Cloud API** for intelligent source gathering, summarization, fact-checking, and structured report generation.

---

## 🖼️ Output Preview

> Add your Streamlit app screenshots here.

```text
Paste screenshot / output image here
```

---

## 📊 Sample Output

> Add one sample generated research output here.

```text
Paste generated output here
```

---

# 🚀 Features

- ☁️ Ollama Cloud API integration
- ⚡ FastAPI backend
- 🎨 Streamlit frontend
- 🔍 Multi-source research workflow
- 📚 Source ranking
- ✅ Fact-checking pipeline
- 🧾 JSON storage
- 📜 Research history
- 📄 Structured report generation

---

# 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI |
| LLM API | Ollama Cloud API |
| Storage | JSON |
| Search | DuckDuckGo Scraping |
| Language | Python |

---

# ⚙️ Installation

```bash
git clone https://github.com/QubitGaurav/AI_Research_Agent.git
cd AI_Research_Agent

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

---

# 🔑 Environment Configuration

Create `.env`

```env
OLLAMA_API_KEY=your_ollama_api_key_here
OLLAMA_BASE_URL=https://ollama.com/api
OLLAMA_MODEL=gpt-oss:120b-cloud
OLLAMA_TIMEOUT=300
```

---

# ▶️ Run Backend

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

---

# 🎨 Run Frontend

```bash
streamlit run streamlit_app.py
```

---

# 📡 API Endpoints

```http
GET /api/health
POST /api/research
GET /api/project/{project_id}
GET /api/report/{report_id}
GET /api/research/history
```

---

# 📁 JSON Storage

```text
data/projects/
data/reports/
```

---

# 👨‍💻 Author

Gaurav Sharma  
GitHub: https://github.com/QubitGaurav