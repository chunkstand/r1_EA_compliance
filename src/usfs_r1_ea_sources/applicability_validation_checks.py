from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .applicability_adjudication import APPLICABILITY_ADJUDICATION_EVAL_SCHEMA_VERSION
from .applicability_adjudication import _matching_adjudication_item_result
from .applicability_validation_support import candidate_ids_from_records
from .applicability_validation_support import check
from .applicability_validation_support import decision_status
from .applicability_validation_support import failure
from .applicability_validation_support import first_present
from .applicability_validation_support import read_json_if_exists
from .applicability_validation_support import records_by_key
from .applicability_validation_support import string_list


UNRESOLVED_STATUSES = {"unresolved", "needs_adjudication"}
FINAL_STATUSES = {"applicable", "not_applicable"}


def build_validation_checks(
    *,
    review_id: str,
    source_set_id: str | None,
    paths: dict[str, Path],
    artifacts: dict[str, Any],
) -> list[dict[str, Any]]:
    candidates = artifacts["authority_universe"].get("candidate_authorities") or []
    decisions = artifacts["decisions"]
    applicable_ids = {
        str(row.get("candidate_authority_id") or "")
        for row in artifacts["applicable_authorities"].get("authorities") or []
        if isinstance(row, dict) and row.get("candidate_authority_id")
    }
    non_applicable_ids = {
        str(row.get("candidate_authority_id") or "")
        for row in artifacts["non_applicable_authorities"].get("authorities") or []
        if isinstance(row, dict) and row.get("candidate_authority_id")
    }
    retrieval_by_id = records_by_key(artifacts["retrieval_rows"], "retrieval_trace_id")
    graph_by_id = records_by_key(artifacts["graph_rows"], "graph_path_id")
    certificates_by_id = {
        str(row.get("coverage_certificate_id") or ""): row
        for row in artifacts["search_coverage_certificates"].get("certificates") or []
        if isinstance(row, dict) and row.get("coverage_certificate_id")
    }
    return [
        check_required_artifacts(paths),
        check_review_and_source_identity(
            review_id=review_id,
            source_set_id=source_set_id,
            artifacts=artifacts,
        ),
        check_package_fact_graph_validation(paths=paths, artifacts=artifacts),
        check_selected_action_validation(paths=paths, artifacts=artifacts),
        check_candidate_decisions(candidates, decisions),
        check_partition(
            candidates=candidates,
            decisions=decisions,
            applicable_ids=applicable_ids,
            non_applicable_ids=non_applicable_ids,
        ),
        check_no_unresolved(decisions),
        check_applicable_evidence(decisions),
        check_non_applicable_basis(decisions, certificates_by_id),
        check_retrieval_traceability(decisions, retrieval_by_id),
        check_graph_traceability(decisions, graph_by_id),
        check_forest_plan_scope(decisions),
        check_contradictory_package_evidence(decisions),
        check_human_adjudication_replay(decisions),
    ]


def check_required_artifacts(paths: dict[str, Path]) -> dict[str, Any]:
    missing = [
        {"artifact": name, "path": str(path)}
        for name, path in paths.items()
        if not path.exists()
    ]
    return check(
        "required_applicability_artifacts_exist",
        not missing,
        [
            failure(
                "missing_applicability_artifact",
                artifact=entry["artifact"],
                path=entry["path"],
            )
            for entry in missing
        ],
        {"missing": missing},
    )


def check_review_and_source_identity(
    *,
    review_id: str,
    source_set_id: str | None,
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    failures = []
    for artifact_name in (
        "authority_universe",
        "selected_action",
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
                failure(
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
                failure(
                    "source_set_stale",
                    artifact=artifact_name,
                    details={
                        "field": "source_set_id",
                        "expected": source_set_id,
                        "actual": artifact.get("source_set_id"),
                    },
                )
            )
    return check(
        "review_and_source_set_identity_match",
        not failures,
        failures,
        {"review_id": review_id, "source_set_id": source_set_id},
    )


def check_package_fact_graph_validation(
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
        "package_manifest_sha256": first_present(
            artifacts["package_applicability_context"].get("package_manifest_sha256"),
            artifacts["package_fact_graph"].get("package_manifest_sha256"),
        ),
        "package_chunks_sha256": first_present(
            artifacts["package_applicability_context"].get("package_chunks_sha256"),
            artifacts["package_fact_graph"].get("package_chunks_sha256"),
        ),
        "package_fact_graph_sha256": artifacts["package_fact_graph"].get(
            "package_fact_graph_sha256"
        ),
        "package_context_sha256": artifacts["package_applicability_context"].get(
            "package_context_sha256"
        ),
        "selected_action_sha256": first_present(
            artifacts["selected_action"].get("selected_action_sha256"),
            artifacts["package_applicability_context"].get("selected_action_sha256"),
            artifacts["package_fact_graph"].get("selected_action_sha256"),
        ),
    }
    failures = []
    if not paths["package_fact_graph_validation"].exists():
        failures.append(
            failure(
                "missing_applicability_artifact",
                artifact="package_fact_graph_validation",
                path=str(paths["package_fact_graph_validation"]),
            )
        )
    elif validation.get("schema_version") != "package-fact-graph-validation-v0":
        failures.append(
            failure(
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
            failure(
                "package_cache_stale",
                artifact="package_fact_graph_validation",
                details={"field": "validation.passed", "actual": False},
            )
        )
    for field, expected in expected_pairs.items():
        actual = validation.get(field)
        if expected and actual and actual != expected:
            failures.append(
                failure(
                    "package_cache_stale",
                    artifact="package_fact_graph_validation",
                    details={"field": field, "expected": expected, "actual": actual},
                )
            )
    return check(
        "package_fact_graph_validation_passes_current_artifacts",
        not failures,
        failures,
        {"path": str(paths["package_fact_graph_validation"])},
    )


def check_selected_action_validation(
    *,
    paths: dict[str, Path],
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    selected_action = artifacts["selected_action"]
    validation = artifacts["selected_action_validation"]
    nested_validation = (
        validation.get("validation")
        if isinstance(validation.get("validation"), dict)
        else {}
    )
    selected_action_sha256 = first_present(
        selected_action.get("selected_action_sha256"),
        artifacts["package_applicability_context"].get("selected_action_sha256"),
        artifacts["package_fact_graph"].get("selected_action_sha256"),
    )
    expected_pairs = {
        "package_manifest_sha256": first_present(
            artifacts["package_applicability_context"].get("package_manifest_sha256"),
            artifacts["package_fact_graph"].get("package_manifest_sha256"),
        ),
        "package_chunks_sha256": first_present(
            artifacts["package_applicability_context"].get("package_chunks_sha256"),
            artifacts["package_fact_graph"].get("package_chunks_sha256"),
        ),
        "selected_action_sha256": selected_action_sha256,
    }
    failures = []
    if not paths["selected_action"].exists():
        failures.append(
            failure(
                "missing_applicability_artifact",
                artifact="selected_action",
                path=str(paths["selected_action"]),
            )
        )
    elif selected_action.get("schema_version") != "selected-action-v0":
        failures.append(
            failure(
                "package_cache_stale",
                artifact="selected_action",
                details={
                    "field": "schema_version",
                    "actual": selected_action.get("schema_version"),
                },
            )
        )
    if not paths["selected_action_validation"].exists():
        failures.append(
            failure(
                "missing_applicability_artifact",
                artifact="selected_action_validation",
                path=str(paths["selected_action_validation"]),
            )
        )
    elif validation.get("schema_version") != "selected-action-validation-v0":
        failures.append(
            failure(
                "package_cache_stale",
                artifact="selected_action_validation",
                details={
                    "field": "schema_version",
                    "actual": validation.get("schema_version"),
                },
            )
        )
    elif not nested_validation.get("passed"):
        failures.append(
            failure(
                "package_cache_stale",
                artifact="selected_action_validation",
                details={
                    "field": "validation.passed",
                    "actual": nested_validation.get("passed"),
                },
            )
        )
    for field, expected in expected_pairs.items():
        actual = validation.get(field)
        if expected and actual and actual != expected:
            failures.append(
                failure(
                    "package_cache_stale",
                    artifact="selected_action_validation",
                    details={"field": field, "expected": expected, "actual": actual},
                )
            )
    return check(
        "selected_action_validation_passes_current_artifacts",
        not failures,
        failures,
        {"path": str(paths["selected_action_validation"])},
    )


def check_candidate_decisions(
    candidates: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_values = candidate_ids_from_records(candidates)
    decision_ids = [str(row.get("candidate_authority_id") or "") for row in decisions]
    decision_counts = Counter(decision_ids)
    missing = sorted(candidate_values - set(decision_ids))
    duplicates = sorted(
        candidate_id for candidate_id, count in decision_counts.items() if count > 1
    )
    unexpected = sorted(set(decision_ids) - candidate_values)
    failures = [
        *[
            failure("missing_candidate_decision", candidate_authority_id=candidate_id)
            for candidate_id in missing
        ],
        *[
            failure("duplicate_decision", candidate_authority_id=candidate_id)
            for candidate_id in duplicates
        ],
        *[
            failure("partition_gap", candidate_authority_id=candidate_id)
            for candidate_id in unexpected
        ],
    ]
    return check(
        "candidate_universe_has_exactly_one_decision",
        not failures and bool(candidate_values),
        failures,
        {
            "candidate_authority_count": len(candidate_values),
            "decision_count": len(decisions),
            "missing_candidate_authority_ids": missing,
            "duplicate_candidate_authority_ids": duplicates,
            "unexpected_candidate_authority_ids": unexpected,
        },
    )


def check_partition(
    *,
    candidates: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    applicable_ids: set[str],
    non_applicable_ids: set[str],
) -> dict[str, Any]:
    candidate_values = candidate_ids_from_records(candidates)
    overlap = sorted(applicable_ids & non_applicable_ids)
    decision_ids_by_status = defaultdict(set)
    for decision in decisions:
        decision_ids_by_status[decision_status(decision)].add(
            str(decision.get("candidate_authority_id") or "")
        )
    final_ids = decision_ids_by_status["applicable"] | decision_ids_by_status["not_applicable"]
    partition_values = applicable_ids | non_applicable_ids
    missing_final = sorted(final_ids - partition_values)
    partition_extra = sorted(partition_values - final_ids)
    unresolved_ids = sorted(candidate_values - partition_values)
    failures = [
        *[
            failure("partition_overlap", candidate_authority_id=candidate_id)
            for candidate_id in overlap
        ],
        *[
            failure("partition_gap", candidate_authority_id=candidate_id)
            for candidate_id in missing_final
        ],
        *[
            failure("partition_gap", candidate_authority_id=candidate_id)
            for candidate_id in partition_extra
        ],
        *[
            failure("unresolved_authority", candidate_authority_id=candidate_id)
            for candidate_id in unresolved_ids
        ],
    ]
    return check(
        "applicable_and_non_applicable_partition_candidate_universe",
        not failures and bool(candidate_values),
        failures,
        {
            "candidate_authority_count": len(candidate_values),
            "applicable_partition_count": len(applicable_ids),
            "non_applicable_partition_count": len(non_applicable_ids),
            "overlap": overlap,
            "missing_final": missing_final,
            "partition_extra": partition_extra,
            "unresolved_or_unpartitioned": unresolved_ids,
        },
    )


def check_no_unresolved(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    unresolved = [
        str(decision.get("candidate_authority_id") or "")
        for decision in decisions
        if decision_status(decision) in UNRESOLVED_STATUSES
    ]
    return check(
        "no_unresolved_or_needs_adjudication_decisions",
        not unresolved,
        [
            failure("unresolved_authority", candidate_authority_id=candidate_id)
            for candidate_id in unresolved
        ],
        {"unresolved_candidate_authority_ids": unresolved},
    )


def check_applicable_evidence(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    failures = []
    for decision in decisions:
        if decision_status(decision) != "applicable":
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
                failure(
                    "applicable_evidence_gap",
                    candidate_authority_id=str(
                        decision.get("candidate_authority_id") or ""
                    ),
                )
            )
    return check(
        "applicable_decisions_have_required_basis",
        not failures,
        failures,
        {"failure_count": len(failures)},
    )


def check_non_applicable_basis(
    decisions: list[dict[str, Any]],
    certificates_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    failures = []
    for decision in decisions:
        if decision_status(decision) != "not_applicable":
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
                failure(
                    "non_applicable_basis_gap",
                    candidate_authority_id=str(
                        decision.get("candidate_authority_id") or ""
                    ),
                )
            )
        if not (has_adjudication or sufficient_cert):
            failures.append(
                failure(
                    "search_coverage_gap",
                    candidate_authority_id=str(
                        decision.get("candidate_authority_id") or ""
                    ),
                )
            )
    return check(
        "non_applicable_decisions_have_basis_or_adjudication",
        not failures,
        failures,
        {"failure_count": len(failures)},
    )


def check_retrieval_traceability(
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
                failure(
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
            if not retrieval_trace_row_valid(row):
                failures.append(
                    failure(
                        "retrieval_trace_gap",
                        candidate_authority_id=str(
                            decision.get("candidate_authority_id") or ""
                        ),
                        details={"retrieval_trace_id": trace_id},
                    )
                )
    return check(
        "retrieval_backed_decisions_have_trace_rows",
        not failures,
        failures,
        {"failure_count": len(failures)},
    )


def check_graph_traceability(
    decisions: list[dict[str, Any]],
    graph_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    failures = []
    for decision in decisions:
        graph_path_ids = [str(value) for value in decision.get("graph_path_ids") or []]
        for graph_path_id in graph_path_ids:
            row = graph_by_id.get(graph_path_id)
            if not graph_trace_row_valid(row):
                failures.append(
                    failure(
                        "graph_trace_gap",
                        candidate_authority_id=str(
                            decision.get("candidate_authority_id") or ""
                        ),
                        details={"graph_path_id": graph_path_id},
                    )
                )
    return check(
        "graph_supported_decisions_have_path_rows",
        not failures,
        failures,
        {"failure_count": len(failures)},
    )


def check_forest_plan_scope(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    failures = []
    for decision in decisions:
        if decision.get("candidate_authority_type") != "forest_plan_component":
            continue
        if decision_status(decision) in UNRESOLVED_STATUSES:
            failures.append(
                failure(
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
                failure(
                    "forest_plan_scope_unresolved",
                    candidate_authority_id=str(
                        decision.get("candidate_authority_id") or ""
                    ),
                )
            )
    return check(
        "forest_plan_component_decisions_have_scope_context",
        not failures,
        failures,
        {"failure_count": len(failures)},
    )


def check_contradictory_package_evidence(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    failures = []
    for decision in decisions:
        if decision_status(decision) not in FINAL_STATUSES:
            continue
        has_positive = bool(decision.get("package_evidence_spans"))
        has_negative = bool(decision.get("negative_evidence_spans"))
        has_contradiction_notes = bool(decision.get("contradiction_notes"))
        has_adjudication = bool(decision.get("human_adjudication_refs"))
        resolved_by_arbitration = _resolved_by_positive_precedence(decision)
        if (
            has_contradiction_notes or (has_positive and has_negative)
        ) and not has_adjudication and not resolved_by_arbitration:
            failures.append(
                failure(
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
    return check(
        "contradictory_package_evidence_requires_adjudication",
        not failures,
        failures,
        {"failure_count": len(failures)},
    )


def _resolved_by_positive_precedence(decision: dict[str, Any]) -> bool:
    summary = decision.get("arbitration_summary")
    if not isinstance(summary, dict):
        return False
    return (
        summary.get("decision_effect") == "positive_precedence_over_negative_trigger"
        and ((summary.get("contract") or {}).get("positive_negative_conflict_policy"))
        == "positive_precedence"
    )


def check_human_adjudication_replay(decisions: list[dict[str, Any]]) -> dict[str, Any]:
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
                failure(
                    "adjudication_missing",
                    candidate_authority_id=candidate_id,
                    details={"reason": "human_adjudication_basis_without_reference"},
                )
            )
            continue
        for ref in refs:
            failures.extend(
                adjudication_ref_failures(
                    decision=decision,
                    ref=ref,
                    eval_cache=eval_cache,
                )
            )
    return check(
        "human_adjudication_references_are_replayable",
        not failures,
        failures,
        {"failure_count": len(failures)},
    )


def adjudication_ref_failures(
    *,
    decision: dict[str, Any],
    ref: dict[str, Any],
    eval_cache: dict[Path, dict[str, Any]],
) -> list[dict[str, Any]]:
    failures = []
    candidate_id = str(decision.get("candidate_authority_id") or "")
    current_status = decision_status(decision)
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
    if not string_list(ref.get("adjudicated_by")):
        missing_fields.append("adjudicated_by")
    if not string_list(ref.get("supporting_citation_refs")):
        missing_fields.append("supporting_citation_refs")
    if missing_fields:
        failures.append(
            failure(
                "adjudication_missing",
                candidate_authority_id=candidate_id,
                details={"reason": "adjudication_reference_incomplete", "fields": missing_fields},
            )
        )
    if ref.get("decision_id") != decision.get("decision_id"):
        failures.append(
            failure(
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
            failure(
                "adjudication_missing",
                candidate_authority_id=candidate_id,
                details={
                    "field": "candidate_authority_id",
                    "expected": decision.get("candidate_authority_id"),
                    "actual": ref.get("candidate_authority_id"),
                },
            )
        )
    if ref.get("final_status") != current_status:
        failures.append(
            failure(
                "adjudication_missing",
                candidate_authority_id=candidate_id,
                details={
                    "field": "final_status",
                    "expected": current_status,
                    "actual": ref.get("final_status"),
                },
            )
        )
    expected_disposition = (
        "human_applicable" if current_status == "applicable" else "human_not_applicable"
    )
    if current_status in FINAL_STATUSES and ref.get("disposition") != expected_disposition:
        failures.append(
            failure(
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
            failure(
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
            failure(
                "adjudication_missing",
                candidate_authority_id=candidate_id,
                path=eval_path_text,
                details={"reason": "adjudication_eval_missing"},
            )
        )
        return failures
    eval_payload = eval_cache.get(eval_path)
    if eval_payload is None:
        eval_payload = read_json_if_exists(eval_path)
        eval_cache[eval_path] = eval_payload
    if eval_payload.get("schema_version") != APPLICABILITY_ADJUDICATION_EVAL_SCHEMA_VERSION:
        failures.append(
            failure(
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
            failure(
                "adjudication_missing",
                candidate_authority_id=candidate_id,
                path=eval_path_text,
                details={"field": "summary.passed", "actual": summary.get("passed")},
            )
        )
    item_result = _matching_adjudication_item_result(eval_payload, ref)
    if not item_result or not item_result.get("passed"):
        failures.append(
            failure(
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


def retrieval_trace_row_valid(row: dict[str, Any] | None) -> bool:
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


def graph_trace_row_valid(row: dict[str, Any] | None) -> bool:
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
