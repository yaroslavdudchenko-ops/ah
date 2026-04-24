import asyncio
import logging
from typing import Optional, TYPE_CHECKING
from app.services.ai_gateway import ai_client, AIGatewayError
from app.models.protocol import Protocol

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_RAG_SECTION_INTRO = (
    "\n\n--- КОНТЕКСТ ИЗ ОДОБРЕННЫХ ПРОТОКОЛОВ (только для справки, не копировать) ---\n"
    "Ниже — аналогичные разделы из существующих протоколов. "
    "Используй их как структурный ориентир, но генерируй текст для ТЕКУЩЕГО исследования:\n\n"
)

SYSTEM_PROMPT = """Ты — эксперт по разработке клинических протоколов исследований (GCP/ICH E6 R2, GCP ЕАЭС, 61-ФЗ).
Генерируй чёткий, структурированный текст раздела протокола КИ.
Используй заголовки H2/H3. Не пиши вступлений вроде "Конечно!" или "Раздел:".
Весь контент — черновик для медицинского ревью (пометь: FOR REVIEW ONLY — SYNTHETIC DATA).
Длина раздела: 200–500 слов. Язык: русский (если не указано иное)."""

# MVP: 7 обязательных секций (FR-03.1). Расширенный набор — 12 секций (P1).
MVP_SECTIONS = [
    "introduction",
    "objectives",
    "design",
    "population",
    "treatment",
    "efficacy",
    "safety",
]

FULL_SECTIONS = [
    "title_page",
    "synopsis",
    "introduction",
    "objectives",
    "design",
    "population",
    "treatment",
    "efficacy",
    "safety",
    "statistics",
    "ethics",
    "references",
]

SECTION_PROMPTS: dict[str, str] = {
    "title_page": "Сгенерируй ТОЛЬКО раздел «Title Page» (Титульная страница) протокола КИ. Включи: название исследования, фазу, версию (DRAFT v0.1), дату.",
    "synopsis": "Сгенерируй ТОЛЬКО раздел «Synopsis» (Краткое резюме) протокола КИ. Включи: цель, дизайн, популяцию, первичную конечную точку, длительность.",
    "introduction": "Сгенерируй ТОЛЬКО раздел «Introduction & Background» (Введение и обоснование). Включи: обоснование исследования, текущий стандарт лечения, ратиональность препарата.",
    "objectives": "Сгенерируй ТОЛЬКО раздел «Study Objectives» (Цели исследования). Укажи первичную и вторичные цели. Используй терминологию ICH E6 R2 §6.2.",
    "design": "Сгенерируй ТОЛЬКО раздел «Study Design» (Дизайн исследования). Опиши тип дизайна, рандомизацию, ослепление, длительность, схему визитов.",
    "population": "Сгенерируй ТОЛЬКО раздел «Study Population» (Популяция). Включи: критерии включения, критерии исключения, ожидаемое число пациентов.",
    "treatment": "Сгенерируй ТОЛЬКО раздел «Study Treatment» (Лечение). Опиши препарат, дозирование, путь введения, продолжительность лечения.",
    "efficacy": "Сгенерируй ТОЛЬКО раздел «Efficacy Assessments» (Оценка эффективности). Укажи первичную и вторичные конечные точки, методы оценки, расписание.",
    "safety": "Сгенерируй ТОЛЬКО раздел «Safety Assessments» (Оценка безопасности). Включи: мониторинг НЯ/СНЯ, лабораторные показатели, правила отмены.",
    "statistics": "Сгенерируй ТОЛЬКО раздел «Statistical Analysis» (Статистический анализ). Включи: гипотезы, размер выборки, популяции анализа (ITT/PP/Safety), методы.",
    "ethics": "Сгенерируй ТОЛЬКО раздел «Ethics» (Этические аспекты). Включи: одобрение ЭК/ИРБ, информированное согласие (61-ФЗ), GCP ЕАЭС соответствие.",
    "references": "Сгенерируй ТОЛЬКО раздел «References» (Список литературы). Включи ≥5 релевантных научных ссылок (ICH руководства, публикации по препарату) в формате Vancouver.",
    # ── Artifacts (Appendix A & B) ────────────────────────────────────────────
    "sap": (
        "Сгенерируй ТОЛЬКО Приложение A: Statistical Analysis Plan (SAP — План статистического анализа). "
        "Включи следующие разделы:\n"
        "1. Цели анализа и статистические гипотезы (нулевая и альтернативная)\n"
        "2. Популяции анализа: ITT (Intent-to-Treat), PP (Per-Protocol), Safety Set — с определениями\n"
        "3. Первичная конечная точка: метод анализа, уровень значимости (α=0.05), поправки на множественность\n"
        "4. Вторичные конечные точки: описательная статистика\n"
        "5. Расчёт размера выборки (power analysis): мощность ≥80%, обоснование\n"
        "6. Методы обработки пропущенных данных (MCAR/MAR/MNAR, MI или MMRM)\n"
        "7. Промежуточные анализы и правила досрочного останова (если применимо)\n"
        "8. Программное обеспечение: SAS 9.4 / R ≥4.3 / Python\n"
        "Формат: заголовок «Appendix A: Statistical Analysis Plan» + структурированный markdown-текст. "
        "Пометь: DRAFT FOR REVIEW ONLY — SYNTHETIC DATA."
    ),
    "icf": (
        "Сгенерируй ТОЛЬКО Приложение B: Informed Consent Form Template (ICF — Форма информированного согласия). "
        "Включи обязательные разделы по 61-ФЗ и GCP ICH E6 R2 §4.8:\n"
        "1. Полное название исследования, спонсор, версия и дата\n"
        "2. Введение и цель исследования (простым языком для пациента)\n"
        "3. Описание процедур исследования: визиты, анализы, продолжительность\n"
        "4. Ожидаемые риски и неудобства\n"
        "5. Возможная польза для пациента и общества\n"
        "6. Альтернативные варианты лечения\n"
        "7. Конфиденциальность данных (152-ФЗ, GCP §2.11, GDPR при международном участии)\n"
        "8. Добровольность участия и право выхода без объяснения причин\n"
        "9. Компенсация и лечение в случае ущерба здоровью\n"
        "10. Контакты исследователя, спонсора и независимого ЭК\n"
        "11. Строки для подписи пациента, даты и исследователя\n"
        "Формат: заголовок «Appendix B: Informed Consent Form» + готовая к заполнению форма. "
        "Пометь: DRAFT FOR REVIEW ONLY — SYNTHETIC DATA."
    ),
}

THERAPEUTIC_AREA_CONTEXT = {
    "oncology": "терминология: RECIST 1.1, ORR, PFS, OS, DOR, ECOG. Ссылки: ICH E6 §6.4, RECIST guidelines.",
    "rheumatology": "терминология: ACR20, DAS28, HAQ-DI, EULAR. Ссылки: ICH E6 §6.4.",
    "dermatology": "терминология: PASI, BSA, IGA, DLQI. Ссылки: ICH E6 §6.4.",
    "cardiology": "терминология: MACE, EF, NYHA. Ссылки: ICH E6 §6.4.",
    "neurology": "терминология: EDSS, NIHSS, mRS. Ссылки: ICH E6 §6.4.",
}

PHASE_CONTEXT = {
    "I": "Акцент на безопасность и ФК/ФД. Язык: exploratory. Небольшая популяция.",
    "II": "Акцент на предварительную эффективность и дозирование. Язык: investigational.",
    "III": "Акцент на подтверждение эффективности. Язык: confirmatory. Сравнение с контролем.",
}


def _build_context(protocol: Protocol) -> str:
    ta_ctx = THERAPEUTIC_AREA_CONTEXT.get(
        protocol.therapeutic_area.lower(),
        f"терапевтическая область: {protocol.therapeutic_area}",
    )
    ph_ctx = PHASE_CONTEXT.get(protocol.phase, f"фаза {protocol.phase}")
    incl = "\n".join(f"  - {c}" for c in (protocol.inclusion_criteria or []))
    excl = "\n".join(f"  - {c}" for c in (protocol.exclusion_criteria or []))
    sec_ep = ", ".join(protocol.secondary_endpoints or []) or "не указаны"

    return f"""
ПАРАМЕТРЫ ПРОТОКОЛА:
- Препарат: {protocol.drug_name} ({protocol.inn})
- Фаза: {protocol.phase} — {ph_ctx}
- Терапевтическая область: {protocol.therapeutic_area} — {ta_ctx}
- Индикация: {protocol.indication}
- Популяция: {protocol.population}
- Первичная конечная точка: {protocol.primary_endpoint}
- Вторичные конечные точки: {sec_ep}
- Длительность: {protocol.duration_weeks} недель
- Дозирование: {protocol.dosing}
- Критерии включения:
{incl or "  не указаны"}
- Критерии исключения:
{excl or "  не указаны"}
""".strip()


async def _generate_section(
    section: str,
    protocol: Protocol,
    custom_prompt: str | None = None,
    rag_context: str | None = None,
) -> tuple[str, str]:
    """Generate one section. Returns (section_name, text)."""
    section_prompt = SECTION_PROMPTS.get(section, f"Сгенерируй раздел {section}")
    context_str = _build_context(protocol)
    user_prompt = f"{section_prompt}\n\n{context_str}"

    if rag_context:
        user_prompt += rag_context

    if custom_prompt:
        user_prompt += f"\n\nДОПОЛНИТЕЛЬНЫЕ ИНСТРУКЦИИ ОТ ПОЛЬЗОВАТЕЛЯ:\n{custom_prompt}"

    try:
        text = await ai_client.complete(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            max_tokens=1500,
            context={"section": section, "protocol_id": protocol.id},
        )
        return section, text
    except AIGatewayError:
        fallback = _fallback_section(section, protocol)
        logger.warning("ai_fallback_used", extra={"section": section, "protocol_id": protocol.id})
        return section, fallback


async def _fetch_rag_context(
    section: str,
    protocol: Protocol,
    db: "AsyncSession",
    current_version_ids: Optional[list[str]] = None,
) -> str | None:
    """
    Retrieve similar sections from DB for RAG augmentation.
    Returns None if RAG is disabled or no relevant results found.
    """
    try:
        from app.services.embedding_service import embed_text, find_similar_sections
        from app.core.config import settings

        if not settings.AI_EMBEDDING_URL:
            return None

        query = f"{protocol.drug_name} {protocol.indication} Phase {protocol.phase} {section}"
        query_embedding = await embed_text(query)
        if query_embedding is None:
            return None

        similar = await find_similar_sections(
            db, query_embedding, section, exclude_version_ids=current_version_ids
        )
        if not similar:
            return None

        rag_parts = []
        for i, item in enumerate(similar, 1):
            snippet = item["text"][:800].strip()
            sim_pct = int(item["similarity"] * 100)
            rag_parts.append(f"[Пример {i}, схожесть {sim_pct}%]:\n{snippet}")

        logger.info(
            "rag_context_retrieved",
            extra={"section": section, "protocol_id": protocol.id, "count": len(similar)},
        )
        return _RAG_SECTION_INTRO + "\n\n".join(rag_parts)
    except Exception as e:
        logger.warning("rag_context_failed", extra={"error": str(e), "section": section})
        return None


def _fallback_section(section: str, protocol: Protocol) -> str:
    """Template-based fallback when AI Gateway is unavailable."""
    return (
        f"## {section.replace('_', ' ').title()}\n\n"
        f"> **[TEMPLATE FALLBACK — FOR REVIEW ONLY — SYNTHETIC DATA]**\n\n"
        f"Данный раздел требует заполнения медицинским исследователем.\n\n"
        f"**Параметры:** {protocol.drug_name} ({protocol.inn}), фаза {protocol.phase}, "
        f"{protocol.indication}.\n\n"
        f"**Первичная конечная точка:** {protocol.primary_endpoint}"
    )


async def generate_protocol_sections(
    protocol: Protocol,
    sections: Optional[list[str]] = None,
    custom_prompt: str | None = None,
    db: Optional["AsyncSession"] = None,
    current_version_ids: Optional[list[str]] = None,
) -> dict[str, str]:
    """
    Generate all requested sections concurrently.
    Defaults to MVP 7 sections. Falls back to template on AI error.
    If db is provided, attempts RAG augmentation for each section.
    """
    _ARTIFACT_SECTIONS = {"sap", "icf"}
    target = sections or MVP_SECTIONS
    target = [s for s in target if s in SECTION_PROMPTS and s not in _ARTIFACT_SECTIONS]

    # Pre-fetch RAG context for all sections concurrently (if db available)
    rag_contexts: dict[str, str | None] = {}
    if db is not None:
        rag_tasks = [
            _fetch_rag_context(s, protocol, db, current_version_ids)
            for s in target
        ]
        rag_results = await asyncio.gather(*rag_tasks, return_exceptions=True)
        for s, r in zip(target, rag_results):
            rag_contexts[s] = r if isinstance(r, str) else None
    else:
        rag_contexts = {s: None for s in target}

    tasks = [
        _generate_section(s, protocol, custom_prompt=custom_prompt, rag_context=rag_contexts.get(s))
        for s in target
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    content: dict[str, str] = {}
    for r in results:
        if isinstance(r, tuple):
            section, text = r
            content[section] = text
        else:
            logger.error("section_generation_exception", extra={"error": str(r)})

    return content


async def generate_single_section(
    protocol: Protocol,
    section_key: str,
    custom_prompt: str | None = None,
    db: Optional["AsyncSession"] = None,
    current_version_ids: Optional[list[str]] = None,
) -> str:
    """FR-03.5 — Regenerate a single section, optionally with RAG context."""
    if section_key not in SECTION_PROMPTS:
        raise ValueError(f"Unknown section: {section_key}")

    rag_context: str | None = None
    if db is not None:
        rag_context = await _fetch_rag_context(section_key, protocol, db, current_version_ids)

    _, text = await _generate_section(
        section_key, protocol, custom_prompt=custom_prompt, rag_context=rag_context
    )
    return text
