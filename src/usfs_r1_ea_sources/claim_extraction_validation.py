from __future__ import annotations

from collections import Counter
from contextlib import closing
from pathlib import Path
import sqlite3

from .artifact_utils import _extraction_summary_is_complete
from .artifact_utils import _int_from_summary
from .artifact_utils import _read_json
from .artifact_utils import _read_jsonl
from .artifact_utils import _safe_int
from .claim_extraction_runtime import CLAIM_PATTERNS
from .claim_extraction_runtime import SUPPORTED_CLAIM_TYPES
from .claim_extraction_runtime import _claim_metrics
from .claim_extraction_runtime import _text_sha256
from .source_set_support import source_derived_dir


DEFAULT_RETRIEVAL_INDEX_FILENAME = "evidence_index.sqlite"
REQUIRED_CLAIM_FIELDS = {
    "claim_id",
    "source_set_id",
    "source_record_id",
    "chunk_id",
    "claim_type",
    "claim_text",
    "citation_label",
    "authority_level",
    "document_role",
    "artifact_sha256",
    "artifact_path",
    "parser_name",
    "parser_version",
    "source_char_start",
    "source_char_end",
    "chunk_char_start",
    "chunk_char_end",
    "content_sha256",
    "chunk_content_sha256",
    "extractor_name",
    "extractor_version",
    "validation_status",
}


def validate_claim_outputs(
    *,
    output_dir: Path,
    source_set_id: str,
    claims_path: Path,
    entities_path: Path,
    nodes_path: Path,
    edges_path: Path,
    chunks_path: Path,
    extraction_validation_path: Path | None = None,
    extraction_validation: dict | None = None,
    extraction_summary_path: Path | None = None,
    extraction_summary: dict | None = None,
    retrieval_validation_path: Path | None = None,
    retrieval_validation: dict | None = None,
    retrieval_summary_path: Path | None = None,
    retrieval_summary: dict | None = None,
    retrieval_index_path: Path | None = None,
    retrieval_index_records: dict[str, dict] | None = None,
    retrieval_index_error: str | None = None,
    chunks: list[dict] | None = None,
    claims: list[dict] | None = None,
    entities: list[dict] | None = None,
    nodes: list[dict] | None = None,
    edges: list[dict] | None = None,
    metrics: dict | None = None,
    allow_partial_retrieval: bool = False,
) -> dict:
    output_dir = Path(output_dir)
    derived_source_dir = source_derived_dir(output_dir / "derived", source_set_id)
    extraction_validation_path = (
        extraction_validation_path
        or derived_source_dir / "diagnostics" / "extraction_validation.json"
    )
    extraction_summary_path = (
        extraction_summary_path or derived_source_dir / "diagnostics" / "summary.json"
    )
    retrieval_validation_path = (
        retrieval_validation_path or derived_source_dir / "retrieval" / "retrieval_validation.json"
    )
    retrieval_summary_path = retrieval_summary_path or derived_source_dir / "retrieval" / "summary.json"
    if extraction_validation is None and extraction_validation_path.exists():
        extraction_validation = _read_json(extraction_validation_path)
    if extraction_summary is None and extraction_summary_path.exists():
        extraction_summary = _read_json(extraction_summary_path)
    if retrieval_validation is None and retrieval_validation_path.exists():
        retrieval_validation = _read_json(retrieval_validation_path)
    if retrieval_summary is None and retrieval_summary_path.exists():
        retrieval_summary = _read_json(retrieval_summary_path)
    retrieval_index_path = retrieval_index_path or _retrieval_index_path(
        derived_source_dir,
        retrieval_summary,
    )
    if retrieval_index_records is None:
        retrieval_index_records, retrieval_index_error = _load_retrieval_index_records(
            retrieval_index_path
        )
    chunks = chunks if chunks is not None else (_read_jsonl(chunks_path) if chunks_path.exists() else [])
    claims = claims if claims is not None else (_read_jsonl(claims_path) if claims_path.exists() else [])
    entities = (
        entities if entities is not None else (_read_jsonl(entities_path) if entities_path.exists() else [])
    )
    nodes = nodes if nodes is not None else (_read_jsonl(nodes_path) if nodes_path.exists() else [])
    edges = edges if edges is not None else (_read_jsonl(edges_path) if edges_path.exists() else [])
    metrics = metrics or _claim_metrics(claims=claims, entities=entities, nodes=nodes, edges=edges)

    checks = [
        {
            "name": "extraction_validation_passed",
            "passed": bool(extraction_validation and extraction_validation.get("passed")),
            "details": {
                "path": str(extraction_validation_path),
                "exists": extraction_validation_path.exists(),
                "passed": bool(extraction_validation and extraction_validation.get("passed")),
            },
        },
        {
            "name": "extraction_scope_is_complete",
            "passed": _extraction_summary_is_complete(extraction_summary)
            or allow_partial_retrieval,
            "details": {
                "path": str(extraction_summary_path),
                "exists": extraction_summary_path.exists(),
                "allow_partial_retrieval": allow_partial_retrieval,
                "complete": _extraction_summary_is_complete(extraction_summary),
                "catalog_source_count": _int_from_summary(
                    extraction_summary,
                    "catalog_source_count",
                ),
                "selected_source_count": _int_from_summary(
                    extraction_summary,
                    "selected_source_count",
                ),
                "required_extraction_source_count": _int_from_summary(
                    extraction_summary,
                    "required_extraction_source_count",
                ),
                "selected_required_extraction_source_count": _int_from_summary(
                    extraction_summary,
                    "selected_required_extraction_source_count",
                ),
                "extracted_count": _int_from_summary(extraction_summary, "extracted_count"),
                "failed_count": _int_from_summary(extraction_summary, "failed_count"),
                "skipped_excluded_count": _int_from_summary(
                    extraction_summary,
                    "skipped_excluded_count",
                ),
                "filters": (extraction_summary or {}).get("filters", {}),
            },
        },
        {
            "name": "retrieval_validation_passed",
            "passed": bool(retrieval_validation and retrieval_validation.get("passed")),
            "details": {
                "path": str(retrieval_validation_path),
                "exists": retrieval_validation_path.exists(),
                "passed": bool(retrieval_validation and retrieval_validation.get("passed")),
            },
        },
        {
            "name": "retrieval_is_reviewer_ready",
            "passed": bool(retrieval_summary and retrieval_summary.get("reviewer_ready"))
            or allow_partial_retrieval,
            "details": {
                "path": str(retrieval_summary_path),
                "exists": retrieval_summary_path.exists(),
                "allow_partial_retrieval": allow_partial_retrieval,
                "reviewer_ready": bool(
                    retrieval_summary and retrieval_summary.get("reviewer_ready")
                ),
            },
        },
        _check_retrieval_index_readable(
            retrieval_index_path,
            retrieval_index_records,
            retrieval_index_error,
        ),
        {
            "name": "claims_jsonl_exists",
            "passed": claims_path.exists(),
            "details": {"path": str(claims_path)},
        },
        {
            "name": "entities_jsonl_exists",
            "passed": entities_path.exists(),
            "details": {"path": str(entities_path)},
        },
        {
            "name": "claim_graph_jsonl_exists",
            "passed": nodes_path.exists() and edges_path.exists(),
            "details": {"nodes_path": str(nodes_path), "edges_path": str(edges_path)},
        },
        _check_claims_loaded(claims),
        _check_unique_ids(claims, key="claim_id", check_name="claim_ids_are_unique"),
        _check_unique_ids(entities, key="entity_id", check_name="entity_ids_are_unique"),
        _check_required_claim_fields(claims),
        _check_claim_types_supported(claims),
        _check_claim_source_set_ids_match(source_set_id, claims),
        _check_claim_chunk_ids_resolve(chunks, claims),
        _check_claim_offsets_match_chunk_text(chunks, claims),
        _check_claim_offsets_match_source_text(output_dir, chunks, claims),
        _check_claim_content_hashes(claims),
        _check_claims_match_retrieval_index(
            chunks,
            claims,
            retrieval_index_records,
            retrieval_index_error,
        ),
        _check_no_unsupported_claims(claims),
        _check_entities_resolve_to_claims(claims, entities),
        _check_graph_integrity(claims, entities, nodes, edges),
        _check_graph_health(metrics),
    ]
    strict_blockers = {
        "extraction_validation_passed",
        "extraction_scope_is_complete",
        "retrieval_is_reviewer_ready",
    }
    passed = all(check["passed"] for check in checks)
    if allow_partial_retrieval:
        passed = all(
            check["passed"] or check["name"] in strict_blockers
            for check in checks
        )
    return {
        "source_set_id": source_set_id,
        "passed": passed,
        "checks": checks,
        "metrics": metrics,
    }


def _check_retrieval_index_readable(
    index_path: Path,
    retrieval_index_records: dict[str, dict] | None,
    retrieval_index_error: str | None,
) -> dict:
    records = retrieval_index_records or {}
    return {
        "name": "retrieval_index_exists_and_readable",
        "passed": retrieval_index_error is None and bool(records),
        "details": {
            "path": str(index_path),
            "exists": index_path.exists(),
            "error": retrieval_index_error,
            "chunk_count": len(records),
        },
    }


def _check_claims_loaded(claims: list[dict]) -> dict:
    return {
        "name": "claims_loaded",
        "passed": bool(claims),
        "details": {"claim_count": len(claims)},
    }


def _check_unique_ids(records: list[dict], *, key: str, check_name: str) -> dict:
    counts = Counter(record.get(key) for record in records)
    duplicates = sorted(record_id for record_id, count in counts.items() if record_id and count > 1)
    return {
        "name": check_name,
        "passed": not duplicates,
        "details": {"duplicate_ids": duplicates[:50], "duplicate_count": len(duplicates)},
    }


def _check_required_claim_fields(claims: list[dict]) -> dict:
    failures = []
    for claim in claims:
        missing = [
            field for field in sorted(REQUIRED_CLAIM_FIELDS) if claim.get(field) in (None, "")
        ]
        if missing:
            failures.append({"claim_id": claim.get("claim_id"), "missing_fields": missing})
    return {
        "name": "claims_have_required_provenance",
        "passed": not failures and bool(claims),
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_claim_types_supported(claims: list[dict]) -> dict:
    failures = [
        {"claim_id": claim.get("claim_id"), "claim_type": claim.get("claim_type")}
        for claim in claims
        if claim.get("claim_type") not in SUPPORTED_CLAIM_TYPES
    ]
    return {
        "name": "claim_types_are_supported",
        "passed": not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_claim_source_set_ids_match(source_set_id: str, claims: list[dict]) -> dict:
    mismatches = [
        {
            "claim_id": claim.get("claim_id"),
            "expected_source_set_id": source_set_id,
            "actual_source_set_id": claim.get("source_set_id"),
        }
        for claim in claims
        if claim.get("source_set_id") != source_set_id
    ]
    return {
        "name": "claim_source_set_ids_match",
        "passed": not mismatches and bool(claims),
        "details": {"mismatches": mismatches[:50], "mismatch_count": len(mismatches)},
    }


def _check_claim_chunk_ids_resolve(chunks: list[dict], claims: list[dict]) -> dict:
    chunk_ids = {str(chunk.get("chunk_id")) for chunk in chunks if chunk.get("chunk_id")}
    missing = [
        {"claim_id": claim.get("claim_id"), "chunk_id": claim.get("chunk_id")}
        for claim in claims
        if str(claim.get("chunk_id")) not in chunk_ids
    ]
    return {
        "name": "claim_chunk_ids_resolve",
        "passed": bool(chunks) and not missing,
        "details": {"missing": missing[:50], "missing_count": len(missing)},
    }


def _check_claim_offsets_match_chunk_text(chunks: list[dict], claims: list[dict]) -> dict:
    chunks_by_id = {str(chunk.get("chunk_id")): chunk for chunk in chunks if chunk.get("chunk_id")}
    mismatches = []
    for claim in claims:
        chunk = chunks_by_id.get(str(claim.get("chunk_id")))
        if not chunk:
            continue
        try:
            start = int(claim["chunk_char_start"])
            end = int(claim["chunk_char_end"])
        except (KeyError, TypeError, ValueError):
            mismatches.append({"claim_id": claim.get("claim_id"), "reason": "invalid_offsets"})
            continue
        text = str(chunk.get("text") or "")
        if start < 0 or end <= start or end > len(text):
            mismatches.append({"claim_id": claim.get("claim_id"), "reason": "offset_out_of_range"})
            continue
        if text[start:end] != claim.get("claim_text"):
            mismatches.append({"claim_id": claim.get("claim_id"), "reason": "text_mismatch"})
    return {
        "name": "claim_offsets_match_chunk_text",
        "passed": bool(claims) and not mismatches,
        "details": {"mismatches": mismatches[:50], "mismatch_count": len(mismatches)},
    }


def _check_claim_offsets_match_source_text(
    output_dir: Path,
    chunks: list[dict],
    claims: list[dict],
) -> dict:
    chunks_by_id = {str(chunk.get("chunk_id")): chunk for chunk in chunks if chunk.get("chunk_id")}
    text_cache: dict[str, str | None] = {}
    mismatches = []
    for claim in claims:
        chunk = chunks_by_id.get(str(claim.get("chunk_id")))
        if not chunk:
            continue
        path_value = claim.get("source_text_path") or chunk.get("source_text_path")
        if not path_value:
            mismatches.append({"claim_id": claim.get("claim_id"), "reason": "missing_text_path"})
            continue
        path_key = str(path_value)
        if path_key not in text_cache:
            path = _resolve_path(output_dir, path_key)
            text_cache[path_key] = path.read_text(encoding="utf-8") if path.exists() else None
        source_text = text_cache[path_key]
        if source_text is None:
            mismatches.append({"claim_id": claim.get("claim_id"), "reason": "missing_text_file"})
            continue
        try:
            start = int(claim["source_char_start"])
            end = int(claim["source_char_end"])
        except (KeyError, TypeError, ValueError):
            mismatches.append({"claim_id": claim.get("claim_id"), "reason": "invalid_offsets"})
            continue
        if start < 0 or end <= start or end > len(source_text):
            mismatches.append({"claim_id": claim.get("claim_id"), "reason": "offset_out_of_range"})
            continue
        if source_text[start:end] != claim.get("claim_text"):
            mismatches.append({"claim_id": claim.get("claim_id"), "reason": "text_mismatch"})
    return {
        "name": "claim_offsets_match_source_text",
        "passed": bool(claims) and not mismatches,
        "details": {"mismatches": mismatches[:50], "mismatch_count": len(mismatches)},
    }


def _check_claim_content_hashes(claims: list[dict]) -> dict:
    failures = [
        claim.get("claim_id")
        for claim in claims
        if claim.get("content_sha256") != _text_sha256(str(claim.get("claim_text") or ""))
    ]
    return {
        "name": "claim_content_hashes_match_text",
        "passed": bool(claims) and not failures,
        "details": {"claim_ids": failures[:50], "failure_count": len(failures)},
    }


def _check_claims_match_retrieval_index(
    chunks: list[dict],
    claims: list[dict],
    retrieval_index_records: dict[str, dict] | None,
    retrieval_index_error: str | None,
) -> dict:
    index_records = retrieval_index_records or {}
    chunks_by_id = {str(chunk.get("chunk_id")): chunk for chunk in chunks if chunk.get("chunk_id")}
    mismatches = []
    for claim in claims:
        chunk_id = str(claim.get("chunk_id") or "")
        chunk = chunks_by_id.get(chunk_id)
        index_record = index_records.get(chunk_id)
        if not index_record:
            mismatches.append(
                {"claim_id": claim.get("claim_id"), "chunk_id": chunk_id, "reason": "missing_index"}
            )
            continue
        for field in (
            "source_set_id",
            "source_record_id",
            "artifact_sha256",
            "artifact_path",
            "citation_label",
            "parser_name",
            "parser_version",
            "content_sha256",
        ):
            expected = str((chunk or claim).get(field) or "")
            actual = str(index_record.get(field) or "")
            if expected != actual:
                mismatches.append(
                    {
                        "claim_id": claim.get("claim_id"),
                        "chunk_id": chunk_id,
                        "field": field,
                        "expected": expected,
                        "actual": actual,
                    }
                )
    return {
        "name": "claims_match_retrieval_index",
        "passed": retrieval_index_error is None and bool(claims) and not mismatches,
        "details": {
            "retrieval_index_error": retrieval_index_error,
            "mismatches": mismatches[:50],
            "mismatch_count": len(mismatches),
        },
    }


def _check_no_unsupported_claims(claims: list[dict]) -> dict:
    failures = []
    for claim in claims:
        if claim.get("validation_status") != "valid":
            failures.append({"claim_id": claim.get("claim_id"), "reason": "invalid_status"})
        if not claim.get("citation_label"):
            failures.append({"claim_id": claim.get("claim_id"), "reason": "missing_citation"})
        if claim.get("claim_type") not in SUPPORTED_CLAIM_TYPES:
            failures.append({"claim_id": claim.get("claim_id"), "reason": "unsupported_type"})
        if not any(pattern.pattern_id == claim.get("pattern_id") for pattern in CLAIM_PATTERNS):
            failures.append({"claim_id": claim.get("claim_id"), "reason": "unknown_pattern"})
    return {
        "name": "no_unsupported_claims_emitted",
        "passed": bool(claims) and not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_entities_resolve_to_claims(claims: list[dict], entities: list[dict]) -> dict:
    claim_ids = {str(claim["claim_id"]) for claim in claims}
    failures = []
    for entity in entities:
        entity_claim_ids = [str(claim_id) for claim_id in entity.get("claim_ids", [])]
        missing = sorted(set(entity_claim_ids) - claim_ids)
        if missing or not entity_claim_ids:
            failures.append({"entity_id": entity.get("entity_id"), "missing_claim_ids": missing})
    return {
        "name": "entities_resolve_to_claims",
        "passed": not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_graph_integrity(
    claims: list[dict],
    entities: list[dict],
    nodes: list[dict],
    edges: list[dict],
) -> dict:
    node_ids = {node.get("id") for node in nodes}
    edge_ids = [edge.get("id") for edge in edges]
    duplicate_edges = sorted(edge_id for edge_id, count in Counter(edge_ids).items() if count > 1)
    dangling = [
        edge.get("id")
        for edge in edges
        if edge.get("source") not in node_ids or edge.get("target") not in node_ids
    ]
    claim_node_ids = {node.get("id") for node in nodes if node.get("type") == "Claim"}
    entity_node_ids = {node.get("id") for node in nodes if node.get("type") == "Entity"}
    missing_claim_nodes = sorted({claim["claim_id"] for claim in claims} - claim_node_ids)
    missing_entity_nodes = sorted({entity["entity_id"] for entity in entities} - entity_node_ids)
    failures = []
    if duplicate_edges:
        failures.append({"reason": "duplicate_edges", "ids": duplicate_edges[:50]})
    if dangling:
        failures.append({"reason": "dangling_edges", "ids": dangling[:50]})
    if missing_claim_nodes:
        failures.append({"reason": "missing_claim_nodes", "ids": missing_claim_nodes[:50]})
    if missing_entity_nodes:
        failures.append({"reason": "missing_entity_nodes", "ids": missing_entity_nodes[:50]})
    return {
        "name": "claim_graph_node_edge_integrity",
        "passed": bool(nodes) and bool(edges) and not failures,
        "details": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "failures": failures,
        },
    }


def _check_graph_health(metrics: dict) -> dict:
    passed = (
        metrics["claim_count"] > 0
        and metrics["claim_node_count"] == metrics["claim_count"]
        and metrics["dangling_edge_count"] == 0
        and metrics["claim_evidence_coverage_rate"] == 1.0
        and metrics["claim_authority_coverage_rate"] == 1.0
        and metrics["claim_topic_coverage_rate"] == 1.0
    )
    return {
        "name": "claim_graph_health_metrics_pass",
        "passed": passed,
        "details": metrics,
    }


def _load_retrieval_index_records(index_path: Path) -> tuple[dict[str, dict], str | None]:
    if not index_path.exists():
        return {}, f"missing retrieval index: {index_path}"
    query = """
        SELECT
          chunk_id, source_set_id, source_record_id, artifact_sha256, artifact_path,
          citation_label, parser_name, parser_version, content_sha256
        FROM chunks
        ORDER BY source_record_id, chunk_index
    """
    try:
        with closing(sqlite3.connect(index_path)) as connection:
            connection.row_factory = sqlite3.Row
            return {str(row["chunk_id"]): dict(row) for row in connection.execute(query)}, None
    except sqlite3.Error as error:
        return {}, str(error)


def _with_additional_checks(
    validation: dict,
    checks: list[dict],
    *,
    allow_partial_retrieval: bool,
) -> dict:
    merged_checks = [*validation["checks"], *checks]
    ignored = {
        "extraction_validation_passed",
        "extraction_scope_is_complete",
        "retrieval_is_reviewer_ready",
    }
    passed = all(
        check["passed"] or (allow_partial_retrieval and check["name"] in ignored)
        for check in merged_checks
    )
    return {
        **validation,
        "passed": passed,
        "checks": merged_checks,
    }


def _retrieval_index_path(source_derived_dir: Path, retrieval_summary: dict | None) -> Path:
    summary_path = (retrieval_summary or {}).get("sqlite_path")
    if summary_path:
        return Path(str(summary_path))
    return source_derived_dir / "retrieval" / DEFAULT_RETRIEVAL_INDEX_FILENAME


def _check_detail_count(validation: dict, check_name: str, detail_key: str) -> int:
    for check in validation.get("checks", []):
        if check.get("name") == check_name:
            return _safe_int((check.get("details") or {}).get(detail_key))
    return 0


def _resolve_path(output_dir: Path, value: str) -> Path:
    path = Path(value)
    candidates = [path] if path.is_absolute() else [path, output_dir / path, output_dir.parent / path]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]
