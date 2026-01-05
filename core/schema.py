from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class Location(BaseModel):
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None

class WorkAuthorization(BaseModel):
    us: Optional[str] = None
    uk: Optional[str] = None
    eu: Optional[str] = None
    other: Optional[str] = None

class Candidate(BaseModel):
    full_name: Optional[str] = None
    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)
    location_current: Location = Field(default_factory=Location)
    citizenship: List[str] = Field(default_factory=list)
    work_authorization: WorkAuthorization = Field(default_factory=WorkAuthorization)
    linkedin: Optional[str] = None
    github: Optional[str] = None
    languages_spoken: List[str] = Field(default_factory=list)

class TargetFit(BaseModel):
    geographic_markets: List[str] = Field(default_factory=list)      # US/Europe/APAC
    investment_approaches: List[str] = Field(default_factory=list)   # Fundamental/Systematic
    asset_classes: List[str] = Field(default_factory=list)           # Equity/Credit/Macro/...
    sectors: List[str] = Field(default_factory=list)                 # Technology/Healthcare/...
    roles: List[str] = Field(default_factory=list)                   # Junior Analyst/Quant Research/...

class Summary(BaseModel):
    years_experience: Optional[float] = None
    current_title: Optional[str] = None
    current_employer: Optional[str] = None
    education_level: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)

class Skills(BaseModel):
    programming: List[str] = Field(default_factory=list)
    data: List[str] = Field(default_factory=list)
    ml: List[str] = Field(default_factory=list)
    finance: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    other: List[str] = Field(default_factory=list)

class ParsedResume(BaseModel):
    resume_id: str
    candidate: Candidate = Field(default_factory=Candidate)

    target_fit: TargetFit = Field(default_factory=TargetFit)
    summary: Summary = Field(default_factory=Summary)
    education: List[Dict[str, Any]] = Field(default_factory=list)
    experience: List[Dict[str, Any]] = Field(default_factory=list)
    skills: Skills = Field(default_factory=Skills)
    certifications: List[Dict[str, Any]] = Field(default_factory=list)

    metadata: Dict[str, Any] = Field(default_factory=dict)
    evidence: Dict[str, Any] = Field(default_factory=dict)

def json_schema() -> Dict[str, Any]:
    """
    Returns a JSON schema that LLM providers can use for constrained output.
    """
    return ParsedResume.model_json_schema()
