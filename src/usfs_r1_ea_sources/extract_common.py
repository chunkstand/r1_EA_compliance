from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import html
import json
import re
from urllib.parse import unquote, urlparse


DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
DOC_CONTENT_TYPE = "application/msword"
PDF_TEXT_FALLBACK_ERROR_CLASSES = {"docling_timeout", "docling_unavailable"}
PDF_TEXT_FALLBACK_MAX_DECOMPRESS_BYTES = 512 * 1024 * 1024
CHUNKED_DOCLING_PDF_PAGE_COUNT = 10
CHUNKED_DOCLING_PDF_MIN_TIMEOUT_SECONDS = 180.0
PDF_RASTER_OCR_DPI = 100
PDF_RASTER_OCR_PARALLEL_MIN_PAGES = 24
PDF_RASTER_OCR_MAX_WORKERS = 4
APPLE_VISION_OCR_TIMEOUT_SECONDS = 600.0
DOCLING_PYTHON_ENV_VAR = "USFS_R1_DOCLING_PYTHON"
SUCCESS_STATUSES = {"downloaded", "downloaded_existing", "duplicate_content", "duplicate_url"}
NON_EXTRACTABLE_SOURCE_STATUSES = {"skipped_excluded"}
CURRENT_REUSE_INVENTORY_CLASSIFICATIONS = {"already_current", "already_current_cg_slice"}
TERMINAL_STATUSES = {
    "extracted",
    "skipped_excluded",
    "no_artifact",
    "artifact_missing",
    "hash_mismatch",
    "placeholder_artifact",
    "parser_error",
    "parser_timeout",
    "empty_text",
}
REQUIRED_CHUNK_PROVENANCE = {
    "source_set_id",
    "source_record_id",
    "artifact_sha256",
    "artifact_path",
    "citation_label",
    "original_url",
    "effective_url",
    "final_url",
    "parser_name",
    "parser_version",
    "extracted_at",
    "char_start",
    "char_end",
    "content_sha256",
}
DIRECT_DOCUMENT_URL_CLASSES = {
    "Official DOJ PDF",
    "Official FS media PDF",
    "Official FWS document",
    "Official Forest Service PDF",
    "Official Forest Service directive PDF",
    "Official Forest Service directive document",
    "Official Forest Service/RMRS PDF",
    "Official USDA guidance PDF",
    "Official USFS direct file",
}
DOCLING_PRIORITY_KEYWORDS = (
    "docling:",
    "table",
    "map",
    "page labels",
    "direct file",
    "pdf/doc",
    "chapter/handbook pdf/doc",
)
DIRECT_DOCUMENT_REQUIRED_INSTRUCTION_KEYWORDS = (
    "manual pinyon/box export",
    "extract direct usfs media file",
    "extract full direct file",
    "chapter/handbook pdf/doc",
)
WEB_SOURCE_DIRECT_DOCUMENT_REQUIRED_INSTRUCTION_KEYWORDS = (
    "first export/download the direct file",
)
DOCLING_OCR_KEYWORDS = ("appendix maps", "map", "scanned", "ocr")
MARKUP_TOKEN_RE = re.compile(r"</?[A-Za-z][A-Za-z0-9:_-]{0,30}>")
PROVING_PLACEHOLDER_ARTIFACT_SCHEMA_VERSION = "source-register-proving-artifact-v1"


@dataclass(frozen=True)
class ExtractionBuildResult:
    source_set_id: str
    derived_dir: Path
    extracted_text_dir: Path
    docling_json_dir: Path
    chunks_path: Path
    extraction_manifest_path: Path
    validation_path: Path
    summary_path: Path
    summary: dict


@dataclass(frozen=True)
class TextBlock:
    text: str
    heading: str | None = None
    section: str | None = None
    page: int | None = None
    char_start: int | None = None
    char_end: int | None = None


@dataclass(frozen=True)
class ExtractionPayload:
    text: str
    blocks: list[TextBlock]
    parser_name: str
    parser_version: str
    docling_json: dict | None = None
    metadata: dict | None = None


class ExtractionFailure(Exception):
    def __init__(self, error_class: str, message: str) -> None:
        super().__init__(message)
        self.error_class = error_class
        self.message = message


def _canonical_metadata_text(row: dict, key: str) -> str:
    return str((row.get("metadata") or {}).get(key) or "").strip()


def _normalized_planning_text(value: object) -> str:
    return str(value or "").strip().lower()


def _is_source_register_v1_row(row: dict) -> bool:
    return _canonical_metadata_text(row, "loader_contract") == "source_register_v1"


def _load_proving_placeholder_artifact(artifact_path: Path) -> dict | None:
    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    if payload.get("schema_version") != PROVING_PLACEHOLDER_ARTIFACT_SCHEMA_VERSION:
        return None
    return payload


def _requires_direct_document_artifact(row: dict) -> bool:
    if not _is_source_register_v1_row(row):
        return False
    parser_admission_class = _canonical_metadata_text(row, "parser_admission_class")
    if parser_admission_class == "direct_document":
        return True
    url_class = _canonical_metadata_text(row, "url_class")
    if url_class in DIRECT_DOCUMENT_URL_CLASSES:
        return True
    instruction_text = _normalized_planning_text(
        _canonical_metadata_text(row, "docling_instructions")
    )
    if any(
        keyword in instruction_text
        for keyword in DIRECT_DOCUMENT_REQUIRED_INSTRUCTION_KEYWORDS
    ):
        return True
    return parser_admission_class == "web_source" and any(
        keyword in instruction_text
        for keyword in WEB_SOURCE_DIRECT_DOCUMENT_REQUIRED_INSTRUCTION_KEYWORDS
    )


def _prefers_docling_for_row(row: dict) -> bool:
    if not _is_source_register_v1_row(row):
        return False
    if str(row.get("expected_parser") or "").lower() in {"pdf", "docx"}:
        return True
    if _requires_direct_document_artifact(row):
        return True
    docling_text = " ".join(
        [
            _normalized_planning_text(_canonical_metadata_text(row, "docling_instructions")),
            _normalized_planning_text(row.get("document_type")),
        ]
    )
    return any(keyword in docling_text for keyword in DOCLING_PRIORITY_KEYWORDS)


def _docling_ocr_for_row(row: dict) -> bool:
    if not _is_source_register_v1_row(row):
        return False
    docling_text = " ".join(
        [
            _normalized_planning_text(_canonical_metadata_text(row, "docling_instructions")),
            _normalized_planning_text(row.get("document_type")),
        ]
    )
    return any(keyword in docling_text for keyword in DOCLING_OCR_KEYWORDS)


def _extraction_priority(row: dict) -> str:
    if not _is_source_register_v1_row(row):
        return "legacy_standard"
    source_partition = str(row.get("source_partition") or "").strip()
    currentness_status = _normalized_planning_text(
        _canonical_metadata_text(row, "currentness_status")
    )
    parser_admission_class = _canonical_metadata_text(row, "parser_admission_class")
    if source_partition == "currentness_supersession_archive" or "superseded" in currentness_status:
        return "currentness_archive"
    if _requires_direct_document_artifact(row):
        return "direct_document_verification"
    if parser_admission_class == "structured_web_source":
        return "structured_authority_capture"
    if parser_admission_class == "web_source":
        return "web_fallback_capture"
    return "canonical_standard"


def _base_manifest_record(*, row: dict, extracted_at: str) -> dict:
    support_document_role = str(
        (row.get("metadata") or {}).get("document_role")
        or row.get("document_role")
        or ""
    )
    return {
        "source_set_id": row["source_set_id"],
        "source_record_id": row["source_record_id"],
        "title": row["title"],
        "document_role": row["document_role"],
        "support_document_role": support_document_role,
        "authority_level": row["authority_level"],
        "host": row["host"],
        "document_type": row.get("document_type"),
        "source_partition": row.get("source_partition"),
        "source_partition_basis": row.get("source_partition_basis"),
        "expected_parser": row["expected_parser"],
        "loader_contract": _canonical_metadata_text(row, "loader_contract") or None,
        "currentness_status": _canonical_metadata_text(row, "currentness_status") or None,
        "url_class": _canonical_metadata_text(row, "url_class") or None,
        "parser_admission_class": _canonical_metadata_text(row, "parser_admission_class")
        or None,
        "direct_file_readiness_class": _canonical_metadata_text(
            row,
            "direct_file_readiness_class",
        )
        or None,
        "docling_instructions": _canonical_metadata_text(row, "docling_instructions")
        or None,
        "extraction_priority": _extraction_priority(row),
        "direct_document_artifact_required": _requires_direct_document_artifact(row),
        "artifact_is_proving_placeholder": False,
        "proving_placeholder_schema_version": None,
        "source_status": row["source_status"],
        "download_run_id": row.get("download_run_id"),
        "artifact_sha256": row.get("artifact_sha256"),
        "artifact_path": row.get("artifact_path"),
        "artifact_byte_size": row.get("artifact_byte_size"),
        "content_type": row.get("content_type"),
        "citation_label": row.get("citation_label"),
        "original_url": row.get("original_url"),
        "effective_url": row.get("effective_url"),
        "final_url": _final_url(row),
        "retrieved_at": row.get("retrieved_at"),
        "extracted_at": extracted_at,
        "status": None,
        "artifact_sha256_verified": None,
        "actual_artifact_sha256": None,
        "parser_name": None,
        "parser_version": None,
        "parser_metadata": None,
        "text_path": None,
        "docling_json_path": None,
        "text_char_count": 0,
        "text_sha256": None,
        "chunk_count": 0,
        "failure": None,
    }


def _failed_record(base_record: dict, *, status: str, error_class: str, message: str) -> dict:
    record = dict(base_record)
    record.update(
        {
            "status": status,
            "failure": {
                "error_class": error_class,
                "error_message": message,
            },
        }
    )
    return record


def _skipped_record(base_record: dict, *, status: str, reason: str) -> dict:
    record = dict(base_record)
    record.update(
        {
            "status": status,
            "artifact_sha256_verified": None,
            "parser_metadata": {"skip_reason": reason},
            "failure": None,
        }
    )
    return record


def _effective_parser(row: dict, artifact_path: Path) -> str:
    expected = (row.get("expected_parser") or "").lower()
    content_type = (row.get("content_type") or "").lower()
    suffix = artifact_path.suffix.lower()
    if content_type == "application/zip" or suffix == ".zip":
        return "zip"
    if expected in {"html", "xml", "pdf", "docx", "doc", "image", "xlsx"}:
        return expected
    if expected == "structured_web_adapter":
        if content_type in {"application/xml", "text/xml"} or suffix == ".xml":
            return "xml"
        return "html"
    if content_type == "application/pdf" or suffix == ".pdf":
        return "pdf"
    if content_type == DOC_CONTENT_TYPE or suffix == ".doc":
        return "doc"
    if content_type in {"application/xml", "text/xml"} or suffix == ".xml":
        return "xml"
    if content_type in {"text/html", "application/xhtml+xml"} or suffix in {".html", ".htm"}:
        return "html"
    if content_type == DOCX_CONTENT_TYPE or suffix == ".docx":
        return "docx"
    if (
        content_type
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        or suffix == ".xlsx"
    ):
        return "xlsx"
    if content_type.startswith("image/") or suffix in {".jpg", ".jpeg", ".png"}:
        return "image"
    if content_type.startswith("text/"):
        return "text"
    return expected or "text"


def _resolve_artifact_path(output_dir: Path, artifact_path: str) -> Path:
    path = Path(artifact_path)
    if path.is_absolute():
        return path
    if path.exists():
        return path
    return output_dir / path


def _resolve_existing_path(output_dir: Path, value: object | None) -> Path | None:
    if not value:
        return None
    path = Path(str(value))
    candidates = [path] if path.is_absolute() else [path, output_dir / path, output_dir.parent / path]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _text_path(extracted_text_dir: Path, *, source_record_id: str, artifact_sha256: str) -> Path:
    return extracted_text_dir / f"{source_record_id}_{artifact_sha256[:16]}.txt"


def _payload_cache_path(payload_cache_dir: Path, row: dict) -> Path:
    source_record_id = str(row["source_record_id"])
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", source_record_id):
        raise ValueError(f"Unsafe source_record_id for payload cache path: {source_record_id!r}")
    artifact_sha256 = str(row["artifact_sha256"])
    return payload_cache_dir / f"{source_record_id}_{artifact_sha256[:16]}.json"


def _parser_metadata_with_reuse(metadata: dict | None, *, reused: bool) -> dict | None:
    if not reused:
        return metadata
    return {**(metadata or {}), "reused_existing": True}


def _final_url(row: dict) -> str | None:
    return row.get("artifact_final_url") or row.get("citation_final_url") or row.get("effective_url")


def _decode_bytes(body: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return body.decode(encoding)
        except UnicodeDecodeError:
            continue
    return body.decode("utf-8", errors="replace")


def _clean_text(value: str) -> str:
    text = html.unescape(value)
    text = MARKUP_TOKEN_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_reuse_inventory_records(
    reuse_inventory_path: Path | None,
    *,
    source_set_id: str,
) -> dict[str, dict] | None:
    if reuse_inventory_path is None:
        return None
    raw_records = _load_reuse_inventory_payload_records(Path(reuse_inventory_path))
    records: dict[str, dict] = {}
    for record in raw_records:
        if record.get("source_set_id") != source_set_id:
            raise ValueError(
                "Reuse inventory source_set_id does not match catalog source_set_id: "
                f"{record.get('source_set_id')} != {source_set_id}"
            )
        source_record_id = str(record.get("source_record_id") or "")
        if source_record_id:
            records[source_record_id] = record
    return records


def _load_reuse_inventory_payload_records(path: Path) -> list[dict]:
    if path.is_dir():
        return _read_jsonl(path / "reuse_inventory_records.jsonl")
    if path.name == "reuse_inventory.json":
        payload = _read_json(path)
        records = payload.get("records")
        if isinstance(records, list):
            return [record for record in records if isinstance(record, dict)]
        sibling_records = path.parent / "reuse_inventory_records.jsonl"
        return _read_jsonl(sibling_records)
    if path.name == "summary.json":
        return _read_jsonl(path.parent / "reuse_inventory_records.jsonl")
    return _read_jsonl(path)


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Missing JSONL file: {path}")
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def _xml_local_name(tag: str) -> str:
    if "}" in tag:
        tag = tag.rsplit("}", 1)[1]
    return tag.upper()


def _xml_scope_for_row(row: dict | None) -> dict | None:
    if not row:
        return None
    host = (row.get("host") or "").lower()
    urls = [
        row.get("artifact_final_url"),
        row.get("citation_final_url"),
        row.get("effective_url"),
        row.get("normalized_url"),
        row.get("original_url"),
    ]
    for value in urls:
        if not value:
            continue
        parsed = urlparse(str(value))
        if parsed.netloc and "ecfr.gov" not in parsed.netloc.lower() and "ecfr.gov" not in host:
            continue
        path = unquote(parsed.path or str(value))
        for segment in path.split("/"):
            lowered = segment.lower()
            if lowered.startswith("section-"):
                identifier = segment.split("-", 1)[1]
                if identifier:
                    return {"type": "SECTION", "identifier": identifier, "url": str(value)}
            if lowered.startswith("subpart-"):
                identifier = segment.split("-", 1)[1]
                if identifier:
                    return {
                        "type": "SUBPART",
                        "identifier": identifier.upper(),
                        "url": str(value),
                    }
    return None


def _normalize_xml_scope_identifier(value: object) -> str:
    return str(value or "").strip().lower()
