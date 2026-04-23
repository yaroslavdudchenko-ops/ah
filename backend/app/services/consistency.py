import json
import logging
from app.services.ai_gateway import ai_client, AIGatewayError
from app.schemas.generate import CheckResponse, IssueItem, GcpHint

logger = logging.getLogger(__name__)

CONSISTENCY_SYSTEM_PROMPT = """Ты — эксперт GCP/ICH по проверке клинических протоколов.
Анализируй текст протокола на: терминологические несоответствия, логические противоречия между разделами,
нарушения следующих стандартов:
- ICH E6 (R2) — международный стандарт GCP
- GCP ЕАЭС (Решение Совета ЕЭК №79 от 03.11.2016, ред. Решения №63 от 01.08.2025) — основной действующий стандарт GCP в РФ
  (Приказ Минздрава №200н утратил силу с 01.09.2024, применяется GCP ЕАЭС)
- 61-ФЗ «Об обращении лекарственных средств» глава 7 (ст.38–44) — правовая основа КИ в РФ
- Приказ Минздрава №353н от 26.05.2021 — информированное согласие
- Приказ Минздрава №75н от 17.02.2025 — внесение изменений в протокол КИ
- Приказ Минздрава №708н от 23.12.2024 — реестр разрешений на КИ
- Решение Совета ЕЭК №77 от 03.11.2016 — Правила GMP ЕАЭС для исследуемых лекарственных препаратов
- 152-ФЗ — защита персональных данных участников

Верни JSON строго в формате:
{
  "compliance_score": <int 0-100>,
  "rf_compliance_score": <int 0-100>,
  "issues": [
    {"type": <str>, "severity": "high|medium|low", "section": <str>, "description": <str>, "suggestion": <str>}
  ],
  "gcp_hints": [
    {"category": "ICH E6|GCP ЕАЭС|61-ФЗ|Приказ №353н|Приказ №75н|Решение ЕЭК №77", "priority": "high|medium|low", "recommendation": <str>, "gcp_reference": <str>}
  ],
  "summary": <str>,
  "rf_summary": <str>
}
Только JSON, без комментариев."""

VALID_ISSUE_TYPES = {
    "terminology_mismatch",
    "endpoint_mismatch",
    "population_inconsistency",
    "duration_mismatch",
    "dosing_inconsistency",
    "sample_size_endpoint",
    "gcp_gap",
    "rf_compliance_gap",
}


async def check_consistency(content: dict[str, str], protocol_title: str) -> CheckResponse:
    sections_text = "\n\n".join(
        f"### {k.upper()}\n{v}" for k, v in content.items() if v
    )
    user_prompt = f"Протокол: {protocol_title}\n\n{sections_text[:12000]}"

    try:
        raw = await ai_client.complete(
            system_prompt=CONSISTENCY_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=2000,
            context={"action": "consistency_check"},
        )
        data = _parse_response(raw)
        return CheckResponse(**data)
    except AIGatewayError as exc:
        logger.warning("consistency_check_gateway_error", extra={"error": str(exc)})
        return _fallback_response()
    except Exception as exc:
        logger.error("consistency_check_parse_error", extra={"error": str(exc)})
        return _fallback_response()


def _parse_response(raw: str) -> dict:
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON found in AI response")
    data = json.loads(raw[start:end])
    data.setdefault("compliance_score", 50)
    data.setdefault("rf_compliance_score", 50)
    data.setdefault("issues", [])
    data.setdefault("gcp_hints", [])
    data.setdefault("summary", "Проверка выполнена.")
    data.setdefault("rf_summary", "РФ-соответствие проверено.")
    return data


def _fallback_response() -> CheckResponse:
    return CheckResponse(
        compliance_score=0,
        rf_compliance_score=0,
        issues=[
            IssueItem(
                type="gcp_gap",
                severity="high",
                section="all",
                description="AI Gateway недоступен. Автоматическая проверка консистентности невозможна.",
                suggestion="Проведите ручную проверку по чеклисту ICH E6 R2.",
            )
        ],
        gcp_hints=[
            GcpHint(
                category="ICH E6",
                priority="high",
                recommendation="Проверьте вручную соответствие протокола ICH E6 R2 §6 и GCP ЕАЭС.",
                gcp_reference="ICH E6 R2 §6",
            )
        ],
        summary="Проверка не выполнена — AI Gateway недоступен.",
        rf_summary="РФ-проверка не выполнена — AI Gateway недоступен.",
    )
