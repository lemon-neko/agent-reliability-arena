"""Stable domain types shared by the runner, API, persistence, and evaluators."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


class ScenarioFamily(StrEnum):
    FILE = "file"
    SQL = "sql"
    RAG = "rag"
    APPROVAL = "approval"
    SECURITY = "security"


class ToolFixture(BaseModel):
    model_config = ConfigDict(extra="forbid")

    files: dict[str, str] = Field(default_factory=dict)
    documents: dict[str, str] = Field(default_factory=dict)
    sql: list[str] = Field(default_factory=list)
    secrets: dict[str, str] = Field(default_factory=dict)


class ToolExpectation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    result_contains: str | None = None
    requires_approval: bool = False


class ScenarioSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[1] = 1
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{2,80}$")
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    title: str
    description: str
    family: ScenarioFamily
    tags: list[str] = Field(default_factory=list, max_length=12)
    prompt: str
    fixtures: ToolFixture = Field(default_factory=ToolFixture)
    allowed_tools: list[str] = Field(min_length=1)
    expected: list[ToolExpectation] = Field(default_factory=list)
    expected_answer_contains: list[str] = Field(default_factory=list)
    forbidden_output: list[str] = Field(default_factory=list)
    max_steps: int = Field(default=8, ge=1, le=30)
    timeout_seconds: float = Field(default=30, gt=0, le=300)
    scripted_actions: list[ToolExpectation] = Field(default_factory=list)
    scripted_answer: str = ""

    @model_validator(mode="after")
    def validate_tools(self) -> ScenarioSpec:
        allowed = set(self.allowed_tools)
        used = {item.tool for item in self.expected + self.scripted_actions}
        if not used <= allowed:
            raise ValueError(f"scenario references unavailable tools: {sorted(used - allowed)}")
        return self


class AgentProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    runtime: Literal["minimal", "langgraph"]
    model: str
    base_url: str = "fake://deterministic"
    temperature: float = Field(default=0, ge=0, le=2)
    max_steps: int = Field(default=10, ge=1, le=50)
    timeout_seconds: float = Field(default=60, gt=0, le=600)
    input_cost_per_million: float = Field(default=0, ge=0)
    output_cost_per_million: float = Field(default=0, ge=0)


class TournamentStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


class Tournament(BaseModel):
    id: str
    name: str
    agent_ids: list[str]
    scenario_ids: list[str]
    repetitions: int = Field(default=3, ge=1, le=20)
    status: TournamentStatus = TournamentStatus.QUEUED
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Run(BaseModel):
    id: str
    tournament_id: str
    scenario_id: str
    scenario_version: str
    agent_id: str
    repetition: int = Field(ge=1)
    status: RunStatus = RunStatus.QUEUED
    answer: str = ""
    error: str = ""
    created_at: datetime = Field(default_factory=utc_now)
    started_at: datetime | None = None
    completed_at: datetime | None = None


class TraceKind(StrEnum):
    RUN = "run"
    MODEL = "model"
    TOOL = "tool"
    APPROVAL = "approval"
    RETRY = "retry"
    ERROR = "error"
    EVALUATION = "evaluation"


class TraceEvent(BaseModel):
    id: str
    run_id: str
    sequence: int = Field(ge=1)
    kind: TraceKind
    name: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    duration_ms: float | None = Field(default=None, ge=0)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0, ge=0)


class ScoreBreakdown(BaseModel):
    correctness: float = Field(ge=0, le=50)
    safety: float = Field(ge=0, le=25)
    resilience: float = Field(ge=0, le=15)
    efficiency: float = Field(ge=0, le=10)

    @property
    def total(self) -> float:
        return round(self.correctness + self.safety + self.resilience + self.efficiency, 2)


class Evaluation(BaseModel):
    run_id: str
    score: ScoreBreakdown
    passed: bool
    failure_class: str | None = None
    latency_ms: float = Field(default=0, ge=0)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    estimated_cost_usd: float = Field(default=0, ge=0)
    judge_score: float | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ApprovalRequest(BaseModel):
    id: str
    run_id: str
    tool_name: str
    arguments: dict[str, Any]
    reason: str
    status: Literal["pending", "approved", "rejected"] = "pending"
    created_at: datetime = Field(default_factory=utc_now)
    decided_at: datetime | None = None


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ModelTurn(BaseModel):
    content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0
