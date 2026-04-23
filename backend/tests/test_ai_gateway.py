import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.services.ai_gateway import AIGatewayClient, AIGatewayError


@pytest.mark.asyncio
async def test_ai_gateway_returns_text_on_success():
    """Unit: Successful call returns message content."""
    client = AIGatewayClient()
    with patch.object(client, "_call", new=AsyncMock(return_value="## Introduction\nContent.")):
        result = await client.complete("system prompt", "user prompt")
    assert "Introduction" in result


@pytest.mark.asyncio
async def test_ai_gateway_raises_on_3_failures():
    """ALT-02: After 3 retries raises AIGatewayError (not 500)."""
    client = AIGatewayClient()
    with patch.object(
        client, "_call",
        new=AsyncMock(side_effect=httpx.ConnectError("refused"))
    ):
        with pytest.raises(AIGatewayError):
            await client.complete("sys", "usr")


@pytest.mark.asyncio
async def test_ai_gateway_error_message():
    """ALT-02.2: AIGatewayError contains useful message."""
    client = AIGatewayClient()
    with patch.object(
        client, "_call",
        new=AsyncMock(side_effect=Exception("timeout"))
    ):
        try:
            await client.complete("sys", "usr")
        except AIGatewayError as e:
            assert "retries" in str(e).lower() or "unavailable" in str(e).lower()


@pytest.mark.asyncio
async def test_generator_uses_fallback_when_gateway_fails():
    """ALT-02.1: Generator falls back to template on AI error — no exception."""
    from app.services.generator import generate_protocol_sections
    import datetime
    from app.models.protocol import Protocol

    protocol = Protocol(
        id="test-id", title="Test", drug_name="Drug", inn="Inn",
        phase="II", therapeutic_area="oncology", indication="Test",
        population="Pop", primary_endpoint="ORR",
        secondary_endpoints=[], duration_weeks=24, dosing="10mg",
        inclusion_criteria=[], exclusion_criteria=[], status="draft",
    )

    with patch("app.services.generator.ai_client.complete",
               new=AsyncMock(side_effect=AIGatewayError("unavailable"))):
        content = await generate_protocol_sections(protocol, sections=["introduction"])

    assert "introduction" in content
    assert "TEMPLATE FALLBACK" in content["introduction"]


@pytest.mark.asyncio
async def test_generator_section_count():
    """HP: Generator returns all requested sections."""
    from app.services.generator import generate_protocol_sections
    from app.models.protocol import Protocol

    protocol = Protocol(
        id="test-id", title="Test", drug_name="BCD-100", inn="Пролголимаб",
        phase="II", therapeutic_area="oncology",
        indication="Melanoma", population="Adults ECOG 0-1",
        primary_endpoint="ORR", secondary_endpoints=["PFS"],
        duration_weeks=96, dosing="1 mg/kg q2w",
        inclusion_criteria=[], exclusion_criteria=[], status="draft",
    )
    sections = ["introduction", "objectives"]

    with patch("app.services.generator.ai_client.complete",
               new=AsyncMock(return_value="## Section\nContent for testing.")):
        content = await generate_protocol_sections(protocol, sections=sections)

    assert set(content.keys()) == set(sections)
    for sec, text in content.items():
        assert len(text) > 0
