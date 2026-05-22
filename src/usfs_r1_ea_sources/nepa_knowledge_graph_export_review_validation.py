from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .nepa_knowledge_graph_export_models import REQUIRED_REVIEW_ARTIFACT_INPUT_NAMES
from .nepa_knowledge_graph_export_models import _candidate_authority_node_id
from .nepa_knowledge_graph_export_models import _check
from .nepa_knowledge_graph_export_models import _compliance_finding_node_id
from .nepa_knowledge_graph_export_models import _decision_node_id
from .nepa_knowledge_graph_export_models import _decision_readiness_blockers
from .nepa_knowledge_graph_export_models import _decision_status
from .nepa_knowledge_graph_export_models import _dict
from .nepa_knowledge_graph_export_models import _dict_list
from .nepa_knowledge_graph_export_models import _generated_rule_node_id
from .nepa_knowledge_graph_export_models import _read_json
from .nepa_knowledge_graph_export_models import _read_jsonl
from .nepa_knowledge_graph_export_models import _strings


def _review_overlay_validation_checks(
    *,
    graph: dict[str, Any],
    review_id: str,
    review_artifacts: dict[str, Any],
) -> list[dict[str, Any]]:
    authority_universe = _dict(review_artifacts.get("authority_universe_snapshot"))
    candidate_authorities = _dict_list(authority_universe.get("candidate_authorities"))
    decisions = _dict_list(review_artifacts.get("applicability_decisions"))
    search_coverage = _dict(review_artifacts.get("search_coverage_certificates"))
    generated_rule_pack = _dict(review_artifacts.get("generated_rule_pack"))
    compliance_matrix = _dict(review_artifacts.get("compliance_matrix"))
    applicability_validation = _dict(review_artifacts.get("applicability_validation"))
    generated_rule_pack_validation = _dict(review_artifacts.get("generated_rule_pack_validation"))
    compliance_validation = _dict(review_artifacts.get("compliance_validation"))
    review_input_gaps = _review_required_input_gaps(graph)
    coverage_reference_gaps = _search_coverage_reference_gaps(
        decisions,
        certificates_by_id={
            str(certificate.get("coverage_certificate_id")): certificate
            for certificate in _dict_list(search_coverage.get("certificates"))
            if certificate.get("coverage_certificate_id")
        },
    )
    retrieval_trace_reference_gaps = _trace_reference_gaps(
        decisions,
        trace_field="retrieval_trace_ids",
        available_ids={
            str(record.get("retrieval_trace_id"))
            for record in _dict_list(review_artifacts.get("applicability_retrieval_trace"))
            if record.get("retrieval_trace_id")
        },
    )
    graph_trace_reference_gaps = _graph_trace_reference_gaps(
        decisions,
        available_ids={
            str(record.get("graph_path_id"))
            for record in _dict_list(review_artifacts.get("applicability_graph_trace"))
            if record.get("graph_path_id")
        },
    )

    node_ids = {str(node.get("node_id")) for node in _dict_list(graph.get("nodes"))}
    edges = _dict_list(graph.get("edges"))
    edge_tuples = {
        (
            str(edge.get("edge_type") or ""),
            str(edge.get("source_node_id") or ""),
            str(edge.get("target_node_id") or ""),
        )
        for edge in edges
    }
    decision_by_candidate_id: dict[str, list[dict[str, Any]]] = {}
    decisions_by_id: dict[str, dict[str, Any]] = {}
    for decision in decisions:
        decision_by_candidate_id.setdefault(str(decision.get("candidate_authority_id") or ""), []).append(
            decision
        )
        decisions_by_id[str(decision.get("decision_id") or "")] = decision
    candidate_node_gaps = sorted(
        str(candidate.get("candidate_authority_id") or "")
        for candidate in candidate_authorities
        if _candidate_authority_node_id(candidate, base_rule_node_ids={}, template_node_ids={})
        not in node_ids
    )
    decision_cardinality_gaps = {
        str(candidate.get("candidate_authority_id") or ""): len(
            decision_by_candidate_id.get(str(candidate.get("candidate_authority_id") or ""), [])
        )
        for candidate in candidate_authorities
        if len(decision_by_candidate_id.get(str(candidate.get("candidate_authority_id") or ""), []))
        != 1
    }
    decision_mapping_gaps = sorted(
        str(decision.get("decision_id") or "")
        for decision in decisions
        if str(decision.get("candidate_authority_id") or "")
        not in {
            str(candidate.get("candidate_authority_id") or "")
            for candidate in candidate_authorities
        }
    )
    decision_edge_gaps = sorted(
        str(decision.get("decision_id") or "")
        for decision in decisions
        if (
            "PRODUCES_APPLICABILITY_DECISION",
            _candidate_authority_node_id(
                decision,
                base_rule_node_ids={},
                template_node_ids={},
            ),
            _decision_node_id(review_id, decision),
        )
        not in edge_tuples
    )
    unsupported_non_applicable = sorted(
        str(decision.get("decision_id") or "")
        for decision in decisions
        if _decision_status(decision) == "not_applicable"
        and not decision.get("search_coverage_certificate_ids")
        and not decision.get("human_adjudication_refs")
    )
    invalid_generated_rules = sorted(
        str(rule.get("generated_rule_id") or rule.get("id") or "")
        for rule in _dict_list(generated_rule_pack.get("rules"))
        if _decision_status(decisions_by_id.get(str(rule.get("applicability_decision_id") or ""), {}))
        != "applicable"
    )
    generated_rule_edge_gaps = sorted(
        str(rule.get("generated_rule_id") or rule.get("id") or "")
        for rule in _dict_list(generated_rule_pack.get("rules"))
        if (
            "GENERATES_RULE",
            _decision_node_id(
                review_id,
                decisions_by_id.get(str(rule.get("applicability_decision_id") or ""), {}),
            ),
            _generated_rule_node_id(
                review_id,
                str(rule.get("generated_rule_id") or rule.get("id") or ""),
            ),
        )
        not in edge_tuples
    )
    compliance_finding_edge_gaps = sorted(
        str(row.get("row_id") or row.get("rule_id") or "")
        for row in _dict_list(compliance_matrix.get("rows"))
        if (
            "SUPPORTS_COMPLIANCE_FINDING",
            _generated_rule_node_id(review_id, str(row.get("rule_id") or "")),
            _compliance_finding_node_id(review_id, str(row.get("row_id") or row.get("rule_id") or "")),
        )
        not in edge_tuples
    )
    finding_evidence_edge_gaps = []
    for row in _dict_list(compliance_matrix.get("rows")):
        finding_id = str(row.get("row_id") or row.get("rule_id") or "")
        finding_node_id = _compliance_finding_node_id(review_id, finding_id)
        evidence_edge_count = sum(
            1
            for edge_type, source_node_id, target_node_id in edge_tuples
            if edge_type == "SUPPORTS_COMPLIANCE_FINDING"
            and target_node_id == finding_node_id
            and source_node_id.startswith("evidence_span:review:")
        )
        if evidence_edge_count == 0:
            finding_evidence_edge_gaps.append(finding_id)
    return [
        _check(
            "nepa_3d_review_graph_links_required_review_artifacts",
            not review_input_gaps,
            "required review artifact inputs exist and are hashed",
            review_input_gaps,
        ),
        _check(
            "nepa_3d_review_graph_inputs_are_validated",
            bool(
                applicability_validation.get("passed")
                and generated_rule_pack_validation.get("passed")
                and compliance_validation.get("passed")
            ),
            {
                "applicability_validation": True,
                "generated_rule_pack_validation": True,
                "compliance_validation": True,
            },
            {
                "applicability_validation": applicability_validation.get("passed"),
                "generated_rule_pack_validation": generated_rule_pack_validation.get("passed"),
                "compliance_validation": compliance_validation.get("passed"),
            },
        ),
        _check(
            "nepa_3d_review_graph_exports_all_candidate_authorities",
            not candidate_node_gaps,
            len(candidate_authorities),
            candidate_node_gaps,
        ),
        _check(
            "nepa_3d_review_graph_maps_each_candidate_to_one_decision",
            not decision_cardinality_gaps,
            "exactly one decision per candidate authority",
            decision_cardinality_gaps,
        ),
        _check(
            "nepa_3d_review_graph_decisions_map_to_candidates",
            not decision_mapping_gaps,
            "all decisions reference candidate_authority_id values in authority_universe_snapshot",
            decision_mapping_gaps,
        ),
        _check(
            "nepa_3d_review_graph_links_candidates_to_decisions",
            not decision_edge_gaps,
            "PRODUCES_APPLICABILITY_DECISION edge for each decision",
            decision_edge_gaps,
        ),
        _check(
            "nepa_3d_review_graph_non_applicable_decisions_have_support",
            not unsupported_non_applicable,
            "search coverage certificate or adjudication reference",
            unsupported_non_applicable,
        ),
        _check(
            "nepa_3d_review_graph_search_coverage_references_resolve",
            not coverage_reference_gaps,
            "decision search coverage certificate IDs resolve and cover the decision",
            coverage_reference_gaps,
        ),
        _check(
            "nepa_3d_review_graph_retrieval_trace_references_resolve",
            not retrieval_trace_reference_gaps,
            "decision retrieval_trace_ids resolve to applicability retrieval trace records",
            retrieval_trace_reference_gaps,
        ),
        _check(
            "nepa_3d_review_graph_graph_trace_references_resolve",
            not graph_trace_reference_gaps,
            "decision graph path IDs resolve to applicability graph trace records",
            graph_trace_reference_gaps,
        ),
        _check(
            "nepa_3d_review_graph_generated_rules_from_applicable_decisions",
            not invalid_generated_rules,
            "generated rules derive only from applicable decisions",
            invalid_generated_rules,
        ),
        _check(
            "nepa_3d_review_graph_links_generated_rules_to_decisions",
            not generated_rule_edge_gaps,
            "GENERATES_RULE edge for each generated rule",
            generated_rule_edge_gaps,
        ),
        _check(
            "nepa_3d_review_graph_links_findings_to_generated_rules",
            not compliance_finding_edge_gaps,
            "SUPPORTS_COMPLIANCE_FINDING edge from generated rule to finding",
            compliance_finding_edge_gaps,
        ),
        _check(
            "nepa_3d_review_graph_links_findings_to_evidence",
            not finding_evidence_edge_gaps,
            "SUPPORTS_COMPLIANCE_FINDING evidence edge for each compliance finding",
            finding_evidence_edge_gaps,
        ),
    ]


def _forest_plan_inventory_ownership(
    *,
    forest_components: dict[str, Any],
    forest_plan_components_path: Path,
    output_dir: Path,
    source_set_id: str,
) -> dict[str, Any]:
    expected_path = (
        output_dir
        / "derived"
        / source_set_id
        / "forest_plan_components"
        / "component_inventory.json"
    ).resolve()
    actual_path = Path(forest_plan_components_path).resolve()
    inventory_source_set_id = str(forest_components.get("source_set_id") or "")
    return {
        "passed": actual_path == expected_path and inventory_source_set_id == source_set_id,
        "expected": {
            "source_set_id": source_set_id,
            "artifact_path": str(expected_path),
        },
        "actual": {
            "source_set_id": inventory_source_set_id or None,
            "artifact_path": str(actual_path),
        },
    }


def _review_required_input_gaps(graph: dict[str, Any]) -> dict[str, str]:
    inputs_by_name = {
        str(input_record.get("name") or ""): input_record
        for input_record in _dict_list(graph.get("inputs"))
    }
    gaps = {}
    for input_name in REQUIRED_REVIEW_ARTIFACT_INPUT_NAMES:
        input_record = inputs_by_name.get(input_name)
        if not input_record:
            gaps[input_name] = "missing_input_record"
        elif not input_record.get("exists"):
            gaps[input_name] = "missing_file"
        elif not input_record.get("sha256"):
            gaps[input_name] = "missing_hash"
    return gaps


def _search_coverage_reference_gaps(
    decisions: list[dict[str, Any]],
    *,
    certificates_by_id: dict[str, dict[str, Any]],
) -> dict[str, list[str]]:
    gaps = {}
    for decision in decisions:
        decision_id = str(decision.get("decision_id") or "")
        candidate_id = str(decision.get("candidate_authority_id") or "")
        decision_gaps = []
        for certificate_id in _strings(decision.get("search_coverage_certificate_ids")):
            certificate = certificates_by_id.get(certificate_id)
            if not certificate:
                decision_gaps.append(f"{certificate_id}:missing_certificate")
                continue
            covered_decision_ids = set(_strings(certificate.get("covered_decision_ids")))
            covered_candidate_ids = set(
                _strings(certificate.get("covered_candidate_authority_ids"))
            )
            if decision_id and decision_id not in covered_decision_ids:
                decision_gaps.append(f"{certificate_id}:decision_not_covered")
            if candidate_id and candidate_id not in covered_candidate_ids:
                decision_gaps.append(f"{certificate_id}:candidate_not_covered")
            if str(certificate.get("coverage_result") or "") != "sufficient":
                decision_gaps.append(f"{certificate_id}:coverage_not_sufficient")
        if decision_gaps:
            gaps[decision_id] = sorted(decision_gaps)
    return gaps


def _trace_reference_gaps(
    decisions: list[dict[str, Any]],
    *,
    trace_field: str,
    available_ids: set[str],
) -> dict[str, list[str]]:
    gaps = {}
    for decision in decisions:
        missing = sorted(
            trace_id
            for trace_id in _strings(decision.get(trace_field))
            if trace_id not in available_ids
        )
        if missing:
            gaps[str(decision.get("decision_id") or "")] = missing
    return gaps


def _graph_trace_reference_gaps(
    decisions: list[dict[str, Any]],
    *,
    available_ids: set[str],
) -> dict[str, list[str]]:
    gaps = {}
    for decision in decisions:
        decision_graph_path_ids = set(_strings(decision.get("selected_graph_path_ids")))
        decision_graph_path_ids.update(_strings(decision.get("graph_path_ids")))
        missing = sorted(
            graph_path_id
            for graph_path_id in decision_graph_path_ids
            if graph_path_id not in available_ids
        )
        if missing:
            gaps[str(decision.get("decision_id") or "")] = missing
    return gaps


def _review_overlay_summary(
    *,
    review_id: str,
    candidate_authorities: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    generated_rules: list[dict[str, Any]],
    compliance_rows: list[dict[str, Any]],
    search_coverage: dict[str, Any],
    review_artifacts: dict[str, Any],
) -> dict[str, Any]:
    decision_status_counts = Counter(_decision_status(decision) for decision in decisions)
    artifact_counts = _review_artifact_counts(review_artifacts)
    return {
        "review_id": review_id,
        "review_candidate_authority_count": len(candidate_authorities),
        "review_candidate_authority_type_counts": dict(
            Counter(str(candidate.get("candidate_authority_type")) for candidate in candidate_authorities)
        ),
        "review_decision_count": len(decisions),
        "review_decision_status_counts": dict(decision_status_counts),
        "applicable_decision_count": decision_status_counts.get("applicable", 0),
        "non_applicable_decision_count": decision_status_counts.get("not_applicable", 0),
        "needs_adjudication_decision_count": decision_status_counts.get("needs_adjudication", 0),
        "unresolved_decision_count": decision_status_counts.get("unresolved", 0),
        "generated_rule_count": len(generated_rules),
        "compliance_finding_count": len(compliance_rows),
        "search_coverage_certificate_count": len(_dict_list(search_coverage.get("certificates"))),
        "review_blocker_count": sum(
            1 for decision in decisions if _decision_readiness_blockers(decision)
        ),
        "review_required_artifact_count": len(REQUIRED_REVIEW_ARTIFACT_INPUT_NAMES),
        **artifact_counts,
    }


def _review_artifact_counts(review_artifacts: dict[str, Any]) -> dict[str, int]:
    package_fact_graph = _dict(review_artifacts.get("package_fact_graph"))
    search_coverage = _dict(review_artifacts.get("search_coverage_certificates"))
    return {
        "review_package_fact_node_count": len(_dict_list(package_fact_graph.get("nodes"))),
        "review_package_fact_edge_count": len(_dict_list(package_fact_graph.get("edges"))),
        "review_retrieval_trace_count": len(
            _dict_list(review_artifacts.get("applicability_retrieval_trace"))
        ),
        "review_graph_trace_count": len(
            _dict_list(review_artifacts.get("applicability_graph_trace"))
        ),
        "review_search_coverage_certificate_count": len(
            _dict_list(search_coverage.get("certificates"))
        ),
        "review_finding_graph_node_count": len(
            _dict_list(review_artifacts.get("finding_graph_nodes"))
        ),
        "review_finding_graph_edge_count": len(
            _dict_list(review_artifacts.get("finding_graph_edges"))
        ),
    }


def _review_artifact_paths(review_dir: Path | None) -> dict[str, Path]:
    if review_dir is None:
        return {}
    applicability_dir = review_dir / "applicability"
    return {
        "review_authority_universe_snapshot": applicability_dir / "authority_universe_snapshot.json",
        "review_package_fact_graph": applicability_dir / "package_fact_graph.json",
        "review_applicability_retrieval_trace": applicability_dir / "applicability_retrieval_trace.jsonl",
        "review_applicability_graph_trace": applicability_dir / "applicability_graph_trace.jsonl",
        "review_applicability_decisions": applicability_dir / "applicability_decisions.jsonl",
        "review_search_coverage_certificates": applicability_dir / "search_coverage_certificates.json",
        "review_applicability_validation": applicability_dir / "applicability_validation.json",
        "review_generated_rule_pack": applicability_dir / "generated_rule_pack.json",
        "review_generated_rule_pack_validation": applicability_dir
        / "generated_rule_pack_validation.json",
        "review_compliance_matrix": review_dir / "compliance_matrix.json",
        "review_compliance_validation": review_dir / "compliance_validation.json",
        "review_finding_graph_nodes": review_dir / "finding_graph_nodes.jsonl",
        "review_finding_graph_edges": review_dir / "finding_graph_edges.jsonl",
    }


def _load_review_artifacts(paths: dict[str, Path]) -> dict[str, Any]:
    return {
        "authority_universe_snapshot": _read_json(paths["review_authority_universe_snapshot"]),
        "package_fact_graph": _read_json(paths["review_package_fact_graph"]),
        "applicability_retrieval_trace": _read_jsonl(
            paths["review_applicability_retrieval_trace"]
        ),
        "applicability_graph_trace": _read_jsonl(paths["review_applicability_graph_trace"]),
        "applicability_decisions": _read_jsonl(paths["review_applicability_decisions"]),
        "search_coverage_certificates": _read_json(
            paths["review_search_coverage_certificates"]
        ),
        "applicability_validation": _read_json(paths["review_applicability_validation"]),
        "generated_rule_pack": _read_json(paths["review_generated_rule_pack"]),
        "generated_rule_pack_validation": _read_json(
            paths["review_generated_rule_pack_validation"]
        ),
        "compliance_matrix": _read_json(paths["review_compliance_matrix"]),
        "compliance_validation": _read_json(paths["review_compliance_validation"]),
        "finding_graph_nodes": _read_jsonl(paths["review_finding_graph_nodes"]),
        "finding_graph_edges": _read_jsonl(paths["review_finding_graph_edges"]),
    }
