from pydantic import BaseModel
from typing import Optional, List


class GenerateRequest(BaseModel):
    sections: Optional[List[str]] = None  # None = generate all 7 MVP sections
    comment: Optional[str] = None
    custom_prompt: Optional[str] = None  # User-provided additional instructions for AI


class GenerateStatus(BaseModel):
    task_id: str
    status: str  # pending | running | completed | failed
    progress: int  # 0-100
    sections_done: List[str]
    sections_total: List[str]
    version_id: Optional[str] = None
    error: Optional[str] = None


class CheckRequest(BaseModel):
    version_id: Optional[str] = None  # None = latest version


class IssueItem(BaseModel):
    type: str
    severity: str
    section: str
    description: str
    suggestion: str


class GcpHint(BaseModel):
    category: str
    priority: str
    recommendation: str
    gcp_reference: str


class CheckResponse(BaseModel):
    compliance_score: int
    rf_compliance_score: int
    issues: List[IssueItem]
    gcp_hints: List[GcpHint]
    summary: str
    rf_summary: str


# P2 stubs — структуры заготовлены для будущей реализации
class DiffSection(BaseModel):
    section: str
    old_text: Optional[str]
    new_text: Optional[str]
    diff_html: str


class DiffResponse(BaseModel):
    protocol_id: str
    version_from: int
    version_to: int
    sections: List[DiffSection]
