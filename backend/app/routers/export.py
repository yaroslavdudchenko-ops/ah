import csv
import io
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.protocol import Protocol, ProtocolVersion, OpenIssue, AuditLog
from app.schemas.protocol import error_body
from app.services.export_service import (
    export_markdown, export_html, export_docx,
    CONTENT_TYPES, FILENAMES, ExportFormat,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/protocols", tags=["export"])


@router.get("/{protocol_id}/export")
async def export_protocol(
    protocol_id: str,
    format: ExportFormat = Query("md", description="md | html | docx"),
    version_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(
        select(Protocol)
        .options(selectinload(Protocol.open_issues))
        .where(Protocol.id == protocol_id)
    )
    protocol = result.scalar_one_or_none()
    if not protocol:
        raise HTTPException(
            status_code=404,
            detail=error_body("PROTOCOL_NOT_FOUND", f"Protocol {protocol_id} not found"),
        )

    if version_id:
        ver_result = await db.execute(
            select(ProtocolVersion).where(
                ProtocolVersion.id == version_id,
                ProtocolVersion.protocol_id == protocol_id,
            )
        )
        version = ver_result.scalar_one_or_none()
    else:
        ver_result = await db.execute(
            select(ProtocolVersion)
            .where(ProtocolVersion.protocol_id == protocol_id)
            .order_by(ProtocolVersion.version_number.desc())
            .limit(1)
        )
        version = ver_result.scalar_one_or_none()

    if not version:
        raise HTTPException(
            status_code=422,
            detail=error_body("NO_CONTENT", "No generated content. Run /generate first."),
        )

    try:
        if format == "md":
            data = export_markdown(protocol, version)
        elif format == "html":
            data = export_html(protocol, version)
        elif format == "docx":
            data = export_docx(protocol, version)
        else:
            raise HTTPException(status_code=400, detail=error_body("BAD_FORMAT", "Unknown format"))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=error_body("EXPORT_ERROR", str(exc)))

    await db.execute(
        insert(AuditLog).values(
            entity_type="protocol",
            entity_id=protocol_id,
            action="export",
            performed_by=current_user.get("sub", "unknown"),
            metadata={"format": format, "version_id": version.id, "version_number": version.version_number},
        )
    )
    await db.commit()
    logger.info("export_audit", extra={"protocol_id": protocol_id, "format": format, "user": current_user.get("sub")})

    return Response(
        content=data,
        media_type=CONTENT_TYPES[format],
        headers={"Content-Disposition": f'attachment; filename="{FILENAMES[format]}"'},
    )


@router.get("/{protocol_id}/open-issues/export")
async def export_open_issues(
    protocol_id: str,
    format: str = Query("json", description="json | csv"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """FR-07.4 — Export open issues list as JSON or CSV."""
    proto_result = await db.execute(select(Protocol).where(Protocol.id == protocol_id))
    protocol = proto_result.scalar_one_or_none()
    if not protocol:
        raise HTTPException(
            status_code=404,
            detail=error_body("PROTOCOL_NOT_FOUND", f"Protocol {protocol_id} not found"),
        )

    issues_result = await db.execute(
        select(OpenIssue)
        .where(OpenIssue.protocol_id == protocol_id)
        .order_by(OpenIssue.created_at)
    )
    issues = issues_result.scalars().all()

    if format == "json":
        payload = {
            "protocol_id": protocol_id,
            "protocol_title": protocol.title,
            "drug_name": protocol.drug_name,
            "generated_at": None,
            "issues": [
                {
                    "id": i.id,
                    "section": i.section,
                    "issue_type": i.issue_type,
                    "severity": i.severity,
                    "description": i.description,
                    "suggestion": i.suggestion,
                    "resolved": i.resolved,
                    "created_at": i.created_at.isoformat() if i.created_at else None,
                }
                for i in issues
            ],
        }
        return Response(
            content=json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
            media_type="application/json; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="open_issues.json"'},
        )

    if format == "csv":
        buf = io.StringIO()
        writer = csv.DictWriter(
            buf,
            fieldnames=["id", "section", "issue_type", "severity", "description", "suggestion", "resolved", "created_at"],
        )
        writer.writeheader()
        for i in issues:
            writer.writerow({
                "id": i.id,
                "section": i.section,
                "issue_type": i.issue_type,
                "severity": i.severity,
                "description": i.description,
                "suggestion": i.suggestion or "",
                "resolved": i.resolved,
                "created_at": i.created_at.isoformat() if i.created_at else "",
            })
        return Response(
            content=buf.getvalue().encode("utf-8-sig"),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": 'attachment; filename="open_issues.csv"'},
        )

    raise HTTPException(
        status_code=400,
        detail=error_body("BAD_FORMAT", "Supported formats: json, csv"),
    )
