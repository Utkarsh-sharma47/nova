"""Deterministic synthetic document fixtures (no real customer documents)."""

from __future__ import annotations


def make_text_invoice(*, body: str | None = None) -> bytes:
    content = body or (
        "COMMERCIAL INVOICE\n"
        "Invoice Number: INV-1001\n"
        "Shipper: Acme Logistics LLC\n"
        "Consignee: Example Trading Co\n"
        "Amount: USD 1250.00\n"
    )
    return content.encode("utf-8")


def build_simple_pdf(text: str, *, pages: int = 1) -> bytes:
    page_refs = " ".join(f"{3 + i} 0 R" for i in range(pages))
    font_obj_num = 3 + pages * 2
    objects: list[bytes] = [
        b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n",
        f"2 0 obj<< /Type /Pages /Kids [{page_refs}] /Count {pages} >>endobj\n".encode(),
    ]
    content_objs: list[bytes] = []
    for i in range(pages):
        page_num = 3 + i
        content_num = 3 + pages + i
        page_text = text if pages == 1 else f"{text} (page {i + 1})"
        safe = page_text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = f"BT /F1 12 Tf 72 720 Td ({safe}) Tj ET\n".encode("latin-1", "replace")
        objects.append(
            (
                f"{page_num} 0 obj<< /Type /Page /Parent 2 0 R "
                f"/MediaBox [0 0 612 792] /Contents {content_num} 0 R "
                f"/Resources<< /Font<< /F1 {font_obj_num} 0 R >> >> >>endobj\n"
            ).encode()
        )
        content_objs.append(
            f"{content_num} 0 obj<< /Length {len(stream)} >>stream\n".encode()
            + stream
            + b"endstream\nendobj\n"
        )
    objects.extend(content_objs)
    objects.append(
        (
            f"{font_obj_num} 0 obj<< /Type /Font /Subtype /Type1 "
            f"/BaseFont /Helvetica >>endobj\n"
        ).encode()
    )
    header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    body = b""
    offsets = [0]
    for obj in objects:
        offsets.append(len(header) + len(body))
        body += obj
    xref_pos = len(header) + len(body)
    xref_lines = [f"xref\n0 {len(objects) + 1}\n", "0000000000 65535 f \n"]
    for off in offsets[1:]:
        xref_lines.append(f"{off:010d} 00000 n \n")
    trailer = (
        f"trailer<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_pos}\n%%EOF\n"
    )
    return header + body + "".join(xref_lines).encode() + trailer.encode()


def make_digital_pdf(*, text: str | None = None, pages: int = 1) -> bytes:
    return build_simple_pdf(
        text or "BILL OF LADING BL-NOVA-0001 Vessel MV Example",
        pages=pages,
    )


def make_corrupt_pdf() -> bytes:
    return b"%PDF-1.4\n1 0 obj<<>>endobj\n"


def make_pdf_without_eof() -> bytes:
    return b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\ntrailer"


def make_binary_garbage() -> bytes:
    return b"\x00\x01\x02\xffPNG\r\n" + b"\x00" * 64
