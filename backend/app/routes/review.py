from fastapi import APIRouter
from typing import Dict, Any
from ..models.schemas import HumanReviewRequest
from ..orchestrator.workflow import WorkflowOrchestrator

router = APIRouter(prefix="/api/review", tags=["Human Review"])
orchestrator = WorkflowOrchestrator()

@router.post("", response_model=Dict[str, Any])
def submit_review(review: HumanReviewRequest):
    return orchestrator.process_human_review(review)
