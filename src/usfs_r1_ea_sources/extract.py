from __future__ import annotations

from pathlib import Path
import importlib.util
import multiprocessing
import shutil
import subprocess
import sys
import tempfile

from .extract_chunking import _chunk_id
from .extract_chunking import _chunk_text
from .extract_common import PDF_RASTER_OCR_DPI
from .extract_common import PDF_RASTER_OCR_MAX_WORKERS
from .extract_common import PDF_RASTER_OCR_PARALLEL_MIN_PAGES
from .extract_common import PDF_TEXT_FALLBACK_MAX_DECOMPRESS_BYTES
from .extract_common import ExtractionBuildResult
from .extract_common import ExtractionFailure
from .extract_common import ExtractionPayload
from .extract_common import TextBlock
from .extract_common import _clean_text
from .extract_common import _effective_parser
from .extract_common import _normalize_xml_scope_identifier
from .extract_common import _read_json
from .extract_common import _write_json
from .extract_common import _xml_local_name
from .extract_common import _xml_scope_for_row
from .extract_docling_support import _raise_pypdf_decompression_limit
from .extract_docling_support import _rapidocr_torch
from .extract_docling_support import _resolve_external_docling_python
from .extract_markup_support import _extract_docx
from .extract_markup_support import _extract_html
from .extract_markup_support import _extract_plain_text
from .extract_markup_support import _extract_xml
from .extract_markup_support import _extract_zip
from .extract_markup_support import _find_xml_scope_element
from . import extract_docling_support
from . import extract_markup_support
from . import extract_pdf_support
from . import extract_runtime

__all__ = [
    "Path",
    "PDF_RASTER_OCR_DPI",
    "PDF_RASTER_OCR_MAX_WORKERS",
    "PDF_RASTER_OCR_PARALLEL_MIN_PAGES",
    "PDF_TEXT_FALLBACK_MAX_DECOMPRESS_BYTES",
    "ExtractionBuildResult",
    "ExtractionFailure",
    "ExtractionPayload",
    "TextBlock",
    "_chunk_id",
    "_chunk_text",
    "_clean_text",
    "_effective_parser",
    "_extract_docx",
    "_extract_html",
    "_extract_pdf",
    "_extract_plain_text",
    "_extract_row",
    "_extract_xml",
    "_extract_zip",
    "_extract_payload",
    "_find_xml_scope_element",
    "_normalize_xml_scope_identifier",
    "_raise_pypdf_decompression_limit",
    "_rapidocr_torch",
    "_resolve_external_docling_python",
    "_read_json",
    "_write_json",
    "_xml_local_name",
    "_xml_scope_for_row",
    "_try_extract_docling",
    "_try_extract_docling_external",
    "_try_extract_docling_isolated",
    "_docling_child_main",
    "_try_extract_pdf_text_fallback",
    "_try_extract_pdf_raster_ocr",
    "_collect_pdf_raster_ocr_blocks",
    "_pdf_raster_ocr_worker_count",
    "_ocr_pdf_raster_page",
    "_apple_vision_ocr_available",
    "_pdf_raster_ocr_engine_order",
    "_collect_pdf_raster_apple_vision_blocks",
    "_try_extract_chunked_docling_pdf",
    "_extract_doc",
    "_extract_image",
    "build_extraction",
    "importlib",
    "multiprocessing",
    "shutil",
    "subprocess",
    "tempfile",
]


def _self():
    return sys.modules[__name__]


def build_extraction(
    *,
    output_dir: Path,
    catalog_dir: Path | None = None,
    id_filter: str | None = None,
    id_filters: set[str] | None = None,
    parser_filter: str | None = None,
    limit: int | None = None,
    chunk_max_chars: int = 1800,
    chunk_overlap_chars: int = 200,
    prefer_docling: bool = False,
    docling_ocr: bool = False,
    docling_timeout_seconds: float | None = 300.0,
    allow_invalid_catalog: bool = False,
    reuse_existing: bool = False,
    reuse_inventory_path: Path | None = None,
    merge_selected_into_existing: bool = False,
) -> ExtractionBuildResult:
    return extract_runtime.build_extraction(
        output_dir=output_dir,
        catalog_dir=catalog_dir,
        id_filter=id_filter,
        id_filters=id_filters,
        parser_filter=parser_filter,
        limit=limit,
        chunk_max_chars=chunk_max_chars,
        chunk_overlap_chars=chunk_overlap_chars,
        prefer_docling=prefer_docling,
        docling_ocr=docling_ocr,
        docling_timeout_seconds=docling_timeout_seconds,
        allow_invalid_catalog=allow_invalid_catalog,
        reuse_existing=reuse_existing,
        reuse_inventory_path=reuse_inventory_path,
        merge_selected_into_existing=merge_selected_into_existing,
        facade_module=_self(),
    )


def _extract_row(
    *,
    row: dict,
    output_dir: Path,
    extracted_text_dir: Path,
    docling_json_dir: Path,
    extracted_at: str,
    chunk_max_chars: int,
    chunk_overlap_chars: int,
    prefer_docling: bool,
    docling_ocr: bool,
    docling_timeout_seconds: float | None,
    reuse_existing: bool,
    reuse_inventory_record: dict | None,
    reuse_inventory_enforced: bool,
    payload_cache_dir: Path,
) -> tuple[dict, list[dict]]:
    return extract_runtime._extract_row(
        row=row,
        output_dir=output_dir,
        extracted_text_dir=extracted_text_dir,
        docling_json_dir=docling_json_dir,
        extracted_at=extracted_at,
        chunk_max_chars=chunk_max_chars,
        chunk_overlap_chars=chunk_overlap_chars,
        prefer_docling=prefer_docling,
        docling_ocr=docling_ocr,
        docling_timeout_seconds=docling_timeout_seconds,
        reuse_existing=reuse_existing,
        reuse_inventory_record=reuse_inventory_record,
        reuse_inventory_enforced=reuse_inventory_enforced,
        payload_cache_dir=payload_cache_dir,
        facade_module=_self(),
    )


def _extract_payload(
    *,
    row: dict,
    artifact_path: Path,
    prefer_docling: bool,
    docling_ocr: bool,
    docling_timeout_seconds: float | None,
) -> ExtractionPayload:
    return extract_runtime._extract_payload(
        row=row,
        artifact_path=artifact_path,
        prefer_docling=prefer_docling,
        docling_ocr=docling_ocr,
        docling_timeout_seconds=docling_timeout_seconds,
        facade_module=_self(),
    )


def _extract_pdf(
    artifact_path: Path,
    *,
    ocr_enabled: bool,
    timeout_seconds: float | None,
) -> ExtractionPayload:
    return extract_pdf_support._extract_pdf(
        artifact_path,
        ocr_enabled=ocr_enabled,
        timeout_seconds=timeout_seconds,
        facade_module=_self(),
    )


def _try_extract_docling(
    artifact_path: Path,
    *,
    ocr_enabled: bool,
    timeout_seconds: float | None,
) -> ExtractionPayload | None:
    return extract_docling_support._try_extract_docling(
        artifact_path,
        ocr_enabled=ocr_enabled,
        timeout_seconds=timeout_seconds,
        facade_module=_self(),
    )


def _try_extract_docling_external(
    artifact_path: Path,
    *,
    ocr_enabled: bool,
    timeout_seconds: float | None,
    python_path: Path,
) -> ExtractionPayload | None:
    return extract_docling_support._try_extract_docling_external(
        artifact_path,
        ocr_enabled=ocr_enabled,
        timeout_seconds=timeout_seconds,
        python_path=python_path,
        facade_module=_self(),
    )


def _try_extract_docling_isolated(
    artifact_path: Path,
    *,
    ocr_enabled: bool,
    timeout_seconds: float,
) -> ExtractionPayload | None:
    return extract_docling_support._try_extract_docling_isolated(
        artifact_path,
        ocr_enabled=ocr_enabled,
        timeout_seconds=timeout_seconds,
        facade_module=_self(),
    )


def _docling_child_main(
    artifact_path: str,
    ocr_enabled: bool,
    timeout_seconds: float | None,
    result_path: str,
) -> None:
    extract_docling_support._docling_child_main(
        artifact_path,
        ocr_enabled=ocr_enabled,
        timeout_seconds=timeout_seconds,
        result_path=result_path,
        facade_module=_self(),
    )


def _try_extract_pdf_text_fallback(artifact_path: Path) -> ExtractionPayload | None:
    return extract_pdf_support._try_extract_pdf_text_fallback(
        artifact_path,
        facade_module=_self(),
    )


def _try_extract_pdf_raster_ocr(
    artifact_path: Path,
    *,
    fallback_error_class: str,
    fallback_error_message: str,
) -> ExtractionPayload | None:
    return extract_pdf_support._try_extract_pdf_raster_ocr(
        artifact_path,
        fallback_error_class=fallback_error_class,
        fallback_error_message=fallback_error_message,
        facade_module=_self(),
    )


def _collect_pdf_raster_ocr_blocks(image_paths: list[Path]) -> list[TextBlock]:
    return extract_pdf_support._collect_pdf_raster_ocr_blocks(
        image_paths,
        facade_module=_self(),
    )


def _pdf_raster_ocr_worker_count(page_count: int) -> int:
    return extract_pdf_support._pdf_raster_ocr_worker_count(
        page_count,
        facade_module=_self(),
    )


def _ocr_pdf_raster_page(image_path: str) -> tuple[int, str | None]:
    return extract_pdf_support._ocr_pdf_raster_page(
        image_path,
        facade_module=_self(),
    )


def _apple_vision_ocr_available() -> bool:
    return extract_pdf_support._apple_vision_ocr_available(facade_module=_self())


def _pdf_raster_ocr_engine_order(page_count: int) -> list[str]:
    return extract_pdf_support._pdf_raster_ocr_engine_order(
        page_count,
        facade_module=_self(),
    )


def _collect_pdf_raster_apple_vision_blocks(image_paths: list[Path]) -> list[TextBlock]:
    return extract_pdf_support._collect_pdf_raster_apple_vision_blocks(
        image_paths,
        facade_module=_self(),
    )


def _try_extract_chunked_docling_pdf(
    artifact_path: Path,
    *,
    ocr_enabled: bool,
    timeout_seconds: float | None,
    fallback_error_class: str,
    fallback_error_message: str,
) -> ExtractionPayload | None:
    return extract_pdf_support._try_extract_chunked_docling_pdf(
        artifact_path,
        ocr_enabled=ocr_enabled,
        timeout_seconds=timeout_seconds,
        fallback_error_class=fallback_error_class,
        fallback_error_message=fallback_error_message,
        facade_module=_self(),
    )


def _extract_doc(artifact_path: Path) -> ExtractionPayload:
    return extract_markup_support._extract_doc(artifact_path, facade_module=_self())


def _extract_image(
    artifact_path: Path,
    *,
    ocr_enabled: bool,
    timeout_seconds: float | None,
) -> ExtractionPayload:
    return extract_markup_support._extract_image(
        artifact_path,
        ocr_enabled=ocr_enabled,
        timeout_seconds=timeout_seconds,
        facade_module=_self(),
    )
