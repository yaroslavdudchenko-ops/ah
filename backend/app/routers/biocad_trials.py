"""
GET /api/v1/biocad-trials — проксирование открытого реестра КИ БИОКАД.

Источник: https://api.biocadless.com/v1/terms/nozology
Данные публично доступны, заголовок x-biocad-app: clinicaltrials.
"""
import httpx
from fastapi import APIRouter, HTTPException, Query
from app.core.security import get_current_user
from fastapi import Depends

BIOCAD_API_URL = "https://api.biocadless.com/v1/terms/nozology"
BIOCAD_HEADERS = {"x-biocad-app": "clinicaltrials"}
BIOCAD_PARAMS = {
    "pagination": "false",
    "select": "components fields title seo excerpt slug",
}

router = APIRouter(prefix="/api/v1/biocad-trials", tags=["biocad-trials"])


@router.get("")
async def list_biocad_trials(
    area: str | None = Query(None, description="Фильтр по терапевтической области (oncology, dermatology, ...)"),
    phase: str | None = Query(None, description="Фильтр по фазе (I, II, III, IV)"),
    _: dict = Depends(get_current_user),
):
    """
    Список клинических исследований БИОКАД из открытого реестра.

    Парсит api.biocadless.com в реальном времени и возвращает нормализованный список.
    Данные публичны — API ключ не требуется (только заголовок x-biocad-app).
    """
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(BIOCAD_API_URL, headers=BIOCAD_HEADERS, params=BIOCAD_PARAMS)
            resp.raise_for_status()
            raw = resp.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail={"error": {"code": "UPSTREAM_TIMEOUT", "message": "BIOCAD API timeout"}})
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail={"error": {"code": "UPSTREAM_ERROR", "message": str(e)}})

    records = raw.get("records", [])
    result = []
    for rec in records:
        fields = rec.get("fields", {})
        phases = [p.get("label", "") for p in (fields.get("phase") or [])]
        nozology = [n.get("label", "") for n in (fields.get("nozology") or [])]
        study_status = (fields.get("study_status") or {}).get("label", "")
        rec_status = (fields.get("recruitment_status") or {}).get("label", "")

        normalized = {
            "title": rec.get("title", ""),
            "slug": rec.get("slug", ""),
            "phase": "–".join(phases) if phases else None,
            "study_status": study_status,
            "recruitment_status": rec_status,
            "nozology": nozology,
        }

        # Фильтр по фазе
        if phase and phase.upper() not in [p.upper() for p in phases]:
            continue

        result.append(normalized)

    return {
        "total": len(result),
        "source": "api.biocadless.com",
        "records": result,
    }
