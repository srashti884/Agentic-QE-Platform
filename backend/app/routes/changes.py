from fastapi import APIRouter, HTTPException
from typing import List
from ..models.schemas import ApiChange
from ..repositories.change_repo import ChangeRepository

router = APIRouter(prefix="/api/changes", tags=["API Changes"])
repo = ChangeRepository()

@router.get("", response_model=List[ApiChange])
def list_changes():
    return repo.get_all()

@router.get("/{change_id}", response_model=ApiChange)
def get_change(change_id: str):
    change = repo.get_by_id(change_id)
    if not change:
        raise HTTPException(status_code=404, detail=f"Change '{change_id}' not found")
    return change

@router.post("", response_model=ApiChange)
def create_change(change: ApiChange):
    return repo.add_change(change)
