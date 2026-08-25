"""Phase 8 query persistence: validations, validation_checks, decisions.

Revision ID: 0003_phase8_query
Revises: 0002_phase4_extractor
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_phase8_query"
down_revision: str | None = "0002_phase4_extractor"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB(astext_type=sa.Text())
NOW = sa.text("now()")


def upgrade() -> None:
    op.create_table(
        "validations",
        sa.Column("validation_id", UUID, primary_key=True),
        sa.Column(
            "verification_run_id",
            UUID,
            sa.ForeignKey("verification_runs.verification_run_id"),
            nullable=False,
        ),
        sa.Column("shipment_id", UUID, sa.ForeignKey("shipments.shipment_id"), nullable=False),
        sa.Column("document_id", UUID, sa.ForeignKey("documents.document_id")),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("aggregate_result", sa.Text()),
        sa.Column(
            "document_version_ids",
            JSONB,
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("summary_json", JSONB),
        sa.Column("error_code", sa.Text()),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "status IN ('pending','running','completed','failed')",
            name="ck_validations_status",
        ),
        sa.CheckConstraint(
            "aggregate_result IS NULL OR aggregate_result IN ('MATCH','MISMATCH','UNCERTAIN')",
            name="ck_validations_aggregate_result",
        ),
        sa.CheckConstraint(
            "(status <> 'completed') OR (aggregate_result IS NOT NULL)",
            name="ck_validations_completed_has_result",
        ),
        sa.CheckConstraint(
            "(status <> 'failed') OR (aggregate_result IS NULL OR aggregate_result <> 'MATCH')",
            name="ck_validations_failed_not_match",
        ),
        sa.UniqueConstraint("verification_run_id", name="uq_validations_verification_run"),
    )
    op.create_index(
        "ix_validations_shipment_created",
        "validations",
        ["shipment_id", "created_at"],
    )
    op.create_index("ix_validations_document_id", "validations", ["document_id"])

    op.create_table(
        "validation_checks",
        sa.Column("validation_check_id", UUID, primary_key=True),
        sa.Column(
            "validation_id",
            UUID,
            sa.ForeignKey("validations.validation_id"),
            nullable=False,
        ),
        sa.Column("rule_key", sa.Text(), nullable=False),
        sa.Column("check_sequence", sa.Integer(), nullable=False),
        sa.Column("result", sa.Text(), nullable=False),
        sa.Column("field_key", sa.Text()),
        sa.Column("reason_code", sa.Text(), nullable=False),
        sa.Column("reason_detail", sa.Text()),
        sa.Column("evaluator", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float()),
        sa.Column("expected_json", JSONB),
        sa.Column("actual_json", JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.CheckConstraint(
            "result IN ('MATCH','MISMATCH','UNCERTAIN')",
            name="ck_validation_checks_result",
        ),
        sa.UniqueConstraint(
            "validation_id",
            "rule_key",
            "check_sequence",
            name="uq_validation_checks_rule_sequence",
        ),
    )
    op.create_index(
        "ix_validation_checks_validation_id",
        "validation_checks",
        ["validation_id"],
    )
    op.create_index("ix_validation_checks_result", "validation_checks", ["result"])

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
        ),
        sa.Column("validation_id", UUID, sa.ForeignKey("validations.validation_id")),
        sa.Column("disposition", sa.Text(), nullable=False),
        sa.Column("policy_id", sa.Text()),
        sa.Column("policy_version", sa.Text(), nullable=False),
        sa.Column("reason_codes", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("reasons", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("confidence", sa.Float()),
        sa.Column("actor_type", sa.Text(), nullable=False),
        sa.Column("agent_version", sa.Text()),
        sa.Column("trace_id", sa.Text()),
        sa.Column(
            "reasoning_json",
            JSONB,
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("risk_flags", JSONB),
        sa.Column("supersedes_decision_id", UUID, sa.ForeignKey("decisions.decision_id")),
        sa.Column(
            "input_fingerprint",
            sa.String(64),
            nullable=False,
            server_default="",
        ),
        sa.Column("llm_rationale", sa.Text()),
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
    op.create_index(
        "ix_decisions_shipment_decided",
        "decisions",
        ["shipment_id", "decided_at"],
    )
    op.create_index(
        "ix_decisions_disposition_decided",
        "decisions",
        ["disposition", "decided_at"],
    )
    op.create_index("ix_decisions_document_id", "decisions", ["document_id"])


def downgrade() -> None:
    op.drop_index("ix_decisions_document_id", table_name="decisions")
    op.drop_index("ix_decisions_disposition_decided", table_name="decisions")
    op.drop_index("ix_decisions_shipment_decided", table_name="decisions")
    op.drop_table("decisions")
    op.drop_index("ix_validation_checks_result", table_name="validation_checks")
    op.drop_index("ix_validation_checks_validation_id", table_name="validation_checks")
    op.drop_table("validation_checks")
    op.drop_index("ix_validations_document_id", table_name="validations")
    op.drop_index("ix_validations_shipment_created", table_name="validations")
    op.drop_table("validations")
