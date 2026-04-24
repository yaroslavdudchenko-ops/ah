<!-- v1.1.0 | 2026-04-24 -->

# Frontend Design System Plan

---

**Author:** Frontend Developer / UI-UX Designer  
**Date:** 2026-04-23 | **Updated:** 2026-04-24  
**Version:** 1.1.0  
**Source:** [docs/functional-requirements.md](functional-requirements.md), [docs/ui-ux-brief.md](ui-ux-brief.md)  
**Standards:** Atomic Design (Brad Frost), WCAG 2.1 AA  
**Status:** Partially Implemented (MVP delivered — see актуальные компоненты ниже)

> **Примечание (2026-04-24):** Фронтенд реализован в рамках MVP. Ряд компонентов из этого плана реализован
> с адаптацией под Synthia-брендинг. Storybook и subcomponent catalog — P2 backlog.

---

## 1. Purpose

A design system provides a single source of truth for all UI components, tokens, and patterns across the AI Protocol Generator frontend. It ensures visual consistency, accelerates development, and enforces accessibility requirements.

---

## 2. Technology

| Tool | Choice | Reason |
|------|--------|--------|
| Component framework | React 18 + TypeScript | Project standard |
| Styling | Tailwind CSS | Utility-first, no custom CSS overhead |
| Component catalog | Storybook (optional P2) | Visual documentation |
| Icons | Heroicons v2 | Tailwind-compatible, MIT license |
| Typography | Inter (Google Fonts) | Readable, widely used in medical SaaS |

---

## 3. Design Tokens (Tailwind config)

### Color palette

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        // Brand
        primary:   { DEFAULT: '#2563EB', hover: '#1D4ED8', light: '#EFF6FF' },
        secondary: { DEFAULT: '#7C3AED', hover: '#6D28D9' },

        // Semantic
        success:  { DEFAULT: '#16A34A', bg: '#F0FDF4' },
        warning:  { DEFAULT: '#D97706', bg: '#FFFBEB' },
        danger:   { DEFAULT: '#DC2626', bg: '#FEF2F2' },
        info:     { DEFAULT: '#0284C7', bg: '#F0F9FF' },

        // Clinical-specific
        clinical: {
          disclaimer: '#92400E',   // amber-800 — AI disclaimer text
          watermark:  '#6B7280',   // gray-500 — watermark text
          score: {
            high:   '#16A34A',     // compliance >= 80
            medium: '#D97706',     // compliance 60-79
            low:    '#DC2626',     // compliance < 60
          }
        },

        // Neutrals
        surface:  '#F9FAFB',
        border:   '#E5E7EB',
      }
    }
  }
}
```

### Typography scale

```javascript
fontSize: {
  xs:   ['0.75rem',  { lineHeight: '1rem' }],
  sm:   ['0.875rem', { lineHeight: '1.25rem' }],
  base: ['1rem',     { lineHeight: '1.5rem' }],
  lg:   ['1.125rem', { lineHeight: '1.75rem' }],
  xl:   ['1.25rem',  { lineHeight: '1.75rem' }],
  '2xl':['1.5rem',   { lineHeight: '2rem' }],
  '3xl':['1.875rem', { lineHeight: '2.25rem' }],
}
```

### Spacing
Use Tailwind default spacing scale (4px base unit). Custom additions:
```javascript
spacing: {
  '18': '4.5rem',
  '72': '18rem',
  '84': '21rem',
  '96': '24rem',
}
```

---

## 4. Component Library (Atomic Design)

### Atoms

| Component | File | Description |
|-----------|------|-------------|
| `Button` | `components/ui/Button.tsx` | variants: primary, secondary, ghost, danger; sizes: sm, md, lg |
| `Badge` | `components/ui/Badge.tsx` | variants: success, warning, danger, info, gray |
| `Input` | `components/ui/Input.tsx` | text, number, textarea with error state |
| `Select` | `components/ui/Select.tsx` | single select with option groups |
| `Spinner` | `components/ui/Spinner.tsx` | sizes: sm, md, lg |
| `Tooltip` | `components/ui/Tooltip.tsx` | hover info with 300ms delay |

### Molecules

| Component | File | Description |
|-----------|------|-------------|
| `FormField` | `components/ui/FormField.tsx` | label + Input + error message |
| `TagInput` | `components/ui/TagInput.tsx` | list editor for inclusion/exclusion criteria |
| `ComplianceBadge` | `components/clinical/ComplianceBadge.tsx` | compliance_score 0–100 with color |
| `AIDisclaimer` | `components/clinical/AIDisclaimer.tsx` | amber warning bar for AI content |
| `ProgressSteps` | `components/ui/ProgressSteps.tsx` | 3-step form progress indicator |

### Organisms

| Component | File | Description |
|-----------|------|-------------|
| `ProtocolCard` | `components/protocol/ProtocolCard.tsx` | protocol list item with status badge |
| `SectionViewer` | `components/protocol/SectionViewer.tsx` | single protocol section with regenerate button |
| `GenerationStatus` | `components/protocol/GenerationStatus.tsx` | AI generation progress (idle/generating/complete/error) |
| `DiffSection` | `components/protocol/DiffSection.tsx` | side-by-side diff with color lines |
| `ExportDialog` | `components/protocol/ExportDialog.tsx` | format selector + watermark warning |
| `Navbar` | `components/layout/Navbar.tsx` | top navigation with project name |
| `Sidebar` | `components/layout/Sidebar.tsx` | protocol section navigation |

---

## 5. Clinical UI Patterns (mandatory)

### AI Disclaimer (every AI-generated section)
```tsx
// components/clinical/AIDisclaimer.tsx
export const AIDisclaimer = () => (
  <div className="flex items-center gap-2 rounded-md bg-amber-50 border border-amber-200 px-3 py-2 text-xs text-amber-800">
    <ExclamationTriangleIcon className="h-4 w-4 shrink-0" />
    AI-Assisted. Requires qualified person review.
  </div>
);
```

### Compliance Score Badge
```tsx
// components/clinical/ComplianceBadge.tsx
export const ComplianceBadge = ({ score }: { score: number }) => {
  const color = score >= 80 ? 'text-green-700 bg-green-50 border-green-200'
              : score >= 60 ? 'text-yellow-700 bg-yellow-50 border-yellow-200'
              : 'text-red-700 bg-red-50 border-red-200';
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${color}`}>
      GCP Score: {score}/100
    </span>
  );
};
```

### Export Watermark Warning
```tsx
<div className="rounded-md bg-gray-50 border border-gray-200 p-3 text-sm text-gray-600">
  ⚠ Export will contain: <br/>
  <code className="text-xs">"FOR DEMONSTRATION PURPOSES ONLY — SYNTHETIC DATA"</code>
</div>
```

---

## 6. Accessibility (WCAG 2.1 AA)

| Rule | Implementation |
|------|---------------|
| Color contrast ≥ 4.5:1 for text | Use defined palette only — don't override with custom colors |
| Focus visible on all interactive elements | `focus:outline-none focus:ring-2 focus:ring-primary` |
| Form labels linked to inputs | Always use `htmlFor` + `id` pair |
| Error messages associated with inputs | `aria-describedby` on error text |
| Loading states announced | `aria-live="polite"` on generation status |
| Keyboard navigation | Tab order follows visual layout |

---

## 7. Implementation Roadmap

| Phase | Tasks | Priority |
|-------|-------|----------|
| **P0 — Tokens** | Set up `tailwind.config.js` with full token set | Before any components |
| **P0 — Atoms** | Button, Badge, Input, Select, Spinner | Phase 5 start |
| **P0 — Clinical** | AIDisclaimer, ComplianceBadge, ExportDialog watermark | Before any protocol UI |
| **P1 — Molecules** | FormField, TagInput, ProgressSteps, GenerationStatus | Phase 5 |
| **P1 — Organisms** | ProtocolCard, SectionViewer, DiffSection | Phase 5 |
| **P2 — Storybook** | Component catalog with all variants | After MVP |

---

## 8. File structure

```
frontend/src/
  components/
    ui/                    ← Atoms & generic molecules
      Button.tsx
      Badge.tsx
      Input.tsx
      Select.tsx
      Spinner.tsx
      FormField.tsx
      TagInput.tsx
    clinical/              ← Clinical-specific components
      AIDisclaimer.tsx
      ComplianceBadge.tsx
      WatermarkNotice.tsx
    protocol/              ← Protocol-domain organisms
      ProtocolCard.tsx
      SectionViewer.tsx
      GenerationStatus.tsx
      DiffSection.tsx
      ExportDialog.tsx
    layout/
      Navbar.tsx
      Sidebar.tsx
  styles/
    globals.css            ← Tailwind directives only
```

---

## 9. Фактически реализованные компоненты (MVP, 2026-04-24)

| Компонент | Файл | Статус |
|---|---|---|
| Layout + Synthia branding | `components/Layout.tsx` | ✅ Реализован |
| SynthiaOrb (SVG Morphing Blob) | `components/SynthiaOrb.tsx` | ✅ Реализован |
| DraftModal (печать/PDF) | `components/DraftModal.tsx` | ✅ Реализован |
| TagBadge (hash-based color) | `components/TagBadge.tsx` | ✅ Реализован |
| TagInput (add/remove) | `components/TagInput.tsx` | ✅ Реализован |
| StatusBadge | `components/StatusBadge.tsx` | ✅ Реализован |
| Spinner | `components/Spinner.tsx` | ✅ Реализован |
| ErrorAlert | `components/ErrorAlert.tsx` | ✅ Реализован |
| ProtectedRoute (RBAC) | `components/ProtectedRoute.tsx` | ✅ Реализован |
| Button, Badge, Input, FormField | — | Tailwind inline (не выделены в атомы) |
| Storybook | — | P2 Backlog |

**Last Updated:** 2026-04-24  
**Status:** Partially Implemented (MVP complete)
