"""Add private Agent risk assessment and attestation records."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("agent_targets"):
        op.create_table(
            "agent_targets",
            sa.Column("id", sa.String(length=64), primary_key=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("data", sa.JSON(), nullable=False),
        )
        op.create_index("ix_agent_targets_created_at", "agent_targets", ["created_at"])
    if not inspector.has_table("assessments"):
        op.create_table(
            "assessments",
            sa.Column("id", sa.String(length=64), primary_key=True),
            sa.Column(
                "target_id",
                sa.String(length=64),
                sa.ForeignKey("agent_targets.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("status", sa.String(length=40), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("data", sa.JSON(), nullable=False),
        )
        op.create_index("ix_assessments_target_id", "assessments", ["target_id"])
        op.create_index("ix_assessments_status", "assessments", ["status"])
        op.create_index("ix_assessments_created_at", "assessments", ["created_at"])
    if not inspector.has_table("risk_test_runs"):
        op.create_table(
            "risk_test_runs",
            sa.Column("id", sa.String(length=64), primary_key=True),
            sa.Column(
                "assessment_id",
                sa.String(length=64),
                sa.ForeignKey("assessments.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("variant_id", sa.String(length=120), nullable=False),
            sa.Column("repetition", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=40), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("data", sa.JSON(), nullable=False),
            sa.UniqueConstraint("assessment_id", "variant_id", "repetition"),
        )
        op.create_index("ix_risk_test_runs_assessment_id", "risk_test_runs", ["assessment_id"])
        op.create_index("ix_risk_test_runs_status", "risk_test_runs", ["status"])
        op.create_index("ix_risk_test_runs_created_at", "risk_test_runs", ["created_at"])
    if not inspector.has_table("risk_trace_events"):
        op.create_table(
            "risk_trace_events",
            sa.Column("id", sa.String(length=64), primary_key=True),
            sa.Column(
                "test_run_id",
                sa.String(length=64),
                sa.ForeignKey("risk_test_runs.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("sequence", sa.Integer(), nullable=False),
            sa.Column("data", sa.JSON(), nullable=False),
            sa.UniqueConstraint("test_run_id", "sequence"),
        )
        op.create_index("ix_risk_trace_events_test_run_id", "risk_trace_events", ["test_run_id"])
    if not inspector.has_table("risk_findings"):
        op.create_table(
            "risk_findings",
            sa.Column("id", sa.String(length=64), primary_key=True),
            sa.Column(
                "assessment_id",
                sa.String(length=64),
                sa.ForeignKey("assessments.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "test_run_id",
                sa.String(length=64),
                sa.ForeignKey("risk_test_runs.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("severity", sa.String(length=20), nullable=False),
            sa.Column("data", sa.JSON(), nullable=False),
        )
        op.create_index("ix_risk_findings_assessment_id", "risk_findings", ["assessment_id"])
        op.create_index("ix_risk_findings_test_run_id", "risk_findings", ["test_run_id"])
        op.create_index("ix_risk_findings_severity", "risk_findings", ["severity"])
    if not inspector.has_table("risk_reports"):
        op.create_table(
            "risk_reports",
            sa.Column(
                "assessment_id",
                sa.String(length=64),
                sa.ForeignKey("assessments.id", ondelete="CASCADE"),
                primary_key=True,
            ),
            sa.Column("data", sa.JSON(), nullable=False),
            sa.Column("html", sa.Text(), nullable=False),
        )
    if not inspector.has_table("attestations"):
        op.create_table(
            "attestations",
            sa.Column("id", sa.String(length=80), primary_key=True),
            sa.Column(
                "assessment_id",
                sa.String(length=64),
                sa.ForeignKey("assessments.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("data", sa.JSON(), nullable=False),
        )
        op.create_index("ix_attestations_assessment_id", "attestations", ["assessment_id"])


def downgrade() -> None:
    for table in (
        "attestations",
        "risk_reports",
        "risk_findings",
        "risk_trace_events",
        "risk_test_runs",
        "assessments",
        "agent_targets",
    ):
        if sa.inspect(op.get_bind()).has_table(table):
            op.drop_table(table)
