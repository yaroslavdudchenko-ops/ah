from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.protocol import Protocol, ProtocolVersion, OpenIssue, AuditLog
from app.schemas.generate import CheckRequest, CheckResponse
from app.schemas.protocol import error_body
from app.services.consistency import check_consistency

router = APIRouter(prefix="/api/v1/protocols", tags=["check"])


@router.post("/{protocol_id}/check", response_model=CheckResponse)
async def check_protocol(
    protocol_id: str,
    body: CheckRequest,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Protocol).where(Protocol.id == protocol_id))
    protocol = result.scalar_one_or_none()
    if not protocol:
        raise HTTPException(
            status_code=404,
            detail=error_body("PROTOCOL_NOT_FOUND", f"Protocol {protocol_id} not found"),
        )

    # Get specified version or latest
    if body.version_id:
        ver_result = await db.execute(
            select(ProtocolVersion).where(
                ProtocolVersion.id == body.version_id,
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
            detail=error_body(
                "NO_CONTENT",
                "Protocol has no generated content. Run /generate first.",
            ),
        )

    check_result = await check_consistency(version.content, protocol.title)

    # Persist high-severity issues as open_issues
    for issue in check_result.issues:
        if issue.severity == "high":
            db.add(OpenIssue(
                protocol_id=protocol_id,
                section=issue.section,
                issue_type=issue.type,
                severity=issue.severity,
                description=issue.description,
                suggestion=issue.suggestion,
            ))

    # Update compliance_score on version
    version.compliance_score = check_result.compliance_score
    db.add(AuditLog(
        entity_type="protocol",
        entity_id=protocol_id,
        action="consistency_check",
        metadata_={
            "compliance_score": check_result.compliance_score,
            "rf_compliance_score": check_result.rf_compliance_score,
            "issues_count": len(check_result.issues),
        },
    ))
    await db.commit()

    return check_result
