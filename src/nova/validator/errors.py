"""Validator errors."""

from __future__ import annotations

from typing import Any


class ValidatorError(Exception):
    code: str = "VALIDATOR_ERROR"
    retryable: bool = False

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class InvalidExtractionError(ValidatorError):
    code = "EXTRACTION_INVALID"


class InvalidRuleExpressionError(ValidatorError):
    code = "RULE_EXPRESSION_INVALID"


class ValidatorTimeoutError(ValidatorError):
    code = "VALIDATOR_TIMEOUT"


class ValidatorPersistenceError(ValidatorError):
    code = "VALIDATOR_PERSISTENCE_FAILURE"
    retryable = True
