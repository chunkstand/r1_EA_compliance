from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .applicability_eval_trajectory import score_case_trajectory
from .applicability_eval_support import _read_json_if_exists
from .applicability_eval_support import _read_jsonl_if_exists
from .applicability_eval_support import _string_list_mapping
from .applicability_eval_support import _string_mapping
from .applicability_eval_support import _strings
from .records import sha256_file


def _read_case_artifacts(applicability_dir: Path) -> dict[str, Any]:
    return {
        "authority_universe": _read_json_if_exists(
            applicability_dir / "authority_universe_snapshot.json"
        ),
        "package_fact_graph": _read_json_if_exists(
            applicability_dir / "package_fact_graph.json"
        ),
        "applicability_validation": _read_json_if_exists(
            applicability_dir / "applicability_validation.json"
        ),
        "decisions": _read_jsonl_if_exists(applicability_dir / "applicability_decisions.jsonl"),
        "retrieval_rows": _read_jsonl_if_exists(
            applicability_dir / "applicability_retrieval_trace.jsonl"
        ),
        "graph_rows": _read_jsonl_if_exists(
            applicability_dir / "applicability_graph_trace.jsonl"
        ),
        "applicable_authorities": _read_json_if_exists(
            applicability_dir / "applicable_authorities.json"
        ),
        "non_applicable_authorities": _read_json_if_exists(
            applicability_dir / "non_applicable_authorities.json"
        ),
        "search_coverage_certificates": _read_json_if_exists(
            applicability_dir / "search_coverage_certificates.json"
        ),
        "applicability_gate_graph": _read_json_if_exists(
            applicability_dir / "applicability_gate_graph.json"
        ),
        "applicability_gate_graph_summary": _read_json_if_exists(
            applicability_dir / "applicability_gate_graph_summary.json"
        ),
        "applicability_gate_graph_validation": _read_json_if_exists(
            applicability_dir / "applicability_gate_graph_validation.json"
        ),
        "generated_rule_pack": _read_json_if_exists(
            applicability_dir / "generated_rule_pack.json"
        ),
        "generated_validation": _read_json_if_exists(
            applicability_dir / "generated_rule_pack_validation.json"
        ),
        "applicability_adjudication_template": _read_json_if_exists(
            applicability_dir / "applicability_adjudication_template.json"
        ),
        "applicability_adjudication_eval": _read_json_if_exists(
            applicability_dir / "applicability_adjudication_eval.json"
        ),
        "applicability_adjudication_apply": _read_json_if_exists(
            applicability_dir / "applicability_adjudication_apply.json"
        ),
    }


def _score_case(
    *,
    case: dict[str, Any],
    case_id: str,
    review_id: str,
    source_set_id: str,
    review_dir: Path,
    retrieval_index_path: Path,
    adjudication_summary: dict[str, Any] | None = None,
    validation_summary: dict[str, Any],
    generated_summary: dict[str, Any] | None,
    generated_error: str | None,
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    decisions = artifacts["decisions"]
    generated_rule_pack = artifacts["generated_rule_pack"]
    generated_validation = artifacts["generated_validation"]
    applicable = artifacts["applicable_authorities"]
    non_applicable = artifacts["non_applicable_authorities"]
    coverage = artifacts["search_coverage_certificates"]
    gate_graph = artifacts["applicability_gate_graph"]
    gate_graph_summary = artifacts["applicability_gate_graph_summary"]
    gate_graph_validation = artifacts["applicability_gate_graph_validation"]
    generated_validation_summary = (
        generated_validation.get("summary")
        if isinstance(generated_validation.get("summary"), dict)
        else {}
    )
    package_fact_graph = artifacts["package_fact_graph"]
    retrieval_rows = artifacts["retrieval_rows"]
    graph_rows = artifacts["graph_rows"]
    decisions_by_rule = _decisions_by_rule_id(decisions)
    actual_statuses = {
        rule_id: decision.get("status")
        for rule_id, decision in sorted(decisions_by_rule.items())
    }
    expected_statuses = {
        str(rule_id): str(status)
        for rule_id, status in (case.get("expected_statuses") or {}).items()
    }
    default_family_status = str(
        case.get("expected_status_for_candidate_authority_family_rule_ids") or ""
    ).strip()
    if default_family_status:
        for rule_id in _strings(case.get("candidate_authority_family_rule_ids")):
            expected_statuses.setdefault(rule_id, default_family_status)
    status_mismatches = [
        {
            "rule_id": rule_id,
            "expected": expected,
            "actual": actual_statuses.get(rule_id),
        }
        for rule_id, expected in sorted(expected_statuses.items())
        if actual_statuses.get(rule_id) != expected
    ]
    applicable_rule_ids = _partition_rule_ids(applicable)
    non_applicable_rule_ids = _partition_rule_ids(non_applicable)
    expected_applicable = sorted(_strings(case.get("expected_applicable_rule_ids")))
    expected_non_applicable = sorted(_strings(case.get("expected_non_applicable_rule_ids")))
    expected_applicable_specified = bool(case.get("expected_applicable_rule_ids")) or bool(
        expected_statuses
    )
    expected_non_applicable_specified = bool(
        case.get("expected_non_applicable_rule_ids")
    ) or bool(expected_statuses)
    if not expected_applicable and expected_statuses:
        expected_applicable = sorted(
            rule_id
            for rule_id, status in expected_statuses.items()
            if status == "applicable"
        )
    if not expected_non_applicable and expected_statuses:
        expected_non_applicable = sorted(
            rule_id
            for rule_id, status in expected_statuses.items()
            if status == "not_applicable"
        )
    expected_generated = sorted(_strings(case.get("expected_generated_rule_ids")))
    generated_rule_ids = sorted(
        str(rule.get("base_rule_id") or rule.get("id"))
        for rule in generated_rule_pack.get("rules") or []
        if isinstance(rule, dict)
    )
    if not expected_generated and generated_rule_pack:
        expected_generated = applicable_rule_ids
    expected_fact_types = sorted(_strings(case.get("expected_package_fact_types")))
    actual_fact_types = sorted(
        {
            str(node.get("node_type"))
            for node in package_fact_graph.get("nodes") or []
            if isinstance(node, dict) and node.get("node_type")
        }
    )
    expected_retrieval = sorted(_strings(case.get("expected_retrieval_rule_ids")))
    expected_graph = sorted(_strings(case.get("expected_graph_rule_ids")))
    expected_absent_graph = sorted(
        _strings(case.get("expected_absent_graph_rule_ids"))
        or _strings(case.get("expected_graph_non_path_rule_ids"))
    )
    expected_negative = sorted(_strings(case.get("expected_negative_evidence_rule_ids")))
    expected_trigger_miss = sorted(
        _strings(case.get("expected_trigger_miss_rule_ids"))
    )
    expected_source_records = _string_list_mapping(
        case.get("expected_source_record_ids_by_rule_id")
    )
    expected_document_roles = _string_list_mapping(
        case.get("expected_document_roles_by_rule_id")
    )
    expected_package_sections = _string_list_mapping(
        case.get("expected_package_section_families_by_rule_id")
    )
    expected_basis_types = _string_mapping(case.get("expected_basis_types_by_rule_id"))
    expected_arbitration_statuses = _string_mapping(
        case.get("expected_arbitration_statuses_by_rule_id")
    )
    expected_arbitration_effects = _string_mapping(
        case.get("expected_arbitration_decision_effects_by_rule_id")
    )
    coverage_ids = _coverage_certificate_ids(coverage)
    non_applicable_coverage_gaps = []
    for authority in non_applicable.get("authorities") or []:
        if not isinstance(authority, dict):
            non_applicable_coverage_gaps.append(
                {"rule_id": None, "reason": "invalid_authority"}
            )
            continue
        cert_ids = _strings(authority.get("search_coverage_certificate_ids"))
        missing = [cert_id for cert_id in cert_ids if cert_id not in coverage_ids]
        if not cert_ids or missing:
            non_applicable_coverage_gaps.append(
                {
                    "rule_id": _authority_rule_id(authority),
                    "search_coverage_certificate_ids": cert_ids,
                    "missing_certificate_ids": missing,
                }
            )
    expected_generated_ready = bool(
        case.get("expected_generated_rule_pack_ready", True)
    )
    generated_validation_passed = bool(
        generated_summary
        and generated_summary.get("passed")
        and generated_validation_summary.get("generated_rule_pack_ready") is True
    )
    required_artifact_gaps = _required_artifact_gaps(
        artifacts,
        generated_rule_pack_required=expected_generated_ready,
    )
    generated_rule_pack_hash_matches_validation = (
        not expected_generated_ready
        or _file_hash_matches(
            review_dir / "applicability" / "generated_rule_pack.json",
            str(
                generated_validation_summary.get(
                    "expected_generated_rule_pack_sha256"
                )
                or generated_validation_summary.get("generated_rule_pack_sha256")
                or ""
            ),
        )
    )
    expected_generated_count = case.get("expected_generated_rule_count")
    if expected_generated_count is not None:
        generated_count_matches = len(generated_rule_ids) == int(expected_generated_count)
    else:
        generated_count_matches = generated_rule_ids == applicable_rule_ids
    gate_graph_decision_mismatches = _gate_graph_decision_mismatches(
        decisions=decisions,
        gate_graph=gate_graph,
    )
    gate_graph_input_hash_gaps = _gate_graph_input_hash_gaps(gate_graph)
    gate_graph_identity_matches = (
        str(gate_graph.get("review_id") or "") == review_id
        and str(gate_graph.get("source_set_id") or "") == source_set_id
        and str(gate_graph_summary.get("contract_id") or "")
        == str(gate_graph.get("contract_id") or "")
    )
    gate_graph_validation_passed = (
        bool(gate_graph_validation.get("passed"))
        and bool(gate_graph_summary.get("passed"))
        and bool(gate_graph.get("validation", {}).get("passed"))
    )
    gate_graph_required = bool(case.get("expected_gate_graph_required"))
    result_flags = {
        "validation_passed_matches": bool(validation_summary.get("passed"))
        == bool(case.get("expected_validation_passed", True)),
        "expected_statuses_match": not status_mismatches,
        "expected_applicable_authorities_match": (
            not expected_applicable_specified or applicable_rule_ids == expected_applicable
        ),
        "expected_non_applicable_authorities_match": (
            not expected_non_applicable_specified
            or non_applicable_rule_ids == expected_non_applicable
        ),
        "package_fact_types_match": set(expected_fact_types).issubset(
            set(actual_fact_types)
        ),
        "retrieval_trace_coverage_matches": _rules_have_retrieval(
            expected_retrieval,
            retrieval_rows,
        ),
        "graph_trace_coverage_matches": _rules_have_graph(expected_graph, graph_rows),
        "graph_non_path_matches": _rules_lack_graph(expected_absent_graph, graph_rows),
        "source_record_alignment_matches": _rules_match_retrieval_source_records(
            expected_source_records,
            retrieval_rows,
        ),
        "document_role_alignment_matches": _rules_match_retrieval_document_roles(
            expected_document_roles,
            retrieval_rows,
        ),
        "package_section_alignment_matches": _rules_match_package_sections(
            expected_package_sections,
            decisions_by_rule,
        ),
        "basis_type_alignment_matches": _rules_match_basis_types(
            expected_basis_types,
            decisions_by_rule,
        ),
        "arbitration_status_alignment_matches": _rules_match_decision_values(
            expected_arbitration_statuses,
            decisions_by_rule,
            "arbitration_status",
        ),
        "arbitration_decision_effect_alignment_matches": _rules_match_decision_values(
            expected_arbitration_effects,
            decisions_by_rule,
            "arbitration_summary.decision_effect",
        ),
        "negative_evidence_matches": _rules_have_decision_field(
            expected_negative,
            decisions_by_rule,
            "negative_evidence_spans",
        ),
        "trigger_miss_evidence_matches": _rules_have_decision_field(
            expected_trigger_miss,
            decisions_by_rule,
            "explicit_trigger_miss_evidence",
        ),
        "non_applicable_coverage_supported": not non_applicable_coverage_gaps,
        "required_applicability_artifacts_present": not required_artifact_gaps,
        "generated_rule_pack_ready_matches": generated_validation_passed
        == expected_generated_ready,
        "generated_rule_pack_matches_applicability": (
            generated_rule_ids == expected_generated
            and generated_count_matches
            and generated_rule_ids == applicable_rule_ids
        ),
        "generated_rule_pack_hash_matches_validation": (
            generated_rule_pack_hash_matches_validation
        ),
    }
    if gate_graph_required:
        result_flags.update(
            {
                "gate_graph_validation_passed": gate_graph_validation_passed,
                "gate_graph_identity_matches": gate_graph_identity_matches,
                "gate_graph_input_hashes_match": not gate_graph_input_hash_gaps,
                "gate_graph_consistency_matches": not gate_graph_decision_mismatches,
            }
        )
    trajectory_process_quality = score_case_trajectory(
        review_dir=review_dir,
        retrieval_index_path=retrieval_index_path,
        artifacts=artifacts,
        validation_summary=validation_summary,
        generated_summary=generated_summary,
        generated_error=generated_error,
        expected_generated_ready=expected_generated_ready,
    )
    result_flags["trajectory_process_quality_matches"] = bool(
        trajectory_process_quality.get("passed")
    )
    failure_reasons = [name for name, passed in result_flags.items() if not passed]
    failure_taxonomy = _failure_taxonomy(
        result_flags=result_flags,
        status_mismatches=status_mismatches,
        non_applicable_coverage_gaps=non_applicable_coverage_gaps,
        gate_graph_decision_mismatches=gate_graph_decision_mismatches,
        gate_graph_input_hash_gaps=gate_graph_input_hash_gaps,
        gate_graph_identity={
            "expected_review_id": review_id,
            "actual_review_id": gate_graph.get("review_id"),
            "expected_source_set_id": source_set_id,
            "actual_source_set_id": gate_graph.get("source_set_id"),
            "summary_contract_id": gate_graph_summary.get("contract_id"),
            "graph_contract_id": gate_graph.get("contract_id"),
        },
        gate_graph_validation={
            "summary_passed": gate_graph_summary.get("passed"),
            "validation_passed": gate_graph_validation.get("passed"),
            "graph_validation_passed": gate_graph.get("validation", {}).get("passed"),
        },
        trajectory_process_quality=trajectory_process_quality,
        generated_error=generated_error,
    )
    return {
        "id": case_id,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "profile": case.get("profile"),
        "coverage_tags": sorted(_strings(case.get("coverage_tags"))),
        "review_dir": str(review_dir),
        "retrieval_index_path": str(retrieval_index_path),
        "applicability_dir": str(review_dir / "applicability"),
        "authority_universe_path": str(
            review_dir / "applicability" / "authority_universe_snapshot.json"
        ),
        "package_fact_graph_path": str(
            review_dir / "applicability" / "package_fact_graph.json"
        ),
        "retrieval_trace_path": str(
            review_dir / "applicability" / "applicability_retrieval_trace.jsonl"
        ),
        "graph_trace_path": str(
            review_dir / "applicability" / "applicability_graph_trace.jsonl"
        ),
        "applicability_validation_path": str(
            review_dir / "applicability" / "applicability_validation.json"
        ),
        "gate_graph_path": str(
            review_dir / "applicability" / "applicability_gate_graph.json"
        ),
        "gate_graph_summary_path": str(
            review_dir / "applicability" / "applicability_gate_graph_summary.json"
        ),
        "gate_graph_validation_path": str(
            review_dir / "applicability" / "applicability_gate_graph_validation.json"
        ),
        "generated_rule_pack_path": str(
            review_dir / "applicability" / "generated_rule_pack.json"
        ),
        "candidate_authority_count": len(
            artifacts["authority_universe"].get("candidate_authorities") or []
        ),
        "decision_count": len(decisions),
        "retrieval_trace_row_count": len(retrieval_rows),
        "graph_trace_row_count": len(graph_rows),
        "gate_graph_contract_id": gate_graph.get("contract_id"),
        "gate_graph_node_count": gate_graph_summary.get("node_count", 0),
        "gate_graph_edge_count": gate_graph_summary.get("edge_count", 0),
        "forest_plan_component_gate_count": gate_graph_summary.get(
            "forest_plan_component_gate_count",
            0,
        ),
        "forest_plan_instance_gate_count": gate_graph_summary.get(
            "forest_plan_instance_gate_count",
            0,
        ),
        "gate_graph_decision_mismatches": gate_graph_decision_mismatches,
        "gate_graph_input_hash_gaps": gate_graph_input_hash_gaps,
        "gate_graph_required": gate_graph_required,
        "gate_graph_validation_passed": gate_graph_validation_passed,
        "gate_graph_identity_matches": gate_graph_identity_matches,
        "gate_graph_input_hashes_match": not gate_graph_input_hash_gaps,
        "gate_graph_consistency_matches": not gate_graph_decision_mismatches,
        "actual_statuses": actual_statuses,
        "expected_statuses": expected_statuses,
        "status_mismatches": status_mismatches,
        "applicable_rule_ids": applicable_rule_ids,
        "non_applicable_rule_ids": non_applicable_rule_ids,
        "generated_rule_ids": generated_rule_ids,
        "expected_generated_rule_ids": expected_generated,
        "package_fact_types": actual_fact_types,
        "expected_package_fact_types": expected_fact_types,
        "expected_absent_graph_rule_ids": expected_absent_graph,
        "expected_source_record_ids_by_rule_id": expected_source_records,
        "expected_document_roles_by_rule_id": expected_document_roles,
        "expected_package_section_families_by_rule_id": expected_package_sections,
        "expected_basis_types_by_rule_id": expected_basis_types,
        "expected_arbitration_statuses_by_rule_id": expected_arbitration_statuses,
        "expected_arbitration_decision_effects_by_rule_id": expected_arbitration_effects,
        "basis_types_by_rule_id": _basis_types_by_rule_id(decisions_by_rule),
        "arbitration_statuses_by_rule_id": _decision_values_by_rule_id(
            decisions_by_rule,
            "arbitration_status",
        ),
        "arbitration_decision_effects_by_rule_id": _decision_values_by_rule_id(
            decisions_by_rule,
            "arbitration_summary.decision_effect",
        ),
        "arbitration_summary": _case_arbitration_summary(decisions),
        "authority_family_ids_by_rule_id": _authority_family_ids_by_rule_id(
            decisions_by_rule
        ),
        "adjudicated_rule_ids": _adjudicated_rule_ids(decisions_by_rule),
        "adjudication_summary": adjudication_summary,
        "required_artifact_gaps": required_artifact_gaps,
        "non_applicable_coverage_gaps": non_applicable_coverage_gaps,
        "generated_error": generated_error,
        "generated_rule_pack_ready": generated_validation_passed,
        "trajectory_process_quality": trajectory_process_quality,
        "trajectory_process_quality_passed": trajectory_process_quality.get("passed"),
        "validation_passed": bool(validation_summary.get("passed")),
        **result_flags,
        "failure_reasons": failure_reasons,
        "failure_taxonomy": failure_taxonomy,
        "failure_category_counts": dict(
            Counter(item["category"] for item in failure_taxonomy)
        ),
        "passed": not failure_reasons,
    }


def _decisions_by_rule_id(decisions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result = {}
    for decision in decisions:
        rule_id = _decision_rule_id(decision)
        if rule_id:
            result[rule_id] = decision
    return result


def _decision_rule_id(decision: dict[str, Any]) -> str:
    rule_template = decision.get("rule_template")
    if isinstance(rule_template, dict) and rule_template.get("rule_id"):
        return str(rule_template["rule_id"])
    candidate_id = str(decision.get("candidate_authority_id") or "")
    return candidate_id.rsplit(":", 1)[-1] if candidate_id else ""


def _authority_rule_id(authority: dict[str, Any]) -> str:
    rule_template = authority.get("rule_template")
    if isinstance(rule_template, dict) and rule_template.get("rule_id"):
        return str(rule_template["rule_id"])
    candidate_id = str(authority.get("candidate_authority_id") or "")
    return candidate_id.rsplit(":", 1)[-1] if candidate_id else ""


def _partition_rule_ids(payload: dict[str, Any]) -> list[str]:
    return sorted(
        _authority_rule_id(authority)
        for authority in payload.get("authorities") or []
        if isinstance(authority, dict) and _authority_rule_id(authority)
    )


def _rules_have_retrieval(rule_ids: list[str], rows: list[dict[str, Any]]) -> bool:
    if not rule_ids:
        return True
    candidate_ids = {
        str(row.get("candidate_authority_id") or "")
        for row in rows
        if row.get("candidate_authority_id")
    }
    return all(
        any(candidate_id.endswith(f":{rule_id}") for candidate_id in candidate_ids)
        for rule_id in rule_ids
    )


def _rules_have_graph(rule_ids: list[str], rows: list[dict[str, Any]]) -> bool:
    if not rule_ids:
        return True
    candidate_ids = {
        str(row.get("candidate_authority_id") or "")
        for row in rows
        if row.get("candidate_authority_id")
    }
    return all(
        any(candidate_id.endswith(f":{rule_id}") for candidate_id in candidate_ids)
        for rule_id in rule_ids
    )


def _rules_lack_graph(rule_ids: list[str], rows: list[dict[str, Any]]) -> bool:
    if not rule_ids:
        return True
    candidate_ids = {
        str(row.get("candidate_authority_id") or "")
        for row in rows
        if row.get("candidate_authority_id")
    }
    return all(
        not any(candidate_id.endswith(f":{rule_id}") for candidate_id in candidate_ids)
        for rule_id in rule_ids
    )


def _rules_match_retrieval_source_records(
    expected_by_rule: dict[str, list[str]],
    rows: list[dict[str, Any]],
) -> bool:
    if not expected_by_rule:
        return True
    actual = _retrieval_source_record_ids_by_rule(rows)
    return all(
        set(expected).issubset(actual.get(rule_id, set()))
        for rule_id, expected in expected_by_rule.items()
    )


def _rules_match_retrieval_document_roles(
    expected_by_rule: dict[str, list[str]],
    rows: list[dict[str, Any]],
) -> bool:
    if not expected_by_rule:
        return True
    actual = _retrieval_document_roles_by_rule(rows)
    return all(
        set(expected).issubset(actual.get(rule_id, set()))
        for rule_id, expected in expected_by_rule.items()
    )


def _rules_match_package_sections(
    expected_by_rule: dict[str, list[str]],
    decisions_by_rule: dict[str, dict[str, Any]],
) -> bool:
    if not expected_by_rule:
        return True
    actual = {
        rule_id: _decision_package_section_families(decision)
        for rule_id, decision in decisions_by_rule.items()
    }
    return all(
        set(expected).issubset(actual.get(rule_id, set()))
        for rule_id, expected in expected_by_rule.items()
    )


def _rules_match_basis_types(
    expected_by_rule: dict[str, str],
    decisions_by_rule: dict[str, dict[str, Any]],
) -> bool:
    if not expected_by_rule:
        return True
    return all(
        str((decisions_by_rule.get(rule_id) or {}).get("basis_type") or "") == expected
        for rule_id, expected in expected_by_rule.items()
    )


def _rules_match_decision_values(
    expected_by_rule: dict[str, str],
    decisions_by_rule: dict[str, dict[str, Any]],
    dotted_field: str,
) -> bool:
    if not expected_by_rule:
        return True
    return all(
        _decision_dotted_value(decisions_by_rule.get(rule_id) or {}, dotted_field)
        == expected
        for rule_id, expected in expected_by_rule.items()
    )


def _basis_types_by_rule_id(
    decisions_by_rule: dict[str, dict[str, Any]],
) -> dict[str, str]:
    return {
        rule_id: str(decision.get("basis_type") or "")
        for rule_id, decision in sorted(decisions_by_rule.items())
    }


def _decision_values_by_rule_id(
    decisions_by_rule: dict[str, dict[str, Any]],
    dotted_field: str,
) -> dict[str, str]:
    return {
        rule_id: _decision_dotted_value(decision, dotted_field)
        for rule_id, decision in sorted(decisions_by_rule.items())
    }


def _decision_dotted_value(decision: dict[str, Any], dotted_field: str) -> str:
    current: Any = decision
    for part in dotted_field.split("."):
        if not isinstance(current, dict):
            return ""
        current = current.get(part)
    return str(current or "")


def _authority_family_ids_by_rule_id(
    decisions_by_rule: dict[str, dict[str, Any]],
) -> dict[str, str]:
    family_ids = {}
    for rule_id, decision in sorted(decisions_by_rule.items()):
        rule_template = decision.get("rule_template")
        if isinstance(rule_template, dict) and rule_template.get("authority_family_id"):
            family_ids[rule_id] = str(rule_template["authority_family_id"])
    return family_ids


def _adjudicated_rule_ids(decisions_by_rule: dict[str, dict[str, Any]]) -> list[str]:
    return sorted(
        rule_id
        for rule_id, decision in decisions_by_rule.items()
        if str(decision.get("basis_type") or "") == "human_adjudication"
        or bool(decision.get("human_adjudication_refs"))
    )


def _rules_have_decision_field(
    rule_ids: list[str],
    decisions_by_rule: dict[str, dict[str, Any]],
    field: str,
) -> bool:
    return all(
        bool((decisions_by_rule.get(rule_id) or {}).get(field)) for rule_id in rule_ids
    )


def _retrieval_source_record_ids_by_rule(
    rows: list[dict[str, Any]],
) -> dict[str, set[str]]:
    actual: dict[str, set[str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        rule_id = _rule_id_from_candidate_id(str(row.get("candidate_authority_id") or ""))
        if not rule_id:
            continue
        values = actual.setdefault(rule_id, set())
        values.update(_strings(row.get("source_record_filters")))
        source_filters = row.get("source_filters") if isinstance(row.get("source_filters"), dict) else {}
        values.update(_strings(source_filters.get("source_record_ids")))
        for result in row.get("ranked_results") or []:
            if isinstance(result, dict) and result.get("source_record_id"):
                values.add(str(result["source_record_id"]))
    return actual


def _retrieval_document_roles_by_rule(rows: list[dict[str, Any]]) -> dict[str, set[str]]:
    actual: dict[str, set[str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        rule_id = _rule_id_from_candidate_id(str(row.get("candidate_authority_id") or ""))
        if not rule_id:
            continue
        source_filters = row.get("source_filters") if isinstance(row.get("source_filters"), dict) else {}
        actual.setdefault(rule_id, set()).update(
            _strings(source_filters.get("document_roles"))
        )
    return actual


def _decision_package_section_families(decision: dict[str, Any]) -> set[str]:
    sections = set()
    for field in (
        "package_evidence_spans",
        "negative_evidence_spans",
        "explicit_trigger_miss_evidence",
    ):
        for span in decision.get(field) or []:
            if isinstance(span, dict) and span.get("section_family"):
                sections.add(str(span["section_family"]))
    return sections


def _rule_id_from_candidate_id(candidate_id: str) -> str:
    return candidate_id.rsplit(":", 1)[-1] if candidate_id else ""


def _gate_graph_decision_mismatches(
    *,
    decisions: list[dict[str, Any]],
    gate_graph: dict[str, Any],
) -> list[dict[str, Any]]:
    nodes_by_candidate_id = {
        str(node.get("candidate_authority_id")): node
        for node in _dict_list(gate_graph.get("nodes"))
        if node.get("candidate_authority_id")
    }
    mismatches = []
    for decision in decisions:
        candidate_id = str(decision.get("candidate_authority_id") or "")
        if not candidate_id:
            continue
        node = nodes_by_candidate_id.get(candidate_id)
        expected_status, expected_activation = _expected_gate_state_for_decision(
            decision,
        )
        if not node:
            mismatches.append(
                {
                    "candidate_authority_id": candidate_id,
                    "expected_gate_status": expected_status,
                    "expected_activation_state": expected_activation,
                    "actual_gate_status": None,
                    "actual_activation_state": None,
                }
            )
            continue
        actual_status = str(node.get("gate_status") or "")
        actual_activation = str(node.get("activation_state") or "")
        if actual_status == expected_status and actual_activation == expected_activation:
            continue
        mismatches.append(
            {
                "candidate_authority_id": candidate_id,
                "expected_gate_status": expected_status,
                "expected_activation_state": expected_activation,
                "actual_gate_status": actual_status,
                "actual_activation_state": actual_activation,
                "gate_id": node.get("gate_id"),
            }
        )
    return mismatches


def _gate_graph_input_hash_gaps(gate_graph: dict[str, Any]) -> list[dict[str, Any]]:
    gaps = []
    for record in _dict_list(gate_graph.get("inputs")):
        name = str(record.get("name") or "")
        path_value = str(record.get("path") or "")
        expected_sha256 = str(record.get("sha256") or "")
        if not name or not path_value or not expected_sha256:
            gaps.append(
                {
                    "name": name or None,
                    "path": path_value or None,
                    "expected_sha256": expected_sha256 or None,
                    "actual_sha256": None,
                    "reason": "missing_input_hash_record",
                }
            )
            continue
        path = Path(path_value)
        actual_sha256 = sha256_file(path) if path.exists() else None
        if actual_sha256 != expected_sha256:
            gaps.append(
                {
                    "name": name,
                    "path": path_value,
                    "expected_sha256": expected_sha256,
                    "actual_sha256": actual_sha256,
                    "reason": "input_hash_mismatch" if actual_sha256 else "missing_input",
                }
            )
    return gaps


def _expected_gate_state_for_decision(decision: dict[str, Any]) -> tuple[str, str]:
    status = str(decision.get("status") or decision.get("applicability_status") or "")
    if status == "applicable":
        return "applicable", "open"
    if status == "not_applicable":
        return "not_applicable", "closed"
    if status in {"unresolved", "needs_adjudication"}:
        return status, "blocked"
    return "candidate", "pending"


def _dict_list(value: object) -> list[dict[str, Any]]:
    return [item for item in value or [] if isinstance(item, dict)]


def _coverage_certificate_ids(payload: dict[str, Any]) -> set[str]:
    return {
        str(
            certificate.get("coverage_certificate_id")
            or certificate.get("certificate_id")
            or ""
        )
        for certificate in payload.get("certificates") or []
        if isinstance(certificate, dict)
        and str(
            certificate.get("coverage_certificate_id")
            or certificate.get("certificate_id")
            or ""
        ).strip()
    }


def _required_artifact_gaps(
    artifacts: dict[str, Any],
    *,
    generated_rule_pack_required: bool,
) -> list[str]:
    required: dict[str, Any] = {
        "authority_universe": artifacts["authority_universe"],
        "package_fact_graph": artifacts["package_fact_graph"],
        "applicability_validation": artifacts["applicability_validation"],
        "applicability_decisions": artifacts["decisions"],
        "applicability_retrieval_trace": artifacts["retrieval_rows"],
        "applicability_graph_trace": artifacts["graph_rows"],
        "applicable_authorities": artifacts["applicable_authorities"],
        "non_applicable_authorities": artifacts["non_applicable_authorities"],
        "search_coverage_certificates": artifacts["search_coverage_certificates"],
        "applicability_gate_graph": artifacts["applicability_gate_graph"],
        "applicability_gate_graph_summary": artifacts["applicability_gate_graph_summary"],
        "applicability_gate_graph_validation": artifacts[
            "applicability_gate_graph_validation"
        ],
    }
    if generated_rule_pack_required:
        required["generated_rule_pack"] = artifacts["generated_rule_pack"]
        required["generated_rule_pack_validation"] = artifacts["generated_validation"]
    return sorted(name for name, value in required.items() if not value)


def _file_hash_matches(path: Path, expected_sha256: str) -> bool:
    return bool(path.exists() and expected_sha256 and sha256_file(path) == expected_sha256)


def _case_arbitration_summary(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts: Counter[str] = Counter()
    effect_counts: Counter[str] = Counter()
    applicable_with_weak_auxiliary = 0
    weak_positive_only = 0
    insufficient_strong_positive = 0
    positive_negative_conflict = 0
    for decision in decisions:
        if not isinstance(decision, dict):
            continue
        arbitration_status = str(decision.get("arbitration_status") or "not_recorded")
        status = str(decision.get("status") or "")
        summary = decision.get("arbitration_summary")
        decision_effect = (
            str(summary.get("decision_effect") or "not_recorded")
            if isinstance(summary, dict)
            else "not_recorded"
        )
        status_counts[arbitration_status] += 1
        effect_counts[decision_effect] += 1
        if status == "applicable" and decision.get("weak_auxiliary_trigger_groups"):
            applicable_with_weak_auxiliary += 1
        if status == "needs_adjudication" and arbitration_status == "weak_positive_only":
            weak_positive_only += 1
        if (
            status == "needs_adjudication"
            and arbitration_status == "insufficient_strong_positive_trigger"
        ):
            insufficient_strong_positive += 1
        if (
            status == "needs_adjudication"
            and arbitration_status == "positive_negative_conflict"
        ):
            positive_negative_conflict += 1
    return {
        "schema_version": "applicability-arbitration-summary-v0",
        "decision_count": sum(status_counts.values()),
        "arbitration_status_counts": dict(sorted(status_counts.items())),
        "decision_effect_counts": dict(sorted(effect_counts.items())),
        "applicable_with_weak_auxiliary_count": applicable_with_weak_auxiliary,
        "weak_positive_only_needs_adjudication_count": weak_positive_only,
        "insufficient_strong_positive_needs_adjudication_count": (
            insufficient_strong_positive
        ),
        "positive_negative_conflict_needs_adjudication_count": positive_negative_conflict,
        "conservative_arbitration_needs_adjudication_count": (
            weak_positive_only + insufficient_strong_positive
        ),
        "genuine_conflict_needs_adjudication_count": positive_negative_conflict,
    }


def _failure_taxonomy(
    *,
    result_flags: dict[str, bool],
    status_mismatches: list[dict[str, Any]],
    non_applicable_coverage_gaps: list[dict[str, Any]],
    gate_graph_decision_mismatches: list[dict[str, Any]],
    gate_graph_input_hash_gaps: list[dict[str, Any]],
    gate_graph_identity: dict[str, Any],
    gate_graph_validation: dict[str, Any],
    trajectory_process_quality: dict[str, Any],
    generated_error: str | None,
) -> list[dict[str, Any]]:
    taxonomy = []
    for name, passed in sorted(result_flags.items()):
        if passed:
            continue
        category = {
            "expected_statuses_match": "applicability_status_mismatch",
            "expected_applicable_authorities_match": "applicable_partition_mismatch",
            "expected_non_applicable_authorities_match": "non_applicable_partition_mismatch",
            "graph_trace_coverage_matches": "graph_trace_gap",
            "graph_non_path_matches": "graph_trace_gap",
            "source_record_alignment_matches": "source_record_alignment_mismatch",
            "document_role_alignment_matches": "document_role_alignment_mismatch",
            "package_section_alignment_matches": "package_section_alignment_mismatch",
            "basis_type_alignment_matches": "adjudication_mismatch",
            "arbitration_status_alignment_matches": "arbitration_mismatch",
            "arbitration_decision_effect_alignment_matches": "arbitration_mismatch",
            "package_fact_types_match": "package_fact_gap",
            "retrieval_trace_coverage_matches": "retrieval_trace_gap",
            "non_applicable_coverage_supported": "search_coverage_gap",
            "required_applicability_artifacts_present": "missing_applicability_artifact",
            "generated_rule_pack_matches_applicability": "generated_rule_pack_mismatch",
            "generated_rule_pack_hash_matches_validation": (
                "generated_rule_pack_mismatch"
            ),
            "generated_rule_pack_ready_matches": "generated_rule_pack_not_ready",
            "validation_passed_matches": "applicability_validation_mismatch",
            "gate_graph_validation_passed": "gate_graph_validation_mismatch",
            "gate_graph_identity_matches": "gate_graph_identity_mismatch",
            "gate_graph_input_hashes_match": "gate_graph_stale_artifact",
            "gate_graph_consistency_matches": "gate_graph_consistency_mismatch",
            "trajectory_process_quality_matches": "trajectory_process_quality_mismatch",
        }.get(name, "applicability_eval_mismatch")
        details: dict[str, Any] = {}
        if name == "expected_statuses_match":
            details["status_mismatches"] = status_mismatches
        if name == "non_applicable_coverage_supported":
            details["coverage_gaps"] = non_applicable_coverage_gaps
        if name == "gate_graph_consistency_matches":
            details["decision_mismatches"] = gate_graph_decision_mismatches
        if name == "gate_graph_input_hashes_match":
            details["input_hash_gaps"] = gate_graph_input_hash_gaps
        if name == "gate_graph_identity_matches":
            details["identity"] = gate_graph_identity
        if name == "gate_graph_validation_passed":
            details["validation"] = gate_graph_validation
        if name == "trajectory_process_quality_matches":
            details["trajectory_process_quality"] = trajectory_process_quality
        if generated_error:
            details["generated_error"] = generated_error
        taxonomy.append({"check": name, "category": category, "details": details})
    return taxonomy
