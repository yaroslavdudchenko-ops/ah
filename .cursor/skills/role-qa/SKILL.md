---
name: role-qa
description: Activates QA Engineer perspective for AI Protocol Generator. Use when writing test cases, updating the test plan, running tests, validating demo scenarios, or checking the pre-delivery regression checklist. Enforces P0 test case coverage and synthetic demo data policy.
---

# Role: QA Engineer — AI Protocol Generator

## Test strategy
| Level | Tool | Scope |
|-------|------|-------|
| Unit | pytest | Services, utils — mocked DB and AI Gateway |
| Integration | pytest + testcontainers | Real PostgreSQL, Alembic migrations |
| E2E | Playwright | Critical user paths only |
| Manual | checklist | Demo scenarios before delivery |

## P0 test cases (must pass before demo)

| ID | Given | When | Then |
|----|-------|------|------|
| TC-01 | Template Phase II exists | `POST /protocols` with BCD-100 data | 12 sections in DB (MVP min 7), status=`completed` |
| TC-02 | Protocol v1 exists | Edit title via `PATCH`, then `GET /diff` | `version_number=2`, diff shows title change |
| TC-03 | Protocol with sections exists | `POST /protocols/{id}/check` | `compliance_score` (0–100), `issues[]` typed, `severity` present |
| TC-04 | Protocol v1 exists | `GET /protocols/{id}/export?format=docx` | File downloads, H1/H2/H3 headings present |
| TC-05 | Export downloaded | Open DOCX | Contains `"FOR DEMONSTRATION PURPOSES ONLY — SYNTHETIC DATA"` |
| TC-06 | Services running | `GET /health` | `{"status":"ok","db":"connected"}` |

## Demo data policy
Only use:
- **BCD-100** — anti-PD-1, Phase II, oncology, 96 weeks
- **BCD-089** — IL-17 inhibitor, Phase III, rheumatology, 52 weeks

Never use real patient data or confidential clinical trial results.

## Mocking AI Gateway in tests
```python
@pytest.fixture
def mock_ai_gateway(httpx_mock, settings):
    httpx_mock.add_response(
        url=f"{settings.AI_GATEWAY_URL}/v1/chat/completions",
        json={"choices": [{"message": {"content": "## Introduction\nSynthetic content..."}}]}
    )
```
При тестировании недоступности Gateway — проверяй HTTP 503 (не 500, не fallback на внешние LLM).

## Regression checklist (run before every demo)
- [ ] TC-01 through TC-06 pass
- [ ] `docker compose up` starts clean
- [ ] No 500 errors in logs
- [ ] Export file opens in Word without errors
- [ ] Compliance badge visible in UI
- [ ] Watermark present in exported DOCX

## Checklist
- [ ] All P0 test cases pass
- [ ] Synthetic data only (BCD-100 / BCD-089)
- [ ] Test plan at `docs/test-plan.md` updated after new cases
