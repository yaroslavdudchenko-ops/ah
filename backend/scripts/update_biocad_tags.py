"""
Патч: добавить теги "Набор открыт"/"Набор завершен" к уже импортированным BIOCAD-протоколам
и добавить 1 новый протокол BCD-281-2/MUSCAT (Рассеянный склероз, Набор открыт, Фаза II).

Источник данных: открытый реестр ct.biocad.ru (страница /ru/nozology, публичная HTML-страница).
Набор данных получен 2026-04-26.

Запуск:
    docker compose exec backend python scripts/update_biocad_tags.py
"""
import asyncio
import uuid
import datetime
from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.models.protocol import Protocol, ProtocolVersion, AuditLog

# ── Статус набора из ct.biocad.ru ────────────────────────────────────────────
# Источник: https://ct.biocad.ru/ru/nozology — публичная страница реестра КИ
# Дата парсинга: 2026-04-26

RECRUITMENT_MAP: dict[str, str] = {
    # Набор открыт
    "BCD-248-2/FLAMMINGO":    "Набор открыт",   # Множественная миелома, Фаза III
    "BCD-261-4/ULTRAMARINE":  "Набор открыт",   # Язвенный колит, Фаза II
    # Набор завершен
    "ANB-002-1/SAFRAN":       "Набор завершен",  # Гемофилия B, Фаза III
    "ANB-002-2/MAGNOLIA":     "Набор завершен",  # Гемофилия B, Фаза I
    "ANB-004-1/BLUEBELL":     "Набор завершен",  # Спинальная мышечная атрофия, Фаза III
    "BCD-057-5":              "Набор завершен",  # Ревматоидный артрит, Фаза I
    "BCD-085-16/PLANETA-KIDS":"Набор завершен",  # Бляшечный псориаз, Фаза II (pediatric)
    "BCD-089-5/LUNAR":        "Набор завершен",  # Ревматоидный артрит, Фаза I–II
    "BCD-132-4/MIRANTIBUS":   "Набор завершен",  # Рассеянный склероз, Фаза III
    "BCD-180-2/ELEFTA":       "Набор завершен",  # Аксиальный спондилоартрит, Фаза II
    "BCD-248-1":              "Набор завершен",  # Множественная миелома, Фаза I–II
    "BCD-261-2/COMANDOR":     "Набор завершен",  # Болезнь Крона, Фаза I
    "BCD-264-2/DARVIVA":      "Набор завершен",  # Множественная миелома, Фаза III
    "BCD-272-1":              "Набор завершен",  # Бронхиальная астма, Фаза I
    "BCD-281-1":              "Набор завершен",  # Рассеянный склероз, Фаза III
}

DEMO_LABEL = (
    "> FOR DEMONSTRATION PURPOSES ONLY — SYNTHETIC DATA | "
    "AI-Assisted draft based on BIOCAD public registry | "
    "Требует проверки квалифицированным медицинским специалистом."
)


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


# ── Новый протокол: BCD-281-2/MUSCAT ─────────────────────────────────────────
# Источник: ct.biocad.ru/ru/nozology — Статус набора: Набор открыт
# Нозология: Рассеянный склероз | Фаза II | Статус исследования: Активно

NEW_PROTOCOL = {
    "drug_name": "BCD-281-2/MUSCAT",
    "title": "BCD-281-2/MUSCAT — КИ при рассеянном склерозе",
    "inn": "BCD-281-2/MUSCAT (МНН уточняется)",
    "phase": "II",
    "therapeutic_area": "neurology",
    "indication": "Рассеянный склероз. Статус набора: Набор открыт.",
    "population": "Взрослые 18–60 лет с диагнозом рассеянный склероз, подтверждённым клинически и инструментально (МРТ), EDSS 0–6.5",
    "primary_endpoint": "Годовая частота рецидивов (ARR) на 96-й неделе",
    "secondary_endpoints": [
        "Изменение EDSS от baseline на неделе 96",
        "МРТ-активность (новые T2-очаги, Gd+ очаги)",
        "Время до устойчивого прогрессирования нетрудоспособности (CDP)",
        "Безопасность (НЯ ≥3 ст. по CTCAE v5.0)",
    ],
    "duration_weeks": 96,
    "dosing": "Согласно схеме исследования (в/в или п/к введение, режим дозирования определяется протоколом Фазы II)",
    "inclusion_criteria": [
        "Возраст 18–60 лет",
        "Подтверждённый диагноз рассеянного склероза (критерии McDonald 2017)",
        "EDSS 0–6.5 на скрининге",
        "≥1 рецидив за последние 12 мес или ≥1 Gd+ очаг на МРТ",
        "Подписанное информированное согласие (61-ФЗ, Приказ №353н)",
    ],
    "exclusion_criteria": [
        "Первично-прогрессирующий РС (PPMS) без обострений",
        "Активные инфекционные заболевания",
        "Беременность или лактация",
        "МРТ-противопоказания",
        "Тяжёлые психиатрические расстройства",
    ],
    "status": "generated",
    "tags": ["neurology", "Фаза II", "Активно", "Набор открыт", "BIOCAD", "Парсинг", "ct.biocad.ru"],
    "content": {
        "title_page": f"""## Титульная страница

**Полное название:** Клиническое исследование BCD-281-2/MUSCAT у пациентов с рассеянным склерозом

**Краткое название:** BCD-281-2/MUSCAT

**Спонсор:** АО «БИОКАД», г. Санкт-Петербург, Российская Федерация
**Фаза:** II
**Статус исследования:** Активно | Набор: Набор открыт
**Нозология:** Рассеянный склероз

{DEMO_LABEL}
""",
        "synopsis": """## Краткое резюме (Synopsis)

| Параметр | Значение |
|---|---|
| Препарат | BCD-281-2/MUSCAT |
| Нозология | Рассеянный склероз |
| Фаза | II — предварительная эффективность и безопасность |
| Статус | Активно |
| Набор | Набор открыт |
| Первичная КТ | Годовая частота рецидивов (ARR) на 96 неделе |
| Ключевая терминология | EDSS, ARR, МРТ (T2/Gd+), CDP, MSFC. Ссылки: ICH E6 §6.4. |

> Данные получены из открытого реестра КИ БИОКАД (ct.biocad.ru) и дополнены синтетическим контентом для демонстрационных целей.
""",
        "introduction": """## Введение и обоснование

### 1.1 Актуальность

Рассеянный склероз (РС) — хроническое аутоиммунное демиелинизирующее заболевание ЦНС, поражающее преимущественно молодых людей трудоспособного возраста. В России насчитывается ~100 000 пациентов с РС. Несмотря на широкий арсенал болезнь-модифицирующих препаратов (ПИТРС), значительная доля пациентов продолжает иметь клиническую и МРТ-активность.

### 1.2 Обоснование исследования

Исследование BCD-281-2/MUSCAT (Фаза II) направлено на оценку предварительной эффективности и безопасности в целевой популяции пациентов с рецидивирующими формами РС. Предшествующее исследование BCD-281-1 (Фаза III, набор завершён) предоставило данные по безопасности и ФК-профилю.

*[Данный раздел требует расширения квалифицированным клиническим исследователем.]*
""",
        "objectives": """## Цели и задачи исследования

### Первичная цель

Оценить эффективность BCD-281-2/MUSCAT у пациентов с рецидивирующим РС.

**Первичная конечная точка:** Годовая частота рецидивов (ARR) на 96-й неделе

### Вторичные цели

| Цель | Конечная точка | Временная точка |
|---|---|---|
| Безопасность | Частота НЯ ≥3 ст. (CTCAE v5.0) | Всё исследование |
| МРТ-активность | Новые/увеличивающиеся T2-очаги, Gd+ очаги | Нед. 24, 48, 96 |
| Нетрудоспособность | CDP (≥1 балла EDSS, подтверждённое через 12 нед) | Всё исследование |
| Качество жизни | MSFC, MSIS-29 | Baseline, нед. 48, 96 |

### Применимые стандарты

ICH E6(R2), GCP ЕАЭС (Решение ЕЭК №79), 61-ФЗ, Приказ Минздрава №353н.
""",
        "design": """## Дизайн исследования

**Фаза:** II
**Тип:** Рандомизированное, двойное слепое, плацебо-контролируемое или с активным компаратором
**Статус:** Активно | Набор открыт

### Схема исследования

```
Скрининг (4–8 нед)
    ↓
Рандомизация → BCD-281-2/MUSCAT vs компаратор/плацебо
    ↓
Период лечения (96 недель)
    ↓
Первичная оценка (ARR) — неделя 96
    ↓
Follow-up / EOT
```

### Ключевые периоды

| Период | Длительность |
|---|---|
| Скрининг | До 56 дней |
| Лечение | 96 недель |
| Follow-up | 12–24 нед после EOT |

*[Подробная схема визитов и расписание МРТ-оценок подлежат разработке.]*
""",
        "population": """## Популяция исследования

**Нозология:** Рассеянный склероз (рецидивирующие формы: RRMS, активный SPMS)

### Критерии включения

1. Подтверждённый диагноз РС (критерии McDonald 2017)
2. Возраст 18–60 лет
3. EDSS 0–6.5 на скрининге
4. ≥1 рецидив за последние 12 мес или ≥1 Gd+ очаг на МРТ
5. Адекватная функция органов (лаборатория, ЭКГ)
6. Подписанное информированное согласие (61-ФЗ, Приказ №353н)

### Критерии исключения

1. Первично-прогрессирующий РС (PPMS) без воспалительной активности
2. Беременность или лактация
3. Активные инфекционные заболевания
4. МРТ-противопоказания (металлические имплантаты, клаустрофобия)
5. Тяжёлые психиатрические расстройства
6. Участие в других КИ <30 дней

*[Окончательные критерии подлежат разработке клиническими специалистами спонсора.]*
""",
        "statistics": """## Статистический анализ

### Популяции анализа

| Популяция | Определение |
|---|---|
| ITT (Intent-To-Treat) | Все рандомизированные пациенты |
| PP (Per-Protocol) | ITT без существенных нарушений |
| Safety | Все получившие ≥1 дозу |

### Первичный анализ

**Первичная конечная точка:** ARR на 96-й неделе

Метод: отрицательная биномиальная регрессия (negative binomial model), поправка на длительность наблюдения и страты рандомизации.

### Обоснование размера выборки

*[Расчёт N подлежит определению биостатистиком на основе исторических данных по ARR и допущений о различиях между группами (обычно мощность ≥80% при α=0.05).]*
""",
    },
}


async def main():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as db:

        # ── Шаг 1: Обновить теги у существующих BIOCAD-протоколов ──────────────
        print("\n[1] Обновление тегов у существующих протоколов...")
        updated = 0
        for drug_name, rec_status in RECRUITMENT_MAP.items():
            result = await db.execute(
                select(Protocol).where(Protocol.drug_name == drug_name)
            )
            proto = result.scalar_one_or_none()
            if proto is None:
                print(f"   [warn] не найден: {drug_name}")
                continue

            current_tags = proto.tags or []
            # Убираем старые статусы набора, добавляем актуальный
            new_tags = [
                t for t in current_tags
                if t not in ("Набор открыт", "Набор завершен")
            ]
            new_tags.append(rec_status)

            # SQLAlchemy не отслеживает мутации списка JSONB — нужно явное присваивание
            from sqlalchemy.orm.attributes import flag_modified
            proto.tags = new_tags
            flag_modified(proto, "tags")

            db.add(AuditLog(
                id=_uuid(),
                entity_type="protocol",
                entity_id=proto.id,
                action="update",
                performed_by="system",
                metadata_={
                    "change": f"tags += '{rec_status}'",
                    "source": "ct.biocad.ru scrape 2026-04-26",
                    "role": "system",
                },
            ))

            print(f"   [~] {drug_name:30s} → {rec_status}")
            updated += 1

        # ── Шаг 2: Добавить BCD-281-2/MUSCAT ──────────────────────────────────
        print("\n[2] Добавление нового протокола BCD-281-2/MUSCAT...")
        existing = await db.execute(
            select(Protocol).where(Protocol.drug_name == NEW_PROTOCOL["drug_name"])
        )
        if existing.scalar_one_or_none() is not None:
            print(f"   [skip] {NEW_PROTOCOL['drug_name']} уже существует")
        else:
            pid = _uuid()
            p = Protocol(
                id=pid,
                title=NEW_PROTOCOL["title"],
                drug_name=NEW_PROTOCOL["drug_name"],
                inn=NEW_PROTOCOL["inn"],
                phase=NEW_PROTOCOL["phase"],
                therapeutic_area=NEW_PROTOCOL["therapeutic_area"],
                indication=NEW_PROTOCOL["indication"],
                population=NEW_PROTOCOL["population"],
                primary_endpoint=NEW_PROTOCOL["primary_endpoint"],
                secondary_endpoints=NEW_PROTOCOL["secondary_endpoints"],
                duration_weeks=NEW_PROTOCOL["duration_weeks"],
                dosing=NEW_PROTOCOL["dosing"],
                inclusion_criteria=NEW_PROTOCOL["inclusion_criteria"],
                exclusion_criteria=NEW_PROTOCOL["exclusion_criteria"],
                status=NEW_PROTOCOL["status"],
                tags=NEW_PROTOCOL["tags"],
                created_by="system",
            )
            db.add(p)

            db.add(AuditLog(
                id=_uuid(),
                entity_type="protocol",
                entity_id=pid,
                action="create",
                performed_by="system",
                metadata_={
                    "title": NEW_PROTOCOL["title"],
                    "role": "system",
                    "source": "ct.biocad.ru scrape 2026-04-26",
                    "biocad_slug": "bcd-281-2-muscat",
                },
            ))

            ver = ProtocolVersion(
                id=_uuid(),
                protocol_id=pid,
                version_number=1,
                content=NEW_PROTOCOL["content"],
                comment=(
                    "Импортировано из открытого реестра КИ БИОКАД (ct.biocad.ru). "
                    "Нозология: Рассеянный склероз. Набор: Набор открыт."
                ),
                compliance_score=None,
                generated_by="ct.biocad.ru-parser/synthetic-template",
            )
            db.add(ver)

            db.add(AuditLog(
                id=_uuid(),
                entity_type="protocol",
                entity_id=pid,
                action="ai_generate",
                performed_by="system",
                metadata_={
                    "model": "synthetic-template",
                    "sections": list(NEW_PROTOCOL["content"].keys()),
                    "version": 1,
                    "source": "ct.biocad.ru-parser",
                    "role": "system",
                },
            ))

            print(f"   [+] {NEW_PROTOCOL['drug_name']} | neurology | Фаза II | Набор открыт")

        await db.commit()

        # ── Финальный отчёт ────────────────────────────────────────────────────
        print(f"\n✅ Обновлено тегов: {updated}")

        print("\n📊 Итоговое распределение по статусу набора:")
        result = await db.execute(select(Protocol.drug_name, Protocol.tags, Protocol.therapeutic_area))
        rows = result.all()
        open_list, closed_list = [], []
        for drug_name, tags, area in rows:
            tags = tags or []
            if "Набор открыт" in tags:
                open_list.append((drug_name, area))
            elif "Набор завершен" in tags:
                closed_list.append((drug_name, area))

        print(f"\n  Набор открыт ({len(open_list)}):")
        for d, a in open_list:
            print(f"    {d:35s} | {a}")

        print(f"\n  Набор завершен ({len(closed_list)}):")
        for d, a in closed_list:
            print(f"    {d:35s} | {a}")

        total = await db.execute(select(Protocol))
        total_count = len(total.scalars().all())
        print(f"\n  Всего протоколов в БД: {total_count}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
