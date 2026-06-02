from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from .eval_trace_contract import DEFAULT_EVAL_TRACE_CONTRACT_PATH
from .eval_trace_contract import load_eval_trace_contract
from .eval_trace_inventory_models import ArtifactSpec as _ArtifactSpec
from .eval_trace_inventory_models import EvalTraceInventoryResult
from .records import sha256_file


INVENTORY_RESULT_SCHEMA_VERSION = "eval-trace-inventory-results-v1"
INVENTORY_REPORT_SCHEMA_VERSION = "eval-trace-inventory-report-v1"
DEFAULT_EVAL_TRACE_INVENTORY_RESULTS_DIR = Path("source_library/evaluations/eval_trace_inventory")
REPO_ROOT = Path(__file__).resolve().parents[2]


def run_eval_trace_inventory(
    *,
    output_dir: Path = Path("source_library"),
    source_set_id: str | None = None,
    review_id: str | None = None,
    catalog_dir: Path | None = None,
    results_path: Path | None = None,
    format: str = "json",
    fail_on_missing_required: bool = False,
    contract_path: Path = DEFAULT_EVAL_TRACE_CONTRACT_PATH,
    repo_root: Path = REPO_ROOT,
) -> EvalTraceInventoryResult:
    if format not in {"json", "markdown"}:
        raise ValueError("eval-trace-inventory format must be json or markdown")

    repo_root = repo_root.resolve()
    output_dir = _resolve_path(output_dir, repo_root)
    contract = load_eval_trace_contract(_resolve_path(contract_path, repo_root))
    replay_context = _load_replay_context(repo_root, review_id)

    resolved_source_set_id = source_set_id or _string(replay_context.get("source_set_id"))
    resolved_catalog_dir = _resolve_catalog_dir(
        catalog_dir=catalog_dir,
        replay_context=replay_context,
        output_dir=output_dir,
        repo_root=repo_root,
    )
    scope_kind = "review" if review_id else "source_set"
    specs = _artifact_specs(
        output_dir=output_dir,
        repo_root=repo_root,
        source_set_id=resolved_source_set_id,
        review_id=review_id,
        catalog_dir=resolved_catalog_dir,
        scope_kind=scope_kind,
    )
    artifact_records = [
        _inspect_artifact(
            spec,
            repo_root=repo_root,
            source_set_id=resolved_source_set_id,
            review_id=review_id,
        )
        for spec in specs
    ]

    source_set_mismatches = _source_set_mismatches(
        artifact_records, resolved_source_set_id
    )
    review_id_mismatches = _review_id_mismatches(artifact_records, review_id)
    missing_cross_links = _missing_cross_links(artifact_records)
    stale_artifacts = _stale_artifacts(artifact_records)
    trace_hash_mismatches = _trace_hash_mismatches(artifact_records, repo_root)
    link_checks = _required_link_checks(
        contract=contract,
        artifact_records=artifact_records,
        replay_context=replay_context,
        catalog_dir=resolved_catalog_dir,
        repo_root=repo_root,
        source_set_id=resolved_source_set_id,
        review_id=review_id,
        source_set_mismatches=source_set_mismatches,
        review_id_mismatches=review_id_mismatches,
        missing_cross_links=missing_cross_links,
        stale_artifacts=stale_artifacts,
        trace_hash_mismatches=trace_hash_mismatches,
    )
    required_link_status = {
        "passed": all(check["passed"] for check in link_checks),
        "checks": link_checks,
    }
    passed = required_link_status["passed"]
    export_readiness = {
        "canonical_json_ready": False,
        "openinference_ready": False,
        "reason": "sqlite_store_not_built",
        "inventory_rows_exportable": passed,
        "local_source_of_record": True,
    }
    summary = {
        "schema_version": INVENTORY_RESULT_SCHEMA_VERSION,
        "contract_id": contract["contract_id"],
        "contract_version": contract["version"],
        "scope": {
            "scope_kind": scope_kind,
            "source_set_id": resolved_source_set_id,
            "review_id": review_id,
            "catalog_dir": _display_path(resolved_catalog_dir, repo_root)
            if resolved_catalog_dir is not None
            else None,
        },
        "passed": passed,
        "command_succeeded": passed or not fail_on_missing_required,
        "coverage_status": "passed" if passed else "blocked",
        "required_artifact_count": sum(1 for record in artifact_records if record["required"]),
        "present_artifact_count": sum(1 for record in artifact_records if record["exists"]),
        "missing_required_artifact_count": sum(
            1 for record in artifact_records if record["required"] and not record["exists"]
        ),
        "malformed_artifact_count": sum(
            1 for record in artifact_records if record["status"] == "malformed"
        ),
        "artifact_families": artifact_records,
        "required_link_status": required_link_status,
        "missing_cross_links": missing_cross_links,
        "stale_artifacts": stale_artifacts,
        "source_set_mismatches": source_set_mismatches,
        "review_id_mismatches": review_id_mismatches,
        "trace_hash_mismatches": trace_hash_mismatches,
        "export_readiness": export_readiness,
    }
    report = _markdown_report(summary)
    if results_path is not None:
        _write_results(_resolve_path(results_path, repo_root), summary, report, format)
    return EvalTraceInventoryResult(summary=summary, report=report)


def _artifact_specs(
    *,
    output_dir: Path,
    repo_root: Path,
    source_set_id: str | None,
    review_id: str | None,
    catalog_dir: Path | None,
    scope_kind: str,
) -> list[_ArtifactSpec]:
    resolved_catalog_dir = catalog_dir or output_dir / "catalog"
    specs = [
        _ArtifactSpec("source_set_manifest", resolved_catalog_dir / "source_set_manifest.json"),
        _ArtifactSpec("source_catalog", resolved_catalog_dir / "source_catalog.jsonl", kind="jsonl"),
    ]
    if scope_kind == "source_set":
        if source_set_id:
            specs.append(
                _ArtifactSpec(
                    "phase_eval",
                    output_dir
                    / "derived"
                    / source_set_id
                    / "evidence_graph"
                    / "phase_eval_results.json",
                )
            )
        return specs

    assert review_id is not None
    review_dir = output_dir / "reviews" / review_id
    specs.extend(
        [
            _ArtifactSpec("replay_context", repo_root / "config" / "replay_contexts" / f"{review_id}.json"),
            _ArtifactSpec("phase_eval", review_dir / "phase_eval_results.json"),
            _ArtifactSpec(
                "applicability_trace",
                review_dir / "applicability" / "applicability_retrieval_trace.jsonl",
                kind="jsonl",
            ),
            _ArtifactSpec(
                "applicability_trace",
                review_dir / "applicability" / "applicability_graph_trace.jsonl",
                kind="jsonl",
            ),
            _ArtifactSpec(
                "applicability_trace",
                review_dir
                / "applicability"
                / "applicability_retrieval_graph_diagnostics.json",
            ),
            _ArtifactSpec(
                "forest_plan_component_eval",
                review_dir / "forest_plan_component_eval_results.json",
            ),
            _ArtifactSpec(
                "forest_plan_component_eval_coverage",
                output_dir
                / "evaluations"
                / "forest_plan_component_eval_coverage"
                / "forest_plan_component_eval_coverage_results.json",
            ),
            _ArtifactSpec("v1_ea_eval", review_dir / "v1_ea_eval_results.json"),
            _ArtifactSpec(
                "real_package_review_coverage_eval",
                output_dir
                / "reviews"
                / "real_package_review_coverage_eval"
                / "real_package_review_coverage_eval_results.json",
            ),
            _ArtifactSpec(
                "decision_support",
                review_dir / "decision_support" / "ea_consistency_decision_support.json",
            ),
            _ArtifactSpec(
                "decision_support",
                review_dir / "decision_support" / "ea_consistency_decision_support_manifest.json",
            ),
            _ArtifactSpec(
                "final_qa",
                review_dir / "final_qa" / "east_crazies_final_qa_certification.json",
            ),
            _ArtifactSpec(
                "final_qa",
                review_dir / "final_qa" / "east_crazies_final_qa_certification_validation.json",
            ),
            _ArtifactSpec(
                "review_packet_index",
                review_dir / "review_packet_index" / "review_packet_index.json",
            ),
            _ArtifactSpec(
                "review_packet_index",
                review_dir / "review_packet_index" / "review_packet_index_validation.json",
            ),
            _ArtifactSpec(
                "promotion_suite",
                _promotion_suite_path(output_dir, source_set_id),
            ),
        ]
    )
    return specs


def _inspect_artifact(
    spec: _ArtifactSpec,
    *,
    repo_root: Path,
    source_set_id: str | None,
    review_id: str | None,
) -> dict[str, Any]:
    display_path = _display_path(spec.path, repo_root)
    if not spec.path.exists():
        return {
            "family_id": spec.family_id,
            "path": display_path,
            "required": spec.required,
            "exists": False,
            "status": "missing",
            "origin_artifact_ref": display_path,
            "artifact_sha256": None,
            "source_set_id": None,
            "review_id": None,
            "passed": False,
        }

    artifact_sha256 = sha256_file(spec.path)
    record: dict[str, Any] = {
        "family_id": spec.family_id,
        "path": display_path,
        "required": spec.required,
        "exists": True,
        "status": "present",
        "origin_artifact_ref": display_path,
        "artifact_sha256": artifact_sha256,
        "source_set_id": None,
        "review_id": None,
        "passed": None,
    }
    try:
        if spec.kind == "jsonl":
            record.update(_inspect_jsonl_artifact(spec, source_set_id=source_set_id))
        else:
            payload = _read_json(spec.path)
            record.update(
                _inspect_json_artifact(
                    spec,
                    payload,
                    source_set_id=source_set_id,
                    review_id=review_id,
                )
            )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        record["status"] = "malformed"
        record["error"] = str(exc)
    return record


def _inspect_json_artifact(
    spec: _ArtifactSpec,
    payload: dict[str, Any],
    *,
    source_set_id: str | None,
    review_id: str | None,
) -> dict[str, Any]:
    if spec.family_id == "forest_plan_component_eval_coverage":
        scoped = _matching_slot(payload, review_id)
        return {
            "schema_version": _string(payload.get("schema_version")),
            "source_set_id": _string(scoped.get("result_source_set_id"))
            or _string(scoped.get("contract_source_set_id")),
            "review_id": _string(scoped.get("review_id")),
            "passed": bool(scoped.get("passed")) if scoped else bool(payload.get("passed")),
            "scoped_slot_id": _string(scoped.get("slot_id")),
            "global_passed": bool(payload.get("passed")),
        }
    if spec.family_id == "real_package_review_coverage_eval":
        scoped = _matching_slot(payload, review_id)
        return {
            "schema_version": _string(payload.get("schema_version")),
            "source_set_id": _string(scoped.get("source_set_id")),
            "review_id": _string(scoped.get("review_id")),
            "passed": bool(scoped.get("passed")) if scoped else bool(payload.get("passed")),
            "scoped_slot_id": _string(scoped.get("slot_id")),
            "global_passed": bool(payload.get("passed")),
        }
    if spec.family_id == "promotion_suite":
        return {
            "schema_version": _string(payload.get("schema_version")),
            "source_set_id": _string(payload.get("source_set_id")),
            "review_id": None,
            "passed": bool(payload.get("promotion_ready")),
            "suite_id": _string(payload.get("suite_id")),
        }

    summary = _dict(payload.get("summary"))
    contract = _dict(payload.get("contract"))
    source_set = (
        _string(payload.get("source_set_id"))
        or _string(summary.get("source_set_id"))
        or _string(contract.get("source_set_id"))
    )
    review = _string(payload.get("review_id")) or _string(summary.get("review_id"))
    passed = _passed_status(payload, summary)
    result = {
        "schema_version": _string(payload.get("schema_version"))
        or _string(summary.get("schema_version")),
        "source_set_id": source_set,
        "review_id": review,
        "passed": passed,
    }
    if spec.family_id == "applicability_trace":
        result["retrieval_trace_sha256"] = _string(payload.get("retrieval_trace_sha256"))
        result["graph_trace_sha256"] = _string(payload.get("graph_trace_sha256"))
    if spec.family_id == "phase_eval":
        result["direct_eval_status"] = _string(payload.get("review_direct_eval_status")) or _string(
            payload.get("direct_eval_status")
        )
    return result


def _inspect_jsonl_artifact(
    spec: _ArtifactSpec,
    *,
    source_set_id: str | None,
) -> dict[str, Any]:
    line_count = 0
    first_payload: dict[str, Any] = {}
    missing_artifact_hash_count = 0
    source_set_ids: set[str] = set()
    with spec.path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            line_count += 1
            payload = json.loads(line)
            if line_count == 1:
                first_payload = payload
            row_source_set_id = _string(payload.get("source_set_id"))
            if row_source_set_id:
                source_set_ids.add(row_source_set_id)
            if spec.family_id == "source_catalog" and not _string(payload.get("artifact_sha256")):
                missing_artifact_hash_count += 1
    observed_source_set_id = (
        next(iter(source_set_ids)) if len(source_set_ids) == 1 else _string(first_payload.get("source_set_id"))
    )
    status = "present"
    if source_set_id and source_set_ids and source_set_ids != {source_set_id}:
        status = "stale"
    return {
        "status": status,
        "line_count": line_count,
        "source_set_id": observed_source_set_id,
        "review_id": _string(first_payload.get("review_id")),
        "passed": line_count > 0,
        "missing_artifact_hash_count": missing_artifact_hash_count,
    }


def _required_link_checks(
    *,
    contract: dict[str, Any],
    artifact_records: list[dict[str, Any]],
    replay_context: dict[str, Any],
    catalog_dir: Path | None,
    repo_root: Path,
    source_set_id: str | None,
    review_id: str | None,
    source_set_mismatches: list[dict[str, Any]],
    review_id_mismatches: list[dict[str, Any]],
    missing_cross_links: list[dict[str, Any]],
    stale_artifacts: list[dict[str, Any]],
    trace_hash_mismatches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        _link_check(
            "source_set_identity_match",
            bool(source_set_id) and not source_set_mismatches,
            "source_set_mismatch",
            source_set_mismatches,
        ),
        _link_check(
            "review_identity_match",
            not review_id or not review_id_mismatches,
            "review_id_mismatch",
            review_id_mismatches,
        ),
        _link_check(
            "source_artifact_hash_present",
            not _missing_artifact_hash_links(artifact_records),
            "missing_source_artifact_hash",
            _missing_artifact_hash_links(artifact_records),
        ),
        _link_check(
            "origin_artifact_ref_present",
            not missing_cross_links,
            "missing_origin_artifact_ref",
            missing_cross_links,
        ),
        _link_check(
            "replay_context_catalog_match",
            _replay_context_catalog_matches(replay_context, catalog_dir, repo_root)
            if review_id
            else True,
            "replay_context_catalog_mismatch",
            _replay_catalog_detail(replay_context, catalog_dir),
        ),
        _link_check(
            "applicability_trace_hash_match",
            not trace_hash_mismatches,
            "trace_hash_mismatch",
            trace_hash_mismatches,
        ),
        _link_check(
            "phase_eval_direct_eval_present",
            _phase_eval_direct_eval_present(artifact_records),
            "direct_eval_missing",
            _family_records(artifact_records, "phase_eval"),
        ),
        _link_check(
            "export_local_provenance_preserved",
            not source_set_mismatches and not review_id_mismatches and not missing_cross_links,
            "missing_source_ref",
            {
                "source_set_mismatches": source_set_mismatches,
                "review_id_mismatches": review_id_mismatches,
                "missing_cross_links": missing_cross_links,
            },
        ),
        _link_check(
            "ratchet_scope_explicit",
            not contract.get("ratchet_scopes", {}).get("global_fail_closed"),
            "ratchet_scope_missing",
            contract.get("ratchet_scopes"),
        ),
        _link_check(
            "no_hosted_source_of_record",
            bool(contract.get("export_contract", {}).get("local_source_of_record")),
            "hosted_source_of_record",
            contract.get("export_contract"),
        ),
        _link_check(
            "stale_artifacts_absent",
            not stale_artifacts,
            "stale_artifact",
            stale_artifacts,
        ),
    ]


def _link_check(
    check_id: str,
    passed: bool,
    failure_reason: str,
    detail: object,
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "passed": bool(passed),
        "failure_reason": None if passed else failure_reason,
        "detail": detail,
    }


def _source_set_mismatches(
    artifact_records: list[dict[str, Any]],
    source_set_id: str | None,
) -> list[dict[str, Any]]:
    if not source_set_id:
        return []
    mismatches = []
    for record in artifact_records:
        actual = _string(record.get("source_set_id"))
        if actual and actual != source_set_id:
            mismatches.append(
                {
                    "family_id": record["family_id"],
                    "path": record["path"],
                    "expected": source_set_id,
                    "actual": actual,
                }
            )
    return mismatches


def _review_id_mismatches(
    artifact_records: list[dict[str, Any]],
    review_id: str | None,
) -> list[dict[str, Any]]:
    if not review_id:
        return []
    mismatches = []
    for record in artifact_records:
        actual = _string(record.get("review_id"))
        if actual and actual != review_id:
            mismatches.append(
                {
                    "family_id": record["family_id"],
                    "path": record["path"],
                    "expected": review_id,
                    "actual": actual,
                }
            )
    return mismatches


def _missing_cross_links(artifact_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    missing = []
    for record in artifact_records:
        if record["required"] and not record["exists"]:
            missing.append(
                {
                    "family_id": record["family_id"],
                    "path": record["path"],
                    "failure_reason": "missing_required_artifact",
                }
            )
        elif record["required"] and record["status"] == "malformed":
            missing.append(
                {
                    "family_id": record["family_id"],
                    "path": record["path"],
                    "failure_reason": "malformed_artifact",
                }
            )
    return missing


def _stale_artifacts(artifact_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "family_id": record["family_id"],
            "path": record["path"],
            "failure_reason": "stale_artifact",
        }
        for record in artifact_records
        if record["status"] == "stale"
    ]


def _trace_hash_mismatches(
    artifact_records: list[dict[str, Any]],
    repo_root: Path,
) -> list[dict[str, Any]]:
    diagnostics = next(
        (
            record
            for record in artifact_records
            if record["family_id"] == "applicability_trace"
            and record["path"].endswith("applicability_retrieval_graph_diagnostics.json")
            and record["exists"]
            and record["status"] == "present"
        ),
        None,
    )
    if diagnostics is None:
        return []

    mismatches = []
    trace_records = _family_records(artifact_records, "applicability_trace")
    for suffix, key in (
        ("applicability_retrieval_trace.jsonl", "retrieval_trace_sha256"),
        ("applicability_graph_trace.jsonl", "graph_trace_sha256"),
    ):
        record = next((entry for entry in trace_records if entry["path"].endswith(suffix)), None)
        expected = _string(diagnostics.get(key))
        actual = _string(record.get("artifact_sha256")) if record else None
        if expected and actual and expected != actual:
            mismatches.append(
                {
                    "family_id": "applicability_trace",
                    "path": record["path"],
                    "expected": expected,
                    "actual": actual,
                }
            )
    del repo_root
    return mismatches


def _missing_artifact_hash_links(artifact_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    missing = []
    for record in artifact_records:
        if record["required"] and record["exists"] and not record.get("artifact_sha256"):
            missing.append({"family_id": record["family_id"], "path": record["path"]})
        if record["family_id"] == "source_catalog" and record.get("missing_artifact_hash_count", 0):
            missing.append(
                {
                    "family_id": record["family_id"],
                    "path": record["path"],
                    "missing_artifact_hash_count": record["missing_artifact_hash_count"],
                }
            )
    return missing


def _phase_eval_direct_eval_present(artifact_records: list[dict[str, Any]]) -> bool:
    phase_records = _family_records(artifact_records, "phase_eval")
    if not phase_records:
        return False
    return all(
        not record["required"]
        or _string(record.get("direct_eval_status")) == "direct_eval_present"
        for record in phase_records
        if record["exists"] and record["status"] == "present"
    )


def _family_records(artifact_records: list[dict[str, Any]], family_id: str) -> list[dict[str, Any]]:
    return [record for record in artifact_records if record["family_id"] == family_id]


def _load_replay_context(repo_root: Path, review_id: str | None) -> dict[str, Any]:
    if not review_id:
        return {}
    path = repo_root / "config" / "replay_contexts" / f"{review_id}.json"
    if not path.exists():
        return {}
    try:
        return _read_json(path)
    except (OSError, json.JSONDecodeError):
        return {}


def _resolve_catalog_dir(
    *,
    catalog_dir: Path | None,
    replay_context: dict[str, Any],
    output_dir: Path,
    repo_root: Path,
) -> Path | None:
    if catalog_dir is not None:
        return _resolve_path(catalog_dir, repo_root)
    replay_catalog = _string(replay_context.get("catalog_dir"))
    if replay_catalog:
        return _resolve_path(Path(replay_catalog), repo_root)
    return output_dir / "catalog"


def _replay_context_catalog_matches(
    replay_context: dict[str, Any],
    catalog_dir: Path | None,
    repo_root: Path,
) -> bool:
    replay_catalog = _string(replay_context.get("catalog_dir"))
    if not replay_context or not replay_catalog or catalog_dir is None:
        return False
    return _resolve_path(Path(replay_catalog), repo_root).resolve() == catalog_dir.resolve()


def _replay_catalog_detail(
    replay_context: dict[str, Any],
    catalog_dir: Path | None,
) -> dict[str, str | None]:
    return {
        "replay_context_catalog_dir": _string(replay_context.get("catalog_dir")),
        "inventory_catalog_dir": str(catalog_dir) if catalog_dir is not None else None,
    }


def _promotion_suite_path(output_dir: Path, source_set_id: str | None) -> Path:
    suite_root = output_dir / "reviews" / "promotion_suite"
    preferred = suite_root / "post-v1-region1-ea-promotion-suite" / "promotion_suite_results.json"
    if preferred.exists():
        return preferred
    candidates = sorted(suite_root.glob("*/promotion_suite_results.json"))
    if source_set_id:
        for candidate in candidates:
            try:
                payload = _read_json(candidate)
            except (OSError, json.JSONDecodeError):
                continue
            if _string(payload.get("source_set_id")) == source_set_id:
                return candidate
    return preferred


def _matching_slot(payload: dict[str, Any], review_id: str | None) -> dict[str, Any]:
    if not review_id:
        return {}
    slots = payload.get("slots")
    if not isinstance(slots, list):
        return {}
    for slot in slots:
        if isinstance(slot, dict) and slot.get("review_id") == review_id:
            return slot
    return {}


def _passed_status(payload: dict[str, Any], summary: dict[str, Any]) -> bool | None:
    for key in ("passed", "reviewer_ready", "validation_passed"):
        if isinstance(payload.get(key), bool):
            return bool(payload[key])
        if isinstance(summary.get(key), bool):
            return bool(summary[key])
    if _string(payload.get("machine_replay_status")):
        return payload.get("machine_replay_status") == "passed"
    if _string(payload.get("validation_status")):
        return payload.get("validation_status") == "passed"
    return None


def _write_results(path: Path, summary: dict[str, Any], report: str, format: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if format == "markdown":
        path.write_text(report, encoding="utf-8")
    else:
        path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _markdown_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Eval Trace Inventory Report",
        "",
        f"Schema version: `{INVENTORY_REPORT_SCHEMA_VERSION}`",
        f"Coverage status: `{summary['coverage_status']}`",
        f"Passed: `{str(summary['passed']).lower()}`",
        "",
        "## Scope",
        "",
        f"- Source set: `{summary['scope']['source_set_id']}`",
        f"- Review: `{summary['scope']['review_id']}`",
        f"- Catalog dir: `{summary['scope']['catalog_dir']}`",
        "",
        "## Link Status",
        "",
    ]
    for check in summary["required_link_status"]["checks"]:
        state = "passed" if check["passed"] else f"failed: {check['failure_reason']}"
        lines.append(f"- `{check['check_id']}`: {state}")
    return "\n".join(lines) + "\n"


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise json.JSONDecodeError("JSON payload must be an object", path.read_text(), 0)
    return payload


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string(value: Any) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def _resolve_path(path: Path, repo_root: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def _display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root))
    except ValueError:
        return str(path)
