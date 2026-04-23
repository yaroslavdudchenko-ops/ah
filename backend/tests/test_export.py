import pytest
from tests.conftest import bcd100_payload
from app.models.protocol import Protocol, ProtocolVersion
from app.services.export_service import export_markdown, export_html


# ─── Happy Path ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_md_happy_path(client):
    """HP-01.10: Export MD after generation returns file."""
    create = await client.post("/api/v1/protocols", json=bcd100_payload())
    pid = create.json()["id"]
    # Inject a version directly via API simulate
    resp = await client.get(f"/api/v1/protocols/{pid}/export?format=md")
    # No content yet → 422
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_export_before_generation(client):
    """ALT-03.1: Export before generate → 422 NO_CONTENT."""
    create = await client.post("/api/v1/protocols", json=bcd100_payload())
    pid = create.json()["id"]
    resp = await client.get(f"/api/v1/protocols/{pid}/export?format=md")
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"]["code"] == "NO_CONTENT"


@pytest.mark.asyncio
async def test_export_nonexistent_protocol(client):
    """ALT-04: Export nonexistent → 404."""
    resp = await client.get(
        "/api/v1/protocols/00000000-0000-0000-0000-000000000000/export?format=md"
    )
    assert resp.status_code == 404


# ─── Unit tests for export_service ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_markdown_structure():
    """Unit: MD export contains required sections."""
    from app.models.protocol import Protocol, ProtocolVersion
    import datetime

    protocol = Protocol(
        id="test-id", title="Test Protocol", drug_name="Drug-X", inn="Inn-X",
        phase="II", therapeutic_area="oncology", indication="Test indication",
        population="Test population", primary_endpoint="ORR",
        secondary_endpoints=[], duration_weeks=24, dosing="10 mg/kg",
        inclusion_criteria=[], exclusion_criteria=[], status="draft",
    )
    version = ProtocolVersion(
        id="ver-id", protocol_id="test-id", version_number=1,
        content={"introduction": "## Introduction\nTest content."},
        generated_by="InHouse/Qwen3.5-122B",
        created_at=datetime.datetime.now(),
    )

    md = export_markdown(protocol, version).decode("utf-8")
    assert "# Test Protocol" in md
    assert "FOR DEMONSTRATION PURPOSES ONLY" in md
    assert "AI-Assisted. Requires qualified person review." in md
    assert "## Introduction" in md
    assert "Drug-X" in md


@pytest.mark.asyncio
async def test_export_html_is_valid():
    """Unit: HTML export wraps content in valid HTML."""
    import datetime
    from app.models.protocol import Protocol, ProtocolVersion

    protocol = Protocol(
        id="test-id", title="HTML Test", drug_name="Drug-Y", inn="Inn-Y",
        phase="III", therapeutic_area="dermatology", indication="Psoriasis",
        population="Adults", primary_endpoint="PASI 75",
        secondary_endpoints=["PASI 90"], duration_weeks=52, dosing="80mg sc",
        inclusion_criteria=[], exclusion_criteria=[], status="draft",
    )
    version = ProtocolVersion(
        id="ver-id", protocol_id="test-id", version_number=1,
        content={"design": "## Design\nRandomized controlled trial."},
        generated_by="InHouse/Qwen3.5-122B",
        created_at=datetime.datetime.now(),
    )

    html = export_html(protocol, version).decode("utf-8")
    assert "<!DOCTYPE html>" in html
    assert "<html" in html
    assert "HTML Test" in html
    assert "PASI 75" in html
    assert "FOR DEMONSTRATION PURPOSES ONLY" in html
