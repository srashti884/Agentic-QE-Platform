import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from ..models.schemas import (
    ApiChange,
    PipelineRunResult,
    PipelineStepResult,
    HumanReviewRequest
)
from ..agents.change_analyzer import ChangeAnalyzerAgent
from ..agents.impact_analyzer import ImpactAnalyzerAgent
from ..agents.prioritizer import PrioritizerAgent
from ..agents.explainability import ExplainabilityAgent
from ..repositories.change_repo import ChangeRepository
from ..repositories.test_repo import TestRepository
from ..repositories.audit_repo import AuditRepository

class WorkflowOrchestrator:
    """
    Coordinates Agentic QE workflow across agents, repositories, and human checkpoints.
    Tracks execution modes, metrics, PACTS compliance, and audit events.
    """
    def __init__(
        self,
        change_repo: Optional[ChangeRepository] = None,
        test_repo: Optional[TestRepository] = None,
        audit_repo: Optional[AuditRepository] = None
    ):
        self.change_repo = change_repo or ChangeRepository()
        self.test_repo = test_repo or TestRepository()
        self.audit_repo = audit_repo or AuditRepository()

        self.change_analyzer = ChangeAnalyzerAgent()
        self.impact_analyzer = ImpactAnalyzerAgent()
        self.prioritizer = PrioritizerAgent()
        self.explainability = ExplainabilityAgent()

    def run_pipeline_for_change(self, change: ApiChange) -> PipelineRunResult:
        pipeline_id = f"PIPE-{uuid.uuid4().hex[:8].upper()}"
        steps = []
        all_tests = self.test_repo.get_all()

        # Step 1: Change Analysis
        t0 = time.perf_counter()
        change_meta = self.change_analyzer.execute(change)
        dur1 = round((time.perf_counter() - t0) * 1000, 2)
        steps.append(PipelineStepResult(
            step_id=1,
            step_name="Change Analysis",
            agent_name=self.change_analyzer.name,
            capability=self.change_analyzer.capability,
            execution_mode=self.change_analyzer.execution_mode,
            pacts_principle=self.change_analyzer.pacts_principle,
            status="SUCCESS",
            duration_ms=dur1,
            summary=f"Parsed {change.http_method} {change.endpoint} ({change.service}). Risk tier: {change_meta.get('risk_tier', 'STANDARD')}.",
            input_summary=f"API Change: {change.title} ({change.id})",
            output_summary=f"Extracted route, {len(change.changed_fields)} changed fields, breaking={change.is_breaking}",
            details=change_meta
        ))

        # Step 2: Test Impact Analysis
        t0 = time.perf_counter()
        impacted_candidates = self.impact_analyzer.execute(change, all_tests)
        dur2 = round((time.perf_counter() - t0) * 1000, 2)
        direct_matches = sum(1 for _, it, _ in impacted_candidates if it == "Direct Endpoint Match")
        dep_matches = sum(1 for _, it, _ in impacted_candidates if it == "Upstream/Downstream Dependency")
        steps.append(PipelineStepResult(
            step_id=2,
            step_name="Test Impact Analysis",
            agent_name=self.impact_analyzer.name,
            capability=self.impact_analyzer.capability,
            execution_mode=self.impact_analyzer.execution_mode,
            pacts_principle=self.impact_analyzer.pacts_principle,
            status="SUCCESS",
            duration_ms=dur2,
            summary=f"Identified {len(impacted_candidates)} impacted tests ({direct_matches} direct, {dep_matches} dependencies) out of {len(all_tests)} total tests.",
            input_summary=f"Changed API: {change.endpoint} + {len(all_tests)} regression tests",
            output_summary=f"{len(impacted_candidates)} candidate tests flagged for regression",
            details={
                "total_evaluated": len(all_tests),
                "direct_matches": direct_matches,
                "dependency_matches": dep_matches
            }
        ))

        # Step 3: Regression Prioritization
        t0 = time.perf_counter()
        prioritized_tests = self.prioritizer.execute(change, impacted_candidates)
        dur3 = round((time.perf_counter() - t0) * 1000, 2)
        high_cnt = sum(1 for t in prioritized_tests if t.priority == "High")
        med_cnt = sum(1 for t in prioritized_tests if t.priority == "Medium")
        low_cnt = sum(1 for t in prioritized_tests if t.priority == "Low")
        steps.append(PipelineStepResult(
            step_id=3,
            step_name="Regression Prioritization",
            agent_name=self.prioritizer.name,
            capability=self.prioritizer.capability,
            execution_mode=self.prioritizer.execution_mode,
            pacts_principle=self.prioritizer.pacts_principle,
            status="SUCCESS",
            duration_ms=dur3,
            summary=f"Categorized into High ({high_cnt}), Medium ({med_cnt}), and Low ({low_cnt}) priority tiers.",
            input_summary=f"{len(impacted_candidates)} impacted candidates with test history & criticality",
            output_summary=f"Ranked {len(prioritized_tests)} tests deterministically (0-100 scale)",
            details={
                "high_count": high_cnt,
                "medium_count": med_cnt,
                "low_count": low_cnt,
                "top_score": prioritized_tests[0].score if prioritized_tests else 0
            }
        ))

        # Step 4: Transparent Explainability
        t0 = time.perf_counter()
        explanation_data = self.explainability.execute(change, prioritized_tests)
        dur4 = round((time.perf_counter() - t0) * 1000, 2)
        steps.append(PipelineStepResult(
            step_id=4,
            step_name="Explainability & Justification",
            agent_name=self.explainability.name,
            capability=self.explainability.capability,
            execution_mode=self.explainability.execution_mode,
            pacts_principle=self.explainability.pacts_principle,
            status="SUCCESS",
            duration_ms=dur4,
            summary="Synthesized transparent mathematical attribution per test factor.",
            input_summary="Prioritized test candidates with component score vectors",
            output_summary=f"{len(explanation_data['primary_ranking_drivers'])} primary ranking drivers attributed",
            details=explanation_data
        ))

        # Calculate estimated total runtime
        total_suite_runtime = sum(t.execution_time_seconds for t in prioritized_tests if t.is_included_in_run)

        # Step 5: Audit Log Generation
        self.audit_repo.log_event(
            event_type="PIPELINE_RUN",
            change_id=change.id,
            actor="Agent Orchestrator",
            action=f"Executed Agentic QE pipeline ({pipeline_id}) for {change.title}",
            details={
                "pipeline_id": pipeline_id,
                "total_evaluated": len(all_tests),
                "impacted_count": len(prioritized_tests),
                "priorities": {"High": high_cnt, "Medium": med_cnt, "Low": low_cnt},
                "execution_mode": self.prioritizer.execution_mode
            }
        )

        return PipelineRunResult(
            pipeline_id=pipeline_id,
            change=change,
            steps=steps,
            impacted_tests=prioritized_tests,
            total_tests_evaluated=len(all_tests),
            impacted_count=len(prioritized_tests),
            high_priority_count=high_cnt,
            medium_priority_count=med_cnt,
            low_priority_count=low_cnt,
            total_execution_time_seconds=total_suite_runtime,
            execution_mode=self.prioritizer.execution_mode,
            created_at=datetime.now(timezone.utc).isoformat()
        )

    def process_human_review(self, review: HumanReviewRequest) -> Dict[str, Any]:
        """
        Records human approval, priority modifications, or rejection in the audit trail.
        """
        audit_entry = self.audit_repo.log_event(
            event_type="HUMAN_REVIEW",
            change_id=review.change_id,
            actor=review.reviewed_by,
            action=f"Human Review Decision: {review.decision}",
            details={
                "decision": review.decision,
                "comments": review.comments,
                "selected_test_ids": review.selected_test_ids,
                "priority_overrides": review.priority_overrides
            }
        )
        return {
            "status": "RECORDED",
            "audit_id": audit_entry.id,
            "decision": review.decision,
            "timestamp": audit_entry.timestamp
        }
