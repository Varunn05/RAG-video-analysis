from typing import Literal

from pydantic import BaseModel, Field


Verdict = Literal["TRUE", "FALSE", "MISLEADING", "UNVERIFIABLE", "ERROR"]
Confidence = Literal["HIGH", "MEDIUM", "LOW", "N/A"]


class AnalysisRequest(BaseModel):
    youtube_url: str = Field(min_length=11, max_length=2_048)


class Source(BaseModel):
    title: str
    url: str
    snippet: str


class FactCheck(BaseModel):
    timestamp: str
    claim: str
    status: Verdict
    explanation: str
    confidence: Confidence
    source_url: str | None = None
    sources: list[Source] = Field(default_factory=list)


class Summary(BaseModel):
    total_claims: int
    true: int
    false: int
    misleading: int
    unverifiable: int
    errors: int


class AnalysisReport(BaseModel):
    video_id: str
    summary: Summary
    claims: list[FactCheck]
