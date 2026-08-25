"""Validator Agent package (public API)."""

from nova.agents.validator import (
    ENGINE_VERSION,
    VALIDATOR_VERSION,
    ValidatorAgent,
    evaluate_deterministic_rule,
)
from nova.validation_store import (
    FailingValidationStore,
    InMemoryValidationStore,
    ValidationRecord,
    ValidationStorePort,
)

try:
    from nova.validator.codes import ValidationCode
except ImportError:  # pragma: no cover
    ValidationCode = None  # type: ignore[misc, assignment]

try:
    from nova.validator.version import RULES_ENGINE_VERSION
except ImportError:  # pragma: no cover
    RULES_ENGINE_VERSION = ENGINE_VERSION

__all__ = [
    "ENGINE_VERSION",
    "FailingValidationStore",
    "InMemoryValidationStore",
    "RULES_ENGINE_VERSION",
    "VALIDATOR_VERSION",
    "ValidationCode",
    "ValidationRecord",
    "ValidationStorePort",
    "ValidatorAgent",
    "evaluate_deterministic_rule",
]
