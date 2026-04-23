from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.protocol import Template
from app.schemas.protocol import TemplateResponse, error_body

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])


@router.get("", response_model=list[TemplateResponse])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Template).order_by(Template.phase, Template.name))
    return result.scalars().all()


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(
            status_code=404,
            detail=error_body("TEMPLATE_NOT_FOUND", f"Template {template_id} not found"),
        )
    return template


# P2 STUB: create/update templates via API
@router.post("", status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def create_template():
    """P2 feature — template management via API."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=error_body("NOT_IMPLEMENTED", "Template creation is a P2 feature."),
    )
