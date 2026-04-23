import pytest


@pytest.mark.asyncio
async def test_health_ok(client):
    """HP: health endpoint returns 200 with db connected."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["db"] == "connected"
