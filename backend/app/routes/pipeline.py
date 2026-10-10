from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from ..models.schemas import PipelineRunResult, ApiChange
from ..orchestrator.workflow import WorkflowOrchestrator
from ..repositories.change_repo import ChangeRepository

router = APIRouter(prefix="/api/pipeline", tags=["Pipeline Execution"])
orchestrator = WorkflowOrchestrator()
change_repo = ChangeRepository()

@router.post("/run", response_model=PipelineRunResult)
def run_pipeline(payload: Dict[str, str]):
    change_id = payload.get("change_id")
    if not change_id:
        raise HTTPException(status_code=400, detail="change_id is required in request body")
    change = change_repo.get_by_id(change_id)
    if not change:
        raise HTTPException(status_code=404, detail=f"Change '{change_id}' not found")
    return orchestrator.run_pipeline_for_change(change)

@router.post("/custom", response_model=PipelineRunResult)
def run_custom_pipeline(change: ApiChange):
    # Save change if new
    change_repo.add_change(change)
    return orchestrator.run_pipeline_for_change(change)
