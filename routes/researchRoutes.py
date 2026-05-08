from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from controller import controller
from utils.jsonDB import json_db

router = APIRouter()

class ResearchRequest(BaseModel):
    user_id: str
    query: str

class ProjectResponse(BaseModel):
    project_id: str
    status: str
    message: str

@router.post("/research", response_model=ProjectResponse)
async def start_research(request: ResearchRequest):
    """Start a new research project"""
    try:
        project_id = await controller.process_research_request(request.user_id, request.query)
        return ProjectResponse(
            project_id=project_id,
            status="started",
            message="Research project started successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start research: {str(e)}")

@router.get("/project/{project_id}")
async def get_project(project_id: str):
    """Get project status and data"""
    try:
        project = await json_db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get project: {str(e)}")

@router.get("/report/{report_id}")
async def get_report(report_id: str):
    """Get a completed research report"""
    try:
        report = await json_db.get_report(report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}")

@router.get("/projects/{user_id}")
async def get_user_projects(user_id: str):
    """Get all projects for a user"""
    try:
        projects = await json_db.storage.list_documents("projects")
        user_projects = [p for p in projects if p.get("userId") == user_id]
        return {"projects": user_projects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get projects: {str(e)}")