"""Phase 6 decisions table with failsafe AUTO_APPROVE prohibition.

Revision ID: 0002_phase6_decisions
Revises: 0001_phase3_foundation
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_phase6_decisions"
down_revision: str | None = "0001_phase3_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB(astext_type=sa.Text())
NOW = sa.text("now()")


def upgrade() -> None:
    op.create_table(
        "decisions",
        sa.Column("decision_id", UUID, primary_key=True),
        sa.Column(
            "verification_run_id",
            UUID,
            sa.ForeignKey("verification_runs.verification_run_id"),
            nullable=False,
        ),
        sa.Column("shipment_id", UUID, sa.ForeignKey("shipments.shipment_id"), nullable=False),
        sa.Column("document_id", UUID, sa.ForeignKey("documents.document_id"), nullable=False),
        sa.Column(
            "document_version_id",
            UUID,
            sa.ForeignKey("document_versions.document_version_id"),
            nullable=False,
        ),
        sa.Column("validation_result_id", UUID, nullable=False),
        sa.Column("disposition", sa.Text(), nullable=False),
        sa.Column("policy_id", sa.Text()),
        sa.Column("policy_version", sa.Text(), nullable=False),
        sa.Column("reason_codes", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("reasons", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column(
            "triggering_check_ids",
            JSONB,
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "safety_constraints_applied",
            JSONB,
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("confidence", sa.Float()),
        sa.Column("actor_type", sa.Text(), nullable=False),
        sa.Column("agent_version", sa.Text()),
        sa.Column("trace_id", UUID, nullable=False),
        sa.Column(
            "reasoning_json",
            JSONB,
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("risk_flags", JSONB),
        sa.Column("supersedes_decision_id", UUID, sa.ForeignKey("decisions.decision_id")),
        sa.Column("input_fingerprint", sa.String(64), nullable=False),
        sa.Column("llm_rationale", sa.Text()),
        sa.Column(
            "evidence_refs",
            JSONB,
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("routing_rule_version", sa.Text()),
        sa.Column("decided_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.CheckConstraint(
            "disposition IN ('AUTO_APPROVE','HUMAN_REVIEW','AMENDMENT_REQUEST')",
            name="ck_decisions_disposition",
        ),
        sa.CheckConstraint(
            "actor_type IN ('router','system_failsafe')",
            name="ck_decisions_actor_type",
        ),
        sa.CheckConstraint(
            "actor_type <> 'system_failsafe' OR disposition <> 'AUTO_APPROVE'",
            name="ck_decisions_failsafe_no_auto_approve",
        ),
        sa.UniqueConstraint("verification_run_id", name="uq_decisions_verification_run"),
    )
    op.create_index("ix_decisions_shipment_id", "decisions", ["shipment_id"])
    op.create_index("ix_decisions_decided_at", "decisions", ["decided_at"])


def downgrade() -> None:
    op.drop_index("ix_decisions_decided_at", table_name="decisions")
    op.drop_index("ix_decisions_shipment_id", table_name="decisions")
    op.drop_table("decisions")
