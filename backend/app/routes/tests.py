from fastapi import APIRouter, HTTPException
from typing import List, Optional
from ..models.schemas import RegressionTest
from ..repositories.test_repo import TestRepository

router = APIRouter(prefix="/api/tests", tags=["Regression Tests"])
repo = TestRepository()

@router.get("", response_model=List[RegressionTest])
def list_tests(service: Optional[str] = None):
    if service:
        return repo.get_by_service(service)
    return repo.get_all()

@router.get("/{test_id}", response_model=RegressionTest)
def get_test(test_id: str):
    test = repo.get_by_id(test_id)
    if not test:
        raise HTTPException(status_code=404, detail=f"Test '{test_id}' not found")
    return test
