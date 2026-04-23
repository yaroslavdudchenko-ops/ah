import asyncio
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.protocol import Protocol, ProtocolVersion, AuditLog
from app.schemas.generate import GenerateRequest, GenerateStatus
from app.schemas.protocol import error_body
from app.services.generator import generate_protocol_sections, MVP_SECTIONS
from app.services.ai_gateway import AIGatewayError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/protocols", tags=["generate"])

# In-memory task store for MVP (replace with Redis/DB for production)
_tasks: dict[str, dict] = {}


@router.post("/{protocol_id}/generate", status_code=status.HTTP_202_ACCEPTED)
async def start_generation(
    protocol_id: str,
    body: GenerateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    protocol = await _get_protocol_or_404(protocol_id, db)
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

    background_tasks.add_task(_run_generation, task_id, protocol_id, sections, body.comment)
    return {"task_id": task_id}


@router.get("/{protocol_id}/generate/{task_id}", response_model=GenerateStatus)
async def get_generation_status(protocol_id: str, task_id: str):
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail=error_body("TASK_NOT_FOUND", f"Task {task_id} not found"),
        )
    return GenerateStatus(task_id=task_id, **task)


async def _run_generation(
    task_id: str, protocol_id: str, sections: list[str], comment: str | None
) -> None:
    _tasks[task_id]["status"] = "running"
    async with (await _get_session()) as db:
        try:
            result = await db.execute(select(Protocol).where(Protocol.id == protocol_id))
            protocol = result.scalar_one_or_none()
            if not protocol:
                _tasks[task_id].update({"status": "failed", "error": "Protocol not found"})
                return

            content = await generate_protocol_sections(protocol, sections)

            # Determine next version number
            from sqlalchemy import func
            count_result = await db.execute(
                select(func.count()).select_from(ProtocolVersion).where(
                    ProtocolVersion.protocol_id == protocol_id
                )
            )
            count = count_result.scalar() or 0
            version = ProtocolVersion(
                protocol_id=protocol_id,
                version_number=count + 1,
                content=content,
                comment=comment,
            )
            db.add(version)
            db.add(AuditLog(
                entity_type="protocol",
                entity_id=protocol_id,
                action="ai_generate",
                metadata_={
                    "model": "InHouse/Qwen3.5-122B",
                    "sections": sections,
                    "version": count + 1,
                },
            ))
            await db.commit()
            await db.refresh(version)

            _tasks[task_id].update({
                "status": "completed",
                "progress": 100,
                "sections_done": list(content.keys()),
                "version_id": version.id,
            })
        except Exception as exc:
            logger.error("generation_failed", extra={"task_id": task_id, "error": str(exc)})
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
