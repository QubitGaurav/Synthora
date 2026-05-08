import json
import os
from pathlib import Path
from typing import Dict, Any, List
from services.storageService import storage_service

class JSONDatabase:
    def __init__(self):
        self.storage = storage_service

    async def create_project(self, user_id: str, query: str) -> str:
        """Create a new research project"""
        project_data = {
            "projectId": "",  # Will be set by storage
            "userId": user_id,
            "query": query,
            "createdAt": "",  # Will be set by storage
            "status": "pending",
            "sources": [],
            "summary": {
                "keyInsights": [],
                "risks": [],
                "opportunities": []
            },
            "factChecks": [],
            "finalReport": ""
        }
        return await self.storage.save_document("projects", project_data)

    async def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get project by ID"""
        return await self.storage.get_document("projects", project_id)

    async def update_project(self, project_id: str, updates: Dict[str, Any]):
        """Update project data"""
        await self.storage.update_document("projects", project_id, updates)

    async def create_user(self, user_data: Dict[str, Any]) -> str:
        """Create a new user"""
        return await self.storage.save_document("users", user_data)

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get user by ID"""
        return await self.storage.get_document("users", user_id)

    async def save_report(self, report_data: Dict[str, Any]) -> str:
        """Save a final report"""
        return await self.storage.save_document("reports", report_data)

    async def get_report(self, report_id: str) -> Dict[str, Any]:
        """Get report by ID"""
        return await self.storage.get_document("reports", report_id)

    async def cache_search_results(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Cache search results"""
        cache_data = {
            "query": query,
            "results": results,
            "timestamp": ""  # Will be set by storage
        }
        return await self.storage.save_document("cache", cache_data)

    async def get_cached_results(self, query: str) -> List[Dict[str, Any]]:
        """Get cached search results"""
        # Simple implementation - in real app, would need better caching logic
        cache_docs = await self.storage.list_documents("cache")
        for doc in cache_docs:
            if doc.get("query") == query:
                return doc.get("results", [])
        return []

json_db = JSONDatabase()