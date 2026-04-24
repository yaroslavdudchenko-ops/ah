from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


class ProtocolCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=500)
    drug_name: str = Field(..., min_length=2, max_length=200)
    inn: str = Field(..., min_length=2, max_length=200)
    phase: str = Field(..., pattern="^(I|II|III|IV)$")
    therapeutic_area: str = Field(..., min_length=2, max_length=200)
    indication: str = Field(..., min_length=10)
    population: str = Field(..., min_length=10, max_length=1000)
    primary_endpoint: str = Field(..., min_length=3)
    secondary_endpoints: List[str] = Field(default_factory=list)
    duration_weeks: int = Field(..., ge=1, le=520)
    dosing: str = Field(..., min_length=5)
    inclusion_criteria: List[str] = Field(default_factory=list)
    exclusion_criteria: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    template_id: Optional[str] = None

    @field_validator("phase")
    @classmethod
    def validate_phase(cls, v: str) -> str:
        if v not in ("I", "II", "III", "IV"):
            raise ValueError("phase must be I, II, III, or IV")
        return v


class ProtocolUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=500)
    drug_name: Optional[str] = Field(None, min_length=2, max_length=200)
    inn: Optional[str] = Field(None, min_length=2, max_length=200)
    phase: Optional[str] = Field(None, pattern="^(I|II|III|IV)$")
    therapeutic_area: Optional[str] = None
    indication: Optional[str] = None
    population: Optional[str] = None
    primary_endpoint: Optional[str] = None
    secondary_endpoints: Optional[List[str]] = None
    duration_weeks: Optional[int] = Field(None, ge=1, le=520)
    dosing: Optional[str] = None
    inclusion_criteria: Optional[List[str]] = None
    exclusion_criteria: Optional[List[str]] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None


class ProtocolResponse(BaseModel):
    id: str
    title: str
    drug_name: str
    inn: str
    phase: str
    therapeutic_area: str
    indication: str
    population: str
    primary_endpoint: str
    secondary_endpoints: List[str]
    duration_weeks: int
    dosing: str
    inclusion_criteria: List[str]
    exclusion_criteria: List[str]
    status: str
    created_by: Optional[str] = None
    tags: List[str] = []
    template_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProtocolListItem(BaseModel):
    id: str
    title: str
    drug_name: str
    phase: str
    therapeutic_area: str
    status: str
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VersionResponse(BaseModel):
    id: str
    protocol_id: str
    version_number: int
    content: dict
    comment: Optional[str]
    compliance_score: Optional[int]
    generated_by: str
    is_archived: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class OpenIssueResponse(BaseModel):
    id: str
    protocol_id: str
    section: str
    issue_type: str
    severity: str
    description: str
    suggestion: Optional[str]
    resolved: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TemplateResponse(BaseModel):
    id: str
    name: str
    phase: str
    design_type: str
    description: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class ErrorResponse(BaseModel):
    error: dict


def error_body(code: str, message: str, details: list | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or []}}
