from typing import List, Dict, Any
from .base import BaseAgent
from ..models.schemas import PrioritizedTest, ApiChange

class ExplainabilityAgent(BaseAgent):
    """
    Agent: Explainability Agent
    Purpose: Provides transparent, rule-based mathematical justification for prioritized test suites.
    PACTS Principle: Transparent + Purposeful
    """
    def __init__(self):
        super().__init__(
            name="Explainability Agent",
            capability="Deterministic Transparent Factor Attribution",
            pacts_principle="Transparent + Purposeful"
        )

    def execute(self, change: ApiChange, tests: List[PrioritizedTest]) -> Dict[str, Any]:
        """
        Produces suite-level and test-level transparent rationales.
        """
        high_tests = [t for t in tests if t.priority == "High"]
        med_tests = [t for t in tests if t.priority == "Medium"]
        low_tests = [t for t in tests if t.priority == "Low"]

        key_drivers = []
        if change.is_breaking:
            key_drivers.append("Breaking API contract change detected (+7-10 pts across integration tests)")
        if change.business_criticality == "Critical":
            key_drivers.append("Critical business tier endpoint flagged; prioritized mission-critical workflows")
        
        failed_prior = [t.id for t in tests if t.last_run_status == "FAILED"]
        if failed_prior:
            key_drivers.append(f"Historical test failures penalized tests {', '.join(failed_prior)} to ensure fast regression detection")

        return {
            "mode": self.execution_mode,
            "total_analyzed": len(tests),
            "priority_distribution": {
                "High": len(high_tests),
                "Medium": len(med_tests),
                "Low": len(low_tests)
            },
            "primary_ranking_drivers": key_drivers,
            "transparency_note": "Scoring uses verified deterministic weightings. No black-box ML extrapolation is utilized."
        }
