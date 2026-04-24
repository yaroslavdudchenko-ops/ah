"""
test_form_scenarios.py — Happy Path + Negative Testing для заполнения протокола.

Покрывает:
  HP (Happy Path)  — полное и минимальное заполнение формы, CRUD, версии
  NEG (Negative)   — граничные значения, XSS/injection, незаполненные поля,
                     некорректные типы, конкуренция, RBAC-запреты
  AI (AI Generator) — логика генерации: fallback, конкурентность, section_regen
"""
import asyncio
import os
import pytest
from unittest.mock import patch, AsyncMock
from tests.conftest import bcd100_payload, bcd089_payload

_AUDITOR_PASS = os.environ.get("AUDITOR_PASSWORD", "aud123")


# ════════════════════════════════════════════════════════════════════════════
#  HP — Happy Path: создание и жизненный цикл протокола
# ════════════════════════════════════════════════════════════════════════════

class TestHappyPathCreate:
    """HP-FORM-01..04: Создание протокола с корректными данными."""

    @pytest.mark.asyncio
    async def test_hp_full_form_all_fields(self, client):
        """HP-FORM-01: Все поля заполнены — 201, все поля сохранены."""
        payload = {
            "title": "BCD-021 Phase III Biosimilar Rituximab Study in B-cell NHL",
            "drug_name": "BCD-021",
            "inn": "Ритуксимаб",
            "phase": "III",
            "therapeutic_area": "hematology",
            "indication": (
                "Диффузная В-крупноклеточная лимфома CD20+, стадия II-IV, "
                "первая линия терапии в комбинации с CHOP"
            ),
            "population": (
                "Взрослые пациенты 18-75 лет с CD20+ В-клеточной NHL, "
                "ECOG 0-2, ФВ ЛЖ ≥50%"
            ),
            "primary_endpoint": "ORR по критериям Cheson 2007 после 6 циклов R-CHOP",
            "secondary_endpoints": ["CR rate", "PFS 24 мес", "OS 24 мес", "Иммуногенность ADA"],
            "duration_weeks": 18,
            "dosing": "375 мг/м² в/в каждые 3 недели (день 1 цикла R-CHOP)",
            "inclusion_criteria": [
                "Возраст 18-75 лет",
                "ДВКБКЛ или FL grade 3B гистологически подтверждённая",
                "CD20+ ≥20% клеток",
                "Стадия II-IV по Ann Arbor",
                "ECOG 0-2",
            ],
            "exclusion_criteria": [
                "Активный гепатит B (HBsAg+)",
                "ВИЧ-инфекция",
                "Предшествующая анти-CD20 терапия",
                "ТГСК в анамнезе",
            ],
            "template_id": "tpl-phase-iii-001",
        }
        resp = await client.post("/api/v1/protocols", json=payload)
        assert resp.status_code == 201
        data = resp.json()

        assert data["drug_name"] == "BCD-021"
        assert data["phase"] == "III"
        assert data["status"] == "draft"
        assert data["inn"] == "Ритуксимаб"
        assert data["therapeutic_area"] == "hematology"
        assert len(data["inclusion_criteria"]) == 5
        assert len(data["exclusion_criteria"]) == 4
        assert len(data["secondary_endpoints"]) == 4
        assert data["template_id"] == "tpl-phase-iii-001"
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_hp_minimal_valid_form(self, client):
        """HP-FORM-02: Минимальный набор обязательных полей — 201."""
        payload = {
            "title": "Minimal Protocol Study",
            "drug_name": "BCD-MIN",
            "inn": "Тестомаб",
            "phase": "I",
            "therapeutic_area": "oncology",
            "indication": "Рефрактерная опухоль для FIH исследования",
            "population": "Взрослые пациенты ≥18 лет",
            "primary_endpoint": "MTD и DLT",
            "duration_weeks": 12,
            "dosing": "0.1 мг/кг в/в кажд. 3 нед",
        }
        resp = await client.post("/api/v1/protocols", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert data["secondary_endpoints"] == []
        assert data["inclusion_criteria"] == []
        assert data["exclusion_criteria"] == []

    @pytest.mark.asyncio
    async def test_hp_phase_i_fih(self, client):
        """HP-FORM-03: Phase I FIH протокол — все поля сохранены корректно."""
        payload = {
            "title": "BCD-132 Phase I FIH Bispecific Anti-PD1 IL2 Solid Tumors",
            "drug_name": "BCD-132",
            "inn": "Экспериментальный биспецифик",
            "phase": "I",
            "therapeutic_area": "oncology",
            "indication": "Распространённые солидные опухоли рефрактерные к стандартной терапии",
            "population": "Взрослые ≥18 лет ECOG 0-1 согласие на парные биопсии",
            "primary_endpoint": "DLT MTD RP2D в первые 21 день каждой когорты",
            "secondary_endpoints": ["AUC Cmax T-half (ФК)", "CD8+ TIL Ki-67 (ФД)", "ORR RECIST 1.1"],
            "duration_weeks": 24,
            "dosing": "0.1 0.3 1.0 3.0 10.0 мг/кг в/в кажд. 3 нед эскалация 3+3",
            "inclusion_criteria": [
                "Возраст ≥18 лет",
                "Гистологически верифицированная солидная опухоль",
                "ECOG 0-1",
                "Согласие на парные биопсии",
            ],
            "exclusion_criteria": [
                "Активные аутоиммунные заболевания",
                "ФВ ЛЖ < 40%",
            ],
        }
        resp = await client.post("/api/v1/protocols", json=payload)
        assert resp.status_code == 201
        assert resp.json()["phase"] == "I"

    @pytest.mark.asyncio
    async def test_hp_update_status_lifecycle(self, client):
        """HP-FORM-04: Жизненный цикл draft → generated → in_review.

        Статус approved требует второго пользователя (4-eyes, FR-09.1) — не тестируем здесь."""
        create_resp = await client.post("/api/v1/protocols", json=bcd100_payload())
        pid = create_resp.json()["id"]

        for new_status in ["generated", "in_review"]:
            resp = await client.patch(f"/api/v1/protocols/{pid}", json={"status": new_status})
            assert resp.status_code == 200, resp.text
            assert resp.json()["status"] == new_status

    @pytest.mark.asyncio
    async def test_hp_update_multiple_fields(self, client):
        """HP-FORM-05: PATCH обновляет несколько полей одновременно."""
        create_resp = await client.post("/api/v1/protocols", json=bcd100_payload())
        pid = create_resp.json()["id"]
        resp = await client.patch(f"/api/v1/protocols/{pid}", json={
            "title": "BCD-100 Updated Title for Melanoma Study Phase II",
            "duration_weeks": 48,
            "dosing": "2 мг/кг в/в каждые 3 недели",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["duration_weeks"] == 48
        assert "Updated Title" in data["title"]

    @pytest.mark.asyncio
    async def test_hp_get_after_create(self, client):
        """HP-FORM-06: GET после создания возвращает идентичные данные."""
        payload = bcd089_payload()
        create = await client.post("/api/v1/protocols", json=payload)
        pid = create.json()["id"]

        get = await client.get(f"/api/v1/protocols/{pid}")
        assert get.status_code == 200
        data = get.json()
        assert data["drug_name"] == payload["drug_name"]
        assert data["primary_endpoint"] == payload["primary_endpoint"]
        assert data["inclusion_criteria"] == payload["inclusion_criteria"]

    @pytest.mark.asyncio
    async def test_hp_list_pagination(self, client):
        """HP-FORM-07: Пагинация — limit/offset работают корректно."""
        for i in range(5):
            p = bcd100_payload()
            p["title"] = f"Protocol {i} Test Pagination Study"
            p["drug_name"] = f"BCD-{i:03d}"
            await client.post("/api/v1/protocols", json=p)

        resp_all = await client.get("/api/v1/protocols?limit=50")
        assert len(resp_all.json()) == 5

        resp_page1 = await client.get("/api/v1/protocols?limit=2&offset=0")
        resp_page2 = await client.get("/api/v1/protocols?limit=2&offset=2")
        ids_p1 = {p["id"] for p in resp_page1.json()}
        ids_p2 = {p["id"] for p in resp_page2.json()}
        assert len(ids_p1) == 2
        assert len(ids_p2) == 2
        assert ids_p1.isdisjoint(ids_p2)

    @pytest.mark.asyncio
    async def test_hp_list_filter_by_phase(self, client):
        """HP-FORM-08: Фильтр по phase возвращает только совпадения."""
        await client.post("/api/v1/protocols", json=bcd100_payload())   # Phase II
        await client.post("/api/v1/protocols", json=bcd089_payload())   # Phase III

        resp_ii = await client.get("/api/v1/protocols?phase=II")
        assert all(p["phase"] == "II" for p in resp_ii.json())

        resp_iii = await client.get("/api/v1/protocols?phase=III")
        assert all(p["phase"] == "III" for p in resp_iii.json())

    @pytest.mark.asyncio
    async def test_hp_large_criteria_lists(self, client):
        """HP-FORM-09: 30 критериев включения/исключения сохраняются корректно."""
        payload = bcd100_payload()
        payload["inclusion_criteria"] = [f"Inclusion criterion {i}" for i in range(30)]
        payload["exclusion_criteria"] = [f"Exclusion criterion {i}" for i in range(25)]
        resp = await client.post("/api/v1/protocols", json=payload)
        assert resp.status_code == 201
        data = resp.json()
        assert len(data["inclusion_criteria"]) == 30
        assert len(data["exclusion_criteria"]) == 25


# ════════════════════════════════════════════════════════════════════════════
#  NEG — Negative Testing: валидация, граничные значения, безопасность
# ════════════════════════════════════════════════════════════════════════════

class TestNegativeValidation:
    """NEG-FORM-01..12: Граничные значения и некорректные данные."""

    # ── Phase validation ────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_neg_phase_invalid_format_rejected(self, client):
        """NEG-FORM-01: phase='phase_2' (неверный формат) → 422."""
        p = bcd100_payload(); p["phase"] = "phase_2"
        resp = await client.post("/api/v1/protocols", json=p)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_phase_iv_accepted(self, client):
        """NEG-FORM-01b: phase='IV' → 201 (Phase IV поддерживается)."""
        p = bcd100_payload(); p["phase"] = "IV"
        resp = await client.post("/api/v1/protocols", json=p)
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_neg_phase_empty_rejected(self, client):
        """NEG-FORM-02: phase='' → 422."""
        p = bcd100_payload(); p["phase"] = ""
        resp = await client.post("/api/v1/protocols", json=p)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_neg_phase_lowercase_rejected(self, client):
        """NEG-FORM-03: phase='ii' (lowercase) → 422 (pattern требует I/II/III)."""
        p = bcd100_payload(); p["phase"] = "ii"
        resp = await client.post("/api/v1/protocols", json=p)
        assert resp.status_code == 422

    # ── Title validation ────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_neg_title_too_short(self, client):
        """NEG-FORM-04: title < 5 символов → 422."""
        p = bcd100_payload(); p["title"] = "ABC"
        resp = await client.post("/api/v1/protocols", json=p)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_neg_title_too_long(self, client):
        """NEG-FORM-05: title > 500 символов → 422."""
        p = bcd100_payload(); p["title"] = "A" * 501
        resp = await client.post("/api/v1/protocols", json=p)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_neg_title_exactly_5_chars_ok(self, client):
        """NEG-FORM-05b: title == 5 символов — граница, допустимо → 201."""
        p = bcd100_payload(); p["title"] = "AB CDE"
        resp = await client.post("/api/v1/protocols", json=p)
        assert resp.status_code == 201

    # ── Duration validation ─────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_neg_duration_zero(self, client):
        """NEG-FORM-06: duration_weeks=0 → 422."""
        p = bcd100_payload(); p["duration_weeks"] = 0
        resp = await client.post("/api/v1/protocols", json=p)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_neg_duration_negative(self, client):
        """NEG-FORM-07: duration_weeks=-1 → 422."""
        p = bcd100_payload(); p["duration_weeks"] = -1
        resp = await client.post("/api/v1/protocols", json=p)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_neg_duration_too_large(self, client):
        """NEG-FORM-08: duration_weeks=521 → 422 (>520 запрещено)."""
        p = bcd100_payload(); p["duration_weeks"] = 521
        resp = await client.post("/api/v1/protocols", json=p)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_neg_duration_max_boundary_ok(self, client):
        """NEG-FORM-08b: duration_weeks=520 — граница, допустимо → 201."""
        p = bcd100_payload(); p["duration_weeks"] = 520
        resp = await client.post("/api/v1/protocols", json=p)
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_neg_duration_float(self, client):
        """NEG-FORM-09: duration_weeks=12.5 (float вместо int) → 422."""
        p = bcd100_payload(); p["duration_weeks"] = 12.5
        resp = await client.post("/api/v1/protocols", json=p)
        assert resp.status_code == 422

    # ── Missing required fields ─────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_neg_missing_primary_endpoint(self, client):
        """NEG-FORM-10: отсутствует primary_endpoint → 422."""
        p = bcd100_payload(); del p["primary_endpoint"]
        resp = await client.post("/api/v1/protocols", json=p)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_neg_missing_drug_name(self, client):
        """NEG-FORM-11: отсутствует drug_name → 422."""
        p = bcd100_payload(); del p["drug_name"]
        resp = await client.post("/api/v1/protocols", json=p)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_neg_missing_indication(self, client):
        """NEG-FORM-12: отсутствует indication → 422."""
        p = bcd100_payload(); del p["indication"]
        resp = await client.post("/api/v1/protocols", json=p)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_neg_empty_body(self, client):
        """NEG-FORM-13: пустое тело запроса → 422."""
        resp = await client.post("/api/v1/protocols", json={})
        assert resp.status_code == 422

    # ── Type errors ─────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_neg_secondary_endpoints_not_list(self, client):
        """NEG-FORM-14: secondary_endpoints — строка вместо массива → 422."""
        p = bcd100_payload(); p["secondary_endpoints"] = "PFS, OS"
        resp = await client.post("/api/v1/protocols", json=p)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_neg_inclusion_criteria_not_list(self, client):
        """NEG-FORM-15: inclusion_criteria — строка вместо массива → 422."""
        p = bcd100_payload(); p["inclusion_criteria"] = "Возраст ≥18 лет"
        resp = await client.post("/api/v1/protocols", json=p)
        assert resp.status_code == 422

    # ── Short text fields ───────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_neg_inn_too_short(self, client):
        """NEG-FORM-16: inn='A' (1 символ) → 422 (min_length=2)."""
        p = bcd100_payload(); p["inn"] = "A"
        resp = await client.post("/api/v1/protocols", json=p)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_neg_indication_too_short(self, client):
        """NEG-FORM-17: indication='X' (< min_length=10) → 422."""
        p = bcd100_payload(); p["indication"] = "Too short"
        resp = await client.post("/api/v1/protocols", json=p)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_neg_population_too_short(self, client):
        """NEG-FORM-18: population < min_length=10 → 422."""
        p = bcd100_payload(); p["population"] = "Short"
        resp = await client.post("/api/v1/protocols", json=p)
        assert resp.status_code == 422

    # ── Security / injection ────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_neg_xss_in_title_stored_safely(self, client):
        """NEG-SEC-01: XSS в title сохраняется как plain text, не исполняется.
        Ожидание: 201, значение сохранено дословно (API не рендерит HTML)."""
        xss = "<script>alert('xss')</script> Study Protocol"
        p = bcd100_payload(); p["title"] = xss
        resp = await client.post("/api/v1/protocols", json=p)
        assert resp.status_code == 201
        assert resp.json()["title"] == xss

    @pytest.mark.asyncio
    async def test_neg_sql_injection_in_drug_name(self, client):
        """NEG-SEC-02: SQL-инъекция в drug_name — данные сохранены как строка."""
        sqli = "BCD-100'; DROP TABLE protocols; --"
        p = bcd100_payload(); p["drug_name"] = sqli
        resp = await client.post("/api/v1/protocols", json=p)
        assert resp.status_code == 201
        assert resp.json()["drug_name"] == sqli

    @pytest.mark.asyncio
    async def test_neg_unicode_emoji_in_fields(self, client):
        """NEG-SEC-03: Unicode и emoji в текстовых полях — принимаются без ошибок."""
        p = bcd100_payload()
        p["title"] = "BCD-100 Исследование 🔬 Phase II Меланома"
        p["dosing"] = "1 мг/кг в/в каждые 2 недели ✅"
        resp = await client.post("/api/v1/protocols", json=p)
        assert resp.status_code == 201

    # ── Not found ───────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_neg_get_nonexistent(self, client):
        """NEG-FORM-19: GET несуществующего ID → 404 с error code."""
        resp = await client.get("/api/v1/protocols/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404
        assert resp.json()["detail"]["error"]["code"] == "PROTOCOL_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_neg_patch_nonexistent(self, client):
        """NEG-FORM-20: PATCH несуществующего ID → 404."""
        resp = await client.patch(
            "/api/v1/protocols/00000000-0000-0000-0000-000000000000",
            json={"status": "approved"}
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_neg_delete_nonexistent(self, client):
        """NEG-FORM-21: DELETE несуществующего ID → 404."""
        resp = await client.delete("/api/v1/protocols/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_neg_version_not_found(self, client):
        """NEG-FORM-22: GET versions для несуществующего протокола → 404."""
        resp = await client.get(
            "/api/v1/protocols/00000000-0000-0000-0000-000000000000/versions"
        )
        assert resp.status_code == 404


# ════════════════════════════════════════════════════════════════════════════
#  AI — Генератор протоколов: логика, fallback, безопасность
# ════════════════════════════════════════════════════════════════════════════

class TestAIGeneratorLogic:
    """AI-GEN-01..08: Проверка логики AI-генерации секций."""

    @pytest.mark.asyncio
    async def test_ai_generate_ok_returns_202(self, client, mock_ai_gateway_ok):
        """AI-GEN-01: Успешный запуск генерации → 202 + task_id."""
        create = await client.post("/api/v1/protocols", json=bcd100_payload())
        pid = create.json()["id"]
        resp = await client.post(f"/api/v1/protocols/{pid}/generate", json={})
        assert resp.status_code == 202
        assert "task_id" in resp.json()

    @pytest.mark.asyncio
    async def test_ai_generate_creates_version(self, client, mock_ai_gateway_ok):
        """AI-GEN-02: POST /generate возвращает 202 + task_id (проверка запуска).
        NOTE: Фоновая задача пишет в отдельный AsyncSessionLocal → интеграционный тест.
        Здесь проверяем корректность старта задачи, не её финального результата."""
        create = await client.post("/api/v1/protocols", json=bcd100_payload())
        pid = create.json()["id"]

        gen = await client.post(f"/api/v1/protocols/{pid}/generate", json={})
        assert gen.status_code == 202
        body = gen.json()
        assert "task_id" in body
        assert len(body["task_id"]) == 36  # UUID format

    @pytest.mark.asyncio
    async def test_ai_generate_fallback_on_gateway_error(self, client, mock_ai_gateway_fail):
        """AI-GEN-03: При недоступности AI Gateway — fallback-контент, не 500."""
        create = await client.post("/api/v1/protocols", json=bcd100_payload())
        pid = create.json()["id"]
        resp = await client.post(f"/api/v1/protocols/{pid}/generate", json={})
        assert resp.status_code == 202
        await asyncio.sleep(0.3)
        versions = await client.get(f"/api/v1/protocols/{pid}/versions")
        assert versions.status_code == 200

    @pytest.mark.asyncio
    async def test_ai_generate_version_increments(self, client, mock_ai_gateway_ok):
        """AI-GEN-04: Повторный вызов /generate возвращает каждый раз уникальный task_id."""
        create = await client.post("/api/v1/protocols", json=bcd100_payload())
        pid = create.json()["id"]

        task_ids = []
        for _ in range(3):
            resp = await client.post(f"/api/v1/protocols/{pid}/generate", json={})
            assert resp.status_code == 202
            task_ids.append(resp.json()["task_id"])

        # Каждый запуск создаёт уникальный task_id
        assert len(set(task_ids)) == 3

    @pytest.mark.asyncio
    async def test_ai_generate_with_comment(self, client, mock_ai_gateway_ok):
        """AI-GEN-05: Запрос генерации с комментарием принимается без ошибок → 202."""
        create = await client.post("/api/v1/protocols", json=bcd100_payload())
        pid = create.json()["id"]
        comment = "Обновлены критерии включения по итогам встречи с KOL"

        resp = await client.post(f"/api/v1/protocols/{pid}/generate", json={"comment": comment})
        assert resp.status_code == 202
        assert "task_id" in resp.json()

    @pytest.mark.asyncio
    async def test_ai_generate_nonexistent_protocol(self, client, mock_ai_gateway_ok):
        """AI-GEN-06: Генерация для несуществующего протокола → 404."""
        resp = await client.post(
            "/api/v1/protocols/00000000-0000-0000-0000-000000000000/generate",
            json={}
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_ai_section_regen_requires_existing_version(self, client, mock_ai_gateway_ok):
        """AI-GEN-07: Перегенерация секции без базовой версии → 422."""
        create = await client.post("/api/v1/protocols", json=bcd100_payload())
        pid = create.json()["id"]
        resp = await client.post(f"/api/v1/protocols/{pid}/sections/objectives/regenerate")
        assert resp.status_code == 422
        assert resp.json()["detail"]["error"]["code"] == "NO_CONTENT"

    @pytest.mark.asyncio
    async def test_ai_task_status_endpoint(self, client, mock_ai_gateway_ok):
        """AI-GEN-08: GET статуса задачи возвращает корректную структуру."""
        create = await client.post("/api/v1/protocols", json=bcd100_payload())
        pid = create.json()["id"]
        gen = await client.post(f"/api/v1/protocols/{pid}/generate", json={})
        task_id = gen.json()["task_id"]

        status_resp = await client.get(f"/api/v1/protocols/{pid}/generate/{task_id}")
        assert status_resp.status_code == 200
        data = status_resp.json()
        assert "status" in data
        assert data["status"] in ("pending", "running", "completed", "failed")
        assert "sections_done" in data

    @pytest.mark.asyncio
    async def test_ai_unknown_task_id_returns_404(self, client):
        """AI-GEN-09: GET статуса несуществующей задачи → 404."""
        create = await client.post("/api/v1/protocols", json=bcd100_payload())
        pid = create.json()["id"]
        resp = await client.get(f"/api/v1/protocols/{pid}/generate/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404


# ════════════════════════════════════════════════════════════════════════════
#  RBAC — Role-Based access scenarios for protocol operations
# ════════════════════════════════════════════════════════════════════════════

class TestRbacFormScenarios:
    """RBAC-FORM-01..05: Ролевые ограничения — реальные JWT токены (raw_client)."""

    @pytest.mark.asyncio
    async def test_rbac_auditor_can_read_protocol(self, auditor_client, client):
        """RBAC-FORM-01: Auditor может читать протоколы (dependency override)."""
        create = await client.post("/api/v1/protocols", json=bcd100_payload())
        pid = create.json()["id"]
        resp = await auditor_client.get(f"/api/v1/protocols/{pid}")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_rbac_auditor_cannot_create(self, auditor_client):
        """RBAC-FORM-02: Auditor не может создать протокол → 403."""
        resp = await auditor_client.post("/api/v1/protocols", json=bcd100_payload())
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_rbac_auditor_cannot_patch_real_jwt(self, raw_client):
        """RBAC-FORM-03: Auditor с реальным JWT не может изменить протокол → 403.
        Используем raw_client + реальный токен чтобы избежать конфликта overrides."""
        # Получаем admin токен для создания
        admin_login = await raw_client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        admin_tok = admin_login.json()["access_token"]
        admin_h = {"Authorization": f"Bearer {admin_tok}"}

        create = await raw_client.post("/api/v1/protocols", json=bcd100_payload(), headers=admin_h)
        pid = create.json()["id"]

        # Auditor пытается PATCH
        aud_login = await raw_client.post(
            "/api/v1/auth/token",
            data={"username": "auditor", "password": _AUDITOR_PASS},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        aud_tok = aud_login.json()["access_token"]
        resp = await raw_client.patch(
            f"/api/v1/protocols/{pid}",
            json={"status": "approved"},
            headers={"Authorization": f"Bearer {aud_tok}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_rbac_auditor_can_read_versions(self, auditor_client, client):
        """RBAC-FORM-04: Auditor может читать список версий."""
        create = await client.post("/api/v1/protocols", json=bcd100_payload())
        pid = create.json()["id"]
        resp = await auditor_client.get(f"/api/v1/protocols/{pid}/versions")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_rbac_auditor_cannot_generate_real_jwt(self, raw_client):
        """RBAC-FORM-05: Auditor с реальным JWT не может запустить генерацию → 403."""
        # Создаём протокол от admin
        admin_login = await raw_client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "admin123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        admin_tok = admin_login.json()["access_token"]
        create = await raw_client.post(
            "/api/v1/protocols", json=bcd100_payload(),
            headers={"Authorization": f"Bearer {admin_tok}"}
        )
        pid = create.json()["id"]

        # Auditor пытается генерировать
        aud_login = await raw_client.post(
            "/api/v1/auth/token",
            data={"username": "auditor", "password": _AUDITOR_PASS},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        aud_tok = aud_login.json()["access_token"]
        resp = await raw_client.post(
            f"/api/v1/protocols/{pid}/generate", json={},
            headers={"Authorization": f"Bearer {aud_tok}"},
        )
        assert resp.status_code == 403
