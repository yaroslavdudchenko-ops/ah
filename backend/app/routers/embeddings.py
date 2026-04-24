"""
POST /api/v1/embeddings/reindex — admin-only RAG reindex endpoint.
GET  /api/v1/embeddings/status  — check embedding coverage.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/embeddings", tags=["embeddings"])


def _require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"error": {"code": "FORBIDDEN", "message": "Admin only"}})
    return current_user


@router.post("/reindex", status_code=202)
async def reindex_embeddings(
    limit: int = 200,
    force: bool = False,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(_require_admin),
):
    """
    Re-index all protocol versions that don't have embeddings yet.
    Admin only. Runs in the request (not background) for simplicity.
    Set force=true to re-embed already indexed sections.
    """
    if not settings.AI_EMBEDDING_URL:
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "EMBEDDING_NOT_CONFIGURED",
                    "message": "AI_EMBEDDING_URL is not set — RAG is disabled",
                }
            },
        )

    from app.services.embedding_service import reindex_all
    result = await reindex_all(db, limit=limit)
    return {"status": "ok", **result}


@router.get("/status")
async def embedding_status(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """
    Return RAG readiness: how many protocol versions and sections are indexed.
    Available to all authenticated users.
    """
    try:
        result = await db.execute(
            text("""
                SELECT
                    (SELECT COUNT(*) FROM protocol_versions) AS total_versions,
                    (SELECT COUNT(DISTINCT version_id) FROM protocol_embeddings) AS indexed_versions,
                    (SELECT COUNT(*) FROM protocol_embeddings) AS total_sections
            """)
        )
        row = result.fetchone()
        total_v = row[0] if row else 0
        indexed_v = row[1] if row else 0
        total_s = row[2] if row else 0

        return {
            "rag_enabled": bool(settings.AI_EMBEDDING_URL),
            "embedding_model": settings.AI_EMBEDDING_MODEL if settings.AI_EMBEDDING_URL else None,
            "total_versions": total_v,
            "indexed_versions": indexed_v,
            "total_sections": total_s,
            "coverage_pct": round((indexed_v / total_v * 100) if total_v else 0, 1),
        }
    except Exception as e:
        logger.warning("embedding_status_failed", extra={"error": str(e)})
        return {
            "rag_enabled": bool(settings.AI_EMBEDDING_URL),
            "error": "protocol_embeddings table not yet created — run migration 005",
        }
