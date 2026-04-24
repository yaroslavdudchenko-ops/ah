import asyncio
import logging
from typing import Optional
from app.services.ai_gateway import ai_client, AIGatewayError
from app.models.protocol import Protocol

logger = logging.getLogger(__name__)

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
    section: str, protocol: Protocol, custom_prompt: str | None = None
) -> tuple[str, str]:
    """Generate one section. Returns (section_name, text)."""
    section_prompt = SECTION_PROMPTS.get(section, f"Сгенерируй раздел {section}")
    context_str = _build_context(protocol)
    user_prompt = f"{section_prompt}\n\n{context_str}"
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
) -> dict[str, str]:
    """
    Generate all requested sections concurrently.
    Defaults to MVP 7 sections. Falls back to template on AI error.
    """
    # SAP and ICF are on-demand artifacts — excluded from bulk auto-generation
    _ARTIFACT_SECTIONS = {"sap", "icf"}
    target = sections or MVP_SECTIONS
    target = [s for s in target if s in SECTION_PROMPTS and s not in _ARTIFACT_SECTIONS]

    tasks = [_generate_section(s, protocol, custom_prompt=custom_prompt) for s in target]
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
    protocol: Protocol, section_key: str, custom_prompt: str | None = None
) -> str:
    """FR-03.5 — Regenerate a single section."""
    if section_key not in SECTION_PROMPTS:
        raise ValueError(f"Unknown section: {section_key}")
    _, text = await _generate_section(section_key, protocol, custom_prompt=custom_prompt)
    return text
