# 🧠 Synthora

An AI-powered research agent built using **FastAPI**, **Streamlit**, and **Ollama Cloud API** for intelligent source gathering, summarization, fact-checking, and structured report generation.

---

## 🖼️ Output Preview

<img width="1919" height="957" alt="Screenshot 2026-05-26 180139" src="https://github.com/user-attachments/assets/6ad085ec-a6fe-48d7-8016-2c38284786a7" />


---

## 📊 Sample Output

> Add one sample generated research output here.

<img width="1906" height="964" alt="Screenshot 2026-05-26 180247" src="https://github.com/user-attachments/assets/c5fab23c-3e0a-4c26-88d2-b757fcec661b" />
<img width="1910" height="967" alt="Screenshot 2026-05-26 180237" src="https://github.com/user-attachments/assets/8833dd5a-37bb-4768-af5d-876d9a0a6d84" />
<img width="1915" height="964" alt="Screenshot 2026-05-26 180223" src="https://github.com/user-attachments/assets/6646c098-a107-444e-a010-1d45947a34a8" />
<img width="1918" height="972" alt="Screenshot 2026-05-26 180210" src="https://github.com/user-attachments/assets/f0bb54b3-3b1d-4dba-9326-8d2c61684e08" />
<img width="1916" height="964" alt="Screenshot 2026-05-26 180153" src="https://github.com/user-attachments/assets/f30d33c4-3967-4539-8f21-03ea55464d5a" />


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
