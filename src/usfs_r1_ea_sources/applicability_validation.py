from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import hashlib
import json
import re

from .applicability_adjudication import APPLICABILITY_ADJUDICATION_APPLY_SCHEMA_VERSION
from .applicability_adjudication import APPLICABILITY_ADJUDICATION_EVAL_SCHEMA_VERSION
from .applicability_adjudication import APPLICABILITY_ADJUDICATION_TEMPLATE_SCHEMA_VERSION
from .applicability_adjudication import ApplicabilityAdjudicationApplyResult
from .applicability_adjudication import ApplicabilityAdjudicationEvalResult
from .applicability_adjudication import ApplicabilityAdjudicationTemplateResult
from .applicability_adjudication import _matching_adjudication_item_result
from .applicability_adjudication import evaluate_applicability_adjudication
from .applicability_adjudication import write_applicability_adjudication_template
from .applicability_adjudication_apply import apply_applicability_adjudication
from .records import sha256_file


APPLICABILITY_VALIDATION_SCHEMA_VERSION = "applicability-validation-v0"
SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
UNRESOLVED_STATUSES = {"unresolved", "needs_adjudication"}
FINAL_STATUSES = {"applicable", "not_applicable"}
REQUIRED_PROVENANCE_ENTITY_IDS = {
    "authority_universe",
    "package_fact_graph",
    "package_applicability_context",
    "retrieval_trace",
    "graph_trace",
    "decision_ledger",
    "search_coverage_certificates",
    "applicable_authorities",
    "non_applicable_authorities",
}
FILE_HASH_PROVENANCE_ENTITY_IDS = {
    "package_applicability_context",
    "retrieval_trace",
    "graph_trace",
    "decision_ledger",
    "applicable_authorities",
    "non_applicable_authorities",
    "applicability_adjudication",
    "applicability_adjudication_eval",
    "applicability_adjudication_apply",
}


@dataclass(frozen=True)
class ApplicabilityValidationResult:
    review_id: str
    source_set_id: str | None
    applicability_dir: Path
    validation_path: Path
    summary: dict[str, Any]


__all__ = [
    "APPLICABILITY_ADJUDICATION_APPLY_SCHEMA_VERSION",
    "APPLICABILITY_ADJUDICATION_EVAL_SCHEMA_VERSION",
    "APPLICABILITY_ADJUDICATION_TEMPLATE_SCHEMA_VERSION",
    "APPLICABILITY_VALIDATION_SCHEMA_VERSION",
    "ApplicabilityAdjudicationApplyResult",
    "ApplicabilityAdjudicationEvalResult",
    "ApplicabilityAdjudicationTemplateResult",
    "ApplicabilityValidationResult",
    "apply_applicability_adjudication",
    "evaluate_applicability_adjudication",
    "validate_applicability_run",
    "write_applicability_adjudication_template",
]


def validate_applicability_run(
    *,
    output_dir: Path,
    review_id: str,
    source_set_id: str | None = None,
    authority_universe_path: Path | None = None,
    package_fact_graph_path: Path | None = None,
    package_applicability_context_path: Path | None = None,
    package_fact_graph_validation_path: Path | None = None,
    retrieval_trace_path: Path | None = None,
    graph_trace_path: Path | None = None,
    decisions_path: Path | None = None,
    applicable_authorities_path: Path | None = None,
    non_applicable_authorities_path: Path | None = None,
    search_coverage_certificates_path: Path | None = None,
    provenance_path: Path | None = None,
    validation_path: Path | None = None,
) -> ApplicabilityValidationResult:
    """Validate the applicability-first artifacts before rule-pack generation."""

    output_dir = Path(output_dir)
    _validate_safe_segment(review_id, "review_id")
    applicability_dir = output_dir / "reviews" / review_id / "applicability"
    paths = _artifact_paths(
        applicability_dir=applicability_dir,
        authority_universe_path=authority_universe_path,
        package_fact_graph_path=package_fact_graph_path,
        package_applicability_context_path=package_applicability_context_path,
        package_fact_graph_validation_path=package_fact_graph_validation_path,
        retrieval_trace_path=retrieval_trace_path,
        graph_trace_path=graph_trace_path,
        decisions_path=decisions_path,
        applicable_authorities_path=applicable_authorities_path,
        non_applicable_authorities_path=non_applicable_authorities_path,
        search_coverage_certificates_path=search_coverage_certificates_path,
        provenance_path=provenance_path,
    )
    validation_path = Path(validation_path) if validation_path else (
        applicability_dir / "applicability_validation.json"
    )

    artifacts = _load_validation_artifacts(paths)
    if source_set_id is None:
        source_set_id = _first_present_source_set_id(artifacts)
    if source_set_id:
        _validate_safe_segment(source_set_id, "source_set_id")

    checks = _validation_checks(
        review_id=review_id,
        source_set_id=source_set_id,
        paths=paths,
        artifacts=artifacts,
    )
    failures = [
        failure
        for check in checks
        for failure in check.get("failures", [])
        if isinstance(failure, dict)
    ]
    failure_counts = Counter(str(failure.get("failure_category") or "") for failure in failures)
    decisions = artifacts["decisions"]
    status_counts = dict(sorted(Counter(_decision_status(row) for row in decisions).items()))
    unresolved_count = sum(status_counts.get(status, 0) for status in UNRESOLVED_STATUSES)
    passed = all(check["passed"] for check in checks)
    candidate_ids = _candidate_ids(artifacts["authority_universe"])
    applicable_ids = _partition_ids(artifacts["applicable_authorities"])
    non_applicable_ids = _partition_ids(artifacts["non_applicable_authorities"])
    hashes = _artifact_hashes(paths, artifacts)
    summary = {
        "schema_version": APPLICABILITY_VALIDATION_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": review_id,
        "source_set_id": source_set_id,
        "applicability_run_id": _first_present_run_id(artifacts),
        "passed": passed,
        "reviewer_ready": passed,
        "generated_rule_pack_ready": passed,
        "candidate_authority_count": len(candidate_ids),
        "decision_count": len(decisions),
        "decision_status_counts": status_counts,
        "applicable_authority_count": len(applicable_ids),
        "non_applicable_authority_count": len(non_applicable_ids),
        "unresolved_authority_count": unresolved_count,
        "needs_adjudication_authority_count": status_counts.get("needs_adjudication", 0),
        "failure_category_counts": dict(sorted(failure_counts.items())),
        "validation_path": str(validation_path),
        "artifact_hashes": hashes,
    }
    validation = {
        "schema_version": APPLICABILITY_VALIDATION_SCHEMA_VERSION,
        "created_at": summary["created_at"],
        "applicability_run_id": summary["applicability_run_id"],
        "review_id": review_id,
        "source_set_id": source_set_id,
        "passed": passed,
        "reviewer_ready": passed,
        "generated_rule_pack_ready": passed,
        "summary": summary,
        "artifact_paths": {name: str(path) for name, path in paths.items()},
        "hashes": hashes,
        "checks": checks,
        "failures": failures,
    }
    _write_json(validation_path, validation)
    return ApplicabilityValidationResult(
        review_id=review_id,
        source_set_id=source_set_id,
        applicability_dir=applicability_dir,
        validation_path=validation_path,
        summary=summary,
    )


def _artifact_paths(
    *,
    applicability_dir: Path,
    authority_universe_path: Path | None,
    package_fact_graph_path: Path | None,
    package_applicability_context_path: Path | None,
    package_fact_graph_validation_path: Path | None,
    retrieval_trace_path: Path | None,
    graph_trace_path: Path | None,
    decisions_path: Path | None,
    applicable_authorities_path: Path | None,
    non_applicable_authorities_path: Path | None,
    search_coverage_certificates_path: Path | None,
    provenance_path: Path | None,
) -> dict[str, Path]:
    return {
        "authority_universe": Path(authority_universe_path)
        if authority_universe_path
        else applicability_dir / "authority_universe_snapshot.json",
        "package_fact_graph": Path(package_fact_graph_path)
        if package_fact_graph_path
        else applicability_dir / "package_fact_graph.json",
        "package_applicability_context": Path(package_applicability_context_path)
        if package_applicability_context_path
        else applicability_dir / "package_applicability_context.json",
        "package_fact_graph_validation": Path(package_fact_graph_validation_path)
        if package_fact_graph_validation_path
        else applicability_dir / "package_fact_graph_validation.json",
        "retrieval_trace": Path(retrieval_trace_path)
        if retrieval_trace_path
        else applicability_dir / "applicability_retrieval_trace.jsonl",
        "graph_trace": Path(graph_trace_path)
        if graph_trace_path
        else applicability_dir / "applicability_graph_trace.jsonl",
        "decisions": Path(decisions_path)
        if decisions_path
        else applicability_dir / "applicability_decisions.jsonl",
        "applicable_authorities": Path(applicable_authorities_path)
        if applicable_authorities_path
        else applicability_dir / "applicable_authorities.json",
        "non_applicable_authorities": Path(non_applicable_authorities_path)
        if non_applicable_authorities_path
        else applicability_dir / "non_applicable_authorities.json",
        "search_coverage_certificates": Path(search_coverage_certificates_path)
        if search_coverage_certificates_path
        else applicability_dir / "search_coverage_certificates.json",
        "provenance": Path(provenance_path)
        if provenance_path
        else applicability_dir / "applicability_provenance.json",
    }


def _load_validation_artifacts(paths: dict[str, Path]) -> dict[str, Any]:
    return {
        "authority_universe": _read_json_if_exists(paths["authority_universe"]),
        "package_fact_graph": _read_json_if_exists(paths["package_fact_graph"]),
        "package_applicability_context": _read_json_if_exists(
            paths["package_applicability_context"]
        ),
        "package_fact_graph_validation": _read_json_if_exists(
            paths["package_fact_graph_validation"]
        ),
        "retrieval_rows": _read_jsonl_if_exists(paths["retrieval_trace"]),
        "graph_rows": _read_jsonl_if_exists(paths["graph_trace"]),
        "decisions": _read_jsonl_if_exists(paths["decisions"]),
        "applicable_authorities": _read_json_if_exists(paths["applicable_authorities"]),
        "non_applicable_authorities": _read_json_if_exists(paths["non_applicable_authorities"]),
        "search_coverage_certificates": _read_json_if_exists(
            paths["search_coverage_certificates"]
        ),
        "provenance": _read_json_if_exists(paths["provenance"]),
    }


def _validation_checks(
    *,
    review_id: str,
    source_set_id: str | None,
    paths: dict[str, Path],
    artifacts: dict[str, Any],
) -> list[dict[str, Any]]:
    candidates = artifacts["authority_universe"].get("candidate_authorities") or []
    decisions = artifacts["decisions"]
    applicable_ids = _partition_ids(artifacts["applicable_authorities"])
    non_applicable_ids = _partition_ids(artifacts["non_applicable_authorities"])
    retrieval_by_id = _records_by_key(artifacts["retrieval_rows"], "retrieval_trace_id")
    graph_by_id = _records_by_key(artifacts["graph_rows"], "graph_path_id")
    certificates_by_id = {
        str(row.get("coverage_certificate_id") or ""): row
        for row in artifacts["search_coverage_certificates"].get("certificates") or []
        if isinstance(row, dict) and row.get("coverage_certificate_id")
    }
    return [
        _check_required_artifacts(paths),
        _check_review_and_source_identity(
            review_id=review_id,
            source_set_id=source_set_id,
            artifacts=artifacts,
        ),
        _check_package_fact_graph_validation(paths=paths, artifacts=artifacts),
        _check_candidate_decisions(candidates, decisions),
        _check_partition(
            candidates=candidates,
            decisions=decisions,
            applicable_ids=applicable_ids,
            non_applicable_ids=non_applicable_ids,
        ),
        _check_no_unresolved(decisions),
        _check_applicable_evidence(decisions),
        _check_non_applicable_basis(decisions, certificates_by_id),
        _check_retrieval_traceability(decisions, retrieval_by_id),
        _check_graph_traceability(decisions, graph_by_id),
        _check_forest_plan_scope(decisions),
        _check_contradictory_package_evidence(decisions),
        _check_human_adjudication_replay(decisions),
        _check_artifact_freshness(paths=paths, artifacts=artifacts, decisions=decisions),
        _check_provenance(artifacts["provenance"], paths, artifacts),
    ]


def _check_required_artifacts(paths: dict[str, Path]) -> dict[str, Any]:
    missing = [
        {"artifact": name, "path": str(path)}
        for name, path in paths.items()
        if not path.exists()
    ]
    return _check(
        "required_applicability_artifacts_exist",
        not missing,
        [
            _failure(
                "missing_applicability_artifact",
                artifact=entry["artifact"],
                path=entry["path"],
            )
            for entry in missing
        ],
        {"missing": missing},
    )


def _check_review_and_source_identity(
    *,
    review_id: str,
    source_set_id: str | None,
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    failures = []
    for artifact_name in (
        "authority_universe",
        "package_fact_graph",
        "package_applicability_context",
        "applicable_authorities",
        "non_applicable_authorities",
        "search_coverage_certificates",
        "provenance",
    ):
        artifact = artifacts.get(artifact_name)
        if not isinstance(artifact, dict) or not artifact:
            continue
        if artifact.get("review_id") and artifact.get("review_id") != review_id:
            failures.append(
                _failure(
                    "package_cache_stale",
                    artifact=artifact_name,
                    details={
                        "field": "review_id",
                        "expected": review_id,
                        "actual": artifact.get("review_id"),
                    },
                )
            )
        if (
            source_set_id
            and artifact.get("source_set_id")
            and artifact.get("source_set_id") != source_set_id
        ):
            failures.append(
                _failure(
                    "source_set_stale",
                    artifact=artifact_name,
                    details={
                        "field": "source_set_id",
                        "expected": source_set_id,
                        "actual": artifact.get("source_set_id"),
                    },
                )
            )
    return _check(
        "review_and_source_set_identity_match",
        not failures,
        failures,
        {"review_id": review_id, "source_set_id": source_set_id},
    )


def _check_package_fact_graph_validation(
    *,
    paths: dict[str, Path],
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    validation = artifacts["package_fact_graph_validation"]
    nested_validation = (
        validation.get("validation")
        if isinstance(validation.get("validation"), dict)
        else {}
    )
    summary = (
        validation.get("summary")
        if isinstance(validation.get("summary"), dict)
        else {}
    )
    passed = bool(
        nested_validation.get("passed")
        if "passed" in nested_validation
        else summary.get("validation_passed")
    )
    expected_pairs = {
        "package_manifest_sha256": _first_present(
            artifacts["package_applicability_context"].get("package_manifest_sha256"),
            artifacts["package_fact_graph"].get("package_manifest_sha256"),
        ),
        "package_chunks_sha256": _first_present(
            artifacts["package_applicability_context"].get("package_chunks_sha256"),
            artifacts["package_fact_graph"].get("package_chunks_sha256"),
        ),
        "package_fact_graph_sha256": artifacts["package_fact_graph"].get(
            "package_fact_graph_sha256"
        ),
        "package_context_sha256": artifacts["package_applicability_context"].get(
            "package_context_sha256"
        ),
    }
    failures = []
    if not paths["package_fact_graph_validation"].exists():
        failures.append(
            _failure(
                "missing_applicability_artifact",
                artifact="package_fact_graph_validation",
                path=str(paths["package_fact_graph_validation"]),
            )
        )
    elif validation.get("schema_version") != "package-fact-graph-validation-v0":
        failures.append(
            _failure(
                "package_cache_stale",
                artifact="package_fact_graph_validation",
                details={
                    "field": "schema_version",
                    "actual": validation.get("schema_version"),
                },
            )
        )
    elif not passed:
        failures.append(
            _failure(
                "package_cache_stale",
                artifact="package_fact_graph_validation",
                details={"field": "validation.passed", "actual": False},
            )
        )
    for field, expected in expected_pairs.items():
        actual = validation.get(field)
        if expected and actual and actual != expected:
            failures.append(
                _failure(
                    "package_cache_stale",
                    artifact="package_fact_graph_validation",
                    details={"field": field, "expected": expected, "actual": actual},
                )
            )
    return _check(
        "package_fact_graph_validation_passes_current_artifacts",
        not failures,
        failures,
        {"path": str(paths["package_fact_graph_validation"])},
    )


def _check_candidate_decisions(
    candidates: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_ids = _candidate_ids_from_records(candidates)
    decision_ids = [str(row.get("candidate_authority_id") or "") for row in decisions]
    decision_counts = Counter(decision_ids)
    missing = sorted(candidate_ids - set(decision_ids))
    duplicates = sorted(
        candidate_id for candidate_id, count in decision_counts.items() if count > 1
    )
    unexpected = sorted(set(decision_ids) - candidate_ids)
    failures = [
        *[
            _failure("missing_candidate_decision", candidate_authority_id=candidate_id)
            for candidate_id in missing
        ],
        *[
            _failure("duplicate_decision", candidate_authority_id=candidate_id)
            for candidate_id in duplicates
        ],
        *[
            _failure("partition_gap", candidate_authority_id=candidate_id)
            for candidate_id in unexpected
        ],
    ]
    return _check(
        "candidate_universe_has_exactly_one_decision",
        not failures and bool(candidate_ids),
        failures,
        {
            "candidate_authority_count": len(candidate_ids),
            "decision_count": len(decisions),
            "missing_candidate_authority_ids": missing,
            "duplicate_candidate_authority_ids": duplicates,
            "unexpected_candidate_authority_ids": unexpected,
        },
    )


def _check_partition(
    *,
    candidates: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    applicable_ids: set[str],
    non_applicable_ids: set[str],
) -> dict[str, Any]:
    candidate_ids = _candidate_ids_from_records(candidates)
    overlap = sorted(applicable_ids & non_applicable_ids)
    decision_ids_by_status = defaultdict(set)
    for decision in decisions:
        decision_ids_by_status[_decision_status(decision)].add(
            str(decision.get("candidate_authority_id") or "")
        )
    final_ids = decision_ids_by_status["applicable"] | decision_ids_by_status["not_applicable"]
    partition_ids = applicable_ids | non_applicable_ids
    missing_final = sorted(final_ids - partition_ids)
    partition_extra = sorted(partition_ids - final_ids)
    unresolved_ids = sorted(candidate_ids - partition_ids)
    failures = [
        *[
            _failure("partition_overlap", candidate_authority_id=candidate_id)
            for candidate_id in overlap
        ],
        *[
            _failure("partition_gap", candidate_authority_id=candidate_id)
            for candidate_id in missing_final
        ],
        *[
            _failure("partition_gap", candidate_authority_id=candidate_id)
            for candidate_id in partition_extra
        ],
        *[
            _failure("unresolved_authority", candidate_authority_id=candidate_id)
            for candidate_id in unresolved_ids
        ],
    ]
    return _check(
        "applicable_and_non_applicable_partition_candidate_universe",
        not failures and bool(candidate_ids),
        failures,
        {
            "candidate_authority_count": len(candidate_ids),
            "applicable_partition_count": len(applicable_ids),
            "non_applicable_partition_count": len(non_applicable_ids),
            "overlap": overlap,
            "missing_final": missing_final,
            "partition_extra": partition_extra,
            "unresolved_or_unpartitioned": unresolved_ids,
        },
    )


def _check_no_unresolved(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    unresolved = [
        str(decision.get("candidate_authority_id") or "")
        for decision in decisions
        if _decision_status(decision) in UNRESOLVED_STATUSES
    ]
    return _check(
        "no_unresolved_or_needs_adjudication_decisions",
        not unresolved,
        [
            _failure("unresolved_authority", candidate_authority_id=candidate_id)
            for candidate_id in unresolved
        ],
        {"unresolved_candidate_authority_ids": unresolved},
    )


def _check_applicable_evidence(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    failures = []
    for decision in decisions:
        if _decision_status(decision) != "applicable":
            continue
        basis_type = str(decision.get("basis_type") or "")
        has_mandatory_basis = basis_type == "mandatory_baseline" and bool(
            (decision.get("basis") or {}).get("baseline_required")
        )
        has_package = bool(decision.get("package_evidence_spans"))
        has_source = bool(decision.get("source_library_evidence_spans"))
        has_validated_mandatory_basis = has_mandatory_basis and has_source
        if not (has_validated_mandatory_basis or (has_package and has_source)):
            failures.append(
                _failure(
                    "applicable_evidence_gap",
                    candidate_authority_id=str(
                        decision.get("candidate_authority_id") or ""
                    ),
                )
            )
    return _check(
        "applicable_decisions_have_required_basis",
        not failures,
        failures,
        {"failure_count": len(failures)},
    )


def _check_non_applicable_basis(
    decisions: list[dict[str, Any]],
    certificates_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    failures = []
    for decision in decisions:
        if _decision_status(decision) != "not_applicable":
            continue
        cert_ids = [str(value) for value in decision.get("search_coverage_certificate_ids") or []]
        sufficient_cert = any(
            (certificates_by_id.get(cert_id) or {}).get("coverage_result") == "sufficient"
            for cert_id in cert_ids
        )
        has_negative = bool(decision.get("negative_evidence_spans"))
        has_trigger_miss = bool(decision.get("explicit_trigger_miss_evidence"))
        has_adjudication = bool(decision.get("human_adjudication_refs"))
        if not (has_adjudication or (sufficient_cert and (has_negative or has_trigger_miss))):
            failures.append(
                _failure(
                    "non_applicable_basis_gap",
                    candidate_authority_id=str(
                        decision.get("candidate_authority_id") or ""
                    ),
                )
            )
        if not (has_adjudication or sufficient_cert):
            failures.append(
                _failure(
                    "search_coverage_gap",
                    candidate_authority_id=str(
                        decision.get("candidate_authority_id") or ""
                    ),
                )
            )
    return _check(
        "non_applicable_decisions_have_basis_or_adjudication",
        not failures,
        failures,
        {"failure_count": len(failures)},
    )


def _check_retrieval_traceability(
    decisions: list[dict[str, Any]],
    retrieval_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    failures = []
    for decision in decisions:
        trace_ids = [str(value) for value in decision.get("retrieval_trace_ids") or []]
        used_retrieval = bool(
            trace_ids
            or decision.get("selected_retrieval_result_ids")
            or decision.get("source_library_evidence_spans")
        )
        if not used_retrieval:
            continue
        if not trace_ids:
            failures.append(
                _failure(
                    "retrieval_trace_gap",
                    candidate_authority_id=str(
                        decision.get("candidate_authority_id") or ""
                    ),
                    details={"reason": "missing_retrieval_trace_ids"},
                )
            )
            continue
        for trace_id in trace_ids:
            row = retrieval_by_id.get(trace_id)
            if not _retrieval_trace_row_valid(row):
                failures.append(
                    _failure(
                        "retrieval_trace_gap",
                        candidate_authority_id=str(
                            decision.get("candidate_authority_id") or ""
                        ),
                        details={"retrieval_trace_id": trace_id},
                    )
                )
    return _check(
        "retrieval_backed_decisions_have_trace_rows",
        not failures,
        failures,
        {"failure_count": len(failures)},
    )


def _check_graph_traceability(
    decisions: list[dict[str, Any]],
    graph_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    failures = []
    for decision in decisions:
        graph_path_ids = [str(value) for value in decision.get("graph_path_ids") or []]
        for graph_path_id in graph_path_ids:
            row = graph_by_id.get(graph_path_id)
            if not _graph_trace_row_valid(row):
                failures.append(
                    _failure(
                        "graph_trace_gap",
                        candidate_authority_id=str(
                            decision.get("candidate_authority_id") or ""
                        ),
                        details={"graph_path_id": graph_path_id},
                    )
                )
    return _check(
        "graph_supported_decisions_have_path_rows",
        not failures,
        failures,
        {"failure_count": len(failures)},
    )


def _check_forest_plan_scope(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    failures = []
    for decision in decisions:
        if decision.get("candidate_authority_type") != "forest_plan_component":
            continue
        if _decision_status(decision) in UNRESOLVED_STATUSES:
            failures.append(
                _failure(
                    "forest_plan_scope_unresolved",
                    candidate_authority_id=str(
                        decision.get("candidate_authority_id") or ""
                    ),
                )
            )
            continue
        has_source = bool(decision.get("source_library_evidence_spans"))
        has_package_or_negative = bool(
            decision.get("package_evidence_spans")
            or decision.get("negative_evidence_spans")
            or decision.get("explicit_trigger_miss_evidence")
            or decision.get("human_adjudication_refs")
        )
        if not (has_source and has_package_or_negative):
            failures.append(
                _failure(
                    "forest_plan_scope_unresolved",
                    candidate_authority_id=str(
                        decision.get("candidate_authority_id") or ""
                    ),
                )
            )
    return _check(
        "forest_plan_component_decisions_have_scope_context",
        not failures,
        failures,
        {"failure_count": len(failures)},
    )


def _check_contradictory_package_evidence(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    failures = []
    for decision in decisions:
        if _decision_status(decision) not in FINAL_STATUSES:
            continue
        has_positive = bool(decision.get("package_evidence_spans"))
        has_negative = bool(decision.get("negative_evidence_spans"))
        has_contradiction_notes = bool(decision.get("contradiction_notes"))
        has_adjudication = bool(decision.get("human_adjudication_refs"))
        if (has_contradiction_notes or (has_positive and has_negative)) and not has_adjudication:
            failures.append(
                _failure(
                    "contradictory_package_evidence",
                    candidate_authority_id=str(
                        decision.get("candidate_authority_id") or ""
                    ),
                    details={
                        "has_package_evidence": has_positive,
                        "has_negative_evidence": has_negative,
                        "has_contradiction_notes": has_contradiction_notes,
                    },
                )
            )
    return _check(
        "contradictory_package_evidence_requires_adjudication",
        not failures,
        failures,
        {"failure_count": len(failures)},
    )


def _check_human_adjudication_replay(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    failures = []
    eval_cache: dict[Path, dict[str, Any]] = {}
    for decision in decisions:
        refs = [
            ref
            for ref in decision.get("human_adjudication_refs") or []
            if isinstance(ref, dict)
        ]
        requires_replay = str(decision.get("basis_type") or "") == "human_adjudication" or bool(
            refs
        )
        if not requires_replay:
            continue
        candidate_id = str(decision.get("candidate_authority_id") or "")
        if not refs:
            failures.append(
                _failure(
                    "adjudication_missing",
                    candidate_authority_id=candidate_id,
                    details={"reason": "human_adjudication_basis_without_reference"},
                )
            )
            continue
        for ref in refs:
            failures.extend(
                _adjudication_ref_failures(
                    decision=decision,
                    ref=ref,
                    eval_cache=eval_cache,
                )
            )
    return _check(
        "human_adjudication_references_are_replayable",
        not failures,
        failures,
        {"failure_count": len(failures)},
    )


def _adjudication_ref_failures(
    *,
    decision: dict[str, Any],
    ref: dict[str, Any],
    eval_cache: dict[Path, dict[str, Any]],
) -> list[dict[str, Any]]:
    failures = []
    candidate_id = str(decision.get("candidate_authority_id") or "")
    decision_status = _decision_status(decision)
    required_strings = (
        "adjudication_id",
        "item_id",
        "decision_id",
        "candidate_authority_id",
        "adjudication_eval_path",
        "final_status",
        "disposition",
        "adjudicated_at",
        "source_type",
        "rationale",
    )
    missing_fields = [
        field
        for field in required_strings
        if not str(ref.get(field) or "").strip()
    ]
    if not _string_list(ref.get("adjudicated_by")):
        missing_fields.append("adjudicated_by")
    if not _string_list(ref.get("supporting_citation_refs")):
        missing_fields.append("supporting_citation_refs")
    if missing_fields:
        failures.append(
            _failure(
                "adjudication_missing",
                candidate_authority_id=candidate_id,
                details={"reason": "adjudication_reference_incomplete", "fields": missing_fields},
            )
        )
    if ref.get("decision_id") != decision.get("decision_id"):
        failures.append(
            _failure(
                "adjudication_missing",
                candidate_authority_id=candidate_id,
                details={
                    "field": "decision_id",
                    "expected": decision.get("decision_id"),
                    "actual": ref.get("decision_id"),
                },
            )
        )
    if ref.get("candidate_authority_id") != decision.get("candidate_authority_id"):
        failures.append(
            _failure(
                "adjudication_missing",
                candidate_authority_id=candidate_id,
                details={
                    "field": "candidate_authority_id",
                    "expected": decision.get("candidate_authority_id"),
                    "actual": ref.get("candidate_authority_id"),
                },
            )
        )
    if ref.get("final_status") != decision_status:
        failures.append(
            _failure(
                "adjudication_missing",
                candidate_authority_id=candidate_id,
                details={
                    "field": "final_status",
                    "expected": decision_status,
                    "actual": ref.get("final_status"),
                },
            )
        )
    expected_disposition = (
        "human_applicable" if decision_status == "applicable" else "human_not_applicable"
    )
    if decision_status in FINAL_STATUSES and ref.get("disposition") != expected_disposition:
        failures.append(
            _failure(
                "adjudication_missing",
                candidate_authority_id=candidate_id,
                details={
                    "field": "disposition",
                    "expected": expected_disposition,
                    "actual": ref.get("disposition"),
                },
            )
        )
    adjudication_file = str(ref.get("adjudication_file") or "").strip()
    if adjudication_file and not Path(adjudication_file).exists():
        failures.append(
            _failure(
                "adjudication_missing",
                candidate_authority_id=candidate_id,
                path=adjudication_file,
                details={"reason": "adjudication_file_missing"},
            )
        )
    eval_path_text = str(ref.get("adjudication_eval_path") or "").strip()
    if not eval_path_text:
        return failures
    eval_path = Path(eval_path_text)
    if not eval_path.exists():
        failures.append(
            _failure(
                "adjudication_missing",
                candidate_authority_id=candidate_id,
                path=eval_path_text,
                details={"reason": "adjudication_eval_missing"},
            )
        )
        return failures
    eval_payload = eval_cache.get(eval_path)
    if eval_payload is None:
        eval_payload = _read_json_if_exists(eval_path)
        eval_cache[eval_path] = eval_payload
    if eval_payload.get("schema_version") != APPLICABILITY_ADJUDICATION_EVAL_SCHEMA_VERSION:
        failures.append(
            _failure(
                "adjudication_missing",
                candidate_authority_id=candidate_id,
                path=eval_path_text,
                details={
                    "field": "schema_version",
                    "actual": eval_payload.get("schema_version"),
                },
            )
        )
    summary = eval_payload.get("summary") if isinstance(eval_payload.get("summary"), dict) else {}
    if not summary.get("passed"):
        failures.append(
            _failure(
                "adjudication_missing",
                candidate_authority_id=candidate_id,
                path=eval_path_text,
                details={"field": "summary.passed", "actual": summary.get("passed")},
            )
        )
    item_result = _matching_adjudication_item_result(eval_payload, ref)
    if not item_result or not item_result.get("passed"):
        failures.append(
            _failure(
                "adjudication_missing",
                candidate_authority_id=candidate_id,
                path=eval_path_text,
                details={
                    "reason": "adjudication_item_not_replayable",
                    "item_id": ref.get("item_id"),
                    "decision_id": ref.get("decision_id"),
                },
            )
        )
    return failures


def _check_artifact_freshness(
    *,
    paths: dict[str, Path],
    artifacts: dict[str, Any],
    decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    failures = []
    universe_hash = artifacts["authority_universe"].get("authority_universe_sha256")
    package_fact_graph_hash = artifacts["package_fact_graph"].get("package_fact_graph_sha256")
    package_manifest_hash = _first_present(
        artifacts["package_applicability_context"].get("package_manifest_sha256"),
        artifacts["package_fact_graph"].get("package_manifest_sha256"),
    )
    package_chunks_hash = _first_present(
        artifacts["package_applicability_context"].get("package_chunks_sha256"),
        artifacts["package_fact_graph"].get("package_chunks_sha256"),
    )
    retrieval_hash = _optional_file_sha256(paths["retrieval_trace"])
    graph_hash = _optional_file_sha256(paths["graph_trace"])
    coverage_hash = artifacts["search_coverage_certificates"].get(
        "search_coverage_certificates_sha256"
    )
    decision_hash = _optional_file_sha256(paths["decisions"])
    applicable_decision_hash = artifacts["applicable_authorities"].get(
        "applicability_decisions_sha256"
    )
    non_applicable_decision_hash = artifacts["non_applicable_authorities"].get(
        "applicability_decisions_sha256"
    )
    if decision_hash and applicable_decision_hash and applicable_decision_hash != decision_hash:
        failures.append(
            _failure(
                "source_set_stale",
                artifact="applicable_authorities",
                details={"field": "applicability_decisions_sha256"},
            )
        )
    if (
        decision_hash
        and non_applicable_decision_hash
        and non_applicable_decision_hash != decision_hash
    ):
        failures.append(
            _failure(
                "source_set_stale",
                artifact="non_applicable_authorities",
                details={"field": "applicability_decisions_sha256"},
            )
        )
    expected_partition_pairs = {
        "authority_universe_sha256": (universe_hash, "source_set_stale"),
        "package_manifest_sha256": (package_manifest_hash, "package_cache_stale"),
        "package_chunks_sha256": (package_chunks_hash, "package_cache_stale"),
        "package_fact_graph_sha256": (package_fact_graph_hash, "package_cache_stale"),
        "retrieval_trace_sha256": (retrieval_hash, "retrieval_trace_stale"),
        "graph_trace_sha256": (graph_hash, "graph_trace_stale"),
        "search_coverage_certificates_sha256": (
            coverage_hash,
            "search_coverage_stale",
        ),
        "catalog_sha256": (
            artifacts["authority_universe"].get("catalog_sha256"),
            "source_set_stale",
        ),
    }
    for artifact_name in ("applicable_authorities", "non_applicable_authorities"):
        artifact = artifacts[artifact_name]
        for field, (expected, category) in expected_partition_pairs.items():
            actual = artifact.get(field)
            if expected and actual and actual != expected:
                failures.append(
                    _failure(
                        category,
                        artifact=artifact_name,
                        details={"field": field, "expected": expected, "actual": actual},
                    )
                )
    expected_coverage_pairs = {
        "authority_universe_sha256": (universe_hash, "source_set_stale"),
        "package_fact_graph_sha256": (package_fact_graph_hash, "package_cache_stale"),
        "retrieval_trace_sha256": (retrieval_hash, "retrieval_trace_stale"),
        "graph_trace_sha256": (graph_hash, "graph_trace_stale"),
    }
    for field, (expected, category) in expected_coverage_pairs.items():
        actual = artifacts["search_coverage_certificates"].get(field)
        if expected and actual and actual != expected:
            failures.append(
                _failure(
                    category,
                    artifact="search_coverage_certificates",
                    details={"field": field, "expected": expected, "actual": actual},
                )
            )
    for decision in decisions:
        freshness = decision.get("freshness") if isinstance(decision.get("freshness"), dict) else {}
        candidate_id = str(decision.get("candidate_authority_id") or "")
        expected_pairs = {
            "authority_universe_sha256": (universe_hash, "source_set_stale"),
            "package_manifest_sha256": (package_manifest_hash, "package_cache_stale"),
            "package_chunks_sha256": (package_chunks_hash, "package_cache_stale"),
            "package_fact_graph_sha256": (package_fact_graph_hash, "package_cache_stale"),
            "retrieval_trace_sha256": (retrieval_hash, "retrieval_trace_stale"),
            "graph_trace_sha256": (graph_hash, "graph_trace_stale"),
            "search_coverage_certificates_sha256": (
                coverage_hash,
                "search_coverage_stale",
            ),
        }
        for field, (expected, category) in expected_pairs.items():
            actual = freshness.get(field)
            if expected and actual and actual != expected:
                failures.append(
                    _failure(
                        category,
                        candidate_authority_id=candidate_id,
                        details={"field": field, "expected": expected, "actual": actual},
                    )
                )
    return _check(
        "artifact_hashes_match_current_inputs",
        not failures,
        failures,
        {"failure_count": len(failures)},
    )


def _check_provenance(
    provenance: dict[str, Any],
    paths: dict[str, Path],
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    entities = provenance.get("entities") if isinstance(provenance.get("entities"), list) else []
    expected_hashes = _expected_provenance_hashes(paths=paths, artifacts=artifacts)
    entity_ids = {
        str(entity.get("entity_id") or "")
        for entity in entities
        if isinstance(entity, dict)
    }
    missing = sorted(REQUIRED_PROVENANCE_ENTITY_IDS - entity_ids)
    missing_entity_failures = [
        _failure("provenance_gap", artifact=entity_id) for entity_id in missing
    ]
    missing_paths = []
    stale_hashes = []
    for entity in entities:
        if not isinstance(entity, dict):
            continue
        entity_id = str(entity.get("entity_id") or "")
        path = entity.get("path")
        if entity_id in REQUIRED_PROVENANCE_ENTITY_IDS and path and not Path(str(path)).exists():
            missing_paths.append({"entity_id": entity_id, "path": str(path)})
        if entity_id in REQUIRED_PROVENANCE_ENTITY_IDS and not entity.get("exists", True):
            missing_paths.append({"entity_id": entity_id, "path": str(path or "")})
        expected_hash = expected_hashes.get(entity_id)
        if (
            not expected_hash
            and entity_id in FILE_HASH_PROVENANCE_ENTITY_IDS
            and path
            and Path(str(path)).exists()
        ):
            expected_hash = sha256_file(Path(str(path)))
        actual_hash = str(entity.get("sha256") or "")
        if expected_hash and actual_hash != expected_hash:
            stale_hashes.append(
                {
                    "entity_id": entity_id,
                    "expected": expected_hash,
                    "actual": actual_hash or None,
                }
            )
    failures = [
        *missing_entity_failures,
        *[
            _failure("provenance_gap", artifact=row["entity_id"], path=row["path"])
            for row in missing_paths
        ],
        *[
            _failure(
                "provenance_gap",
                artifact=row["entity_id"],
                details={"expected": row["expected"], "actual": row["actual"]},
            )
            for row in stale_hashes
        ],
    ]
    return _check(
        "provenance_covers_required_applicability_artifacts",
        not failures and paths["provenance"].exists(),
        failures,
        {
            "missing_entity_ids": missing,
            "missing_entity_paths": missing_paths,
            "stale_entity_hashes": stale_hashes,
        },
    )


def _expected_provenance_hashes(
    *,
    paths: dict[str, Path],
    artifacts: dict[str, Any],
) -> dict[str, str | None]:
    return {
        "authority_universe": artifacts["authority_universe"].get(
            "authority_universe_sha256"
        ),
        "package_fact_graph": artifacts["package_fact_graph"].get(
            "package_fact_graph_sha256"
        ),
        "package_applicability_context": _optional_file_sha256(
            paths["package_applicability_context"]
        ),
        "retrieval_trace": _optional_file_sha256(paths["retrieval_trace"]),
        "graph_trace": _optional_file_sha256(paths["graph_trace"]),
        "decision_ledger": _optional_file_sha256(paths["decisions"]),
        "search_coverage_certificates": artifacts[
            "search_coverage_certificates"
        ].get("search_coverage_certificates_sha256"),
        "applicable_authorities": _optional_file_sha256(paths["applicable_authorities"]),
        "non_applicable_authorities": _optional_file_sha256(
            paths["non_applicable_authorities"]
        ),
        "package_manifest": _first_present(
            artifacts["package_applicability_context"].get("package_manifest_sha256"),
            artifacts["package_fact_graph"].get("package_manifest_sha256"),
        ),
        "package_chunks": _first_present(
            artifacts["package_applicability_context"].get("package_chunks_sha256"),
            artifacts["package_fact_graph"].get("package_chunks_sha256"),
        ),
    }


def _retrieval_trace_row_valid(row: dict[str, Any] | None) -> bool:
    if not isinstance(row, dict):
        return False
    if not row.get("query_type") or not row.get("retrieval_trace_id"):
        return False
    ranked_results = row.get("ranked_results")
    if not isinstance(ranked_results, list):
        return False
    for result in ranked_results:
        if not isinstance(result, dict):
            return False
        if result.get("selected_status") not in {"selected", "rejected"}:
            return False
        if result.get("rank") is None or not result.get("result_id"):
            return False
    searched_index = row.get("searched_index")
    return isinstance(searched_index, dict) and bool(
        searched_index.get("searched_index_hash")
        or searched_index.get("graph_artifact_hash")
    )


def _graph_trace_row_valid(row: dict[str, Any] | None) -> bool:
    if not isinstance(row, dict):
        return False
    if not row.get("graph_path_id"):
        return False
    if row.get("selected_status") not in {"selected", "rejected"}:
        return False
    if row.get("traversal_depth") is None:
        return False
    if row.get("graph_artifact_hash"):
        return True
    graph_artifacts = row.get("graph_artifacts")
    return any(
        isinstance(artifact, dict)
        and (artifact.get("graph_artifact_hash") or artifact.get("package_fact_graph_sha256"))
        for artifact in graph_artifacts or []
    )


def _artifact_hashes(paths: dict[str, Path], artifacts: dict[str, Any]) -> dict[str, Any]:
    return {
        "authority_universe_sha256": artifacts["authority_universe"].get(
            "authority_universe_sha256"
        ),
        "package_manifest_sha256": _first_present(
            artifacts["package_applicability_context"].get("package_manifest_sha256"),
            artifacts["package_fact_graph"].get("package_manifest_sha256"),
        ),
        "package_chunks_sha256": _first_present(
            artifacts["package_applicability_context"].get("package_chunks_sha256"),
            artifacts["package_fact_graph"].get("package_chunks_sha256"),
        ),
        "package_fact_graph_sha256": artifacts["package_fact_graph"].get(
            "package_fact_graph_sha256"
        ),
        "package_context_sha256": artifacts["package_applicability_context"].get(
            "package_context_sha256"
        ),
        "retrieval_trace_sha256": _optional_file_sha256(paths["retrieval_trace"]),
        "graph_trace_sha256": _optional_file_sha256(paths["graph_trace"]),
        "search_coverage_certificates_sha256": _optional_file_sha256(
            paths["search_coverage_certificates"]
        ),
        "applicability_decisions_sha256": _optional_file_sha256(paths["decisions"]),
        "applicable_authorities_sha256": _optional_file_sha256(
            paths["applicable_authorities"]
        ),
        "non_applicable_authorities_sha256": _optional_file_sha256(
            paths["non_applicable_authorities"]
        ),
        "applicability_provenance_sha256": _optional_file_sha256(paths["provenance"]),
        "catalog_sha256": artifacts["authority_universe"].get("catalog_sha256"),
        "source_claims_sha256": artifacts["authority_universe"].get("source_claims_sha256"),
        "rule_claim_links_sha256": artifacts["authority_universe"].get(
            "rule_claim_links_sha256"
        ),
        "forest_plan_component_inventory_sha256": artifacts["authority_universe"].get(
            "forest_plan_component_inventory_sha256"
        ),
    }


def _candidate_ids(authority_universe: dict[str, Any]) -> set[str]:
    return _candidate_ids_from_records(authority_universe.get("candidate_authorities") or [])


def _candidate_ids_from_records(records: list[dict[str, Any]]) -> set[str]:
    return {
        str(record.get("candidate_authority_id") or "")
        for record in records
        if isinstance(record, dict) and record.get("candidate_authority_id")
    }


def _partition_ids(payload: dict[str, Any]) -> set[str]:
    return {
        str(row.get("candidate_authority_id") or "")
        for row in payload.get("authorities") or []
        if isinstance(row, dict) and row.get("candidate_authority_id")
    }


def _decision_status(decision: dict[str, Any]) -> str:
    return str(decision.get("status") or "")


def _source_set_from_decisions(decisions: list[dict[str, Any]]) -> str | None:
    for decision in decisions:
        source_set_id = str(decision.get("source_set_id") or "").strip()
        if source_set_id:
            return source_set_id
    return None


def _first_present_source_set_id(artifacts: dict[str, Any]) -> str | None:
    for key in (
        "authority_universe",
        "package_fact_graph",
        "package_applicability_context",
        "applicable_authorities",
        "non_applicable_authorities",
        "search_coverage_certificates",
        "provenance",
    ):
        value = str((artifacts.get(key) or {}).get("source_set_id") or "").strip()
        if value:
            return value
    return _source_set_from_decisions(artifacts.get("decisions") or [])


def _first_present_run_id(artifacts: dict[str, Any]) -> str | None:
    for key in (
        "applicable_authorities",
        "non_applicable_authorities",
        "search_coverage_certificates",
        "provenance",
    ):
        value = str((artifacts.get(key) or {}).get("applicability_run_id") or "").strip()
        if value:
            return value
    for decision in artifacts.get("decisions") or []:
        value = str(decision.get("applicability_run_id") or "").strip()
        if value:
            return value
    return None


def _first_present(*values: Any) -> Any:
    for value in values:
        if value:
            return value
    return None


def _records_by_key(records: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    by_key = {}
    for record in records:
        value = str(record.get(key) or "")
        if value:
            by_key[value] = record
    return by_key


def _check(
    name: str,
    passed: bool,
    failures: list[dict[str, Any]],
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "name": name,
        "passed": passed,
        "failure_categories": sorted(
            {
                str(failure.get("failure_category") or "")
                for failure in failures
                if failure.get("failure_category")
            }
        ),
        "failures": failures,
        "details": details,
    }


def _failure(
    failure_category: str,
    *,
    candidate_authority_id: str | None = None,
    artifact: str | None = None,
    path: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "failure_category": failure_category,
        "candidate_authority_id": candidate_authority_id,
        "artifact": artifact,
        "path": path,
        "details": details or {},
    }


def _read_json_if_exists(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return value


def _read_required_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object for {label}: {path}")
    return value


def _read_jsonl_if_exists(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _read_required_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    return _read_jsonl_if_exists(path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl_and_hash(path: Path, records: list[dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    return sha256_file(path)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _optional_file_sha256(path: Path | None) -> str | None:
    return sha256_file(path) if path is not None and path.exists() else None


def _stable_id(*parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return f"{parts[0]}:{digest[:16]}"


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item or "").strip()]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []


def _validate_safe_segment(value: str | None, label: str) -> None:
    if not value or not SAFE_SEGMENT_RE.fullmatch(value):
        raise ValueError(f"{label} must contain only letters, numbers, dot, underscore, or hyphen.")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
