from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class ApiChange(BaseModel):
    id: str
    title: str
    service: str
    endpoint: str
    http_method: str = "POST"
    business_criticality: str = "High"  # Critical, High, Medium, Low
    is_breaking: bool = False
    description: str
    changed_fields: List[str] = Field(default_factory=list)
    author: str = "Quality Engineering"
    commit_hash: str = "local-head"
    timestamp: str = ""

class RegressionTest(BaseModel):
    id: str
    name: str
    service: str
    target_endpoints: List[str]
    test_type: str = "API"  # API, Integration, E2E
    business_criticality: str = "Medium"  # Critical, High, Medium, Low
    historical_failure_rate: float = 0.0  # 0.0 to 1.0
    execution_time_seconds: int = 15
    flakiness_score: float = 0.0
    tags: List[str] = Field(default_factory=list)
    last_run_status: str = "PASSED"
    description: str = ""

class ScoreFactorBreakdown(BaseModel):
    direct_endpoint_points: float = 0.0
    service_coupling_points: float = 0.0
    criticality_points: float = 0.0
    failure_history_points: float = 0.0
    flakiness_points: float = 0.0
    breaking_change_points: float = 0.0
    total_score: float = 0.0
    formula_summary: str = ""

class PrioritizedTest(BaseModel):
    id: str
    name: str
    service: str
    target_endpoints: List[str]
    test_type: str
    business_criticality: str
    historical_failure_rate: float
    execution_time_seconds: int
    flakiness_score: float
    tags: List[str] = Field(default_factory=list)
    last_run_status: str
    description: str
    impact_type: str  # Direct Endpoint Match, Upstream/Downstream Dependency, Unrelated
    priority: str  # High, Medium, Low, Excluded
    score: float
    score_breakdown: ScoreFactorBreakdown
    explanation: str
    selected_by_default: bool = True
    manual_override_priority: Optional[str] = None
    is_included_in_run: bool = True

class PipelineStepResult(BaseModel):
    step_id: int
    step_name: str
    agent_name: str
    capability: str
    execution_mode: str  # Platform Agent | Local Deterministic Fallback
    pacts_principle: str  # e.g., "Targeted + Proactive"
    status: str = "SUCCESS"  # SUCCESS | WARNING | FAILED
    duration_ms: float = 0.0
    summary: str
    input_summary: str
    output_summary: str
    details: Dict[str, Any] = Field(default_factory=dict)

class PipelineRunResult(BaseModel):
    pipeline_id: str
    change: ApiChange
    steps: List[PipelineStepResult]
    impacted_tests: List[PrioritizedTest]
    total_tests_evaluated: int
    impacted_count: int
    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
    total_execution_time_seconds: int
    execution_mode: str
    created_at: str

class HumanReviewRequest(BaseModel):
    change_id: str
    decision: str  # APPROVED, MODIFIED, REJECTED
    reviewed_by: str = "QA Engineer"
    comments: str = ""
    selected_test_ids: List[str] = Field(default_factory=list)
    priority_overrides: Dict[str, str] = Field(default_factory=dict)

class AuditLogEntry(BaseModel):
    id: str
    timestamp: str
    event_type: str
    change_id: str
    actor: str
    action: str
    details: Dict[str, Any] = Field(default_factory=dict)


