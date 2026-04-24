"""
Парсинг открытого API BIOCAD Clinical Trials → создание 15 протоколов КИ.

Источник: https://api.biocadless.com/v1/terms/nozology
Заголовок: x-biocad-app: clinicaltrials

Запуск:
    docker compose exec backend python scripts/seed_from_biocad_api.py

Что делает:
    1. Запрашивает все КИ из открытого API BIOCAD (47 записей)
    2. Дедуплицирует по терапевтическим областям, выбирает 15 штук
    3. Создаёт Protocol + ProtocolVersion (синтетический контент) + AuditLog
    4. Пропускает уже существующие (по drug_name)
"""
import asyncio
import datetime
import uuid
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.models.protocol import Protocol, ProtocolVersion, AuditLog

# ── API ───────────────────────────────────────────────────────────────────────
BIOCAD_API_URL = "https://api.biocadless.com/v1/terms/nozology"
BIOCAD_API_HEADERS = {"x-biocad-app": "clinicaltrials"}
BIOCAD_API_PARAMS = {
    "pagination": "false",
    "select": "components fields title seo excerpt slug",
}

# ── Маппинг нозологий → терапевтическая область ──────────────────────────────
NOZOLOGY_TO_AREA: dict[str, str] = {
    "рак молочной железы": "oncology",
    "рак мочевого пузыря": "oncology",
    "немелкоклеточный рак лёгкого": "oncology",
    "немелкоклеточный рак легкого": "oncology",
    "рак лёгкого": "oncology",
    "рак легкого": "oncology",
    "меланома": "oncology",
    "рак желудка": "oncology",
    "рак почки": "oncology",
    "рак шейки матки": "oncology",
    "рак яичников": "oncology",
    "рак предстательной железы": "oncology",
    "колоректальный рак": "oncology",
    "лимфома": "hematology",
    "лейкоз": "hematology",
    "миелома": "hematology",
    "псориаз": "dermatology",
    "атопический дерматит": "dermatology",
    "ревматоидный артрит": "rheumatology",
    "анкилозирующий спондилит": "rheumatology",
    "болезнь бехтерева": "rheumatology",
    "псориатический артрит": "rheumatology",
    "системная красная волчанка": "rheumatology",
    "рассеянный склероз": "neurology",
    "болезнь паркинсона": "neurology",
    "болезнь альцгеймера": "neurology",
    "сахарный диабет": "endocrinology",
    "ожирение": "endocrinology",
    "хроническая сердечная недостаточность": "cardiology",
    "ишемическая болезнь сердца": "cardiology",
    "хобл": "pulmonology",
    "бронхиальная астма": "pulmonology",
    "болезнь крона": "gastroenterology",
    "язвенный колит": "gastroenterology",
}

def _map_area(nozology_labels: list[str]) -> str:
    for label in nozology_labels:
        for key, area in NOZOLOGY_TO_AREA.items():
            if key in label.lower():
                return area
    return "oncology"

# ── Маппинг фаз ───────────────────────────────────────────────────────────────
def _map_phase(phases: list[str]) -> str | None:
    mapping = {"i": "I", "ii": "II", "iii": "III", "iv": "IV",
               "1": "I", "2": "II", "3": "III", "4": "IV"}
    for p in phases:
        cleaned = p.strip().lower().replace("фаза ", "").replace("phase ", "")
        if cleaned in mapping:
            return mapping[cleaned]
        for k, v in mapping.items():
            if k in cleaned:
                return v
    return None

# ── Генератор синтетического контента по шаблону ─────────────────────────────
def _build_content(rec: dict, area: str, phase: str) -> dict[str, str]:
    title = rec["title"]
    noz = ", ".join(rec["nozology"]) or "онкологическое заболевание"
    status = rec.get("study_status", "Активно")
    rec_status = rec.get("recruitment_status", "Набор открыт")

    area_terms = {
        "oncology": "RECIST 1.1, ORR, PFS, OS, DOR, ECOG. Ссылки: ICH E6 §6.4, RECIST guidelines.",
        "dermatology": "PASI, BSA, IGA, DLQI. Ссылки: ICH E6 §6.4.",
        "rheumatology": "ACR20, DAS28, HAQ-DI, EULAR. Ссылки: ICH E6 §6.4.",
        "hematology": "ORR (Cheson), CR, PFS, OS, Lugano 2014. Ссылки: ICH E6 §6.4.",
        "neurology": "EDSS, NIHSS, mRS, UPDRS. Ссылки: ICH E6 §6.4.",
        "cardiology": "MACE, EF, NYHA, NT-proBNP. Ссылки: ICH E6 §6.4.",
        "pulmonology": "FEV1, FVC, ACQ, AQLQ. Ссылки: ICH E6 §6.4.",
        "endocrinology": "HbA1c, FPG, BMI, HOMA-IR. Ссылки: ICH E6 §6.4.",
        "gastroenterology": "CDAI, Mayo Score, клинический ответ/ремиссия. Ссылки: ICH E6 §6.4.",
        "immunology": "ACR20, SLEDAI, BILAG. Ссылки: ICH E6 §6.4.",
    }.get(area, "стандартные клинические критерии.")

    phase_ctx = {
        "I": "Фаза I (FIH). Эскалация доз 3+3, определение MTD и RP2D. Акцент: безопасность, ФК/ФД.",
        "II": "Фаза II. Предварительная эффективность и безопасность. Дизайн: открытое или рандомизированное.",
        "III": "Фаза III. Подтверждение эффективности. РКИ, двойное слепое, компаратор или плацебо.",
        "IV": "Фаза IV. Пострегистрационное исследование. Реальная клиническая практика.",
    }.get(phase, "Клиническое исследование.")

    primary_ep = {
        "oncology": "ORR по RECIST 1.1 (CR + PR) на неделе 24",
        "dermatology": "PASI 75 на неделе 12",
        "rheumatology": "ACR20 на неделе 12",
        "hematology": "ORR по критериям Cheson после 6 циклов",
        "neurology": "Изменение EDSS от baseline на неделе 96",
        "cardiology": "MACE (сердечно-сосудистая смертность + ИМ + инсульт) на 36 мес",
        "pulmonology": "Изменение FEV1 от baseline на неделе 52",
        "endocrinology": "Изменение HbA1c от baseline на неделе 26",
        "gastroenterology": "Клиническая ремиссия на неделе 8",
        "immunology": "ACR50 на неделе 24",
    }.get(area, "Первичная конечная точка по стандарту ICH E6 §6.2")

    return {
        "title_page": f"""## Титульная страница

**Полное название:** Клиническое исследование {title} у пациентов с {noz}

**Краткое название:** {title}

**Спонсор:** АО «БИОКАД», г. Санкт-Петербург, Российская Федерация
**Фаза:** {phase}
**Статус исследования:** {status} | Набор: {rec_status}
**Нозология:** {noz}

> FOR DEMONSTRATION PURPOSES ONLY — SYNTHETIC DATA | AI-Assisted draft based on BIOCAD public registry | Требует проверки квалифицированным медицинским специалистом.
""",

        "synopsis": f"""## Краткое резюме (Synopsis)

| Параметр | Значение |
|---|---|
| Препарат | {title} |
| Нозология | {noz} |
| Фаза | {phase} — {phase_ctx} |
| Статус | {status} |
| Набор | {rec_status} |
| Первичная КТ | {primary_ep} |
| Ключевая терминология | {area_terms} |

> Данные получены из открытого реестра КИ БИОКАД (api.biocadless.com) и дополнены синтетическим контентом для демонстрационных целей.
""",

        "introduction": f"""## Введение и обоснование

### 1.1 Актуальность

{noz} является значимой медицинской проблемой, требующей новых терапевтических подходов. Настоящее исследование препарата {title} направлено на расширение доказательной базы в данной нозологии.

### 1.2 Контекст терапевтической области

Терапевтическая область: **{area}**. Ключевые методологические стандарты: {area_terms}

### 1.3 Обоснование исследования

{phase_ctx}

Существующие данные доклинических и/или ранних клинических исследований {title} свидетельствуют об обоснованности проведения данного исследования.

*[Данный раздел требует расширения квалифицированным клиническим исследователем с включением актуальных данных из публикаций и внутренней документации спонсора.]*
""",

        "objectives": f"""## Цели и задачи исследования

### Первичная цель

Оценить эффективность и/или безопасность {title} у пациентов с {noz}.

**Первичная конечная точка:** {primary_ep}

### Вторичные цели

| Цель | Конечная точка | Временная точка |
|---|---|---|
| Безопасность | Частота НЯ ≥3 ст. (CTCAE v5.0) | Всё исследование |
| Дополнительная эффективность | Вторичные КТ по стандарту {area} | Согласно расписанию визитов |
| Качество жизни | PROMs (опросники QoL) | Baseline, неделя 12, 24 |
| ФК (при наличии) | AUC, Cmax, T½ | Цикл 1, 3 |

### Применимые стандарты

ICH E6(R2), GCP ЕАЭС (Решение ЕЭК №79), 61-ФЗ, Приказ Минздрава №353н.
""",

        "design": f"""## Дизайн исследования

**Фаза:** {phase}
**Тип:** {phase_ctx}
**Статус:** {status} | Набор: {rec_status}

### Схема исследования

```
Скрининг (4 нед)
    ↓
Период лечения ({title})
    ↓
Первичная оценка ({primary_ep})
    ↓
Follow-up / EOT / Продолжение терапии
```

### Ключевые периоды

| Период | Длительность |
|---|---|
| Скрининг | До 28 дней |
| Лечение | Согласно протоколу |
| Follow-up | До 12–24 мес после EOT |

*[Подробная схема визитов и оценок подлежит разработке.]*
""",

        "population": f"""## Популяция исследования

**Нозология:** {noz}

### Критерии включения (ориентировочные)

1. Подтверждённый диагноз: {noz}
2. Возраст ≥18 лет (или согласно дизайну)
3. Адекватная функция органов (лаборатория, ЭКГ)
4. Подписанное информированное согласие (61-ФЗ, Приказ №353н)
5. Соответствие фазовым требованиям: {phase_ctx}

### Критерии исключения (ориентировочные)

1. Беременность / лактация
2. Активные инфекционные заболевания
3. Несовместимые сопутствующие заболевания
4. Предшествующая терапия, исключённая протоколом
5. Участие в других КИ <30 дней

*[Окончательные критерии подлежат разработке клиническими специалистами спонсора.]*
""",

        "statistics": f"""## Статистический анализ

### Популяции анализа

| Популяция | Определение |
|---|---|
| ITT (Intent-To-Treat) | Все рандомизированные пациенты |
| PP (Per-Protocol) | ITT без существенных нарушений |
| Safety | Все получившие ≥1 дозу |

### Первичный анализ

Первичная конечная точка: **{primary_ep}**

Метод анализа зависит от типа данных:
- Бинарные КТ: точный метод Кохрана-Мантеля-Хензеля или хи-квадрат с поправкой на страты
- Непрерывные КТ: смешанная модель повторных измерений (MMRM)
- Время-до-события: метод Каплана-Мейера, лог-ранк тест

### Обоснование размера выборки

*[Расчёт N подлежит определению биостатистиком на основе допущений об ожидаемых различиях и мощности исследования (обычно ≥80% при α=0.05).]*
""",
    }


# ── Маппинг нозологий → параметры протокола ──────────────────────────────────
AREA_DEFAULTS: dict[str, dict] = {
    "oncology": {
        "population": "Взрослые пациенты ≥18 лет с подтверждённым онкологическим заболеванием, ECOG 0-1",
        "dosing": "Согласно схеме исследования (в/в инфузия или п/к введение, дозирование определяется по массе тела или фиксированное)",
        "duration_weeks": 48,
        "secondary_endpoints": ["PFS (медиана)", "OS (12-мес)", "DoR", "Безопасность (НЯ ≥3 ст.)"],
        "inclusion_criteria": ["Возраст ≥18 лет", "Гистологически верифицированный диагноз", "ECOG 0-1", "≥1 измеримый очаг по RECIST 1.1", "Адекватная функция органов"],
        "exclusion_criteria": ["Активные метастазы ЦНС", "Активные аутоиммунные заболевания", "Системная иммуносупрессия", "Беременность/лактация"],
    },
    "dermatology": {
        "population": "Взрослые 18-75 лет со среднетяжёлой или тяжёлой формой дерматологического заболевания (PASI ≥12 или соответствующий балл активности)",
        "dosing": "Согласно схеме п/к введения (нагрузочная доза + поддерживающий режим каждые 2-4 недели)",
        "duration_weeks": 52,
        "secondary_endpoints": ["PASI 90", "IGA 0/1", "DLQI ≤5", "PASI 100 (полное очищение)"],
        "inclusion_criteria": ["Возраст 18-75 лет", "Диагноз подтверждён дерматологом", "PASI ≥12 или BSA ≥10%", "Неадекватный ответ на стандартную терапию"],
        "exclusion_criteria": ["Активный туберкулёз", "Беременность/лактация", "Предшествующая биотерапия (если исключена)", "Болезнь Крона (при анти-IL-17)"],
    },
    "rheumatology": {
        "population": "Взрослые 18-70 лет с активным ревматологическим заболеванием (DAS28 >3.2 или эквивалент), недостаточно отвечающие на стандартную терапию",
        "dosing": "Согласно схеме: п/к или в/в введение с нагрузочной и поддерживающей дозой",
        "duration_weeks": 52,
        "secondary_endpoints": ["ACR50, ACR70", "DAS28 <2.6 (ремиссия)", "HAQ-DI изменение", "Структурная прогрессия (МРТ/рентген)"],
        "inclusion_criteria": ["Возраст 18-70 лет", "Активное заболевание (DAS28 >3.2)", "Неадекватный ответ на БПВП", "Нет активного ТБ (квантиферон)"],
        "exclusion_criteria": ["Активные инфекции", "Беременность/лактация", "Тяжёлые сопутствующие заболевания", "Живые вакцины <4 нед"],
    },
    "hematology": {
        "population": "Взрослые 18-75 лет с гематологическим злокачественным заболеванием, подтверждённым гистологически, статус ECOG 0-2",
        "dosing": "Согласно схеме полихимиотерапии (в/в инфузия в определённые дни цикла)",
        "duration_weeks": 24,
        "secondary_endpoints": ["PFS 24 мес", "OS 24 мес", "CR rate", "Иммуногенность (ADA)", "ФК (AUC, Cmax)"],
        "inclusion_criteria": ["Возраст 18-75 лет", "Гистологически верифицированный диагноз", "ECOG 0-2", "Адекватная функция КМ (нейтрофилы ≥1.5×10⁹/л)", "ФВ ЛЖ ≥50%"],
        "exclusion_criteria": ["Активный гепатит B", "ВИЧ-инфекция", "Предшествующая иммунотерапия (если исключена)", "ТГСК в анамнезе"],
    },
    "neurology": {
        "population": "Взрослые 18-60 лет с неврологическим заболеванием, подтверждённым клинически и инструментально",
        "dosing": "Согласно схеме (в/в или п/к введение, различная частота)",
        "duration_weeks": 96,
        "secondary_endpoints": ["Частота рецидивов (при РС)", "МРТ-активность", "Качество жизни (EQ-5D)", "Когнитивные функции"],
        "inclusion_criteria": ["Возраст 18-60 лет", "Подтверждённый диагноз", "EDSS 0-6.5 (при РС)", "Подписанное ИС"],
        "exclusion_criteria": ["Активные инфекции", "Беременность/лактация", "МРТ-противопоказания", "Тяжёлые психиатрические расстройства"],
    },
    "cardiology": {
        "population": "Взрослые ≥18 лет с сердечно-сосудистым заболеванием высокого риска, стабильное состояние",
        "dosing": "Пероральный или парентеральный приём согласно схеме",
        "duration_weeks": 144,
        "secondary_endpoints": ["ССС-смертность", "Госпитализация по поводу СН", "ФВ ЛЖ динамика", "NT-proBNP"],
        "inclusion_criteria": ["Возраст ≥18 лет", "Подтверждённый ССЗ", "Стабильная терапия ≥3 мес", "ФВ ЛЖ согласно критериям"],
        "exclusion_criteria": ["Острый ИМ или инсульт <3 мес", "ФВ ЛЖ <25%", "Почечная недостаточность (СКФ <15)", "Беременность"],
    },
    "pulmonology": {
        "population": "Взрослые 18-70 лет с подтверждённым лёгочным заболеванием, FEV1 >30% от должного",
        "dosing": "Ингаляционный, п/к или в/в путь введения согласно форме выпуска",
        "duration_weeks": 52,
        "secondary_endpoints": ["FVC динамика", "Частота обострений", "ACQ-7 (астма)", "Качество жизни SGRQ"],
        "inclusion_criteria": ["Возраст 18-70 лет", "Подтверждённый диагноз (спирометрия)", "FEV1 >30% от должного", "Оптимальная базисная терапия"],
        "exclusion_criteria": ["ОРЗ <4 нед", "Активный ТБ", "Тяжёлые сопутствующие заболевания", "Беременность/лактация"],
    },
    "endocrinology": {
        "population": "Взрослые 18-75 лет с подтверждённым эндокринным заболеванием, получающие стандартную терапию",
        "dosing": "Пероральный или п/к приём согласно схеме",
        "duration_weeks": 52,
        "secondary_endpoints": ["FPG динамика", "Масса тела", "АД", "Липидный профиль", "Безопасность (гипогликемия)"],
        "inclusion_criteria": ["Возраст 18-75 лет", "HbA1c 7.5-11% (СД 2)", "ИМТ 25-45 (при ожирении)", "Стабильная терапия ≥3 мес"],
        "exclusion_criteria": ["СД 1 типа", "Тяжёлая почечная недостаточность", "Беременность/лактация", "АМИ/инсульт <6 мес"],
    },
    "gastroenterology": {
        "population": "Взрослые 18-65 лет с активным воспалительным заболеванием кишечника, подтверждённым эндоскопически",
        "dosing": "В/в индукция (0, 2, 6 нед) → п/к поддерживающая терапия каждые 8 нед",
        "duration_weeks": 52,
        "secondary_endpoints": ["Эндоскопическое улучшение", "Биохимическая ремиссия (СРБ, ФК)", "QoL (IBDQ)", "Кортикостероид-свободная ремиссия"],
        "inclusion_criteria": ["Возраст 18-65 лет", "Активная ВЗК (CDAI ≥220 или Mayo ≥6)", "Неадекватный ответ на стандартную терапию", "Нет активного ТБ"],
        "exclusion_criteria": ["Активные инфекции", "Стома/колостома", "Хирургическое вмешательство <4 нед", "Беременность/лактация"],
    },
    "immunology": {
        "population": "Взрослые 18-65 лет с аутоиммунным заболеванием, подтверждённым лабораторно и клинически",
        "dosing": "Согласно схеме (п/к или в/в, различная частота)",
        "duration_weeks": 52,
        "secondary_endpoints": ["Клиническая ремиссия", "Биомаркеры воспаления", "Иммуногенность (ADA)", "Безопасность"],
        "inclusion_criteria": ["Возраст 18-65 лет", "Подтверждённый диагноз", "Активная болезнь", "Неадекватный ответ на ГКС/иммуносупрессоры"],
        "exclusion_criteria": ["Активные инфекции", "Беременность/лактация", "Живые вакцины <4 нед", "Нейтропения"],
    },
}


def _build_protocol_data(rec: dict, area: str, phase: str) -> dict:
    defaults = AREA_DEFAULTS.get(area, AREA_DEFAULTS["oncology"])
    noz = ", ".join(rec["nozology"]) if rec["nozology"] else "клиническое исследование"
    title_study = rec["title"]

    primary_ep = {
        "oncology": "ORR по RECIST 1.1 (CR + PR), независимая оценка, неделя 24",
        "dermatology": "PASI 75 на неделе 12 (% пациентов с улучшением PASI ≥75%)",
        "rheumatology": "ACR20 на неделе 12 (% пациентов с улучшением ≥20% по критериям ACR)",
        "hematology": "ORR по критериям Cheson 2007 после завершения лечения",
        "neurology": "Годовая частота рецидивов (ARR) на 96 неделе",
        "cardiology": "Время до первого MACE (ССС-смертность / нефатальный ИМ / нефатальный инсульт)",
        "pulmonology": "Изменение FEV1 от baseline (мл) на неделе 52",
        "endocrinology": "Изменение HbA1c от baseline (%) на неделе 26",
        "gastroenterology": "Клиническая ремиссия на неделе 8 (CDAI <150 или Mayo ≤2)",
        "immunology": "ACR50 на неделе 24 или эквивалентный критерий активности заболевания",
    }.get(area, "Первичная конечная точка по протоколу")

    status_map = {
        "Активно": "generated",
        "Завершено": "approved",
        "Приостановлено": "draft",
    }
    proto_status = status_map.get(rec.get("study_status", "Активно"), "draft")

    return {
        "title": f"{title_study} — КИ при {noz}",
        "drug_name": title_study,
        "inn": f"{title_study} (МНН уточняется)",
        "phase": phase,
        "therapeutic_area": area,
        "indication": f"{noz}. Статус набора: {rec.get('recruitment_status', 'уточняется')}.",
        "population": defaults["population"],
        "primary_endpoint": primary_ep,
        "secondary_endpoints": defaults["secondary_endpoints"],
        "duration_weeks": defaults["duration_weeks"],
        "dosing": defaults["dosing"],
        "inclusion_criteria": defaults["inclusion_criteria"],
        "exclusion_criteria": defaults["exclusion_criteria"],
        "status": proto_status,
        "tags": [area, f"Фаза {phase}", rec.get("study_status", "Активно"), "BIOCAD", "Парсинг"],
    }


# ── Fetch API ─────────────────────────────────────────────────────────────────
async def fetch_biocad_trials() -> list[dict]:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(BIOCAD_API_URL, headers=BIOCAD_API_HEADERS, params=BIOCAD_API_PARAMS)
        resp.raise_for_status()
        data = resp.json()

    records = data.get("records", [])
    result = []
    for rec in records:
        fields = rec.get("fields", {})
        phases_raw = [p.get("label", "") for p in (fields.get("phase") or [])]
        nozology = [n.get("label", "") for n in (fields.get("nozology") or [])]
        result.append({
            "title": rec.get("title", "Unknown"),
            "slug": rec.get("slug", ""),
            "phase_raw": phases_raw,
            "study_status": (fields.get("study_status") or {}).get("label", ""),
            "recruitment_status": (fields.get("recruitment_status") or {}).get("label", ""),
            "nozology": nozology,
        })
    return result


def _select_diverse_15(records: list[dict]) -> list[tuple[dict, str, str]]:
    """Выбрать 15 записей из разных терапевтических областей."""
    area_seen: dict[str, int] = {}
    selected = []

    # Сортируем: сначала с нозологиями, потом с фазами, потом по алфавиту
    sorted_recs = sorted(
        records,
        key=lambda r: (
            len(r["nozology"]) == 0,
            len(r["phase_raw"]) == 0,
            r["title"],
        )
    )

    for rec in sorted_recs:
        if len(selected) >= 15:
            break

        phase = _map_phase(rec["phase_raw"])
        if not phase:
            phase = "II"

        area = _map_area(rec["nozology"])
        count = area_seen.get(area, 0)

        if count >= 3:
            continue

        area_seen[area] = count + 1
        selected.append((rec, area, phase))

    return selected


# ── Main ─────────────────────────────────────────────────────────────────────
async def main():
    print("\n🔍 Fetching BIOCAD Clinical Trials API...")
    records = await fetch_biocad_trials()
    print(f"   Получено записей: {len(records)}")

    selected = _select_diverse_15(records)
    print(f"   Отобрано для импорта: {len(selected)}")

    # Статистика по областям
    from collections import Counter
    area_counts = Counter(a for _, a, _ in selected)
    print(f"   Терапевтические области: {dict(area_counts)}\n")

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    created = 0
    skipped = 0

    async with Session() as db:
        # Получить все существующие drug_name для деduplication
        existing = await db.execute(select(Protocol.drug_name))
        existing_names = {row[0] for row in existing}

        for rec, area, phase in selected:
            drug_name = rec["title"]

            if drug_name in existing_names:
                print(f"   [skip] уже существует: {drug_name}")
                skipped += 1
                continue

            proto_data = _build_protocol_data(rec, area, phase)
            content = _build_content(rec, area, phase)

            pid = str(uuid.uuid4())
            proto = Protocol(
                id=pid,
                title=proto_data["title"],
                drug_name=proto_data["drug_name"],
                inn=proto_data["inn"],
                phase=proto_data["phase"],
                therapeutic_area=proto_data["therapeutic_area"],
                indication=proto_data["indication"],
                population=proto_data["population"],
                primary_endpoint=proto_data["primary_endpoint"],
                secondary_endpoints=proto_data["secondary_endpoints"],
                duration_weeks=proto_data["duration_weeks"],
                dosing=proto_data["dosing"],
                inclusion_criteria=proto_data["inclusion_criteria"],
                exclusion_criteria=proto_data["exclusion_criteria"],
                status=proto_data["status"],
                tags=proto_data["tags"],
                created_by="system",
            )
            db.add(proto)

            # AuditLog — создание
            db.add(AuditLog(
                id=str(uuid.uuid4()),
                entity_type="protocol",
                entity_id=pid,
                action="create",
                performed_by="system",
                metadata_={
                    "title": proto_data["title"],
                    "role": "system",
                    "source": "biocad_api_parser",
                    "biocad_slug": rec["slug"],
                },
            ))

            # ProtocolVersion
            ver = ProtocolVersion(
                id=str(uuid.uuid4()),
                protocol_id=pid,
                version_number=1,
                content=content,
                comment=f"Импортировано из BIOCAD Clinical Trials API. Нозология: {', '.join(rec['nozology'])}. Статус: {rec['study_status']}.",
                compliance_score=None,
                generated_by="biocad-api-parser/synthetic-template",
            )
            db.add(ver)

            # AuditLog — генерация
            db.add(AuditLog(
                id=str(uuid.uuid4()),
                entity_type="protocol",
                entity_id=pid,
                action="ai_generate",
                performed_by="system",
                metadata_={
                    "model": "synthetic-template",
                    "sections": list(content.keys()),
                    "version": 1,
                    "source": "biocad_api_parser",
                    "role": "system",
                },
            ))

            existing_names.add(drug_name)
            created += 1
            print(f"   [+] {drug_name} | {area} | Фаза {phase} | {proto_data['status']}")

        await db.commit()

    await engine.dispose()
    print(f"\n✅ Готово: создано {created}, пропущено {skipped} (уже существуют)")
    print("   Откройте http://localhost:<frontend-port>/protocols для просмотра")


if __name__ == "__main__":
    asyncio.run(main())
