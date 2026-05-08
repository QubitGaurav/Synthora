import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class StorageService:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def _get_file_path(self, collection: str, id: str) -> Path:
        """Get file path for a document"""
        return self.data_dir / collection / f"{id}.json"

    def _ensure_collection_dir(self, collection: str):
        """Ensure collection directory exists"""
        (self.data_dir / collection).mkdir(exist_ok=True)

    async def save_document(self, collection: str, document: Dict[str, Any], id: Optional[str] = None) -> str:
        """Save a document to JSON file"""
        if id is None:
            id = str(uuid.uuid4())

        self._ensure_collection_dir(collection)
        file_path = self._get_file_path(collection, id)

        # Add metadata
        document["_id"] = id
        document["_created_at"] = datetime.now().isoformat()
        document["_updated_at"] = datetime.now().isoformat()

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(document, f, indent=2, ensure_ascii=False)

        return id

    async def get_document(self, collection: str, id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID"""
        file_path = self._get_file_path(collection, id)
        if not file_path.exists():
            return None

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    async def update_document(self, collection: str, id: str, updates: Dict[str, Any]) -> bool:
        """Update a document"""
        document = await self.get_document(collection, id)
        if not document:
            return False

        document.update(updates)
        document["_updated_at"] = datetime.now().isoformat()

        file_path = self._get_file_path(collection, id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(document, f, indent=2, ensure_ascii=False)

        return True

    async def list_documents(self, collection: str) -> List[Dict[str, Any]]:
        """List all documents in a collection"""
        collection_dir = self.data_dir / collection
        if not collection_dir.exists():
            return []

        documents = []
        for file_path in collection_dir.glob("*.json"):
            with open(file_path, 'r', encoding='utf-8') as f:
                documents.append(json.load(f))

        return documents

    async def delete_document(self, collection: str, id: str) -> bool:
        """Delete a document"""
        file_path = self._get_file_path(collection, id)
        if not file_path.exists():
            return False

        file_path.unlink()
        return True

storage_service = StorageService()