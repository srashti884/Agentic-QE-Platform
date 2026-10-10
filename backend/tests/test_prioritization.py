from app.agents.prioritizer import PrioritizerAgent
from app.models.schemas import ApiChange, RegressionTest

def test_prioritizer_scoring():
    agent = PrioritizerAgent()

    change = ApiChange(
        id="CHG-TEST",
        title="Payment Update",
        service="PaymentService",
        endpoint="/api/v1/payments/process",
        http_method="POST",
        business_criticality="Critical",
        is_breaking=True,
        description="Breaking update",
        changed_fields=["token"]
    )

    t1 = RegressionTest(
        id="TEST-HIGH",
        name="Critical Direct Payment Test",
        service="PaymentService",
        target_endpoints=["/api/v1/payments/process"],
        test_type="E2E",
        business_criticality="Critical",
        historical_failure_rate=0.4,
        execution_time_seconds=20,
        flakiness_score=0.1,
        last_run_status="FAILED"
    )

    impacted_candidates = [(t1, "Direct Endpoint Match", 35.0)]
    results = agent.execute(change, impacted_candidates)

    assert len(results) == 1
    res = results[0]
    assert res.priority == "High"
    assert res.score >= 70.0
    assert res.score_breakdown.direct_endpoint_points == 35.0
    assert res.score_breakdown.criticality_points == 25.0
    assert res.score_breakdown.breaking_change_points == 10.0
