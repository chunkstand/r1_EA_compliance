from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any

from .artifact_utils import _dict
from .artifact_utils import _dict_list
from .artifact_utils import _read_json_if_exists
from .artifact_utils import _safe_int
from .artifact_utils import _selector_value
from .ea_consistency_decision_support import DEFAULT_CONFIG_PATH as DECISION_SUPPORT_CONFIG_PATH
from .ea_consistency_decision_support import (
    DEFAULT_EXPECTED_SUMMARY_PATH as DECISION_SUPPORT_EXPECTED_SUMMARY_PATH,
)
from .ea_consistency_decision_support import infer_decision_support_contract_paths
from .ea_consistency_decision_support import validate_ea_consistency_decision_support_report
from .final_qa_certification import MANIFEST_FILENAME as FINAL_QA_MANIFEST_FILENAME
from .final_qa_certification import PDF_FILENAME as FINAL_QA_PDF_FILENAME
from .final_qa_certification import REPORT_FILENAME as FINAL_QA_REPORT_FILENAME
from .final_qa_certification import VALIDATION_FILENAME as FINAL_QA_VALIDATION_FILENAME
from .final_qa_certification import VALIDATION_SCHEMA_VERSION as FINAL_QA_VALIDATION_SCHEMA_VERSION
from .phase_eval_support import _applicability_validation_hash_gaps
from .phase_eval_support import _authority_partition_ids
from .phase_eval_support import _candidate_authority_ids
from .phase_eval_support import _failed_check_names
from .phase_eval_support import _file_hash_matches
from .phase_eval_support import _generated_rule_candidate_id
from .phase_eval_support import _non_applicable_coverage_gaps
from .phase_eval_support import _path_exists
from .phase_eval_support import _path_string
from .phase_eval_support import _phase
from .phase_eval_support import _read_json_if_path
from .phase_eval_support import _read_jsonl_if_path
from .review_packet_index import PACKET_INDEX_FILENAME as REVIEW_PACKET_INDEX_FILENAME
from .review_packet_index import PACKET_INDEX_PDF_FILENAME as REVIEW_PACKET_INDEX_PDF_FILENAME
from .review_packet_index import PACKET_INDEX_SCHEMA_VERSION as REVIEW_PACKET_INDEX_SCHEMA_VERSION
from .review_packet_index import RENDER_MANIFEST_FILENAME as REVIEW_PACKET_RENDER_MANIFEST_FILENAME
from .review_packet_index import RENDER_MANIFEST_SCHEMA_VERSION as REVIEW_PACKET_RENDER_SCHEMA_VERSION
from .review_packet_index import ROW_INVENTORY_FILENAME as REVIEW_PACKET_ROW_INVENTORY_FILENAME
from .review_packet_index import ROW_INVENTORY_SCHEMA_VERSION as REVIEW_PACKET_ROW_SCHEMA_VERSION
from .review_packet_index import VALIDATION_FILENAME as REVIEW_PACKET_VALIDATION_FILENAME
from .review_packet_index import VALIDATION_SCHEMA_VERSION as REVIEW_PACKET_VALIDATION_SCHEMA_VERSION


def _review_packet_index_phase(
    *,
    review_id: str,
    source_set_id: str,
    review_dir: Path,
    review_packet_index_dir: Path,
) -> dict:
    inventory_path = review_packet_index_dir / REVIEW_PACKET_ROW_INVENTORY_FILENAME
    render_manifest_path = (
        review_packet_index_dir / REVIEW_PACKET_RENDER_MANIFEST_FILENAME
    )
    packet_index_path = review_packet_index_dir / REVIEW_PACKET_INDEX_FILENAME
    validation_path = review_packet_index_dir / REVIEW_PACKET_VALIDATION_FILENAME
    pdf_path = review_packet_index_dir / REVIEW_PACKET_INDEX_PDF_FILENAME
    matrix_path = review_dir / "compliance_matrix.json"

    inventory = _read_json_if_exists(inventory_path)
    render_manifest = _read_json_if_exists(render_manifest_path)
    packet_index = _read_json_if_exists(packet_index_path)
    validation = _read_json_if_exists(validation_path)
    matrix = _read_json_if_exists(matrix_path)
    validation_summary = _dict((validation or {}).get("summary"))
    matrix_rows = _dict_list((matrix or {}).get("rows"))
    matrix_forest_rows = _dict_list(
        _dict((matrix or {}).get("forest_plan_compliance")).get("rows")
    )
    authority_row_ids = {str(row.get("rule_id")) for row in matrix_rows if row.get("rule_id")}
    inventory_authority_ids = {
        str(row.get("rule_id"))
        for row in _dict_list((inventory or {}).get("applicable_authority_rows"))
        if row.get("rule_id")
    }
    packet_authority_ids = {
        str(row.get("rule_id"))
        for row in _dict_list((packet_index or {}).get("applicable_authority_rows"))
        if row.get("rule_id")
    }
    render_authority_ids = {
        str(_dict(row.get("row_identity")).get("rule_id"))
        for row in _dict_list((render_manifest or {}).get("rows"))
        if row.get("row_class") == "applicable_authority"
        and _dict(row.get("row_identity")).get("rule_id")
    }
    forest_component_ids = {
        str(row.get("component_id"))
        for row in matrix_forest_rows
        if row.get("component_id")
    }
    render_forest_ids = {
        str(_dict(row.get("row_identity")).get("component_id"))
        for row in _dict_list((render_manifest or {}).get("rows"))
        if row.get("row_class") == "forest_plan_component"
        and _dict(row.get("row_identity")).get("component_id")
    }
    packet_forest_ids = {
        str(row.get("component_id"))
        for row in _dict_list((packet_index or {}).get("forest_plan_component_rows"))
        if row.get("component_id")
    }
    checks = {
        "inventory_exists": inventory is not None,
        "render_manifest_exists": render_manifest is not None,
        "packet_index_exists": packet_index is not None,
        "validation_exists": validation is not None,
        "pdf_exists": pdf_path.exists(),
        "inventory_schema_matches": (inventory or {}).get("schema_version")
        == REVIEW_PACKET_ROW_SCHEMA_VERSION,
        "render_manifest_schema_matches": (render_manifest or {}).get("schema_version")
        == REVIEW_PACKET_RENDER_SCHEMA_VERSION,
        "packet_index_schema_matches": (packet_index or {}).get("schema_version")
        == REVIEW_PACKET_INDEX_SCHEMA_VERSION,
        "validation_schema_matches": (validation or {}).get("schema_version")
        == REVIEW_PACKET_VALIDATION_SCHEMA_VERSION,
        "packet_identity_matches": (packet_index or {}).get("review_id") == review_id
        and (packet_index or {}).get("source_set_id") == source_set_id,
        "validation_identity_matches": (validation or {}).get("review_id") == review_id
        and (validation or {}).get("source_set_id") == source_set_id,
        "validation_passed": (validation or {}).get("passed") is True,
        "validation_reviewer_ready": (validation or {}).get("reviewer_ready") is True,
        "validation_failed_check_count_zero": validation_summary.get("failed_check_count") == 0,
        "render_manifest_passed": _dict((render_manifest or {}).get("summary")).get("passed")
        is True,
        "authority_inventory_rows_match_matrix": inventory_authority_ids == authority_row_ids,
        "authority_render_rows_match_matrix": render_authority_ids == authority_row_ids,
        "authority_packet_rows_match_matrix": packet_authority_ids == authority_row_ids,
        "forest_render_rows_match_matrix": render_forest_ids == forest_component_ids,
        "forest_packet_rows_match_matrix": packet_forest_ids == forest_component_ids,
        "pdf_header_valid": (
            pdf_path.exists()
            and pdf_path.stat().st_size > 0
            and pdf_path.read_bytes().startswith(b"%PDF-")
        ),
    }
    passed = all(checks.values())
    return _phase(
        "review_packet_index",
        passed=passed,
        reviewer_ready=passed,
        details={
            "row_inventory_path": str(inventory_path),
            "render_manifest_path": str(render_manifest_path),
            "packet_index_path": str(packet_index_path),
            "validation_path": str(validation_path),
            "pdf_path": str(pdf_path),
            "failed_checks": sorted(name for name, passed in checks.items() if not passed),
            "applicable_authority_count": validation_summary.get(
                "applicable_authority_count"
            ),
            "non_applicable_authority_count": validation_summary.get(
                "non_applicable_authority_count"
            ),
            "forest_plan_component_row_count": validation_summary.get(
                "forest_plan_component_row_count"
            ),
            "applicable_standard_count": validation_summary.get(
                "applicable_standard_count"
            ),
            "failure_category_counts": validation_summary.get(
                "failure_category_counts",
                {},
            ),
            **checks,
        },
    )


def _final_qa_certification_phase(
    *,
    review_id: str,
    source_set_id: str,
    final_qa_dir: Path,
) -> dict:
    report_path = final_qa_dir / FINAL_QA_REPORT_FILENAME
    manifest_path = final_qa_dir / FINAL_QA_MANIFEST_FILENAME
    pdf_path = final_qa_dir / FINAL_QA_PDF_FILENAME
    validation_path = final_qa_dir / FINAL_QA_VALIDATION_FILENAME

    report = _read_json_if_exists(report_path)
    manifest = _read_json_if_exists(manifest_path)
    validation = _read_json_if_exists(validation_path)
    pdf_header_valid = (
        pdf_path.exists()
        and pdf_path.stat().st_size > 0
        and pdf_path.read_bytes().startswith(b"%PDF-")
    )
    report_identity_matches = bool(
        report
        and report.get("review_id") == review_id
        and report.get("source_set_id") == source_set_id
    )
    manifest_identity_matches = bool(
        manifest
        and manifest.get("review_id") == review_id
        and manifest.get("source_set_id") == source_set_id
    )
    validation_identity_matches = bool(
        validation
        and validation.get("review_id") == review_id
        and validation.get("source_set_id") == source_set_id
    )
    checks = {
        "report_exists": report is not None,
        "manifest_exists": manifest is not None,
        "pdf_exists": pdf_path.exists(),
        "validation_exists": validation is not None,
        "report_schema_matches": (report or {}).get("schema_version")
        == "east-crazies-final-qa-certification-report-v1",
        "manifest_schema_matches": (manifest or {}).get("schema_version")
        == "east-crazies-final-qa-certification-manifest-v1",
        "validation_schema_matches": (validation or {}).get("schema_version")
        == FINAL_QA_VALIDATION_SCHEMA_VERSION,
        "report_identity_matches": report_identity_matches,
        "manifest_identity_matches": manifest_identity_matches,
        "validation_identity_matches": validation_identity_matches,
        "report_machine_replay_passed": _selector_value(
            report or {},
            "gate_replay_summary.machine_replay_status",
        )
        == "passed",
        "manifest_validation_status_passed": (manifest or {}).get("validation_status")
        == "passed",
        "validation_result_passed": (validation or {}).get("passed") is True,
        "validation_result_no_failed_checks": (validation or {}).get("failed_check_count") == 0,
        "validation_result_check_count_sufficient": _safe_int(
            (validation or {}).get("check_count")
        )
        >= 157,
        "pdf_header_valid": pdf_header_valid,
        "accepted_v1_risk_visible": _selector_value(
            report or {},
            "accepted_v1_risk_ledger.accepted_pending_count",
        )
        == 14,
        "legal_conclusion_boundary": _selector_value(
            report or {},
            "certification_statement.legal_conclusion",
        )
        is False,
    }
    passed = all(checks.values())
    return _phase(
        "final_qa_certification_report",
        passed=passed,
        reviewer_ready=passed,
        details={
            "report_path": str(report_path),
            "manifest_path": str(manifest_path),
            "pdf_path": str(pdf_path),
            "validation_path": str(validation_path),
            "failed_checks": sorted(name for name, passed in checks.items() if not passed),
            "check_count": (validation or {}).get("check_count"),
            "failed_check_count": (validation or {}).get("failed_check_count"),
            "failure_category_counts": (validation or {}).get("failure_category_counts", {}),
            **checks,
        },
    )


def _decision_support_phase(
    *,
    output_dir: Path,
    review_id: str,
    decision_support_dir: Path | None,
) -> dict:
    config_path: Path | None = DECISION_SUPPORT_CONFIG_PATH
    expected_summary_path: Path | None = DECISION_SUPPORT_EXPECTED_SUMMARY_PATH
    if decision_support_dir is not None and decision_support_dir.exists():
        inferred_config, inferred_expected = infer_decision_support_contract_paths(
            decision_support_dir
        )
        config_path = inferred_config or config_path
        expected_summary_path = inferred_expected or expected_summary_path
    try:
        result = validate_ea_consistency_decision_support_report(
            output_dir=output_dir,
            review_id=review_id,
            config_path=config_path,
            expected_summary_path=expected_summary_path,
        )
        summary = result.summary
    except (OSError, ValueError, json.JSONDecodeError) as error:
        summary = {
            "passed": False,
            "reviewer_ready": False,
            "failure_categories": ["stale_artifact"],
            "failure_count": 1,
            "counts": {},
            "checks": [],
            "failures": [{"name": "decision_support_validation_error", "message": str(error)}],
            "report_path": str(
                (decision_support_dir or output_dir / "reviews" / review_id / "decision_support")
                / "ea_consistency_decision_support.json"
            ),
            "markdown_path": str(
                (decision_support_dir or output_dir / "reviews" / review_id / "decision_support")
                / "ea_consistency_decision_support.md"
            ),
            "pdf_path": str(
                (decision_support_dir or output_dir / "reviews" / review_id / "decision_support")
                / "ea_consistency_decision_support.pdf"
            ),
            "manifest_path": str(
                (decision_support_dir or output_dir / "reviews" / review_id / "decision_support")
                / "ea_consistency_decision_support_manifest.json"
            ),
            "pdf_header_valid": False,
        }
    return _phase(
        "decision_support_report",
        passed=bool(summary.get("passed")),
        reviewer_ready=bool(summary.get("reviewer_ready")),
        details={
            "report_path": summary.get("report_path"),
            "markdown_path": summary.get("markdown_path"),
            "pdf_path": summary.get("pdf_path"),
            "manifest_path": summary.get("manifest_path"),
            "validation_passed": bool(summary.get("passed")),
            "reviewer_ready": bool(summary.get("reviewer_ready")),
            "pdf_header_valid": bool(summary.get("pdf_header_valid")),
            "failure_categories": summary.get("failure_categories", []),
            "failure_count": summary.get("failure_count", 0),
            "counts": summary.get("counts", {}),
            "failed_checks": _decision_support_failed_check_names(summary),
        },
    )


def _decision_support_failed_check_names(summary: dict[str, Any]) -> list[str]:
    failed_checks = [
        str(check.get("name"))
        for check in _dict_list(summary.get("checks"))
        if check.get("passed") is False
    ]
    failed_checks.extend(
        str(failure.get("name"))
        for failure in _dict_list(summary.get("failures"))
        if failure.get("name")
    )
    return sorted(set(failed_checks))


def _knowledge_graph_phase(
    name: str,
    *,
    validation: dict | None,
    summary: dict | None,
    validation_path: Path | None,
    summary_path: Path | None,
    expected_source_set_id: str,
    expected_review_id: str | None = None,
) -> dict:
    validation_passed = bool(validation and validation.get("passed"))
    summary_validation_passed = bool(summary and summary.get("validation_passed"))
    source_set_matches = bool(
        summary and summary.get("source_set_id") == expected_source_set_id
    )
    review_id_matches = (
        True
        if expected_review_id is None
        else bool(summary and summary.get("review_id") == expected_review_id)
    )
    failed_validation_checks = _failed_check_names(validation)
    failed_validation_check_count = (
        summary.get("failed_validation_check_count")
        if isinstance(summary, dict)
        else None
    )
    passed = (
        validation_passed
        and summary_validation_passed
        and source_set_matches
        and review_id_matches
        and not failed_validation_checks
        and failed_validation_check_count in (None, 0)
    )
    return _phase(
        name,
        passed=passed,
        reviewer_ready=passed,
        details={
            "validation_path": _path_string(validation_path),
            "summary_path": _path_string(summary_path),
            "validation_passed": validation_passed,
            "summary_validation_passed": summary_validation_passed,
            "expected_source_set_id": expected_source_set_id,
            "source_set_id": (summary or {}).get("source_set_id"),
            "source_set_matches": source_set_matches,
            "expected_review_id": expected_review_id,
            "review_id": (summary or {}).get("review_id"),
            "review_id_matches": review_id_matches,
            "validation_check_count": (summary or {}).get("validation_check_count"),
            "failed_validation_check_count": failed_validation_check_count,
            "failed_validation_checks": failed_validation_checks,
            "failure_category_counts": (validation or {}).get(
                "failure_category_counts",
                {},
            ),
            "node_count": (summary or {}).get("node_count", 0),
            "edge_count": (summary or {}).get("edge_count", 0),
            "readiness_blocker_counts": (summary or {}).get(
                "readiness_blocker_counts",
                {},
            ),
            "graph_path": (summary or {}).get("graph_path"),
        },
    )


def _read_applicability_phase_artifacts(
    *,
    authority_universe_path: Path | None,
    package_fact_graph_path: Path | None,
    package_fact_graph_validation_path: Path | None,
    applicability_retrieval_trace_path: Path | None,
    applicability_graph_trace_path: Path | None,
    applicability_trace_diagnostics_path: Path | None,
    applicability_decisions_path: Path | None,
    applicable_authorities_path: Path | None,
    non_applicable_authorities_path: Path | None,
    search_coverage_certificates_path: Path | None,
    applicability_validation_path: Path | None,
    generated_rule_pack_path: Path | None,
    generated_rule_pack_validation_path: Path | None,
) -> dict:
    return {
        "paths": {
            "authority_universe": authority_universe_path,
            "package_fact_graph": package_fact_graph_path,
            "package_fact_graph_validation": package_fact_graph_validation_path,
            "applicability_retrieval_trace": applicability_retrieval_trace_path,
            "applicability_graph_trace": applicability_graph_trace_path,
            "applicability_trace_diagnostics": applicability_trace_diagnostics_path,
            "applicability_decisions": applicability_decisions_path,
            "applicable_authorities": applicable_authorities_path,
            "non_applicable_authorities": non_applicable_authorities_path,
            "search_coverage_certificates": search_coverage_certificates_path,
            "applicability_validation": applicability_validation_path,
            "generated_rule_pack": generated_rule_pack_path,
            "generated_rule_pack_validation": generated_rule_pack_validation_path,
        },
        "authority_universe": _read_json_if_path(authority_universe_path),
        "package_fact_graph": _read_json_if_path(package_fact_graph_path),
        "package_fact_graph_validation": _read_json_if_path(package_fact_graph_validation_path),
        "retrieval_rows": _read_jsonl_if_path(applicability_retrieval_trace_path),
        "graph_rows": _read_jsonl_if_path(applicability_graph_trace_path),
        "trace_diagnostics": _read_json_if_path(applicability_trace_diagnostics_path),
        "decisions": _read_jsonl_if_path(applicability_decisions_path),
        "applicable_authorities": _read_json_if_path(applicable_authorities_path),
        "non_applicable_authorities": _read_json_if_path(non_applicable_authorities_path),
        "search_coverage_certificates": _read_json_if_path(search_coverage_certificates_path),
        "applicability_validation": _read_json_if_path(applicability_validation_path),
        "generated_rule_pack": _read_json_if_path(generated_rule_pack_path),
        "generated_rule_pack_validation": _read_json_if_path(
            generated_rule_pack_validation_path
        ),
    }


def _gold_rule_pack_match_mode(
    *,
    gold_eval: dict,
    expected_rule_pack_id: str | None,
    expected_rule_pack_version: str | None,
    generated_rule_pack: dict,
) -> str | None:
    gold_pair = (gold_eval.get("rule_pack_id"), gold_eval.get("rule_pack_version"))
    expected_pair = (expected_rule_pack_id, expected_rule_pack_version)
    if gold_pair == expected_pair:
        return "direct"
    generated_pair = (
        generated_rule_pack.get("rule_pack_id"),
        generated_rule_pack.get("version"),
    )
    generated_base_pair = (
        generated_rule_pack.get("base_rule_pack_id"),
        generated_rule_pack.get("base_rule_pack_version"),
    )
    if expected_pair == generated_pair and gold_pair == generated_base_pair:
        return "generated_base"
    return None


def _applicability_arbitration_summary(decisions: list[dict]) -> dict:
    status_counts: Counter[str] = Counter()
    effect_counts: Counter[str] = Counter()
    applicable_with_weak_auxiliary = 0
    weak_positive_only = 0
    insufficient_strong_positive = 0
    positive_negative_conflict = 0
    for decision in decisions:
        if not isinstance(decision, dict):
            continue
        status = str(decision.get("status") or "")
        arbitration_status = str(decision.get("arbitration_status") or "not_recorded")
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
        if status == "needs_adjudication" and arbitration_status == "positive_negative_conflict":
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


def _applicability_phase_gates(
    *,
    review_dir: Path,
    source_set_id: str,
    artifacts: dict,
    arbitration_summary: dict,
) -> list[dict]:
    paths = artifacts["paths"]
    authority_universe = artifacts["authority_universe"]
    package_fact_graph = artifacts["package_fact_graph"]
    package_fact_graph_validation = artifacts["package_fact_graph_validation"]
    retrieval_rows = artifacts["retrieval_rows"]
    graph_rows = artifacts["graph_rows"]
    trace_diagnostics = artifacts["trace_diagnostics"]
    decisions = artifacts["decisions"]
    applicable = artifacts["applicable_authorities"]
    non_applicable = artifacts["non_applicable_authorities"]
    coverage = artifacts["search_coverage_certificates"]
    applicability_validation = artifacts["applicability_validation"]
    generated_rule_pack = artifacts["generated_rule_pack"]
    generated_validation = artifacts["generated_rule_pack_validation"]
    candidate_ids = _candidate_authority_ids(authority_universe)
    decision_ids = {
        str(row.get("candidate_authority_id") or "")
        for row in decisions
        if isinstance(row, dict) and row.get("candidate_authority_id")
    }
    applicable_ids = _authority_partition_ids(applicable)
    non_applicable_ids = _authority_partition_ids(non_applicable)
    coverage_ids = {
        str(row.get("coverage_certificate_id") or row.get("certificate_id") or "")
        for row in coverage.get("certificates") or []
        if isinstance(row, dict)
    }
    non_applicable_coverage_gaps = _non_applicable_coverage_gaps(
        non_applicable,
        coverage_ids,
    )
    generated_rules = (
        generated_rule_pack.get("rules")
        if isinstance(generated_rule_pack.get("rules"), list)
        else []
    )
    generated_candidate_ids = {
        candidate_id
        for rule in generated_rules
        if isinstance(rule, dict)
        for candidate_id in [_generated_rule_candidate_id(rule)]
        if candidate_id
    }
    generated_summary = (
        generated_validation.get("summary")
        if isinstance(generated_validation.get("summary"), dict)
        else {}
    )
    validation_hash_gaps = _applicability_validation_hash_gaps(applicability_validation)
    authority_ready = (
        bool(authority_universe)
        and authority_universe.get("schema_version") == "authority-universe-snapshot-v0"
        and authority_universe.get("source_set_id") == source_set_id
        and bool((authority_universe.get("validation") or {}).get("passed"))
    )
    package_ready = (
        bool(package_fact_graph)
        and bool(package_fact_graph_validation)
        and package_fact_graph.get("source_set_id") == source_set_id
        and bool((package_fact_graph_validation.get("validation") or {}).get("passed"))
        and package_fact_graph.get("package_fact_graph_sha256")
        == package_fact_graph_validation.get("package_fact_graph_sha256")
    )
    retrieval_ready = (
        bool(retrieval_rows)
        and bool(trace_diagnostics)
        and bool((trace_diagnostics.get("validation") or {}).get("passed"))
        and _file_hash_matches(
            paths["applicability_retrieval_trace"],
            trace_diagnostics.get("retrieval_trace_sha256"),
        )
    )
    graph_ready = (
        _path_exists(paths["applicability_graph_trace"])
        and bool(trace_diagnostics)
        and _file_hash_matches(
            paths["applicability_graph_trace"],
            trace_diagnostics.get("graph_trace_sha256"),
        )
    )
    determination_ready = (
        bool(decisions)
        and bool(candidate_ids)
        and candidate_ids == decision_ids
        and applicable_ids.union(non_applicable_ids).issubset(candidate_ids)
        and not non_applicable_coverage_gaps
    )
    validation_ready = (
        bool(applicability_validation)
        and applicability_validation.get("source_set_id") == source_set_id
        and bool(applicability_validation.get("passed"))
        and not validation_hash_gaps
    )
    generated_ready = (
        bool(generated_rule_pack)
        and bool(generated_validation)
        and generated_rule_pack.get("source_set_id") == source_set_id
        and bool(generated_validation.get("passed"))
        and generated_summary.get("generated_rule_pack_ready") is True
        and generated_candidate_ids == applicable_ids
        and _file_hash_matches(
            paths["generated_rule_pack"],
            generated_summary.get("expected_generated_rule_pack_sha256")
            or generated_summary.get("generated_rule_pack_sha256"),
        )
    )
    return [
        _phase(
            "authority_universe",
            passed=authority_ready,
            reviewer_ready=authority_ready,
            details={
                "review_dir": str(review_dir),
                "path": _path_string(paths["authority_universe"]),
                "exists": _path_exists(paths["authority_universe"]),
                "source_set_matches": authority_universe.get("source_set_id") == source_set_id,
                "validation_passed": bool(
                    (authority_universe.get("validation") or {}).get("passed")
                ),
                "candidate_authority_count": len(candidate_ids),
            },
        ),
        _phase(
            "package_fact_graph",
            passed=package_ready,
            reviewer_ready=package_ready,
            details={
                "path": _path_string(paths["package_fact_graph"]),
                "validation_path": _path_string(paths["package_fact_graph_validation"]),
                "exists": _path_exists(paths["package_fact_graph"]),
                "validation_exists": _path_exists(paths["package_fact_graph_validation"]),
                "source_set_matches": package_fact_graph.get("source_set_id") == source_set_id,
                "validation_passed": bool(
                    (package_fact_graph_validation.get("validation") or {}).get("passed")
                ),
                "package_fact_graph_hash_matches": package_fact_graph.get(
                    "package_fact_graph_sha256"
                )
                == package_fact_graph_validation.get("package_fact_graph_sha256"),
                "fact_count": len(package_fact_graph.get("nodes") or []),
            },
        ),
        _phase(
            "applicability_retrieval_trace",
            passed=retrieval_ready,
            reviewer_ready=retrieval_ready,
            details={
                "path": _path_string(paths["applicability_retrieval_trace"]),
                "diagnostics_path": _path_string(paths["applicability_trace_diagnostics"]),
                "exists": _path_exists(paths["applicability_retrieval_trace"]),
                "trace_row_count": len(retrieval_rows),
                "validation_passed": bool(
                    (trace_diagnostics.get("validation") or {}).get("passed")
                ),
                "trace_hash_matches": _file_hash_matches(
                    paths["applicability_retrieval_trace"],
                    trace_diagnostics.get("retrieval_trace_sha256"),
                ),
            },
        ),
        _phase(
            "applicability_graph_trace",
            passed=graph_ready,
            reviewer_ready=graph_ready,
            details={
                "path": _path_string(paths["applicability_graph_trace"]),
                "exists": _path_exists(paths["applicability_graph_trace"]),
                "trace_row_count": len(graph_rows),
                "trace_hash_matches": _file_hash_matches(
                    paths["applicability_graph_trace"],
                    trace_diagnostics.get("graph_trace_sha256"),
                ),
            },
        ),
        _phase(
            "applicability_determination",
            passed=determination_ready,
            reviewer_ready=determination_ready,
            details={
                "decisions_path": _path_string(paths["applicability_decisions"]),
                "applicable_authorities_path": _path_string(paths["applicable_authorities"]),
                "non_applicable_authorities_path": _path_string(
                    paths["non_applicable_authorities"]
                ),
                "search_coverage_certificates_path": _path_string(
                    paths["search_coverage_certificates"]
                ),
                "decision_count": len(decisions),
                "candidate_authority_count": len(candidate_ids),
                "all_candidates_decided": candidate_ids == decision_ids,
                "applicable_authority_count": len(applicable_ids),
                "non_applicable_authority_count": len(non_applicable_ids),
                "arbitration_summary": arbitration_summary,
                "non_applicable_coverage_gaps": non_applicable_coverage_gaps,
            },
        ),
        _phase(
            "applicability_validation",
            passed=validation_ready,
            reviewer_ready=validation_ready,
            details={
                "path": _path_string(paths["applicability_validation"]),
                "exists": _path_exists(paths["applicability_validation"]),
                "source_set_matches": applicability_validation.get("source_set_id")
                == source_set_id,
                "passed": bool(applicability_validation.get("passed")),
                "hash_gaps": validation_hash_gaps,
                "failed_checks": _failed_check_names(applicability_validation),
            },
        ),
        _phase(
            "generated_rule_pack",
            passed=generated_ready,
            reviewer_ready=generated_ready,
            details={
                "generated_rule_pack_path": _path_string(paths["generated_rule_pack"]),
                "generated_rule_pack_validation_path": _path_string(
                    paths["generated_rule_pack_validation"]
                ),
                "exists": _path_exists(paths["generated_rule_pack"]),
                "validation_exists": _path_exists(paths["generated_rule_pack_validation"]),
                "source_set_matches": generated_rule_pack.get("source_set_id") == source_set_id,
                "validation_passed": bool(generated_validation.get("passed")),
                "generated_rule_pack_ready": generated_summary.get(
                    "generated_rule_pack_ready"
                ),
                "generated_rule_count": len(generated_rules),
                "applicable_authority_count": len(applicable_ids),
                "generated_rules_match_applicable_authorities": generated_candidate_ids
                == applicable_ids,
                "generated_rule_pack_hash_matches": _file_hash_matches(
                    paths["generated_rule_pack"],
                    generated_summary.get("expected_generated_rule_pack_sha256")
                    or generated_summary.get("generated_rule_pack_sha256"),
                ),
            },
        ),
    ]
