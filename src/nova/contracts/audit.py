"""Audit event contract."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field

from nova.contracts.common import ContractModel


class ActorType(StrEnum):
    USER = "USER"
    SYSTEM = "SYSTEM"
    AGENT = "AGENT"
    ANONYMOUS = "ANONYMOUS"


class AuditEvent(ContractModel):
    contract_version: str = "1.0.0"
    event_type: str = Field(min_length=1)
    actor_type: ActorType
    actor_id: str | None = None
    entity_type: str | None = None
    entity_id: UUID | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    trace_id: UUID | None = None
    request_id: UUID | None = None
    created_at: datetime
