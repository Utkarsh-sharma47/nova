"""Phase 3+ HTTP routes including Phase 8 query and Phase 9 ops reads."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Header, Query, Request, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from nova.api.deps import (
    authenticate,
    ingestion_service,
    ops_service,
    query_service,
    settings,
)
from nova.application.ingestion import IngestCommand, IngestionService
from nova.application.ops import OpsService
from nova.contracts.query import QueryRequest, QueryResponse
from nova.domain.errors import MissingIdempotencyKey, ValidationFailure
from nova.infrastructure.storage import LocalFilesystemStorage
from nova.observability.metrics import render_metrics
from nova.persistence.database import database_ready
from nova.query.service import QueryService

router = APIRouter()


class CreateCustomerBody(BaseModel):
    name: str = Field(min_length=1, max_length=200)


@router.get("/health", tags=["ops"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/metrics", tags=["ops"])
def metrics() -> Response:
    body, content_type = render_metrics()
    return Response(content=body, media_type=content_type)


@router.get("/ready", tags=["ops"])
def ready(request: Request) -> JSONResponse:
    database = database_ready()
    storage = LocalFilesystemStorage(settings(request).document_storage_path).is_writable()
    checks = {
        "database": "ok" if database else "fail",
        "object_storage": "ok" if storage else "fail",
    }
    if database and storage:
        return JSONResponse({"status": "ready", "checks": checks})
    trace_id = str(request.state.trace_id)
    return JSONResponse(
        status_code=503,
        content={
            "status": "not_ready",
            "checks": checks,
            "error": {
                "code": "DEPENDENCY_UNAVAILABLE",
                "message": "One or more required dependencies are unavailable.",
                "details": {"checks": [name for name, value in checks.items() if value == "fail"]},
                "trace_id": trace_id,
                "retryable": True,
            },
        },
    )


@router.post("/v1/customers", status_code=201, tags=["customers"])
def create_customer(
    body: CreateCustomerBody,
    request: Request,
    _principal: Annotated[str, Depends(authenticate)],
    service: Annotated[OpsService, Depends(ops_service)],
) -> dict[str, object]:
    return service.create_customer(name=body.name, trace_id=str(request.state.trace_id))


@router.get("/v1/ops/summary", tags=["ops"])
def ops_summary(
    request: Request,
    customer_id: Annotated[UUID, Query()],
    _principal: Annotated[str, Depends(authenticate)],
    service: Annotated[OpsService, Depends(ops_service)],
) -> dict[str, object]:
    return service.summary(customer_id, trace_id=str(request.state.trace_id))


@router.post("/v1/documents", status_code=202, tags=["documents"])
async def ingest_document(
    request: Request,
    customer_id: Annotated[UUID, Form()],
    principal: Annotated[str, Depends(authenticate)],
    service: Annotated[IngestionService, Depends(ingestion_service)],
    file: Annotated[UploadFile | None, File()] = None,
    source_path: Annotated[str | None, Form()] = None,
    shipment_id: Annotated[UUID | None, Form()] = None,
    document_type: Annotated[str, Form()] = "UNKNOWN",
    external_ref: Annotated[str | None, Form()] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> dict[str, object]:
    if not idempotency_key:
        raise MissingIdempotencyKey()
    if (file is None) == (source_path is None):
        raise ValidationFailure("Exactly one of file or source_path is required.")
    if file is not None:
        blob = await file.read()
        filename = file.filename or ""
        media_type = file.content_type or "application/octet-stream"
    else:
        assert source_path is not None
        blob, filename, media_type = service.load_staged(source_path)
    return service.ingest(
        IngestCommand(
            blob=blob,
            filename=filename,
            media_type=media_type,
            customer_id=customer_id,
            shipment_id=shipment_id,
            document_type=document_type,
            external_ref=external_ref,
            idempotency_key=idempotency_key,
            principal=principal,
            trace_id=str(request.state.trace_id),
        )
    )


@router.get("/v1/documents", tags=["documents"])
def list_documents(
    request: Request,
    customer_id: Annotated[UUID, Query()],
    _principal: Annotated[str, Depends(authenticate)],
    service: Annotated[OpsService, Depends(ops_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict[str, object]:
    return service.list_documents(
        customer_id,
        limit=limit,
        trace_id=str(request.state.trace_id),
    )


@router.get("/v1/documents/{document_id}", tags=["documents"])
def get_document(
    document_id: UUID,
    request: Request,
    _principal: Annotated[str, Depends(authenticate)],
    service: Annotated[IngestionService, Depends(ingestion_service)],
) -> dict[str, object]:
    return service.get_document(document_id, str(request.state.trace_id))


@router.get("/v1/documents/{document_id}/validation", tags=["documents"])
def get_document_validation(
    document_id: UUID,
    request: Request,
    _principal: Annotated[str, Depends(authenticate)],
    service: Annotated[IngestionService, Depends(ingestion_service)],
) -> dict[str, object]:
    return service.get_validation(document_id, str(request.state.trace_id))


@router.get("/v1/documents/{document_id}/decision", tags=["documents"])
def get_document_decision(
    document_id: UUID,
    request: Request,
    _principal: Annotated[str, Depends(authenticate)],
    service: Annotated[IngestionService, Depends(ingestion_service)],
) -> dict[str, object]:
    return service.get_decision(document_id, str(request.state.trace_id))


@router.get("/v1/shipments/{shipment_id}", tags=["shipments"])
def get_shipment(
    shipment_id: UUID,
    request: Request,
    _principal: Annotated[str, Depends(authenticate)],
    service: Annotated[IngestionService, Depends(ingestion_service)],
) -> dict[str, object]:
    return service.get_shipment(shipment_id, str(request.state.trace_id))


@router.get("/v1/shipments/{shipment_id}/validation", tags=["shipments"])
def get_shipment_validation(
    shipment_id: UUID,
    request: Request,
    _principal: Annotated[str, Depends(authenticate)],
    service: Annotated[IngestionService, Depends(ingestion_service)],
) -> dict[str, object]:
    """Convenience alias: validation for the latest document on the shipment."""
    shipment = service.get_shipment(shipment_id, str(request.state.trace_id))
    docs = shipment.get("documents") or []
    if not docs:
        from nova.domain.errors import ValidationNotFound

        raise ValidationNotFound(details={"shipment_id": str(shipment_id)})
    document_id = UUID(str(docs[0]["document_id"]))
    return service.get_validation(document_id, str(request.state.trace_id))


@router.get("/v1/shipments/{shipment_id}/decision", tags=["shipments"])
def get_shipment_decision(
    shipment_id: UUID,
    request: Request,
    _principal: Annotated[str, Depends(authenticate)],
    service: Annotated[IngestionService, Depends(ingestion_service)],
) -> dict[str, object]:
    """Convenience alias: decision for the latest document on the shipment."""
    shipment = service.get_shipment(shipment_id, str(request.state.trace_id))
    docs = shipment.get("documents") or []
    if not docs:
        from nova.domain.errors import DecisionNotFound

        raise DecisionNotFound(details={"shipment_id": str(shipment_id)})
    document_id = UUID(str(docs[0]["document_id"]))
    return service.get_decision(document_id, str(request.state.trace_id))


@router.post("/v1/query", tags=["query"])
def post_query(
    body: QueryRequest,
    request: Request,
    _principal: Annotated[str, Depends(authenticate)],
    service: Annotated[QueryService, Depends(query_service)],
) -> QueryResponse:
    return service.answer(body, trace_id=str(request.state.trace_id))
