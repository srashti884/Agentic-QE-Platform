import json
import os
from typing import List, Optional
from ..models.schemas import RegressionTest

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "regression_tests.json")

class TestRepository:
    def __init__(self, filepath: str = DATA_PATH):
        self.filepath = filepath

    def get_all(self) -> List[RegressionTest]:
        if not os.path.exists(self.filepath):
            return []
        with open(self.filepath, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        return [RegressionTest(**item) for item in raw_data]

    def get_by_id(self, test_id: str) -> Optional[RegressionTest]:
        tests = self.get_all()
        for t in tests:
            if t.id == test_id:
                return t
        return None

    def get_by_service(self, service: str) -> List[RegressionTest]:
        return [t for t in self.get_all() if t.service.lower() == service.lower()]
