from typing import List, Tuple
from .base import BaseAgent
from ..models.schemas import ApiChange, RegressionTest, PrioritizedTest, ScoreFactorBreakdown

class PrioritizerAgent(BaseAgent):
    """
    Agent: Regression Prioritization Agent
    Purpose: Deterministically prioritizes tests using API relationship, criticality, risk, and failure history.
    PACTS Principle: Adaptive + Scalable
    NOTE: This is a deterministic rule-based scoring engine for enterprise quality engineering,
    NOT an unverified black-box ML model.
    """
    def __init__(self):
        super().__init__(
            name="Regression Prioritization Agent",
            capability="Multi-Factor Deterministic Risk & Criticality Prioritization",
            pacts_principle="Adaptive + Scalable"
        )

    def execute(
        self,
        change: ApiChange,
        impacted_candidates: List[Tuple[RegressionTest, str, float]]
    ) -> List[PrioritizedTest]:
        prioritized_tests: List[PrioritizedTest] = []

        for test, impact_type, endpoint_match_weight in impacted_candidates:
            # 1. Endpoint & Relationship Points (Max 35)
            endpoint_pts = endpoint_match_weight

            # 2. Criticality Points (Max 25)
            # Evaluate maximum of change criticality and test criticality
            crit_rank = {"critical": 25.0, "high": 18.0, "medium": 10.0, "low": 4.0}
            change_crit_val = crit_rank.get(change.business_criticality.lower(), 10.0)
            test_crit_val = crit_rank.get(test.business_criticality.lower(), 10.0)
            criticality_pts = max(change_crit_val, test_crit_val)

            # 3. Historical Failure Points (Max 25)
            # Base failure rate (0.0 - 1.0) scaled to 20 pts + 5 pts if last run was FAILED
            failure_pts = round(test.historical_failure_rate * 20.0, 1)
            if test.last_run_status.upper() == "FAILED":
                failure_pts += 5.0

            # 4. Breaking Change Sensitivity (Max 10)
            breaking_pts = 0.0
            if change.is_breaking:
                if test.test_type in ["E2E", "Integration"]:
                    breaking_pts = 10.0
                else:
                    breaking_pts = 7.0

            # 5. Flakiness / Execution Risk (Max 5)
            flakiness_pts = min(round(test.flakiness_score * 10.0, 1), 5.0)

            # Total Score calculation
            total_raw = endpoint_pts + criticality_pts + failure_pts + breaking_pts + flakiness_pts
            total_score = min(round(total_raw, 1), 100.0)

            # Priority Bucket assignment
            if total_score >= 65.0:
                priority = "High"
            elif total_score >= 40.0:
                priority = "Medium"
            else:
                priority = "Low"

            breakdown = ScoreFactorBreakdown(
                direct_endpoint_points=endpoint_pts,
                service_coupling_points=0.0 if impact_type == "Direct Endpoint Match" else 20.0,
                criticality_points=criticality_pts,
                failure_history_points=failure_pts,
                flakiness_points=flakiness_pts,
                breaking_change_points=breaking_pts,
                total_score=total_score,
                formula_summary=(
                    f"Match({endpoint_pts}) + Criticality({criticality_pts}) + "
                    f"Failures({failure_pts}) + Breaking({breaking_pts}) + Flakiness({flakiness_pts})"
                )
            )

            explanation = (
                f"Assigned {priority} priority (Score: {total_score}/100) due to "
                f"{impact_type.lower()} on '{change.endpoint}', "
                f"{test.business_criticality} criticality tier (+{criticality_pts} pts), "
                f"and {int(test.historical_failure_rate * 100)}% historical failure rate (+{failure_pts} pts)."
            )

            prioritized_tests.append(
                PrioritizedTest(
                    id=test.id,
                    name=test.name,
                    service=test.service,
                    target_endpoints=test.target_endpoints,
                    test_type=test.test_type,
                    business_criticality=test.business_criticality,
                    historical_failure_rate=test.historical_failure_rate,
                    execution_time_seconds=test.execution_time_seconds,
                    flakiness_score=test.flakiness_score,
                    tags=test.tags,
                    last_run_status=test.last_run_status,
                    description=test.description,
                    impact_type=impact_type,
                    priority=priority,
                    score=total_score,
                    score_breakdown=breakdown,
                    explanation=explanation,
                    selected_by_default=(priority in ["High", "Medium"]),
                    manual_override_priority=None,
                    is_included_in_run=(priority in ["High", "Medium"])
                )
            )

        # Sort descending by score
        prioritized_tests.sort(key=lambda t: t.score, reverse=True)
        return prioritized_tests
