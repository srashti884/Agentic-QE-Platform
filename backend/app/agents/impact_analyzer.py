from typing import List, Dict, Any, Tuple
from .base import BaseAgent
from ..models.schemas import ApiChange, RegressionTest

class ImpactAnalyzerAgent(BaseAgent):
    """
    Agent: Test Impact Analysis Agent
    Purpose: Correlates the changed API/module with existing tests to discover impacted tests.
    PACTS Principle: Targeted + Transparent
    """
    def __init__(self):
        super().__init__(
            name="Test Impact Analysis Agent",
            capability="Test Impact Analysis & Blast Radius Mapping",
            pacts_principle="Targeted + Transparent"
        )

    def execute(self, change: ApiChange, all_tests: List[RegressionTest]) -> List[Tuple[RegressionTest, str, float]]:
        """
        Returns list of tuples: (RegressionTest, impact_type, initial_impact_weight)
        impact_type: "Direct Endpoint Match" | "Upstream/Downstream Dependency"
        """
        if self.platform_agent_available:
            return self._call_platform_agent(change, all_tests)
        return self._local_deterministic_impact(change, all_tests)

    def _call_platform_agent(self, change: ApiChange, all_tests: List[RegressionTest]) -> List[Tuple[RegressionTest, str, float]]:
        # Platform integration fallback to local logic
        return self._local_deterministic_impact(change, all_tests)

    def _local_deterministic_impact(self, change: ApiChange, all_tests: List[RegressionTest]) -> List[Tuple[RegressionTest, str, float]]:
        impacted = []
        target_endpoint_clean = change.endpoint.strip().lower()
        target_service_clean = change.service.strip().lower()
        changed_tags = [f.lower().replace(".", " ").replace("-", " ") for f in change.changed_fields]

        for test in all_tests:
            is_direct_endpoint = False
            for ep in test.target_endpoints:
                if ep.strip().lower() == target_endpoint_clean:
                    is_direct_endpoint = True
                    break

            is_service_match = test.service.strip().lower() == target_service_clean

            # Check if any tag or description correlates with changed fields
            tag_overlap = False
            for tag in test.tags:
                tag_lower = tag.lower()
                for ctag in changed_tags:
                    if tag_lower in ctag or ctag in tag_lower:
                        tag_overlap = True
                        break

            if is_direct_endpoint:
                impacted.append((test, "Direct Endpoint Match", 35.0))
            elif is_service_match or tag_overlap or any(target_endpoint_clean in ep.lower() for ep in test.target_endpoints):
                impacted.append((test, "Upstream/Downstream Dependency", 20.0))

        return impacted
