import io
import logging
import mistune
from typing import Literal
from app.models.protocol import Protocol, ProtocolVersion

logger = logging.getLogger(__name__)

SECTION_TITLES = {
    "title_page": "Title Page / Титульная страница",
    "synopsis": "Synopsis / Краткое резюме",
    "introduction": "Introduction & Background / Введение",
    "objectives": "Study Objectives / Цели исследования",
    "design": "Study Design / Дизайн исследования",
    "population": "Study Population / Популяция",
    "treatment": "Study Treatment / Лечение",
    "efficacy": "Efficacy Assessments / Оценка эффективности",
    "safety": "Safety Assessments / Оценка безопасности",
    "statistics": "Statistical Analysis / Статистический анализ",
    "ethics": "Ethics / Этические аспекты",
    "references": "References / Список литературы",
}

ExportFormat = Literal["md", "html", "docx"]


def _build_markdown(protocol: Protocol, version: ProtocolVersion) -> str:
    content = version.content or {}
    lines = [
        f"# {protocol.title}",
        f"> **FOR REVIEW ONLY — SYNTHETIC DATA** | Версия: {version.version_number} | Модель: {version.generated_by}",
        "",
        "## Параметры исследования",
        f"- **Препарат:** {protocol.drug_name} ({protocol.inn})",
        f"- **Фаза:** {protocol.phase}",
        f"- **Терапевтическая область:** {protocol.therapeutic_area}",
        f"- **Индикация:** {protocol.indication}",
        f"- **Первичная конечная точка:** {protocol.primary_endpoint}",
        f"- **Длительность:** {protocol.duration_weeks} недель",
        f"- **Дозирование:** {protocol.dosing}",
        "",
    ]
    for section_key, text in content.items():
        title = SECTION_TITLES.get(section_key, section_key.replace("_", " ").title())
        lines.append(f"## {title}")
        lines.append(text)
        lines.append("")

    open_issues = getattr(protocol, "open_issues", [])
    if open_issues:
        lines.append("## Список открытых вопросов")
        for issue in open_issues:
            lines.append(f"- **[{issue.severity.upper()}]** {issue.section}: {issue.description}")
        lines.append("")

    return "\n".join(lines)


def export_markdown(protocol: Protocol, version: ProtocolVersion) -> bytes:
    return _build_markdown(protocol, version).encode("utf-8")


def export_html(protocol: Protocol, version: ProtocolVersion) -> bytes:
    md_text = _build_markdown(protocol, version)
    renderer = mistune.create_markdown()
    body = renderer(md_text)
    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>{protocol.title}</title>
<style>
  body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; line-height: 1.6; }}
  h1 {{ border-bottom: 2px solid #333; padding-bottom: 8px; }}
  h2 {{ border-bottom: 1px solid #ccc; margin-top: 32px; }}
  blockquote {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 8px 16px; margin: 0; }}
  table {{ border-collapse: collapse; width: 100%; }}
  td, th {{ border: 1px solid #ddd; padding: 8px; }}
</style>
</head>
<body>
{body}
</body>
</html>"""
    return html.encode("utf-8")


def export_docx(protocol: Protocol, version: ProtocolVersion) -> bytes:
    """P2 feature — DOCX export via python-docx."""
    try:
        from docx import Document
        from docx.shared import Pt

        doc = Document()
        doc.add_heading(protocol.title, level=0)
        doc.add_paragraph(
            "FOR REVIEW ONLY — SYNTHETIC DATA | "
            f"Version: {version.version_number} | Model: {version.generated_by}"
        )

        doc.add_heading("Параметры исследования", level=1)
        params = [
            f"Препарат: {protocol.drug_name} ({protocol.inn})",
            f"Фаза: {protocol.phase}",
            f"Терапевтическая область: {protocol.therapeutic_area}",
            f"Индикация: {protocol.indication}",
            f"Первичная конечная точка: {protocol.primary_endpoint}",
            f"Длительность: {protocol.duration_weeks} недель",
            f"Дозирование: {protocol.dosing}",
        ]
        for p in params:
            doc.add_paragraph(p, style="List Bullet")

        content = version.content or {}
        for section_key, text in content.items():
            title = SECTION_TITLES.get(section_key, section_key.replace("_", " ").title())
            doc.add_heading(title, level=1)
            for para in text.split("\n\n"):
                para = para.strip()
                if para.startswith("## ") or para.startswith("### "):
                    doc.add_heading(para.lstrip("#").strip(), level=2)
                elif para:
                    doc.add_paragraph(para)

        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()
    except Exception as exc:
        logger.error("docx_export_failed", extra={"error": str(exc)})
        raise


CONTENT_TYPES: dict[ExportFormat, str] = {
    "md": "text/markdown; charset=utf-8",
    "html": "text/html; charset=utf-8",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

FILENAMES: dict[ExportFormat, str] = {
    "md": "protocol.md",
    "html": "protocol.html",
    "docx": "protocol.docx",
}
