from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.openaiService import openai_service
import json
import re
    try:
        raw_output = await openai_service.generate_content(prompt, model="pro")

class ResearchRequest(BaseModel):
    query: str


def _clean_json(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        raise HTTPException(status_code=500, detail=f"OpenAI processing error: {str(exc)}")
    if text.endswith("```"):
        text = text[:-3]
    match = re.search(r"({.*}|\[.*\])", text, flags=re.S)
    return match.group(1).strip() if match else text


@router.post("/research")
async def start_research(request: ResearchRequest):
    """Process a user query and return structured research output."""
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query must not be empty")

    prompt = f"""
You are a research assistant.
Given the query below, provide a structured JSON object with the following keys:
- keyInsights: array of 3-5 concise insights
- statistics: array of extracted numeric facts, trends, or data points
- arguments: array of main viewpoints or positions
- risks: array of potential downsides or challenges
- opportunities: array of potential benefits or next steps

Return only valid JSON. Do not add extra explanation, markdown, or code fences.

Query: {query}
"""

    try:
        raw_output = await gemini_service.generate_content(prompt, model="pro")
        cleaned = _clean_json(raw_output)
        structured = json.loads(cleaned)
        if not isinstance(structured, dict):
            raise ValueError("Expected JSON object")
        return {
            "query": query,
            "raw_output": raw_output,
            "structured_output": structured,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ollama processing error: {str(exc)}")
