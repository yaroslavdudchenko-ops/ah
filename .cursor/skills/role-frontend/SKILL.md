---
name: role-frontend
description: Activates Frontend Developer perspective for AI Protocol Generator. Use when building React/TypeScript components, Tailwind UI, API hooks, form validation, or the diff/export UI. Enforces component naming, form validation rules, required clinical UI elements, and P0 screen priorities.
---

# Role: Frontend Developer — AI Protocol Generator

## Stack
React 18 | Vite | TypeScript | Tailwind CSS | React Router v6 | TanStack Query (react-query)

## Project layout
```
frontend/
  src/
    api/          # axios/fetch hooks per entity
    components/   # shared UI components
    pages/        # one folder per route
    hooks/        # custom React hooks
    types/        # TypeScript interfaces
  public/
  Dockerfile      # nginx:alpine
```

## P0 screens (implement in this order)
| Screen | Route | Key elements |
|--------|-------|--------------|
| Protocol List | `/` | Status badges, New button, search |
| Create Protocol | `/protocols/new` | 3-step form |
| Protocol Viewer | `/protocols/:id` | Section sidebar, regenerate, compliance badge |
| Diff Viewer | `/protocols/:id/diff` | Side-by-side, color lines |

## Required clinical UI elements
Every component that renders AI content **must** include:
```tsx
<p className="text-xs text-amber-600 mt-2">
  AI-Assisted. Requires qualified person review.
</p>
```

`compliance_score` badge on viewer:
```tsx
<span className={`badge ${score >= 80 ? 'badge-green' : score >= 60 ? 'badge-yellow' : 'badge-red'}`}>
  GCP Score: {score}
</span>
```

## Form validation (FR-02.6 — enforced on submit)
```typescript
const validateProtocol = (data: ProtocolFormData): string[] => {
  const errors: string[] = [];
  if (!['I','II','III'].includes(data.phase)) errors.push('Phase must be I, II, or III');
  if (data.duration_weeks <= 0) errors.push('Duration must be positive');
  if (data.primary_endpoint.length < 3) errors.push('Primary endpoint min 3 chars');
  if (data.title.length < 5) errors.push('Title min 5 chars');
  return errors;
};
```

## Generation polling pattern
```typescript
const { data } = useQuery({
  queryKey: ['generation', taskId],
  queryFn: () => api.getGenerationStatus(protocolId, taskId),
  refetchInterval: (data) => data?.status === 'completed' ? false : 2000,
  enabled: !!taskId,
});
```

## Export watermark preview
Show this text in the export dialog before download:
```
⚠ This export will contain:
"FOR DEMONSTRATION PURPOSES ONLY — SYNTHETIC DATA"
```

## Checklist
- [ ] Form blocks submit when validation fails
- [ ] AI disclaimer shown on all generated content
- [ ] compliance_score badge renders with correct color
- [ ] Export dialog shows watermark warning
- [ ] Diff view shows added/removed lines in green/red
