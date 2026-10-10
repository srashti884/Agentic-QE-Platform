from app.agents.change_analyzer import ChangeAnalyzerAgent
from app.models.schemas import ApiChange

def test_change_analyzer_local_fallback():
    agent = ChangeAnalyzerAgent()
    assert agent.name == "Change Analysis Agent"
    assert "Deterministic" in agent.execution_mode

    change = ApiChange(
        id="CHG-TEST",
        title="Test API Change",
        service="PaymentService",
        endpoint="/api/v1/payments/process",
        http_method="POST",
        business_criticality="Critical",
        is_breaking=True,
        description="Breaking payment update",
        changed_fields=["token", "idempotency_key"]
    )

    result = agent.execute(change)
    assert result["endpoint"] == "/api/v1/payments/process"
    assert result["service"] == "PaymentService"
    assert result["is_breaking"] is True
    assert result["risk_tier"] == "CRITICAL"
    assert len(result["changed_fields"]) == 2
