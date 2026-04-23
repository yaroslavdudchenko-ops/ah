import pytest


@pytest.mark.asyncio
async def test_list_templates_returns_seeds(client):
    """HP: 3 seed templates present after migration."""
    resp = await client.get("/api/v1/templates")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    phases = {t["phase"] for t in data}
    assert {"I", "II", "III"}.issubset(phases)


@pytest.mark.asyncio
async def test_get_template_by_id(client):
    """HP: GET single template by ID."""
    templates = (await client.get("/api/v1/templates")).json()
    tid = templates[0]["id"]
    resp = await client.get(f"/api/v1/templates/{tid}")
    assert resp.status_code == 200
    assert resp.json()["id"] == tid


@pytest.mark.asyncio
async def test_get_nonexistent_template(client):
    """ALT-04.3: GET nonexistent template → 404."""
    resp = await client.get("/api/v1/templates/nonexistent-id")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "TEMPLATE_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_template_stub_501(client):
    """ALT-05.2: POST /templates → 501 NOT_IMPLEMENTED."""
    resp = await client.post("/api/v1/templates", json={})
    assert resp.status_code == 501
    assert resp.json()["error"]["code"] == "NOT_IMPLEMENTED"
