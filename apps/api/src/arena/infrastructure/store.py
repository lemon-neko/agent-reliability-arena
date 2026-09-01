"""SQLAlchemy persistence for tournaments, runs, traces, approvals, and scores."""

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
