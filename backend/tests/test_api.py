from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "HEALTHY"

def test_list_changes():
    res = client.get("/api/changes")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 4

def test_list_tests():
    res = client.get("/api/tests")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 10

def test_run_pipeline():
    res = client.post("/api/pipeline/run", json={"change_id": "CHG-101"})
    assert res.status_code == 200
    data = res.json()
    assert data["pipeline_id"].startswith("PIPE-")
    assert len(data["steps"]) == 4
    assert len(data["impacted_tests"]) > 0

def test_human_review_and_audit():
    review_payload = {
        "change_id": "CHG-101",
        "decision": "APPROVED",
        "reviewed_by": "Senior QA Tester",
        "comments": "Automated verification pass",
        "selected_test_ids": ["TEST-PAY-001", "TEST-PAY-002"]
    }
    res = client.post("/api/review", json=review_payload)
    assert res.status_code == 200
    assert res.json()["decision"] == "APPROVED"

    audit_res = client.get("/api/audit")
    assert audit_res.status_code == 200
    logs = audit_res.json()
    assert len(logs) > 0
