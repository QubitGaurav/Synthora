import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class JsonDB:
    def __init__(self, base_dir: str = "data") -> None:
        self.base = Path(base_dir)
        for folder in ["users", "projects", "reports", "cache"]:
            (self.base / folder).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    async def create_project(self, user_id: str, query: str) -> str:
        project_id = f"project_{uuid.uuid4().hex[:12]}"
        project = {
            "_id": project_id,
            "userId": user_id,
            "query": query,
            "status": "created",
            "_created_at": self._now(),
            "_updated_at": self._now(),
        }
        await self.update_project(project_id, project)
        return project_id

    async def update_project(self, project_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        path = self.base / "projects" / f"{project_id}.json"
        data: Dict[str, Any] = {}
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
        data.update(updates)
        data.setdefault("_id", project_id)
        data["_updated_at"] = self._now()
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return data

    async def get_project(self, project_id: str) -> Dict[str, Any]:
        path = self.base / "projects" / f"{project_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Project not found: {project_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    async def list_user_projects(self, user_id: str) -> List[Dict[str, Any]]:
        projects = []
        for path in (self.base / "projects").glob("*.json"):
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("userId") == user_id:
                projects.append(data)
        return sorted(projects, key=lambda item: item.get("_updated_at", ""), reverse=True)

    async def save_report(self, report_data: Dict[str, Any]) -> str:
        report_id = f"report_{uuid.uuid4().hex[:12]}"
        report_data.update({"_id": report_id, "_created_at": self._now(), "_updated_at": self._now()})
        path = self.base / "reports" / f"{report_id}.json"
        path.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding="utf-8")
        return report_id

    async def get_report(self, report_id: str) -> Dict[str, Any]:
        path = self.base / "reports" / f"{report_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Report not found: {report_id}")
        return json.loads(path.read_text(encoding="utf-8"))


json_db = JsonDB()
