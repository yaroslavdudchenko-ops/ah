import uuid
import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phase: Mapped[str] = mapped_column(String(10), nullable=False)
    design_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    section_prompts: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    protocols: Mapped[list["Protocol"]] = relationship("Protocol", back_populates="template")


class Protocol(Base):
    __tablename__ = "protocols"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    drug_name: Mapped[str] = mapped_column(String(200), nullable=False)
    inn: Mapped[str] = mapped_column(String(200), nullable=False)
    phase: Mapped[str] = mapped_column(String(10), nullable=False)
    therapeutic_area: Mapped[str] = mapped_column(String(200), nullable=False)
    indication: Mapped[str] = mapped_column(Text, nullable=False)
    population: Mapped[str] = mapped_column(Text, nullable=False)
    primary_endpoint: Mapped[str] = mapped_column(Text, nullable=False)
    secondary_endpoints: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    duration_weeks: Mapped[int] = mapped_column(Integer, nullable=False)
    dosing: Mapped[str] = mapped_column(Text, nullable=False)
    inclusion_criteria: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    exclusion_criteria: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="draft")
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    template_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("templates.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    template: Mapped[Optional["Template"]] = relationship("Template", back_populates="protocols")
    versions: Mapped[list["ProtocolVersion"]] = relationship(
        "ProtocolVersion",
        back_populates="protocol",
        order_by="ProtocolVersion.version_number",
        cascade="all, delete-orphan",
    )
    open_issues: Mapped[list["OpenIssue"]] = relationship(
        "OpenIssue", back_populates="protocol", cascade="all, delete-orphan"
    )


class ProtocolVersion(Base):
    __tablename__ = "protocol_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    protocol_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("protocols.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    compliance_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    generated_by: Mapped[str] = mapped_column(
        String(100), nullable=False, default="InHouse/Qwen3.5-122B"
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    protocol: Mapped["Protocol"] = relationship("Protocol", back_populates="versions")


class OpenIssue(Base):
    __tablename__ = "open_issues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    protocol_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("protocols.id", ondelete="CASCADE"), nullable=False
    )
    section: Mapped[str] = mapped_column(String(100), nullable=False)
    issue_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    suggestion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    protocol: Mapped["Protocol"] = relationship("Protocol", back_populates="open_issues")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    performed_by: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
