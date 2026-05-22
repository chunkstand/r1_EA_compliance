from __future__ import annotations

from pathlib import Path
import importlib.metadata
import json
import sys
from typing import Any

from .extract_chunking import _assemble_blocks
from .extract_common import APPLE_VISION_OCR_TIMEOUT_SECONDS
from .extract_common import CHUNKED_DOCLING_PDF_MIN_TIMEOUT_SECONDS
from .extract_common import CHUNKED_DOCLING_PDF_PAGE_COUNT
from .extract_common import PDF_RASTER_OCR_DPI
from .extract_common import PDF_RASTER_OCR_MAX_WORKERS
from .extract_common import PDF_RASTER_OCR_PARALLEL_MIN_PAGES
from .extract_common import PDF_TEXT_FALLBACK_ERROR_CLASSES
from .extract_common import PDF_TEXT_FALLBACK_MAX_DECOMPRESS_BYTES
from .extract_common import ExtractionFailure
from .extract_common import ExtractionPayload
from .extract_common import TextBlock
from .extract_common import _clean_text
from .extract_docling_support import _convert_docling_in_process
from .extract_docling_support import _raise_pypdf_decompression_limit
from .extract_docling_support import _with_payload_metadata

def _extract_pdf(
    artifact_path: Path,
    *,
    ocr_enabled: bool,
    timeout_seconds: float | None,
    facade_module: Any,
) -> ExtractionPayload:
    try:
        payload = facade_module._try_extract_docling(
            artifact_path,
            ocr_enabled=ocr_enabled,
            timeout_seconds=timeout_seconds,
        )
    except ExtractionFailure as error:
        if error.error_class in PDF_TEXT_FALLBACK_ERROR_CLASSES:
            try:
                fallback_payload = facade_module._try_extract_pdf_text_fallback(artifact_path)
            except ExtractionFailure as fallback_error:
                raster_payload = facade_module._try_extract_pdf_raster_ocr(
                    artifact_path,
                    fallback_error_class=fallback_error.error_class,
                    fallback_error_message=fallback_error.message,
                )
                if raster_payload is not None:
                    return raster_payload
                chunked_payload = facade_module._try_extract_chunked_docling_pdf(
                    artifact_path,
                    ocr_enabled=ocr_enabled,
                    timeout_seconds=timeout_seconds,
                    fallback_error_class=fallback_error.error_class,
                    fallback_error_message=fallback_error.message,
                )
                if chunked_payload is not None:
                    return chunked_payload
                raise
            if fallback_payload is not None:
                return _with_payload_metadata(
                    fallback_payload,
                    {
                        "fallback_from": "docling",
                        "fallback_error_class": error.error_class,
                        "fallback_error_message": error.message,
                        "pypdf_max_decompress_bytes": PDF_TEXT_FALLBACK_MAX_DECOMPRESS_BYTES,
                    },
                )
            chunked_payload = facade_module._try_extract_chunked_docling_pdf(
                artifact_path,
                ocr_enabled=ocr_enabled,
                timeout_seconds=timeout_seconds,
                fallback_error_class=error.error_class,
                fallback_error_message=error.message,
            )
            if chunked_payload is not None:
                return chunked_payload
        raise
    if payload is not None:
        return payload
    try:
        fallback_payload = facade_module._try_extract_pdf_text_fallback(artifact_path)
    except ExtractionFailure as fallback_error:
        raster_payload = facade_module._try_extract_pdf_raster_ocr(
            artifact_path,
            fallback_error_class=fallback_error.error_class,
            fallback_error_message=fallback_error.message,
        )
        if raster_payload is not None:
            return raster_payload
        chunked_payload = facade_module._try_extract_chunked_docling_pdf(
            artifact_path,
            ocr_enabled=ocr_enabled,
            timeout_seconds=timeout_seconds,
            fallback_error_class=fallback_error.error_class,
            fallback_error_message=fallback_error.message,
        )
        if chunked_payload is not None:
            return chunked_payload
        raise
    if fallback_payload is not None:
        return _with_payload_metadata(
            fallback_payload,
            {
                "fallback_from": "docling",
                "fallback_error_class": "docling_unavailable",
                "fallback_error_message": (
                    "Docling is not installed in the active Python environment."
                ),
                "pypdf_max_decompress_bytes": PDF_TEXT_FALLBACK_MAX_DECOMPRESS_BYTES,
            },
        )
    chunked_payload = facade_module._try_extract_chunked_docling_pdf(
        artifact_path,
        ocr_enabled=ocr_enabled,
        timeout_seconds=timeout_seconds,
        fallback_error_class="docling_unavailable",
        fallback_error_message=(
            "Docling is not installed in the active Python environment."
        ),
    )
    if chunked_payload is not None:
        return chunked_payload
    raise ExtractionFailure(
        "docling_unavailable",
        "Docling is required for this parser but is not installed in the active Python "
        "environment.",
    )



def _try_extract_pdf_text_fallback(artifact_path: Path, *, facade_module: Any) -> ExtractionPayload | None:
    if facade_module.importlib.util.find_spec("pypdf") is None:
        return None
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    try:
        version = importlib.metadata.version("pypdf")
    except importlib.metadata.PackageNotFoundError:
        version = "unknown"
    try:
        _raise_pypdf_decompression_limit()
        reader = PdfReader(str(artifact_path))
        blocks = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = _clean_text(page.extract_text() or "")
            if text:
                blocks.append(TextBlock(text=text, page=page_number))
    except Exception as error:
        raise ExtractionFailure("pdf_text_fallback_failed", str(error)) from error
    if not blocks:
        raise ExtractionFailure(
            "pdf_text_fallback_empty",
            "PDF text fallback produced no text.",
        )
    text, blocks = _assemble_blocks(blocks)
    return ExtractionPayload(
        text=text,
        blocks=blocks,
        parser_name="pypdf_text_fallback",
        parser_version=version,
        metadata={"pypdf_max_decompress_bytes": PDF_TEXT_FALLBACK_MAX_DECOMPRESS_BYTES},
    )


def _try_extract_pdf_raster_ocr(
    artifact_path: Path,
    *,
    fallback_error_class: str,
    fallback_error_message: str,
    facade_module: Any,
) -> ExtractionPayload | None:
    if facade_module.shutil.which("pdftoppm") is None:
        return None
    if facade_module.importlib.util.find_spec("rapidocr") is None:
        return None

    with facade_module.tempfile.TemporaryDirectory(prefix="usfs-r1-raster-ocr-") as tmp:
        tmpdir = Path(tmp)
        output_prefix = tmpdir / "page"
        command = [
            "pdftoppm",
            "-png",
            "-r",
            str(PDF_RASTER_OCR_DPI),
            str(artifact_path),
            str(output_prefix),
        ]
        completed = facade_module.subprocess.run(command, check=False, capture_output=True, text=True)
        if completed.returncode != 0:
            return None

        image_paths = sorted(
            tmpdir.glob("page-*.png"),
            key=lambda path: int(path.stem.rsplit("-", 1)[-1]),
        )
        if not image_paths:
            return None

        for engine in facade_module._pdf_raster_ocr_engine_order(len(image_paths)):
            try:
                if engine == "apple_vision":
                    blocks = facade_module._collect_pdf_raster_apple_vision_blocks(image_paths)
                    if blocks:
                        return _build_pdf_raster_ocr_payload(
                            blocks,
                            parser_name="apple_vision_pdf_raster",
                            parser_version="vision_swift",
                            fallback_error_class=fallback_error_class,
                            fallback_error_message=fallback_error_message,
                            page_count=len(image_paths),
                            backend="apple_vision_swift",
                        )
                    continue

                blocks = facade_module._collect_pdf_raster_ocr_blocks(image_paths)
                if blocks:
                    return _build_pdf_raster_ocr_payload(
                        blocks,
                        parser_name="rapidocr_pdf_raster",
                        parser_version="torch",
                        fallback_error_class=fallback_error_class,
                        fallback_error_message=fallback_error_message,
                        page_count=len(image_paths),
                        backend="rapidocr_torch",
                    )
            except Exception:
                continue

    return None


def _build_pdf_raster_ocr_payload(
    blocks: list[TextBlock],
    *,
    parser_name: str,
    parser_version: str,
    fallback_error_class: str,
    fallback_error_message: str,
    page_count: int,
    backend: str,
) -> ExtractionPayload:
    text, assembled_blocks = _assemble_blocks(blocks)
    return ExtractionPayload(
        text=text,
        blocks=assembled_blocks,
        parser_name=parser_name,
        parser_version=parser_version,
        metadata={
            "fallback_from": "pdf_raster_ocr",
            "fallback_error_class": fallback_error_class,
            "fallback_error_message": fallback_error_message,
            "pdf_raster_ocr_dpi": PDF_RASTER_OCR_DPI,
            "pdf_raster_ocr_page_count": page_count,
            "pdf_raster_ocr_backend": backend,
        },
    )


def _collect_pdf_raster_ocr_blocks(image_paths: list[Path], *, facade_module: Any) -> list[TextBlock]:
    worker_count = facade_module._pdf_raster_ocr_worker_count(len(image_paths))
    image_path_strings = [str(path) for path in image_paths]
    if worker_count == 1:
        results = [facade_module._ocr_pdf_raster_page(path) for path in image_path_strings]
    else:
        try:
            context = facade_module.multiprocessing.get_context("spawn")
            with context.Pool(processes=worker_count) as pool:
                results = pool.map(facade_module._ocr_pdf_raster_page, image_path_strings)
        except Exception:
            results = [facade_module._ocr_pdf_raster_page(path) for path in image_path_strings]
    return [
        TextBlock(text=page_text, page=page_number)
        for page_number, page_text in results
        if page_text
    ]


def _pdf_raster_ocr_worker_count(page_count: int, *, facade_module: Any) -> int:
    if page_count < PDF_RASTER_OCR_PARALLEL_MIN_PAGES:
        return 1
    try:
        cpu_count = facade_module.multiprocessing.cpu_count()
    except NotImplementedError:
        cpu_count = 1
    return max(1, min(PDF_RASTER_OCR_MAX_WORKERS, cpu_count))


def _ocr_pdf_raster_page(image_path: str, *, facade_module: Any) -> tuple[int, str | None]:
    page_number = int(Path(image_path).stem.rsplit("-", 1)[-1])
    ocr = facade_module._rapidocr_torch(use_cls=False)
    result = ocr(image_path)
    page_texts = [_clean_text(text) for text in getattr(result, "txts", ()) if _clean_text(text)]
    if not page_texts:
        return page_number, None
    return page_number, "\n".join(page_texts)


def _apple_vision_ocr_available(*, facade_module: Any) -> bool:
    return sys.platform == "darwin" and facade_module.shutil.which("swift") is not None


def _pdf_raster_ocr_engine_order(page_count: int, *, facade_module: Any) -> list[str]:
    apple_vision_available = facade_module._apple_vision_ocr_available()
    rapidocr_available = facade_module.importlib.util.find_spec("rapidocr") is not None
    prefer_apple_vision = apple_vision_available and page_count >= PDF_RASTER_OCR_PARALLEL_MIN_PAGES

    order: list[str] = []
    if prefer_apple_vision:
        order.append("apple_vision")
    if rapidocr_available:
        order.append("rapidocr")
    if apple_vision_available and "apple_vision" not in order:
        order.append("apple_vision")
    return order


def _collect_pdf_raster_apple_vision_blocks(image_paths: list[Path], *, facade_module: Any) -> list[TextBlock]:
    if not image_paths:
        return []

    script = """
import AppKit
import Foundation
import Vision

func pageNumber(from path: String) -> Int {
    let stem = URL(fileURLWithPath: path).deletingPathExtension().lastPathComponent
    return Int(stem.split(separator: "-").last ?? "0") ?? 0
}

func emit(page: Int, text: String) throws {
    let payload: [String: Any] = ["page": page, "text": text]
    let data = try JSONSerialization.data(withJSONObject: payload, options: [])
    FileHandle.standardOutput.write(data)
    FileHandle.standardOutput.write("\\n".data(using: .utf8)!)
}

for path in CommandLine.arguments.dropFirst() {
    let page = pageNumber(from: path)
    let url = URL(fileURLWithPath: path)
    guard let image = NSImage(contentsOf: url) else {
        fputs("load_failed:\\(page):\\(path)\\n", stderr)
        exit(1)
    }
    var rect = NSRect(origin: .zero, size: image.size)
    guard let cgImage = image.cgImage(forProposedRect: &rect, context: nil, hints: nil) else {
        fputs("cgimage_failed:\\(page):\\(path)\\n", stderr)
        exit(1)
    }
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = false
    let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
    do {
        try handler.perform([request])
    } catch {
        fputs("ocr_failed:\\(page):\\(error.localizedDescription)\\n", stderr)
        exit(1)
    }
    let text = (request.results ?? []).compactMap { $0.topCandidates(1).first?.string }.joined(separator: "\\n")
    do {
        try emit(page: page, text: text)
    } catch {
        fputs("emit_failed:\\(page):\\(error.localizedDescription)\\n", stderr)
        exit(1)
    }
}
"""

    with facade_module.tempfile.NamedTemporaryFile(
        prefix="usfs-r1-apple-vision-ocr-",
        suffix=".swift",
        delete=False,
    ) as handle:
        script_path = Path(handle.name)
    try:
        script_path.write_text(script, encoding="utf-8")
        completed = facade_module.subprocess.run(
            ["swift", str(script_path), *[str(path) for path in image_paths]],
            check=False,
            capture_output=True,
            text=True,
            timeout=APPLE_VISION_OCR_TIMEOUT_SECONDS,
        )
    finally:
        script_path.unlink(missing_ok=True)

    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "Apple Vision OCR failed.")

    blocks = []
    for line in completed.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        payload = json.loads(line)
        page_number = int(payload.get("page") or 0)
        page_text = _clean_text(payload.get("text") or "")
        if page_text:
            blocks.append(TextBlock(text=page_text, page=page_number))
    return sorted(blocks, key=lambda block: (block.page or 0, block.char_start or 0))


def _try_extract_chunked_docling_pdf(
    artifact_path: Path,
    *,
    ocr_enabled: bool,
    timeout_seconds: float | None,
    fallback_error_class: str,
    fallback_error_message: str,
    facade_module: Any,
) -> ExtractionPayload | None:
    if not ocr_enabled:
        return None
    if facade_module.importlib.util.find_spec("pypdf") is None:
        return None
    try:
        from pypdf import PdfReader
        from pypdf import PdfWriter
    except ImportError:
        return None

    try:
        reader = PdfReader(str(artifact_path))
    except Exception:
        return None

    page_count = len(reader.pages)
    if page_count <= CHUNKED_DOCLING_PDF_PAGE_COUNT:
        return None

    docling_available = facade_module.importlib.util.find_spec("docling") is not None
    chunk_timeout_seconds = (
        None
        if timeout_seconds is None
        else max(timeout_seconds, CHUNKED_DOCLING_PDF_MIN_TIMEOUT_SECONDS)
    )
    parser_name = "docling"
    parser_version = "unknown"
    payload_metadata: dict = {}
    blocks: list[TextBlock] = []
    chunk_count = 0

    for start in range(0, page_count, CHUNKED_DOCLING_PDF_PAGE_COUNT):
        end = min(start + CHUNKED_DOCLING_PDF_PAGE_COUNT, page_count)
        writer = PdfWriter()
        for page_index in range(start, end):
            writer.add_page(reader.pages[page_index])
        with facade_module.tempfile.NamedTemporaryFile(
            prefix="usfs-r1-docling-pdf-chunk-",
            suffix=".pdf",
            delete=False,
        ) as handle:
            chunk_path = Path(handle.name)
        try:
            with chunk_path.open("wb") as output_handle:
                writer.write(output_handle)
            if docling_available:
                chunk_payload = _convert_docling_in_process(
                    chunk_path,
                    ocr_enabled=ocr_enabled,
                    timeout_seconds=None,
                )
            else:
                chunk_payload = facade_module._try_extract_docling(
                    chunk_path,
                    ocr_enabled=ocr_enabled,
                    timeout_seconds=chunk_timeout_seconds,
                )
        except ExtractionFailure:
            return None
        finally:
            chunk_path.unlink(missing_ok=True)

        if chunk_payload is None or not chunk_payload.text.strip():
            return None

        chunk_count += 1
        parser_name = chunk_payload.parser_name or parser_name
        parser_version = chunk_payload.parser_version or parser_version
        if not payload_metadata and chunk_payload.metadata:
            payload_metadata = dict(chunk_payload.metadata)
        blocks.extend(
            TextBlock(
                text=block.text,
                heading=block.heading,
                section=block.section,
                page=(block.page + start) if block.page is not None else None,
            )
            for block in chunk_payload.blocks
        )

    text, assembled_blocks = _assemble_blocks(blocks)
    return ExtractionPayload(
        text=text,
        blocks=assembled_blocks,
        parser_name=parser_name,
        parser_version=parser_version,
        metadata={
            **payload_metadata,
            "fallback_from": "docling_chunked_pdf",
            "fallback_error_class": fallback_error_class,
            "fallback_error_message": fallback_error_message,
            "chunked_pdf_chunk_count": chunk_count,
            "chunked_pdf_page_chunk_size": CHUNKED_DOCLING_PDF_PAGE_COUNT,
            "chunked_pdf_page_count": page_count,
        },
    )
