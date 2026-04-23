import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_user, require_write, require_delete
from app.models.protocol import Protocol, ProtocolVersion, AuditLog
from app.schemas.protocol import (
    ProtocolCreate, ProtocolUpdate, ProtocolResponse, ProtocolListItem,
    VersionResponse, error_body,
)

router = APIRouter(prefix="/api/v1/protocols", tags=["protocols"])
tags_router = APIRouter(prefix="/api/v1", tags=["tags"])


@tags_router.get("/tags", response_model=list[str])
async def list_all_tags(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """All unique tags across all protocols — for autocomplete."""
    result = await db.execute(select(Protocol.tags))
    all_tags: set[str] = set()
    for (tags,) in result:
        if isinstance(tags, list):
            all_tags.update(t for t in tags if isinstance(t, str) and t.strip())
    return sorted(all_tags)


@router.post("", response_model=ProtocolResponse, status_code=status.HTTP_201_CREATED)
async def create_protocol(
    body: ProtocolCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_write),
):
    protocol_id = str(uuid.uuid4())
    protocol = Protocol(id=protocol_id, **body.model_dump())
    db.add(protocol)
    db.add(AuditLog(
        entity_type="protocol", entity_id=protocol_id,
        action="create",
        performed_by=current_user["username"],
        metadata_={"title": body.title, "role": current_user["role"]},
    ))
    await db.flush()
    await db.refresh(protocol)
    return protocol


@router.get("", response_model=list[ProtocolListItem])
async def list_protocols(
    limit: int = 50,
    offset: int = 0,
    phase: Optional[str] = None,
    status: Optional[str] = Query(None, description="Filter by status (draft|generated|approved)"),
    therapeutic_area: Optional[str] = Query(None, description="Filter by therapeutic area"),
    search: Optional[str] = Query(None, description="Search by title or drug name (case-insensitive)"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    q = select(Protocol).order_by(Protocol.updated_at.desc())
    if phase:
        q = q.where(Protocol.phase == phase)
    if status:
        q = q.where(Protocol.status == status)
    if therapeutic_area:
        q = q.where(Protocol.therapeutic_area.ilike(f"%{therapeutic_area}%"))
    if search:
        term = f"%{search}%"
        q = q.where(
            Protocol.title.ilike(term) | Protocol.drug_name.ilike(term)
        )
    result = await db.execute(q)
    protocols = result.scalars().all()
    # Tag filter: Python-level (JSON array membership)
    if tag:
        protocols = [p for p in protocols if tag in (p.tags or [])]
    return protocols[offset : offset + limit]


@router.get("/{protocol_id}", response_model=ProtocolResponse)
async def get_protocol(
    protocol_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await _get_or_404(protocol_id, db)


@router.patch("/{protocol_id}", response_model=ProtocolResponse)
async def update_protocol(
    protocol_id: str,
    body: ProtocolUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_write),
):
    protocol = await _get_or_404(protocol_id, db)
    update_data = body.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(protocol, k, v)
    db.add(AuditLog(
        entity_type="protocol", entity_id=protocol_id,
        action="update",
        performed_by=current_user["username"],
        metadata_={"fields": list(update_data.keys()), "role": current_user["role"]},
    ))
    await db.flush()
    await db.refresh(protocol)
    return protocol


@router.delete("/{protocol_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_protocol(
    protocol_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_delete),
):
    protocol = await _get_or_404(protocol_id, db)
    db.add(AuditLog(
        entity_type="protocol", entity_id=protocol_id,
        action="delete",
        performed_by=current_user["username"],
        metadata_={"title": protocol.title, "role": current_user["role"]},
    ))
    await db.delete(protocol)


@router.get("/{protocol_id}/versions", response_model=list[VersionResponse])
async def list_versions(
    protocol_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    await _get_or_404(protocol_id, db)
    result = await db.execute(
        select(ProtocolVersion)
        .where(ProtocolVersion.protocol_id == protocol_id)
        .order_by(ProtocolVersion.version_number)
    )
    return result.scalars().all()


@router.get("/{protocol_id}/versions/{version_id}", response_model=VersionResponse)
async def get_version(
    protocol_id: str,
    version_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    await _get_or_404(protocol_id, db)
    result = await db.execute(
        select(ProtocolVersion).where(
            ProtocolVersion.id == version_id,
            ProtocolVersion.protocol_id == protocol_id,
        )
    )
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(
            status_code=404,
            detail=error_body("VERSION_NOT_FOUND", f"Version {version_id} not found"),
        )
    return version


@router.get("/{protocol_id}/diff")
async def diff_versions(
    protocol_id: str,
    v1: int,
    v2: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=error_body("NOT_IMPLEMENTED", "Version diff is a P2 feature."),
    )


async def _get_or_404(protocol_id: str, db: AsyncSession) -> Protocol:
    result = await db.execute(select(Protocol).where(Protocol.id == protocol_id))
    protocol = result.scalar_one_or_none()
    if not protocol:
        raise HTTPException(
            status_code=404,
            detail=error_body("PROTOCOL_NOT_FOUND", f"Protocol {protocol_id} not found"),
        )
    return protocol
