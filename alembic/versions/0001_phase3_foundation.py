"""Phase 3 foundation tables for document ingestion.

Revision ID: 0001_phase3_foundation
Revises:
Create Date: 2026-08-25

Creates: customers, shipments, documents, document_versions,
verification_runs, idempotency_records.

NOTE: The decisions.actor_type / disposition failsafe CHECK
(system_failsafe cannot AUTO_APPROVE) is deferred until the decisions
table is introduced in a later phase.
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


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "customers",
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("external_key", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("default_timezone", sa.Text(), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("char_length(name) > 0", name="ck_customers_name_nonempty"),
        sa.CheckConstraint(
            "status IN ('draft', 'active', 'suspended', 'archived')",
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
        sa.Column(
            "shipment_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customers.customer_id"),
            nullable=False,
        ),
        sa.Column("customer_shipment_ref", sa.Text(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="open"),
        sa.Column("priority", sa.Integer(), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('open', 'ingesting', 'extracting', 'validating', 'routing', "
            "'decided', 'closed')",
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

    # documents without circular current_version FK first
    op.create_table(
        "documents",
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "shipment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("shipments.shipment_id"),
            nullable=False,
        ),
        sa.Column("document_type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="received"),
        sa.Column("display_name", sa.Text(), nullable=True),
        sa.Column("source_system", sa.Text(), nullable=True),
        sa.Column(
            "ingestion_channel", sa.Text(), nullable=False, server_default="upload"
        ),
        sa.Column("external_ref", sa.Text(), nullable=True),
        sa.Column("current_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('received', 'stored', 'processing', 'processed', "
            "'failed', 'superseded', 'withdrawn')",
            name="ck_documents_status",
        ),
        sa.CheckConstraint(
            "document_type IN ('commercial_invoice', 'bill_of_lading', 'packing_list', 'other')",
            name="ck_documents_type",
        ),
        sa.CheckConstraint(
            "ingestion_channel IN ('upload', 'path', 'email', 'api')",
            name="ck_documents_channel",
        ),
    )

    op.create_table(
        "document_versions",
        sa.Column(
            "document_version_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.document_id"),
            nullable=False,
        ),
        sa.Column(
            "shipment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("shipments.shipment_id"),
            nullable=False,
        ),
        sa.Column("document_type", sa.Text(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("storage_uri", sa.Text(), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("media_type", sa.Text(), nullable=False),
        sa.Column("byte_size", sa.BigInteger(), nullable=False),
        sa.Column("original_filename", sa.Text(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("ingestion_idempotency_key", sa.Text(), nullable=True),
        sa.Column("source_message_id", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("version_number > 0", name="ck_document_versions_number"),
        sa.CheckConstraint("byte_size >= 0", name="ck_document_versions_byte_size"),
        sa.CheckConstraint(
            "char_length(content_sha256) = 64",
            name="ck_document_versions_sha_len",
        ),
        sa.UniqueConstraint(
            "document_id", "version_number", name="uq_document_versions_number"
        ),
        sa.UniqueConstraint(
            "shipment_id",
            "document_type",
            "content_sha256",
            name="uq_document_versions_shipment_type_hash",
        ),
    )
    op.create_index(
        "uq_document_versions_idempotency",
        "document_versions",
        ["ingestion_idempotency_key"],
        unique=True,
        postgresql_where=sa.text("ingestion_idempotency_key IS NOT NULL"),
    )

    op.create_foreign_key(
        "fk_documents_current_version",
        "documents",
        "document_versions",
        ["current_version_id"],
        ["document_version_id"],
    )

    op.create_table(
        "verification_runs",
        sa.Column(
            "verification_run_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "shipment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("shipments.shipment_id"),
            nullable=False,
        ),
        sa.Column("status", sa.Text(), nullable=False, server_default="queued"),
        sa.Column("idempotency_key", sa.Text(), nullable=True),
        sa.Column("trigger", sa.Text(), nullable=False, server_default="upload"),
        sa.Column(
            "document_version_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')",
            name="ck_verification_runs_status",
        ),
    )
    op.create_index(
        "uq_verification_runs_idempotency",
        "verification_runs",
        ["idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )

    op.create_table(
        "idempotency_records",
        sa.Column(
            "idempotency_record_id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("principal_hash", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("request_fingerprint", sa.Text(), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shipment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("verification_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("response_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "principal_hash",
            "idempotency_key",
            name="uq_idempotency_principal_key",
        ),
        sa.CheckConstraint(
            "char_length(idempotency_key) BETWEEN 8 AND 128",
            name="ck_idempotency_key_length",
        ),
    )


def downgrade() -> None:
    op.drop_table("idempotency_records")
    op.drop_index("uq_verification_runs_idempotency", table_name="verification_runs")
    op.drop_table("verification_runs")
    op.drop_constraint("fk_documents_current_version", "documents", type_="foreignkey")
    op.drop_index("uq_document_versions_idempotency", table_name="document_versions")
    op.drop_table("document_versions")
    op.drop_table("documents")
    op.drop_index("uq_shipments_customer_ref", table_name="shipments")
    op.drop_table("shipments")
    op.drop_index("uq_customers_external_key", table_name="customers")
    op.drop_table("customers")
