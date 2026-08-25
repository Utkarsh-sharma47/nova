"""Compatibility facade for the canonical :mod:`nova.documents` package."""

from nova.documents import (
    DigitalPdfAdapter,
    DocumentProcessingService,
    DocumentProcessorPort,
    PassthroughTextAdapter,
    ProcessorRegistry,
)

__all__ = [
    "DigitalPdfAdapter",
    "DocumentProcessingService",
    "DocumentProcessorPort",
    "PassthroughTextAdapter",
    "ProcessorRegistry",
]
