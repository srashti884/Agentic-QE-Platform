import json
import os
from typing import List, Optional
from ..models.schemas import ApiChange

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "api_changes.json")

class ChangeRepository:
    def __init__(self, filepath: str = DATA_PATH):
        self.filepath = filepath

    def get_all(self) -> List[ApiChange]:
        if os.path.exists(self.filepath):
            with open(self.filepath, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            return [ApiChange(**item) for item in raw_data]
        return []

    def get_by_id(self, change_id: str) -> Optional[ApiChange]:
        changes = self.get_all()
        for c in changes:
            if c.id == change_id:
                return c
        return None

    def add_change(self, change: ApiChange) -> ApiChange:
        changes = self.get_all()
        # Remove if exists
        changes = [c for c in changes if c.id != change.id]
        changes.append(change)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump([c.model_dump() for c in changes], f, indent=2)
        return change
