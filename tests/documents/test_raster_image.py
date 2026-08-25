"""Document processor image adapter and sniffing tests."""

from __future__ import annotations

from nova.documents.adapters.raster_image import RasterImageAdapter
from nova.documents.limits import SUPPORTED_MEDIA_TYPES
from nova.documents.sniffing import detect_media_type
from nova.documents.validation import validate_document

PNG_1X1 = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)
JPEG_MIN = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xd9"
)


def test_supported_media_includes_png_jpeg() -> None:
    assert "image/png" in SUPPORTED_MEDIA_TYPES
    assert "image/jpeg" in SUPPORTED_MEDIA_TYPES


def test_sniff_png_and_jpeg() -> None:
    assert detect_media_type(PNG_1X1) == "image/png"
    assert detect_media_type(JPEG_MIN) == "image/jpeg"


def test_validate_and_process_png() -> None:
    validated = validate_document(
        PNG_1X1,
        declared_media_type="image/png",
        original_filename="scan.png",
    )
    assert validated.detected_media_type == "image/png"
    content = RasterImageAdapter().process(PNG_1X1, media_type="image/png")
    assert content.media_type == "image/png"
    assert content.text is None
    assert len(content.images) == 1
    assert content.images[0].data_base64
    assert "no_local_ocr_vision_llm_required" in content.warnings
