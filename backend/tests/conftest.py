import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from unittest.mock import AsyncMock, patch

from app.main import app
from app.core.database import get_db
from app.models.base import Base


TEST_DB_URL = "postgresql+asyncpg://app:app@db:5432/protocols_test"


@pytest_asyncio.fixture(scope="session")
async def engine():
    eng = create_async_engine(TEST_DB_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
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
    """Mock AI Gateway failure — should trigger fallback, not 500."""
    with patch("app.services.ai_gateway.AIGatewayClient._call") as mock:
        mock.side_effect = Exception("Connection refused")
        yield mock


@pytest.fixture
def mock_consistency_ok():
    """Mock consistency check response."""
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


# ─── Shared payload factories ───────────────────────────────────────────────

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
