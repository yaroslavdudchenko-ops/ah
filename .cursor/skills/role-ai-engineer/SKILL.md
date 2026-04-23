---
name: role-ai-engineer
description: Activates AI Engineer perspective for AI Protocol Generator. Use when writing or reviewing prompts, AI Gateway integration, consistency checks, GCP compliance logic, or PROMPTS.md. Enforces prompt structure with therapeutic_area_context, 12-section coverage, typed issue categories. Only internal AI Gateway (InHouse/Qwen3.5-122B) — no external LLMs allowed.
---

# Role: AI Engineer — AI Protocol Generator

## Provider

**Единственный провайдер — внутренний AI Gateway. Внешние LLM (OpenRouter, OpenAI, Anthropic) запрещены политикой ИБ (NFR-08).**

| Параметр | Значение |
|---|---|
| Endpoint | `POST ${AI_GATEWAY_URL}/v1/chat/completions` |
| Auth | `Authorization: Bearer $AI_GATEWAY_API_KEY` |
| Модель | `InHouse/Qwen3.5-122B` |
| При недоступности | HTTP 503 (не 500), не fallback на внешние LLM |

## Prompt file locations
```
prompts/
  system-prompt.md
  section-generators/
    introduction.md   objectives.md   design.md
    population.md     dosing.md       efficacy.md
    safety.md         statistics.md   ethics.md
  validation-prompts/
    consistency-check.md
    gcp-compliance.md
```

## Required prompt structure

```markdown
## ЗАДАЧА
[One sentence goal]

## КОНТЕКСТ
- Препарат: {drug_name} ({inn})
- Фаза: {phase}
- Терапевтическая область: {therapeutic_area}

## ТРЕБОВАНИЯ
- Используй терминологию ICH E6 R2
- Выходной формат — markdown, без preamble
- Длина раздела: 200–400 слов

## ГЕНЕРИРУЙ ТОЛЬКО РАЗДЕЛ "{section_name}"
```

## Context objects (inject into every call)
```python
THERAPEUTIC_AREA_CONTEXT = {
    "oncology": {"terminology": ["RECIST","ORR","PFS","OS","DOR"], "ref": "ICH E6 §6.4"},
    "rheumatology": {"terminology": ["ACR20","DAS28","HAQ-DI"], "ref": "ICH E6 §6.4"},
}
PHASE_CONTEXT = {
    "I": {"focus": "безопасность и ФК/ФД", "language": "exploratory"},
    "II": {"focus": "предварительная эффективность", "language": "investigational"},
    "III": {"focus": "подтверждение эффективности", "language": "confirmatory"},
}
```

## 12 sections to generate (FR-03.1)
`title_page` `synopsis` `introduction` `objectives` `design` `population` `treatment` `efficacy` `safety` `statistics` `ethics` `references`

MVP minimum (7 sections): `introduction` `objectives` `design` `population` `treatment` `efficacy` `safety`

## Consistency check — required issue types
```
terminology_mismatch     endpoint_mismatch        population_inconsistency
duration_mismatch        dosing_inconsistency      sample_size_endpoint
```

Response schema:
```json
{
  "compliance_score": 87,
  "issues": [
    {"type": "terminology_mismatch", "severity": "high",
     "description": "...", "section": "objectives", "suggestion": "..."}
  ],
  "gcp_hints": [
    {"category": "ICH E6", "priority": "high",
     "recommendation": "...", "gcp_reference": "§6.4.2"}
  ]
}
```

## Retry & degradation policy

1. AI Gateway primary call (`AI_GATEWAY_URL`)
2. Retry × 3 (exponential backoff via `tenacity`) — при сетевых ошибках
3. При исчерпании попыток → HTTP 503 с описанием причины

**Fallback на внешние LLM (OpenRouter, OpenAI и др.) запрещён.** Данные КИ не могут покидать внутренний контур.

## PROMPTS.md maintenance
After every prompt change, log to PROMPTS.md:
- Version, date, section, change summary, avg token cost

## Checklist
- [ ] All 12 section prompts exist in `prompts/section-generators/` (MVP: 7 minimum)
- [ ] All JSON response fields use snake_case
- [ ] `consistency-check.md` returns typed issues with severity
- [ ] При недоступности Gateway — возвращается HTTP 503 (не 500, не fallback на внешние LLM)
- [ ] PROMPTS.md updated with latest iteration notes
