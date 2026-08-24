"""Document ingestion routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, File, Form, Header, UploadFile
from fastapi.responses import JSONResponse

from nova.api.deps import AuthTokenDep, SessionDep, SettingsDep, StorageDep
from nova.domain.errors import BadRequestError
from nova.observability.logging import get_trace_id
from nova.services.ingestion import DocumentIngestionService

router = APIRouter(prefix="/v1", tags=["documents"])

_OPTIONAL_FILE = File(None)


@router.post("/documents")
async def ingest_document(
    session: SessionDep,
    storage: StorageDep,
    settings: SettingsDep,
    token: AuthTokenDep,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    file: UploadFile | None = _OPTIONAL_FILE,
    customer_id: str = Form(...),
    shipment_id: str | None = Form(default=None),
    document_type: str | None = Form(default=None),
    external_ref: str | None = Form(default=None),
    source_path: str | None = Form(default=None),
) -> JSONResponse:
    try:
        customer_uuid = UUID(customer_id)
    except ValueError as exc:
        raise BadRequestError(
            "customer_id must be a UUID.",
            details={"customer_id": customer_id},
        ) from exc

    shipment_uuid: UUID | None = None
    if shipment_id:
        try:
            shipment_uuid = UUID(shipment_id)
        except ValueError as exc:
            raise BadRequestError(
                "shipment_id must be a UUID.",
                details={"shipment_id": shipment_id},
            ) from exc

    file_bytes: bytes | None = None
    filename: str | None = None
    media_type: str | None = None
    if file is not None and file.filename:
        file_bytes = await file.read()
        filename = file.filename
        media_type = file.content_type

    service = DocumentIngestionService(
        session=session,
        storage=storage,
        settings=settings,
        principal_token=token,
    )
    result = await service.ingest(
        idempotency_key=idempotency_key,
        customer_id=customer_uuid,
        file_bytes=file_bytes,
        filename=filename,
        media_type=media_type,
        document_type_hint=document_type,
        shipment_id=shipment_uuid,
        external_ref=external_ref,
        source_path=source_path,
    )
    body = result.to_response_dict()
    if not body.get("trace_id"):
        body["trace_id"] = get_trace_id()
    return JSONResponse(status_code=202, content=body)
