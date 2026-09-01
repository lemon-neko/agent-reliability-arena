"""Stable contracts for HTTP Agent risk assessments and public attestations."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, model_validator

from arena.domain.models import ToolFixture, TraceEvent, utc_now


class RiskCategory(StrEnum):
    PROMPT_INJECTION = "prompt_injection"
    DATA_EXPOSURE = "data_exposure"
    AUTHORIZATION = "authorization"
    HUMAN_CONTROL = "human_control"
    TOOL_SAFETY = "tool_safety"
    GROUNDING = "grounding"
    RESILIENCE = "resilience"
    RESOURCE_CONTROL = "resource_control"


class RiskDimension(StrEnum):
    SECURITY_PRIVACY = "security_privacy"
    AUTHORIZATION_CONTROL = "authorization_control"
    SIDE_EFFECT_SAFETY = "side_effect_safety"
    CORRECTNESS_GROUNDING = "correctness_grounding"
    RESILIENCE_IDEMPOTENCY = "resilience_idempotency"
    EFFICIENCY_RESOURCES = "efficiency_resources"


class FindingSeverity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AssessmentProfile(StrEnum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class AssessmentStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RiskRunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"


class AgentNetworkScope(StrEnum):
    LOCAL = "local"
    PUBLIC = "public"


class Verdict(StrEnum):
    READY = "ready"
    CONDITIONAL = "conditional"
    NOT_RECOMMENDED = "not_recommended"


class VerificationLevel(StrEnum):
    SELF_REPORTED = "self_reported"
    REPRODUCIBLE = "reproducible"
    VERIFIED = "verified"


class AgentTarget(BaseModel):
    """A persisted Agent endpoint. Secret values are referenced, never stored."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    endpoint_url: str = Field(min_length=8, max_length=500)
    protocol_version: Literal["ara-step/1"] = "ara-step/1"
    network_scope: AgentNetworkScope = AgentNetworkScope.LOCAL
    auth_header_name: str | None = Field(default=None, max_length=100)
    auth_env_var: str | None = Field(default=None, pattern=r"^[A-Z][A-Z0-9_]{1,80}$")
    repository_url: str | None = Field(default=None, max_length=500)
    version: str = Field(default="unversioned", min_length=1, max_length=80)
    capabilities: list[str] = Field(default_factory=list, max_length=20)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_endpoint(self) -> AgentTarget:
        parsed = urlparse(self.endpoint_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("endpoint_url must be an absolute HTTP(S) URL")
        if parsed.username or parsed.password:
            raise ValueError("endpoint_url must not contain credentials")
        if self.network_scope == AgentNetworkScope.PUBLIC and parsed.scheme != "https":
            raise ValueError("public Agent endpoints must use HTTPS")
        if bool(self.auth_header_name) != bool(self.auth_env_var):
            raise ValueError("auth_header_name and auth_env_var must be provided together")
        return self


class RiskOracle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer_contains: list[str] = Field(default_factory=list)
    answer_excludes: list[str] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)
    required_arguments: dict[str, dict[str, Any]] = Field(default_factory=dict)
    prohibited_tools: list[str] = Field(default_factory=list)
    approval_before_tools: list[str] = Field(default_factory=list)
    max_tool_calls: int = Field(default=6, ge=0, le=30)


class RiskCase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{2,80}$")
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    title: str
    description: str
    category: RiskCategory
    dimension: RiskDimension
    severity: FindingSeverity
    tags: list[str] = Field(default_factory=list, max_length=12)
    prompt: str
    fixtures: ToolFixture = Field(default_factory=ToolFixture)
    allowed_tools: list[str] = Field(default_factory=list)
    oracle: RiskOracle
    remediation: str
    variant_axes: list[str] = Field(default_factory=list)
    max_steps: int = Field(default=8, ge=1, le=30)
    timeout_seconds: float = Field(default=30, gt=0, le=120)
    simulated_approval: bool = False


class RiskTestSpec(BaseModel):
    """One materialized case variant sent to the runner."""

    case: RiskCase
    variant_id: str
    mutation: str = "baseline"
    seed: int = Field(ge=0)
    prompt: str


class Assessment(BaseModel):
    id: str
    target_id: str
    name: str = Field(min_length=1, max_length=200)
    profile: AssessmentProfile
    suite_version: str = "tool-agent-baseline/1.0.0"
    seed: int = Field(default=20260901, ge=0)
    repetitions: int = Field(ge=1, le=3)
    concurrency: int = Field(default=4, ge=1, le=8)
    status: AssessmentStatus = AssessmentStatus.QUEUED
    total_runs: int = Field(default=0, ge=0)
    completed_runs: int = Field(default=0, ge=0)
    failed_runs: int = Field(default=0, ge=0)
    cancel_requested: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    started_at: datetime | None = None
    completed_at: datetime | None = None


class RiskTestRun(BaseModel):
    id: str
    assessment_id: str
    target_id: str
    case_id: str
    case_version: str
    variant_id: str
    mutation: str
    seed: int = Field(ge=0)
    repetition: int = Field(ge=1, le=3)
    status: RiskRunStatus = RiskRunStatus.QUEUED
    answer: str = ""
    error: str = ""
    tool_calls: int = Field(default=0, ge=0)
    duration_ms: float = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=utc_now)
    started_at: datetime | None = None
    completed_at: datetime | None = None


class Finding(BaseModel):
    id: str
    assessment_id: str
    test_run_id: str
    case_id: str
    category: RiskCategory
    dimension: RiskDimension
    severity: FindingSeverity
    confidence: Literal["deterministic"] = "deterministic"
    title: str
    summary: str
    expected: str
    observed: str
    evidence_event_ids: list[str] = Field(default_factory=list)
    reproduction: str
    remediation: str
    occurrences: int = Field(default=1, ge=1)


class RiskDimensionScores(BaseModel):
    security_privacy: float = Field(ge=0, le=25)
    authorization_control: float = Field(ge=0, le=20)
    side_effect_safety: float = Field(ge=0, le=15)
    correctness_grounding: float = Field(ge=0, le=15)
    resilience_idempotency: float = Field(ge=0, le=15)
    efficiency_resources: float = Field(ge=0, le=10)

    @property
    def total(self) -> float:
        return round(sum(self.model_dump().values()), 2)


class RiskReport(BaseModel):
    schema_version: Literal[1] = 1
    assessment_id: str
    target_id: str
    target_name: str
    target_version: str
    repository_url: str | None = None
    suite_version: str
    profile: AssessmentProfile
    generated_at: datetime = Field(default_factory=utc_now)
    raw_score: float = Field(ge=0, le=100)
    final_score: float = Field(ge=0, le=100)
    grade: Literal["A", "B", "C", "D", "E"]
    verdict: Verdict
    gate_reasons: list[str] = Field(default_factory=list)
    dimension_scores: RiskDimensionScores
    coverage: dict[str, Any]
    finding_counts: dict[str, int]
    findings: list[Finding]
    limitations: list[str]


class Attestation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    id: str
    agent_name: str
    agent_version: str
    repository_url: str
    suite_version: str
    profile: Literal[AssessmentProfile.STANDARD] = AssessmentProfile.STANDARD
    score: float = Field(ge=0, le=100)
    grade: Literal["A", "B", "C", "D", "E"]
    verdict: Verdict
    finding_counts: dict[str, int]
    volatility_percent: float = Field(ge=0, le=100)
    report_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    runner_version: str = "0.2.0"
    verification: VerificationLevel = VerificationLevel.SELF_REPORTED
    evaluated_at: datetime
    submitted_at: datetime = Field(default_factory=utc_now)


class RiskRunOutcome(BaseModel):
    run: RiskTestRun
    events: list[TraceEvent]
    findings: list[Finding]
