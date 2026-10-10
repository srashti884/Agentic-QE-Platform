from fastapi import APIRouter
from typing import List
from ..models.schemas import AuditLogEntry
from ..repositories.audit_repo import AuditRepository

router = APIRouter(prefix="/api/audit", tags=["Audit Trail"])
repo = AuditRepository()

@router.get("", response_model=List[AuditLogEntry])
def list_audit_trail():
    return repo.get_all()
