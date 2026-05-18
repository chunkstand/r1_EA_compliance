from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path("config/east_crazies_final_qa_certification_v1.json")
DEFAULT_EXPECTED_SUMMARY_PATH = Path(
    "config/fixtures/final_qa/v1_ecid_final_qa_expected_summary.json"
)

REPORT_FILENAME = "east_crazies_final_qa_certification.json"
MARKDOWN_FILENAME = "east_crazies_final_qa_certification.md"
PDF_FILENAME = "east_crazies_final_qa_certification.pdf"
MANIFEST_FILENAME = "east_crazies_final_qa_certification_manifest.json"
VALIDATION_FILENAME = "east_crazies_final_qa_certification_validation.json"
VALIDATION_SCHEMA_VERSION = "east-crazies-final-qa-certification-validation-v1"
GENERATOR_VERSION = "final-qa-certification-sequence-3"
HUMAN_JUDGMENT_CAVEAT = (
    "This packet supports review but does not replace responsible official, "
    "line officer, counsel, or specialist judgment."
)


@dataclass(frozen=True)
class FinalQACertificationResult:
    summary: dict[str, Any]
    report_path: Path
    markdown_path: Path
    pdf_path: Path
    manifest_path: Path
    validation_path: Path


@dataclass(frozen=True)
class OutputPaths:
    results_dir: Path
    report_path: Path
    markdown_path: Path
    pdf_path: Path
    manifest_path: Path
    validation_path: Path


def run_final_qa_certification(
    *,
    output_dir: Path = Path("source_library"),
    review_id: str | None = None,
    config_path: Path = DEFAULT_CONFIG_PATH,
    expected_summary_path: Path = DEFAULT_EXPECTED_SUMMARY_PATH,
    results_dir: Path | None = None,
) -> FinalQACertificationResult:
    """Generate the final QA packet from existing audited review artifacts."""

    config = _read_json(config_path)
    expected = _read_json(expected_summary_path)
    resolved_review_id = review_id or str(config["review_id"])
    paths = _output_paths(output_dir, resolved_review_id, results_dir)

    input_state = _collect_input_state(
        output_dir=output_dir,
        review_id=resolved_review_id,
        config=config,
        expected=expected,
        config_path=config_path,
        expected_summary_path=expected_summary_path,
    )
    if not _checks_passed(input_state["checks"]):
        summary = _summarize_checks(
            checks=input_state["checks"],
            review_id=resolved_review_id,
            source_set_id=str(config.get("source_set_id", "")),
            paths=paths,
            output_written=False,
        )
        return FinalQACertificationResult(
            summary=summary,
            report_path=paths.report_path,
            markdown_path=paths.markdown_path,
            pdf_path=paths.pdf_path,
            manifest_path=paths.manifest_path,
            validation_path=paths.validation_path,
        )

    report = _build_report(
        config=config,
        expected=expected,
        input_state=input_state,
        paths=paths,
        config_path=config_path,
        expected_summary_path=expected_summary_path,
    )
    manifest = report["manifest"]
    markdown = _render_markdown(report)
    pdf_lines = _pdf_lines(report)

    paths.results_dir.mkdir(parents=True, exist_ok=True)
    _write_json(paths.report_path, report)
    paths.markdown_path.write_text(markdown, encoding="utf-8")
    _write_simple_pdf(paths.pdf_path, pdf_lines)
    _write_json(paths.manifest_path, manifest)

    result = validate_final_qa_certification_report(
        output_dir=output_dir,
        review_id=resolved_review_id,
        config_path=config_path,
        expected_summary_path=expected_summary_path,
        results_dir=paths.results_dir,
        require_validation_result=False,
    )
    result.summary["output_written"] = True
    _write_json(paths.validation_path, _validation_result_payload(result.summary, paths))
    result = validate_final_qa_certification_report(
        output_dir=output_dir,
        review_id=resolved_review_id,
        config_path=config_path,
        expected_summary_path=expected_summary_path,
        results_dir=paths.results_dir,
        require_validation_result=True,
    )
    result.summary["output_written"] = True
    return result


def validate_final_qa_certification_report(
    *,
    output_dir: Path = Path("source_library"),
    review_id: str | None = None,
    config_path: Path = DEFAULT_CONFIG_PATH,
    expected_summary_path: Path = DEFAULT_EXPECTED_SUMMARY_PATH,
    results_dir: Path | None = None,
    require_validation_result: bool = True,
) -> FinalQACertificationResult:
    """Validate an existing generated final QA report family without rewriting it."""

    config = _read_json(config_path)
    expected = _read_json(expected_summary_path)
    resolved_review_id = review_id or str(config["review_id"])
    paths = _output_paths(output_dir, resolved_review_id, results_dir)
    checks: list[dict[str, Any]] = []

    input_state = _collect_input_state(
        output_dir=output_dir,
        review_id=resolved_review_id,
        config=config,
        expected=expected,
        config_path=config_path,
        expected_summary_path=expected_summary_path,
    )
    checks.extend(input_state["checks"])

    report = _load_output_json(paths.report_path, "report", checks)
    manifest = _load_output_json(paths.manifest_path, "manifest", checks)
    markdown = _load_output_text(paths.markdown_path, "markdown", checks)
    pdf_bytes = _load_output_bytes(paths.pdf_path, "pdf", checks)
    validation_result = (
        _load_output_json(paths.validation_path, "validation", checks)
        if require_validation_result
        else None
    )

    if report is not None:
        _validate_report(
            report=report,
            config=config,
            expected=expected,
            paths=paths,
            checks=checks,
            require_validation_result=require_validation_result,
        )
    if manifest is not None:
        _validate_manifest(
            manifest=manifest,
            config=config,
            expected=expected,
            input_state=input_state,
            checks=checks,
        )
    if markdown is not None:
        _validate_rendered_text(
            text=markdown,
            text_kind="markdown",
            config=config,
            checks=checks,
        )
    if pdf_bytes is not None:
        _validate_pdf(pdf_bytes=pdf_bytes, config=config, checks=checks)
    if validation_result is not None:
        _validate_validation_result(
            validation_result=validation_result,
            config=config,
            paths=paths,
            checks=checks,
        )

    summary = _summarize_checks(
        checks=checks,
        review_id=resolved_review_id,
        source_set_id=str(config.get("source_set_id", "")),
        paths=paths,
        output_written=False,
    )
    return FinalQACertificationResult(
        summary=summary,
        report_path=paths.report_path,
        markdown_path=paths.markdown_path,
        pdf_path=paths.pdf_path,
        manifest_path=paths.manifest_path,
        validation_path=paths.validation_path,
    )


def _collect_input_state(
    *,
    output_dir: Path,
    review_id: str,
    config: Mapping[str, Any],
    expected: Mapping[str, Any],
    config_path: Path,
    expected_summary_path: Path,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    data_by_key: dict[str, Any] = {}
    artifact_records: list[dict[str, Any]] = []

    _add_check(
        checks,
        name="config_schema_version",
        passed=config.get("schema_version") == "east-crazies-final-qa-certification-config-v1",
        category="unparseable_required_artifact",
        details={"path": str(config_path), "schema_version": config.get("schema_version")},
    )
    _add_check(
        checks,
        name="expected_summary_schema_version",
        passed=expected.get("schema_version") == config.get("expected_summary_schema_version"),
        category="unparseable_required_artifact",
        details={
            "path": str(expected_summary_path),
            "schema_version": expected.get("schema_version"),
        },
    )
    _add_check(
        checks,
        name="review_id_matches_config",
        passed=review_id == config.get("review_id") == expected.get("review_id"),
        category="review_source_set_mismatch",
        details={
            "requested_review_id": review_id,
            "config_review_id": config.get("review_id"),
            "expected_review_id": expected.get("review_id"),
        },
    )
    _add_check(
        checks,
        name="source_set_matches_expected_summary",
        passed=config.get("source_set_id") == expected.get("source_set_id"),
        category="review_source_set_mismatch",
        details={
            "config_source_set_id": config.get("source_set_id"),
            "expected_source_set_id": expected.get("source_set_id"),
        },
    )

    for gate in config.get("required_gates", []):
        artifact_path = _resolve_artifact_path(gate["artifact_path"], output_dir)
        data = _read_required_json(artifact_path, gate["gate_name"], checks)
        if data is None:
            continue
        data_by_key[gate["gate_name"]] = data
        _validate_identity(
            data=data,
            review_id=review_id,
            source_set_id=str(config["source_set_id"]),
            artifact_key=gate["gate_name"],
            checks=checks,
        )
        actual = _selector_value(data, gate["required_pass_selector"])
        self_reference_allowed = _current_promotion_suite_self_reference_allowed(
            gate=gate,
            data=data,
            expected_counts=(
                expected["expected_counts"]
                if isinstance(expected.get("expected_counts"), Mapping)
                else {}
            ),
        )
        _add_check(
            checks,
            name=f"gate_{gate['gate_name']}_passed",
            passed=actual == gate["expected_value"] or self_reference_allowed,
            category=gate.get("failure_category", "stale_artifact"),
            details={
                "path": str(artifact_path),
                "selector": gate["required_pass_selector"],
                "actual": actual,
                "expected": gate["expected_value"],
                "self_reference_allowed": self_reference_allowed,
            },
        )

    for spec in _input_hash_specs(review_id):
        path = _resolve_artifact_path(spec["path"], output_dir)
        key = spec["hash_key"]
        expected_hash = expected.get("input_hashes", {}).get(key)
        if expected_hash is None:
            _add_check(
                checks,
                name=f"expected_hash_declared_{key}",
                passed=False,
                category="input_hash_mismatch",
                details={"path": spec["path"]},
            )
            continue
        if not path.exists():
            _add_check(
                checks,
                name=f"input_artifact_exists_{spec['artifact_key']}",
                passed=False,
                category="missing_required_artifact",
                details={"path": str(path), "expected_sha256": expected_hash},
            )
            continue
        data_for_hash: dict[str, Any] | None = None
        if path.suffix == ".json":
            data_for_hash = _read_required_json(path, spec["artifact_key"], checks)
            if data_for_hash is not None:
                data_by_key[spec["artifact_key"]] = data_for_hash
        actual_hash = _sha256_file(path)
        outer_gate_hash_drift_allowed = _outer_gate_hash_drift_allowed(
            artifact_key=spec["artifact_key"],
            data=data_for_hash,
            expected=expected,
        )
        _add_check(
            checks,
            name=f"input_hash_matches_{spec['artifact_key']}",
            passed=actual_hash == expected_hash or outer_gate_hash_drift_allowed,
            category="input_hash_mismatch",
            details={
                "path": str(path),
                "actual": actual_hash,
                "expected": expected_hash,
                "outer_gate_hash_drift_allowed": outer_gate_hash_drift_allowed,
            },
        )
        record = {
            "artifact_key": spec["artifact_key"],
            "artifact_path": spec["path"],
            "sha256": actual_hash,
            "expected_sha256": expected_hash,
            "size_bytes": path.stat().st_size,
            "schema_version": None,
        }
        if data_for_hash is not None:
            record["schema_version"] = data_for_hash.get("schema_version")
        artifact_records.append(record)

    _validate_configured_source_selectors(expected, output_dir, checks)
    _validate_required_applicable_authority_rows(
        rows=(
            data_by_key.get("compliance_matrix", {}).get("rows", [])
            if isinstance(data_by_key.get("compliance_matrix"), Mapping)
            else []
        ),
        expected=expected,
        checks=checks,
        source_selector="compliance_matrix.rows",
    )
    actual_counts = _derive_actual_counts(data_by_key, checks)
    _validate_actual_counts(actual_counts, config, checks)
    _validate_source_pdf_header(review_id, output_dir, checks)

    return {
        "checks": checks,
        "data_by_key": data_by_key,
        "artifact_records": artifact_records,
        "actual_counts": actual_counts,
    }


def _build_report(
    *,
    config: Mapping[str, Any],
    expected: Mapping[str, Any],
    input_state: Mapping[str, Any],
    paths: OutputPaths,
    config_path: Path,
    expected_summary_path: Path,
) -> dict[str, Any]:
    data_by_key = input_state["data_by_key"]
    counts = input_state["actual_counts"]
    now = _utc_now()

    gate_results = _gate_results(config, data_by_key)
    accepted_risk = _accepted_v1_risk_ledger(expected, data_by_key)
    finding_rows = _finding_rows_from_matrix(
        data_by_key.get("compliance_matrix", {}),
        fallback=expected["required_fixture_rows"]["applicable_authority"],
    )
    source_set_id = str(config["source_set_id"])
    review_id = str(config["review_id"])

    manifest = {
        "schema_version": config["manifest_schema_version"],
        "generated_at": now,
        "generator_version": GENERATOR_VERSION,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "validation_status": "passed",
        "input_hashes": expected["input_hashes"],
        "input_artifacts": input_state["artifact_records"],
        "config_hashes": {
            "config_path": str(config_path),
            "config_sha256": _sha256_file(config_path),
            "expected_summary_path": str(expected_summary_path),
            "expected_summary_sha256": _sha256_file(expected_summary_path),
        },
        "required_gate_names": config["required_gate_names"],
        "section_dependencies": _section_dependencies(config, expected),
        "output_files": {
            "json": str(paths.report_path),
            "markdown": str(paths.markdown_path),
            "pdf": str(paths.pdf_path),
            "manifest": str(paths.manifest_path),
            "validation": str(paths.validation_path),
        },
        "failure_categories": [],
    }

    report = {
        "schema_version": config["report_schema_version"],
        "report_id": f"{review_id}:final-qa-certification",
        "created_at": now,
        "generator_version": GENERATOR_VERSION,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "manifest": manifest,
        "review_boundary": {
            "review_id": review_id,
            "source_set_id": source_set_id,
            "package_path": _selector_value(
                data_by_key.get("compliance_review", {}),
                "package_path",
            ),
            "review_artifact_root": f"source_library/reviews/{review_id}",
            "final_qa_output_dir": str(paths.results_dir),
            "package_file_count": counts["package_file_count"],
            "package_chunk_count": counts["package_chunk_count"],
            "baseline_source_record_count": counts["baseline_source_record_count"],
            "source_record_boundary": "baseline source records plus generated applicable authorities",
            "package_cache_boundary": "review package manifest and package chunks from audited cache",
            "non_canonical_draft_exclusion": {
                "root_east_crazies_drafts_are_canonical": False,
                "blocked_path_prefixes": config["manual_draft_policy"]["blocked_path_prefixes"],
            },
            "legal_conclusion": False,
        },
        "gate_replay_summary": {
            "machine_replay_status": "passed",
            "gates": gate_results,
            "phase_eval": {
                "passed": _selector_value(data_by_key.get("phase_eval", {}), "passed"),
                "reviewer_ready": _selector_value(
                    data_by_key.get("phase_eval", {}),
                    "reviewer_ready",
                ),
                "count_mode": "baseline_excluding_final_qa_self_reference",
                "phase_count": counts["phase_eval_phase_count"],
                "passed_phase_count": counts["phase_eval_passed_phase_count"],
                "live_phase_count": counts["phase_eval_live_phase_count"],
                "live_passed_phase_count": counts["phase_eval_live_passed_phase_count"],
                "final_qa_self_reference_phase_count": counts[
                    "phase_eval_final_qa_self_reference_phase_count"
                ],
            },
            "current_promotion_suite": {
                "current_promotion_ready": _selector_value(
                    data_by_key.get("promotion_suite", {}),
                    "current_promotion_ready",
                ),
                "count_mode": "baseline_excluding_final_qa_packet_gates",
                "required_current_result_count": counts[
                    "promotion_suite_required_current_result_count"
                ],
                "passed_required_current_result_count": counts[
                    "promotion_suite_passed_required_current_result_count"
                ],
                "live_required_current_result_count": counts[
                    "promotion_suite_live_required_current_result_count"
                ],
                "live_passed_required_current_result_count": counts[
                    "promotion_suite_live_passed_required_current_result_count"
                ],
                "final_qa_current_result_count": counts[
                    "promotion_suite_final_qa_current_result_count"
                ],
                "final_qa_current_passed_result_count": counts[
                    "promotion_suite_final_qa_current_passed_result_count"
                ],
                "expansion_failure_category_counts": _selector_value(
                    data_by_key.get("promotion_suite", {}),
                    "expansion_failure_category_counts",
                ),
            },
        },
        "artifact_freshness_ledger": {
            "artifacts": input_state["artifact_records"],
            "config_path": str(config_path),
            "expected_summary_path": str(expected_summary_path),
        },
        "applicability_partition": {
            "candidate_authority_count": counts["candidate_authority_count"],
            "applicable_authority_count": counts["applicable_authority_count"],
            "non_applicable_authority_count": counts["non_applicable_authority_count"],
            "unresolved_authority_count": counts["unresolved_authority_count"],
            "representative_applicable_authority": expected["required_fixture_rows"][
                "applicable_authority"
            ],
            "non_applicable_boundary_evidence": [
                expected["required_fixture_rows"]["non_applicable_authority"]
            ],
            "search_coverage_supported": True,
        },
        "finding_qa": {
            "generated_rule_count": counts["generated_rule_count"],
            "authority_finding_count": counts["authority_finding_count"],
            "authority_finding_status_counts": counts["authority_finding_status_counts"],
            "rule_claim_link_count": counts["rule_claim_link_count"],
            "rule_claim_gap_count": counts["rule_claim_gap_count"],
            "compliance_matrix_authority_row_count": counts[
                "compliance_matrix_authority_row_count"
            ],
            "findings": finding_rows,
        },
        "forest_plan_qa": {
            "scope_status": _selector_value(
                data_by_key.get("forest_plan_context_summary", {}),
                "scope_status",
            ),
            "reviewer_ready": _selector_value(
                data_by_key.get("forest_plan_context_summary", {}),
                "reviewer_ready",
            ),
            "component_count": counts["forest_plan_component_count"],
            "supported_component_count": counts["forest_plan_supported_component_count"],
            "not_applicable_component_count": counts[
                "forest_plan_not_applicable_component_count"
            ],
            "gap_count": counts["forest_plan_gap_count"],
            "standard_count": counts["forest_plan_standard_count"],
            "applicable_standard_count": counts["applicable_standard_count"],
            "applied_standard_count": counts["applied_standard_count"],
            "component_eval": {
                "passed": _selector_value(
                    data_by_key.get("forest_plan_component_eval_results", {}),
                    "passed",
                ),
                "case_count": counts["forest_plan_component_eval_case_count"],
            },
            "component_eval_passed": True,
            "reviewer_resolution_status": "resolved",
            "applicable_standards": [
                _forest_plan_standard_row(expected["required_fixture_rows"]["forest_plan_standard"])
            ],
        },
        "decision_support_qa": {
            "decision_support_manifest_status": _selector_value(
                data_by_key.get("decision_support_manifest", {}),
                "validation_status",
            ),
            "pdf_header_valid": True,
            "residual_risk_rows": [
                expected["required_fixture_rows"]["decision_support_residual_risk"]
            ],
            "litigation_risk_legal_conclusion_count": counts[
                "litigation_risk_legal_conclusion_count"
            ],
            "legal_conclusion": False,
            "implementation_confirmation_rows": _selector_value(
                data_by_key.get("decision_support_report", {}),
                "implementation_confirmation_checklist",
            )
            or [],
        },
        "review_packet_index_qa": {
            "validation_passed": _selector_value(
                data_by_key.get("review_packet_index_validation", {}),
                "passed",
            ),
            "reviewer_ready": _selector_value(
                data_by_key.get("review_packet_index_validation", {}),
                "reviewer_ready",
            ),
            "row_set_sha256": _selector_value(
                data_by_key.get("review_packet_index_validation", {}),
                "summary.row_set_sha256",
            )
            or _selector_value(data_by_key.get("review_packet_row_inventory", {}), "summary.row_set_sha256"),
            "applicable_authority_count": counts[
                "review_packet_index_applicable_authority_count"
            ],
            "non_applicable_authority_count": counts[
                "review_packet_index_non_applicable_authority_count"
            ],
            "forest_plan_component_row_count": counts[
                "review_packet_index_forest_plan_component_row_count"
            ],
            "applicable_standard_count": counts[
                "review_packet_index_applicable_standard_count"
            ],
            "render_manifest_authority_row_count": counts[
                "review_packet_index_render_manifest_authority_row_count"
            ],
            "render_manifest_forest_plan_row_count": counts[
                "review_packet_index_render_manifest_forest_plan_row_count"
            ],
            "validation_failed_check_count": counts[
                "review_packet_index_validation_failed_check_count"
            ],
            "artifact_path": f"source_library/reviews/{review_id}/review_packet_index/review_packet_index.json",
            "validation_path": (
                f"source_library/reviews/{review_id}/review_packet_index/"
                "review_packet_index_validation.json"
            ),
            "legal_conclusion": False,
        },
        "accepted_v1_risk_ledger": accepted_risk,
        "certification_statement": {
            "machine_replay_status": "passed",
            "legal_conclusion": False,
            "caveat": f"{config['certification_caveat']} {HUMAN_JUDGMENT_CAVEAT}",
            "reviewer_signoff": {
                row["field"]: "" for row in config.get("reviewer_signoff_fields", [])
            },
        },
        "residual_blockers_and_stop_conditions": {
            "blockers": [],
            "stop_conditions": [
                "missing_required_artifact",
                "input_hash_mismatch",
                "count_drift",
                "invalid_report_pdf_header",
                "manual_draft_dependency",
                "legal_conclusion_leak",
            ],
        },
    }
    return report


def _validate_report(
    *,
    report: Mapping[str, Any],
    config: Mapping[str, Any],
    expected: Mapping[str, Any],
    paths: OutputPaths,
    checks: list[dict[str, Any]],
    require_validation_result: bool,
) -> None:
    _add_check(
        checks,
        name="report_schema_version",
        passed=report.get("schema_version") == config.get("report_schema_version"),
        category="unparseable_required_artifact",
        details={"schema_version": report.get("schema_version")},
    )
    _add_check(
        checks,
        name="report_identity_matches_config",
        passed=report.get("review_id") == config.get("review_id")
        and report.get("source_set_id") == config.get("source_set_id"),
        category="review_source_set_mismatch",
        details={
            "review_id": report.get("review_id"),
            "source_set_id": report.get("source_set_id"),
        },
    )

    missing_sections = [section for section in config["section_order"] if section not in report]
    _add_check(
        checks,
        name="report_sections_present",
        passed=not missing_sections,
        category="missing_required_gate_section",
        details={"missing_sections": missing_sections},
    )

    gate_names = {
        gate.get("gate_name")
        for gate in _selector_value(report, "gate_replay_summary.gates") or []
    }
    missing_gate_names = sorted(set(config["required_gate_names"]) - gate_names)
    _add_check(
        checks,
        name="required_gate_sections_present",
        passed=not missing_gate_names,
        category="missing_required_gate_section",
        details={"missing_gate_names": missing_gate_names},
    )

    for row in config.get("required_count_fields", []):
        actual = _selector_value(report, row["source_selector"])
        _add_check(
            checks,
            name=f"report_count_matches_{row['field']}",
            passed=actual == row["expected"],
            category=row.get("failure_category", "count_drift"),
            details={
                "selector": row["source_selector"],
                "actual": actual,
                "expected": row["expected"],
            },
        )

    output_paths = {
        REPORT_FILENAME: paths.report_path,
        MARKDOWN_FILENAME: paths.markdown_path,
        PDF_FILENAME: paths.pdf_path,
        MANIFEST_FILENAME: paths.manifest_path,
        VALIDATION_FILENAME: paths.validation_path,
    }
    for filename in expected.get("required_output_files", []):
        if filename == VALIDATION_FILENAME and not require_validation_result:
            continue
        _add_check(
            checks,
            name=f"required_output_exists_{filename}",
            passed=output_paths[filename].exists(),
            category="missing_required_artifact",
            details={"path": str(output_paths[filename])},
        )

    _add_check(
        checks,
        name="non_applicable_boundary_evidence_present",
        passed=bool(
            _selector_value(report, "applicability_partition.non_applicable_boundary_evidence")
        ),
        category="missing_non_applicable_boundary_evidence",
        details={
            "selector": "applicability_partition.non_applicable_boundary_evidence",
        },
    )
    _add_check(
        checks,
        name="finding_source_selectors_present",
        passed=_rows_have_source_selectors(_selector_value(report, "finding_qa.findings") or []),
        category="missing_citation_or_source_selector",
        details={"selector": "finding_qa.findings"},
    )
    findings = _selector_value(report, "finding_qa.findings") or []
    _add_check(
        checks,
        name="all_authority_findings_carried",
        passed=len(findings)
        == expected["expected_counts"]["authority_finding_count"]
        == _selector_value(report, "finding_qa.authority_finding_count"),
        category="missing_citation_or_source_selector",
        details={
            "finding_row_count": len(findings),
            "expected": expected["expected_counts"]["authority_finding_count"],
        },
    )
    _validate_required_applicable_authority_rows(
        rows=findings,
        expected=expected,
        checks=checks,
        source_selector="finding_qa.findings",
    )
    _add_check(
        checks,
        name="finding_trace_ids_present",
        passed=_finding_trace_ids_present(findings),
        category="missing_citation_or_source_selector",
        details={"selector": "finding_qa.findings[].trace_ids"},
    )
    _add_check(
        checks,
        name="accepted_v1_risk_visible",
        passed=_selector_value(report, "accepted_v1_risk_ledger.accepted_pending_count")
        == expected["accepted_v1_risk_ledger"]["accepted_pending_count"]
        and bool(_selector_value(report, "accepted_v1_risk_ledger.risks")),
        category="accepted_v1_risk_hidden",
        details={"selector": "accepted_v1_risk_ledger"},
    )
    hidden_risks = [
        risk
        for risk in _selector_value(report, "accepted_v1_risk_ledger.risks") or []
        if risk.get("hidden_as_pass_finding") is True
    ]
    _add_check(
        checks,
        name="accepted_v1_risk_not_hidden_as_pass",
        passed=not hidden_risks,
        category="accepted_v1_risk_hidden",
        details={"hidden_count": len(hidden_risks)},
    )
    _add_check(
        checks,
        name="legal_conclusion_not_asserted",
        passed=_selector_value(report, "certification_statement.legal_conclusion") is False
        and _selector_value(report, "decision_support_qa.litigation_risk_legal_conclusion_count")
        == 0,
        category="legal_conclusion_leak",
        details={"selector": "certification_statement.legal_conclusion"},
    )
    caveat = str(_selector_value(report, "certification_statement.caveat") or "")
    _add_check(
        checks,
        name="human_certification_not_overclaimed",
        passed=HUMAN_JUDGMENT_CAVEAT in caveat
        and not _contains_prohibited_phrase(json.dumps(report), config),
        category="human_certification_overclaim",
        details={"caveat_present": HUMAN_JUDGMENT_CAVEAT in caveat},
    )
    _add_check(
        checks,
        name="manual_drafts_not_used_as_sources",
        passed=not _artifact_paths_use_blocked_prefix(report, config),
        category="manual_draft_dependency",
        details={"blocked_prefixes": config["manual_draft_policy"]["blocked_path_prefixes"]},
    )


def _validate_manifest(
    *,
    manifest: Mapping[str, Any],
    config: Mapping[str, Any],
    expected: Mapping[str, Any],
    input_state: Mapping[str, Any],
    checks: list[dict[str, Any]],
) -> None:
    _add_check(
        checks,
        name="manifest_schema_version",
        passed=manifest.get("schema_version") == config.get("manifest_schema_version"),
        category="unparseable_required_artifact",
        details={"schema_version": manifest.get("schema_version")},
    )
    _add_check(
        checks,
        name="manifest_identity_matches_config",
        passed=manifest.get("review_id") == config.get("review_id")
        and manifest.get("source_set_id") == config.get("source_set_id"),
        category="review_source_set_mismatch",
        details={
            "review_id": manifest.get("review_id"),
            "source_set_id": manifest.get("source_set_id"),
        },
    )
    _add_check(
        checks,
        name="manifest_validation_status_passed",
        passed=manifest.get("validation_status") == "passed",
        category="stale_artifact",
        details={"validation_status": manifest.get("validation_status")},
    )
    _add_check(
        checks,
        name="manifest_required_gate_names_match_config",
        passed=manifest.get("required_gate_names") == config.get("required_gate_names"),
        category="missing_required_gate_section",
        details={"required_gate_names": manifest.get("required_gate_names")},
    )
    _add_check(
        checks,
        name="manifest_input_hashes_match_expected",
        passed=manifest.get("input_hashes") == expected.get("input_hashes"),
        category="input_hash_mismatch",
        details={"input_hash_count": len(manifest.get("input_hashes", {}))},
    )
    input_artifact_keys = {
        artifact.get("artifact_key") for artifact in input_state.get("artifact_records", [])
    }
    manifest_artifact_keys = {
        artifact.get("artifact_key") for artifact in manifest.get("input_artifacts", [])
    }
    _add_check(
        checks,
        name="manifest_lists_required_input_artifacts",
        passed=input_artifact_keys <= manifest_artifact_keys,
        category="missing_required_artifact",
        details={"missing": sorted(input_artifact_keys - manifest_artifact_keys)},
    )


def _validate_rendered_text(
    *,
    text: str,
    text_kind: str,
    config: Mapping[str, Any],
    checks: list[dict[str, Any]],
) -> None:
    missing = [
        marker
        for marker in config.get("rendering_requirements", {}).get(
            f"{text_kind}_required_text",
            [],
        )
        if marker not in text
    ]
    _add_check(
        checks,
        name=f"{text_kind}_required_text_present",
        passed=not missing,
        category="missing_required_gate_section",
        details={"missing": missing},
    )
    _add_check(
        checks,
        name=f"{text_kind}_has_no_prohibited_certification_phrase",
        passed=not _contains_prohibited_phrase(text, config),
        category="human_certification_overclaim",
        details={"text_kind": text_kind},
    )


def _validate_pdf(
    *,
    pdf_bytes: bytes,
    config: Mapping[str, Any],
    checks: list[dict[str, Any]],
) -> None:
    header = config.get("rendering_requirements", {}).get("pdf_header", "%PDF-")
    _add_check(
        checks,
        name="pdf_header_valid",
        passed=pdf_bytes.startswith(header.encode("ascii")),
        category="invalid_report_pdf_header",
        details={"expected_header": header},
    )
    text = pdf_bytes.decode("latin-1", errors="ignore")
    missing = [
        marker
        for marker in config.get("rendering_requirements", {}).get(
            "pdf_required_text_markers",
            [],
        )
        if marker not in text
    ]
    _add_check(
        checks,
        name="pdf_required_text_markers_present",
        passed=not missing,
        category="missing_required_gate_section",
        details={"missing": missing},
    )
    _add_check(
        checks,
        name="pdf_has_no_prohibited_certification_phrase",
        passed=not _contains_prohibited_phrase(text, config),
        category="human_certification_overclaim",
        details={},
    )


def _phase_eval_counts_for_packet(phase_eval: Any) -> dict[str, int]:
    live_phase_count = _safe_int(_selector_value(phase_eval, "phase_count"))
    live_passed_phase_count = _safe_int(_selector_value(phase_eval, "passed_phase_count"))
    phases = phase_eval.get("phases", []) if isinstance(phase_eval, Mapping) else []
    final_qa_phase_present_count = int(
        any(
            isinstance(phase, Mapping)
            and phase.get("name") == "final_qa_certification_report"
            for phase in phases
        )
    )
    final_qa_phase_passed_count = int(
        any(
            isinstance(phase, Mapping)
            and phase.get("name") == "final_qa_certification_report"
            and phase.get("passed")
            for phase in phases
        )
    )
    phase_count = live_phase_count - final_qa_phase_present_count
    passed_phase_count = live_passed_phase_count - final_qa_phase_passed_count
    return {
        "phase_count": phase_count,
        "passed_phase_count": passed_phase_count,
        "live_phase_count": live_phase_count,
        "live_passed_phase_count": live_passed_phase_count,
        "final_qa_self_reference_phase_count": final_qa_phase_present_count,
    }


def _promotion_suite_counts_for_packet(promotion: Any) -> dict[str, int]:
    live_required_count = _safe_int(
        _selector_value(promotion, "required_current_result_count")
    )
    live_passed_count = _safe_int(
        _selector_value(promotion, "passed_required_current_result_count")
    )
    final_qa_counts = (
        _final_qa_current_result_counts(promotion)
        if isinstance(promotion, Mapping)
        else {"required": 0, "passed": 0}
    )
    return {
        "required_current_result_count": max(
            live_required_count - final_qa_counts["required"],
            0,
        ),
        "passed_required_current_result_count": max(
            live_passed_count - final_qa_counts["passed"],
            0,
        ),
        "live_required_current_result_count": live_required_count,
        "live_passed_required_current_result_count": live_passed_count,
        "final_qa_current_result_count": final_qa_counts["required"],
        "final_qa_current_passed_result_count": final_qa_counts["passed"],
    }


def _derive_actual_counts(
    data_by_key: Mapping[str, Any],
    checks: list[dict[str, Any]],
) -> dict[str, Any]:
    decision = data_by_key.get("decision_support_report", {})
    compliance = data_by_key.get("compliance_review", {})
    matrix = data_by_key.get("compliance_matrix", {})
    applicability = data_by_key.get("applicability_validation", {})
    component_eval = data_by_key.get("forest_plan_component_eval_results", {})
    phase_eval = data_by_key.get("phase_eval", {})
    promotion = data_by_key.get("promotion_suite", {})
    v1_eval = data_by_key.get("v1_ea_eval", {})
    review_packet_validation = data_by_key.get("review_packet_index_validation", {})
    review_packet_inventory = data_by_key.get("review_packet_row_inventory", {})
    render_manifest = data_by_key.get("compliance_matrix_render_manifest", {})
    phase_eval_counts = _phase_eval_counts_for_packet(phase_eval)
    promotion_counts = _promotion_suite_counts_for_packet(promotion)

    compliance_summary = _summary_or_self(compliance)
    applicability_summary = _summary_or_self(applicability)
    component_eval_summary = _summary_or_self(component_eval)
    matrix_summary = matrix.get("summary", {}) if isinstance(matrix, dict) else {}
    forest_components = (
        _selector_value(matrix_summary, "forest_plan_review.component_evaluation")
        or _selector_value(compliance, "forest_plan_review.component_evaluation")
        or {}
    )
    conditional = v1_eval.get("conditional_adjudication", {}) if isinstance(v1_eval, dict) else {}
    authority_integration = (
        _selector_value(matrix_summary, "authority_integration")
        or _selector_value(compliance, "authority_integration")
        or {}
    )
    review_packet_summary = (
        _selector_value(review_packet_validation, "summary")
        or _selector_value(review_packet_inventory, "summary")
        or {}
    )
    render_manifest_summary = (
        render_manifest.get("summary", {}) if isinstance(render_manifest, Mapping) else {}
    )

    counts = {
        "package_file_count": _selector_value(
            decision,
            "record_and_artifact_inventory.package_file_count",
        ),
        "package_chunk_count": _selector_value(
            decision,
            "record_and_artifact_inventory.package_chunk_count",
        ),
        "baseline_source_record_count": _selector_value(
            compliance_summary,
            "baseline_source_record_count",
        ),
        "candidate_authority_count": applicability_summary.get("candidate_authority_count"),
        "applicable_authority_count": applicability_summary.get("applicable_authority_count"),
        "non_applicable_authority_count": applicability_summary.get(
            "non_applicable_authority_count"
        ),
        "unresolved_authority_count": applicability_summary.get("unresolved_authority_count"),
        "generated_rule_count": _selector_value(
            data_by_key.get("generated_rule_pack_validation", {}),
            "summary.generated_rule_count",
        ),
        "authority_finding_count": _selector_value(compliance_summary, "finding_count"),
        "authority_finding_status_counts": _selector_value(
            compliance_summary,
            "finding_status_counts",
        ),
        "rule_claim_link_count": _selector_value(compliance_summary, "rule_claim_link_count"),
        "rule_claim_gap_count": _selector_value(compliance_summary, "rule_claim_gap_count"),
        "compliance_matrix_authority_row_count": _selector_value(matrix_summary, "row_count"),
        "forest_plan_component_count": forest_components.get("component_count"),
        "forest_plan_supported_component_count": forest_components.get("supported_count"),
        "forest_plan_not_applicable_component_count": forest_components.get(
            "not_applicable_count"
        ),
        "forest_plan_gap_count": forest_components.get("gap_count"),
        "forest_plan_standard_count": forest_components.get("standard_count"),
        "applicable_standard_count": forest_components.get("applicable_standard_count"),
        "applied_standard_count": forest_components.get("applied_standard_count"),
        "forest_plan_component_eval_case_count": component_eval_summary.get("case_count"),
        "phase_eval_phase_count": phase_eval_counts["phase_count"],
        "phase_eval_passed_phase_count": phase_eval_counts["passed_phase_count"],
        "phase_eval_live_phase_count": phase_eval_counts["live_phase_count"],
        "phase_eval_live_passed_phase_count": phase_eval_counts[
            "live_passed_phase_count"
        ],
        "phase_eval_final_qa_self_reference_phase_count": phase_eval_counts[
            "final_qa_self_reference_phase_count"
        ],
        "promotion_suite_required_current_result_count": promotion_counts[
            "required_current_result_count"
        ],
        "promotion_suite_passed_required_current_result_count": promotion_counts[
            "passed_required_current_result_count"
        ],
        "promotion_suite_live_required_current_result_count": promotion_counts[
            "live_required_current_result_count"
        ],
        "promotion_suite_live_passed_required_current_result_count": promotion_counts[
            "live_passed_required_current_result_count"
        ],
        "promotion_suite_final_qa_current_result_count": promotion_counts[
            "final_qa_current_result_count"
        ],
        "promotion_suite_final_qa_current_passed_result_count": promotion_counts[
            "final_qa_current_passed_result_count"
        ],
        "accepted_v1_risk_count": conditional.get("accepted_pending_count"),
        "actual_pending_applicable_count": conditional.get("actual_pending_applicable_count"),
        "litigation_risk_legal_conclusion_count": authority_integration.get(
            "legal_conclusion_count"
        ),
        "review_packet_index_applicable_authority_count": review_packet_summary.get(
            "applicable_authority_count"
        ),
        "review_packet_index_non_applicable_authority_count": review_packet_summary.get(
            "non_applicable_authority_count"
        ),
        "review_packet_index_forest_plan_component_row_count": review_packet_summary.get(
            "forest_plan_component_row_count"
        ),
        "review_packet_index_applicable_standard_count": review_packet_summary.get(
            "applicable_standard_count"
        ),
        "review_packet_index_render_manifest_authority_row_count": render_manifest_summary.get(
            "authority_row_count"
        ),
        "review_packet_index_render_manifest_forest_plan_row_count": (
            render_manifest_summary.get("forest_plan_row_count")
        ),
        "review_packet_index_validation_failed_check_count": review_packet_summary.get(
            "failed_check_count"
        ),
    }
    missing = sorted(key for key, value in counts.items() if value is None)
    _add_check(
        checks,
        name="source_counts_derived_from_artifacts",
        passed=not missing,
        category="count_drift",
        details={"missing_count_fields": missing},
    )
    return counts


def _validate_actual_counts(
    actual_counts: Mapping[str, Any],
    config: Mapping[str, Any],
    checks: list[dict[str, Any]],
) -> None:
    for row in config.get("required_count_fields", []):
        field = row["field"]
        if "." in field:
            actual = _selector_value(actual_counts, field)
        else:
            actual = actual_counts.get(field)
        _add_check(
            checks,
            name=f"source_count_matches_{field}",
            passed=actual == row["expected"],
            category=row.get("failure_category", "count_drift"),
            details={"actual": actual, "expected": row["expected"]},
        )


def _validate_source_pdf_header(
    review_id: str,
    output_dir: Path,
    checks: list[dict[str, Any]],
) -> None:
    path = _resolve_artifact_path(
        f"source_library/reviews/{review_id}/decision_support/"
        "ea_consistency_decision_support.pdf",
        output_dir,
    )
    if not path.exists():
        return
    _add_check(
        checks,
        name="decision_support_pdf_header_valid",
        passed=path.read_bytes().startswith(b"%PDF-"),
        category="invalid_report_pdf_header",
        details={"path": str(path)},
    )
    packet_path = _resolve_artifact_path(
        f"source_library/reviews/{review_id}/review_packet_index/review_packet_index.pdf",
        output_dir,
    )
    if not packet_path.exists():
        return
    _add_check(
        checks,
        name="review_packet_index_pdf_header_valid",
        passed=packet_path.read_bytes().startswith(b"%PDF-"),
        category="invalid_report_pdf_header",
        details={"path": str(packet_path)},
    )


def _validate_configured_source_selectors(
    expected: Mapping[str, Any],
    output_dir: Path,
    checks: list[dict[str, Any]],
) -> None:
    selector_rows: list[Mapping[str, Any]] = []
    fixture_rows = expected.get("required_fixture_rows", {})
    for value in fixture_rows.values():
        if isinstance(value, Mapping):
            selector_rows.append(value)
    for value in expected.get("required_applicable_authority_rows", []):
        if isinstance(value, Mapping):
            selector_rows.append(value)
    ledger = expected.get("accepted_v1_risk_ledger", {})
    if isinstance(ledger, Mapping):
        selector_rows.append(ledger)

    missing_selectors: list[str] = []
    missing_paths: list[str] = []
    blocked_paths: list[str] = []
    for row in selector_rows:
        for selector in row.get("source_selectors", []):
            artifact_path = selector.get("artifact_path")
            if not selector.get("selector"):
                missing_selectors.append(str(artifact_path))
            if artifact_path:
                if artifact_path.startswith("East_Crazies_"):
                    blocked_paths.append(artifact_path)
                resolved = _resolve_artifact_path(artifact_path, output_dir)
                if not resolved.exists():
                    missing_paths.append(str(resolved))
        if row.get("source_artifact_path"):
            artifact_path = row["source_artifact_path"]
            if artifact_path.startswith("East_Crazies_"):
                blocked_paths.append(artifact_path)
            resolved = _resolve_artifact_path(artifact_path, output_dir)
            if not resolved.exists():
                missing_paths.append(str(resolved))
        if row.get("source_selector") is None and row.get("source_artifact_path"):
            missing_selectors.append(row["source_artifact_path"])

    _add_check(
        checks,
        name="configured_source_selectors_present",
        passed=not missing_selectors,
        category="missing_citation_or_source_selector",
        details={"missing_selectors": missing_selectors},
    )
    _add_check(
        checks,
        name="configured_source_selector_artifacts_exist",
        passed=not missing_paths,
        category="missing_required_artifact",
        details={"missing_paths": missing_paths},
    )
    _add_check(
        checks,
        name="configured_source_selectors_exclude_manual_drafts",
        passed=not blocked_paths,
        category="manual_draft_dependency",
        details={"blocked_paths": blocked_paths},
    )


def _gate_results(config: Mapping[str, Any], data_by_key: Mapping[str, Any]) -> list[dict[str, Any]]:
    results = []
    for gate in config.get("required_gates", []):
        data = data_by_key.get(gate["gate_name"], {})
        actual = _selector_value(data, gate["required_pass_selector"])
        results.append(
            {
                "gate_name": gate["gate_name"],
                "artifact_path": gate["artifact_path"],
                "selector": gate["required_pass_selector"],
                "actual": actual,
                "expected": gate["expected_value"],
                "status": "passed" if actual == gate["expected_value"] else "failed",
            }
        )
    return results


def _accepted_v1_risk_ledger(
    expected: Mapping[str, Any],
    data_by_key: Mapping[str, Any],
) -> dict[str, Any]:
    expected_ledger = expected["accepted_v1_risk_ledger"]
    v1_eval = data_by_key.get("v1_ea_eval", {})
    conditional = v1_eval.get("conditional_adjudication", {}) if isinstance(v1_eval, dict) else {}
    risks = []
    for row in conditional.get("pending_results", []):
        risks.append(
            {
                "rule_id": row.get("rule_id"),
                "actual_applicability": row.get("actual_applicability"),
                "actual_status": row.get("actual_status"),
                "classification_rationale": row.get("classification_rationale"),
                "source_record_ids": row.get("actual_source_record_ids", []),
                "hidden_as_pass_finding": False,
                "legal_conclusion": False,
            }
        )
    if not risks:
        for row in expected_ledger.get("representative_pending_rows", []):
            risks.append(
                {
                    **row,
                    "source_record_ids": [],
                    "hidden_as_pass_finding": False,
                    "legal_conclusion": False,
                }
            )

    return {
        "policy_mode": conditional.get("policy_mode", expected_ledger["policy_mode"]),
        "accepted_pending_count": conditional.get(
            "accepted_pending_count",
            expected_ledger["accepted_pending_count"],
        ),
        "actual_pending_count": conditional.get(
            "actual_pending_count",
            expected_ledger["actual_pending_count"],
        ),
        "actual_pending_applicable_count": conditional.get(
            "actual_pending_applicable_count",
            expected_ledger["actual_pending_applicable_count"],
        ),
        "accepted_pending_rule_ids": conditional.get(
            "accepted_pending_rule_ids",
            expected_ledger["accepted_pending_rule_ids"],
        ),
        "source_artifact_path": expected_ledger["source_artifact_path"],
        "source_selector": expected_ledger["source_selector"],
        "risks": risks,
    }


def _forest_plan_standard_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "package_evidence": [
            {
                "citation_label": row["ea_package_citation"],
                "source_selectors": row["source_selectors"],
            }
        ],
        "forest_plan_evidence": [
            {
                "citation_label": row["forest_plan_citation"],
                "source_selectors": row["source_selectors"],
            }
        ],
    }


def _finding_rows_from_matrix(
    matrix: Any,
    *,
    fallback: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows = matrix.get("rows", []) if isinstance(matrix, Mapping) else []
    if not rows:
        return [dict(fallback)]
    findings: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        rule_id = str(row.get("rule_id", ""))
        finding = {
            "row_id": row.get("row_id"),
            "rule_id": rule_id,
            "rule_title": row.get("rule_title"),
            "status": row.get("status"),
            "claim_type": row.get("claim_type"),
            "authority_category": row.get("authority_category"),
            "authority_family_id": row.get("authority_family_id"),
            "authority_family_ids": row.get("authority_family_ids") or [],
            "authority_source_record_id": row.get("authority_source_record_id"),
            "candidate_authority_id": row.get("candidate_authority_id"),
            "applicability_decision_id": row.get("applicability_decision_id"),
            "applicability_mode": row.get("applicability_mode"),
            "applicability_status": row.get("applicability_status"),
            "ea_package_citation": row.get("ea_package_citation"),
            "source_library_citation": row.get("source_library_citation"),
            "source_claim_ids": row.get("source_claim_ids") or [],
            "source_claim_count": row.get("source_claim_count"),
            "source_selectors": [
                {
                    "artifact_path": _matrix_artifact_path(matrix),
                    "selector": f"rows[rule_id={rule_id}]",
                }
            ],
            "trace_ids": {
                "applicability_decision_id": row.get("applicability_decision_id"),
                "candidate_authority_id": row.get("candidate_authority_id"),
                "source_claim_ids": row.get("source_claim_ids") or [],
                "search_coverage_certificate_ids": row.get(
                    "search_coverage_certificate_ids"
                )
                or [],
                "human_adjudication_refs": row.get("human_adjudication_refs") or [],
            },
            "source_pointers": {
                "compliance_matrix": {
                    "artifact_path": _matrix_artifact_path(matrix),
                    "selector": f"rows[rule_id={rule_id}]",
                },
                "ea_package_evidence": _evidence_pointer(row.get("ea_package_evidence")),
                "source_library_evidence": _evidence_pointer(row.get("source_library_evidence")),
            },
        }
        findings.append(finding)
    return findings or [dict(fallback)]


def _matrix_artifact_path(matrix: Any) -> str:
    if isinstance(matrix, Mapping):
        review_id = matrix.get("review_id")
        if review_id:
            return f"source_library/reviews/{review_id}/compliance_matrix.json"
    return "source_library/reviews/<review_id>/compliance_matrix.json"


def _evidence_pointer(evidence: Any) -> dict[str, Any] | None:
    if not isinstance(evidence, Mapping):
        return None
    return {
        "artifact_path": evidence.get("artifact_path"),
        "chunk_id": evidence.get("chunk_id"),
        "citation_label": evidence.get("citation_label"),
        "source_record_id": evidence.get("source_record_id"),
        "artifact_sha256": evidence.get("artifact_sha256"),
        "content_sha256": evidence.get("content_sha256"),
    }


def _section_dependencies(
    config: Mapping[str, Any],
    expected: Mapping[str, Any],
) -> list[dict[str, Any]]:
    selectors = {
        row["source_selector"] for row in config.get("required_count_fields", [])
    }
    return [
        {
            "section": section,
            "count_selectors": sorted(selector for selector in selectors if selector.startswith(section)),
            "required": section in expected.get("required_sections", []),
        }
        for section in config.get("section_order", [])
    ]


def _render_markdown(report: Mapping[str, Any]) -> str:
    counts = report["applicability_partition"]
    findings = report["finding_qa"]
    forest = report["forest_plan_qa"]
    phase = report["gate_replay_summary"]["phase_eval"]
    promotion = report["gate_replay_summary"]["current_promotion_suite"]
    packet = report["review_packet_index_qa"]
    accepted = report["accepted_v1_risk_ledger"]
    lines = [
        "# East Crazies Final QA Certification",
        "",
        "## How To Use This Packet",
        "",
        "Use this packet as deterministic machine QA over the existing audited East Crazy "
        "review artifacts. It is not a new compliance review, legal sufficiency "
        "determination, responsible-official approval, counsel certification, or final "
        "agency decision.",
        "",
        "## Machine Replay Status",
        "",
        f"- Review ID: `{report['review_id']}`",
        f"- Source set: `{report['source_set_id']}`",
        f"- Machine replay status: `{report['gate_replay_summary']['machine_replay_status']}`",
        "- Phase eval baseline excluding final QA self-reference: "
        f"`{phase['passed_phase_count']}/{phase['phase_count']}` phases passed",
        "- Phase eval live gate: "
        f"`{phase['live_passed_phase_count']}/{phase['live_phase_count']}` phases passed",
        "- Current promotion suite baseline excluding final QA packet gates: "
        f"`{promotion['passed_required_current_result_count']}/"
        f"{promotion['required_current_result_count']}` required current results passed",
        "- Current promotion suite live gate: "
        f"`{promotion['live_passed_required_current_result_count']}/"
        f"{promotion['live_required_current_result_count']}` required current results passed",
        "",
        "## Gate Replay Summary",
        "",
    ]
    for gate in report["gate_replay_summary"]["gates"]:
        lines.append(
            f"- `{gate['gate_name']}`: `{gate['status']}` from `{gate['artifact_path']}`"
        )
    lines.extend(
        [
            "",
            "## Artifact Freshness Ledger",
            "",
        ]
    )
    for artifact in report["artifact_freshness_ledger"]["artifacts"]:
        lines.append(
            f"- `{artifact['artifact_key']}`: `{artifact['sha256']}` at "
            f"`{artifact['artifact_path']}`"
        )
    lines.extend(
        [
            "",
            "## Applicability Partition",
            "",
            f"- Candidate authorities: `{counts['candidate_authority_count']}`",
            f"- Applicable authorities: `{counts['applicable_authority_count']}`",
            f"- Non-applicable authorities: `{counts['non_applicable_authority_count']}`",
            f"- Unresolved authorities: `{counts['unresolved_authority_count']}`",
            "",
            "## Finding QA",
            "",
            f"- Generated rules: `{findings['generated_rule_count']}`",
            f"- Authority findings: `{findings['authority_finding_count']}`",
            f"- Pass findings: `{findings['authority_finding_status_counts']['pass']}`",
            f"- Rule-claim links: `{findings['rule_claim_link_count']}`",
            f"- Rule-claim gaps: `{findings['rule_claim_gap_count']}`",
            "",
            "## Forest Plan QA",
            "",
            f"- Scope status: `{forest['scope_status']}`",
            f"- Components: `{forest['component_count']}`",
            f"- Supported components: `{forest['supported_component_count']}`",
            f"- Not-applicable components: `{forest['not_applicable_component_count']}`",
            f"- Applicable standards applied: "
            f"`{forest['applied_standard_count']}/{forest['applicable_standard_count']}`",
            "",
            "## Decision Support QA",
            "",
            "- Decision-support manifest status: "
            f"`{report['decision_support_qa']['decision_support_manifest_status']}`",
            f"- PDF header valid: `{report['decision_support_qa']['pdf_header_valid']}`",
            "- Litigation-risk legal conclusion count: "
            f"`{report['decision_support_qa']['litigation_risk_legal_conclusion_count']}`",
            "",
            "## Review Packet Index QA",
            "",
            f"- Packet validation passed: `{packet['validation_passed']}`",
            f"- Applicable authority rows: `{packet['applicable_authority_count']}`",
            f"- Non-applicable authorities: `{packet['non_applicable_authority_count']}`",
            f"- Forest Plan component rows: `{packet['forest_plan_component_row_count']}`",
            f"- Applicable Forest Plan standards: `{packet['applicable_standard_count']}`",
            "- Render manifest rows: "
            f"`{packet['render_manifest_authority_row_count']}` authority / "
            f"`{packet['render_manifest_forest_plan_row_count']}` Forest Plan",
            "",
            "## Accepted V1 Risk Ledger",
            "",
            f"- Policy mode: `{accepted['policy_mode']}`",
            f"- Accepted pending rows: `{accepted['accepted_pending_count']}`",
            f"- Actual pending applicable rows: `{accepted['actual_pending_applicable_count']}`",
            "",
            "## Reviewer Signoff",
            "",
        ]
    )
    for field in report["certification_statement"]["reviewer_signoff"]:
        lines.append(f"- {field}: ")
    lines.extend(
        [
            "",
            "## Certification Statement",
            "",
            report["certification_statement"]["caveat"],
            "",
            "## Residual Blockers And Stop Conditions",
            "",
            f"- Blockers: `{len(report['residual_blockers_and_stop_conditions']['blockers'])}`",
            "- Root-level `East_Crazies_*` draft exports are not canonical review artifacts.",
        ]
    )
    return "\n".join(lines) + "\n"


def _pdf_lines(report: Mapping[str, Any]) -> list[str]:
    phase = report["gate_replay_summary"]["phase_eval"]
    packet = report["review_packet_index_qa"]
    accepted = report["accepted_v1_risk_ledger"]
    return [
        "East Crazies Final QA Certification",
        "How To Use This Packet",
        "Machine Replay Status",
        f"Review ID: {report['review_id']}",
        f"Source set: {report['source_set_id']}",
        "Phase eval baseline excluding final QA self-reference: "
        f"{phase['passed_phase_count']}/{phase['phase_count']} phases passed",
        "Phase eval live gate: "
        f"{phase['live_passed_phase_count']}/{phase['live_phase_count']} phases passed",
        "Review Packet Index",
        f"Packet authority rows: {packet['applicable_authority_count']}",
        f"Packet Forest Plan rows: {packet['forest_plan_component_row_count']}",
        "Accepted V1 Risk Ledger",
        f"Accepted pending rows: {accepted['accepted_pending_count']}",
        "Reviewer Signoff",
        HUMAN_JUDGMENT_CAVEAT,
    ]


def _write_simple_pdf(path: Path, lines: list[str]) -> None:
    content_lines = ["BT", "/F1 12 Tf", "72 740 Td"]
    for line in lines:
        content_lines.append(f"({_escape_pdf_text(line)}) Tj")
        content_lines.append("0 -18 Td")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length "
        + str(len(stream)).encode("ascii")
        + b" >>\nstream\n"
        + stream
        + b"\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for index, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode("ascii"))
        output.extend(body)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode("ascii")
    )
    path.write_bytes(bytes(output))


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _input_hash_specs(review_id: str) -> list[dict[str, str]]:
    review_root = f"source_library/reviews/{review_id}"
    return [
        {
            "artifact_key": "decision_support_report",
            "hash_key": "decision_support_report_sha256",
            "path": f"{review_root}/decision_support/ea_consistency_decision_support.json",
        },
        {
            "artifact_key": "decision_support_markdown",
            "hash_key": "decision_support_markdown_sha256",
            "path": f"{review_root}/decision_support/ea_consistency_decision_support.md",
        },
        {
            "artifact_key": "decision_support_pdf",
            "hash_key": "decision_support_pdf_sha256",
            "path": f"{review_root}/decision_support/ea_consistency_decision_support.pdf",
        },
        {
            "artifact_key": "decision_support_manifest",
            "hash_key": "decision_support_manifest_sha256",
            "path": f"{review_root}/decision_support/ea_consistency_decision_support_manifest.json",
        },
        {
            "artifact_key": "review_packet_row_inventory",
            "hash_key": "review_packet_row_inventory_sha256",
            "path": f"{review_root}/review_packet_index/review_packet_row_inventory.json",
        },
        {
            "artifact_key": "compliance_matrix_render_manifest",
            "hash_key": "compliance_matrix_render_manifest_sha256",
            "path": f"{review_root}/review_packet_index/compliance_matrix_render_manifest.json",
        },
        {
            "artifact_key": "review_packet_index",
            "hash_key": "review_packet_index_sha256",
            "path": f"{review_root}/review_packet_index/review_packet_index.json",
        },
        {
            "artifact_key": "review_packet_index_validation",
            "hash_key": "review_packet_index_validation_sha256",
            "path": f"{review_root}/review_packet_index/review_packet_index_validation.json",
        },
        {
            "artifact_key": "review_packet_index_pdf",
            "hash_key": "review_packet_index_pdf_sha256",
            "path": f"{review_root}/review_packet_index/review_packet_index.pdf",
        },
        {
            "artifact_key": "v1_ea_eval",
            "hash_key": "v1_ea_eval_results_sha256",
            "path": f"{review_root}/v1_ea_eval_results.json",
        },
        {
            "artifact_key": "phase_eval",
            "hash_key": "phase_eval_results_sha256",
            "path": f"{review_root}/phase_eval_results.json",
        },
        {
            "artifact_key": "promotion_suite",
            "hash_key": "promotion_suite_results_sha256",
            "path": "source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite/"
            "promotion_suite_results.json",
        },
        {
            "artifact_key": "compliance_validation",
            "hash_key": "compliance_validation_sha256",
            "path": f"{review_root}/compliance_validation.json",
        },
        {
            "artifact_key": "applicability_validation",
            "hash_key": "applicability_validation_sha256",
            "path": f"{review_root}/applicability/applicability_validation.json",
        },
        {
            "artifact_key": "generated_rule_pack_validation",
            "hash_key": "generated_rule_pack_validation_sha256",
            "path": f"{review_root}/applicability/generated_rule_pack_validation.json",
        },
        {
            "artifact_key": "compliance_matrix",
            "hash_key": "compliance_matrix_sha256",
            "path": f"{review_root}/compliance_matrix.json",
        },
        {
            "artifact_key": "compliance_matrix_pdf",
            "hash_key": "compliance_matrix_pdf_sha256",
            "path": f"{review_root}/compliance_matrix.pdf",
        },
        {
            "artifact_key": "compliance_review",
            "hash_key": "compliance_review_sha256",
            "path": f"{review_root}/compliance_review.json",
        },
        {
            "artifact_key": "forest_plan_context_summary",
            "hash_key": "forest_plan_context_summary_sha256",
            "path": f"{review_root}/forest_plan_context_summary.json",
        },
        {
            "artifact_key": "forest_plan_component_eval_results",
            "hash_key": "forest_plan_component_eval_results_sha256",
            "path": f"{review_root}/forest_plan_component_eval_results.json",
        },
    ]


def _output_paths(
    output_dir: Path,
    review_id: str,
    results_dir: Path | None,
) -> OutputPaths:
    resolved_results_dir = results_dir or output_dir / "reviews" / review_id / "final_qa"
    return OutputPaths(
        results_dir=resolved_results_dir,
        report_path=resolved_results_dir / REPORT_FILENAME,
        markdown_path=resolved_results_dir / MARKDOWN_FILENAME,
        pdf_path=resolved_results_dir / PDF_FILENAME,
        manifest_path=resolved_results_dir / MANIFEST_FILENAME,
        validation_path=resolved_results_dir / VALIDATION_FILENAME,
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_required_json(
    path: Path,
    artifact_key: str,
    checks: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not path.exists():
        _add_check(
            checks,
            name=f"required_json_exists_{artifact_key}",
            passed=False,
            category="missing_required_artifact",
            details={"path": str(path)},
        )
        return None
    try:
        data = _read_json(path)
    except json.JSONDecodeError as exc:
        _add_check(
            checks,
            name=f"required_json_parseable_{artifact_key}",
            passed=False,
            category="unparseable_required_artifact",
            details={"path": str(path), "error": str(exc)},
        )
        return None
    _add_check(
        checks,
        name=f"required_json_parseable_{artifact_key}",
        passed=True,
        category="unparseable_required_artifact",
        details={"path": str(path)},
    )
    return data


def _load_output_json(
    path: Path,
    artifact_key: str,
    checks: list[dict[str, Any]],
) -> dict[str, Any] | None:
    return _read_required_json(path, f"final_qa_{artifact_key}", checks)


def _load_output_text(
    path: Path,
    artifact_key: str,
    checks: list[dict[str, Any]],
) -> str | None:
    if not path.exists():
        _add_check(
            checks,
            name=f"required_output_exists_{artifact_key}",
            passed=False,
            category="missing_required_artifact",
            details={"path": str(path)},
        )
        return None
    return path.read_text(encoding="utf-8")


def _load_output_bytes(
    path: Path,
    artifact_key: str,
    checks: list[dict[str, Any]],
) -> bytes | None:
    if not path.exists():
        _add_check(
            checks,
            name=f"required_output_exists_{artifact_key}",
            passed=False,
            category="missing_required_artifact",
            details={"path": str(path)},
        )
        return None
    return path.read_bytes()


def _resolve_artifact_path(path: str, output_dir: Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    parts = candidate.parts
    if parts and parts[0] == "source_library":
        return output_dir.joinpath(*parts[1:])
    return candidate


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _selector_value(data: Any, selector: str) -> Any:
    current = data
    for part in selector.split("."):
        if isinstance(current, Mapping):
            current = current.get(part)
        else:
            return None
    return current


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _summary_or_self(data: Any) -> Any:
    if isinstance(data, Mapping) and isinstance(data.get("summary"), Mapping):
        return data["summary"]
    return data


def _validate_identity(
    *,
    data: Mapping[str, Any],
    review_id: str,
    source_set_id: str,
    artifact_key: str,
    checks: list[dict[str, Any]],
) -> None:
    artifact_review_id = data.get("review_id")
    artifact_source_set_id = data.get("source_set_id")
    if artifact_review_id is not None:
        _add_check(
            checks,
            name=f"artifact_review_id_matches_{artifact_key}",
            passed=artifact_review_id == review_id,
            category="review_source_set_mismatch",
            details={"actual": artifact_review_id, "expected": review_id},
        )
    if artifact_source_set_id is not None:
        _add_check(
            checks,
            name=f"artifact_source_set_matches_{artifact_key}",
            passed=artifact_source_set_id == source_set_id,
            category="review_source_set_mismatch",
            details={"actual": artifact_source_set_id, "expected": source_set_id},
        )


def _rows_have_source_selectors(rows: list[Any]) -> bool:
    if not rows:
        return False
    return all(
        isinstance(row, Mapping)
        and bool(row.get("source_selectors"))
        and all(selector.get("artifact_path") and selector.get("selector") for selector in row["source_selectors"])
        for row in rows
    )


def _finding_trace_ids_present(rows: list[Any]) -> bool:
    if not rows:
        return False
    required_fields = {
        "rule_id",
        "candidate_authority_id",
        "applicability_decision_id",
        "source_claim_ids",
    }
    for row in rows:
        if not isinstance(row, Mapping):
            return False
        if not all(row.get(field) for field in required_fields):
            return False
        pointers = row.get("source_pointers")
        if not isinstance(pointers, Mapping):
            return False
        for pointer_key in ("ea_package_evidence", "source_library_evidence"):
            pointer = pointers.get(pointer_key)
            if not isinstance(pointer, Mapping):
                return False
            if not pointer.get("artifact_path") or not pointer.get("chunk_id"):
                return False
    return True


def _validate_required_applicable_authority_rows(
    *,
    rows: Any,
    expected: Mapping[str, Any],
    checks: list[dict[str, Any]],
    source_selector: str,
) -> None:
    required_rows = [
        row
        for row in expected.get("required_applicable_authority_rows", [])
        if isinstance(row, Mapping)
    ]
    if not required_rows:
        return
    row_list = [row for row in rows if isinstance(row, Mapping)] if isinstance(rows, list) else []
    rows_by_rule_id = {
        str(row.get("rule_id")): row
        for row in row_list
        if str(row.get("rule_id") or "").strip()
    }
    missing: list[str] = []
    mismatches: list[dict[str, Any]] = []
    for required in required_rows:
        rule_id = str(required.get("rule_id") or "")
        actual = rows_by_rule_id.get(rule_id)
        if actual is None:
            missing.append(rule_id)
            continue
        mismatch_fields = _required_authority_row_mismatch_fields(
            actual=actual,
            required=required,
        )
        if mismatch_fields:
            mismatches.append({"rule_id": rule_id, "fields": mismatch_fields})
    _add_check(
        checks,
        name="required_applicable_authority_rows_present",
        passed=not missing and not mismatches,
        category="missing_applicable_authority_row",
        details={
            "selector": source_selector,
            "required_rule_ids": [str(row.get("rule_id")) for row in required_rows],
            "missing_rule_ids": missing,
            "mismatches": mismatches,
        },
    )


def _required_authority_row_mismatch_fields(
    *,
    actual: Mapping[str, Any],
    required: Mapping[str, Any],
) -> list[str]:
    mismatch_fields: list[str] = []
    for field in (
        "authority_category",
        "authority_source_record_id",
        "candidate_authority_id",
        "applicability_status",
        "applicability_mode",
    ):
        if field in required and actual.get(field) != required[field]:
            mismatch_fields.append(field)
    if "status" in required:
        actual_status = actual.get("status", actual.get("compliance_status"))
        if actual_status != required["status"]:
            mismatch_fields.append("status")
    if "authority_family_id" in required:
        family_id = str(required["authority_family_id"])
        actual_family_ids = {
            str(item)
            for item in actual.get("authority_family_ids") or []
            if str(item or "").strip()
        }
        if actual.get("authority_family_id") != family_id and family_id not in actual_family_ids:
            mismatch_fields.append("authority_family_id")
    return mismatch_fields


def _artifact_paths_use_blocked_prefix(
    report: Mapping[str, Any],
    config: Mapping[str, Any],
) -> bool:
    blocked_prefixes = tuple(config["manual_draft_policy"]["blocked_path_prefixes"])
    paths: list[str] = []
    for artifact in _selector_value(report, "artifact_freshness_ledger.artifacts") or []:
        if artifact.get("artifact_path"):
            paths.append(artifact["artifact_path"])
    for finding in _selector_value(report, "finding_qa.findings") or []:
        for selector in finding.get("source_selectors", []):
            paths.append(selector.get("artifact_path", ""))
    for risk in _selector_value(report, "decision_support_qa.residual_risk_rows") or []:
        paths.append(risk.get("source_artifact_path", ""))
    return any(Path(path).name.startswith(blocked_prefixes) for path in paths)


def _contains_prohibited_phrase(text: str, config: Mapping[str, Any]) -> bool:
    lowered = text.lower()
    return any(
        phrase.lower() in lowered
        for phrase in config.get("prohibited_certification_phrases", [])
    )


def _checks_passed(checks: list[Mapping[str, Any]]) -> bool:
    return all(check.get("passed") for check in checks)


def _add_check(
    checks: list[dict[str, Any]],
    *,
    name: str,
    passed: bool,
    category: str,
    details: Mapping[str, Any],
) -> None:
    checks.append(
        {
            "name": name,
            "passed": bool(passed),
            "failure_category": None if passed else category,
            "details": dict(details),
        }
    )


def _summarize_checks(
    *,
    checks: list[dict[str, Any]],
    review_id: str,
    source_set_id: str,
    paths: OutputPaths,
    output_written: bool,
) -> dict[str, Any]:
    failed = [check for check in checks if not check.get("passed")]
    failure_categories = Counter(
        check["failure_category"] for check in failed if check.get("failure_category")
    )
    return {
        "passed": not failed,
        "machine_replay_status": "passed" if not failed else "failed",
        "review_id": review_id,
        "source_set_id": source_set_id,
        "check_count": len(checks),
        "passed_check_count": len(checks) - len(failed),
        "failed_check_count": len(failed),
        "failure_category_counts": dict(sorted(failure_categories.items())),
        "report_path": str(paths.report_path),
        "markdown_path": str(paths.markdown_path),
        "pdf_path": str(paths.pdf_path),
        "manifest_path": str(paths.manifest_path),
        "validation_path": str(paths.validation_path),
        "output_written": output_written,
    }


def _validation_result_payload(summary: Mapping[str, Any], paths: OutputPaths) -> dict[str, Any]:
    return {
        "schema_version": VALIDATION_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "generator_version": GENERATOR_VERSION,
        "review_id": summary.get("review_id"),
        "source_set_id": summary.get("source_set_id"),
        "passed": bool(summary.get("passed")),
        "machine_replay_status": summary.get("machine_replay_status"),
        "check_count": summary.get("check_count"),
        "passed_check_count": summary.get("passed_check_count"),
        "failed_check_count": summary.get("failed_check_count"),
        "failure_category_counts": summary.get("failure_category_counts", {}),
        "output_written": bool(summary.get("output_written")),
        "output_files": {
            "json": str(paths.report_path),
            "markdown": str(paths.markdown_path),
            "pdf": str(paths.pdf_path),
            "manifest": str(paths.manifest_path),
            "validation": str(paths.validation_path),
        },
        "output_hashes": _validation_output_hashes(paths),
    }


def _validate_validation_result(
    *,
    validation_result: Mapping[str, Any],
    config: Mapping[str, Any],
    paths: OutputPaths,
    checks: list[dict[str, Any]],
) -> None:
    _add_check(
        checks,
        name="validation_result_schema_version",
        passed=validation_result.get("schema_version") == VALIDATION_SCHEMA_VERSION,
        category="unparseable_required_artifact",
        details={"schema_version": validation_result.get("schema_version")},
    )
    _add_check(
        checks,
        name="validation_result_identity_matches_config",
        passed=validation_result.get("review_id") == config.get("review_id")
        and validation_result.get("source_set_id") == config.get("source_set_id"),
        category="review_source_set_mismatch",
        details={
            "review_id": validation_result.get("review_id"),
            "source_set_id": validation_result.get("source_set_id"),
        },
    )
    _add_check(
        checks,
        name="validation_result_passed",
        passed=validation_result.get("passed") is True
        and validation_result.get("machine_replay_status") == "passed",
        category="stale_artifact",
        details={
            "passed": validation_result.get("passed"),
            "machine_replay_status": validation_result.get("machine_replay_status"),
        },
    )
    _add_check(
        checks,
        name="validation_result_no_failed_checks",
        passed=validation_result.get("failed_check_count") == 0
        and validation_result.get("failure_category_counts") == {},
        category="stale_artifact",
        details={
            "failed_check_count": validation_result.get("failed_check_count"),
            "failure_category_counts": validation_result.get("failure_category_counts"),
        },
    )
    _add_check(
        checks,
        name="validation_result_check_count_sufficient",
        passed=_safe_int(validation_result.get("check_count")) >= 157,
        category="stale_artifact",
        details={"check_count": validation_result.get("check_count")},
    )
    output_files = validation_result.get("output_files") or {}
    expected_files = {
        "json": str(paths.report_path),
        "markdown": str(paths.markdown_path),
        "pdf": str(paths.pdf_path),
        "manifest": str(paths.manifest_path),
        "validation": str(paths.validation_path),
    }
    _add_check(
        checks,
        name="validation_result_output_files_match",
        passed=all(output_files.get(key) == value for key, value in expected_files.items()),
        category="stale_artifact",
        details={"output_files": output_files},
    )
    expected_hashes = _validation_output_hashes(paths)
    actual_hashes = validation_result.get("output_hashes") or {}
    _add_check(
        checks,
        name="validation_result_output_hashes_match",
        passed=all(actual_hashes.get(key) == value for key, value in expected_hashes.items()),
        category="stale_artifact",
        details={"output_hashes": actual_hashes},
    )


def _validation_output_hashes(paths: OutputPaths) -> dict[str, str]:
    hash_paths = {
        "json_sha256": paths.report_path,
        "markdown_sha256": paths.markdown_path,
        "pdf_sha256": paths.pdf_path,
        "manifest_sha256": paths.manifest_path,
    }
    return {
        key: _sha256_file(path)
        for key, path in hash_paths.items()
        if path.exists()
    }


def _outer_gate_hash_drift_allowed(
    *,
    artifact_key: str,
    data: Mapping[str, Any] | None,
    expected: Mapping[str, Any],
) -> bool:
    if artifact_key == "phase_eval":
        return _phase_eval_self_reference_allowed(
            data,
            expected_counts=expected.get("expected_counts", {}),
        )
    if artifact_key == "promotion_suite":
        return _promotion_suite_has_only_final_qa_outer_gates(
            data,
            expected_counts=expected.get("expected_counts", {}),
        )
    return False


def _phase_eval_has_only_final_qa_outer_gate(
    data: Mapping[str, Any] | None,
    *,
    expected_counts: Mapping[str, Any],
) -> bool:
    phases = data.get("phases") if isinstance(data, Mapping) else None
    if not isinstance(phases, list):
        return False
    final_qa_phases = [
        phase
        for phase in phases
        if isinstance(phase, Mapping) and phase.get("name") == "final_qa_certification_report"
    ]
    if len(final_qa_phases) != 1:
        return False
    final_qa_phase = final_qa_phases[0]
    if not final_qa_phase.get("passed") or not final_qa_phase.get("reviewer_ready"):
        return False
    expected_phase_count = _safe_int(expected_counts.get("phase_eval_phase_count"))
    expected_passed_count = _safe_int(expected_counts.get("phase_eval_passed_phase_count"))
    return (
        _safe_int(data.get("phase_count")) == expected_phase_count + 1
        and _safe_int(data.get("passed_phase_count")) == expected_passed_count + 1
        and _safe_int(data.get("reviewer_ready_phase_count")) == expected_passed_count + 1
    )


def _phase_eval_pending_only_final_qa_gate(
    data: Mapping[str, Any] | None,
    *,
    expected_counts: Mapping[str, Any],
) -> bool:
    phases = data.get("phases") if isinstance(data, Mapping) else None
    if not isinstance(phases, list):
        return False
    final_qa_phases = [
        phase
        for phase in phases
        if isinstance(phase, Mapping) and phase.get("name") == "final_qa_certification_report"
    ]
    if len(final_qa_phases) != 1:
        return False
    final_qa_phase = final_qa_phases[0]
    if final_qa_phase.get("passed") or final_qa_phase.get("reviewer_ready"):
        return False
    non_final_qa_phases = [
        phase
        for phase in phases
        if isinstance(phase, Mapping) and phase.get("name") != "final_qa_certification_report"
    ]
    if any(not phase.get("passed") or not phase.get("reviewer_ready") for phase in non_final_qa_phases):
        return False
    expected_phase_count = _safe_int(expected_counts.get("phase_eval_phase_count"))
    expected_passed_count = _safe_int(expected_counts.get("phase_eval_passed_phase_count"))
    return (
        _safe_int(data.get("phase_count")) == expected_phase_count + 1
        and _safe_int(data.get("passed_phase_count")) == expected_passed_count
        and _safe_int(data.get("reviewer_ready_phase_count")) == expected_passed_count
    )


def _phase_eval_self_reference_allowed(
    data: Mapping[str, Any] | None,
    *,
    expected_counts: Mapping[str, Any],
) -> bool:
    return _phase_eval_has_only_final_qa_outer_gate(
        data,
        expected_counts=expected_counts,
    ) or _phase_eval_pending_only_final_qa_gate(
        data,
        expected_counts=expected_counts,
    )


def _promotion_suite_has_only_final_qa_outer_gates(
    data: Mapping[str, Any] | None,
    *,
    expected_counts: Mapping[str, Any],
) -> bool:
    if not isinstance(data, Mapping):
        return False
    expected_required = _safe_int(
        expected_counts.get("promotion_suite_required_current_result_count")
    )
    expected_passed = _safe_int(
        expected_counts.get("promotion_suite_passed_required_current_result_count")
    )
    final_qa_counts = _final_qa_current_result_counts(data)
    if final_qa_counts["required"] != 4:
        return False
    return (
        _safe_int(data.get("required_current_result_count"))
        == expected_required + final_qa_counts["required"]
        and _safe_int(data.get("passed_required_current_result_count"))
        == expected_passed + final_qa_counts["passed"]
    )


def _current_promotion_suite_self_reference_allowed(
    *,
    gate: Mapping[str, Any],
    data: Mapping[str, Any],
    expected_counts: Mapping[str, Any],
) -> bool:
    if gate.get("gate_name") == "phase_eval":
        return _phase_eval_self_reference_allowed(
            data,
            expected_counts=expected_counts,
        )
    if gate.get("gate_name") != "current_promotion_suite":
        return False
    if gate.get("required_pass_selector") != "current_promotion_ready":
        return False
    if gate.get("expected_value") is not True:
        return False
    return _promotion_suite_has_only_final_qa_outer_gates(
        data,
        expected_counts=expected_counts,
    )


def _final_qa_current_result_counts(data: Mapping[str, Any]) -> dict[str, int]:
    counts = {"required": 0, "passed": 0}
    for case in data.get("review_cases", []):
        if not isinstance(case, Mapping) or case.get("id") != "v1-cg-ecid":
            continue
        for result in case.get("results", []):
            if not isinstance(result, Mapping):
                continue
            result_id = str(result.get("id") or "")
            if not result_id.startswith("final_qa_certification_"):
                continue
            if result.get("required_for_current_promotion"):
                counts["required"] += 1
                if result.get("passed"):
                    counts["passed"] += 1
    return counts


def _utc_now() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
