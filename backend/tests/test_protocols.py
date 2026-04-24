import pytest
from tests.conftest import bcd100_payload, bcd089_payload
from app.models.protocol import ProtocolVersion


# ─── Happy Path ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_protocol_bcd100(client):
    """HP-01.4: Create BCD-100 protocol — 201 + correct fields."""
    resp = await client.post("/api/v1/protocols", json=bcd100_payload())
    assert resp.status_code == 201
    data = resp.json()
    assert data["drug_name"] == "BCD-100"
    assert data["phase"] == "II"
    assert data["status"] == "draft"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_protocol_bcd089(client):
    """HP-02.1: Create BCD-089 protocol — Phase III."""
    resp = await client.post("/api/v1/protocols", json=bcd089_payload())
    assert resp.status_code == 201
    data = resp.json()
    assert data["phase"] == "III"
    assert data["therapeutic_area"] == "dermatology"


@pytest.mark.asyncio
async def test_list_protocols(client):
    """HP-01.14: List returns both protocols."""
    await client.post("/api/v1/protocols", json=bcd100_payload())
    await client.post("/api/v1/protocols", json=bcd089_payload())
    resp = await client.get("/api/v1/protocols")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_get_protocol(client):
    """HP: GET single protocol returns full object."""
    create = await client.post("/api/v1/protocols", json=bcd100_payload())
    pid = create.json()["id"]
    resp = await client.get(f"/api/v1/protocols/{pid}")
    assert resp.status_code == 200
    assert resp.json()["id"] == pid


@pytest.mark.asyncio
async def test_update_protocol(client):
    """HP: PATCH updates status field."""
    create = await client.post("/api/v1/protocols", json=bcd100_payload())
    pid = create.json()["id"]
    resp = await client.patch(f"/api/v1/protocols/{pid}", json={"status": "in_review"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_review"


@pytest.mark.asyncio
async def test_delete_protocol_blocked(client):
    """ALT-08.1: DELETE always returns 403 DELETION_DISABLED (GCP/ALCOA++ policy)."""
    create = await client.post("/api/v1/protocols", json=bcd100_payload())
    pid = create.json()["id"]
    resp = await client.delete(f"/api/v1/protocols/{pid}")
    assert resp.status_code == 403
    assert resp.json()["detail"]["error"]["code"] == "DELETION_DISABLED"


@pytest.mark.asyncio
async def test_protocol_still_exists_after_delete_attempt(client):
    """ALT-08.2: GET after DELETE attempt → 200 (protocol retained per ALCOA++)."""
    create = await client.post("/api/v1/protocols", json=bcd100_payload())
    pid = create.json()["id"]
    await client.delete(f"/api/v1/protocols/{pid}")
    resp = await client.get(f"/api/v1/protocols/{pid}")
    assert resp.status_code == 200
    assert resp.json()["id"] == pid


# ─── Validation / Negative ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_invalid_phase(client):
    """ALT-01.2: phase='phase_2' (wrong format) → 422 validation error."""
    payload = bcd100_payload()
    payload["phase"] = "phase_2"
    resp = await client.post("/api/v1/protocols", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_phase_iv_valid(client):
    """ALT-01.2b: phase='IV' → 201 (Phase IV теперь поддерживается)."""
    payload = bcd100_payload()
    payload["phase"] = "IV"
    resp = await client.post("/api/v1/protocols", json=payload)
    assert resp.status_code == 201
    assert resp.json()["phase"] == "IV"


@pytest.mark.asyncio
async def test_create_duration_zero(client):
    """ALT-01.3: duration_weeks=0 → 422."""
    payload = bcd100_payload()
    payload["duration_weeks"] = 0
    resp = await client.post("/api/v1/protocols", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_duration_too_large(client):
    """ALT-01.4: duration_weeks=999 → 422."""
    payload = bcd100_payload()
    payload["duration_weeks"] = 999
    resp = await client.post("/api/v1/protocols", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_title_too_short(client):
    """ALT-01.5: title length < 5 → 422."""
    payload = bcd100_payload()
    payload["title"] = "ABC"
    resp = await client.post("/api/v1/protocols", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_missing_required_field(client):
    """ALT-01.1: missing primary_endpoint → 422."""
    payload = bcd100_payload()
    del payload["primary_endpoint"]
    resp = await client.post("/api/v1/protocols", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_nonexistent_protocol(client):
    """ALT-04.1: GET /protocols/invalid-uuid → 404 with error body."""
    resp = await client.get("/api/v1/protocols/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"]["code"] == "PROTOCOL_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_many_exclusion_criteria(client):
    """ALT-06.1: 20 exclusion criteria saved correctly."""
    payload = bcd100_payload()
    payload["exclusion_criteria"] = [f"Criterion {i}" for i in range(20)]
    resp = await client.post("/api/v1/protocols", json=payload)
    assert resp.status_code == 201
    assert len(resp.json()["exclusion_criteria"]) == 20


@pytest.mark.asyncio
async def test_create_empty_secondary_endpoints(client):
    """ALT-06.3: empty secondary_endpoints is valid."""
    payload = bcd100_payload()
    payload["secondary_endpoints"] = []
    resp = await client.post("/api/v1/protocols", json=payload)
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_diff_returns_404_when_versions_missing(client):
    """NEG-DIFF-01: GET /diff без версий в БД → 404 VERSION_NOT_FOUND."""
    create = await client.post("/api/v1/protocols", json=bcd100_payload())
    pid = create.json()["id"]
    resp = await client.get(f"/api/v1/protocols/{pid}/diff?v1=1&v2=2")
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"]["code"] == "VERSION_NOT_FOUND"


@pytest.mark.asyncio
async def test_diff_compare_two_versions(client, db_session):
    """HP-DIFF-01: две версии в тестовой БД → 200 + sections[]."""
    create = await client.post("/api/v1/protocols", json=bcd100_payload())
    pid = create.json()["id"]
    db_session.add(
        ProtocolVersion(
            protocol_id=pid,
            version_number=1,
            content={"introduction": "Version one text.\n"},
        )
    )
    db_session.add(
        ProtocolVersion(
            protocol_id=pid,
            version_number=2,
            content={"introduction": "Version two different text.\n"},
        )
    )
    await db_session.commit()

    resp = await client.get(f"/api/v1/protocols/{pid}/diff?v1=1&v2=2")
    assert resp.status_code == 200
    body = resp.json()
    assert body["protocol_id"] == pid
    assert body["v1"] == 1 and body["v2"] == 2
    assert isinstance(body["sections"], list)
    intro = next((s for s in body["sections"] if s["section"] == "introduction"), None)
    assert intro is not None
    assert intro["changed"] is True
