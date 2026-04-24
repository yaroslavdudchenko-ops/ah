"""
test_new_features.py — Tests for features added in sessions 11-12:
- Edit protocol metadata (PATCH with all fields)
- Exclusion criteria persist and are returned
- Section-specific fallbacks (not all same)
- SAP/ICF fallbacks are unique
- Export audit log written
- Phase IV rejected by backend

Coverage: smoke, happy path, alternative, negative.
"""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.ai_gateway import AIGatewayError


# ─── Helpers ────────────────────────────────────────────────────────────────

BASE_PROTOCOL = {
    "title": "Тестовый протокол BCD-100 Phase II",
    "drug_name": "BCD-100",
    "inn": "пролголимаб",
    "phase": "II",
    "therapeutic_area": "Онкология",
    "indication": "Нерезектабельная меланома кожи, прогрессирующая",
    "population": "Пациенты ≥18 лет с гистологически подтверждённой меланомой",
    "primary_endpoint": "Общая частота ответа по RECIST 1.1 через 24 недели",
    "secondary_endpoints": ["Беспрогрессивная выживаемость (PFS)", "Общая выживаемость (OS)"],
    "duration_weeks": 24,
    "dosing": "1 мг/кг в/в каждые 2 недели",
    "inclusion_criteria": ["Возраст ≥18 лет", "ECOG ≤1", "Подтверждённый диагноз"],
    "exclusion_criteria": ["Аутоиммунные заболевания в анамнезе", "Беременность или лактация"],
    "tags": ["oncology", "phase-ii"],
}


@pytest_asyncio.fixture  # type: ignore
async def auth_client(client, admin_token):
    client.headers.update({"Authorization": f"Bearer {admin_token}"})
    return client


# ─── SMOKE ───────────────────────────────────────────────────────────────────

class TestSmoke:
    @pytest.mark.asyncio
    async def test_smoke_create_with_exclusion_criteria(self, client, admin_token):
        """SMOKE: protocol creates with exclusion_criteria present."""
        r = await client.post(
            "/api/v1/protocols",
            json=BASE_PROTOCOL,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 201
        data = r.json()
        assert "id" in data

    @pytest.mark.asyncio
    async def test_smoke_phase_iv_rejected(self, client, admin_token):
        """SMOKE: backend rejects Phase IV regardless of frontend."""
        body = {**BASE_PROTOCOL, "phase": "IV"}
        r = await client.post(
            "/api/v1/protocols",
            json=body,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 422


# ─── HAPPY PATH ──────────────────────────────────────────────────────────────

class TestEditMeta:
    @pytest.mark.asyncio
    async def test_hp_exclusion_criteria_persisted(self, client, admin_token):
        """HP: exclusion_criteria saved on create and returned on GET."""
        r = await client.post(
            "/api/v1/protocols",
            json=BASE_PROTOCOL,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 201
        pid = r.json()["id"]

        g = await client.get(
            f"/api/v1/protocols/{pid}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert g.status_code == 200
        body = g.json()
        assert body["exclusion_criteria"] == BASE_PROTOCOL["exclusion_criteria"]

    @pytest.mark.asyncio
    async def test_hp_edit_meta_all_fields(self, client, admin_token):
        """HP: PATCH updates all editable metadata fields."""
        r = await client.post(
            "/api/v1/protocols",
            json=BASE_PROTOCOL,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        pid = r.json()["id"]

        patch_data = {
            "title": "Обновлённый протокол BCD-100",
            "drug_name": "BCD-100-updated",
            "inn": "пролголимаб-updated",
            "phase": "III",
            "indication": "Метастатическая меланома, прогрессия после иммунотерапии",
            "population": "Пациенты ≥18 лет после предыдущей линии терапии",
            "primary_endpoint": "Общая выживаемость (OS) через 36 месяцев",
            "dosing": "200 мг в/в каждые 3 недели",
            "duration_weeks": 36,
            "inclusion_criteria": ["Возраст ≥18 лет", "Прогрессия после ≥1 линии"],
            "exclusion_criteria": ["Активные аутоиммунные НЯ ≥3 ст.", "ЦНС-метастазы без лечения"],
        }

        resp = await client.patch(
            f"/api/v1/protocols/{pid}",
            json=patch_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        updated = resp.json()
        assert updated["title"] == patch_data["title"]
        assert updated["phase"] == "III"
        assert updated["dosing"] == patch_data["dosing"]
        assert updated["exclusion_criteria"] == patch_data["exclusion_criteria"]
        assert updated["inclusion_criteria"] == patch_data["inclusion_criteria"]
        assert updated["duration_weeks"] == 36

    @pytest.mark.asyncio
    async def test_hp_edit_meta_partial_patch(self, client, admin_token):
        """HP: PATCH can update only selected fields (partial update)."""
        r = await client.post(
            "/api/v1/protocols",
            json=BASE_PROTOCOL,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        pid = r.json()["id"]

        resp = await client.patch(
            f"/api/v1/protocols/{pid}",
            json={"dosing": "2 мг/кг в/в каждые 4 недели"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["dosing"] == "2 мг/кг в/в каждые 4 недели"
        # Other fields unchanged
        assert resp.json()["title"] == BASE_PROTOCOL["title"]

    @pytest.mark.asyncio
    async def test_hp_edit_meta_creates_audit(self, client, admin_token):
        """HP: PATCH generates audit log entry."""
        r = await client.post(
            "/api/v1/protocols",
            json=BASE_PROTOCOL,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        pid = r.json()["id"]

        await client.patch(
            f"/api/v1/protocols/{pid}",
            json={"dosing": "новое дозирование"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        audit = await client.get(
            f"/api/v1/protocols/{pid}/audit",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert audit.status_code == 200
        actions = [e["action"] for e in audit.json()]
        assert "update" in actions


# ─── SECTION FALLBACKS ────────────────────────────────────────────────────────

class TestSectionFallbacks:
    @pytest.mark.asyncio
    async def test_hp_fallbacks_are_unique_per_section(self, client, admin_token):
        """HP: when AI unavailable, each section has unique fallback content."""
        r = await client.post(
            "/api/v1/protocols",
            json=BASE_PROTOCOL,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        pid = r.json()["id"]

        with patch(
            "app.services.generator.ai_client.complete",
            new=AsyncMock(side_effect=AIGatewayError("unavailable")),
        ):
            gen = await client.post(
                f"/api/v1/protocols/{pid}/generate",
                json={"sections": ["introduction", "objectives", "design", "population", "treatment"]},
                headers={"Authorization": f"Bearer {admin_token}"},
            )
            assert gen.status_code == 202
            task_id = gen.json()["task_id"]

            import asyncio
            for _ in range(10):
                status_r = await client.get(
                    f"/api/v1/protocols/{pid}/generate/{task_id}",
                    headers={"Authorization": f"Bearer {admin_token}"},
                )
                if status_r.json().get("status") in ("completed", "failed"):
                    break
                await asyncio.sleep(0.5)

        vers = await client.get(
            f"/api/v1/protocols/{pid}/versions",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert vers.status_code == 200
        versions = vers.json()
        assert len(versions) > 0
        content = versions[-1]["content"]

        sections = list(content.values())
        # All sections must have unique content (not identical)
        assert len(set(sections)) == len(sections), "All fallback sections must be unique"

    @pytest.mark.asyncio
    async def test_hp_fallback_contains_for_review_only(self, client, admin_token):
        """HP: fallback sections contain FOR REVIEW ONLY marker."""
        from app.services.generator import _fallback_section
        from app.models.protocol import Protocol

        proto = Protocol(
            id="test-id",
            title=BASE_PROTOCOL["title"],
            drug_name=BASE_PROTOCOL["drug_name"],
            inn=BASE_PROTOCOL["inn"],
            phase=BASE_PROTOCOL["phase"],
            therapeutic_area=BASE_PROTOCOL["therapeutic_area"],
            indication=BASE_PROTOCOL["indication"],
            population=BASE_PROTOCOL["population"],
            primary_endpoint=BASE_PROTOCOL["primary_endpoint"],
            secondary_endpoints=BASE_PROTOCOL["secondary_endpoints"],
            duration_weeks=BASE_PROTOCOL["duration_weeks"],
            dosing=BASE_PROTOCOL["dosing"],
            inclusion_criteria=BASE_PROTOCOL["inclusion_criteria"],
            exclusion_criteria=BASE_PROTOCOL["exclusion_criteria"],
            status="draft",
        )

        from app.services.generator import FULL_SECTIONS
        texts = {s: _fallback_section(s, proto) for s in FULL_SECTIONS}

        for section, text in texts.items():
            assert "FOR REVIEW ONLY" in text, f"Section {section} missing FOR REVIEW ONLY marker"

    @pytest.mark.asyncio
    async def test_hp_sap_fallback_unique(self, client, admin_token):
        """HP: SAP fallback is unique (not same as introduction fallback)."""
        from app.services.generator import _fallback_section
        from app.models.protocol import Protocol

        proto = Protocol(
            id="test-id",
            title=BASE_PROTOCOL["title"],
            drug_name=BASE_PROTOCOL["drug_name"],
            inn=BASE_PROTOCOL["inn"],
            phase=BASE_PROTOCOL["phase"],
            therapeutic_area=BASE_PROTOCOL["therapeutic_area"],
            indication=BASE_PROTOCOL["indication"],
            population=BASE_PROTOCOL["population"],
            primary_endpoint=BASE_PROTOCOL["primary_endpoint"],
            secondary_endpoints=BASE_PROTOCOL["secondary_endpoints"],
            duration_weeks=BASE_PROTOCOL["duration_weeks"],
            dosing=BASE_PROTOCOL["dosing"],
            inclusion_criteria=BASE_PROTOCOL["inclusion_criteria"],
            exclusion_criteria=BASE_PROTOCOL["exclusion_criteria"],
            status="draft",
        )

        sap_text = _fallback_section("sap", proto)
        icf_text = _fallback_section("icf", proto)
        intro_text = _fallback_section("introduction", proto)

        assert sap_text != icf_text, "SAP and ICF fallbacks must differ"
        assert sap_text != intro_text, "SAP and Introduction fallbacks must differ"
        assert "Appendix A" in sap_text
        assert "Appendix B" in icf_text


# ─── ALTERNATIVE / EDGE CASES ────────────────────────────────────────────────

class TestAlternative:
    @pytest.mark.asyncio
    async def test_alt_edit_meta_empty_exclusion_criteria(self, client, admin_token):
        """ALT: PATCH with empty exclusion_criteria clears the list."""
        r = await client.post(
            "/api/v1/protocols",
            json=BASE_PROTOCOL,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        pid = r.json()["id"]

        resp = await client.patch(
            f"/api/v1/protocols/{pid}",
            json={"exclusion_criteria": []},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["exclusion_criteria"] == []

    @pytest.mark.asyncio
    async def test_alt_many_exclusion_criteria(self, client, admin_token):
        """ALT: protocol with 10 exclusion criteria saves all of them."""
        body = {**BASE_PROTOCOL, "exclusion_criteria": [f"Критерий исключения {i}" for i in range(10)]}
        r = await client.post(
            "/api/v1/protocols",
            json=body,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 201
        pid = r.json()["id"]

        g = await client.get(
            f"/api/v1/protocols/{pid}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert len(g.json()["exclusion_criteria"]) == 10

    @pytest.mark.asyncio
    async def test_alt_fallback_contains_protocol_params(self, client, admin_token):
        """ALT: fallback section includes actual protocol drug name."""
        from app.services.generator import _fallback_section
        from app.models.protocol import Protocol

        proto = Protocol(
            id="test-id",
            title="Test",
            drug_name="BCD-UNIQUE-TEST",
            inn="тест-inn",
            phase="II",
            therapeutic_area="Онкология",
            indication="Тест показание",
            population="Тест популяция",
            primary_endpoint="Тест КТ",
            secondary_endpoints=[],
            duration_weeks=12,
            dosing="1 мг/кг",
            inclusion_criteria=[],
            exclusion_criteria=[],
            status="draft",
        )

        intro = _fallback_section("introduction", proto)
        assert "BCD-UNIQUE-TEST" in intro


# ─── NEGATIVE ────────────────────────────────────────────────────────────────

class TestNegative:
    @pytest.mark.asyncio
    async def test_neg_phase_iv_rejected(self, client, admin_token):
        """NEG: Phase IV is rejected by backend schema validation."""
        body = {**BASE_PROTOCOL, "phase": "IV"}
        r = await client.post(
            "/api/v1/protocols",
            json=body,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_neg_edit_meta_nonexistent_protocol(self, client, admin_token):
        """NEG: PATCH on non-existent protocol returns 404."""
        resp = await client.patch(
            "/api/v1/protocols/00000000-0000-0000-0000-000000000000",
            json={"dosing": "test"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_neg_auditor_cannot_edit_meta(self, client, auditor_token, admin_token):
        """NEG: auditor cannot PATCH protocol metadata."""
        r = await client.post(
            "/api/v1/protocols",
            json=BASE_PROTOCOL,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        pid = r.json()["id"]

        resp = await client.patch(
            f"/api/v1/protocols/{pid}",
            json={"dosing": "попытка изменить"},
            headers={"Authorization": f"Bearer {auditor_token}"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_neg_edit_meta_invalid_phase(self, client, admin_token):
        """NEG: PATCH with invalid phase is rejected."""
        r = await client.post(
            "/api/v1/protocols",
            json=BASE_PROTOCOL,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        pid = r.json()["id"]

        resp = await client.patch(
            f"/api/v1/protocols/{pid}",
            json={"phase": "IV"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_neg_edit_meta_title_too_short(self, client, admin_token):
        """NEG: PATCH with title < 5 chars is rejected."""
        r = await client.post(
            "/api/v1/protocols",
            json=BASE_PROTOCOL,
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        pid = r.json()["id"]

        resp = await client.patch(
            f"/api/v1/protocols/{pid}",
            json={"title": "abc"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422


import pytest_asyncio
