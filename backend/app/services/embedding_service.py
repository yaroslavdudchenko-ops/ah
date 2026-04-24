"""
RAG Embedding Service — Retrieval-Augmented Generation for protocol sections.

Architecture (Phase 1 — JSONB + numpy):
  Indexing:  ProtocolVersion.content[section] → embed_text() → protocol_embeddings.embedding (JSONB)
  Retrieval: load embeddings from DB → numpy cosine_similarity → top-K above threshold
  Enhanced:  top-K similar sections → LLM prompt context → better section text

Phase 2 (future, >5000 protocols): migrate to pgvector/pgvector:pg16 + vector(1536) IVFFlat index.

Fallback: if AI Gateway embedding endpoint is unavailable → RAG silently disabled,
          generation proceeds without context (graceful degrade, never a blocking error).

Security: only synthetic/approved protocol content is indexed. No PII.
"""
import logging
import math
from typing import Optional

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)

# Sections excluded from indexing (too short / structural-only)
_SKIP_SECTIONS = {"title_page", "synopsis", "references"}

# Text truncation before embedding (token limit)
_MAX_EMBED_CHARS = 3000


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Pure Python cosine similarity. Fast enough for <5000 vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


async def embed_text(content: str) -> Optional[list[float]]:
    """
    Call AI Gateway OpenAI-compatible embeddings endpoint.
    Returns None on any failure — caller handles gracefully (skip RAG).
    """
    if not settings.AI_EMBEDDING_URL:
        return None

    text_input = content[:_MAX_EMBED_CHARS].strip()
    if not text_input:
        return None

    try:
        base = settings.AI_EMBEDDING_URL.rstrip("/")
        # AI Gateway uses /api/v2/embeddings (OpenAI-compatible, BIOCAD internal)
        url = f"{base}/api/v2/embeddings"
        # verify=False: BIOCAD internal gateway uses corporate CA not present in Alpine container
        async with httpx.AsyncClient(timeout=settings.AI_EMBEDDING_TIMEOUT, verify=False) as client:
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {settings.AI_GATEWAY_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "input": text_input,
                    "model": settings.AI_EMBEDDING_MODEL,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["data"][0]["embedding"]
    except httpx.HTTPStatusError as e:
        logger.warning(
            "embedding_http_error",
            extra={"status": e.response.status_code, "url": str(e.request.url)},
        )
        return None
    except httpx.TimeoutException:
        logger.warning("embedding_timeout", extra={"url": settings.AI_EMBEDDING_URL})
        return None
    except Exception as e:
        logger.warning("embedding_failed", extra={"error": str(e)})
        return None


async def find_similar_sections(
    db: AsyncSession,
    query_embedding: list[float],
    section_key: str,
    exclude_version_ids: Optional[list[str]] = None,
) -> list[dict]:
    """
    Find top-K similar protocol sections using cosine similarity (numpy in Python).

    Returns list of {"section": str, "text": str, "similarity": float}
    sorted by similarity DESC. Only returns results above RAG_SIMILARITY_THRESHOLD.
    Returns [] on any error (graceful fallback).
    """
    if not query_embedding:
        return []

    try:
        exclude_clause = ""
        params: dict = {"section": section_key}

        if exclude_version_ids:
            exclude_clause = "AND pe.version_id != ALL(:exclude_ids)"
            params["exclude_ids"] = exclude_version_ids

        result = await db.execute(
            text(f"""
                SELECT
                    pe.version_id,
                    pe.section_key,
                    pe.embedding,
                    pv.content->>pe.section_key AS section_text
                FROM protocol_embeddings pe
                JOIN protocol_versions pv ON pe.version_id = pv.id
                WHERE pe.section_key = :section
                  AND pe.embedding IS NOT NULL
                  {exclude_clause}
                ORDER BY pe.created_at DESC
                LIMIT 100
            """),
            params,
        )
        rows = result.fetchall()

        scored: list[dict] = []
        for version_id, sec_key, embedding_json, section_text in rows:
            if not embedding_json or not section_text:
                continue
            embedding = embedding_json if isinstance(embedding_json, list) else list(embedding_json)
            sim = _cosine_similarity(query_embedding, embedding)
            if sim >= settings.RAG_SIMILARITY_THRESHOLD:
                scored.append({
                    "section": sec_key,
                    "text": section_text,
                    "similarity": sim,
                    "version_id": version_id,
                })

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:settings.RAG_TOP_K]

    except Exception as e:
        logger.warning("find_similar_failed", extra={"error": str(e), "section": section_key})
        return []


async def index_version(
    db: AsyncSession,
    version_id: str,
    content: dict,
    force: bool = False,
) -> int:
    """
    Generate and store embeddings for all sections of a protocol version.

    Args:
        version_id: ProtocolVersion.id
        content: dict of {section_key: text}
        force: re-index even if embedding already exists

    Returns: number of sections successfully indexed.
    """
    if not settings.AI_EMBEDDING_URL:
        return 0

    indexed = 0
    for section_key, section_text in content.items():
        if section_key in _SKIP_SECTIONS:
            continue
        if not section_text or not isinstance(section_text, str) or len(section_text.strip()) < 50:
            continue

        # Check existing (skip unless force)
        if not force:
            existing = await db.execute(
                text(
                    "SELECT 1 FROM protocol_embeddings "
                    "WHERE version_id = :vid AND section_key = :sk"
                ),
                {"vid": version_id, "sk": section_key},
            )
            if existing.fetchone():
                continue

        embedding = await embed_text(section_text)
        if embedding is None:
            logger.debug(
                "embedding_skipped",
                extra={"version_id": version_id, "section": section_key},
            )
            continue

        import json as _json
        embedding_json = _json.dumps(embedding)

        await db.execute(
            text("""
                INSERT INTO protocol_embeddings (id, version_id, section_key, embedding, model)
                VALUES (gen_random_uuid(), :vid, :sk, :emb::jsonb, :model)
                ON CONFLICT (version_id, section_key) DO UPDATE
                    SET embedding = EXCLUDED.embedding,
                        model = EXCLUDED.model,
                        created_at = NOW()
            """),
            {
                "vid": version_id,
                "sk": section_key,
                "emb": embedding_json,
                "model": settings.AI_EMBEDDING_MODEL,
            },
        )
        indexed += 1

    if indexed > 0:
        await db.commit()
        logger.info(
            "index_version_done",
            extra={"version_id": version_id, "sections": indexed},
        )

    return indexed


async def reindex_all(db: AsyncSession, limit: int = 200) -> dict:
    """
    Find and index all protocol versions that have no embeddings yet.
    Called at startup and via POST /embeddings/reindex.
    """
    if not settings.AI_EMBEDDING_URL:
        return {"skipped": True, "reason": "AI_EMBEDDING_URL not configured"}

    try:
        result = await db.execute(
            text("""
                SELECT pv.id, pv.content
                FROM protocol_versions pv
                WHERE NOT EXISTS (
                    SELECT 1 FROM protocol_embeddings pe WHERE pe.version_id = pv.id
                )
                ORDER BY pv.created_at DESC
                LIMIT :limit
            """),
            {"limit": limit},
        )
        rows = result.fetchall()
    except Exception as e:
        logger.warning("reindex_all_query_failed", extra={"error": str(e)})
        return {"error": str(e)}

    total_sections = 0
    for version_id, content in rows:
        count = await index_version(db, version_id, content or {})
        total_sections += count

    logger.info(
        "reindex_all_done",
        extra={"versions": len(rows), "sections_indexed": total_sections},
    )
    return {
        "versions_processed": len(rows),
        "sections_indexed": total_sections,
    }
