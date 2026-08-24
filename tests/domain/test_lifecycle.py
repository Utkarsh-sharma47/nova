"""Domain lifecycle tests."""

from __future__ import annotations

import pytest

from nova.domain.lifecycle import (
    DocumentStatus,
    DocumentType,
    InvalidDocumentTransitionError,
    assert_document_transition,
    parse_wire_document_type,
    to_api_status,
)


def test_allowed_transition() -> None:
    assert_document_transition(DocumentStatus.RECEIVED, DocumentStatus.STORED)


def test_disallowed_transition() -> None:
    with pytest.raises(InvalidDocumentTransitionError):
        assert_document_transition(DocumentStatus.RECEIVED, DocumentStatus.PROCESSED)


def test_parse_wire_document_type() -> None:
    assert parse_wire_document_type("INVOICE") == DocumentType.COMMERCIAL_INVOICE
    assert parse_wire_document_type("bill_of_lading") == DocumentType.BILL_OF_LADING
    assert parse_wire_document_type(None) == DocumentType.OTHER


def test_parse_wire_document_type_rejects_unknown() -> None:
    with pytest.raises(ValueError):
        parse_wire_document_type("not-a-type")


def test_to_api_status_mapping() -> None:
    assert to_api_status(DocumentStatus.STORED).value == "ACCEPTED"
    assert to_api_status(DocumentStatus.FAILED).value == "FAILED"
