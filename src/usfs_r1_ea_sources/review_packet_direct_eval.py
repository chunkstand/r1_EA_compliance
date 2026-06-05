from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .review_packet_index_artifacts import _output_paths
from .review_packet_index_common import _dict
from .review_packet_index_common import _sha256_file
from .review_packet_index_common import _utc_now
from .review_packet_index_common import _write_json


REVIEW_PACKET_DIRECT_EVAL_SCHEMA_VERSION = "review-packet-direct-eval-results-v1"
REVIEW_PACKET_FAILURE_INTAKE_SCHEMA_VERSION = "review-packet-failure-intake-cases-v1"
REVIEW_PACKET_DIRECT_EVAL_CONTRACT_ID = "review-packet-direct-eval-v1"
REVIEW_PACKET_DIRECT_EVAL_SCORER_VERSION = "review-packet-direct-eval-deterministic-v1"
REVIEW_PACKET_DIRECT_EVAL_FILENAME = "review_packet_direct_eval_results.json"
REVIEW_PACKET_FAILURE_INTAKE_FILENAME = "review_packet_failure_intake_cases.json"

REQUIRED_METRIC_GROUP_IDS = [
    "identity_and_freshness",
    "row_inventory_completeness",
    "render_manifest_alignment",
    "cross_artifact_row_alignment",
    "artifact_hash_alignment",
    "reviewer_boundary",
]


@dataclass(frozen=True)
class ReviewPacketDirectEvalResult:
    summary: dict[str, Any]
    output_path: Path
    failure_intake_path: Path


def run_review_packet_direct_eval(
    *,
    output_dir: Path = Path("source_library"),
    review_id: str,
    results_dir: Path | None = None,
) -> ReviewPacketDirectEvalResult:
    """Score existing review-packet artifacts as a deterministic direct eval."""

    output_dir = Path(output_dir)
    review_dir = output_dir / "reviews" / review_id
    index_dir = Path(results_dir) if results_dir is not None else review_dir / "review_packet_index"
    paths = _output_paths(index_dir)
    output_path = index_dir / REVIEW_PACKET_DIRECT_EVAL_FILENAME
    failure_intake_path = index_dir / REVIEW_PACKET_FAILURE_INTAKE_FILENAME

    row_inventory = _read_json(paths.row_inventory_path)
    render_manifest = _read_json(paths.render_manifest_path)
    packet_index = _read_json(paths.packet_index_path)
    validation = _read_json(paths.validation_path)
    packet_markdown = _read_text(paths.packet_index_markdown_path)
    source_set_id = _first_text(
        validation.get("source_set_id"),
        row_inventory.get("source_set_id"),
        render_manifest.get("source_set_id"),
        packet_index.get("source_set_id"),
    )
    source_artifacts = _source_artifacts(paths)
    metric_groups = _metric_groups(
        review_id=review_id,
        source_set_id=source_set_id,
        row_inventory=row_inventory,
        render_manifest=render_manifest,
        packet_index=packet_index,
        validation=validation,
        packet_markdown=packet_markdown,
        source_artifacts=source_artifacts,
        paths=paths,
    )
    failed_groups = [group for group in metric_groups if not group["passed"]]
    failure_cases = [
        _failure_case(
            group=group,
            review_id=review_id,
            source_set_id=source_set_id,
            paths=paths,
        )
        for group in failed_groups
    ]
    failure_intake = {
        "schema_version": REVIEW_PACKET_FAILURE_INTAKE_SCHEMA_VERSION,
        "contract_id": REVIEW_PACKET_DIRECT_EVAL_CONTRACT_ID,
        "scorer_version": REVIEW_PACKET_DIRECT_EVAL_SCORER_VERSION,
        "created_at": _utc_now(),
        "review_id": review_id,
        "source_set_id": source_set_id,
        "case_count": len(failure_cases),
        "cases": failure_cases,
    }
    index_dir.mkdir(parents=True, exist_ok=True)
    _write_json(failure_intake_path, failure_intake)

    required_present_missing = sorted(
        set(REQUIRED_METRIC_GROUP_IDS) - {group["id"] for group in metric_groups}
    )
    blocking_gap_group_ids = sorted(group["id"] for group in failed_groups)
    summary = {
        "schema_version": REVIEW_PACKET_DIRECT_EVAL_SCHEMA_VERSION,
        "contract_id": REVIEW_PACKET_DIRECT_EVAL_CONTRACT_ID,
        "scorer_version": REVIEW_PACKET_DIRECT_EVAL_SCORER_VERSION,
        "created_at": _utc_now(),
        "review_id": review_id,
        "source_set_id": source_set_id,
        "direct_eval_present": True,
        "passed": not failed_groups and not required_present_missing,
        "metric_group_count": len(metric_groups),
        "required_metric_group_ids": REQUIRED_METRIC_GROUP_IDS,
        "required_metric_group_ids_present": required_present_missing,
        "blocking_gap_group_ids": blocking_gap_group_ids,
        "failure_intake_path": str(failure_intake_path),
        "failure_intake_case_count": len(failure_cases),
        "source_artifacts": source_artifacts,
        "metric_groups": metric_groups,
    }
    _write_json(output_path, summary)
    return ReviewPacketDirectEvalResult(
        summary=summary,
        output_path=output_path,
        failure_intake_path=failure_intake_path,
    )


def _metric_groups(
    *,
    review_id: str,
    source_set_id: str,
    row_inventory: dict[str, Any],
    render_manifest: dict[str, Any],
    packet_index: dict[str, Any],
    validation: dict[str, Any],
    packet_markdown: str,
    source_artifacts: list[dict[str, Any]],
    paths: Any,
) -> list[dict[str, Any]]:
    row_summary = _dict(row_inventory.get("summary"))
    render_summary = _dict(render_manifest.get("summary"))
    packet_summary = _dict(packet_index.get("row_inventory_summary"))
    validation_summary = _dict(validation.get("summary"))
    validation_checks = _checks_by_name(validation)
    return [
        _metric_group(
            "identity_and_freshness",
            passed=(
                all(record["exists"] and record.get("parse_ok", True) for record in source_artifacts)
                and validation.get("review_id") == review_id
                and row_inventory.get("review_id") == review_id
                and render_manifest.get("review_id") == review_id
                and packet_index.get("review_id") == review_id
                and validation.get("source_set_id") == source_set_id
                and row_inventory.get("source_set_id") == source_set_id
                and render_manifest.get("source_set_id") == source_set_id
                and packet_index.get("source_set_id") == source_set_id
                and validation.get("passed") is True
                and validation.get("reviewer_ready") is True
            ),
            failure_category="review_source_set_mismatch",
            metrics={
                "validation_passed": validation.get("passed"),
                "validation_reviewer_ready": validation.get("reviewer_ready"),
                "validation_check_count": validation_summary.get("check_count"),
                "validation_failed_check_count": validation_summary.get("failed_check_count"),
            },
        ),
        _metric_group(
            "row_inventory_completeness",
            passed=(
                _safe_int(row_summary.get("applicable_authority_count")) > 0
                and _safe_int(row_summary.get("non_applicable_authority_count")) > 0
                and bool(row_summary.get("row_set_sha256"))
                and _check_passed(validation_checks, "applicable_forest_plan_standards_present")
                and _check_passed(
                    validation_checks,
                    "land_exchange_rows_first_class_in_packet_index",
                )
            ),
            failure_category="missing_packet_index_row",
            metrics={
                "applicable_authority_count": row_summary.get("applicable_authority_count"),
                "non_applicable_authority_count": row_summary.get(
                    "non_applicable_authority_count"
                ),
                "forest_plan_component_row_count": row_summary.get(
                    "forest_plan_component_row_count"
                ),
                "applicable_standard_count": row_summary.get("applicable_standard_count"),
                "sidecar_rule_claim_links_used": row_summary.get(
                    "sidecar_rule_claim_links_used"
                ),
            },
        ),
        _metric_group(
            "render_manifest_alignment",
            passed=(
                render_summary.get("passed") is True
                and render_summary.get("pdf_header_valid") is True
                and _safe_int(render_summary.get("authority_row_count"))
                == _safe_int(row_summary.get("applicable_authority_count"))
                and _safe_int(render_summary.get("forest_plan_row_count"))
                == _safe_int(row_summary.get("forest_plan_component_row_count"))
                and _check_passed(
                    validation_checks,
                    "render_manifest_authority_rows_match_matrix",
                )
                and _check_passed(
                    validation_checks,
                    "render_manifest_forest_plan_rows_match_matrix",
                )
            ),
            failure_category="missing_matrix_render_row",
            metrics={
                "render_manifest_row_count": render_summary.get("row_count"),
                "render_manifest_authority_row_count": render_summary.get(
                    "authority_row_count"
                ),
                "render_manifest_forest_plan_row_count": render_summary.get(
                    "forest_plan_row_count"
                ),
                "pdf_header_valid": render_summary.get("pdf_header_valid"),
            },
        ),
        _metric_group(
            "cross_artifact_row_alignment",
            passed=(
                validation.get("passed") is True
                and _safe_int(validation_summary.get("failed_check_count")) == 0
                and not validation_summary.get("failure_category_counts")
                and packet_summary == row_summary
                and _authority_row_checks_passed(validation_checks)
                and _check_passed(validation_checks, "packet_index_rows_match_inventory")
                and _check_passed(
                    validation_checks,
                    "forest_plan_rows_match_component_findings",
                )
                and _safe_int(
                    validation_summary.get("sidecar_rule_claim_lineage_failed_check_count")
                )
                == 0
            ),
            failure_category="missing_applicable_authority_row",
            metrics={
                "failed_check_count": validation_summary.get("failed_check_count"),
                "failure_category_counts": validation_summary.get(
                    "failure_category_counts",
                    {},
                ),
                "sidecar_rule_claim_lineage_failed_check_count": validation_summary.get(
                    "sidecar_rule_claim_lineage_failed_check_count"
                ),
            },
        ),
        _metric_group(
            "artifact_hash_alignment",
            passed=_artifact_hashes_align(validation=validation, paths=paths),
            failure_category="stale_artifact",
            metrics={
                "declared_output_hash_count": len(
                    validation.get("output_hashes", {})
                    if isinstance(validation.get("output_hashes"), dict)
                    else {}
                ),
                "source_artifact_count": len(source_artifacts),
            },
        ),
        _metric_group(
            "reviewer_boundary",
            passed=(
                _dict(packet_index.get("review_boundary")).get(
                    "root_east_crazies_drafts_are_canonical"
                )
                is False
                and _check_passed(validation_checks, "non_canonical_root_drafts_not_referenced")
                and "not legal advice" in packet_markdown
            ),
            failure_category="non_canonical_draft_dependency",
            metrics={
                "root_east_crazies_drafts_are_canonical": _dict(
                    packet_index.get("review_boundary")
                ).get("root_east_crazies_drafts_are_canonical"),
                "packet_markdown_has_legal_boundary": "not legal advice" in packet_markdown,
            },
        ),
    ]


def _metric_group(
    group_id: str,
    *,
    passed: bool,
    failure_category: str,
    metrics: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": group_id,
        "passed": bool(passed),
        "failure_category": None if passed else failure_category,
        "metrics": metrics,
    }


def _artifact_hashes_align(*, validation: dict[str, Any], paths: Any) -> bool:
    output_hashes = validation.get("output_hashes")
    if not isinstance(output_hashes, dict):
        return False
    required_output_hashes = {
        "row_inventory_json_sha256": paths.row_inventory_path,
        "row_inventory_markdown_sha256": paths.row_inventory_markdown_path,
        "render_manifest_sha256": paths.render_manifest_path,
        "packet_index_json_sha256": paths.packet_index_path,
        "packet_index_markdown_sha256": paths.packet_index_markdown_path,
        "packet_index_pdf_sha256": paths.packet_index_pdf_path,
    }
    return all(
        path.exists() and output_hashes.get(key) == _sha256_file(path)
        for key, path in required_output_hashes.items()
    )


def _failure_case(
    *,
    group: dict[str, Any],
    review_id: str,
    source_set_id: str,
    paths: Any,
) -> dict[str, Any]:
    group_id = str(group["id"])
    return {
        "case_id": f"review-packet:{review_id}:{group_id}",
        "review_id": review_id,
        "source_set_id": source_set_id,
        "metric_group_id": group_id,
        "failure_category": group.get("failure_category"),
        "owner": "review_packet_index",
        "risk_level": "blocking",
        "lifecycle_status": "open",
        "assertion": f"Review packet direct-eval metric group {group_id} must pass.",
        "review_condition": "Inspect the cited review packet artifacts and validation sidecar.",
        "removal_condition": "Remove only after the metric group is green in a regenerated direct-eval artifact.",
        "scorer_version": REVIEW_PACKET_DIRECT_EVAL_SCORER_VERSION,
        "source_artifacts": _source_artifacts(paths),
    }


def _source_artifacts(paths: Any) -> list[dict[str, Any]]:
    artifact_paths = [
        ("row_inventory", paths.row_inventory_path, "json"),
        ("row_inventory_markdown", paths.row_inventory_markdown_path, "text"),
        ("render_manifest", paths.render_manifest_path, "json"),
        ("packet_index", paths.packet_index_path, "json"),
        ("packet_index_markdown", paths.packet_index_markdown_path, "text"),
        ("packet_index_pdf", paths.packet_index_pdf_path, "pdf"),
        ("validation", paths.validation_path, "json"),
    ]
    return [_artifact_record(artifact_id, path, artifact_type) for artifact_id, path, artifact_type in artifact_paths]


def _artifact_record(artifact_id: str, path: Path, artifact_type: str) -> dict[str, Any]:
    record: dict[str, Any] = {
        "artifact_id": artifact_id,
        "path": str(path),
        "exists": path.exists(),
        "artifact_type": artifact_type,
    }
    if not path.exists():
        record["parse_ok"] = False
        return record
    record["sha256"] = _sha256_file(path)
    record["size_bytes"] = path.stat().st_size
    if artifact_type == "json":
        try:
            parsed = json.loads(path.read_text(encoding="utf-8"))
            record["parse_ok"] = isinstance(parsed, dict)
        except json.JSONDecodeError as exc:
            record["parse_ok"] = False
            record["error"] = str(exc)
    elif artifact_type == "pdf":
        record["parse_ok"] = path.read_bytes().startswith(b"%PDF-")
    else:
        record["parse_ok"] = True
    return record


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _checks_by_name(validation: dict[str, Any]) -> dict[str, dict[str, Any]]:
    checks = validation.get("checks")
    if not isinstance(checks, list):
        return {}
    return {
        str(check.get("name")): check
        for check in checks
        if isinstance(check, dict) and check.get("name")
    }


def _check_passed(checks_by_name: dict[str, dict[str, Any]], name: str) -> bool:
    return checks_by_name.get(name, {}).get("passed") is True


def _authority_row_checks_passed(checks_by_name: dict[str, dict[str, Any]]) -> bool:
    authority_checks = [
        check
        for name, check in checks_by_name.items()
        if name.endswith("_authority_rows_match_applicability")
    ]
    return bool(authority_checks) and all(check.get("passed") is True for check in authority_checks)


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _first_text(*values: Any) -> str:
    for value in values:
        if value not in (None, ""):
            return str(value)
    return ""
