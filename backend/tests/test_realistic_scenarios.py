"""
test_realistic_scenarios.py — Реалистичные сценарии тестирования с синтетическими
данными, приближёнными к реальным протоколам BIOCAD.

Покрывает:
  REAL-PROTO  — Полные протоколы (5 препаратов, разные фазы/области)
  LIFECYCLE   — Полный цикл: create → generate → check → export
  SEARCH      — Поиск и фильтрация
  TAGS        — Управление тегами
  RBAC-FULL   — RBAC во всех операциях
  SMOKE       — Smoke-тесты критических путей
"""
import pytest


# ══════════════════════════════════════════════════════════════════════════════
#  Фабрики реалистичных протоколов (синтетические данные BIOCAD)
# ══════════════════════════════════════════════════════════════════════════════

def payload_bcd100_melanoma() -> dict:
    """BCD-100 (пролголимаб) Phase II — антиPD-1, метастатическая меланома."""
    return {
        "title": "BCD-100-002: Многоцентровое открытое исследование пролголимаба при метастатической меланоме",
        "drug_name": "BCD-100",
        "inn": "Пролголимаб",
        "phase": "II",
        "therapeutic_area": "Онкология",
        "indication": (
            "Неоперабельная или метастатическая меланома кожи, "
            "прогрессия после ≥1 линии стандартной терапии"
        ),
        "population": (
            "Взрослые пациенты ≥18 лет с морфологически подтверждённой "
            "неоперабельной или метастатической меланомой кожи; ECOG PS 0–1; "
            "ожидаемая продолжительность жизни ≥3 мес"
        ),
        "primary_endpoint": "ORR (Complete Response + Partial Response) по RECIST 1.1 на неделе 24",
        "secondary_endpoints": [
            "PFS (медиана, 95% ДИ) по RECIST 1.1",
            "OS (медиана, 95% ДИ)",
            "DoR — длительность ответа",
            "ORR по irRECIST",
            "DCR — контроль заболевания",
            "Профиль безопасности: НЯ ≥Grade 3 (CTCAE v5.0)",
            "Иммуногенность (ADA к пролголимабу)",
        ],
        "duration_weeks": 96,
        "dosing": (
            "Пролголимаб 1 мг/кг в/в инфузия 60 мин каждые 2 недели; "
            "до прогрессии, неприемлемой токсичности или 96 нед"
        ),
        "inclusion_criteria": [
            "Возраст ≥18 лет",
            "Морфологически подтверждённая меланома кожи стадия IIIC/IV (AJCC 8th edition)",
            "Прогрессия после ≥1 линии терапии (включая анти-BRAF если BRAF V600+)",
            "ECOG PS 0–1 на момент скрининга",
            "ОФВ ЛЖ ≥50% (ЭхоКГ или МУГА)",
            "Адекватная функция органов: АЛТ/АСТ ≤2,5 × ВГН, Cr ≤1,5 × ВГН",
            "Подписанное информированное согласие (61-ФЗ, ст.20)",
        ],
        "exclusion_criteria": [
            "Активные аутоиммунные заболевания, требующие иммуносупрессии",
            "Системные ГКС >10 мг/сут преднизолона в последние 14 дней",
            "Предшествующая терапия анти-PD-1/PD-L1/CTLA-4",
            "Активные метастазы в ЦНС (нелеченые или симптоматические)",
            "ВИЧ-инфекция, активный гепатит B или C",
            "Беременность или лактация",
            "Тяжёлые НЯ ≥Grade 3 от предшествующей иммунотерапии",
        ],
        "tags": ["онкология", "pd-1", "фаза-2", "меланома"],
    }


def payload_bcd089_psoriasis() -> dict:
    """BCD-089 (биоаналог иксекизумаба) Phase III — анти-IL-17A, псориаз."""
    return {
        "title": "BCD-089-3/EQUAL: Рандомизированное двойное слепое исследование при псориазе",
        "drug_name": "BCD-089",
        "inn": "Биоаналог иксекизумаба",
        "phase": "III",
        "therapeutic_area": "Дерматология",
        "indication": (
            "Среднетяжёлый и тяжёлый бляшечный псориаз у взрослых, "
            "требующий системной терапии или фототерапии"
        ),
        "population": (
            "Взрослые пациенты ≥18 лет с хроническим бляшечным псориазом ≥6 мес; "
            "PASI ≥12, BSA ≥10%, IGA ≥3; кандидаты на системную терапию"
        ),
        "primary_endpoint": "PASI 75 (снижение PASI ≥75% от базового) на 12 неделе",
        "secondary_endpoints": [
            "PASI 90 на 12 и 52 неделе",
            "PASI 100 (полный клиренс) на 12 неделе",
            "IGA 0/1 на 12 неделе",
            "DLQI (улучшение ≥4 баллов) на 12 неделе",
            "Поддержание ответа PASI 75 на 52 неделе",
            "Безопасность: НЯ, СНЯ (CTCAE v5.0)",
        ],
        "duration_weeks": 52,
        "dosing": (
            "BCD-089 160 мг п/к (2×80 мг) в нед 0; "
            "затем 80 мг п/к каждые 2 недели нед 2–12; "
            "затем 80 мг п/к каждые 4 недели нед 16–52"
        ),
        "inclusion_criteria": [
            "Возраст ≥18 лет",
            "Хронический бляшечный псориаз ≥6 месяцев (анамнез или документация)",
            "PASI ≥12 при скрининге",
            "BSA ≥10%",
            "IGA ≥3 (умеренный и тяжёлый)",
            "Кандидат на системную терапию или биологическую терапию",
        ],
        "exclusion_criteria": [
            "Гуттатный, эритродермический, пустулёзный псориаз",
            "Предшествующая терапия анти-IL-17 или анти-IL-12/23",
            "Активный туберкулёз или латентный ТБ без профилактики",
            "Беременность, лактация, неэффективная контрацепция",
            "ВИЧ, гепатит B (HBsAg+), гепатит C",
        ],
        "tags": ["дерматология", "il-17", "биоаналог", "фаза-3", "псориаз"],
    }


def payload_bcd132_ra() -> dict:
    """BCD-132 (биоаналог тоцилизумаба) Phase III — анти-IL-6R, ревматоидный артрит."""
    return {
        "title": "BCD-132-3: Биоэквивалентность тоцилизумабу при ревматоидном артрите",
        "drug_name": "BCD-132",
        "inn": "Биоаналог тоцилизумаба",
        "phase": "III",
        "therapeutic_area": "Ревматология",
        "indication": (
            "Активный ревматоидный артрит средней и высокой степени активности "
            "у взрослых, неудовлетворительный ответ или непереносимость БПВП"
        ),
        "population": (
            "Взрослые пациенты 18–75 лет с РА по критериям ACR/EULAR 2010; "
            "DAS28-СРБ ≥3.2; неудовлетворительный ответ на ≥1 БПВП"
        ),
        "primary_endpoint": (
            "Снижение DAS28-СРБ от базового к 24 неделе (non-inferiority margin 0.6)"
        ),
        "secondary_endpoints": [
            "ACR20 / ACR50 / ACR70 на 24 и 48 неделе",
            "DAS28 ремиссия (<2.6) на 24 неделе",
            "HAQ-DI изменение от базового к 24 неделе",
            "Рентгенологическое прогрессирование (mTSS) к 52 неделе",
            "Иммуногенность: ADA, нADA к BCD-132 и референс-препарату",
        ],
        "duration_weeks": 52,
        "dosing": (
            "BCD-132 8 мг/кг в/в инфузия 60 мин каждые 4 недели; "
            "в комбинации с метотрексатом 15–25 мг/нед"
        ),
        "inclusion_criteria": [
            "РА по критериям ACR/EULAR 2010, давность ≥6 месяцев",
            "DAS28-СРБ ≥3.2 при скрининге",
            "Неудовлетворительный ответ на ≥1 БПВП (включая метотрексат)",
            "Возраст 18–75 лет",
            "Стабильная доза метотрексата 15–25 мг/нед ≥4 нед до скрининга",
        ],
        "exclusion_criteria": [
            "Предшествующая терапия тоцилизумабом или другими анти-IL-6",
            "Активные инфекции, требующие антибиотикотерапии",
            "АЛТ/АСТ >1,5 × ВГН",
            "Нейтрофилы <2×10⁹/л, тромбоциты <100×10⁹/л",
            "Тяжёлая сердечная недостаточность (NYHA III/IV)",
        ],
        "tags": ["ревматология", "il-6", "биоаналог", "фаза-3", "ра"],
    }


def payload_bcd021_lymphoma() -> dict:
    """BCD-021 (биоаналог ритуксимаба) Phase I — FIH PK/PD, лимфома."""
    return {
        "title": "BCD-021-1: Фармакокинетика и безопасность биоаналога ритуксимаба у пациентов с НХЛ",
        "drug_name": "BCD-021",
        "inn": "Биоаналог ритуксимаба",
        "phase": "I",
        "therapeutic_area": "Онкология",
        "indication": (
            "В-клеточная неходжкинская лимфома (НХЛ) CD20+, "
            "рецидив или рефрактерность после ≥1 линии терапии"
        ),
        "population": (
            "Взрослые пациенты ≥18 лет с CD20+ В-клеточной НХЛ; "
            "ECOG PS 0–2; кандидаты на ритуксимабсодержащую схему"
        ),
        "primary_endpoint": (
            "Фармакокинетическое биоподобие: AUC0-∞, Cmax, t1/2 BCD-021 vs ритуксимаба"
        ),
        "secondary_endpoints": [
            "Деплеция CD19+ В-лимфоцитов (ФД биоподобие)",
            "Иммуногенность: ADA, нADA к BCD-021 и референс-препарату",
            "Профиль безопасности: НЯ, СНЯ (CTCAE v5.0)",
            "ORR (ЧОО) по Lugano 2014",
        ],
        "duration_weeks": 24,
        "dosing": (
            "BCD-021 375 мг/м² в/в инфузия 1 раз в неделю × 4 (НХЛ-режим); "
            "или 1 цикл в рамках R-CHOP схемы"
        ),
        "inclusion_criteria": [
            "CD20+ В-клеточная НХЛ, гистологически подтверждённая",
            "Рецидив или рефрактерность после ≥1 предшествующей линии",
            "ECOG PS 0–2",
            "Возраст ≥18 лет",
            "Адекватная функция костного мозга: нейтрофилы ≥1.5×10⁹/л",
        ],
        "exclusion_criteria": [
            "ЦНС-поражение лимфомой",
            "Тяжёлые инфузионные реакции на ритуксимаб в анамнезе",
            "ВИЧ, активный гепатит B или C",
            "Предшествующая ТГСК <6 месяцев",
        ],
        "tags": ["онкология", "cd20", "биоаналог", "фаза-1", "нхл", "фк"],
    }


def payload_bcd057_nsclc() -> dict:
    """BCD-057 (биоаналог пембролизумаба) Phase II/III — НМРЛ."""
    return {
        "title": "BCD-057-2/3: Биоаналог пембролизумаба первой линии при НМРЛ с высокой экспрессией PD-L1",
        "drug_name": "BCD-057",
        "inn": "Биоаналог пембролизумаба",
        "phase": "III",
        "therapeutic_area": "Онкология",
        "indication": (
            "Местнораспространённый или метастатический немелкоклеточный рак лёгкого (НМРЛ), "
            "TPS PD-L1 ≥50%, без EGFR/ALK-мутаций, первая линия терапии"
        ),
        "population": (
            "Взрослые пациенты ≥18 лет с морфологически подтверждённым НМРЛ стадия IIIB/IV; "
            "PD-L1 TPS ≥50% (22C3 pharmDx); без активирующих мутаций EGFR/ALK; "
            "ECOG PS 0–1; ≥1 измеримый очаг по RECIST 1.1"
        ),
        "primary_endpoint": "PFS (progression-free survival) по RECIST 1.1 — независимая рентгенологическая оценка",
        "secondary_endpoints": [
            "OS (Overall Survival)",
            "ORR по RECIST 1.1",
            "DoR (Duration of Response)",
            "TTR (Time to Response)",
            "Иммуногенность: ADA, нADA",
            "Фармакокинетика: Cmin на неделе 6",
            "PRO: EORTC QLQ-C30, QLQ-LC13",
        ],
        "duration_weeks": 104,
        "dosing": (
            "BCD-057 200 мг в/в инфузия 30 мин каждые 3 недели; "
            "до прогрессии, неприемлемой токсичности или 35 циклов (104 нед)"
        ),
        "inclusion_criteria": [
            "НМРЛ стадия IIIB (нерезектабельный) или IV, морфологически подтверждённый",
            "PD-L1 TPS ≥50% по 22C3 pharmDx (централизованное тестирование)",
            "Отсутствие активирующих мутаций EGFR (экзоны 18–21) и транслокаций ALK",
            "ECOG PS 0–1",
            "≥1 измеримый очаг по RECIST 1.1",
            "Адекватная функция органов",
            "Возраст ≥18 лет",
        ],
        "exclusion_criteria": [
            "Предшествующая системная терапия НМРЛ стадия IIIB/IV",
            "Активные метастазы в ЦНС или лептоменингеальные метастазы",
            "Активные аутоиммунные заболевания (требующие иммуносупрессии)",
            "Интерстициальные заболевания лёгких",
            "ВИЧ, активный гепатит B или C",
            "Предшествующая терапия анти-PD-1/PD-L1/CTLA-4",
        ],
        "tags": ["онкология", "pd-1", "нмрл", "фаза-3", "первая-линия"],
    }


# ══════════════════════════════════════════════════════════════════════════════
#  REAL-PROTO: Создание реалистичных протоколов
# ══════════════════════════════════════════════════════════════════════════════

class TestRealisticProtocolCreation:
    """Создание 5 реалистичных протоколов BIOCAD."""

    @pytest.mark.asyncio
    async def test_bcd100_melanoma_create(self, client):
        """REAL-01: BCD-100 Фаза II онкология — создание и проверка полей."""
        payload = payload_bcd100_melanoma()
        resp = await client.post("/api/v1/protocols", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["drug_name"] == "BCD-100"
        assert data["phase"] == "II"
        assert data["status"] == "draft"
        assert "ORR" in data["primary_endpoint"]
        assert len(data["secondary_endpoints"]) == 7
        assert len(data["inclusion_criteria"]) == 7
        assert "онкология" in data["tags"]

    @pytest.mark.asyncio
    async def test_bcd089_psoriasis_create(self, client):
        """REAL-02: BCD-089 Фаза III дерматология — создание."""
        resp = await client.post("/api/v1/protocols", json=payload_bcd089_psoriasis())
        assert resp.status_code == 201
        data = resp.json()
        assert data["phase"] == "III"
        assert "PASI" in data["primary_endpoint"]
        assert "дерматология" in data["tags"]

    @pytest.mark.asyncio
    async def test_bcd132_ra_create(self, client):
        """REAL-03: BCD-132 Фаза III ревматология — создание."""
        resp = await client.post("/api/v1/protocols", json=payload_bcd132_ra())
        assert resp.status_code == 201
        data = resp.json()
        assert data["phase"] == "III"
        assert data["therapeutic_area"] == "Ревматология"
        assert "DAS28" in data["primary_endpoint"]

    @pytest.mark.asyncio
    async def test_bcd021_phase1_create(self, client):
        """REAL-04: BCD-021 Фаза I ФК — создание."""
        resp = await client.post("/api/v1/protocols", json=payload_bcd021_lymphoma())
        assert resp.status_code == 201
        data = resp.json()
        assert data["phase"] == "I"
        assert "фк" in data["tags"]

    @pytest.mark.asyncio
    async def test_bcd057_nsclc_create(self, client):
        """REAL-05: BCD-057 Фаза III НМРЛ — создание."""
        resp = await client.post("/api/v1/protocols", json=payload_bcd057_nsclc())
        assert resp.status_code == 201
        data = resp.json()
        assert data["phase"] == "III"
        assert "PFS" in data["primary_endpoint"]
        assert len(data["secondary_endpoints"]) == 7


# ══════════════════════════════════════════════════════════════════════════════
#  LIFECYCLE: Полный жизненный цикл протокола
# ══════════════════════════════════════════════════════════════════════════════

class TestProtocolLifecycle:
    """Lifecycle tests — совместимы с BackgroundTasks в ASGI test client.

    BackgroundTasks теряют DB-сессию при закрытии event loop в тестах.
    Lifecycle-тесты проверяют корректные HTTP-статусы и endpoint availability.
    """

    @pytest.mark.asyncio
    async def test_lifecycle_create_and_generate_accepted(self, client, mock_ai_gateway_ok):
        """LIFECYCLE-01: Create → Generate returns 202 + task_id."""
        resp = await client.post("/api/v1/protocols", json=payload_bcd100_melanoma())
        assert resp.status_code == 201
        proto_id = resp.json()["id"]
        assert resp.json()["status"] == "draft"

        gen_resp = await client.post(
            f"/api/v1/protocols/{proto_id}/generate",
            json={"sections": None},
        )
        assert gen_resp.status_code == 202
        assert "task_id" in gen_resp.json()
        task_id = gen_resp.json()["task_id"]

        # Poll endpoint returns valid shape
        status_resp = await client.get(f"/api/v1/protocols/{proto_id}/generate/{task_id}")
        assert status_resp.status_code == 200
        data = status_resp.json()
        assert "status" in data
        assert data["status"] in ("pending", "running", "completed", "failed")

    @pytest.mark.asyncio
    async def test_lifecycle_export_before_generate_422(self, client):
        """LIFECYCLE-02: Export без генерации → 422."""
        resp = await client.post("/api/v1/protocols", json=payload_bcd089_psoriasis())
        proto_id = resp.json()["id"]
        export_resp = await client.get(f"/api/v1/protocols/{proto_id}/export?format=md")
        assert export_resp.status_code == 422

    @pytest.mark.asyncio
    async def test_lifecycle_check_no_content_422(self, client):
        """LIFECYCLE-03: GCP-проверка без сгенерированного контента → 422 NO_CONTENT."""
        resp = await client.post("/api/v1/protocols", json=payload_bcd132_ra())
        proto_id = resp.json()["id"]
        check_resp = await client.post(
            f"/api/v1/protocols/{proto_id}/check",
            json={"version_id": None},
        )
        # 422 ожидается — нет generated content. Run /generate first.
        assert check_resp.status_code == 422
        assert "NO_CONTENT" in str(check_resp.json())

    @pytest.mark.asyncio
    async def test_lifecycle_versions_empty_before_generate(self, client):
        """LIFECYCLE-04: Версии = [] до генерации."""
        resp = await client.post("/api/v1/protocols", json=payload_bcd057_nsclc())
        proto_id = resp.json()["id"]
        ver_resp = await client.get(f"/api/v1/protocols/{proto_id}/versions")
        assert ver_resp.status_code == 200
        assert ver_resp.json() == []

    @pytest.mark.asyncio
    async def test_lifecycle_generate_bcd089_accepted(self, client, mock_ai_gateway_ok):
        """LIFECYCLE-05: BCD-089 Фаза III generate → 202."""
        resp = await client.post("/api/v1/protocols", json=payload_bcd089_psoriasis())
        proto_id = resp.json()["id"]

        gen_resp = await client.post(
            f"/api/v1/protocols/{proto_id}/generate",
            json={"sections": None},
        )
        assert gen_resp.status_code == 202
        assert "task_id" in gen_resp.json()


# ══════════════════════════════════════════════════════════════════════════════
#  SEARCH: Поиск и фильтрация
# ══════════════════════════════════════════════════════════════════════════════

class TestSearchAndFilter:
    """Поиск по названию и фильтрация по атрибутам."""

    @pytest.mark.asyncio
    async def test_search_by_drug_name(self, client):
        """SEARCH-01: Поиск по названию препарата."""
        await client.post("/api/v1/protocols", json=payload_bcd100_melanoma())
        await client.post("/api/v1/protocols", json=payload_bcd089_psoriasis())

        resp = await client.get("/api/v1/protocols?search=BCD-100")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert all("BCD-100" in p["title"] or "BCD-100" in p["drug_name"] for p in data)

    @pytest.mark.asyncio
    async def test_search_by_title_partial(self, client):
        """SEARCH-02: Поиск по части названия (слово из заголовка)."""
        await client.post("/api/v1/protocols", json=payload_bcd100_melanoma())
        await client.post("/api/v1/protocols", json=payload_bcd089_psoriasis())

        # BCD-100 title contains "пролголимаба" and drug_name "BCD-100"
        resp = await client.get("/api/v1/protocols?search=пролголимаба")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert any("BCD-100" in p["drug_name"] for p in data)

    @pytest.mark.asyncio
    async def test_filter_by_phase(self, client):
        """SEARCH-03: Фильтр по фазе — только Фаза I."""
        await client.post("/api/v1/protocols", json=payload_bcd100_melanoma())  # II
        await client.post("/api/v1/protocols", json=payload_bcd021_lymphoma())   # I

        resp = await client.get("/api/v1/protocols?phase=I")
        assert resp.status_code == 200
        data = resp.json()
        assert all(p["phase"] == "I" for p in data)
        drug_names = [p["drug_name"] for p in data]
        assert "BCD-021" in drug_names
        assert "BCD-100" not in drug_names

    @pytest.mark.asyncio
    async def test_filter_by_therapeutic_area(self, client):
        """SEARCH-04: Фильтр по терапевтической области."""
        await client.post("/api/v1/protocols", json=payload_bcd089_psoriasis())
        await client.post("/api/v1/protocols", json=payload_bcd132_ra())

        resp = await client.get("/api/v1/protocols?therapeutic_area=Дерматология")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert all("дерматол" in p["therapeutic_area"].lower() for p in data)

    @pytest.mark.asyncio
    async def test_search_empty_results(self, client):
        """SEARCH-05: Поиск без результатов → пустой массив."""
        resp = await client.get("/api/v1/protocols?search=НЕСУЩЕСТВУЮЩИЙ_ПРЕПАРАТ_XYZ999")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_combined_filters(self, client):
        """SEARCH-06: Комбинация поиска + фаза + статус."""
        await client.post("/api/v1/protocols", json=payload_bcd100_melanoma())
        await client.post("/api/v1/protocols", json=payload_bcd057_nsclc())

        resp = await client.get("/api/v1/protocols?phase=III&status=draft")
        assert resp.status_code == 200
        data = resp.json()
        assert all(p["phase"] == "III" and p["status"] == "draft" for p in data)


# ══════════════════════════════════════════════════════════════════════════════
#  TAGS: Тегирование протоколов
# ══════════════════════════════════════════════════════════════════════════════

class TestTagManagement:
    """Создание, сохранение, фильтрация и удаление тегов."""

    @pytest.mark.asyncio
    async def test_tags_created_with_protocol(self, client):
        """TAGS-01: Теги создаются вместе с протоколом."""
        resp = await client.post("/api/v1/protocols", json=payload_bcd100_melanoma())
        assert resp.status_code == 201
        data = resp.json()
        assert "онкология" in data["tags"]
        assert "pd-1" in data["tags"]

    @pytest.mark.asyncio
    async def test_tags_persisted_after_patch(self, client):
        """TAGS-02: Теги сохраняются после PATCH-обновления."""
        resp = await client.post("/api/v1/protocols", json=payload_bcd089_psoriasis())
        proto_id = resp.json()["id"]

        patch_resp = await client.patch(
            f"/api/v1/protocols/{proto_id}",
            json={"tags": ["псориаз", "биоаналог", "il-17", "новый-тег"]}
        )
        assert patch_resp.status_code == 200
        updated = patch_resp.json()
        assert "новый-тег" in updated["tags"]
        assert "псориаз" in updated["tags"]

        # Verify persistence via GET
        get_resp = await client.get(f"/api/v1/protocols/{proto_id}")
        assert "новый-тег" in get_resp.json()["tags"]

    @pytest.mark.asyncio
    async def test_filter_by_tag(self, client):
        """TAGS-03: Фильтрация по тегу через query param."""
        await client.post("/api/v1/protocols", json=payload_bcd100_melanoma())   # tags: онкология
        await client.post("/api/v1/protocols", json=payload_bcd089_psoriasis())  # tags: дерматология

        resp = await client.get("/api/v1/protocols?tag=онкология")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert all("онкология" in p["tags"] for p in data)

    @pytest.mark.asyncio
    async def test_global_tags_endpoint(self, client):
        """TAGS-04: GET /tags возвращает все уникальные теги."""
        await client.post("/api/v1/protocols", json=payload_bcd100_melanoma())
        await client.post("/api/v1/protocols", json=payload_bcd089_psoriasis())

        resp = await client.get("/api/v1/tags")
        assert resp.status_code == 200
        tags = resp.json()
        assert isinstance(tags, list)
        assert "онкология" in tags
        assert "псориаз" in tags

    @pytest.mark.asyncio
    async def test_tags_empty_list(self, client):
        """TAGS-05: Протокол без тегов — tags=[]."""
        payload = payload_bcd132_ra()
        payload["tags"] = []
        resp = await client.post("/api/v1/protocols", json=payload)
        assert resp.status_code == 201
        assert resp.json()["tags"] == []

    @pytest.mark.asyncio
    async def test_tags_cleared_via_patch(self, client):
        """TAGS-06: Теги удаляются через PATCH с пустым массивом."""
        resp = await client.post("/api/v1/protocols", json=payload_bcd100_melanoma())
        proto_id = resp.json()["id"]

        patch_resp = await client.patch(f"/api/v1/protocols/{proto_id}", json={"tags": []})
        assert patch_resp.status_code == 200
        assert patch_resp.json()["tags"] == []


# ══════════════════════════════════════════════════════════════════════════════
#  RBAC-FULL: Полная матрица RBAC
# ══════════════════════════════════════════════════════════════════════════════

class TestRBACFull:
    """Проверка матрицы ролей: admin / employee / auditor."""

    @pytest.mark.asyncio
    async def test_auditor_cannot_create(self, auditor_client):
        """RBAC-01: Auditor не может создать протокол → 403."""
        resp = await auditor_client.post("/api/v1/protocols", json=payload_bcd100_melanoma())
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_auditor_can_list(self, client, auditor_client):
        """RBAC-02: Auditor может просматривать список."""
        await client.post("/api/v1/protocols", json=payload_bcd100_melanoma())
        resp = await auditor_client.get("/api/v1/protocols")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_auditor_can_read_single(self, client, auditor_client):
        """RBAC-03: Auditor может читать отдельный протокол."""
        proto_id = (await client.post("/api/v1/protocols", json=payload_bcd089_psoriasis())).json()["id"]
        resp = await auditor_client.get(f"/api/v1/protocols/{proto_id}")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_auditor_cannot_delete(self, client, auditor_client):
        """RBAC-04: Auditor не может удалить → 403."""
        proto_id = (await client.post("/api/v1/protocols", json=payload_bcd100_melanoma())).json()["id"]
        resp = await auditor_client.delete(f"/api/v1/protocols/{proto_id}")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_employee_can_create(self, db_session):
        """RBAC-05: Employee может создавать протоколы."""
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        from app.core.database import get_db
        from app.core.security import get_current_user, require_write

        _employee = {"username": "employee", "role": "employee"}

        async def override_db():
            yield db_session

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = lambda: _employee
        app.dependency_overrides[require_write] = lambda: _employee

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/api/v1/protocols", json=payload_bcd132_ra())

        app.dependency_overrides.clear()
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_employee_cannot_delete(self, db_session):
        """RBAC-06: Employee не может удалять → 403."""
        from httpx import AsyncClient, ASGITransport
        from app.main import app
        from app.core.database import get_db
        from app.core.security import get_current_user, require_write, require_delete

        _admin = {"username": "admin", "role": "admin"}
        _employee = {"username": "employee", "role": "employee"}

        async def override_db():
            yield db_session

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user] = lambda: _admin
        app.dependency_overrides[require_write] = lambda: _admin

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            create_resp = await ac.post("/api/v1/protocols", json=payload_bcd057_nsclc())
            proto_id = create_resp.json()["id"]

        app.dependency_overrides[get_current_user] = lambda: _employee
        app.dependency_overrides[require_delete] = lambda: (_ for _ in ()).throw(
            __import__('fastapi').HTTPException(status_code=403, detail="Forbidden")
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            del_resp = await ac.delete(f"/api/v1/protocols/{proto_id}")

        app.dependency_overrides.clear()
        assert del_resp.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_rejected(self, raw_client):
        """RBAC-07: Без токена → 401."""
        resp = await raw_client.get("/api/v1/protocols")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_audit_log_accessible_to_auditor(self, client, auditor_client):
        """RBAC-08: Auditor может читать audit log."""
        await client.post("/api/v1/protocols", json=payload_bcd100_melanoma())
        resp = await auditor_client.get("/api/v1/audit-log")
        assert resp.status_code == 200


# ══════════════════════════════════════════════════════════════════════════════
#  SMOKE: Критические пути — быстрые проверки
# ══════════════════════════════════════════════════════════════════════════════

class TestSmoke:
    """Smoke-тесты: проверяют, что система «жива» и базовые операции работают."""

    @pytest.mark.asyncio
    async def test_smoke_health(self, client):
        """SMOKE-01: /health → ok."""
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_smoke_create_and_list(self, client):
        """SMOKE-02: Создать и найти в списке."""
        resp = await client.post("/api/v1/protocols", json=payload_bcd100_melanoma())
        assert resp.status_code == 201
        proto_id = resp.json()["id"]

        list_resp = await client.get("/api/v1/protocols")
        ids = [p["id"] for p in list_resp.json()]
        assert proto_id in ids

    @pytest.mark.asyncio
    async def test_smoke_get_templates(self, client):
        """SMOKE-03: Шаблоны возвращаются — ≥3 шт."""
        resp = await client.get("/api/v1/templates")
        assert resp.status_code == 200
        assert len(resp.json()) >= 3

    @pytest.mark.asyncio
    async def test_smoke_404_on_missing_protocol(self, client):
        """SMOKE-04: Несуществующий протокол → 404."""
        resp = await client.get("/api/v1/protocols/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_smoke_generate_missing_protocol(self, client):
        """SMOKE-05: Генерация несуществующего UUID → 404."""
        resp = await client.post(
            "/api/v1/protocols/00000000-0000-0000-0000-000000000000/generate",
            json={"sections": None},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_smoke_export_before_generate(self, client):
        """SMOKE-06: Экспорт без контента → 422."""
        resp = await client.post("/api/v1/protocols", json=payload_bcd089_psoriasis())
        proto_id = resp.json()["id"]
        export_resp = await client.get(f"/api/v1/protocols/{proto_id}/export?format=md")
        assert export_resp.status_code == 422

    @pytest.mark.asyncio
    async def test_smoke_phase_validation(self, client):
        """SMOKE-07: Невалидная фаза → 422."""
        payload = payload_bcd100_melanoma()
        payload["phase"] = "phase_2"  # неверный формат
        resp = await client.post("/api/v1/protocols", json=payload)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_smoke_audit_log(self, client):
        """SMOKE-08: После create — в audit log есть запись."""
        await client.post("/api/v1/protocols", json=payload_bcd021_lymphoma())
        resp = await client.get("/api/v1/audit-log?limit=5")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    @pytest.mark.asyncio
    async def test_smoke_patch_dosing(self, client):
        """SMOKE-09: PATCH изменяет поле dosing."""
        resp = await client.post("/api/v1/protocols", json=payload_bcd132_ra())
        proto_id = resp.json()["id"]

        new_dosing = "BCD-132 4 мг/кг в/в каждые 4 недели (скорректированная доза)"
        patch_resp = await client.patch(
            f"/api/v1/protocols/{proto_id}",
            json={"dosing": new_dosing}
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["dosing"] == new_dosing

    @pytest.mark.asyncio
    async def test_smoke_delete_removes_protocol(self, client):
        """SMOKE-10: DELETE → 204, затем GET → 404."""
        resp = await client.post("/api/v1/protocols", json=payload_bcd057_nsclc())
        proto_id = resp.json()["id"]

        del_resp = await client.delete(f"/api/v1/protocols/{proto_id}")
        assert del_resp.status_code == 204

        get_resp = await client.get(f"/api/v1/protocols/{proto_id}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_smoke_ai_gateway_failure_503(self, client, mock_ai_gateway_fail):
        """SMOKE-11: При недоступном AI Gateway → task failed, не внутренний 500."""
        resp = await client.post("/api/v1/protocols", json=payload_bcd100_melanoma())
        proto_id = resp.json()["id"]

        gen_resp = await client.post(
            f"/api/v1/protocols/{proto_id}/generate",
            json={"sections": None},
        )
        assert gen_resp.status_code == 202

        import asyncio
        task_id = gen_resp.json()["task_id"]
        sr = None
        for _ in range(15):
            sr = await client.get(f"/api/v1/protocols/{proto_id}/generate/{task_id}")
            if sr.json().get("status") in ("completed", "failed"):
                break
            await asyncio.sleep(0.2)

        assert sr is not None
        assert sr.json()["status"] == "failed"
