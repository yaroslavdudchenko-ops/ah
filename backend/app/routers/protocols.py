import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_user, require_write, require_delete
from app.models.protocol import Protocol, ProtocolVersion, AuditLog
from app.schemas.protocol import (
    ProtocolCreate, ProtocolUpdate, ProtocolResponse, ProtocolListItem,
    VersionResponse, error_body,
)

# Fields allowed as suggestion sources — extensible for RAG
SUGGESTION_FIELDS = {
    "indication", "population", "primary_endpoint", "dosing",
    "drug_name", "inn", "therapeutic_area",
}

# Fields that remain mutable even on locked (versioned) protocols
_ALWAYS_MUTABLE = {"tags", "status"}
# Fields that lock the protocol for editing once it has AI-generated versions
_LOCKED_FIELDS = {
    "title", "drug_name", "inn", "phase", "therapeutic_area", "indication",
    "population", "primary_endpoint", "secondary_endpoints", "duration_weeks",
    "dosing", "inclusion_criteria", "exclusion_criteria",
}

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
    protocol = Protocol(id=protocol_id, created_by=current_user["username"], **body.model_dump())
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


@router.get("/suggestions", response_model=list[str])
async def field_suggestions(
    field: str = Query(..., description="Protocol field name to get suggestions for"),
    q: str = Query("", description="Search query (prefix/substring match)"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Return unique non-empty values for a given protocol field that match q.

    Designed to be replaced by a RAG/semantic provider in the future:
    the field + q contract is stable; the backend implementation can be
    swapped for embedding-based retrieval without changing the API surface.
    """
    if field not in SUGGESTION_FIELDS:
        raise HTTPException(
            status_code=422,
            detail=error_body("INVALID_FIELD", f"Field '{field}' is not a valid suggestion source."),
        )
    col = getattr(Protocol, field, None)
    if col is None:
        raise HTTPException(status_code=422, detail=error_body("INVALID_FIELD", "Unknown field."))

    q_stmt = select(col).where(col.isnot(None)).where(col != "")
    if q:
        q_stmt = q_stmt.where(col.ilike(f"%{q}%"))
    q_stmt = q_stmt.group_by(col).order_by(col).limit(limit)

    result = await db.execute(q_stmt)
    return [row[0] for row in result if row[0] and str(row[0]).strip()]


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

    # Check if protocol is locked (has at least one AI-generated version)
    locked_fields_in_request = set(update_data.keys()) & _LOCKED_FIELDS
    if locked_fields_in_request:
        version_count_result = await db.execute(
            select(func.count()).select_from(ProtocolVersion).where(
                ProtocolVersion.protocol_id == protocol_id
            )
        )
        version_count = version_count_result.scalar() or 0
        if version_count > 0:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=error_body(
                    "PROTOCOL_LOCKED",
                    "Protocol is locked for editing once AI content has been generated. "
                    "Core study design fields cannot be changed. Only tags and status are mutable.",
                    details=sorted(locked_fields_in_request),
                ),
            )

    # Approve cannot be done by the protocol creator (4-eyes principle)
    if update_data.get("status") == "approved":
        if protocol.created_by and protocol.created_by == current_user["username"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_body(
                    "SELF_APPROVAL_FORBIDDEN",
                    "The protocol creator cannot approve their own protocol. "
                    "A second authorized user must perform the approval (4-eyes principle, GCP).",
                ),
            )

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


@router.delete("/{protocol_id}", status_code=status.HTTP_403_FORBIDDEN)
async def delete_protocol(
    protocol_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_delete),
):
    """Deletion is permanently disabled for GCP/audit compliance.
    Protocols are retained for the full audit trail. Use status='retired' to deactivate."""
    await _get_or_404(protocol_id, db)
    db.add(AuditLog(
        entity_type="protocol", entity_id=protocol_id,
        action="delete_attempt",
        performed_by=current_user["username"],
        metadata_={"role": current_user["role"], "result": "blocked_by_policy"},
    ))
    await db.flush()
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=error_body(
            "DELETION_DISABLED",
            "Protocol deletion is disabled for GCP/ALCOA++ audit compliance. "
            "Protocols are retained indefinitely. Set status='retired' to deactivate.",
        ),
    )


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


@router.post("/{protocol_id}/fork", response_model=ProtocolResponse, status_code=status.HTTP_201_CREATED)
async def fork_protocol(
    protocol_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_write),
):
    """Create a new editable revision from a locked protocol.

    The source protocol is archived (status=archived, tag 'Archive' added).
    The fork is a fresh draft with identical study design metadata.
    """
    source = await _get_or_404(protocol_id, db)

    # Archive the source protocol
    archived_tags = list(source.tags or [])
    if "Archive" not in archived_tags:
        archived_tags.append("Archive")
    source.status = "archived"
    source.tags = archived_tags
    db.add(AuditLog(
        entity_type="protocol", entity_id=protocol_id,
        action="archived_by_fork",
        performed_by=current_user["username"],
        metadata_={"role": current_user["role"], "forked_by": current_user["username"]},
    ))

    # Create the fork
    fork_id = str(uuid.uuid4())
    fork = Protocol(
        id=fork_id,
        title=source.title,
        drug_name=source.drug_name,
        inn=source.inn,
        phase=source.phase,
        therapeutic_area=source.therapeutic_area,
        indication=source.indication,
        population=source.population,
        primary_endpoint=source.primary_endpoint,
        secondary_endpoints=list(source.secondary_endpoints or []),
        duration_weeks=source.duration_weeks,
        dosing=source.dosing,
        inclusion_criteria=list(source.inclusion_criteria or []),
        exclusion_criteria=list(source.exclusion_criteria or []),
        status="draft",
        tags=list(source.tags or []),
        template_id=source.template_id,
    )
    db.add(fork)
    db.add(AuditLog(
        entity_type="protocol", entity_id=fork_id,
        action="create",
        performed_by=current_user["username"],
        metadata_={"role": current_user["role"], "forked_from": protocol_id, "title": fork.title},
    ))
    await db.flush()
    await db.refresh(fork)
    return fork


@router.post("/{protocol_id}/copy", response_model=ProtocolResponse, status_code=status.HTTP_201_CREATED)
async def copy_protocol(
    protocol_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_write),
):
    """Create a draft copy of any protocol without archiving the source.

    Unlike /fork, the source protocol is NOT archived — this is a pure duplication
    for creating a new independent draft with the same study design metadata.
    """
    source = await _get_or_404(protocol_id, db)

    copy_id = str(uuid.uuid4())
    copy = Protocol(
        id=copy_id,
        title=f"Копия: {source.title}",
        drug_name=source.drug_name,
        inn=source.inn,
        phase=source.phase,
        therapeutic_area=source.therapeutic_area,
        indication=source.indication,
        population=source.population,
        primary_endpoint=source.primary_endpoint,
        secondary_endpoints=list(source.secondary_endpoints or []),
        duration_weeks=source.duration_weeks,
        dosing=source.dosing,
        inclusion_criteria=list(source.inclusion_criteria or []),
        exclusion_criteria=list(source.exclusion_criteria or []),
        status="draft",
        tags=list(source.tags or []),
        template_id=source.template_id,
        created_by=current_user["username"],
    )
    db.add(copy)
    db.add(AuditLog(
        entity_type="protocol", entity_id=copy_id,
        action="create",
        performed_by=current_user["username"],
        metadata_={"role": current_user["role"], "copied_from": protocol_id, "title": copy.title},
    ))
    await db.flush()
    await db.refresh(copy)
    return copy


@router.get("/{protocol_id}/diff")
async def diff_versions(
    protocol_id: str,
    v1: int,
    v2: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Compare two version snapshots section-by-section using unified diff."""
    import difflib

    await _get_or_404(protocol_id, db)

    res1 = await db.execute(
        select(ProtocolVersion).where(
            ProtocolVersion.protocol_id == protocol_id,
            ProtocolVersion.version_number == v1,
        )
    )
    ver1 = res1.scalar_one_or_none()

    res2 = await db.execute(
        select(ProtocolVersion).where(
            ProtocolVersion.protocol_id == protocol_id,
            ProtocolVersion.version_number == v2,
        )
    )
    ver2 = res2.scalar_one_or_none()

    if not ver1 or not ver2:
        raise HTTPException(
            status_code=404,
            detail=error_body("VERSION_NOT_FOUND", "One or both versions not found"),
        )

    content1: dict = ver1.content or {}
    content2: dict = ver2.content or {}
    all_sections = sorted(set(list(content1.keys()) + list(content2.keys())))

    sections_diff = []
    for section in all_sections:
        lines1 = (content1.get(section) or "").splitlines(keepends=True)
        lines2 = (content2.get(section) or "").splitlines(keepends=True)
        diff_lines = list(
            difflib.unified_diff(
                lines1, lines2,
                fromfile=f"v{v1}/{section}",
                tofile=f"v{v2}/{section}",
                lineterm="",
            )
        )
        sections_diff.append({
            "section": section,
            "changed": bool(diff_lines),
            "diff": "\n".join(diff_lines),
        })

    return {
        "protocol_id": protocol_id,
        "v1": v1,
        "v2": v2,
        "sections": sections_diff,
    }


async def _get_or_404(protocol_id: str, db: AsyncSession) -> Protocol:
    result = await db.execute(select(Protocol).where(Protocol.id == protocol_id))
    protocol = result.scalar_one_or_none()
    if not protocol:
        raise HTTPException(
            status_code=404,
            detail=error_body("PROTOCOL_NOT_FOUND", f"Protocol {protocol_id} not found"),
        )
    return protocol
