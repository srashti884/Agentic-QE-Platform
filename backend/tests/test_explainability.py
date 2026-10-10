from app.agents.explainability import ExplainabilityAgent
from app.agents.prioritizer import PrioritizerAgent
from app.models.schemas import ApiChange, RegressionTest

def test_explainability_generation():
    prioritizer = PrioritizerAgent()
    explainer = ExplainabilityAgent()

    change = ApiChange(
        id="CHG-EXP",
        title="Inventory Reserve",
        service="InventoryService",
        endpoint="/api/v1/inventory/reserve",
        http_method="POST",
        business_criticality="Critical",
        is_breaking=True,
        description="Breaking lock change",
        changed_fields=["sku"]
    )

    t1 = RegressionTest(
        id="TEST-INV-1",
        name="Inventory Lock Test",
        service="InventoryService",
        target_endpoints=["/api/v1/inventory/reserve"],
        test_type="Integration",
        business_criticality="Critical",
        historical_failure_rate=0.5,
        execution_time_seconds=30,
        flakiness_score=0.2,
        last_run_status="FAILED"
    )

    prioritized = prioritizer.execute(change, [(t1, "Direct Endpoint Match", 35.0)])
    summary = explainer.execute(change, prioritized)

    assert summary["total_analyzed"] == 1
    assert "Breaking API contract change detected" in summary["primary_ranking_drivers"][0]
    assert "Critical business tier" in summary["primary_ranking_drivers"][1]
    assert prioritized[0].explanation != ""
