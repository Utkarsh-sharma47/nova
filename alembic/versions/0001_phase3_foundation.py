"""Phase 3 application foundation tables.

Revision ID: 0001_phase3_foundation
Revises:
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_phase3_foundation"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID = postgresql.UUID(as_uuid=True)
JSONB = postgresql.JSONB(astext_type=sa.Text())
NOW = sa.text("now()")


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("customer_id", UUID, primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("external_key", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("default_timezone", sa.Text()),
        sa.Column("metadata", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("char_length(name) > 0", name="ck_customers_name_nonempty"),
        sa.CheckConstraint(
            "status IN ('draft','active','suspended','archived')",
            name="ck_customers_status",
        ),
    )
    op.create_index(
        "uq_customers_external_key",
        "customers",
        ["external_key"],
        unique=True,
        postgresql_where=sa.text("external_key IS NOT NULL"),
    )
    op.create_table(
        "shipments",
        sa.Column("shipment_id", UUID, primary_key=True),
        sa.Column("customer_id", UUID, sa.ForeignKey("customers.customer_id"), nullable=False),
        sa.Column("customer_shipment_ref", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("priority", sa.Integer()),
        sa.Column("metadata", JSONB, server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "status IN ('open','ingesting','extracting','validating','routing','decided','closed')",
            name="ck_shipments_status",
        ),
    )
    op.create_index(
        "uq_shipments_customer_ref",
        "shipments",
        ["customer_id", "customer_shipment_ref"],
        unique=True,
        postgresql_where=sa.text("customer_shipment_ref IS NOT NULL"),
    )
    op.create_table(
        "documents",
        sa.Column("document_id", UUID, primary_key=True),
        sa.Column("shipment_id", UUID, sa.ForeignKey("shipments.shipment_id"), nullable=False),
        sa.Column("document_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text()),
        sa.Column("source_system", sa.Text()),
        sa.Column("ingestion_channel", sa.Text(), nullable=False),
        sa.Column("external_ref", sa.Text()),
        sa.Column("current_version_id", UUID),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "document_type IN ('commercial_invoice','bill_of_lading','packing_list','other')",
            name="ck_documents_type",
        ),
        sa.CheckConstraint(
            "status IN ('registered','content_available','in_pipeline','extracted',"
            "'superseded','withdrawn')",
            name="ck_documents_status",
        ),
        sa.CheckConstraint(
            "ingestion_channel IN ('upload','path','email','api')",
            name="ck_documents_channel",
        ),
    )
    op.create_table(
        "document_versions",
        sa.Column("document_version_id", UUID, primary_key=True),
        sa.Column("document_id", UUID, sa.ForeignKey("documents.document_id"), nullable=False),
        sa.Column("shipment_id", UUID, sa.ForeignKey("shipments.shipment_id"), nullable=False),
        sa.Column("document_type", sa.Text(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("storage_uri", sa.Text(), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("media_type", sa.Text(), nullable=False),
        sa.Column("byte_size", sa.BigInteger(), nullable=False),
        sa.Column("original_filename", sa.Text()),
        sa.Column("page_count", sa.Integer()),
        sa.Column("ingestion_idempotency_key", sa.Text()),
        sa.Column("source_message_id", sa.Text()),
        sa.Column("created_by", sa.Text()),
        sa.Column("processor_name", sa.Text()),
        sa.Column("processor_version", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.CheckConstraint("version_number > 0", name="ck_document_versions_number"),
        sa.CheckConstraint("byte_size >= 0", name="ck_document_versions_size"),
        sa.CheckConstraint("char_length(content_sha256) = 64", name="ck_document_versions_sha"),
        sa.UniqueConstraint(
            "document_id",
            "version_number",
            name="uq_document_versions_number",
        ),
        sa.UniqueConstraint(
            "shipment_id",
            "document_type",
            "content_sha256",
            name="uq_document_versions_shipment_type_hash",
        ),
    )
    op.create_foreign_key(
        "fk_documents_current_version",
        "documents",
        "document_versions",
        ["current_version_id"],
        ["document_version_id"],
        deferrable=True,
        initially="DEFERRED",
    )
    op.create_table(
        "verification_runs",
        sa.Column("verification_run_id", UUID, primary_key=True),
        sa.Column("shipment_id", UUID, sa.ForeignKey("shipments.shipment_id"), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.Text()),
        sa.Column("trigger", sa.Text(), nullable=False),
        sa.Column(
            "document_version_ids",
            postgresql.ARRAY(UUID),
            server_default=sa.text("'{}'::uuid[]"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("error_code", sa.Text()),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.CheckConstraint(
            "status IN ('queued','running','succeeded','failed','cancelled')",
            name="ck_verification_runs_status",
        ),
    )
    op.create_table(
        "idempotency_records",
        sa.Column("idempotency_record_id", UUID, primary_key=True),
        sa.Column("principal_hash", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("document_id", UUID, sa.ForeignKey("documents.document_id"), nullable=False),
        sa.Column("shipment_id", UUID, sa.ForeignKey("shipments.shipment_id"), nullable=False),
        sa.Column(
            "verification_run_id",
            UUID,
            sa.ForeignKey("verification_runs.verification_run_id"),
            nullable=False,
        ),
        sa.Column("response_json", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=NOW, nullable=False),
        sa.CheckConstraint(
            "char_length(idempotency_key) BETWEEN 8 AND 128",
            name="ck_idempotency_key_length",
        ),
        sa.UniqueConstraint(
            "principal_hash",
            "idempotency_key",
            name="uq_idempotency_principal_key",
        ),
    )


def downgrade() -> None:
    op.drop_table("idempotency_records")
    op.drop_table("verification_runs")
    op.drop_constraint("fk_documents_current_version", "documents", type_="foreignkey")
    op.drop_table("document_versions")
    op.drop_table("documents")
    op.drop_index("uq_shipments_customer_ref", table_name="shipments")
    op.drop_table("shipments")
    op.drop_index("uq_customers_external_key", table_name="customers")
    op.drop_table("customers")
