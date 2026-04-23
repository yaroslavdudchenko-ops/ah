from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.protocol import Protocol, ProtocolVersion
from app.schemas.protocol import error_body
from app.services.export_service import (
    export_markdown, export_html, export_docx,
    CONTENT_TYPES, FILENAMES, ExportFormat,
)

router = APIRouter(prefix="/api/v1/protocols", tags=["export"])


@router.get("/{protocol_id}/export")
async def export_protocol(
    protocol_id: str,
    format: ExportFormat = Query("md", description="md | html | docx"),
    version_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
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
            # P2 feature — fully implemented in export_service.py
            data = export_docx(protocol, version)
        else:
            raise HTTPException(status_code=400, detail=error_body("BAD_FORMAT", "Unknown format"))
    except NotImplementedError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=error_body("NOT_IMPLEMENTED", f"Format '{format}' is a P2 feature."),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=error_body("EXPORT_ERROR", str(exc)),
        )

    filename = FILENAMES[format]
    content_type = CONTENT_TYPES[format]
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
