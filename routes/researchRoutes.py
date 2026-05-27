from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from controller import controller
from services.ollamaService import ollama_service
from utils.jsonDB import json_db

router = APIRouter(prefix="/api", tags=["research"])


class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=3)
    user_id: str = "local_user"


@router.get("/health")
async def health_check():
    try:
        ollama = await ollama_service.health_check()
        return {"status": "ok", "ollama": ollama}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("/research")
async def start_research(request: ResearchRequest):
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query must not be empty")

    try:
        project_id = await controller.process_research_request(request.user_id, query)
        project = await json_db.get_project(project_id)
        return project
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Research processing error: {exc}")


@router.get("/project/{project_id}")
async def get_project(project_id: str):
    try:
        return await json_db.get_project(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/report/{report_id}")
async def get_report(report_id: str):
    try:
        return await json_db.get_report(report_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/projects/{user_id}")
async def list_projects(user_id: str):
    return await json_db.list_user_projects(user_id)
