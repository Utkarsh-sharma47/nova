"""ExtractorService — LLM-backed field extraction behind LLMPort."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from uuid import UUID, uuid4

from nova import __version__ as NOVA_VERSION
from nova.contracts.common import (
    DocumentContent,
    FieldPresence,
    ModelMetadata,
    StageError,
    UncertaintyFlag,
    UsageMetrics,
)
from nova.contracts.extraction import (
    ExtractedField,
    ExtractionRequest,
    ExtractionResult,
    ExtractionStatus,
)
from nova.extraction import observability as obs
from nova.extraction.fields import assert_supported_fields
from nova.extraction.parsing import normalize_field_dicts, parse_llm_fields_payload
from nova.extraction.prompts import PROMPT_ID, PROMPT_VERSION, build_extraction_prompt
from nova.llm.errors import LLMError, LLMOutputError, LLMProviderError, LLMTimeoutError
from nova.llm.port import LLMImagePart, LLMMessage, LLMPort, LLMRequest

MAX_RETRIES = 2  # 3 total attempts
DEFAULT_TIMEOUT_MS = 60_000
AGENT_VERSION = NOVA_VERSION


class ExtractorService:
    """Produce ExtractionResult from DocumentContent via LLMPort + schema validation."""

    def __init__(
        self,
        llm: LLMPort,
        *,
        max_retries: int = MAX_RETRIES,
        agent_version: str = AGENT_VERSION,
        default_provider: str = "mock",
        default_model: str = "mock-extractor-v1",
    ) -> None:
        self._llm = llm
        self._max_retries = max_retries
        self._agent_version = agent_version
        self._default_provider = default_provider
        self._default_model = default_model

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        started = time.perf_counter()
        agent_execution_id = request.agent_execution_id or uuid4()
        run_id = request.run_id or request.trace_id
        provider = self._default_provider
        model = self._default_model
        attempt = 0
        last_error: StageError | None = None
        total_in = 0
        total_out = 0

        try:
            assert_supported_fields(request.required_fields)
        except ValueError as exc:
            return self._failed(
                request,
                agent_execution_id=agent_execution_id,
                run_id=run_id,
                code="UNSUPPORTED_FIELD",
                message=str(exc),
                retryable=False,
                started=started,
                attempt=0,
                provider=provider,
                model=model,
            )

        content = request.content
        if content is None:
            return self._failed(
                request,
                agent_execution_id=agent_execution_id,
                run_id=run_id,
                code="DOCUMENT_CONTENT_MISSING",
                message="Extraction requires DocumentContent",
                retryable=False,
                started=started,
                attempt=0,
                provider=provider,
                model=model,
            )

        if not _has_extractable_input(content):
            return self._failed(
                request,
                agent_execution_id=agent_execution_id,
                run_id=run_id,
                code="DOCUMENT_UNREADABLE",
                message="Document has no extractable text or image content",
                retryable=False,
                started=started,
                attempt=0,
                provider=provider,
                model=model,
                fields=_all_unknown(request, agent_execution_id, run_id),
            )

        prompt = build_extraction_prompt(
            document_type=request.document_type,
            required_fields=request.required_fields,
            content=content,
        )
        obs.log_start(
            run_id=run_id,
            document_id=request.document_id,
            trace_id=request.trace_id,
            agent_execution_id=agent_execution_id,
            prompt_version=prompt.prompt_version,
            provider=provider,
            model=model,
        )

        deadline = started + (request.timeout_ms / 1000.0)
        max_attempts = self._max_retries + 1

        while attempt < max_attempts:
            attempt += 1
            remaining_ms = int(max(1, (deadline - time.perf_counter()) * 1000))
            if time.perf_counter() >= deadline:
                last_error = StageError(
                    code="TIMEOUT",
                    message="Extraction timeout budget exhausted",
                    retryable=False,
                )
                break
            try:
                llm_response = self._llm.complete(
                    LLMRequest(
                        messages=[
                            LLMMessage(role="system", content=prompt.system),
                            LLMMessage(role="user", content=prompt.user),
                        ],
                        images=[
                            LLMImagePart(
                                media_type=image.media_type,
                                data_base64=image.data_base64,
                            )
                            for image in content.images
                        ],
                        response_format="json",
                        temperature=prompt.temperature,
                        timeout_ms=remaining_ms,
                        metadata={
                            "prompt_id": prompt.prompt_id,
                            "prompt_version": prompt.prompt_version,
                            "agent_version": self._agent_version,
                            "run_id": str(run_id),
                            "attempt": attempt,
                        },
                    )
                )
            except LLMTimeoutError as exc:
                last_error = StageError(
                    code=exc.code,
                    message=exc.message,
                    retryable=True,
                    details=exc.details,
                )
                if attempt >= max_attempts or time.perf_counter() >= deadline:
                    break
                continue
            except LLMProviderError as exc:
                last_error = StageError(
                    code=exc.code,
                    message=exc.message,
                    retryable=exc.retryable,
                    details=exc.details,
                )
                if not exc.retryable or attempt >= max_attempts:
                    break
                continue
            except LLMError as exc:
                last_error = StageError(
                    code=exc.code,
                    message=exc.message,
                    retryable=exc.retryable,
                    details=exc.details,
                )
                if not exc.retryable or attempt >= max_attempts:
                    break
                continue

            provider = llm_response.provider
            model = llm_response.model
            total_in += llm_response.input_tokens or 0
            total_out += llm_response.output_tokens or 0

            try:
                raw_fields = parse_llm_fields_payload(llm_response.content)
                fields, parse_warnings = normalize_field_dicts(
                    raw_fields,
                    required_fields=request.required_fields,
                    trace_id=request.trace_id,
                    document_id=request.document_id,
                    document_version_id=request.document_version_id,
                    shipment_id=request.shipment_id,
                    run_id=run_id,
                    agent_execution_id=agent_execution_id,
                    content=content,
                )
            except LLMOutputError as exc:
                last_error = StageError(
                    code=exc.code,
                    message=exc.message,
                    retryable=True,
                    details=exc.details,
                )
                if attempt >= max_attempts:
                    break
                continue

            status = _status_for_fields(fields)
            duration_ms = (time.perf_counter() - started) * 1000
            result = ExtractionResult(
                contract_version=request.contract_version,
                trace_id=request.trace_id,
                run_id=run_id,
                request_id=request.request_id,
                agent_execution_id=agent_execution_id,
                document_id=request.document_id,
                document_version_id=request.document_version_id,
                shipment_id=request.shipment_id,
                customer_id=request.customer_id,
                created_at=datetime.now(UTC),
                status=status,
                fields=fields,
                document_type_detected=request.document_type,
                warnings=list(content.warnings) + parse_warnings,
                errors=[],
                model_metadata=ModelMetadata(
                    provider=provider,
                    model=model,
                    prompt_id=PROMPT_ID,
                    prompt_version=PROMPT_VERSION,
                    agent_version=self._agent_version,
                    temperature=prompt.temperature,
                    other_config={"max_retries": self._max_retries, "attempt": attempt},
                    invoked_at=datetime.now(UTC),
                ),
                usage=UsageMetrics(
                    input_tokens=total_in or None,
                    output_tokens=total_out or None,
                    latency_ms=int(duration_ms),
                    attempt=attempt,
                ),
            )
            obs.log_complete(
                run_id=run_id,
                document_id=request.document_id,
                trace_id=request.trace_id,
                agent_execution_id=agent_execution_id,
                prompt_version=PROMPT_VERSION,
                provider=provider,
                model=model,
                status=status.value,
                duration_ms=duration_ms,
                attempt=attempt,
            )
            return result

        duration_ms = (time.perf_counter() - started) * 1000
        error = last_error or StageError(
            code="RETRY_EXHAUSTED",
            message="Extraction failed after bounded retries",
            retryable=False,
        )
        if attempt >= max_attempts and error.retryable:
            error = StageError(
                code="RETRY_EXHAUSTED",
                message=f"Retry exhausted after {attempt} attempts: {error.message}",
                retryable=False,
                details={"last_code": error.code},
            )
        obs.log_failure(
            run_id=run_id,
            document_id=request.document_id,
            trace_id=request.trace_id,
            agent_execution_id=agent_execution_id,
            prompt_version=PROMPT_VERSION,
            provider=provider,
            model=model,
            error_code=error.code,
            duration_ms=duration_ms,
            attempt=attempt,
        )
        return ExtractionResult(
            contract_version=request.contract_version,
            trace_id=request.trace_id,
            run_id=run_id,
            request_id=request.request_id,
            agent_execution_id=agent_execution_id,
            document_id=request.document_id,
            document_version_id=request.document_version_id,
            shipment_id=request.shipment_id,
            customer_id=request.customer_id,
            created_at=datetime.now(UTC),
            status=ExtractionStatus.FAILED,
            fields=[],
            warnings=[],
            errors=[error],
            model_metadata=ModelMetadata(
                provider=provider,
                model=model,
                prompt_id=PROMPT_ID,
                prompt_version=PROMPT_VERSION,
                agent_version=self._agent_version,
                other_config={"attempt": attempt},
                invoked_at=datetime.now(UTC),
            ),
            usage=UsageMetrics(
                input_tokens=total_in or None,
                output_tokens=total_out or None,
                latency_ms=int(duration_ms),
                attempt=attempt or None,
            ),
            error_code=error.code,
            error_message=error.message,
        )

    def _failed(
        self,
        request: ExtractionRequest,
        *,
        agent_execution_id: UUID,
        run_id: UUID,
        code: str,
        message: str,
        retryable: bool,
        started: float,
        attempt: int,
        provider: str,
        model: str,
        fields: list[ExtractedField] | None = None,
    ) -> ExtractionResult:
        duration_ms = (time.perf_counter() - started) * 1000
        error = StageError(code=code, message=message, retryable=retryable)
        obs.log_failure(
            run_id=run_id,
            document_id=request.document_id,
            trace_id=request.trace_id,
            agent_execution_id=agent_execution_id,
            prompt_version=PROMPT_VERSION,
            provider=provider,
            model=model,
            error_code=code,
            duration_ms=duration_ms,
            attempt=attempt,
        )
        return ExtractionResult(
            contract_version=request.contract_version,
            trace_id=request.trace_id,
            run_id=run_id,
            request_id=request.request_id,
            agent_execution_id=agent_execution_id,
            document_id=request.document_id,
            document_version_id=request.document_version_id,
            shipment_id=request.shipment_id,
            customer_id=request.customer_id,
            created_at=datetime.now(UTC),
            status=ExtractionStatus.FAILED,
            fields=fields or [],
            warnings=[],
            errors=[error],
            model_metadata=ModelMetadata(
                provider=provider,
                model=model,
                prompt_id=PROMPT_ID,
                prompt_version=PROMPT_VERSION,
                agent_version=self._agent_version,
                invoked_at=datetime.now(UTC),
            ),
            usage=UsageMetrics(latency_ms=int(duration_ms), attempt=attempt or None),
            error_code=code,
            error_message=message,
        )


def _has_extractable_input(content: DocumentContent) -> bool:
    if content.text and content.text.strip():
        return True
    if content.page_texts and any(page.strip() for page in content.page_texts):
        return True
    if content.images:
        return True
    return False


def _status_for_fields(fields: list[ExtractedField]) -> ExtractionStatus:
    if not fields:
        return ExtractionStatus.FAILED
    known = sum(1 for field in fields if field.presence == FieldPresence.KNOWN)
    if known == len(fields) and all(
        field.uncertainty
        not in {
            UncertaintyFlag.SCHEMA_REPAIR,
            UncertaintyFlag.PARTIAL_EVIDENCE,
        }
        for field in fields
    ):
        return ExtractionStatus.SUCCEEDED
    if known == 0 and all(field.presence == FieldPresence.UNKNOWN for field in fields):
        # Still a usable partial for fail-safe routing when model returned unknowns.
        return ExtractionStatus.PARTIAL
    return ExtractionStatus.PARTIAL


def _all_unknown(
    request: ExtractionRequest,
    agent_execution_id: UUID,
    run_id: UUID,
) -> list[ExtractedField]:
    from nova.contracts.common import ConfidenceBand, ConfidenceSource, UncertaintyCode

    return [
        ExtractedField(
            trace_id=request.trace_id,
            run_id=run_id,
            agent_execution_id=agent_execution_id,
            document_id=request.document_id,
            document_version_id=request.document_version_id,
            shipment_id=request.shipment_id,
            field_name=name,
            value=None,
            presence=FieldPresence.UNKNOWN,
            confidence=None,
            confidence_band=ConfidenceBand.UNKNOWN,
            confidence_source=ConfidenceSource.UNKNOWN,
            uncertainty=UncertaintyFlag.OTHER,
            uncertainty_codes=[UncertaintyCode.UNKNOWN],
            evidence=[],
            warnings=["no_extractable_text"],
        )
        for name in request.required_fields
    ]
