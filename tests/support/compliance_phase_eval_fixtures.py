from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json

from usfs_r1_ea_sources.final_qa_certification import run_final_qa_certification
from usfs_r1_ea_sources.phase_eval import run_phase_aligned_eval

from tests.support.compliance_phase_eval_contracts import build_final_qa_config
from tests.support.compliance_phase_eval_contracts import build_final_qa_expected
from tests.support.compliance_phase_eval_contracts import write_decision_support_artifacts
from tests.support.compliance_review_fixtures import (
    _write_downstream_direct_eval_phase_outputs,
    _write_json,
)


def _write_graph_phase_outputs(output_dir: Path, source_set_id: str) -> None:
    graph_dir = output_dir / "derived" / source_set_id / "evidence_graph"
    graph_dir.mkdir(parents=True, exist_ok=True)
    (graph_dir / "evidence_graph_validation.json").write_text(
        json.dumps({"passed": True, "checks": []}, sort_keys=True),
        encoding="utf-8",
    )
    (graph_dir / "summary.json").write_text(
        json.dumps(
            {
                "reviewer_ready": True,
                "validation_passed": True,
                "retrieval_index_path": "index.sqlite",
                "retrieval_index_chunk_count": 2,
                "retrieval_binding_mismatch_count": 0,
                "metrics": {},
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    _write_upstream_evaluation_phase_outputs(output_dir)
    _write_downstream_direct_eval_phase_outputs(output_dir, source_set_id)


def _write_upstream_evaluation_phase_outputs(output_dir: Path) -> None:
    path = output_dir / "evaluations" / "upstream" / "upstream_evaluation_results.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "upstream-evaluation-results-v0",
                "passed": True,
                "lane_summaries": [
                    {"lane_id": "capture", "status": "direct_eval_present"},
                    {"lane_id": "catalog", "status": "direct_eval_present"},
                    {"lane_id": "extraction", "status": "direct_eval_present"},
                ],
                "failed_case_ids": [],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _write_final_qa_phase_outputs(
    review_dir: Path,
    *,
    review_id: str,
    source_set_id: str,
) -> None:
    output_dir = review_dir.parents[1]
    final_qa_dir = review_dir / "final_qa"
    final_qa_dir.mkdir(parents=True, exist_ok=True)

    _write_review_packet_index_artifacts(
        review_dir,
        review_id=review_id,
        source_set_id=source_set_id,
    )
    _write_forest_plan_artifacts(review_dir, review_id=review_id, source_set_id=source_set_id)
    _augment_applicability_gate_artifacts(
        review_dir,
        review_id=review_id,
        source_set_id=source_set_id,
    )
    _write_v1_ea_eval_artifact(review_dir, review_id=review_id, source_set_id=source_set_id)
    write_decision_support_artifacts(
        output_dir=output_dir,
        review_dir=review_dir,
        review_id=review_id,
        source_set_id=source_set_id,
    )

    baseline_phase_eval = run_phase_aligned_eval(
        output_dir=output_dir,
        source_set_id=source_set_id,
        review_id=review_id,
    )
    _write_promotion_suite_artifact(output_dir, source_set_id=source_set_id)

    expected_counts = _phase_eval_expected_counts(
        output_dir=output_dir,
        review_dir=review_dir,
        baseline_phase_eval=baseline_phase_eval.summary,
    )
    config_path = final_qa_dir / "final_qa_contract_config.json"
    expected_path = final_qa_dir / "final_qa_expected_summary.json"
    _write_json(config_path, build_final_qa_config(review_id, source_set_id, expected_counts))
    _write_json(
        expected_path,
        build_final_qa_expected(
            output_dir=output_dir,
            review_id=review_id,
            source_set_id=source_set_id,
            expected_counts=expected_counts,
        ),
    )

    result = run_final_qa_certification(
        output_dir=output_dir,
        review_id=review_id,
        config_path=config_path,
        expected_summary_path=expected_path,
        results_dir=final_qa_dir,
    )
    if result.summary.get("passed") is not True:
        raise AssertionError(
            f"synthetic final QA fixture failed validation: {result.summary}"
        )


def _write_review_packet_index_artifacts(
    review_dir: Path,
    *,
    review_id: str,
    source_set_id: str,
) -> None:
    review_packet_dir = review_dir / "review_packet_index"
    review_packet_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        review_packet_dir / "review_packet_row_inventory.json",
        {
            "schema_version": "review-packet-row-inventory-v1",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "summary": {
                "applicable_authority_count": 1,
                "non_applicable_authority_count": 1,
                "forest_plan_component_row_count": 0,
                "applicable_standard_count": 0,
                "row_set_sha256": "synthetic-row-set",
            },
            "applicable_authority_rows": [{"rule_id": "purpose_need"}],
            "non_applicable_authority_rows": [
                {"candidate_authority_id": "candidate:synthetic-boundary"}
            ],
            "forest_plan_component_rows": [],
            "applicable_forest_plan_standard_rows": [],
        },
    )
    _write_json(
        review_packet_dir / "compliance_matrix_render_manifest.json",
        {
            "schema_version": "compliance-matrix-render-manifest-v1",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "summary": {
                "passed": True,
                "row_count": 1,
                "authority_row_count": 1,
                "forest_plan_row_count": 0,
                "row_set_sha256": "synthetic-render-row-set",
            },
            "rows": [
                {
                    "row_class": "applicable_authority",
                    "row_identity": {"rule_id": "purpose_need"},
                }
            ],
        },
    )
    _write_json(
        review_packet_dir / "review_packet_index.json",
        {
            "schema_version": "review-packet-index-v1",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "row_inventory_summary": {
                "applicable_authority_count": 1,
                "non_applicable_authority_count": 1,
                "forest_plan_component_row_count": 0,
                "applicable_standard_count": 0,
            },
            "render_manifest_summary": {
                "passed": True,
                "authority_row_count": 1,
                "forest_plan_row_count": 0,
            },
            "applicable_authority_rows": [{"rule_id": "purpose_need"}],
            "non_applicable_authority_boundary": {
                "non_applicable_authority_count": 1,
                "rows": [{"candidate_authority_id": "candidate:synthetic-boundary"}],
            },
            "forest_plan_component_rows": [],
            "applicable_forest_plan_standard_rows": [],
        },
    )
    _write_json(
        review_packet_dir / "review_packet_index_validation.json",
        {
            "schema_version": "review-packet-index-validation-v1",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "passed": True,
            "reviewer_ready": True,
            "summary": {
                "failed_check_count": 0,
                "applicable_authority_count": 1,
                "non_applicable_authority_count": 1,
                "forest_plan_component_row_count": 0,
                "applicable_standard_count": 0,
                "row_set_sha256": "synthetic-row-set",
            },
        },
    )
    (review_packet_dir / "review_packet_index.pdf").write_bytes(b"%PDF-1.4\n")


def _write_forest_plan_artifacts(
    review_dir: Path,
    *,
    review_id: str,
    source_set_id: str,
) -> None:
    component_evaluation = {
        "component_count": 0,
        "supported_count": 0,
        "not_applicable_count": 0,
        "gap_count": 0,
        "standard_count": 0,
        "applicable_standard_count": 0,
        "applied_standard_count": 0,
    }
    compliance_matrix_path = review_dir / "compliance_matrix.json"
    compliance_matrix = _read_json(compliance_matrix_path)
    matrix_summary = dict(compliance_matrix.get("summary") or {})
    forest_plan_review = dict(matrix_summary.get("forest_plan_review") or {})
    forest_plan_review["component_evaluation"] = component_evaluation
    matrix_summary["forest_plan_review"] = forest_plan_review
    compliance_matrix["summary"] = matrix_summary
    _write_json(compliance_matrix_path, compliance_matrix)

    compliance_review_path = review_dir / "compliance_review.json"
    compliance_review = _read_json(compliance_review_path)
    compliance_summary = dict(compliance_review.get("summary") or {})
    compliance_summary["forest_plan_review"] = {
        "component_evaluation": component_evaluation
    }
    compliance_review["summary"] = compliance_summary
    _write_json(compliance_review_path, compliance_review)

    _write_json(
        review_dir / "forest_plan_context_summary.json",
        {
            "schema_version": "forest-plan-context-summary-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "reviewer_ready": True,
            "scope_status": "not_in_scope",
            "package_file_count": 1,
            "package_chunk_count": 1,
            "validation_passed": True,
        },
    )
    _write_json(
        review_dir / "forest_plan_component_eval_results.json",
        {
            "schema_version": "forest-plan-component-eval-results-v0",
            "passed": True,
            "summary": {
                "schema_version": "forest-plan-component-eval-results-v0",
                "review_id": review_id,
                "source_set_id": source_set_id,
                "passed": True,
                "case_count": 0,
                "passed_case_count": 0,
                "failed_case_count": 0,
                "metrics": {},
                "failure_category_counts": {},
            },
        },
    )
    _write_json(
        review_dir / "forest_plan_applicable_standard_coverage.json",
        {
            "schema_version": "forest-plan-applicable-standard-coverage-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "passed": True,
            "all_applicable_standards_applied": True,
            "standard_count": 0,
            "applicable_standard_count": 0,
            "applied_standard_count": 0,
            "standards": [],
        },
    )
    _write_json(
        review_dir / "litigation_risk_summary.json",
        {
            "schema_version": "litigation-risk-summary-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "summary": {
                "risk_flag_count": 0,
                "legal_conclusion_count": 0,
                "deterministic_only": True,
            },
            "risk_flags": [],
        },
    )


def _augment_applicability_gate_artifacts(
    review_dir: Path,
    *,
    review_id: str,
    source_set_id: str,
) -> None:
    synthetic_non_applicable = {
        "candidate_authority_id": "candidate:synthetic-boundary",
        "candidate_authority_type": "rule_template",
        "decision_id": "decision:synthetic-boundary",
        "authority_family_id": "synthetic_boundary",
        "authority_family_ids": ["synthetic_boundary"],
        "status": "not_applicable",
        "basis_type": "absent_trigger_evidence",
        "applicability_basis": {"rationale": "Synthetic boundary evidence."},
        "non_applicability_basis": {"rationale": "Synthetic boundary evidence."},
        "retrieval_trace_ids": ["retrieval:candidate:synthetic-boundary"],
        "graph_path_ids": ["graph:candidate:synthetic-boundary"],
        "search_coverage_certificate_ids": ["coverage:synthetic-boundary"],
        "source_record_ids": ["R1EA-NON"],
    }
    synthetic_certificate = {
        "coverage_certificate_id": "coverage:synthetic-boundary",
        "candidate_authority_id": "candidate:synthetic-boundary",
        "covered_candidate_authority_ids": ["candidate:synthetic-boundary"],
        "covered_decision_ids": ["decision:synthetic-boundary"],
        "coverage_class": "non_applicable_authority",
        "coverage_result": "sufficient",
        "rationale": "Synthetic coverage certificate.",
        "missing_query_variants": [],
    }

    authority_universe_path = review_dir / "applicability" / "authority_universe_snapshot.json"
    authority_universe = _read_json(authority_universe_path)
    candidate_authorities = list(authority_universe.get("candidate_authorities") or [])
    candidate_authorities = [
        row
        for row in candidate_authorities
        if row.get("candidate_authority_id") != synthetic_non_applicable["candidate_authority_id"]
    ]
    candidate_authorities.append(synthetic_non_applicable)
    authority_universe["candidate_authorities"] = candidate_authorities
    _write_json(authority_universe_path, authority_universe)

    decisions_path = review_dir / "applicability" / "applicability_decisions.jsonl"
    decisions = _read_jsonl(decisions_path)
    decisions = [
        row
        for row in decisions
        if row.get("candidate_authority_id") != synthetic_non_applicable["candidate_authority_id"]
    ]
    decisions.append(synthetic_non_applicable)
    _write_jsonl(decisions_path, decisions)

    retrieval_trace_path = (
        review_dir / "applicability" / "applicability_retrieval_trace.jsonl"
    )
    retrieval_rows = _read_jsonl(retrieval_trace_path)
    retrieval_rows = [
        row
        for row in retrieval_rows
        if row.get("candidate_authority_id") != synthetic_non_applicable["candidate_authority_id"]
    ]
    retrieval_rows.append(
        {
            "candidate_authority_id": synthetic_non_applicable["candidate_authority_id"],
            "trace_id": "retrieval:candidate:synthetic-boundary",
        }
    )
    _write_jsonl(retrieval_trace_path, retrieval_rows)

    graph_trace_path = review_dir / "applicability" / "applicability_graph_trace.jsonl"
    graph_rows = _read_jsonl(graph_trace_path)
    graph_rows = [
        row
        for row in graph_rows
        if row.get("candidate_authority_id") != synthetic_non_applicable["candidate_authority_id"]
    ]
    graph_rows.append(
        {
            "candidate_authority_id": synthetic_non_applicable["candidate_authority_id"],
            "trace_id": "graph:candidate:synthetic-boundary",
        }
    )
    _write_jsonl(graph_trace_path, graph_rows)

    diagnostics_path = (
        review_dir / "applicability" / "applicability_retrieval_graph_diagnostics.json"
    )
    diagnostics = _read_json(diagnostics_path)
    diagnostics["retrieval_trace_sha256"] = _sha256_file(retrieval_trace_path)
    diagnostics["graph_trace_sha256"] = _sha256_file(graph_trace_path)
    _write_json(diagnostics_path, diagnostics)

    non_applicable_path = review_dir / "applicability" / "non_applicable_authorities.json"
    non_applicable = _read_json(non_applicable_path)
    non_applicable["authorities"] = [synthetic_non_applicable]
    non_applicable["authority_count"] = 1
    _write_json(non_applicable_path, non_applicable)

    coverage_path = review_dir / "applicability" / "search_coverage_certificates.json"
    coverage = _read_json(coverage_path)
    coverage["certificates"] = [synthetic_certificate]
    _write_json(coverage_path, coverage)

    validation_path = review_dir / "applicability" / "applicability_validation.json"
    validation = _read_json(validation_path)
    hashes = dict(validation.get("hashes") or {})
    hashes["authority_universe_sha256"] = _sha256_file(authority_universe_path)
    hashes["decisions_sha256"] = _sha256_file(decisions_path)
    hashes["non_applicable_authorities_sha256"] = _sha256_file(non_applicable_path)
    hashes["search_coverage_certificates_sha256"] = _sha256_file(coverage_path)
    validation.update(
        {
            "review_id": review_id,
            "source_set_id": source_set_id,
            "candidate_authority_count": 2,
            "applicable_authority_count": 1,
            "non_applicable_authority_count": 1,
            "unresolved_authority_count": 0,
            "hashes": hashes,
        }
    )
    _write_json(validation_path, validation)

    generated_rule_pack_path = review_dir / "applicability" / "generated_rule_pack.json"
    generated_rule_pack = _read_json(generated_rule_pack_path)
    generated_rule_pack.update(
        {
            "authority_universe_sha256": hashes["authority_universe_sha256"],
            "decisions_sha256": hashes["decisions_sha256"],
            "non_applicable_authorities_sha256": hashes[
                "non_applicable_authorities_sha256"
            ],
            "search_coverage_certificates_sha256": hashes[
                "search_coverage_certificates_sha256"
            ],
            "applicability_validation_sha256": _sha256_file(validation_path),
        }
    )
    _write_json(generated_rule_pack_path, generated_rule_pack)

    generated_validation_path = (
        review_dir / "applicability" / "generated_rule_pack_validation.json"
    )
    generated_validation = _read_json(generated_validation_path)
    summary = dict(generated_validation.get("summary") or {})
    summary["generated_rule_count"] = 1
    summary["generated_rule_pack_sha256"] = _sha256_file(generated_rule_pack_path)
    summary["expected_generated_rule_pack_sha256"] = summary["generated_rule_pack_sha256"]
    generated_validation["summary"] = summary
    generated_validation["review_id"] = review_id
    generated_validation["source_set_id"] = source_set_id
    _write_json(generated_validation_path, generated_validation)


def _write_v1_ea_eval_artifact(
    review_dir: Path,
    *,
    review_id: str,
    source_set_id: str,
) -> None:
    _write_json(
        review_dir / "v1_ea_eval_results.json",
        {
            "schema_version": "v1-ea-real-review-eval-results-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "passed": True,
            "conditional_adjudication": {
                "policy_mode": "accepted_pending_v1",
                "accepted_pending_count": 1,
                "actual_pending_count": 1,
                "actual_pending_applicable_count": 1,
                "accepted_pending_rule_ids": ["purpose_need"],
                "pending_results": [
                    {
                        "rule_id": "purpose_need",
                        "actual_applicability": "applicable",
                        "actual_status": "pass",
                        "classification_rationale": "Synthetic pending risk.",
                        "actual_source_record_ids": ["R1EA-001"],
                    }
                ],
            },
        },
    )


def _write_promotion_suite_artifact(output_dir: Path, *, source_set_id: str) -> None:
    suite_dir = (
        output_dir
        / "reviews"
        / "promotion_suite"
        / "post-v1-region1-ea-promotion-suite"
    )
    suite_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        suite_dir / "promotion_suite_results.json",
        {
            "schema_version": "promotion-suite-results-v1",
            "source_set_id": source_set_id,
            "current_promotion_ready": True,
            "required_current_result_count": 1,
            "passed_required_current_result_count": 1,
            "expansion_failure_category_counts": {},
            "review_cases": [],
        },
    )


def _phase_eval_expected_counts(
    *,
    output_dir: Path,
    review_dir: Path,
    baseline_phase_eval: dict,
) -> dict[str, int]:
    decision = _read_json(review_dir / "decision_support" / "ea_consistency_decision_support.json")
    applicability = _read_json(review_dir / "applicability" / "applicability_validation.json")
    generated_validation = _read_json(
        review_dir / "applicability" / "generated_rule_pack_validation.json"
    )
    compliance = _summary_or_self(_read_json(review_dir / "compliance_review.json"))
    matrix = _read_json(review_dir / "compliance_matrix.json").get("summary", {})
    forest = _selector(matrix, "forest_plan_review.component_evaluation") or {}
    review_packet = _selector(
        _read_json(review_dir / "review_packet_index" / "review_packet_index_validation.json"),
        "summary",
    ) or {}
    promotion = _read_json(
        output_dir
        / "reviews"
        / "promotion_suite"
        / "post-v1-region1-ea-promotion-suite"
        / "promotion_suite_results.json"
    )
    conditional = _read_json(review_dir / "v1_ea_eval_results.json").get(
        "conditional_adjudication",
        {},
    )

    return {
        "package_file_count": _selector(decision, "record_and_artifact_inventory.package_file_count"),
        "package_chunk_count": _selector(
            decision,
            "record_and_artifact_inventory.package_chunk_count",
        ),
        "baseline_source_record_count": compliance.get("baseline_source_record_count"),
        "candidate_authority_count": applicability.get("candidate_authority_count"),
        "applicable_authority_count": applicability.get("applicable_authority_count"),
        "non_applicable_authority_count": applicability.get("non_applicable_authority_count"),
        "unresolved_authority_count": applicability.get("unresolved_authority_count"),
        "generated_rule_count": _selector(generated_validation, "summary.generated_rule_count"),
        "authority_finding_count": compliance.get("finding_count"),
        "authority_finding_status_counts.pass": _selector(
            compliance,
            "finding_status_counts.pass",
        ),
        "rule_claim_link_count": compliance.get("rule_claim_link_count"),
        "rule_claim_gap_count": compliance.get("rule_claim_gap_count"),
        "compliance_matrix_authority_row_count": matrix.get("applicable_row_count"),
        "forest_plan_component_count": forest.get("component_count", 0),
        "forest_plan_supported_component_count": forest.get("supported_count", 0),
        "forest_plan_not_applicable_component_count": forest.get(
            "not_applicable_count",
            0,
        ),
        "forest_plan_gap_count": forest.get("gap_count", 0),
        "forest_plan_standard_count": forest.get("standard_count", 0),
        "applicable_standard_count": forest.get("applicable_standard_count", 0),
        "applied_standard_count": forest.get("applied_standard_count", 0),
        "forest_plan_component_eval_case_count": _selector(
            _read_json(review_dir / "forest_plan_component_eval_results.json"),
            "summary.case_count",
        )
        or 0,
        "phase_eval_phase_count": baseline_phase_eval["phase_count"],
        "phase_eval_passed_phase_count": baseline_phase_eval["passed_phase_count"],
        "promotion_suite_required_current_result_count": promotion.get(
            "required_current_result_count"
        ),
        "promotion_suite_passed_required_current_result_count": promotion.get(
            "passed_required_current_result_count"
        ),
        "review_packet_index_applicable_authority_count": review_packet.get(
            "applicable_authority_count",
            0,
        ),
        "review_packet_index_non_applicable_authority_count": review_packet.get(
            "non_applicable_authority_count",
            0,
        ),
        "review_packet_index_forest_plan_component_row_count": review_packet.get(
            "forest_plan_component_row_count",
            0,
        ),
        "review_packet_index_applicable_standard_count": review_packet.get(
            "applicable_standard_count",
            0,
        ),
        "review_packet_index_render_manifest_authority_row_count": 1,
        "review_packet_index_render_manifest_forest_plan_row_count": 0,
        "review_packet_index_validation_failed_check_count": review_packet.get(
            "failed_check_count",
            0,
        ),
        "accepted_v1_risk_count": conditional.get("accepted_pending_count"),
        "actual_pending_applicable_count": conditional.get(
            "actual_pending_applicable_count"
        ),
        "litigation_risk_legal_conclusion_count": 0,
    }


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _summary_or_self(payload: dict) -> dict:
    summary = payload.get("summary")
    return summary if isinstance(summary, dict) else payload


def _selector(payload: dict, selector: str):
    current = payload
    for part in selector.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()
