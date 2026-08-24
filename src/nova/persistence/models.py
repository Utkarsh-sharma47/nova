"""SQLAlchemy persistence model for the Phase 3 system of record."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        CheckConstraint("length(name) > 0", name="ck_customers_name_nonempty"),
        CheckConstraint(
            "status IN ('draft','active','suspended','archived')",
            name="ck_customers_status",
        ),
        Index("uq_customers_external_key", "external_key", unique=True),
    )

    customer_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(Text)
    external_key: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="active")
    default_timezone: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Shipment(Base):
    __tablename__ = "shipments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open','ingesting','extracting','validating','routing','decided','closed')",
            name="ck_shipments_status",
        ),
        Index(
            "uq_shipments_customer_ref",
            "customer_id",
            "customer_shipment_ref",
            unique=True,
        ),
    )

    shipment_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    customer_id: Mapped[UUID] = mapped_column(ForeignKey("customers.customer_id"))
    customer_shipment_ref: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="open")
    priority: Mapped[int | None] = mapped_column(Integer)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    documents: Mapped[list[Document]] = relationship(back_populates="shipment")


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        CheckConstraint(
            "document_type IN ('commercial_invoice','bill_of_lading','packing_list','other')",
            name="ck_documents_type",
        ),
        CheckConstraint(
            "status IN ('registered','content_available','in_pipeline','extracted',"
            "'superseded','withdrawn')",
            name="ck_documents_status",
        ),
        CheckConstraint(
            "ingestion_channel IN ('upload','path','email','api')",
            name="ck_documents_channel",
        ),
    )

    document_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    shipment_id: Mapped[UUID] = mapped_column(ForeignKey("shipments.shipment_id"))
    document_type: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="registered")
    display_name: Mapped[str | None] = mapped_column(Text)
    source_system: Mapped[str | None] = mapped_column(Text)
    ingestion_channel: Mapped[str] = mapped_column(Text, default="upload")
    external_ref: Mapped[str | None] = mapped_column(Text)
    current_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("document_versions.document_version_id", use_alter=True)
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    shipment: Mapped[Shipment] = relationship(back_populates="documents")
    versions: Mapped[list[DocumentVersion]] = relationship(
        back_populates="document",
        foreign_keys="DocumentVersion.document_id",
    )


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        CheckConstraint("version_number > 0", name="ck_document_versions_number"),
        CheckConstraint("byte_size >= 0", name="ck_document_versions_size"),
        CheckConstraint("length(content_sha256) = 64", name="ck_document_versions_sha"),
        UniqueConstraint("document_id", "version_number", name="uq_document_versions_number"),
        UniqueConstraint(
            "shipment_id",
            "document_type",
            "content_sha256",
            name="uq_document_versions_shipment_type_hash",
        ),
    )

    document_version_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.document_id"))
    shipment_id: Mapped[UUID] = mapped_column(ForeignKey("shipments.shipment_id"))
    document_type: Mapped[str] = mapped_column(Text)
    version_number: Mapped[int] = mapped_column(Integer)
    storage_uri: Mapped[str] = mapped_column(Text)
    content_sha256: Mapped[str] = mapped_column(String(64))
    media_type: Mapped[str] = mapped_column(Text)
    byte_size: Mapped[int] = mapped_column(BigInteger)
    original_filename: Mapped[str | None] = mapped_column(Text)
    page_count: Mapped[int | None] = mapped_column(Integer)
    ingestion_idempotency_key: Mapped[str | None] = mapped_column(Text)
    source_message_id: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str | None] = mapped_column(Text)
    processor_name: Mapped[str | None] = mapped_column(Text)
    processor_version: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    document: Mapped[Document] = relationship(
        back_populates="versions",
        foreign_keys=[document_id],
    )


class VerificationRun(Base):
    __tablename__ = "verification_runs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued','running','succeeded','failed','cancelled')",
            name="ck_verification_runs_status",
        ),
    )

    verification_run_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    shipment_id: Mapped[UUID] = mapped_column(ForeignKey("shipments.shipment_id"))
    status: Mapped[str] = mapped_column(Text, default="queued")
    idempotency_key: Mapped[str | None] = mapped_column(Text)
    trigger: Mapped[str] = mapped_column(Text, default="api_upload")
    document_version_ids: Mapped[list[str]] = mapped_column(
        JSON().with_variant(postgresql.ARRAY(Uuid(as_uuid=False)), "postgresql"),
        default=list,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (
        CheckConstraint(
            "length(idempotency_key) BETWEEN 8 AND 128",
            name="ck_idempotency_key_length",
        ),
        UniqueConstraint(
            "principal_hash",
            "idempotency_key",
            name="uq_idempotency_principal_key",
        ),
    )

    idempotency_record_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    principal_hash: Mapped[str] = mapped_column(String(64))
    idempotency_key: Mapped[str] = mapped_column(String(128))
    request_fingerprint: Mapped[str] = mapped_column(String(64))
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.document_id"))
    shipment_id: Mapped[UUID] = mapped_column(ForeignKey("shipments.shipment_id"))
    verification_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("verification_runs.verification_run_id")
    )
    response_json: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class DecisionRecord(Base):
    """Append-only router disposition. One decision per verification run."""

    __tablename__ = "decisions"
    __table_args__ = (
        CheckConstraint(
            "disposition IN ('AUTO_APPROVE','HUMAN_REVIEW','AMENDMENT_REQUEST')",
            name="ck_decisions_disposition",
        ),
        CheckConstraint(
            "actor_type IN ('router','system_failsafe')",
            name="ck_decisions_actor_type",
        ),
        CheckConstraint(
            "actor_type <> 'system_failsafe' OR disposition <> 'AUTO_APPROVE'",
            name="ck_decisions_failsafe_no_auto_approve",
        ),
        UniqueConstraint("verification_run_id", name="uq_decisions_verification_run"),
    )

    decision_id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    verification_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("verification_runs.verification_run_id"),
        nullable=False,
    )
    shipment_id: Mapped[UUID] = mapped_column(ForeignKey("shipments.shipment_id"), nullable=False)
    document_id: Mapped[UUID] = mapped_column(ForeignKey("documents.document_id"), nullable=False)
    document_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("document_versions.document_version_id"),
        nullable=False,
    )
    validation_result_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    disposition: Mapped[str] = mapped_column(Text, nullable=False)
    policy_id: Mapped[str | None] = mapped_column(Text)
    policy_version: Mapped[str] = mapped_column(Text, nullable=False)
    reason_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
    reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    triggering_check_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    safety_constraints_applied: Mapped[list[str]] = mapped_column(JSON, default=list)
    confidence: Mapped[float | None] = mapped_column(Float)
    actor_type: Mapped[str] = mapped_column(Text, nullable=False, default="router")
    agent_version: Mapped[str | None] = mapped_column(Text)
    trace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    reasoning_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    risk_flags: Mapped[list[str] | None] = mapped_column(JSON)
    supersedes_decision_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("decisions.decision_id"),
    )
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    input_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    llm_rationale: Mapped[str | None] = mapped_column(Text)
    evidence_refs: Mapped[list[str]] = mapped_column(JSON, default=list)
    routing_rule_version: Mapped[str | None] = mapped_column(Text)
