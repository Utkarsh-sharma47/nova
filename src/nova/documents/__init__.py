"""Document processing infrastructure (Phase 3)."""

from nova.documents.adapters import (
    DigitalPdfAdapter,
    PassthroughTextAdapter,
    ProcessorRegistry,
    default_registry,
)
from nova.documents.errors import DocumentProcessingError
from nova.documents.limits import (
    DEFAULT_LIMITS,
    PROCESSOR_PACKAGE_VERSION,
    SUPPORTED_EXTENSIONS,
    SUPPORTED_MEDIA_TYPES,
    DocumentLimits,
)
from nova.documents.models import (
    DocumentProcessingRequest,
    DocumentProcessingResult,
    DocumentSourceMetadata,
    ProcessingStatus,
)
from nova.documents.port import DocumentProcessorPort
from nova.documents.service import DocumentProcessingService, process_document
from nova.documents.storage import DocumentBlobStorePort, LocalBlobStore
from nova.documents.validation import ValidatedDocument, validate_document

__all__ = [
    "DEFAULT_LIMITS",
    "PROCESSOR_PACKAGE_VERSION",
    "SUPPORTED_EXTENSIONS",
    "SUPPORTED_MEDIA_TYPES",
    "DigitalPdfAdapter",
    "DocumentBlobStorePort",
    "DocumentLimits",
    "DocumentProcessingError",
    "DocumentProcessingRequest",
    "DocumentProcessingResult",
    "DocumentProcessorPort",
    "DocumentSourceMetadata",
    "LocalBlobStore",
    "PassthroughTextAdapter",
    "ProcessingStatus",
    "ProcessorRegistry",
    "DocumentProcessingService",
    "ValidatedDocument",
    "default_registry",
    "process_document",
    "validate_document",
]
