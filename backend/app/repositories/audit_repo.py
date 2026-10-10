import json
import os
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any
from ..models.schemas import AuditLogEntry

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "audit_trail.json")

class AuditRepository:
    def __init__(self, filepath: str = DATA_PATH):
        self.filepath = filepath

    def get_all(self) -> List[AuditLogEntry]:
        if not os.path.exists(self.filepath):
            return []
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            return [AuditLogEntry(**item) for item in raw_data]
        except Exception:
            return []

    def log_event(self, event_type: str, change_id: str, actor: str, action: str, details: Dict[str, Any]) -> AuditLogEntry:
        entries = self.get_all()
        new_entry = AuditLogEntry(
            id=f"AUDIT-{uuid.uuid4().hex[:6].upper()}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            change_id=change_id,
            actor=actor,
            action=action,
            details=details
        )
        entries.insert(0, new_entry)  # Latest first
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump([e.model_dump() for e in entries], f, indent=2)
        return new_entry
