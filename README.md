# Multi-Agent Research Assistant

A sophisticated AI research assistant powered by Google's Gemini AI and a multi-agent architecture with JSON storage.

## Overview

This project implements a multi-agent research system that:
- Accepts user research queries
- Uses specialized agents for different research tasks
- Leverages Gemini 2.5 Pro and Flash models for optimal performance
- Stores all data in JSON format for transparency and debugging
- Provides REST API endpoints for research operations

## Features

- **Multi-Agent Architecture**: Separate agents for search, summarization, fact-checking, and report generation
- **Gemini AI Integration**: Uses Gemini 2.5 Pro for complex tasks and Flash for fast operations
- **JSON Storage**: Fast, transparent data storage with no database overhead
- **REST API**: FastAPI-based backend with comprehensive endpoints
- **Source Ranking**: Intelligent ranking of research sources by relevance
- **Fact-Checking**: Automated verification of claims against multiple sources
- **Professional Reports**: AI-generated comprehensive research reports

## Architecture

```
User Query
   ↓
Controller
   ↓
├── Search Agent (Web scraping, content extraction)
├── Summarization Agent (Gemini Pro - insights, themes)
├── Fact-Check Agent (Cross-reference verification)
└── Report Agent (Final report generation)
   ↓
JSON Storage (projects/, reports/, users/, cache/)
   ↓
Frontend/Dashboard
```

## Tech Stack

- **Backend**: Python + FastAPI
- **AI**: Google Gemini 2.5 Pro + Gemini Flash
- **Storage**: JSON files (MVP approach)
- **Web Scraping**: BeautifulSoup + newspaper3k
- **Data**: Pydantic models

## Project Structure

```
AI_Research_Agent/
├── main.py                 # FastAPI application entry point
├── controller.py           # Main orchestration logic
├── requirements.txt        # Python dependencies
├── README.md              # Project documentation
├── agents/
│   ├── searchAgent.py     # Web search and content extraction
│   ├── summarizeAgent.py  # Content summarization
│   ├── factCheckAgent.py  # Claim verification
│   └── reportAgent.py     # Report generation
├── services/
│   ├── geminiService.py   # Gemini AI integration
│   └── storageService.py  # JSON storage operations
├── routes/
│   └── researchRoutes.py  # FastAPI route handlers
├── utils/
│   └── jsonDB.py          # Database abstraction layer
└── data/
    ├── users/             # User data
    ├── projects/          # Research projects
    ├── reports/           # Generated reports
    └── cache/             # Search result caching
```

## Installation

### Prerequisites
- Python 3.10+
- Google Gemini API key

### Setup

1. Clone or download the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your Gemini API key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

4. Run the application:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Start Research
```http
POST /api/research
Content-Type: application/json

{
  "user_id": "user_001",
  "query": "Impact of AI agents on startup productivity"
}
```

### Get Project Status
```http
GET /api/project/{project_id}
```

### Get Research Report
```http
GET /api/report/{report_id}
```

### Get User Projects
```http
GET /api/projects/{user_id}
```

## Streamlit Frontend

A Streamlit frontend is included for easy local use. Start the backend API first, then run the Streamlit app:

```bash
python main.py
```

In a separate terminal:

```bash
streamlit run streamlit_app.py
```

The Streamlit interface lets you:
- submit a research query
- monitor project status
- view final report content, summary, sources, and fact checks

The app is configured to call the local API at `http://localhost:8000/api`.

## Usage Example

```python
import requests

# Start research
response = requests.post("http://localhost:8000/api/research", json={
    "user_id": "user_001",
    "query": "How are AI agents transforming business operations?"
})

project_id = response.json()["project_id"]

# Check status
status = requests.get(f"http://localhost:8000/api/project/{project_id}")
print(status.json())
```

## Configuration

The system uses environment variables for configuration:
- `GEMINI_API_KEY`: Your Google Gemini API key

## Development

### Adding New Agents
1. Create a new agent class in `agents/`
2. Implement the required methods
3. Update the `controller.py` to include the new agent
4. Add any necessary routes in `routes/`

### Extending Storage
The JSON storage system is designed for easy migration. When ready to scale:
1. PostgreSQL for relational data
2. MongoDB for document storage
3. Vector database for semantic search

## License

This project is open source. See LICENSE file for details.

## Usage

Run the AI research agent:
```bash
python main.py
```

When prompted, enter your research query:
```
What can i help you research? What are the latest developments in quantum computing?
```

### Output Format

The agent returns a structured response containing:
- **topic**: The research topic
- **summary**: Comprehensive summary of findings
- **sources**: List of sources consulted
- **tools_used**: Tools leveraged for the research (search, wiki, save)

### Example Output

```json
{
  "topic": "Quantum Computing Developments",
  "summary": "Recent breakthroughs in quantum computing include...",
  "sources": ["https://example.com", "Wikipedia: Quantum Computing"],
  "tools_used": ["search", "wiki", "save_text_to_file"]
}
```

## Tools Available

### 1. Web Search Tool
- **Provider**: DuckDuckGo
- **Function**: Searches the internet for current information
- **Use Case**: Finding latest news, articles, and web resources

### 2. Wikipedia Tool
- **Provider**: Wikipedia API
- **Function**: Queries Wikipedia for comprehensive topic information
- **Configuration**: Returns top 1 result with up to 100 characters of content
- **Use Case**: Getting structured, reliable background information

### 3. Save Tool
- **Function**: Persists research output to `research_output.txt`
- **Features**: Automatic timestamping, append mode for multiple queries
- **Use Case**: Building a research archive

## Dependencies

- **langchain**: Framework for building LLM applications
- **langchain-anthropic**: Anthropic Claude integration for LangChain
- **langchain-community**: Community tools and integrations
- **langchain-core**: Core LangChain functionality
- **pydantic**: Data validation and serialization
- **python-dotenv**: Environment variable management
- **duckduckgo-search**: Web search functionality
- **wikipedia**: Wikipedia API wrapper
- **langgraph**: Graph-based LLM orchestration

## Configuration

The agent is preconfigured with:
- **Model**: Claude 3.5 Sonnet (claude-3-5-sonnet-20241022)
- **Parser**: Pydantic-based output validation
- **Verbosity**: Enabled for debugging and monitoring

## Output Storage

Research results are automatically saved to `research_output.txt` with:
- Timestamp of when the research was conducted
- Full research output
- Append mode to maintain research history

## Error Handling

The application includes robust error handling:
- JSON parsing failures default to raw response output
- Tool execution errors are caught and reported
- Invalid queries are handled gracefully

## Requirements

See `requirements.txt` for the complete list of dependencies and their versions.

## Notes

- Ensure your Anthropic API key has sufficient quota
- Internet connection required for web search and Wikipedia queries
- Research outputs accumulate in `research_output.txt`; consider archiving or clearing periodically

## Future Enhancements

Potential improvements:
- Support for additional search providers
- Custom knowledge base integration
- Advanced query preprocessing and understanding
- Multi-query research workflows
- Result summarization and comparison
