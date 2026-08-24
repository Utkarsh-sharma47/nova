"""Phase 4 extraction persistence tables.

Revision ID: 0002_phase4_extractor
Revises: 0001_phase3_foundation
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_phase4_extractor"
down_revision: str | None = "0001_phase3_foundation"
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
        "'failed','superseded','withdrawn')",
    )

    op.create_table(
        "agent_executions",
        sa.Column("agent_execution_id", UUID, primary_key=True),
        sa.Column(
            "verification_run_id",
            UUID,
            sa.ForeignKey("verification_runs.verification_run_id"),
            nullable=False,
        ),
        sa.Column("document_id", UUID, sa.ForeignKey("documents.document_id"), nullable=False),
        sa.Column(
            "document_version_id",
            UUID,
            sa.ForeignKey("document_versions.document_version_id"),
            nullable=False,
        ),
        sa.Column("stage", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("attempt_group", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("agent_version", sa.Text(), nullable=False),
        sa.Column("prompt_id", sa.Text()),
        sa.Column("prompt_version", sa.Text()),
        sa.Column("provider", sa.Text()),
        sa.Column("model_name", sa.Text()),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("trace_id", sa.Text()),
        sa.Column("error_code", sa.Text()),
        sa.Column("error_message", sa.Text()),
        sa.Column("result_json", JSONB),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("duration_ms", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.CheckConstraint(
            "stage IN ('extractor','validator','router')",
            name="ck_agent_executions_stage",
        ),
        sa.CheckConstraint(
            "status IN ('running','succeeded','partial','failed')",
            name="ck_agent_executions_status",
        ),
        sa.UniqueConstraint(
            "verification_run_id",
            "stage",
            "attempt_group",
            name="uq_agent_executions_run_stage_group",
        ),
    )

    op.create_table(
        "model_call_metadata",
        sa.Column("model_call_id", UUID, primary_key=True),
        sa.Column(
            "verification_run_id",
            UUID,
            sa.ForeignKey("verification_runs.verification_run_id"),
            nullable=False,
        ),
        sa.Column(
            "agent_execution_id",
            UUID,
            sa.ForeignKey("agent_executions.agent_execution_id"),
        ),
        sa.Column("stage", sa.Text(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("model_name", sa.Text(), nullable=False),
        sa.Column("prompt_version", sa.Text(), nullable=False),
        sa.Column("response_schema_version", sa.Text()),
        sa.Column("temperature", sa.Float()),
        sa.Column("token_input", sa.Integer()),
        sa.Column("token_output", sa.Integer()),
        sa.Column("cost_usd", sa.Float()),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("request_hash", sa.Text()),
        sa.Column("attempt", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
    )

    op.create_table(
        "extracted_fields",
        sa.Column("extracted_field_id", UUID, primary_key=True),
        sa.Column(
            "verification_run_id",
            UUID,
            sa.ForeignKey("verification_runs.verification_run_id"),
            nullable=False,
        ),
        sa.Column(
            "document_version_id",
            UUID,
            sa.ForeignKey("document_versions.document_version_id"),
            nullable=False,
        ),
        sa.Column(
            "agent_execution_id",
            UUID,
            sa.ForeignKey("agent_executions.agent_execution_id"),
        ),
        sa.Column(
            "model_call_id",
            UUID,
            sa.ForeignKey("model_call_metadata.model_call_id"),
        ),
        sa.Column("field_key", sa.Text(), nullable=False),
        sa.Column("value_json", JSONB),
        sa.Column("value_type", sa.Text(), nullable=False),
        sa.Column("presence", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float()),
        sa.Column("evidence_json", JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("is_missing", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("absence_reason", sa.Text()),
        sa.Column("uncertainty_json", JSONB),
        sa.Column("extractor_notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.UniqueConstraint(
            "verification_run_id",
            "document_version_id",
            "field_key",
            name="uq_extracted_fields_run_version_key",
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="ck_extracted_fields_confidence",
        ),
        sa.CheckConstraint(
            "(NOT is_missing) OR value_json IS NULL",
            name="ck_extracted_fields_missing_value",
        ),
    )


def downgrade() -> None:
    op.drop_table("extracted_fields")
    op.drop_table("model_call_metadata")
    op.drop_table("agent_executions")
    op.drop_constraint("ck_documents_status", "documents", type_="check")
    op.create_check_constraint(
        "ck_documents_status",
        "documents",
        "status IN ('registered','content_available','in_pipeline','extracted',"
        "'superseded','withdrawn')",
    )
