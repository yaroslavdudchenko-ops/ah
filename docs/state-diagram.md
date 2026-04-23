# A-003: State Diagram

**Version:** 1.0.0 | **Date:** 2026-04-23 | **Status:** Draft  
**Artifact ID:** A-003

---

## Жизненный цикл протокола (Protocol)

```mermaid
stateDiagram-v2
  [*] --> draft : CreateProtocol

  draft --> generating : StartGeneration
  draft --> draft : UpdateParameters

  generating --> generated : AllSectionsGenerated
  generating --> draft : GenerationFailed

  generated --> in_review : SubmitForReview
  generated --> generating : RegenerateSection

  in_review --> generated : ReviewerReturns
  in_review --> final : ReviewerApproves

  final --> [*]

  note right of draft
    Параметры введены,
    шаблон выбран,
    генерация не начата
  end note

  note right of generating
    AI генерирует секции.
    Прогресс отображается
    в реальном времени (polling)
  end note

  note right of generated
    Черновик готов.
    Доступны: редактирование,
    проверка, экспорт, версионирование
  end note

  note right of in_review
    Передан медицинскому
    ревьюеру. Редактирование
    заблокировано
  end note

  note right of final
    Финальная версия.
    Immutable. Только экспорт
  end note
```

---

## Жизненный цикл версии (ProtocolVersion)

```mermaid
stateDiagram-v2
  [*] --> created : VersionCreated

  created --> current : SetAsCurrent
  created --> archived : NewerVersionCreated

  current --> archived : NewerVersionCreated

  archived --> [*]

  note right of created
    v0.1, v0.2, ...
    Снапшот content JSONB
    на момент сохранения
  end note

  note right of current
    Отображается по умолчанию.
    Только одна версия current
    в каждый момент времени
  end note

  note right of archived
    Доступна для просмотра
    и diff. Не изменяется
    (immutable)
  end note
```

---

## Жизненный цикл задачи генерации (GenerationTask)

```mermaid
stateDiagram-v2
  [*] --> pending : TaskCreated

  pending --> running : WorkerPickedUp

  running --> section_done : SectionGenerated
  section_done --> running : NextSection
  section_done --> completed : AllSectionsDone

  running --> failed : AIError / Timeout

  failed --> pending : Retry (max 3)
  failed --> [*] : MaxRetriesExceeded

  completed --> [*]

  note right of pending
    task_id создан,
    клиент начинает polling
    GET /generate/{task_id}
  end note

  note right of running
    Текущая секция в обработке.
    status = "running",
    current_section = "design"
  end note

  note right of completed
    version_id возвращается
    клиенту. Polling завершён
  end note
```

---

## Жизненный цикл открытого вопроса (OpenIssue)

```mermaid
stateDiagram-v2
  [*] --> open : IssueFound

  open --> resolved : IssueAddressed
  open --> wontfix : IssueIgnored

  resolved --> [*]
  wontfix --> [*]
```
