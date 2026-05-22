from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
import re

from .source_set_support import source_derived_dir


INDEX_SCHEMA_VERSION = "retrieval-index-v1"
RETRIEVAL_EVAL_SCHEMA_VERSION = "retrieval-eval-v1"
RETRIEVAL_EVAL_RESULTS_SCHEMA_VERSION = "retrieval-eval-results-v1"
DEFAULT_INDEX_FILENAME = "evidence_index.sqlite"
TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9'-]{1,}")
STOPWORDS = {
    "about",
    "also",
    "and",
    "are",
    "for",
    "from",
    "has",
    "have",
    "into",
    "its",
    "not",
    "that",
    "the",
    "their",
    "this",
    "was",
    "were",
    "what",
    "when",
    "where",
    "which",
    "with",
}
REQUIRED_CHUNK_FIELDS = {
    "chunk_id",
    "source_set_id",
    "source_record_id",
    "title",
    "document_role",
    "support_document_role",
    "authority_level",
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
    "text",
}


@dataclass(frozen=True)
class RetrievalIndexBuildResult:
    source_set_id: str
    index_dir: Path
    sqlite_path: Path
    manifest_path: Path
    validation_path: Path
    summary_path: Path
    summary: dict


@dataclass(frozen=True)
class RetrievalEvalResult:
    index_path: Path
    eval_file: Path
    output_path: Path
    summary: dict


def default_index_path(output_dir: Path, source_set_id: str | None = None) -> Path:
    output_dir = Path(output_dir)
    if source_set_id is None:
        source_set_id = _source_set_id_from_catalog(output_dir)
    derived_source_dir = source_derived_dir(output_dir / "derived", source_set_id)
    return derived_source_dir / "retrieval" / DEFAULT_INDEX_FILENAME


def _source_set_id_from_catalog(output_dir: Path) -> str:
    manifest_path = output_dir / "catalog" / "source_set_manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing source-set manifest: {manifest_path}")
    manifest = _read_json(manifest_path)
    source_set_id = manifest.get("source_set_id")
    if not source_set_id:
        raise ValueError(f"source_set_manifest.json has no source_set_id: {manifest_path}")
    return str(source_set_id)


def _source_set_id_from_index_path(index_path: Path) -> str:
    if index_path.parent.name != "retrieval":
        raise ValueError(f"Retrieval index path must live under a retrieval directory: {index_path}")
    return index_path.parent.parent.name


def _int_from_summary(extraction_summary: dict | None, key: str) -> int:
    if not extraction_summary:
        return 0
    try:
        return int(extraction_summary.get(key) or 0)
    except (TypeError, ValueError):
        return 0


def _resolve_existing_path(output_dir: Path, value: object | None) -> Path | None:
    if not value:
        return None
    path = Path(str(value))
    candidates = (
        [path]
        if path.is_absolute()
        else [path, output_dir / path, output_dir.parent / path]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _rate(count: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(count / total, 6)
