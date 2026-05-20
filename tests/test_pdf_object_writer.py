from __future__ import annotations

from usfs_r1_ea_sources.pdf_object_writer import (
    DEFAULT_PDF_HEADER,
    write_line_pdf,
    write_paginated_line_pdf,
    write_pdf_objects,
)


def test_write_pdf_objects_uses_default_header_and_trailer(tmp_path) -> None:
    path = tmp_path / "objects.pdf"

    write_pdf_objects(
        path,
        [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [] /Count 0 >>",
        ],
    )

    raw = path.read_bytes()

    assert raw.startswith(DEFAULT_PDF_HEADER + b"1 0 obj\n")
    assert b"xref\n0 3\n" in raw
    assert raw.endswith(b"%%EOF\n")


def test_write_pdf_objects_supports_custom_header(tmp_path) -> None:
    path = tmp_path / "custom-header.pdf"

    write_pdf_objects(path, [b"<< /Type /Catalog >>"], header=b"%PDF-1.4\n")

    assert path.read_bytes().startswith(b"%PDF-1.4\n1 0 obj\n")


def test_write_line_pdf_escapes_text(tmp_path) -> None:
    path = tmp_path / "single-page.pdf"

    write_line_pdf(path, [r"Hello \(Forest)"])

    raw = path.read_bytes()

    assert raw.startswith(b"%PDF-1.4\n1 0 obj\n")
    assert b"/BaseFont /Helvetica" in raw
    assert b"(Hello \\\\\\(Forest\\)) Tj" in raw


def test_write_paginated_line_pdf_supports_custom_font_and_text_transform(tmp_path) -> None:
    path = tmp_path / "paginated.pdf"

    write_paginated_line_pdf(
        path,
        [["A<br>B", "Section \u00a7"]],
        title="Packet",
        font_name="Courier",
        text_transform=lambda value: str(value).replace("<br>", " / ").replace("\u00a7", "Sec."),
    )

    raw = path.read_bytes()

    assert raw.startswith(DEFAULT_PDF_HEADER + b"1 0 obj\n")
    assert b"/BaseFont /Courier" in raw
    assert b"(A / B) Tj T*" in raw
    assert b"(Packet | Page 1 of 1) Tj" in raw
