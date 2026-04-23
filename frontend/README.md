# Frontend — AI Protocol Generator

**Version:** 1.0.0 | **Date:** 2026-04-23

React 18 + Vite + TypeScript + Tailwind CSS

---

## Структура

```
frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── main.tsx                    # Entry point
│   ├── App.tsx                     # Router + Layout
│   ├── api/
│   │   ├── client.ts               # axios/fetch базовый клиент, base URL
│   │   ├── protocols.ts            # API calls: протоколы, версии, diff
│   │   ├── templates.ts            # API calls: шаблоны
│   │   └── types.ts                # TypeScript типы (Protocol, Version, Template...)
│   ├── pages/
│   │   ├── HomePage.tsx            # Список протоколов
│   │   ├── CreateProtocolPage.tsx  # Форма создания
│   │   ├── ProtocolPage.tsx        # Просмотр + редактор секций
│   │   └── DiffPage.tsx            # Сравнение версий
│   ├── components/
│   │   ├── protocol/
│   │   │   ├── ProtocolForm.tsx    # Форма ввода параметров (FR-02)
│   │   │   ├── ProtocolViewer.tsx  # Отображение секций
│   │   │   ├── SectionEditor.tsx   # Редактирование одной секции
│   │   │   └── VersionHistory.tsx  # Список версий
│   │   ├── generation/
│   │   │   ├── GenerateButton.tsx  # Кнопка запуска + статус
│   │   │   └── GenerationStatus.tsx # Прогресс секция за секцией
│   │   ├── diff/
│   │   │   └── DiffViewer.tsx      # Diff секций (добавлено/удалено/изменено)
│   │   ├── export/
│   │   │   └── ExportPanel.tsx     # MD / HTML / DOCX кнопки
│   │   ├── consistency/
│   │   │   └── ConsistencyReport.tsx # Список противоречий + GCP hints
│   │   └── ui/
│   │       ├── Button.tsx
│   │       ├── Badge.tsx
│   │       ├── Spinner.tsx
│   │       └── Toast.tsx
│   ├── hooks/
│   │   ├── useProtocol.ts          # Fetch + state для протокола
│   │   ├── useGeneration.ts        # Polling статуса генерации
│   │   └── useExport.ts            # Trigger download
│   └── utils/
│       ├── formatVersion.ts        # v0.1 → "Версия 0.1"
│       └── sectionLabels.ts        # introduction → "Введение"
├── nginx.conf                      # Serve SPA + proxy /api → backend:8000
├── Dockerfile                      # Multi-stage: build → nginx:alpine
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.ts
```

## Ключевые страницы

| Страница | Путь | Описание |
|---|---|---|
| Список протоколов | `/` | Таблица протоколов с фазой, статусом, датой |
| Создание протокола | `/protocols/new` | Многошаговая форма ввода параметров |
| Просмотр протокола | `/protocols/:id` | Секции, кнопка генерации, экспорт |
| Сравнение версий | `/protocols/:id/diff` | Diff viewer v0.1 → v0.2 |

## Зависимости

```bash
npm create vite@latest . -- --template react-ts
npm install tailwindcss @tailwindcss/typography
npm install react-router-dom axios
npm install @tanstack/react-query
npm install react-diff-viewer-continued
npm install react-hook-form zod @hookform/resolvers
```

## Запуск

```bash
npm install
npm run dev  # http://localhost:5173
```
