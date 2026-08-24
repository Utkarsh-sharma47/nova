"""SQLAlchemy ORM models for Phase 3 ingestion entities."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class CustomerModel(Base):
    __tablename__ = "customers"
    __table_args__ = (
        CheckConstraint("char_length(name) > 0", name="ck_customers_name_nonempty"),
        CheckConstraint(
            "status IN ('draft', 'active', 'suspended', 'archived')",
            name="ck_customers_status",
        ),
        Index(
            "uq_customers_external_key",
            "external_key",
            unique=True,
            postgresql_where=text("external_key IS NOT NULL"),
        ),
    )

    customer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    external_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active")
    default_timezone: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    shipments: Mapped[list[ShipmentModel]] = relationship(back_populates="customer")


class ShipmentModel(Base):
    __tablename__ = "shipments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'ingesting', 'extracting', 'validating', 'routing', "
            "'decided', 'closed')",
            name="ck_shipments_status",
        ),
        Index(
            "uq_shipments_customer_ref",
            "customer_id",
            "customer_shipment_ref",
            unique=True,
            postgresql_where=text("customer_shipment_ref IS NOT NULL"),
        ),
    )

    shipment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    customer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("customers.customer_id"), nullable=False
    )
    customer_shipment_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="open")
    priority: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    customer: Mapped[CustomerModel] = relationship(back_populates="shipments")
    documents: Mapped[list[DocumentModel]] = relationship(back_populates="shipment")
    verification_runs: Mapped[list[VerificationRunModel]] = relationship(
        back_populates="shipment"
    )


class DocumentModel(Base):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint(
            "status IN ('received', 'stored', 'processing', 'processed', "
            "'failed', 'superseded', 'withdrawn')",
            name="ck_documents_status",
        ),
        CheckConstraint(
            "document_type IN ('commercial_invoice', 'bill_of_lading', 'packing_list', 'other')",
            name="ck_documents_type",
        ),
        CheckConstraint(
            "ingestion_channel IN ('upload', 'path', 'email', 'api')",
            name="ck_documents_channel",
        ),
    )

    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    shipment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("shipments.shipment_id"), nullable=False
    )
    document_type: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="received")
    display_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_system: Mapped[str | None] = mapped_column(Text, nullable=True)
    ingestion_channel: Mapped[str] = mapped_column(Text, nullable=False, default="upload")
    external_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_version_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "document_versions.document_version_id",
            use_alter=True,
            name="fk_documents_current_version",
        ),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    shipment: Mapped[ShipmentModel] = relationship(back_populates="documents")
    versions: Mapped[list[DocumentVersionModel]] = relationship(
        back_populates="document",
        foreign_keys="DocumentVersionModel.document_id",
    )


class DocumentVersionModel(Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        CheckConstraint("version_number > 0", name="ck_document_versions_number"),
        CheckConstraint("byte_size >= 0", name="ck_document_versions_byte_size"),
        CheckConstraint(
            "char_length(content_sha256) = 64",
            name="ck_document_versions_sha_len",
        ),
        UniqueConstraint("document_id", "version_number", name="uq_document_versions_number"),
        Index(
            "uq_document_versions_idempotency",
            "ingestion_idempotency_key",
            unique=True,
            postgresql_where=text("ingestion_idempotency_key IS NOT NULL"),
        ),
        UniqueConstraint(
            "shipment_id",
            "document_type",
            "content_sha256",
            name="uq_document_versions_shipment_type_hash",
        ),
    )

    document_version_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    document_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("documents.document_id"), nullable=False
    )
    shipment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("shipments.shipment_id"), nullable=False
    )
    document_type: Mapped[str] = mapped_column(Text, nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_uri: Mapped[str] = mapped_column(Text, nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    media_type: Mapped[str] = mapped_column(Text, nullable=False)
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    original_filename: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ingestion_idempotency_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_message_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    document: Mapped[DocumentModel] = relationship(
        back_populates="versions",
        foreign_keys=[document_id],
    )


class VerificationRunModel(Base):
    __tablename__ = "verification_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'running', 'succeeded', 'failed', 'cancelled')",
            name="ck_verification_runs_status",
        ),
        Index(
            "uq_verification_runs_idempotency",
            "idempotency_key",
            unique=True,
            postgresql_where=text("idempotency_key IS NOT NULL"),
        ),
    )

    verification_run_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    shipment_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("shipments.shipment_id"), nullable=False
    )
    status: Mapped[str] = mapped_column(Text, nullable=False, default="queued")
    idempotency_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    trigger: Mapped[str] = mapped_column(Text, nullable=False, default="upload")
    document_version_ids: Mapped[list[Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb")
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    shipment: Mapped[ShipmentModel] = relationship(back_populates="verification_runs")


class IdempotencyRecordModel(Base):
    """HTTP idempotency records for POST /v1/documents."""

    __tablename__ = "idempotency_records"
    __table_args__ = (
        UniqueConstraint(
            "principal_hash", "idempotency_key", name="uq_idempotency_principal_key"
        ),
        CheckConstraint(
            "char_length(idempotency_key) BETWEEN 8 AND 128",
            name="ck_idempotency_key_length",
        ),
    )

    idempotency_record_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    principal_hash: Mapped[str] = mapped_column(Text, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(Text, nullable=False)
    request_fingerprint: Mapped[str] = mapped_column(Text, nullable=False)
    document_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    shipment_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    verification_run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    response_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
