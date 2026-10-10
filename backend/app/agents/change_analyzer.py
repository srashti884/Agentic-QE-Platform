from typing import Dict, Any
from .base import BaseAgent
from ..models.schemas import ApiChange

class ChangeAnalyzerAgent(BaseAgent):
    """
    Agent: Change Analysis Agent
    Purpose: Identifies changed API, route parameters, breaking flags, and business criticality.
    PACTS Principle: Proactive + Context-aware
    """
    def __init__(self):
        super().__init__(
            name="Change Analysis Agent",
            capability="API Semantic Change Analysis & Extraction",
            pacts_principle="Proactive + Context-aware"
        )

    def execute(self, change: ApiChange) -> Dict[str, Any]:
        """
        Executes change parsing. If platform agent is configured, delegates;
        otherwise runs local deterministic rule extraction.
        """
        if self.platform_agent_available:
            return self._call_platform_agent(change)
        return self._local_deterministic_analysis(change)

    def _call_platform_agent(self, change: ApiChange) -> Dict[str, Any]:
        # Architectural stub for external platform agent (e.g. LLM/Agentic platform endpoint)
        return {
            "mode": "Platform Agent",
            "parsed_endpoint": change.endpoint.strip(),
            "target_service": change.service.strip(),
            "breaking_detected": change.is_breaking,
            "criticality_level": change.business_criticality,
            "changed_parameters_count": len(change.changed_fields),
            "blast_radius_rating": "HIGH" if change.is_breaking or change.business_criticality == "Critical" else "MEDIUM"
        }

    def _local_deterministic_analysis(self, change: ApiChange) -> Dict[str, Any]:
        # Deterministic analysis logic
        endpoint = change.endpoint.strip().lower()
        service = change.service.strip()
        is_breaking = change.is_breaking
        crit = change.business_criticality.capitalize()

        # Extract path tokens (e.g., /api/v1/payments/process -> ['api', 'v1', 'payments', 'process'])
        path_segments = [seg for seg in endpoint.split("/") if seg]

        # Determine semantic risk tier
        if is_breaking or crit == "Critical":
            risk_tier = "CRITICAL"
            suggested_testing_scope = "Comprehensive E2E + Direct API Regression"
        elif crit == "High":
            risk_tier = "HIGH"
            suggested_testing_scope = "Direct API + Dependent Integration Tests"
        else:
            risk_tier = "STANDARD"
            suggested_testing_scope = "Targeted Unit & Endpoint Sanity Tests"

        return {
            "mode": "Local Deterministic Fallback",
            "endpoint": change.endpoint,
            "service": service,
            "http_method": change.http_method.upper(),
            "is_breaking": is_breaking,
            "business_criticality": crit,
            "path_segments": path_segments,
            "changed_fields": change.changed_fields,
            "risk_tier": risk_tier,
            "suggested_testing_scope": suggested_testing_scope,
            "field_count": len(change.changed_fields)
        }
