import asyncio
import time
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_user, require_write
from app.models.protocol import Protocol, ProtocolVersion, AuditLog
from app.schemas.generate import GenerateRequest, GenerateStatus
from app.schemas.protocol import error_body
from app.services.generator import generate_protocol_sections, generate_single_section, MVP_SECTIONS
from app.services.ai_gateway import AIGatewayError
from app.core.prompt_guard import sanitize_custom_prompt

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/protocols", tags=["generate"])

_tasks: dict[str, dict] = {}


@router.post("/{protocol_id}/generate", status_code=status.HTTP_202_ACCEPTED)
async def start_generation(
    protocol_id: str,
    body: GenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_write),
):
    from app.schemas.protocol import error_body as _eb
    protocol = await _get_protocol_or_404(protocol_id, db)

    if protocol.status == "approved":
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=_eb(
                "PROTOCOL_APPROVED",
                "Generation is disabled for approved protocols. "
                "Create a copy or fork to start a new revision.",
            ),
        )

    safe_prompt = sanitize_custom_prompt(body.custom_prompt)

    task_id = str(uuid.uuid4())
    sections = body.sections or MVP_SECTIONS

    _tasks[task_id] = {
        "status": "pending",
        "progress": 0,
        "sections_done": [],
        "sections_total": sections,
        "version_id": None,
        "error": None,
    }

    background_tasks.add_task(
        _run_generation, task_id, protocol_id, sections, body.comment,
        current_user["username"], current_user["role"], safe_prompt,
    )
    return {"task_id": task_id}


@router.get("/{protocol_id}/generate/{task_id}", response_model=GenerateStatus)
async def get_generation_status(
    protocol_id: str,
    task_id: str,
    current_user: dict = Depends(get_current_user),
):
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail=error_body("TASK_NOT_FOUND", f"Task {task_id} not found"),
        )
    return GenerateStatus(task_id=task_id, **task)


@router.post("/{protocol_id}/sections/{section_key}/regenerate", status_code=status.HTTP_202_ACCEPTED)
async def regenerate_section(
    protocol_id: str,
    section_key: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_write),
):
    """FR-03.5 — Regenerate a single section without recreating the full protocol."""
    from app.schemas.protocol import error_body as _eb
    protocol = await _get_protocol_or_404(protocol_id, db)

    if protocol.status == "approved":
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=_eb(
                "PROTOCOL_APPROVED",
                "Regeneration is disabled for approved protocols.",
            ),
        )

    # Check latest version exists
    ver_result = await db.execute(
        select(ProtocolVersion)
        .where(ProtocolVersion.protocol_id == protocol_id)
        .order_by(ProtocolVersion.version_number.desc())
        .limit(1)
    )
    latest = ver_result.scalar_one_or_none()
    if not latest:
        raise HTTPException(
            status_code=422,
            detail=error_body("NO_CONTENT", "Generate the full protocol first."),
        )

    task_id = str(uuid.uuid4())
    _tasks[task_id] = {
        "status": "pending", "progress": 0,
        "sections_done": [], "sections_total": [section_key],
        "version_id": None, "error": None,
    }
    background_tasks.add_task(
        _run_section_regen, task_id, protocol_id, section_key,
        current_user["username"], current_user["role"],
    )
    return {"task_id": task_id, "section": section_key}


async def _run_generation(
    task_id: str, protocol_id: str, sections: list[str],
    comment: str | None, username: str, role: str,
    custom_prompt: str | None = None,
) -> None:
    _tasks[task_id]["status"] = "running"
    t0 = time.monotonic()
    async with (await _get_session()) as db:
        try:
            result = await db.execute(select(Protocol).where(Protocol.id == protocol_id))
            protocol = result.scalar_one_or_none()
            if not protocol:
                _tasks[task_id].update({"status": "failed", "error": "Protocol not found"})
                return

            content = await generate_protocol_sections(protocol, sections, custom_prompt=custom_prompt)
            duration_ms = int((time.monotonic() - t0) * 1000)

            from sqlalchemy import func as sqlfunc, update as sqla_update
            count_result = await db.execute(
                select(sqlfunc.count()).select_from(ProtocolVersion).where(
                    ProtocolVersion.protocol_id == protocol_id
                )
            )
            count = count_result.scalar() or 0

            # Archive all previous versions before creating the new one
            if count > 0:
                await db.execute(
                    sqla_update(ProtocolVersion)
                    .where(ProtocolVersion.protocol_id == protocol_id)
                    .values(is_archived=True)
                )

            version = ProtocolVersion(
                protocol_id=protocol_id,
                version_number=count + 1,
                content=content,
                comment=comment or f"AI-generated v{count + 1}",
                is_archived=False,
            )
            db.add(version)
            db.add(AuditLog(
                entity_type="protocol",
                entity_id=protocol_id,
                action="ai_generate",
                performed_by=username,
                metadata_={
                    "model": "InHouse/Qwen3.5-122B",
                    "sections": sections,
                    "version": count + 1,
                    "duration_ms": duration_ms,
                    "role": role,
                },
            ))
            await db.commit()
            await db.refresh(version)

            _tasks[task_id].update({
                "status": "completed", "progress": 100,
                "sections_done": list(content.keys()),
                "version_id": version.id,
            })
        except Exception as exc:
            logger.error("generation_failed", extra={"task_id": task_id, "error": str(exc)})
            await db.rollback()
            _tasks[task_id].update({"status": "failed", "error": str(exc)})


async def _run_section_regen(
    task_id: str, protocol_id: str, section_key: str,
    username: str, role: str,
) -> None:
    _tasks[task_id]["status"] = "running"
    t0 = time.monotonic()
    async with (await _get_session()) as db:
        try:
            result = await db.execute(select(Protocol).where(Protocol.id == protocol_id))
            protocol = result.scalar_one_or_none()
            if not protocol:
                _tasks[task_id].update({"status": "failed", "error": "Protocol not found"})
                return

            # Get latest version and patch section
            ver_result = await db.execute(
                select(ProtocolVersion)
                .where(ProtocolVersion.protocol_id == protocol_id)
                .order_by(ProtocolVersion.version_number.desc())
                .limit(1)
            )
            latest = ver_result.scalar_one_or_none()

            new_text = await generate_single_section(protocol, section_key)
            duration_ms = int((time.monotonic() - t0) * 1000)

            new_content = dict(latest.content)
            new_content[section_key] = new_text

            from sqlalchemy import func as sqlfunc, update as sqla_update
            count_result = await db.execute(
                select(sqlfunc.count()).select_from(ProtocolVersion).where(
                    ProtocolVersion.protocol_id == protocol_id
                )
            )
            count = count_result.scalar() or 0

            # Archive all previous versions before creating the new one
            await db.execute(
                sqla_update(ProtocolVersion)
                .where(ProtocolVersion.protocol_id == protocol_id)
                .values(is_archived=True)
            )

            version = ProtocolVersion(
                protocol_id=protocol_id,
                version_number=count + 1,
                content=new_content,
                comment=f"Regenerated section: {section_key}",
                is_archived=False,
            )
            db.add(version)
            db.add(AuditLog(
                entity_type="protocol", entity_id=protocol_id,
                action="section_regenerate",
                performed_by=username,
                metadata_={
                    "section": section_key, "version": count + 1,
                    "duration_ms": duration_ms, "role": role,
                },
            ))
            await db.commit()
            await db.refresh(version)

            _tasks[task_id].update({
                "status": "completed", "progress": 100,
                "sections_done": [section_key], "version_id": version.id,
            })
        except Exception as exc:
            logger.error("section_regen_failed", extra={"error": str(exc)})
            await db.rollback()
            _tasks[task_id].update({"status": "failed", "error": str(exc)})


async def _get_session():
    from app.core.database import AsyncSessionLocal
    return AsyncSessionLocal()


async def _get_protocol_or_404(protocol_id: str, db: AsyncSession) -> Protocol:
    result = await db.execute(select(Protocol).where(Protocol.id == protocol_id))
    protocol = result.scalar_one_or_none()
    if not protocol:
        raise HTTPException(
            status_code=404,
            detail=error_body("PROTOCOL_NOT_FOUND", f"Protocol {protocol_id} not found"),
        )
    return protocol
