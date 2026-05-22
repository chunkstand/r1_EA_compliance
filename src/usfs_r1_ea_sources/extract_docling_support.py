from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import importlib.metadata
import json
import multiprocessing
import os
from typing import Any

from .extract_chunking import _blocks_from_plain_text
from .extract_common import DOCLING_PYTHON_ENV_VAR
from .extract_common import PDF_TEXT_FALLBACK_MAX_DECOMPRESS_BYTES
from .extract_common import ExtractionFailure
from .extract_common import ExtractionPayload
from .extract_common import TextBlock
from .extract_common import _read_json

def _try_extract_docling(
    artifact_path: Path,
    *,
    ocr_enabled: bool,
    timeout_seconds: float | None,
    facade_module: Any,
) -> ExtractionPayload | None:
    if facade_module.importlib.util.find_spec("docling") is None:
        external_python = facade_module._resolve_external_docling_python()
        if external_python is None:
            return None
        payload = facade_module._try_extract_docling_external(
            artifact_path,
            ocr_enabled=ocr_enabled,
            timeout_seconds=timeout_seconds,
            python_path=external_python,
            facade_module=facade_module,
        )
        if payload is None:
            return None
        return _with_payload_metadata(
            payload,
            {
                "docling_execution": "external_python",
                "docling_python": str(external_python),
            },
        )

    if timeout_seconds is not None:
        return facade_module._try_extract_docling_isolated(
            artifact_path,
            ocr_enabled=ocr_enabled,
            timeout_seconds=timeout_seconds,
            facade_module=facade_module,
        )

    return _convert_docling_in_process(
        artifact_path,
        ocr_enabled=ocr_enabled,
        timeout_seconds=timeout_seconds,
    )


def _resolve_external_docling_python() -> Path | None:
    env_path = os.environ.get(DOCLING_PYTHON_ENV_VAR)
    if not env_path:
        return None
    candidate = Path(env_path)
    if candidate.exists() and candidate.is_file() and os.access(candidate, os.X_OK):
        return candidate
    return None


def _try_extract_docling_external(
    artifact_path: Path,
    *,
    ocr_enabled: bool,
    timeout_seconds: float | None,
    python_path: Path,
    facade_module: Any,
) -> ExtractionPayload | None:
    with facade_module.tempfile.NamedTemporaryFile(
        prefix="usfs-r1-docling-external-",
        suffix=".json",
        delete=False,
    ) as handle:
        result_path = Path(handle.name)
    try:
        repo_root = Path(__file__).resolve().parents[2]
        src_path = repo_root / "src"
        env = os.environ.copy()
        existing_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            f"{src_path}{os.pathsep}{existing_pythonpath}"
            if existing_pythonpath
            else str(src_path)
        )
        command = [
            str(python_path),
            "-c",
            (
                "from usfs_r1_ea_sources.extract import _docling_child_main; "
                "import sys; "
                "_docling_child_main("
                "sys.argv[1], "
                "sys.argv[2] == '1', "
                "None if sys.argv[3] == 'none' else float(sys.argv[3]), "
                "sys.argv[4])"
            ),
            str(artifact_path),
            "1" if ocr_enabled else "0",
            "none" if timeout_seconds is None else str(timeout_seconds),
            str(result_path),
        ]
        try:
            completed = facade_module.subprocess.run(
                command,
                check=False,
                env=env,
                timeout=timeout_seconds,
                capture_output=True,
                text=True,
            )
        except facade_module.subprocess.TimeoutExpired as error:
            raise ExtractionFailure(
                "docling_timeout",
                f"Docling conversion exceeded hard timeout of {timeout_seconds:g} seconds.",
            ) from error
        if not result_path.exists() or result_path.stat().st_size == 0:
            raise ExtractionFailure(
                "docling_worker_failed",
                "External Docling worker exited without a result file; "
                f"returncode={completed.returncode}.",
            )
        result = _read_json(result_path)
        status = result.get("status")
        if status == "unavailable":
            return None
        if status == "error":
            raise ExtractionFailure(
                result.get("error_class") or "docling_conversion_failed",
                result.get("error_message") or "External Docling worker failed.",
            )
        if status != "ok":
            raise ExtractionFailure(
                "docling_worker_failed",
                f"External Docling worker returned unknown status: {status}",
            )
        return _payload_from_wire(result["payload"])
    finally:
        result_path.unlink(missing_ok=True)


def _try_extract_docling_isolated(
    artifact_path: Path,
    *,
    ocr_enabled: bool,
    timeout_seconds: float,
    facade_module: Any,
) -> ExtractionPayload | None:
    with facade_module.tempfile.NamedTemporaryFile(
        prefix="usfs-r1-docling-",
        suffix=".json",
        delete=False,
    ) as handle:
        result_path = Path(handle.name)
    try:
        context = facade_module.multiprocessing.get_context("spawn")
        process = context.Process(
            target=facade_module._docling_child_main,
            args=(str(artifact_path), ocr_enabled, timeout_seconds, str(result_path)),
        )
        process.start()
        process.join(timeout_seconds)
        if process.is_alive():
            _stop_process(process)
            raise ExtractionFailure(
                "docling_timeout",
                f"Docling conversion exceeded hard timeout of {timeout_seconds:g} seconds.",
            )
        if not result_path.exists() or result_path.stat().st_size == 0:
            raise ExtractionFailure(
                "docling_worker_failed",
                f"Docling worker exited without a result file; exitcode={process.exitcode}.",
            )
        result = _read_json(result_path)
        status = result.get("status")
        if status == "unavailable":
            return None
        if status == "error":
            raise ExtractionFailure(
                result.get("error_class") or "docling_conversion_failed",
                result.get("error_message") or "Docling worker failed.",
            )
        if status != "ok":
            raise ExtractionFailure(
                "docling_worker_failed",
                f"Docling worker returned unknown status: {status}",
            )
        return _payload_from_wire(result["payload"])
    finally:
        result_path.unlink(missing_ok=True)


def _stop_process(process: multiprocessing.Process) -> None:
    process.terminate()
    process.join(5)
    if process.is_alive():
        process.kill()
        process.join(5)


def _docling_child_main(
    artifact_path: str,
    ocr_enabled: bool,
    timeout_seconds: float | None,
    result_path: str,
    facade_module: Any,
) -> None:
    try:
        payload = _convert_docling_in_process(
            Path(artifact_path),
            ocr_enabled=ocr_enabled,
            timeout_seconds=timeout_seconds,
        )
        if payload is None:
            result = {"status": "unavailable"}
        else:
            result = {"status": "ok", "payload": _payload_to_wire(payload)}
    except ExtractionFailure as error:
        result = {
            "status": "error",
            "error_class": error.error_class,
            "error_message": error.message,
        }
    except Exception as error:
        result = {
            "status": "error",
            "error_class": type(error).__name__,
            "error_message": str(error),
        }
    Path(result_path).write_text(json.dumps(result, sort_keys=True), encoding="utf-8")



def _with_payload_metadata(payload: ExtractionPayload, metadata: dict) -> ExtractionPayload:
    return ExtractionPayload(
        text=payload.text,
        blocks=payload.blocks,
        parser_name=payload.parser_name,
        parser_version=payload.parser_version,
        docling_json=payload.docling_json,
        metadata={**(payload.metadata or {}), **metadata},
    )


def _raise_pypdf_decompression_limit() -> None:
    try:
        from pypdf import filters
    except ImportError:
        return
    current = getattr(filters, "ZLIB_MAX_OUTPUT_LENGTH", 0)
    if current < PDF_TEXT_FALLBACK_MAX_DECOMPRESS_BYTES:
        filters.ZLIB_MAX_OUTPUT_LENGTH = PDF_TEXT_FALLBACK_MAX_DECOMPRESS_BYTES


@lru_cache(maxsize=2)
def _rapidocr_torch(*, use_cls: bool = True):
    from rapidocr import RapidOCR
    from rapidocr.utils.typings import EngineType

    params = {
        "Det.engine_type": EngineType.TORCH,
        "Cls.engine_type": EngineType.TORCH,
        "Rec.engine_type": EngineType.TORCH,
    }
    if not use_cls:
        params["Global.use_cls"] = False
    return RapidOCR(params=params)


def _convert_docling_in_process(
    artifact_path: Path,
    *,
    ocr_enabled: bool,
    timeout_seconds: float | None,
) -> ExtractionPayload | None:
    try:
        __import__("docling.document_converter")
    except ImportError:
        return None

    try:
        version = importlib.metadata.version("docling")
    except importlib.metadata.PackageNotFoundError:
        version = "unknown"

    try:
        result = _docling_converter(
            artifact_path,
            ocr_enabled=ocr_enabled,
            timeout_seconds=timeout_seconds,
        ).convert(artifact_path)
        document = getattr(result, "document", None)
        if document is None:
            raise ExtractionFailure("docling_conversion_failed", "Docling returned no document.")
        text = _docling_text(document)
        docling_json = _docling_json(document)
    except ExtractionFailure:
        raise
    except Exception as error:
        raise ExtractionFailure("docling_conversion_failed", str(error)) from error

    text, blocks = _blocks_from_plain_text(text)
    return ExtractionPayload(
        text=text,
        blocks=blocks,
        parser_name="docling",
        parser_version=version,
        docling_json=docling_json,
    )


def _payload_to_wire(payload: ExtractionPayload) -> dict:
    return {
        "text": payload.text,
        "blocks": [
            {
                "text": block.text,
                "heading": block.heading,
                "section": block.section,
                "page": block.page,
                "char_start": block.char_start,
                "char_end": block.char_end,
            }
            for block in payload.blocks
        ],
        "parser_name": payload.parser_name,
        "parser_version": payload.parser_version,
        "docling_json": payload.docling_json,
        "metadata": payload.metadata,
    }


def _payload_from_wire(payload: dict) -> ExtractionPayload:
    return ExtractionPayload(
        text=payload["text"],
        blocks=[
            TextBlock(
                text=block["text"],
                heading=block.get("heading"),
                section=block.get("section"),
                page=block.get("page"),
                char_start=block.get("char_start"),
                char_end=block.get("char_end"),
            )
            for block in payload.get("blocks", [])
        ],
        parser_name=payload["parser_name"],
        parser_version=payload["parser_version"],
        docling_json=payload.get("docling_json"),
        metadata=payload.get("metadata"),
    )


def _docling_converter(
    artifact_path: Path,
    *,
    ocr_enabled: bool,
    timeout_seconds: float | None,
):  # noqa: ANN202
    if artifact_path.suffix.lower() != ".pdf":
        return _docling_default_converter()
    return _docling_pdf_converter(ocr_enabled=ocr_enabled, timeout_seconds=timeout_seconds)


@lru_cache(maxsize=1)
def _docling_default_converter():  # noqa: ANN202
    from docling.document_converter import DocumentConverter
    return DocumentConverter()


@lru_cache(maxsize=8)
def _docling_pdf_converter(
    *,
    ocr_enabled: bool,
    timeout_seconds: float | None,
):  # noqa: ANN202
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import PdfFormatOption
    from docling.document_converter import DocumentConverter

    pipeline_options = PdfPipelineOptions(
        document_timeout=timeout_seconds,
        do_ocr=ocr_enabled,
    )
    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
    )


def _docling_text(document) -> str:  # noqa: ANN001
    for method_name in ("export_to_markdown", "export_to_text"):
        method = getattr(document, method_name, None)
        if callable(method):
            text = method()
            if text:
                return str(text)
    return str(document)


def _docling_json(document) -> dict | None:  # noqa: ANN001
    for method_name in ("export_to_dict", "model_dump", "dict"):
        method = getattr(document, method_name, None)
        if callable(method):
            try:
                value = method()
            except TypeError:
                continue
            if isinstance(value, dict):
                return value
    return None
