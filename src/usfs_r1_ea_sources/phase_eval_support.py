from __future__ import annotations

import hashlib
from pathlib import Path

from .artifact_utils import _read_json
from .artifact_utils import _read_jsonl
from .artifact_utils import _safe_int


FRESHNESS_CHECK_NAMES = {
    "retrieval_index_exists_and_readable",
    "chunk_source_set_ids_match",
    "chunk_content_hashes_match_text",
    "chunks_match_retrieval_index",
    "evidence_span_content_matches_chunks",
}


def _phase(name: str, *, passed: bool, reviewer_ready: bool, details: dict) -> dict:
    failure_reasons = []
    if not passed:
        failure_reasons.append("phase_validation_failed")
    if not reviewer_ready:
        failure_reasons.append("phase_not_reviewer_ready")
    return {
        "name": name,
        "passed": passed,
        "reviewer_ready": reviewer_ready,
        "failure_reasons": failure_reasons,
        "details": details,
    }


def _failed_check_names(validation: dict | None) -> list[str]:
    if not validation:
        return []
    return [
        str(check.get("name"))
        for check in validation.get("checks", [])
        if isinstance(check, dict) and not check.get("passed")
    ]


def _freshness_status(validation: dict | None) -> str:
    if not validation:
        return "missing"
    failed = set(_failed_check_names(validation))
    return "failed" if failed & FRESHNESS_CHECK_NAMES else "passed"


def _current_queue_item_count(queue: dict) -> int:
    items = queue.get("items")
    if isinstance(items, list):
        return len(items)
    return _safe_int(queue.get("item_count"))


def _read_json_if_path(path: Path | None) -> dict:
    return _read_json(path) if path is not None and path.exists() else {}


def _read_jsonl_if_path(path: Path | None) -> list[dict]:
    return _read_jsonl(path) if path is not None and path.exists() else []


def _path_exists(path: Path | None) -> bool:
    return bool(path is not None and path.exists())


def _path_string(path: Path | None) -> str | None:
    return str(path) if path is not None else None


def _file_hash_matches(path: Path | None, expected: str | None) -> bool:
    return bool(path is not None and path.exists() and expected and _sha256_file(path) == expected)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _candidate_authority_ids(payload: dict) -> set[str]:
    return {
        str(candidate.get("candidate_authority_id") or "")
        for candidate in payload.get("candidate_authorities") or []
        if isinstance(candidate, dict) and candidate.get("candidate_authority_id")
    }


def _authority_partition_ids(payload: dict) -> set[str]:
    return {
        str(authority.get("candidate_authority_id") or "")
        for authority in payload.get("authorities") or []
        if isinstance(authority, dict) and authority.get("candidate_authority_id")
    }


def _generated_rule_candidate_id(rule: dict) -> str:
    if rule.get("candidate_authority_id"):
        return str(rule["candidate_authority_id"])
    applicability = rule.get("applicability")
    if isinstance(applicability, dict) and applicability.get("candidate_authority_id"):
        return str(applicability["candidate_authority_id"])
    return ""


def _applicability_validation_hash_gaps(validation: dict) -> list[dict]:
    artifact_paths = (
        validation.get("artifact_paths")
        if isinstance(validation.get("artifact_paths"), dict)
        else {}
    )
    hashes = validation.get("hashes") if isinstance(validation.get("hashes"), dict) else {}
    expected_hash_fields = {
        "applicable_authorities": "applicable_authorities_sha256",
        "decisions": "applicability_decisions_sha256",
        "graph_trace": "graph_trace_sha256",
        "non_applicable_authorities": "non_applicable_authorities_sha256",
        "provenance": "applicability_provenance_sha256",
        "retrieval_trace": "retrieval_trace_sha256",
        "search_coverage_certificates": "search_coverage_certificates_sha256",
    }
    gaps = []
    for artifact_name, hash_field in expected_hash_fields.items():
        artifact_path = artifact_paths.get(artifact_name)
        expected_hash = hashes.get(hash_field)
        if not artifact_path and expected_hash:
            gaps.append(
                {
                    "artifact": artifact_name,
                    "reason": "missing_artifact_path",
                    "hash_field": hash_field,
                }
            )
            continue
        if artifact_path and expected_hash and not _file_hash_matches(
            Path(str(artifact_path)),
            str(expected_hash),
        ):
            gaps.append(
                {
                    "artifact": artifact_name,
                    "reason": "hash_mismatch",
                    "path": str(artifact_path),
                    "hash_field": hash_field,
                    "expected_sha256": str(expected_hash),
                }
            )
    return gaps


def _non_applicable_coverage_gaps(payload: dict, coverage_ids: set[str]) -> list[dict]:
    gaps = []
    for authority in payload.get("authorities") or []:
        if not isinstance(authority, dict):
            gaps.append({"candidate_authority_id": None, "reason": "invalid_authority"})
            continue
        certificate_ids = [
            str(value)
            for value in authority.get("search_coverage_certificate_ids") or []
            if str(value or "").strip()
        ]
        missing = [value for value in certificate_ids if value not in coverage_ids]
        if not certificate_ids or missing:
            gaps.append(
                {
                    "candidate_authority_id": authority.get("candidate_authority_id"),
                    "missing_certificate_ids": missing,
                }
            )
    return gaps
