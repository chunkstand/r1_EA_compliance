from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path


DEFAULT_PDF_HEADER = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
TextTransform = Callable[[str], str]


def write_pdf_objects(
    path: Path,
    objects: Sequence[bytes],
    *,
    header: bytes = DEFAULT_PDF_HEADER,
) -> None:
    """Write a minimal PDF payload from prebuilt indirect object bodies."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = bytearray(header)
    offsets: list[int] = []
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(payload))
        payload.extend(f"{index} 0 obj\n".encode("ascii"))
        payload.extend(obj)
        payload.extend(b"\nendobj\n")
    xref_offset = len(payload)
    payload.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    payload.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        payload.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    payload.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    path.write_bytes(bytes(payload))


def write_line_pdf(
    path: Path,
    lines: Sequence[str],
    *,
    font_name: str = "Helvetica",
    font_size: int = 12,
    start_x: int = 72,
    start_y: int = 740,
    line_step: int = 18,
    page_width: int = 612,
    page_height: int = 792,
    header: bytes = b"%PDF-1.4\n",
    text_transform: TextTransform | None = None,
) -> None:
    """Write a single-page line-oriented PDF using the shared object serializer."""
    content_lines = ["BT", f"/F1 {font_size} Tf", f"{start_x} {start_y} Td"]
    for line in lines:
        content_lines.append(f"({_escape_pdf_text(line, text_transform=text_transform)}) Tj")
        content_lines.append(f"0 {-line_step} Td")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_width} {page_height}] "
            f"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ).encode("ascii"),
        f"<< /Type /Font /Subtype /Type1 /BaseFont /{font_name} >>".encode("ascii"),
        b"<< /Length "
        + str(len(stream)).encode("ascii")
        + b" >>\nstream\n"
        + stream
        + b"\nendstream",
    ]
    write_pdf_objects(path, objects, header=header)


def write_paginated_line_pdf(
    path: Path,
    pages: Sequence[Sequence[str]],
    *,
    title: str,
    font_name: str = "Helvetica",
    page_width: int = 1008,
    page_height: int = 612,
    margin_x: int = 34,
    start_y: int = 568,
    leading: int = 12,
    font_size: int = 8,
    header: bytes = DEFAULT_PDF_HEADER,
    text_transform: TextTransform | None = None,
) -> None:
    """Write a paginated line-oriented PDF with a page footer."""
    objects: list[bytes | None] = [None, None, None]

    def add_object(payload: bytes) -> int:
        objects.append(payload)
        return len(objects)

    for page_number, page_lines in enumerate(pages, start=1):
        content = _paginated_page_content(
            page_lines,
            page_number=page_number,
            page_count=len(pages),
            title=title,
            margin_x=margin_x,
            start_y=start_y,
            leading=leading,
            font_size=font_size,
            text_transform=text_transform,
        )
        content_id = add_object(
            b"<< /Length "
            + str(len(content)).encode("ascii")
            + b" >>\nstream\n"
            + content
            + b"\nendstream"
        )
        page_id = add_object(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_width} {page_height}] "
                f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"
            ).encode("ascii")
        )
        objects[1] = (objects[1] or b"") + f"{page_id} 0 R ".encode("ascii")

    kids = objects[1] or b""
    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objects[1] = (
        b"<< /Type /Pages /Kids ["
        + kids
        + b"] /Count "
        + str(len(pages)).encode("ascii")
        + b" >>"
    )
    objects[2] = f"<< /Type /Font /Subtype /Type1 /BaseFont /{font_name} >>".encode("ascii")
    write_pdf_objects(path, [obj for obj in objects if obj is not None], header=header)


def _paginated_page_content(
    lines: Sequence[str],
    *,
    page_number: int,
    page_count: int,
    title: str,
    margin_x: int,
    start_y: int,
    leading: int,
    font_size: int,
    text_transform: TextTransform | None,
) -> bytes:
    commands = [f"BT /F1 {font_size} Tf {leading} TL {margin_x} {start_y} Td"]
    for line in lines:
        commands.append(f"({_escape_pdf_text(line, text_transform=text_transform)}) Tj T*")
    footer_y = 24 - (start_y - len(lines) * leading)
    commands.append(
        "0 "
        f"{footer_y} Td "
        f"({_escape_pdf_text(f'{title} | Page {page_number} of {page_count}', text_transform=text_transform)}) Tj"
    )
    commands.append("ET")
    return "\n".join(commands).encode("latin-1", errors="replace")


def _escape_pdf_text(value: str, *, text_transform: TextTransform | None) -> str:
    text = text_transform(value) if text_transform is not None else str(value)
    text = text.encode("latin-1", errors="replace").decode("latin-1")
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
