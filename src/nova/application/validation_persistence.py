"""SQL-backed append-only validation store (Phase 7)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from nova.contracts.validation import ValidationOutcome, ValidationResult, ValidationStatus
from nova.persistence.models import ValidationRecordRow
from nova.validation_store import ValidationRecord


def aggregate_outcome(result: ValidationResult) -> str | None:
    if result.status is ValidationStatus.FAILED:
        if result.mismatch_count > 0:
            return ValidationOutcome.MISMATCH.value
        if result.uncertain_count > 0:
            return ValidationOutcome.UNCERTAIN.value
        return None
    if result.mismatch_count > 0:
        return ValidationOutcome.MISMATCH.value
    if result.uncertain_count > 0:
        return ValidationOutcome.UNCERTAIN.value
    return ValidationOutcome.MATCH.value


class SqlValidationStore:
    """Persist ValidationResult JSON append-only; one row per verification run."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def append(self, result: ValidationResult, *, validator_version: str) -> ValidationRecord:
        run_id = result.run_id
        if run_id is None:
            raise ValueError("ValidationResult.run_id required for persistence")
        existing = self.find_by_run(run_id)
        if existing is not None:
            return existing

        validation_id = result.agent_execution_id or uuid4()
        status = (
            "completed" if result.status is ValidationStatus.COMPLETED else "failed"
        )
        aggregate = aggregate_outcome(result)
        row = ValidationRecordRow(
            validation_id=validation_id,
            verification_run_id=run_id,
            shipment_id=result.shipment_id,
            document_id=result.document_id,
            document_version_id=result.document_version_id,
            status=status,
            aggregate_result=aggregate,
            ruleset_id=result.ruleset_id,
            ruleset_version=result.ruleset_version,
            engine_version=result.engine_version,
            validator_version=validator_version,
            result_json=result.model_dump(mode="json"),
            summary_json={
                "match": result.match_count,
                "mismatch": result.mismatch_count,
                "uncertain": result.uncertain_count,
            },
            error_code=result.error_code,
            error_message=result.error_message,
            trace_id=result.trace_id,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
        self.session.add(row)
        self.session.flush()
        return ValidationRecord(
            record_id=row.validation_id,
            run_id=run_id,
            validation_result_id=row.validation_id,
            validator_version=validator_version,
            ruleset_id=result.ruleset_id,
            ruleset_version=result.ruleset_version,
            result=result.model_copy(deep=True),
            created_at=row.created_at,
            model_metadata=(
                result.model_metadata.model_dump(mode="json")
                if result.model_metadata is not None
                else None
            ),
        )

    def get(self, record_id: UUID) -> ValidationRecord | None:
        row = self.session.get(ValidationRecordRow, record_id)
        if row is None:
            return None
        return self._to_record(row)

    def list_for_run(self, run_id: UUID) -> list[ValidationRecord]:
        row = self.find_row_by_run(run_id)
        return [self._to_record(row)] if row is not None else []

    def list_all(self) -> list[ValidationRecord]:
        rows = self.session.scalars(select(ValidationRecordRow)).all()
        return [self._to_record(row) for row in rows]

    def find_by_run(self, run_id: UUID) -> ValidationRecord | None:
        row = self.find_row_by_run(run_id)
        return self._to_record(row) if row is not None else None

    def find_row_by_run(self, run_id: UUID) -> ValidationRecordRow | None:
        return self.session.scalar(
            select(ValidationRecordRow).where(ValidationRecordRow.verification_run_id == run_id)
        )

    def find_row_by_document(self, document_id: UUID) -> ValidationRecordRow | None:
        return self.session.scalar(
            select(ValidationRecordRow)
            .where(ValidationRecordRow.document_id == document_id)
            .order_by(ValidationRecordRow.created_at.desc())
            .limit(1)
        )

    def _to_record(self, row: ValidationRecordRow) -> ValidationRecord:
        result = ValidationResult.model_validate(row.result_json)
        return ValidationRecord(
            record_id=row.validation_id,
            run_id=row.verification_run_id,
            validation_result_id=row.validation_id,
            validator_version=row.validator_version,
            ruleset_id=row.ruleset_id,
            ruleset_version=row.ruleset_version,
            result=result,
            created_at=row.created_at,
            model_metadata=row.summary_json,
        )
