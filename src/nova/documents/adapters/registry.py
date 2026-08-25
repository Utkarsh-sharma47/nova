"""Adapter registry for DocumentProcessorPort implementations."""

from __future__ import annotations

from nova.documents.adapters.digital_pdf import DigitalPdfAdapter
from nova.documents.adapters.passthrough_text import PassthroughTextAdapter
from nova.documents.adapters.raster_image import RasterImageAdapter
from nova.documents.errors import DOC_UNSUPPORTED_MEDIA_TYPE, DocumentProcessingError
from nova.documents.limits import DEFAULT_LIMITS, DocumentLimits
from nova.documents.port import DocumentProcessorPort


class ProcessorRegistry:
    def __init__(self, processors: list[DocumentProcessorPort] | None = None) -> None:
        self._processors = processors or []

    def register(self, processor: DocumentProcessorPort) -> None:
        self._processors.append(processor)

    def get(self, media_type: str) -> DocumentProcessorPort:
        normalized = media_type.split(";")[0].strip().lower()
        for processor in self._processors:
            if processor.supports(normalized):
                return processor
        raise DocumentProcessingError(
            DOC_UNSUPPORTED_MEDIA_TYPE,
            f"No document processor registered for media type: {normalized}",
            details={"media_type": normalized},
        )

    @property
    def processors(self) -> list[DocumentProcessorPort]:
        return list(self._processors)


def default_registry(limits: DocumentLimits = DEFAULT_LIMITS) -> ProcessorRegistry:
    registry = ProcessorRegistry()
    registry.register(DigitalPdfAdapter(limits=limits))
    registry.register(PassthroughTextAdapter())
    registry.register(RasterImageAdapter())
    return registry
