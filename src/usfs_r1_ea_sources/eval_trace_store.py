from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import hashlib
import json
import sqlite3

from .eval_trace_inventory import INVENTORY_RESULT_SCHEMA_VERSION
from .eval_trace_inventory import REPO_ROOT
from .eval_trace_store_sqlite import _duplicate_id_counts
from .eval_trace_store_sqlite import _orphan_counts
from .eval_trace_store_sqlite import _replace_rows
from .eval_trace_store_sqlite import _reset_schema
from .eval_trace_store_sqlite import _row_counts
from .records import sha256_file


STORE_SCHEMA_VERSION = "system-eval-trace-store-v1"
STORE_SUMMARY_SCHEMA_VERSION = "system-eval-trace-store-summary-v1"
@dataclass(frozen=True)
class EvalTraceStoreBuildResult:
    summary: dict[str, Any]


def run_eval_trace_store_build(
    *,
    inventory_path: Path,
    sqlite_path: Path,
    summary_path: Path | None = None,
    repo_root: Path = REPO_ROOT,
) -> EvalTraceStoreBuildResult:
    repo_root = repo_root.resolve()
    inventory_path = _resolve_path(inventory_path, repo_root)
    sqlite_path = _resolve_path(sqlite_path, repo_root)
    summary_path = _resolve_path(summary_path, repo_root) if summary_path is not None else None

    inventory = _read_inventory(inventory_path)
    artifact_records = _artifact_records(inventory)
    store_context = _store_context(inventory, artifact_records)
    store_rows = _build_store_rows(
        artifact_records,
        repo_root=repo_root,
        store_context=store_context,
    )

    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(sqlite_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        _reset_schema(connection)
        _replace_rows(connection, store_rows)
        row_counts = _row_counts(connection)
        orphan_counts = _orphan_counts(connection)
        duplicate_id_counts = _duplicate_id_counts(connection)

    summary = _build_summary(
        inventory=inventory,
        inventory_path=inventory_path,
        sqlite_path=sqlite_path,
        store_rows=store_rows,
        row_counts=row_counts,
        orphan_counts=orphan_counts,
        duplicate_id_counts=duplicate_id_counts,
        repo_root=repo_root,
    )
    if summary_path is not None:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return EvalTraceStoreBuildResult(summary=summary)


def _read_inventory(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("eval trace inventory must be a JSON object")
    if payload.get("schema_version") != INVENTORY_RESULT_SCHEMA_VERSION:
        raise ValueError("eval trace store build requires eval-trace-inventory-results-v1")
    return payload


def _artifact_records(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    records = inventory.get("artifact_families")
    if not isinstance(records, list):
        raise ValueError("eval trace inventory requires artifact_families")
    return [record for record in records if isinstance(record, dict)]


def _store_context(
    inventory: dict[str, Any],
    artifact_records: list[dict[str, Any]],
) -> dict[str, Any]:
    scope = inventory.get("scope")
    if not isinstance(scope, dict):
        scope = {}
    return {
        "contract_id": _string(inventory.get("contract_id")),
        "contract_version": _string(inventory.get("contract_version")),
        "source_set_id": _string(scope.get("source_set_id")),
        "review_id": _string(scope.get("review_id")),
        "catalog_ref": _string(scope.get("catalog_dir"))
        or _first_artifact_ref(artifact_records, "source_catalog"),
        "replay_context_ref": _first_artifact_ref(artifact_records, "replay_context"),
    }


def _build_store_rows(
    artifact_records: list[dict[str, Any]],
    *,
    repo_root: Path,
    store_context: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, list[dict[str, Any]]] = {
        "system_eval_runs": [],
        "system_eval_cases": [],
        "system_eval_case_results": [],
        "system_eval_scores": [],
        "trace_runs": [],
        "trace_spans": [],
    }
    for record in artifact_records:
        assessment = _assess_artifact(record, repo_root=repo_root)
        payload_summary = _artifact_payload_summary(record, assessment["path"])
        eval_run = _eval_run(record, assessment, store_context, payload_summary)
        eval_case = _eval_case(record, eval_run, store_context, payload_summary)
        case_result = _case_result(record, eval_run, eval_case, assessment)
        score = _score(record, case_result, assessment, payload_summary)
        trace_run = _trace_run(record, assessment, store_context)
        trace_span = _trace_span(record, trace_run, assessment)
        rows["system_eval_runs"].append(eval_run)
        rows["system_eval_cases"].append(eval_case)
        rows["system_eval_case_results"].append(case_result)
        rows["system_eval_scores"].append(score)
        rows["trace_runs"].append(trace_run)
        rows["trace_spans"].append(trace_span)
    return rows


def _first_artifact_ref(
    artifact_records: list[dict[str, Any]],
    family_id: str,
) -> str | None:
    for record in artifact_records:
        if record.get("family_id") == family_id:
            return _string(record.get("origin_artifact_ref")) or _string(record.get("path"))
    return None


def _assess_artifact(record: dict[str, Any], *, repo_root: Path) -> dict[str, Any]:
    path = _record_path(record, repo_root)
    expected_hash = _string(record.get("artifact_sha256"))
    exists = path.exists()
    actual_hash = sha256_file(path) if exists else None
    failure_reason = None
    if not bool(record.get("exists")) or not exists:
        failure_reason = "missing_origin_artifact"
    elif record.get("status") != "present":
        failure_reason = str(record.get("status") or "artifact_not_present")
    elif expected_hash and actual_hash != expected_hash:
        failure_reason = "stale_artifact_hash"
    elif not expected_hash:
        failure_reason = "missing_source_artifact_hash"
    elif record.get("passed") is False and not _phase_eval_self_refresh_allowed(
        record,
        path,
    ):
        failure_reason = "origin_artifact_failed"

    passed = failure_reason is None
    return {
        "path": path,
        "exists": exists,
        "expected_hash": expected_hash,
        "actual_hash": actual_hash,
        "passed": passed,
        "status": "passed" if passed else "blocked",
        "failure_reason": failure_reason,
    }


def _phase_eval_self_refresh_allowed(record: dict[str, Any], path: Path) -> bool:
    # phase-eval is a self-referential producer: it can be the artifact that
    # proves the gate and the artifact that needs rewriting after the store
    # refresh. Other failed artifact families still block above.
    if record.get("family_id") != "phase_eval" or not path.exists():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return False
    if not isinstance(payload, dict):
        return False
    if payload.get("schema_version") not in {None, "phase-eval-results-v1"}:
        return False
    for phase in payload.get("phases", []):
        if not isinstance(phase, dict):
            continue
        if phase.get("passed") is False or phase.get("reviewer_ready") is False:
            return True
    return any(isinstance(blocker, dict) for blocker in payload.get("blockers", []))


def _artifact_payload_summary(record: dict[str, Any], path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        if path.suffix == ".jsonl":
            payload = _read_jsonl_payload(path)
        else:
            payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"parse_error": str(exc)}

    source_record_ids = _collect_strings_for_keys(
        payload,
        {
            "source_record_id",
            "source_record_ids",
            "authority_source_record_id",
            "forest_plan_source_record_id",
        },
    )
    citation_labels = _collect_strings_for_keys(
        payload,
        {"citation_label", "citation_labels", "citation_alias", "citation_aliases"},
    )
    scorer_versions = _collect_keyed_scalars(
        payload,
        {"scorer_version", "scorer_versions", "score_version", "scorer_set_version"},
    )
    thresholds = _collect_keyed_scalars(payload, {"threshold", "thresholds"})

    return {
        "schema_version": _string(record.get("schema_version"))
        or _first_collected_string(
            _collect_keyed_scalars(payload, {"schema_version"})
        ),
        "source_record_ids": source_record_ids,
        "citation_labels": citation_labels,
        "scorer_versions": scorer_versions,
        "thresholds": thresholds,
    }


def _read_jsonl_payload(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                payload = json.loads(line)
                if isinstance(payload, dict):
                    rows.append(payload)
    return rows


def _eval_run(
    record: dict[str, Any],
    assessment: dict[str, Any],
    store_context: dict[str, Any],
    payload_summary: dict[str, Any],
) -> dict[str, Any]:
    eval_run_id = _stable_id("eval-run", record["family_id"], record["path"])
    review_id = _string(record.get("review_id")) or store_context["review_id"]
    source_set_id = _string(record.get("source_set_id")) or store_context["source_set_id"]
    source_record_ids = payload_summary.get("source_record_ids")
    scorer_versions = payload_summary.get("scorer_versions")
    thresholds = payload_summary.get("thresholds")
    return {
        "eval_run_id": eval_run_id,
        "schema_version": STORE_SCHEMA_VERSION,
        "contract_id": store_context["contract_id"],
        "contract_version": store_context["contract_version"],
        "eval_name": str(record["family_id"]),
        "eval_kind": _eval_kind(str(record["family_id"])),
        "target_kind": "review" if review_id else "source_set",
        "target_id": review_id or source_set_id,
        "dataset_name": source_set_id or "unknown_source_set",
        "dataset_version": _string(record.get("schema_version")) or "unknown_schema",
        "scorer_set_name": "eval_trace_inventory_link_checks",
        "scorer_set_version": STORE_SCHEMA_VERSION,
        "workflow_version": _string(record.get("schema_version")) or STORE_SCHEMA_VERSION,
        "status": assessment["status"],
        "passed": int(bool(assessment["passed"])),
        "source_set_id": source_set_id,
        "review_id": review_id,
        "origin_artifact_ref": str(record.get("origin_artifact_ref") or record.get("path")),
        "origin_artifact_sha256": assessment["expected_hash"],
        "current_artifact_sha256": assessment["actual_hash"],
        "catalog_ref": store_context["catalog_ref"],
        "replay_context_ref": store_context["replay_context_ref"],
        "source_record_ids_json": _json_dumps(source_record_ids or []),
        "scorer_versions_json": _json_dumps(scorer_versions or {}),
        "thresholds_json": _json_dumps(thresholds or {}),
        "failure_reason": assessment["failure_reason"],
        "summary_json": _json_dumps(
            {
                "inventory_record": record,
                "artifact_payload_summary": payload_summary,
                "contract_id": store_context["contract_id"],
                "contract_version": store_context["contract_version"],
                "catalog_ref": store_context["catalog_ref"],
                "replay_context_ref": store_context["replay_context_ref"],
            }
        ),
    }


def _eval_case(
    record: dict[str, Any],
    eval_run: dict[str, Any],
    store_context: dict[str, Any],
    payload_summary: dict[str, Any],
) -> dict[str, Any]:
    eval_case_id = _stable_id("eval-case", eval_run["eval_run_id"])
    case_key = f"{record['family_id']}:{record['path']}"
    return {
        "eval_case_id": eval_case_id,
        "eval_run_id": eval_run["eval_run_id"],
        "case_key": case_key,
        "case_version": STORE_SCHEMA_VERSION,
        "case_hash": _stable_hash(record),
        "source_kind": "artifact_family",
        "source_ref": str(record.get("path")),
        "input_json": _json_dumps(
            {
                "family_id": record.get("family_id"),
                "path": record.get("path"),
                "source_set_id": record.get("source_set_id")
                or store_context["source_set_id"],
                "review_id": record.get("review_id") or store_context["review_id"],
                "catalog_ref": store_context["catalog_ref"],
                "replay_context_ref": store_context["replay_context_ref"],
            }
        ),
        "expected_json": _json_dumps(
            {
                "exists": True,
                "status": "present",
                "artifact_sha256": record.get("artifact_sha256"),
            }
        ),
        "metadata_json": _json_dumps(
            {
                "inventory_record": record,
                "artifact_payload_summary": payload_summary,
            }
        ),
    }


def _case_result(
    record: dict[str, Any],
    eval_run: dict[str, Any],
    eval_case: dict[str, Any],
    assessment: dict[str, Any],
) -> dict[str, Any]:
    result_id = _stable_id("eval-case-result", eval_case["eval_case_id"])
    return {
        "eval_case_result_id": result_id,
        "eval_run_id": eval_run["eval_run_id"],
        "eval_case_id": eval_case["eval_case_id"],
        "trace_id": _stable_id("trace", record["family_id"], record["path"]),
        "status": assessment["status"],
        "passed": int(bool(assessment["passed"])),
        "score": 1.0 if assessment["passed"] else 0.0,
        "failure_reason": assessment["failure_reason"],
    }


def _score(
    record: dict[str, Any],
    case_result: dict[str, Any],
    assessment: dict[str, Any],
    payload_summary: dict[str, Any],
) -> dict[str, Any]:
    scorer_versions = payload_summary.get("scorer_versions")
    if isinstance(scorer_versions, dict):
        score_version = _first_collected_string(scorer_versions) or STORE_SCHEMA_VERSION
    else:
        score_version = STORE_SCHEMA_VERSION
    return {
        "eval_score_id": _stable_id("eval-score", case_result["eval_case_result_id"]),
        "eval_case_result_id": case_result["eval_case_result_id"],
        "score_name": "artifact_link_integrity",
        "score_kind": "trace_integrity",
        "score_version": score_version,
        "score": 1.0 if assessment["passed"] else 0.0,
        "passed": int(bool(assessment["passed"])),
        "threshold": 1.0,
        "evidence_refs_json": _json_dumps(
            {
                "origin_artifact_ref": record.get("origin_artifact_ref") or record.get("path"),
                "origin_artifact_sha256": assessment["expected_hash"],
                "current_artifact_sha256": assessment["actual_hash"],
                "failure_reason": assessment["failure_reason"],
                "source_record_ids": payload_summary.get("source_record_ids", []),
                "citation_labels": payload_summary.get("citation_labels", []),
            }
        ),
    }


def _trace_run(
    record: dict[str, Any],
    assessment: dict[str, Any],
    store_context: dict[str, Any],
) -> dict[str, Any]:
    return {
        "trace_id": _stable_id("trace", record["family_id"], record["path"]),
        "trace_kind": _trace_kind(record),
        "root_ref_kind": "artifact_family",
        "root_ref_id": str(record.get("family_id")),
        "status": assessment["status"],
        "input_hash": assessment["expected_hash"],
        "output_hash": assessment["actual_hash"],
        "artifact_refs_json": _json_dumps(
            {
                "path": record.get("path"),
                "origin_artifact_ref": record.get("origin_artifact_ref") or record.get("path"),
                "source_set_id": record.get("source_set_id"),
                "review_id": record.get("review_id"),
            }
        ),
        "redaction_policy": "local_unredacted_no_external_export",
        "source_set_id": _string(record.get("source_set_id")) or store_context["source_set_id"],
        "review_id": _string(record.get("review_id")) or store_context["review_id"],
    }


def _trace_span(
    record: dict[str, Any],
    trace_run: dict[str, Any],
    assessment: dict[str, Any],
) -> dict[str, Any]:
    return {
        "span_id": _stable_id("span", trace_run["trace_id"], record["path"]),
        "trace_id": trace_run["trace_id"],
        "parent_span_id": None,
        "span_kind": _span_kind(record),
        "name": str(record.get("family_id")),
        "status": assessment["status"],
        "attributes_json": _json_dumps(
            {
                "path": record.get("path"),
                "artifact_sha256": assessment["expected_hash"],
                "current_artifact_sha256": assessment["actual_hash"],
                "line_count": record.get("line_count"),
                "failure_reason": assessment["failure_reason"],
            }
        ),
        "source_ref_kind": "artifact",
        "source_ref_id": str(record.get("path")),
    }


def _build_summary(
    *,
    inventory: dict[str, Any],
    inventory_path: Path,
    sqlite_path: Path,
    store_rows: dict[str, list[dict[str, Any]]],
    row_counts: dict[str, int],
    orphan_counts: dict[str, int],
    duplicate_id_counts: dict[str, int],
    repo_root: Path,
) -> dict[str, Any]:
    blocked_runs = [
        row for row in store_rows["system_eval_runs"] if row["status"] != "passed"
    ]
    stale_artifact_count = sum(
        1 for row in blocked_runs if row["failure_reason"] == "stale_artifact_hash"
    )
    source_artifact_deletion_count = sum(
        1 for row in blocked_runs if row["failure_reason"] == "missing_origin_artifact"
    )
    missing_required_link_count = _missing_required_link_count(inventory)
    passed = (
        bool(inventory.get("passed"))
        and not blocked_runs
        and missing_required_link_count == 0
        and all(count == 0 for count in orphan_counts.values())
        and all(count == 0 for count in duplicate_id_counts.values())
        and all(count > 0 for count in row_counts.values())
    )
    return {
        "schema_version": STORE_SUMMARY_SCHEMA_VERSION,
        "store_schema_version": STORE_SCHEMA_VERSION,
        "inventory_schema_version": inventory.get("schema_version"),
        "inventory_path": _display_path(inventory_path, repo_root),
        "sqlite_path": _display_path(sqlite_path, repo_root),
        "passed": passed,
        "command_succeeded": passed,
        "row_counts": row_counts,
        "orphan_counts": orphan_counts,
        "duplicate_id_counts": duplicate_id_counts,
        "blocked_eval_run_count": len(blocked_runs),
        "blocked_eval_runs": [
            {
                "eval_run_id": row["eval_run_id"],
                "eval_name": row["eval_name"],
                "origin_artifact_ref": row["origin_artifact_ref"],
                "failure_reason": row["failure_reason"],
            }
            for row in blocked_runs
        ],
        "stale_artifact_count": stale_artifact_count,
        "source_artifact_deletion_count": source_artifact_deletion_count,
        "missing_required_link_count": missing_required_link_count,
        "inventory_passed": bool(inventory.get("passed")),
        "validation_checks": [
            {
                "name": "inventory_passed",
                "passed": bool(inventory.get("passed")),
            },
            {
                "name": "all_rows_inserted",
                "passed": all(count > 0 for count in row_counts.values()),
                "row_counts": row_counts,
            },
            {
                "name": "no_orphans",
                "passed": all(count == 0 for count in orphan_counts.values()),
                "orphan_counts": orphan_counts,
            },
            {
                "name": "no_duplicate_ids",
                "passed": all(count == 0 for count in duplicate_id_counts.values()),
                "duplicate_id_counts": duplicate_id_counts,
            },
            {
                "name": "source_artifacts_current",
                "passed": not blocked_runs,
                "blocked_eval_run_count": len(blocked_runs),
            },
        ],
    }


def _missing_required_link_count(inventory: dict[str, Any]) -> int:
    status = inventory.get("required_link_status")
    if not isinstance(status, dict):
        return 1
    checks = status.get("checks")
    if not isinstance(checks, list):
        return 1
    return sum(
        1
        for check in checks
        if isinstance(check, dict) and not bool(check.get("passed"))
    )


def _eval_kind(family_id: str) -> str:
    return {
        "applicability_trace": "applicability",
        "decision_support": "decision_support",
        "final_qa": "final_qa",
        "forest_plan_component_eval": "forest_plan_component",
        "forest_plan_component_eval_coverage": "forest_plan_component",
        "phase_eval": "phase_eval",
        "promotion_suite": "promotion_suite",
        "real_package_review_coverage_eval": "real_package_review_coverage",
        "replay_context": "phase_eval",
        "review_packet_index": "packet_index",
        "source_catalog": "catalog",
        "source_set_manifest": "catalog",
        "v1_ea_eval": "v1_ea",
    }.get(family_id, "phase_eval")


def _trace_kind(record: dict[str, Any]) -> str:
    path = str(record.get("path") or "")
    if path.endswith("applicability_retrieval_trace.jsonl"):
        return "applicability_retrieval"
    if path.endswith("applicability_graph_trace.jsonl"):
        return "applicability_graph"
    if record.get("family_id") == "replay_context":
        return "replay"
    if record.get("family_id") in {"source_catalog", "source_set_manifest"}:
        return "validation"
    return "evaluation"


def _span_kind(record: dict[str, Any]) -> str:
    path = str(record.get("path") or "")
    if path.endswith("applicability_retrieval_trace.jsonl"):
        return "retrieve"
    if path.endswith("applicability_graph_trace.jsonl"):
        return "search"
    if str(record.get("family_id", "")).endswith("_eval"):
        return "evaluation"
    return "artifact"


def _record_path(record: dict[str, Any], repo_root: Path) -> Path:
    path = Path(str(record.get("path") or ""))
    return path if path.is_absolute() else repo_root / path


def _stable_id(*parts: object) -> str:
    return _stable_hash(parts)[:24]


def _stable_hash(value: object) -> str:
    return hashlib.sha256(_json_dumps(value).encode("utf-8")).hexdigest()


def _collect_strings_for_keys(value: object, keys: set[str]) -> list[str]:
    collected: list[str] = []
    _collect_strings_for_keys_into(value, keys, collected)
    return _unique_sorted_strings(collected)


def _collect_strings_for_keys_into(
    value: object,
    keys: set[str],
    collected: list[str],
) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in keys:
                collected.extend(_string_values(child))
            _collect_strings_for_keys_into(child, keys, collected)
    elif isinstance(value, list):
        for child in value:
            _collect_strings_for_keys_into(child, keys, collected)


def _collect_keyed_scalars(value: object, keys: set[str]) -> dict[str, list[object]]:
    collected: dict[str, list[object]] = {key: [] for key in keys}
    _collect_keyed_scalars_into(value, keys, collected)
    return {
        key: _unique_stable_scalars(values)
        for key, values in sorted(collected.items())
        if values
    }


def _collect_keyed_scalars_into(
    value: object,
    keys: set[str],
    collected: dict[str, list[object]],
) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in keys:
                collected[key].extend(_scalar_values(child))
            _collect_keyed_scalars_into(child, keys, collected)
    elif isinstance(value, list):
        for child in value:
            _collect_keyed_scalars_into(child, keys, collected)


def _string_values(value: object) -> list[str]:
    if isinstance(value, str) and value:
        return [value]
    if isinstance(value, list):
        values: list[str] = []
        for child in value:
            values.extend(_string_values(child))
        return values
    if isinstance(value, dict):
        values = []
        for child in value.values():
            values.extend(_string_values(child))
        return values
    return []


def _scalar_values(value: object) -> list[object]:
    if isinstance(value, str | int | float | bool) and value is not None:
        return [value]
    if isinstance(value, list):
        values: list[object] = []
        for child in value:
            values.extend(_scalar_values(child))
        return values
    if isinstance(value, dict):
        values = []
        for child in value.values():
            values.extend(_scalar_values(child))
        return values
    return []


def _unique_sorted_strings(values: list[str]) -> list[str]:
    return sorted({value for value in values if value})


def _unique_stable_scalars(values: list[object]) -> list[object]:
    seen: set[str] = set()
    unique: list[object] = []
    for value in values:
        key = _json_dumps(value)
        if key in seen:
            continue
        seen.add(key)
        unique.append(value)
    return unique


def _first_collected_string(values_by_key: dict[str, list[object]]) -> str | None:
    for values in values_by_key.values():
        for value in values:
            if isinstance(value, str) and value:
                return value
    return None


def _json_dumps(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _string(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def _resolve_path(path: Path | None, repo_root: Path) -> Path:
    if path is None:
        raise ValueError("path is required")
    return path if path.is_absolute() else repo_root / path


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root))
    except ValueError:
        return str(path)
