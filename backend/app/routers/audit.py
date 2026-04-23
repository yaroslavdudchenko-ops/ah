"""
GET /api/v1/audit-log              — global audit trail (all entities)
GET /api/v1/protocols/{id}/audit   — per-protocol audit trail
"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.protocol import AuditLog
from app.schemas.protocol import error_body

router = APIRouter(tags=["audit"])


def _parse_date(s: Optional[str], end_of_day: bool = False) -> Optional[datetime]:
    """Parse ISO date string (YYYY-MM-DD) to UTC datetime."""
    if not s:
        return None
    try:
        dt = datetime.strptime(s, "%Y-%m-%d")
        if end_of_day:
            dt = dt.replace(hour=23, minute=59, second=59)
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _audit_row(log: AuditLog) -> dict:
    return {
        "id": log.id,
        "entity_type": log.entity_type,
        "entity_id": log.entity_id,
        "action": log.action,
        "performed_by": log.performed_by,
        "metadata": log.metadata_,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


@router.get("/api/v1/audit-log")
async def list_audit_log(
    from_date: Optional[str] = Query(None, description="ISO date YYYY-MM-DD (inclusive)"),
    to_date:   Optional[str] = Query(None, description="ISO date YYYY-MM-DD (inclusive)"),
    action:    Optional[str] = Query(None, description="Filter by action (e.g. ai_generate)"),
    performed_by: Optional[str] = Query(None, description="Filter by username"),
    limit:  int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Global audit trail — all entities, all actions. Accessible to all roles."""
    conditions = []
    dt_from = _parse_date(from_date)
    dt_to   = _parse_date(to_date, end_of_day=True)
    if dt_from:
        conditions.append(AuditLog.created_at >= dt_from)
    if dt_to:
        conditions.append(AuditLog.created_at <= dt_to)
    if action:
        conditions.append(AuditLog.action == action)
    if performed_by:
        conditions.append(AuditLog.performed_by == performed_by)

    q = (
        select(AuditLog)
        .where(and_(*conditions) if conditions else True)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(q)
    logs = result.scalars().all()
    return [_audit_row(log) for log in logs]


@router.get("/api/v1/protocols/{protocol_id}/audit")
async def list_protocol_audit(
    protocol_id: str,
    from_date: Optional[str] = Query(None, description="ISO date YYYY-MM-DD (inclusive)"),
    to_date:   Optional[str] = Query(None, description="ISO date YYYY-MM-DD (inclusive)"),
    limit:  int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Per-protocol audit trail. Accessible to all roles."""
    conditions = [AuditLog.entity_id == protocol_id]
    dt_from = _parse_date(from_date)
    dt_to   = _parse_date(to_date, end_of_day=True)
    if dt_from:
        conditions.append(AuditLog.created_at >= dt_from)
    if dt_to:
        conditions.append(AuditLog.created_at <= dt_to)

    q = (
        select(AuditLog)
        .where(and_(*conditions))
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(q)
    logs = result.scalars().all()
    return [_audit_row(log) for log in logs]
