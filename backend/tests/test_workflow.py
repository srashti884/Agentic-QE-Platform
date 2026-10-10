from app.orchestrator.workflow import WorkflowOrchestrator
from app.models.schemas import ApiChange, HumanReviewRequest

def test_workflow_orchestration():
    orchestrator = WorkflowOrchestrator()
    change = ApiChange(
        id="CHG-TEST-WF",
        title="Workflow Verification Change",
        service="PaymentService",
        endpoint="/api/v1/payments/process",
        http_method="POST",
        business_criticality="High",
        is_breaking=False,
        description="Verify orchestration pipeline",
        changed_fields=["token"]
    )

    result = orchestrator.run_pipeline_for_change(change)
    assert result.pipeline_id.startswith("PIPE-")
    assert len(result.steps) == 4
    assert result.impacted_count > 0
    assert result.total_tests_evaluated > 0

    # Test Human Review flow
    review = HumanReviewRequest(
        change_id=change.id,
        decision="APPROVED",
        reviewed_by="Lead QA Engineer",
        comments="Approved for deployment staging test",
        selected_test_ids=[t.id for t in result.impacted_tests[:2]]
    )
    rev_res = orchestrator.process_human_review(review)
    assert rev_res["status"] == "RECORDED"
    assert rev_res["decision"] == "APPROVED"
