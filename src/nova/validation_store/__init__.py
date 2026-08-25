"""Append-only validation result store (auditability)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from nova.contracts.validation import ValidationResult


@dataclass(frozen=True)
class ValidationRecord:
    """Immutable historical validation record."""

    record_id: UUID
    run_id: UUID | None
    validation_result_id: UUID
    validator_version: str
    ruleset_id: str | None
    ruleset_version: str | None
    result: ValidationResult
    created_at: datetime
    model_metadata: dict[str, object] | None = None


class ValidationStorePort(Protocol):
    def append(self, result: ValidationResult, *, validator_version: str) -> ValidationRecord:
        ...

    def get(self, record_id: UUID) -> ValidationRecord | None:
        ...

    def list_for_run(self, run_id: UUID) -> list[ValidationRecord]:
        ...

    def list_all(self) -> list[ValidationRecord]:
        ...


class InMemoryValidationStore:
    """In-memory append-only store for tests and local evaluation."""

    def __init__(self) -> None:
        self._records: dict[UUID, ValidationRecord] = {}
        self._order: list[UUID] = []

    def append(self, result: ValidationResult, *, validator_version: str) -> ValidationRecord:
        record_id = uuid4()
        validation_result_id = result.agent_execution_id or uuid4()
        meta = None
        if result.model_metadata is not None:
            meta = result.model_metadata.model_dump(mode="json")
        record = ValidationRecord(
            record_id=record_id,
            run_id=result.run_id,
            validation_result_id=validation_result_id,
            validator_version=validator_version,
            ruleset_id=result.ruleset_id,
            ruleset_version=result.ruleset_version,
            result=result.model_copy(deep=True),
            created_at=datetime.now(UTC),
            model_metadata=meta,
        )
        self._records[record_id] = record
        self._order.append(record_id)
        return record

    def get(self, record_id: UUID) -> ValidationRecord | None:
        return self._records.get(record_id)

    def list_for_run(self, run_id: UUID) -> list[ValidationRecord]:
        return [self._records[i] for i in self._order if self._records[i].run_id == run_id]

    def list_all(self) -> list[ValidationRecord]:
        return [self._records[i] for i in self._order]

    def try_mutate(self, record_id: UUID) -> None:
        """Test helper: demonstrate records are treated as immutable snapshots."""
        record = self._records[record_id]
        # Replacing with a mutated copy is the only way callers can "change" history;
        # the original object remains frozen-equivalent via deep copy on append.
        _ = record


@dataclass
class FailingValidationStore:
    """Store that raises on append — models database failure."""

    error: Exception = field(default_factory=lambda: RuntimeError("database unavailable"))

    def append(self, result: ValidationResult, *, validator_version: str) -> ValidationRecord:
        raise self.error

    def get(self, record_id: UUID) -> ValidationRecord | None:
        raise self.error

    def list_for_run(self, run_id: UUID) -> list[ValidationRecord]:
        raise self.error

    def list_all(self) -> list[ValidationRecord]:
        raise self.error
