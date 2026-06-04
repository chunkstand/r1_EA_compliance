from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import json

from .applicability_eval_support import _stable_sha256
from .applicability_eval_support import _strings
from .applicability_eval_support import _write_json
from .records import sha256_file


APPLICABILITY_FAILURE_INTAKE_SCHEMA_VERSION = "applicability-failure-intake-cases-v0"
APPLICABILITY_FAILURE_INTAKE_CASE_SCHEMA_VERSION = "applicability-failure-intake-case-v0"


def write_applicability_failure_intake_cases(
    *,
    eval_output_dir: Path,
    eval_payload: dict[str, Any],
    eval_file: Path,
    case_results: list[dict[str, Any]],
) -> dict[str, Any]:
    cases = [
        _failure_intake_case(case_result)
        for case_result in case_results
        if _needs_intake(case_result)
    ]
    validation = _validation(cases)
    summary_without_hash = _summary(cases=cases, validation=validation)
    payload_without_hash = {
        "schema_version": APPLICABILITY_FAILURE_INTAKE_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "eval_id": eval_payload.get("id"),
        "eval_version": eval_payload.get("version"),
        "eval_file": str(eval_file),
        "eval_file_sha256": sha256_file(eval_file) if eval_file.exists() else None,
        "case_count": len(cases),
        "cases": cases,
        "validation": validation,
        "summary": summary_without_hash,
    }
    stable_hash = _stable_sha256(payload_without_hash)
    payload = {
        **payload_without_hash,
        "failure_intake_cases_sha256": stable_hash,
        "summary": {
            **summary_without_hash,
            "failure_intake_cases_sha256": stable_hash,
        },
    }
    output_path = eval_output_dir / "applicability_failure_intake_cases.json"
    _write_json(output_path, payload)
    file_hash = sha256_file(output_path)
    return {
        "path": output_path,
        "sha256": stable_hash,
        "file_sha256": file_hash,
        "payload": payload,
        "summary": {
            **payload["summary"],
            "failure_intake_cases_path": str(output_path),
            "failure_intake_cases_file_sha256": file_hash,
        },
    }


def _failure_intake_case(case_result: dict[str, Any]) -> dict[str, Any]:
    source_artifact_refs = _source_artifact_refs(case_result)
    source_lineage = _source_lineage(case_result)
    failure_reasons = _strings(case_result.get("failure_reasons"))
    needs_adjudication = _case_needs_adjudication(case_result)
    tags = sorted(
        set(
            [
                "applicability",
                "failure-intake",
                *(_strings(case_result.get("coverage_tags"))),
                *[str(key) for key in (case_result.get("failure_category_counts") or {})],
            ]
        )
    )
    if needs_adjudication:
        tags.append("needs-adjudication")
    return {
        "schema_version": APPLICABILITY_FAILURE_INTAKE_CASE_SCHEMA_VERSION,
        "case_id": f"applicability-failure-intake-{case_result.get('id')}",
        "source_case_id": case_result.get("id"),
        "review_id": case_result.get("review_id"),
        "source_set_id": case_result.get("source_set_id"),
        "profile": case_result.get("profile"),
        "owner_surface": "applicability_eval",
        "risk_level": "high" if failure_reasons else "medium",
        "passed": bool(case_result.get("passed")),
        "needs_adjudication": needs_adjudication,
        "actual_statuses": case_result.get("actual_statuses") or {},
        "expected_statuses": case_result.get("expected_statuses") or {},
        "failure_reasons": failure_reasons,
        "failure_category_counts": case_result.get("failure_category_counts") or {},
        "assertion_contract": {
            "assertions": _assertions(case_result),
            "deterministic_scorers": _deterministic_scorers(case_result),
            "llm_judge": {
                "status": "reserved_deferred",
                "requires_approved_milestone": True,
                "required_before_enablement": [
                    "model_identity",
                    "prompt_hash",
                    "rubric_hash",
                    "temperature",
                    "calibration_examples",
                    "precision_recall_against_human_labels",
                ],
            },
        },
        "source_trace": {
            "source_artifact_refs": source_artifact_refs,
            "source_record_ids": source_lineage["source_record_ids"],
            "citation_labels": source_lineage["citation_labels"],
            "retrieval_trace_ids": source_lineage["retrieval_trace_ids"],
            "graph_path_ids": _strings(case_result.get("selected_graph_path_ids"))
            or _strings(case_result.get("graph_path_ids")),
        },
        "lifecycle": {
            "review_condition": (
                "Review when applicability scorer, fixture expectations, source-set identity, "
                "or source artifact hashes change."
            ),
            "removal_condition": (
                "Remove only after a superseding passing or adjudicated applicability case "
                "covers the same assertion."
            ),
        },
        "human_label": {
            "status": "unlabeled",
            "labeler": None,
            "labels": [],
            "note": None,
            "reviewed_at": None,
        },
        "tags": sorted(set(tags)),
    }


def _source_artifact_refs(case_result: dict[str, Any]) -> list[dict[str, Any]]:
    fields = [
        ("authority_universe", "authority_universe_path"),
        ("package_fact_graph", "package_fact_graph_path"),
        ("retrieval_trace", "retrieval_trace_path"),
        ("graph_trace", "graph_trace_path"),
        ("applicability_validation", "applicability_validation_path"),
        ("gate_graph", "gate_graph_path"),
        ("gate_graph_summary", "gate_graph_summary_path"),
        ("gate_graph_validation", "gate_graph_validation_path"),
        ("generated_rule_pack", "generated_rule_pack_path"),
    ]
    refs = []
    for artifact_name, field in fields:
        value = str(case_result.get(field) or "").strip()
        if not value:
            continue
        path = Path(value)
        if not path.exists():
            continue
        refs.append(
            {
                "artifact_name": artifact_name,
                "artifact_ref": value,
                "sha256": sha256_file(path),
            }
        )
    return refs


def _source_lineage(case_result: dict[str, Any]) -> dict[str, list[str]]:
    retrieval_rows = _read_jsonl(Path(str(case_result.get("retrieval_trace_path") or "")))
    source_record_ids = set()
    citation_labels = set()
    retrieval_trace_ids = set()
    for row in retrieval_rows:
        if row.get("retrieval_trace_id"):
            retrieval_trace_ids.add(str(row["retrieval_trace_id"]))
        for result in row.get("ranked_results") or []:
            if not isinstance(result, dict) or result.get("selected_status") != "selected":
                continue
            if result.get("source_record_id"):
                source_record_ids.add(str(result["source_record_id"]))
            if result.get("citation_label"):
                citation_labels.add(str(result["citation_label"]))
    for values in (case_result.get("expected_source_record_ids_by_rule_id") or {}).values():
        source_record_ids.update(_strings(values))
    return {
        "source_record_ids": sorted(source_record_ids),
        "citation_labels": sorted(citation_labels),
        "retrieval_trace_ids": sorted(retrieval_trace_ids),
    }


def _assertions(case_result: dict[str, Any]) -> list[str]:
    assertions = []
    if case_result.get("failure_reasons"):
        assertions.append("Failure reasons remain replayable from hashed applicability artifacts.")
    if _case_needs_adjudication(case_result):
        assertions.append(
            "Unresolved or needs-adjudication decisions preserve review/source-set, trace, "
            "artifact, and scorer provenance."
        )
    if case_result.get("expected_statuses"):
        assertions.append("Expected applicability statuses remain explicit and replayable.")
    return assertions or ["Applicability case remains replayable from hashed artifacts."]


def _deterministic_scorers(case_result: dict[str, Any]) -> list[dict[str, Any]]:
    scorer_names = [
        "authority_universe_coverage",
        "retrieval_trace_quality",
        "graph_trace_quality",
        "decision_partition_fidelity",
        "generated_rule_pack_fidelity",
    ]
    if case_result.get("gate_graph_required"):
        scorer_names.append("gate_graph_consistency")
    return [
        {
            "score_name": name,
            "score_kind": "applicability_direct_eval",
            "status": "contract_defined",
            "required": True,
        }
        for name in scorer_names
    ]


def _validation(cases: list[dict[str, Any]]) -> dict[str, Any]:
    checks = [
        _check(
            "intake_cases_have_owner_risk_and_lifecycle",
            all(
                case.get("owner_surface")
                and case.get("risk_level") in {"medium", "high", "critical"}
                and (case.get("lifecycle") or {}).get("review_condition")
                and (case.get("lifecycle") or {}).get("removal_condition")
                for case in cases
            ),
        ),
        _check(
            "intake_cases_have_assertions",
            all((case.get("assertion_contract") or {}).get("assertions") for case in cases),
        ),
        _check(
            "intake_cases_have_hashed_artifacts",
            all(
                case.get("source_trace", {}).get("source_artifact_refs")
                and all(
                    ref.get("artifact_ref") and ref.get("sha256")
                    for ref in case.get("source_trace", {}).get("source_artifact_refs") or []
                )
                for case in cases
            ),
        ),
        _check(
            "intake_cases_have_trace_or_source_lineage",
            all(
                case.get("source_trace", {}).get("retrieval_trace_ids")
                or case.get("source_trace", {}).get("graph_path_ids")
                or case.get("source_trace", {}).get("source_record_ids")
                for case in cases
            ),
        ),
    ]
    return {
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def _summary(*, cases: list[dict[str, Any]], validation: dict[str, Any]) -> dict[str, Any]:
    failure_categories: Counter[str] = Counter()
    for case in cases:
        failure_categories.update(case.get("failure_category_counts") or {})
    return {
        "schema_version": "applicability-failure-intake-summary-v0",
        "passed": bool(validation.get("passed")),
        "validation_passed": bool(validation.get("passed")),
        "failure_intake_candidate_count": len(cases),
        "replayable_case_count": len(cases) if validation.get("passed") else 0,
        "failed_case_count": sum(1 for case in cases if not case.get("passed")),
        "needs_adjudication_case_count": sum(
            1 for case in cases if case.get("needs_adjudication")
        ),
        "source_artifact_ref_count": sum(
            len(case.get("source_trace", {}).get("source_artifact_refs") or [])
            for case in cases
        ),
        "failure_category_counts": dict(sorted(failure_categories.items())),
    }


def _needs_intake(case_result: dict[str, Any]) -> bool:
    return not case_result.get("passed") or _case_needs_adjudication(case_result)


def _case_needs_adjudication(case_result: dict[str, Any]) -> bool:
    statuses = set((case_result.get("actual_statuses") or {}).values())
    return "needs_adjudication" in statuses or "unresolved" in statuses


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _check(name: str, passed: bool) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed)}


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
