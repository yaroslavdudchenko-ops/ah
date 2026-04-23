"""
conftest.py — pytest fixtures for integration & unit tests.

Uses function-scoped DB engine to avoid async event-loop conflicts
with pytest-asyncio >= 1.0 session-scoped fixtures.
Each test gets a clean protocols_test DB (tables created/dropped per function).
"""
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from unittest.mock import patch

from app.main import app
from app.core.database import get_db
from app.core.security import get_current_user, require_write
from app.models.base import Base


def _test_db_url() -> str:
    base = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://app:app@db:5432/protocols",
    )
    return base.rsplit("/", 1)[0] + "/protocols_test"


TEST_DB_URL = _test_db_url()


_SEED_SQL = """
INSERT INTO templates (id, name, phase, design_type, description, section_prompts) VALUES
('tpl-phase-i-001', 'Phase I — Open-Label FIH', 'I', 'open-label',
 'Первое исследование на человеке (FIH), открытое, эскалация дозы', '{}'),
('tpl-phase-ii-001', 'Phase II — Single-Arm', 'II', 'open-label',
 'Однорукавное исследование эффективности Phase II', '{}'),
('tpl-phase-iii-001', 'Phase III — RCT Placebo-Controlled', 'III', 'randomized',
 'Рандомизированное двойное слепое плацебо-контролируемое исследование Phase III', '{}')
ON CONFLICT DO NOTHING;
"""


@pytest_asyncio.fixture
async def db_session():
    """Fresh DB per test: create all tables + seed, yield session, drop all tables."""
    from sqlalchemy import text

    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text(_SEED_SQL))

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    """ASGI test client wired to the fresh test DB, authenticated as admin."""
    _admin = {"username": "admin", "role": "admin"}

    async def override_get_db():
        yield db_session

    async def override_auth():
        return _admin

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_auth
    app.dependency_overrides[require_write] = override_auth

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auditor_client(db_session):
    """ASGI test client authenticated as auditor (read-only)."""
    _auditor = {"username": "auditor", "role": "auditor"}

    async def override_get_db():
        yield db_session

    async def override_auth():
        return _auditor

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_auth

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def mock_ai_gateway_ok():
    """Mock successful AI Gateway response."""
    with patch("app.services.ai_gateway.AIGatewayClient._call") as mock:
        mock.return_value = (
            "## Introduction\n\nSynthetic content for testing purposes.\n"
            "**FOR REVIEW ONLY — SYNTHETIC DATA**\n"
        )
        yield mock


@pytest.fixture
def mock_ai_gateway_fail():
    """Mock AI Gateway failure — should return HTTP 503, not 500."""
    with patch("app.services.ai_gateway.AIGatewayClient._call") as mock:
        mock.side_effect = Exception("Connection refused")
        yield mock


@pytest.fixture
def mock_consistency_ok():
    """Mock consistency check — returns a pre-built CheckResponse."""
    with patch("app.services.consistency.check_consistency") as mock:
        from app.schemas.generate import CheckResponse, IssueItem, GcpHint

        mock.return_value = CheckResponse(
            compliance_score=82,
            rf_compliance_score=78,
            issues=[
                IssueItem(
                    type="terminology_mismatch",
                    severity="medium",
                    section="objectives",
                    description="Inconsistent drug name usage",
                    suggestion="Use МНН consistently",
                )
            ],
            gcp_hints=[
                GcpHint(
                    category="ICH E6",
                    priority="medium",
                    recommendation="Specify primary endpoint measurement timepoint",
                    gcp_reference="ICH E6 R2 §6.4",
                )
            ],
            summary="82/100 — minor issues found",
            rf_summary="78/100 — RF compliance checked",
        )
        yield mock


# ─── Demo payload factories ──────────────────────────────────────────────────

def bcd100_payload() -> dict:
    return {
        "title": "BCD-100 Phase II Study in Metastatic Melanoma",
        "drug_name": "BCD-100",
        "inn": "Пролголимаб",
        "phase": "II",
        "therapeutic_area": "oncology",
        "indication": "Метастатическая меланома, прогрессия после 1 линии терапии",
        "population": "Взрослые ≥18 лет, ECOG 0-1",
        "primary_endpoint": "ORR по RECIST 1.1",
        "secondary_endpoints": ["PFS", "OS", "DoR"],
        "duration_weeks": 96,
        "dosing": "1 мг/кг в/в каждые 2 недели",
        "inclusion_criteria": ["Возраст ≥18 лет", "ECOG 0-1"],
        "exclusion_criteria": ["Аутоиммунные заболевания"],
    }


def bcd089_payload() -> dict:
    return {
        "title": "BCD-089 Phase III RCT in Moderate-to-Severe Psoriasis",
        "drug_name": "BCD-089",
        "inn": "Биоаналог иксекизумаба",
        "phase": "III",
        "therapeutic_area": "dermatology",
        "indication": "Псориаз среднетяжёлый и тяжёлый",
        "population": "Взрослые ≥18 лет, PASI ≥12",
        "primary_endpoint": "PASI 75 на 12 неделе",
        "secondary_endpoints": ["PASI 90", "IGA 0/1"],
        "duration_weeks": 52,
        "dosing": "160 мг п/к неделя 0, затем 80 мг каждые 2 недели",
        "inclusion_criteria": ["PASI ≥12", "BSA ≥10%"],
        "exclusion_criteria": ["Беременность", "Активный туберкулёз"],
    }
