"""Dataset loading for Extractor golden / regression fixtures."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DATASET_ID = "extractor-golden"
DATASET_REVISION = "extractor-regression-v1"

# Default path relative to repository root.
DEFAULT_FIXTURES_ROOT = Path("fixtures/evaluation/extractor")


@dataclass(frozen=True)
class GoldField:
    presence: str
    value: Any | None = None
    require_evidence: bool = False
    max_confidence: float | None = None
    min_confidence: float | None = None
    uncertainty_in: tuple[str, ...] | None = None


@dataclass(frozen=True)
class ExtractorCase:
    case_id: str
    category: str
    document_type: str
    required_fields: list[str]
    document_text: str
    gold_fields: dict[str, GoldField]
    expected_status: tuple[str, ...]
    llm_response: str | None
    llm_error: str | None = None
    expect_schema_valid: bool = True
    expect_fabrication: bool = False
    unsupported_fields_allowed: bool = False
    notes: str = ""
    path: Path | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)

    @property
    def in_regression(self) -> bool:
        # Fixed regression dataset: all suite cases are regression-tagged by default.
        return "regression" in self.tags or not self.tags


def default_fixtures_root(repo_root: Path | None = None) -> Path:
    root = repo_root or Path.cwd()
    return root / DEFAULT_FIXTURES_ROOT


def load_extractor_dataset(
    fixtures_root: Path | None = None,
    *,
    categories: set[str] | None = None,
) -> tuple[dict[str, Any], list[ExtractorCase]]:
    root = fixtures_root or default_fixtures_root()
    manifest_path = root / "dataset.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Missing dataset manifest: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cases: list[ExtractorCase] = []
    for entry in manifest.get("cases", []):
        case_id = entry["case_id"]
        case_dir = root / "cases" / case_id
        case = _load_case(case_dir, entry)
        if categories is not None and case.category not in categories:
            continue
        cases.append(case)
    return manifest, cases


def _load_case(case_dir: Path, entry: dict[str, Any]) -> ExtractorCase:
    gold_path = case_dir / "gold.json"
    doc_path = case_dir / "document.txt"
    llm_path = case_dir / "llm_response.json"
    llm_raw_path = case_dir / "llm_response.txt"
    meta = json.loads(gold_path.read_text(encoding="utf-8")) if gold_path.is_file() else {}
    merged = {**entry, **meta}

    document_text = ""
    if doc_path.is_file():
        document_text = doc_path.read_text(encoding="utf-8")

    llm_response: str | None = None
    if llm_path.is_file():
        # Keep as compact JSON string for MockLLM.
        llm_response = json.dumps(json.loads(llm_path.read_text(encoding="utf-8")))
    elif llm_raw_path.is_file():
        llm_response = llm_raw_path.read_text(encoding="utf-8")

    gold_fields: dict[str, GoldField] = {}
    for name, spec in (merged.get("fields") or {}).items():
        gold_fields[name] = GoldField(
            presence=str(spec["presence"]),
            value=spec.get("value"),
            require_evidence=bool(spec.get("require_evidence", False)),
            max_confidence=spec.get("max_confidence"),
            min_confidence=spec.get("min_confidence"),
            uncertainty_in=tuple(spec["uncertainty_in"])
            if spec.get("uncertainty_in")
            else None,
        )

    expected_status = merged.get("expected_status") or ["SUCCEEDED", "PARTIAL", "FAILED"]
    if isinstance(expected_status, str):
        expected_status = [expected_status]

    return ExtractorCase(
        case_id=str(merged["case_id"]),
        category=str(merged.get("category") or entry.get("category") or "unspecified"),
        document_type=str(merged.get("document_type") or "COMMERCIAL_INVOICE"),
        required_fields=list(merged.get("required_fields") or list(gold_fields.keys())),
        document_text=document_text,
        gold_fields=gold_fields,
        expected_status=tuple(str(s) for s in expected_status),
        llm_response=llm_response,
        llm_error=merged.get("llm_error"),
        expect_schema_valid=bool(merged.get("expect_schema_valid", True)),
        expect_fabrication=bool(merged.get("expect_fabrication", False)),
        unsupported_fields_allowed=bool(merged.get("unsupported_fields_allowed", False)),
        notes=str(merged.get("notes") or ""),
        path=case_dir,
        tags=tuple(merged.get("tags") or entry.get("tags") or ("regression",)),
    )
