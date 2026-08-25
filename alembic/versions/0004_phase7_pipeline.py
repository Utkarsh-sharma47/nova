"""Phase 7 validation persistence and document lifecycle expansion.

Revision ID: 0004_phase7_pipeline
Revises: 0003_phase6_decisions
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_phase7_pipeline"
down_revision: str | None = "0003_phase6_decisions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB(astext_type=sa.Text())
NOW = sa.text("now()")


def upgrade() -> None:
    op.drop_constraint("ck_documents_status", "documents", type_="check")
    op.create_check_constraint(
        "ck_documents_status",
        "documents",
        "status IN ('registered','content_available','in_pipeline','extracted',"
        "'validated','decided','failed','superseded','withdrawn')",
    )

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
        sa.Column("document_id", UUID, sa.ForeignKey("documents.document_id"), nullable=False),
        sa.Column(
            "document_version_id",
            UUID,
            sa.ForeignKey("document_versions.document_version_id"),
            nullable=False,
        ),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("aggregate_result", sa.Text()),
        sa.Column("ruleset_id", sa.Text()),
        sa.Column("ruleset_version", sa.Text()),
        sa.Column("engine_version", sa.Text(), nullable=False),
        sa.Column("validator_version", sa.Text(), nullable=False),
        sa.Column("result_json", JSONB, nullable=False),
        sa.Column("summary_json", JSONB),
        sa.Column("error_code", sa.Text()),
        sa.Column("error_message", sa.Text()),
        sa.Column("trace_id", UUID, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("verification_run_id", name="uq_validations_verification_run"),
        sa.CheckConstraint(
            "status IN ('completed','failed')",
            name="ck_validations_status",
        ),
        sa.CheckConstraint(
            "(status <> 'completed') OR (aggregate_result IN ('MATCH','MISMATCH','UNCERTAIN'))",
            name="ck_validations_completed_aggregate",
        ),
        sa.CheckConstraint(
            "(status <> 'failed') OR (aggregate_result IS NULL OR aggregate_result <> 'MATCH')",
            name="ck_validations_failed_not_match",
        ),
    )
    op.create_index("ix_validations_document_id", "validations", ["document_id"])
    op.create_index("ix_validations_shipment_id", "validations", ["shipment_id"])


def downgrade() -> None:
    op.drop_index("ix_validations_shipment_id", table_name="validations")
    op.drop_index("ix_validations_document_id", table_name="validations")
    op.drop_table("validations")
    op.drop_constraint("ck_documents_status", "documents", type_="check")
    op.create_check_constraint(
        "ck_documents_status",
        "documents",
        "status IN ('registered','content_available','in_pipeline','extracted',"
        "'failed','superseded','withdrawn')",
    )
