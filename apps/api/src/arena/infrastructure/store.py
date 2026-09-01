"""SQLAlchemy persistence for arena runs and private risk assessments."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from arena.domain.models import (
    AgentProfile,
    ApprovalRequest,
    Evaluation,
    Run,
    RunStatus,
    Tournament,
    TournamentStatus,
    TraceEvent,
)
from arena.domain.risk import (
    AgentTarget,
    Assessment,
    AssessmentStatus,
    Attestation,
    Finding,
    RiskReport,
    RiskRunOutcome,
    RiskTestRun,
)


class Base(DeclarativeBase):
    pass


class TournamentRecord(Base):
    __tablename__ = "tournaments"
    __table_args__ = (UniqueConstraint("idempotency_key"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String(160))
    name: Mapped[str] = mapped_column(String(200))
    agent_ids: Mapped[list[str]] = mapped_column(JSON)
    scenario_ids: Mapped[list[str]] = mapped_column(JSON)
    repetitions: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RunRecord(Base):
    __tablename__ = "runs"
    __table_args__ = (UniqueConstraint("tournament_id", "scenario_id", "agent_id", "repetition"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tournament_id: Mapped[str] = mapped_column(
        ForeignKey("tournaments.id", ondelete="CASCADE"), index=True
    )
    scenario_id: Mapped[str] = mapped_column(String(100))
    scenario_version: Mapped[str] = mapped_column(String(30))
    agent_id: Mapped[str] = mapped_column(String(100))
    repetition: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(40), index=True)
    answer: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TraceRecord(Base):
    __tablename__ = "trace_events"
    __table_args__ = (UniqueConstraint("run_id", "sequence"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(120))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_usd: Mapped[float] = mapped_column(Float, default=0)


class EvaluationRecord(Base):
    __tablename__ = "evaluations"
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), primary_key=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class ApprovalRecord(Base):
    __tablename__ = "approvals"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), index=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class AgentRecord(Base):
    __tablename__ = "agent_profiles"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class FailureEmbeddingRecord(Base):
    """Optional pgvector surface for later trace/failure clustering."""

    __tablename__ = "failure_embeddings"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("runs.id", ondelete="CASCADE"),
        index=True,
    )
    classification: Mapped[str] = mapped_column(String(120))
    embedding: Mapped[list[float]] = mapped_column(Vector(16))


class AgentTargetRecord(Base):
    __tablename__ = "agent_targets"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class AssessmentRecord(Base):
    __tablename__ = "assessments"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    target_id: Mapped[str] = mapped_column(
        ForeignKey("agent_targets.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(40), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class RiskTestRunRecord(Base):
    __tablename__ = "risk_test_runs"
    __table_args__ = (
        UniqueConstraint("assessment_id", "variant_id", "repetition"),
    )
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    assessment_id: Mapped[str] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), index=True
    )
    variant_id: Mapped[str] = mapped_column(String(120))
    repetition: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(40), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class RiskTraceRecord(Base):
    __tablename__ = "risk_trace_events"
    __table_args__ = (UniqueConstraint("test_run_id", "sequence"),)
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    test_run_id: Mapped[str] = mapped_column(
        ForeignKey("risk_test_runs.id", ondelete="CASCADE"), index=True
    )
    sequence: Mapped[int] = mapped_column(Integer)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class FindingRecord(Base):
    __tablename__ = "risk_findings"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    assessment_id: Mapped[str] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), index=True
    )
    test_run_id: Mapped[str] = mapped_column(
        ForeignKey("risk_test_runs.id", ondelete="CASCADE"), index=True
    )
    severity: Mapped[str] = mapped_column(String(20), index=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class RiskReportRecord(Base):
    __tablename__ = "risk_reports"
    assessment_id: Mapped[str] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), primary_key=True
    )
    data: Mapped[dict[str, Any]] = mapped_column(JSON)
    html: Mapped[str] = mapped_column(Text)


class AttestationRecord(Base):
    __tablename__ = "attestations"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    assessment_id: Mapped[str] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), index=True
    )
    data: Mapped[dict[str, Any]] = mapped_column(JSON)


class ArenaStore:
    def __init__(self, database_url: str) -> None:
        kwargs = {"future": True}
        if database_url.startswith("sqlite"):
            path = database_url.split("///", 1)[-1]
            if path != ":memory:":
                Path(path).parent.mkdir(parents=True, exist_ok=True)
            kwargs["connect_args"] = {"check_same_thread": False}
        self.engine = create_engine(database_url, **kwargs)
        Base.metadata.create_all(self.engine)

    def upsert_agents(self, profiles: tuple[AgentProfile, ...]) -> None:
        with Session(self.engine) as session, session.begin():
            for profile in profiles:
                row = session.get(AgentRecord, profile.id)
                data = profile.model_dump(mode="json")
                if row:
                    row.data = data
                else:
                    session.add(AgentRecord(id=profile.id, data=data))

    def agents(self) -> tuple[AgentProfile, ...]:
        with Session(self.engine) as session:
            rows = session.scalars(select(AgentRecord).order_by(AgentRecord.id)).all()
        return tuple(AgentProfile.model_validate(row.data) for row in rows)

    def agent(self, agent_id: str) -> AgentProfile | None:
        with Session(self.engine) as session:
            row = session.get(AgentRecord, agent_id)
        return AgentProfile.model_validate(row.data) if row else None

    def save_agent_target(self, target: AgentTarget) -> AgentTarget:
        with Session(self.engine) as session, session.begin():
            row = session.get(AgentTargetRecord, target.id)
            data = target.model_dump(mode="json")
            if row:
                row.data = data
            else:
                session.add(
                    AgentTargetRecord(id=target.id, created_at=target.created_at, data=data)
                )
        return target

    def agent_targets(self) -> tuple[AgentTarget, ...]:
        with Session(self.engine) as session:
            rows = session.scalars(
                select(AgentTargetRecord).order_by(AgentTargetRecord.created_at.desc())
            ).all()
        return tuple(AgentTarget.model_validate(row.data) for row in rows)

    def agent_target(self, target_id: str) -> AgentTarget | None:
        with Session(self.engine) as session:
            row = session.get(AgentTargetRecord, target_id)
        return AgentTarget.model_validate(row.data) if row else None

    def create_assessment(
        self, assessment: Assessment, runs: tuple[RiskTestRun, ...]
    ) -> Assessment:
        with Session(self.engine) as session, session.begin():
            session.add(
                AssessmentRecord(
                    id=assessment.id,
                    target_id=assessment.target_id,
                    status=assessment.status.value,
                    created_at=assessment.created_at,
                    data=assessment.model_dump(mode="json"),
                )
            )
            session.add_all(
                [
                    RiskTestRunRecord(
                        id=run.id,
                        assessment_id=run.assessment_id,
                        variant_id=run.variant_id,
                        repetition=run.repetition,
                        status=run.status.value,
                        created_at=run.created_at,
                        data=run.model_dump(mode="json"),
                    )
                    for run in runs
                ]
            )
        return assessment

    def save_assessment(self, assessment: Assessment) -> Assessment:
        with Session(self.engine) as session, session.begin():
            row = session.get(AssessmentRecord, assessment.id)
            if row is None:
                raise KeyError(assessment.id)
            row.status = assessment.status.value
            row.data = assessment.model_dump(mode="json")
        return assessment

    def assessments(self, target_id: str | None = None) -> tuple[Assessment, ...]:
        query = select(AssessmentRecord)
        if target_id:
            query = query.where(AssessmentRecord.target_id == target_id)
        query = query.order_by(AssessmentRecord.created_at.desc())
        with Session(self.engine) as session:
            rows = session.scalars(query).all()
        return tuple(Assessment.model_validate(row.data) for row in rows)

    def assessment(self, assessment_id: str) -> Assessment | None:
        with Session(self.engine) as session:
            row = session.get(AssessmentRecord, assessment_id)
        return Assessment.model_validate(row.data) if row else None

    def request_assessment_cancel(self, assessment_id: str) -> Assessment:
        assessment = self.assessment(assessment_id)
        if assessment is None:
            raise KeyError(assessment_id)
        if assessment.status in {AssessmentStatus.COMPLETED, AssessmentStatus.CANCELLED}:
            return assessment
        return self.save_assessment(assessment.model_copy(update={"cancel_requested": True}))

    def risk_test_runs(self, assessment_id: str) -> tuple[RiskTestRun, ...]:
        with Session(self.engine) as session:
            rows = session.scalars(
                select(RiskTestRunRecord)
                .where(RiskTestRunRecord.assessment_id == assessment_id)
                .order_by(RiskTestRunRecord.created_at, RiskTestRunRecord.id)
            ).all()
        return tuple(RiskTestRun.model_validate(row.data) for row in rows)

    def risk_test_run(self, run_id: str) -> RiskTestRun | None:
        with Session(self.engine) as session:
            row = session.get(RiskTestRunRecord, run_id)
        return RiskTestRun.model_validate(row.data) if row else None

    def save_risk_outcome(self, outcome: RiskRunOutcome) -> None:
        with Session(self.engine) as session, session.begin():
            row = session.get(RiskTestRunRecord, outcome.run.id)
            if row is None:
                raise KeyError(outcome.run.id)
            row.status = outcome.run.status.value
            row.data = outcome.run.model_dump(mode="json")
            session.query(RiskTraceRecord).filter(
                RiskTraceRecord.test_run_id == outcome.run.id
            ).delete()
            session.query(FindingRecord).filter(
                FindingRecord.test_run_id == outcome.run.id
            ).delete()
            session.add_all(
                [
                    RiskTraceRecord(
                        id=event.id,
                        test_run_id=outcome.run.id,
                        sequence=event.sequence,
                        data=event.model_dump(mode="json"),
                    )
                    for event in outcome.events
                ]
            )
            session.add_all(
                [
                    FindingRecord(
                        id=finding.id,
                        assessment_id=finding.assessment_id,
                        test_run_id=finding.test_run_id,
                        severity=finding.severity.value,
                        data=finding.model_dump(mode="json"),
                    )
                    for finding in outcome.findings
                ]
            )

    def risk_events(self, run_id: str, after_sequence: int = 0) -> tuple[TraceEvent, ...]:
        with Session(self.engine) as session:
            rows = session.scalars(
                select(RiskTraceRecord)
                .where(
                    RiskTraceRecord.test_run_id == run_id,
                    RiskTraceRecord.sequence > after_sequence,
                )
                .order_by(RiskTraceRecord.sequence)
            ).all()
        return tuple(TraceEvent.model_validate(row.data) for row in rows)

    def risk_findings(self, assessment_id: str) -> tuple[Finding, ...]:
        with Session(self.engine) as session:
            rows = session.scalars(
                select(FindingRecord)
                .where(FindingRecord.assessment_id == assessment_id)
                .order_by(FindingRecord.severity, FindingRecord.id)
            ).all()
        return tuple(Finding.model_validate(row.data) for row in rows)

    def save_risk_report(self, report: RiskReport, html: str) -> RiskReport:
        with Session(self.engine) as session, session.begin():
            row = session.get(RiskReportRecord, report.assessment_id)
            if row:
                row.data = report.model_dump(mode="json")
                row.html = html
            else:
                session.add(
                    RiskReportRecord(
                        assessment_id=report.assessment_id,
                        data=report.model_dump(mode="json"),
                        html=html,
                    )
                )
        return report

    def risk_report(self, assessment_id: str) -> RiskReport | None:
        with Session(self.engine) as session:
            row = session.get(RiskReportRecord, assessment_id)
        return RiskReport.model_validate(row.data) if row else None

    def risk_report_html(self, assessment_id: str) -> str | None:
        with Session(self.engine) as session:
            row = session.get(RiskReportRecord, assessment_id)
        return row.html if row else None

    def save_attestation(self, assessment_id: str, attestation: Attestation) -> Attestation:
        with Session(self.engine) as session, session.begin():
            row = session.get(AttestationRecord, attestation.id)
            if row:
                row.data = attestation.model_dump(mode="json")
            else:
                session.add(
                    AttestationRecord(
                        id=attestation.id,
                        assessment_id=assessment_id,
                        data=attestation.model_dump(mode="json"),
                    )
                )
        return attestation

    def create_tournament(
        self,
        *,
        name: str,
        agent_ids: list[str],
        scenario_versions: dict[str, str],
        repetitions: int,
        idempotency_key: str,
    ) -> tuple[Tournament, tuple[Run, ...], bool]:
        with Session(self.engine) as session, session.begin():
            existing = session.scalar(
                select(TournamentRecord).where(TournamentRecord.idempotency_key == idempotency_key)
            )
            if existing:
                tournament = _tournament(existing)
                runs = tuple(
                    _run(row)
                    for row in session.scalars(
                        select(RunRecord).where(RunRecord.tournament_id == existing.id)
                    )
                )
                return tournament, runs, False
            stamp = datetime.now(UTC)
            tournament = Tournament(
                id=f"tournament-{uuid4().hex[:12]}",
                name=name[:200],
                agent_ids=agent_ids,
                scenario_ids=list(scenario_versions),
                repetitions=repetitions,
            )
            session.add(
                TournamentRecord(
                    id=tournament.id,
                    idempotency_key=idempotency_key[:160],
                    name=tournament.name,
                    agent_ids=tournament.agent_ids,
                    scenario_ids=tournament.scenario_ids,
                    repetitions=repetitions,
                    status=tournament.status,
                    created_at=stamp,
                    updated_at=stamp,
                )
            )
            runs: list[Run] = []
            for agent_id in agent_ids:
                for scenario_id, version in scenario_versions.items():
                    for repetition in range(1, repetitions + 1):
                        run = Run(
                            id=f"run-{uuid4().hex[:12]}",
                            tournament_id=tournament.id,
                            scenario_id=scenario_id,
                            scenario_version=version,
                            agent_id=agent_id,
                            repetition=repetition,
                        )
                        session.add(_run_record(run))
                        runs.append(run)
            return tournament, tuple(runs), True

    def tournament(self, tournament_id: str) -> Tournament | None:
        with Session(self.engine) as session:
            row = session.get(TournamentRecord, tournament_id)
        return _tournament(row) if row else None

    def runs(self, tournament_id: str | None = None) -> tuple[Run, ...]:
        query = select(RunRecord)
        if tournament_id:
            query = query.where(RunRecord.tournament_id == tournament_id)
        query = query.order_by(RunRecord.created_at, RunRecord.id)
        with Session(self.engine) as session:
            return tuple(_run(row) for row in session.scalars(query))

    def run(self, run_id: str) -> Run | None:
        with Session(self.engine) as session:
            row = session.get(RunRecord, run_id)
        return _run(row) if row else None

    def save_outcome(self, outcome) -> None:
        with Session(self.engine) as session, session.begin():
            current = session.get(RunRecord, outcome.run.id)
            if current is None:
                raise KeyError(outcome.run.id)
            for key, value in outcome.run.model_dump().items():
                if key == "status":
                    value = value.value
                setattr(current, key, value)
            session.query(TraceRecord).filter(TraceRecord.run_id == outcome.run.id).delete()
            session.add_all([_trace_record(event) for event in outcome.events])
            if outcome.evaluation:
                data = outcome.evaluation.model_dump(mode="json")
                evaluation = session.get(EvaluationRecord, outcome.run.id)
                if evaluation:
                    evaluation.data = data
                else:
                    session.add(EvaluationRecord(run_id=outcome.run.id, data=data))
            if outcome.approval:
                session.add(
                    ApprovalRecord(
                        id=outcome.approval.id,
                        run_id=outcome.run.id,
                        data=outcome.approval.model_dump(mode="json"),
                    )
                )
            self._refresh_tournament(session, outcome.run.tournament_id)

    def events(self, run_id: str, after_sequence: int = 0) -> tuple[TraceEvent, ...]:
        with Session(self.engine) as session:
            rows = session.scalars(
                select(TraceRecord)
                .where(TraceRecord.run_id == run_id, TraceRecord.sequence > after_sequence)
                .order_by(TraceRecord.sequence)
            ).all()
        return tuple(_trace(row) for row in rows)

    def evaluation(self, run_id: str) -> Evaluation | None:
        with Session(self.engine) as session:
            row = session.get(EvaluationRecord, run_id)
        return Evaluation.model_validate(row.data) if row else None

    def approval(self, approval_id: str) -> ApprovalRequest | None:
        with Session(self.engine) as session:
            row = session.get(ApprovalRecord, approval_id)
        return ApprovalRequest.model_validate(row.data) if row else None

    def decide_approval(self, approval_id: str, approved: bool) -> ApprovalRequest:
        with Session(self.engine) as session, session.begin():
            row = session.get(ApprovalRecord, approval_id)
            if row is None:
                raise KeyError(approval_id)
            approval = ApprovalRequest.model_validate(row.data)
            if approval.status != "pending":
                return approval
            approval = approval.model_copy(
                update={
                    "status": "approved" if approved else "rejected",
                    "decided_at": datetime.now(UTC),
                }
            )
            row.data = approval.model_dump(mode="json")
            if not approved:
                run = session.get(RunRecord, approval.run_id)
                if run:
                    run.status = RunStatus.FAILED
                    run.error = "approval_rejected"
                    run.completed_at = datetime.now(UTC)
        return approval

    def leaderboard(self) -> list[dict[str, Any]]:
        totals: dict[str, list[float]] = defaultdict(list)
        with Session(self.engine) as session:
            rows = session.execute(
                select(RunRecord.agent_id, EvaluationRecord.data).join(
                    EvaluationRecord, EvaluationRecord.run_id == RunRecord.id
                )
            ).all()
        for agent_id, data in rows:
            score = Evaluation.model_validate(data).score.total
            totals[agent_id].append(score)
        return sorted(
            [
                {
                    "agent_id": agent_id,
                    "mean_score": round(sum(scores) / len(scores), 2),
                    "runs": len(scores),
                    "min_score": min(scores),
                    "max_score": max(scores),
                }
                for agent_id, scores in totals.items()
            ],
            key=lambda row: (-row["mean_score"], row["agent_id"]),
        )

    @staticmethod
    def _refresh_tournament(session: Session, tournament_id: str) -> None:
        tournament = session.get(TournamentRecord, tournament_id)
        if not tournament:
            return
        statuses = set(
            session.scalars(
                select(RunRecord.status).where(RunRecord.tournament_id == tournament_id)
            )
        )
        if statuses <= {
            RunStatus.COMPLETED.value,
            RunStatus.FAILED.value,
            RunStatus.TIMED_OUT.value,
        }:
            tournament.status = TournamentStatus.COMPLETED
        elif RunStatus.WAITING_APPROVAL.value in statuses:
            tournament.status = TournamentStatus.PAUSED
        elif statuses != {RunStatus.QUEUED.value}:
            tournament.status = TournamentStatus.RUNNING
        tournament.updated_at = datetime.now(UTC)


def _tournament(row: TournamentRecord) -> Tournament:
    return Tournament(
        id=row.id,
        name=row.name,
        agent_ids=row.agent_ids,
        scenario_ids=row.scenario_ids,
        repetitions=row.repetitions,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _run(row: RunRecord) -> Run:
    return Run(
        id=row.id,
        tournament_id=row.tournament_id,
        scenario_id=row.scenario_id,
        scenario_version=row.scenario_version,
        agent_id=row.agent_id,
        repetition=row.repetition,
        status=row.status,
        answer=row.answer,
        error=row.error,
        created_at=row.created_at,
        started_at=row.started_at,
        completed_at=row.completed_at,
    )


def _run_record(run: Run) -> RunRecord:
    data = run.model_dump()
    data["status"] = run.status.value
    return RunRecord(**data)


def _trace_record(event: TraceEvent) -> TraceRecord:
    data = event.model_dump()
    data["kind"] = event.kind.value
    return TraceRecord(**data)


def _trace(row: TraceRecord) -> TraceEvent:
    return TraceEvent(
        id=row.id,
        run_id=row.run_id,
        sequence=row.sequence,
        kind=row.kind,
        name=row.name,
        payload=row.payload,
        created_at=row.created_at,
        duration_ms=row.duration_ms,
        input_tokens=row.input_tokens,
        output_tokens=row.output_tokens,
        estimated_cost_usd=row.estimated_cost_usd,
    )
