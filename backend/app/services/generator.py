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


_FALLBACK_TEMPLATES: dict[str, str] = {
    "title_page": (
        "# Протокол клинического исследования\n\n"
        "**Название:** {title}\n\n"
        "**Препарат:** {drug_name} ({inn})\n\n"
        "**Фаза:** {phase}\n\n"
        "**Показание:** {indication}\n\n"
        "**Версия:** DRAFT v0.1 | **Дата:** [ДАТА] | **Статус:** FOR REVIEW ONLY\n\n"
        "**Спонсор:** [НАИМЕНОВАНИЕ СПОНСОРА]\n\n"
        "_Данный документ является синтетическим черновиком для медицинского ревью._"
    ),
    "synopsis": (
        "## Краткое резюме (Synopsis)\n\n"
        "**Препарат:** {drug_name} ({inn})\n\n"
        "**Фаза:** {phase} | **Длительность:** {duration_weeks} недель\n\n"
        "**Показание:** {indication}\n\n"
        "**Популяция:** {population}\n\n"
        "**Первичная конечная точка:** {primary_endpoint}\n\n"
        "**Дизайн:** [Тип дизайна — рандомизированное, двойное слепое / открытое — подлежит уточнению]\n\n"
        "**Предполагаемое число пациентов:** [N — расчёт размера выборки подлежит уточнению]\n\n"
        "_FOR REVIEW ONLY — SYNTHETIC DATA_"
    ),
    "introduction": (
        "## 1. Введение и обоснование\n\n"
        "### 1.1 Обоснование исследования\n\n"
        "[Описание нозологии: распространённость, бремя болезни, неудовлетворённая медицинская потребность "
        "при {indication}. Подлежит заполнению медицинским исследователем.]\n\n"
        "### 1.2 Текущий стандарт лечения\n\n"
        "[Действующие рекомендации и линии терапии при {indication}. Подлежит заполнению.]\n\n"
        "### 1.3 Препарат и обоснование применения\n\n"
        "**{drug_name} ({inn})** — [механизм действия, доклинические и клинические данные]. "
        "Фаза {phase} исследования направлена на [цель фазы]. Подлежит заполнению.\n\n"
        "_FOR REVIEW ONLY — SYNTHETIC DATA_"
    ),
    "objectives": (
        "## 2. Цели исследования\n\n"
        "### 2.1 Первичная цель\n\n"
        "Оценить [первичный параметр эффективности/безопасности] препарата {drug_name} ({inn}) "
        "у пациентов с {indication}.\n\n"
        "**Первичная конечная точка:** {primary_endpoint}\n\n"
        "### 2.2 Вторичные цели\n\n"
        "{secondary_endpoints_block}\n\n"
        "### 2.3 Исследовательские (exploratory) цели\n\n"
        "[Биомаркеры, фармакокинетика, качество жизни — подлежит уточнению]\n\n"
        "_FOR REVIEW ONLY — SYNTHETIC DATA_"
    ),
    "design": (
        "## 3. Дизайн исследования\n\n"
        "**Тип:** [Рандомизированное / нерандомизированное, слепое / открытое, контролируемое / однорукавное]\n\n"
        "**Фаза:** {phase}\n\n"
        "**Длительность участия пациента:** {duration_weeks} недель\n\n"
        "### 3.1 Схема визитов\n\n"
        "| Период | Визит | Неделя | Ключевые процедуры |\n"
        "|--------|-------|--------|--------------------|\n"
        "| Скрининг | V0 | −4 — −1 | [ИС, демография, включение/исключение] |\n"
        "| Лечение | V1 | 0 | [Рандомизация, начало терапии] |\n"
        "| ... | ... | ... | [Подлежит заполнению] |\n"
        "| Завершение | EoT | {duration_weeks} | [Финальная оценка] |\n\n"
        "### 3.2 Рандомизация и ослепление\n\n"
        "[Подлежит заполнению медицинским исследователем]\n\n"
        "_FOR REVIEW ONLY — SYNTHETIC DATA_"
    ),
    "population": (
        "## 4. Популяция исследования\n\n"
        "**Показание:** {indication}\n\n"
        "**Целевая популяция:** {population}\n\n"
        "### 4.1 Критерии включения\n\n"
        "{inclusion_block}\n\n"
        "### 4.2 Критерии исключения\n\n"
        "{exclusion_block}\n\n"
        "### 4.3 Предполагаемое число пациентов\n\n"
        "[N пациентов — расчёт размера выборки подлежит уточнению в разделе «Статистика»]\n\n"
        "_FOR REVIEW ONLY — SYNTHETIC DATA_"
    ),
    "treatment": (
        "## 5. Лечение / Вмешательства\n\n"
        "**Препарат:** {drug_name} ({inn})\n\n"
        "**Режим дозирования:** {dosing}\n\n"
        "**Путь введения:** [в/в инфузия / п/к / перорально — подлежит уточнению]\n\n"
        "**Продолжительность терапии:** {duration_weeks} недель\n\n"
        "### 5.1 Модификации дозы\n\n"
        "[Критерии снижения/отмены дозы — подлежит заполнению]\n\n"
        "### 5.2 Сопутствующая терапия\n\n"
        "[Разрешённые и запрещённые препараты — подлежит заполнению]\n\n"
        "_FOR REVIEW ONLY — SYNTHETIC DATA_"
    ),
    "efficacy": (
        "## 6. Оценка эффективности\n\n"
        "### 6.1 Первичная конечная точка\n\n"
        "**{primary_endpoint}**\n\n"
        "[Метод оценки, временные точки, критерии оценки — подлежит заполнению]\n\n"
        "### 6.2 Вторичные конечные точки\n\n"
        "{secondary_endpoints_block}\n\n"
        "### 6.3 Расписание оценок\n\n"
        "[Таблица расписания оценок эффективности — подлежит заполнению]\n\n"
        "_FOR REVIEW ONLY — SYNTHETIC DATA_"
    ),
    "safety": (
        "## 7. Оценка безопасности\n\n"
        "### 7.1 Нежелательные явления (НЯ)\n\n"
        "Классификация НЯ по CTCAE v5.0. Регистрация всех НЯ с момента подписания ИС "
        "до [конец периода наблюдения].\n\n"
        "### 7.2 Серьёзные нежелательные явления (СНЯ)\n\n"
        "Уведомление спонсора в течение 24 часов. Регуляторная отчётность по 61-ФЗ ст. 44.\n\n"
        "### 7.3 Лабораторные показатели\n\n"
        "[Перечень лабораторных тестов и частота — подлежит заполнению]\n\n"
        "### 7.4 Правила досрочного прекращения\n\n"
        "[Критерии отмены препарата для пациента — подлежит заполнению]\n\n"
        "_FOR REVIEW ONLY — SYNTHETIC DATA_"
    ),
    "statistics": (
        "## 8. Статистический анализ\n\n"
        "### 8.1 Гипотезы\n\n"
        "[H₀ и H₁ для первичной конечной точки — подлежит заполнению]\n\n"
        "### 8.2 Расчёт размера выборки\n\n"
        "[Мощность ≥80%, уровень значимости α=0.05, ожидаемый эффект — подлежит заполнению]\n\n"
        "### 8.3 Популяции анализа\n\n"
        "- **ITT (Intent-to-Treat):** все рандомизированные пациенты\n"
        "- **PP (Per-Protocol):** пациенты без существенных нарушений протокола\n"
        "- **Safety Set:** все пациенты, получившие ≥1 дозы препарата\n\n"
        "### 8.4 Методы статистического анализа\n\n"
        "[Методы для первичной и вторичных КТ — подлежит заполнению]\n\n"
        "_FOR REVIEW ONLY — SYNTHETIC DATA_"
    ),
    "ethics": (
        "## 9. Этические аспекты\n\n"
        "### 9.1 Одобрение регуляторных органов\n\n"
        "Исследование проводится в соответствии с:\n"
        "- ICH E6 (R2) Good Clinical Practice\n"
        "- GCP ЕАЭС (Решение Совета ЕЭК №79, ред. 2025)\n"
        "- 61-ФЗ «Об обращении лекарственных средств» (гл. 7, ст. 38–44)\n"
        "- Приказ Минздрава РФ №353н от 26.05.2021 (информированное согласие)\n\n"
        "### 9.2 Информированное согласие\n\n"
        "Подписание ИС до начала любых процедур скрининга. Форма ИС (Appendix B) "
        "подлежит одобрению Независимым этическим комитетом.\n\n"
        "### 9.3 Конфиденциальность данных\n\n"
        "Персональные данные защищены в соответствии с 152-ФЗ.\n\n"
        "_FOR REVIEW ONLY — SYNTHETIC DATA_"
    ),
    "references": (
        "## 10. Список литературы\n\n"
        "1. ICH E6 (R2) Guideline for Good Clinical Practice. International Council for Harmonisation, 2016.\n"
        "2. Решение Совета ЕЭК №79 «Правила надлежащей клинической практики ЕАЭС». 2016 (ред. 2025).\n"
        "3. 61-ФЗ «Об обращении лекарственных средств». Российская Федерация, 2010.\n"
        "4. Приказ Минздрава РФ №353н «Об утверждении формы информированного согласия». 2021.\n"
        "5. [Публикации по препарату {drug_name} / {inn} — подлежит заполнению]\n"
        "6. [Эпидемиологические данные по {indication} — подлежит заполнению]\n\n"
        "_FOR REVIEW ONLY — SYNTHETIC DATA_"
    ),
    "sap": (
        "# Appendix A: Statistical Analysis Plan (SAP)\n\n"
        "> **DRAFT FOR REVIEW ONLY — SYNTHETIC DATA**\n\n"
        "**Препарат:** {drug_name} ({inn}) | **Фаза:** {phase} | **Показание:** {indication}\n\n"
        "## A.1 Цели анализа и гипотезы\n\n"
        "**H₀:** [нулевая гипотеза для первичной КТ — подлежит заполнению]\n\n"
        "**H₁:** {primary_endpoint} — [альтернативная гипотеза — подлежит заполнению]\n\n"
        "**Уровень значимости:** α = 0.05 (двусторонний)\n\n"
        "## A.2 Популяции анализа\n\n"
        "- **ITT (Intent-to-Treat):** Все рандомизированные пациенты\n"
        "- **PP (Per-Protocol):** Без существенных нарушений протокола\n"
        "- **Safety Set:** Все, получившие ≥1 дозы {drug_name}\n\n"
        "## A.3 Первичная конечная точка\n\n"
        "**{primary_endpoint}**\n\n"
        "[Метод: логранговый тест / t-тест / Fisher — подлежит уточнению биостатистиком]\n\n"
        "## A.4 Расчёт размера выборки\n\n"
        "[N пациентов, мощность ≥80%, ожидаемый эффект — подлежит заполнению]\n\n"
        "## A.5 Обработка пропущенных данных\n\n"
        "[MCAR / MAR / MNAR, метод MI или MMRM — подлежит уточнению]\n\n"
        "## A.6 ПО для анализа\n\nSAS 9.4 / R ≥4.3 / Python\n\n"
        "_FOR REVIEW ONLY — SYNTHETIC DATA_"
    ),
    "icf": (
        "# Appendix B: Informed Consent Form (ICF)\n\n"
        "> **DRAFT FOR REVIEW ONLY — SYNTHETIC DATA**\n\n"
        "**Исследование:** {title}\n"
        "**Препарат:** {drug_name} ({inn}) | **Фаза:** {phase}\n\n"
        "## B.1 Введение\n\n"
        "Уважаемый пациент, вас приглашают принять участие в клиническом исследовании "
        "препарата {drug_name} при {indication}. Участие добровольно.\n\n"
        "## B.2 Цель исследования\n\n"
        "[Изложить цель исследования простым языком — подлежит заполнению]\n\n"
        "## B.3 Процедуры исследования\n\n"
        "Длительность участия: {duration_weeks} недель. Режим: {dosing}.\n"
        "[Описание визитов и процедур — подлежит заполнению]\n\n"
        "## B.4 Риски и неудобства\n\n"
        "[Ожидаемые НЯ — подлежит заполнению врачом-исследователем]\n\n"
        "## B.5 Конфиденциальность (152-ФЗ, GCP §2.11)\n\n"
        "Персональные данные защищены в соответствии с 152-ФЗ.\n\n"
        "## B.6 Добровольность участия\n\n"
        "Вы вправе отказаться в любое время без объяснения причин.\n\n"
        "## B.7 Подписи\n\n"
        "| | Пациент | Исследователь |\n"
        "|-|---------|---------------|\n"
        "| ФИО | __________ | __________ |\n"
        "| Дата | __________ | __________ |\n"
        "| Подпись | __________ | __________ |\n\n"
        "_FOR REVIEW ONLY — SYNTHETIC DATA_"
    ),
}


def _fallback_section(section: str, protocol: Protocol) -> str:
    """Section-specific fallback when AI Gateway is unavailable."""
    incl = protocol.inclusion_criteria or []
    excl = protocol.exclusion_criteria or []
    sec_ep = protocol.secondary_endpoints or []

    inclusion_block = (
        "\n".join(f"{i+1}. {c}" for i, c in enumerate(incl))
        if incl else "1. [Критерии включения подлежат заполнению]"
    )
    exclusion_block = (
        "\n".join(f"{i+1}. {c}" for i, c in enumerate(excl))
        if excl else "1. [Критерии исключения подлежат заполнению]"
    )
    secondary_endpoints_block = (
        "\n".join(f"{i+1}. {ep}" for i, ep in enumerate(sec_ep))
        if sec_ep else "1. [Вторичные конечные точки подлежат заполнению]"
    )

    template = _FALLBACK_TEMPLATES.get(section)
    if template:
        return template.format(
            title=protocol.title,
            drug_name=protocol.drug_name,
            inn=protocol.inn,
            phase=protocol.phase,
            indication=protocol.indication,
            population=protocol.population,
            primary_endpoint=protocol.primary_endpoint,
            duration_weeks=protocol.duration_weeks,
            dosing=protocol.dosing,
            inclusion_block=inclusion_block,
            exclusion_block=exclusion_block,
            secondary_endpoints_block=secondary_endpoints_block,
        )

    # Generic fallback for unknown sections
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
