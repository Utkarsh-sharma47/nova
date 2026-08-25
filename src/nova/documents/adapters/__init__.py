"""Document processor adapters."""

from nova.documents.adapters.digital_pdf import DigitalPdfAdapter
from nova.documents.adapters.passthrough_text import PassthroughTextAdapter
from nova.documents.adapters.raster_image import RasterImageAdapter
from nova.documents.adapters.registry import ProcessorRegistry, default_registry

__all__ = [
    "DigitalPdfAdapter",
    "PassthroughTextAdapter",
    "ProcessorRegistry",
    "RasterImageAdapter",
    "default_registry",
]
