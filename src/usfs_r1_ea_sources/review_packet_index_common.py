from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .pdf_object_writer import write_line_pdf


ROW_INVENTORY_SCHEMA_VERSION = "review-packet-row-inventory-v1"
RENDER_MANIFEST_SCHEMA_VERSION = "compliance-matrix-render-manifest-v1"
PACKET_INDEX_SCHEMA_VERSION = "review-packet-index-v1"
VALIDATION_SCHEMA_VERSION = "review-packet-index-validation-v1"
GENERATOR_VERSION = "review-packet-index-v1"

ROW_INVENTORY_FILENAME = "review_packet_row_inventory.json"
ROW_INVENTORY_MARKDOWN_FILENAME = "review_packet_row_inventory.md"
RENDER_MANIFEST_FILENAME = "compliance_matrix_render_manifest.json"
PACKET_INDEX_FILENAME = "review_packet_index.json"
PACKET_INDEX_MARKDOWN_FILENAME = "review_packet_index.md"
PACKET_INDEX_PDF_FILENAME = "review_packet_index.pdf"
VALIDATION_FILENAME = "review_packet_index_validation.json"

LAND_EXCHANGE_RULE_SOURCES = {
    "flpma_section_206_land_exchange": "R1EA-146",
    "land_exchange_statutory_authorities": "R1EA-137",
    "land_exchange_regulatory_requirements": "R1EA-124",
    "land_exchange_fs_policy_and_project_references": "R1EA-150",
}


@dataclass(frozen=True)
class ReviewPacketIndexResult:
    output_dir: Path
    row_inventory_path: Path
    row_inventory_markdown_path: Path
    render_manifest_path: Path
    packet_index_path: Path
    packet_index_markdown_path: Path
    packet_index_pdf_path: Path
    validation_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class _OutputPaths:
    row_inventory_path: Path
    row_inventory_markdown_path: Path
    render_manifest_path: Path
    packet_index_path: Path
    packet_index_markdown_path: Path
    packet_index_pdf_path: Path
    validation_path: Path


@dataclass(frozen=True)
class _Artifact:
    key: str
    path: Path
    required: bool
    artifact_type: str
    payload: Any
    text: str
    exists: bool
    parse_ok: bool
    sha256: str | None
    error: str | None = None


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _dict_list(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _strings(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item not in (None, "")]
    if value in (None, ""):
        return []
    return [str(value)]


def _md_cell(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _row_set_sha256(rows: list[dict[str, Any]]) -> str:
    return _sha256_json(
        [
            {
                "row_class": row.get("row_class"),
                "row_identity": row.get("row_identity"),
                "row_hash": row.get("row_hash"),
            }
            for row in rows
        ]
    )


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_simple_pdf(path: Path, lines: list[str]) -> None:
    write_line_pdf(path, lines)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _selector(path: Path, selector: str) -> dict[str, str]:
    return {"artifact_path": str(path), "selector": selector}


def _matrix_row_marker(row_class: str, row_id: object) -> str:
    return f"matrix-row:{row_class}:{_safe_marker_id(row_id)}"


def _safe_marker_id(value: object) -> str:
    text = str(value or "unknown")
    return re.sub(r"[^A-Za-z0-9_.:-]+", "-", text).strip("-") or "unknown"
