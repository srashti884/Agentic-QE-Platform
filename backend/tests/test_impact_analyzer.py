from app.agents.impact_analyzer import ImpactAnalyzerAgent
from app.models.schemas import ApiChange, RegressionTest

def test_impact_analyzer_matches():
    agent = ImpactAnalyzerAgent()

    change = ApiChange(
        id="CHG-TEST",
        title="Payment Update",
        service="PaymentService",
        endpoint="/api/v1/payments/process",
        http_method="POST",
        business_criticality="High",
        is_breaking=False,
        description="Non-breaking update",
        changed_fields=["token"]
    )

    tests = [
        RegressionTest(
            id="TEST-1",
            name="Direct Payment Test",
            service="PaymentService",
            target_endpoints=["/api/v1/payments/process"],
            test_type="API",
            business_criticality="High",
            historical_failure_rate=0.2,
            execution_time_seconds=10,
            flakiness_score=0.0
        ),
        RegressionTest(
            id="TEST-2",
            name="Order Service Test calling Payment",
            service="OrderService",
            target_endpoints=["/api/v1/orders/checkout", "/api/v1/payments/process"],
            test_type="E2E",
            business_criticality="Critical",
            historical_failure_rate=0.3,
            execution_time_seconds=30,
            flakiness_score=0.1
        ),
        RegressionTest(
            id="TEST-3",
            name="Unrelated User Test",
            service="UserService",
            target_endpoints=["/api/v1/users/profile"],
            test_type="API",
            business_criticality="Low",
            historical_failure_rate=0.0,
            execution_time_seconds=5,
            flakiness_score=0.0
        )
    ]

    impacted = agent.execute(change, tests)
    impacted_ids = [t.id for t, _, _ in impacted]
    assert "TEST-1" in impacted_ids
    assert "TEST-2" in impacted_ids
    assert "TEST-3" not in impacted_ids
