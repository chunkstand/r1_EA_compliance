from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json

from .ea_consistency_decision_support_models import DEFAULT_CONFIG_PATH
from .ea_consistency_decision_support_models import DEFAULT_EXPECTED_SUMMARY_PATH
from .ea_consistency_decision_support_models import _DecisionSupportContext
from .ea_consistency_decision_support_models import _LoadedArtifact
from .ea_consistency_decision_support_models import _dict
from .ea_consistency_decision_support_models import _dict_list
from .ea_consistency_decision_support_models import _read_json
from .ea_consistency_decision_support_models import _record_check
from .ea_consistency_decision_support_models import _resolved_source_library_evidence
from .ea_consistency_decision_support_models import _strings
from .ea_consistency_decision_support_models import _validation_result
from .ea_consistency_decision_support_report import _current_counts
from .ea_consistency_decision_support_report_validation import (
    _validate_required_applicable_authority_rows,
)
from .ea_consistency_decision_support_rendering import _applicable_standard_rows
from .ea_consistency_decision_support_rendering import _forest_findings_by_component
from .ea_consistency_decision_support_rendering import _resolve_selector


_REVIEW_PACKET_BOOTSTRAP_ALLOWED_CHECKS = {
    "decision_support_authority_rows_match_applicability",
    "decision_support_report_exists_and_parses",
    "final_qa_authority_rows_match_applicability",
    "final_qa_report_exists_and_parses",
}


def _load_required_artifacts(
    *,
    output_dir: Path,
    review_dir: Path,
    review_id: str,
    config: dict[str, Any] | None = None,
) -> dict[str, _LoadedArtifact]:
    config = config or {}
    plan_source_record_id = _plan_consistency_source_record_id(config)
    plan_text_candidates = sorted(
        (review_dir / "package" / "extracted_text").glob(f"{plan_source_record_id}_*.txt")
    )
    plan_text_path = (
        plan_text_candidates[0]
        if plan_text_candidates
        else review_dir / "package" / "extracted_text" / f"{plan_source_record_id}_missing.txt"
    )
    review_packet_dir = review_dir / "review_packet_index"
    specs = {
        "package_manifest": (review_dir / "package" / "package_manifest.jsonl", "jsonl", True),
        "package_chunks": (review_dir / "package" / "package_chunks.jsonl", "jsonl", True),
        "compliance_matrix": (review_dir / "compliance_matrix.json", "json", True),
        "compliance_review": (review_dir / "compliance_review.json", "json", True),
        "compliance_matrix_pdf": (review_dir / "compliance_matrix.pdf", "pdf", True),
        "applicability_validation": (
            review_dir / "applicability" / "applicability_validation.json",
            "json",
            True,
        ),
        "applicable_authorities": (
            review_dir / "applicability" / "applicable_authorities.json",
            "json",
            True,
        ),
        "non_applicable_authorities": (
            review_dir / "applicability" / "non_applicable_authorities.json",
            "json",
            True,
        ),
        "search_coverage_certificates": (
            review_dir / "applicability" / "search_coverage_certificates.json",
            "json",
            True,
        ),
        "generated_rule_pack": (
            review_dir / "applicability" / "generated_rule_pack.json",
            "json",
            True,
        ),
        "generated_rule_pack_validation": (
            review_dir / "applicability" / "generated_rule_pack_validation.json",
            "json",
            True,
        ),
        "forest_plan_component_findings": (
            review_dir / "forest_plan_component_findings.json",
            "json",
            True,
        ),
        "forest_plan_applicable_standard_coverage": (
            review_dir / "forest_plan_applicable_standard_coverage.json",
            "json",
            True,
        ),
        "forest_plan_component_eval_results": (
            review_dir / "forest_plan_component_eval_results.json",
            "json",
            _requires_component_eval_contract(config),
        ),
        "forest_plan_context_summary": (
            review_dir / "forest_plan_context_summary.json",
            "json",
            True,
        ),
        "non_applicable_authority_appendix": (
            review_dir / "non_applicable_authority_appendix.json",
            "json",
            True,
        ),
        "non_applicable_authority_appendix_markdown": (
            review_dir / "non_applicable_authority_appendix.md",
            "text",
            True,
        ),
        "authority_reviewer_resolution_report": (
            review_dir / "authority_reviewer_resolution_report.json",
            "json",
            True,
        ),
        "litigation_risk_summary": (review_dir / "litigation_risk_summary.json", "json", True),
        "forest_plan_reviewer_resolution_queue": (
            review_dir / "forest_plan_reviewer_resolution_queue.json",
            "json",
            True,
        ),
        "review_packet_row_inventory": (
            review_packet_dir / "review_packet_row_inventory.json",
            "json",
            True,
        ),
        "compliance_matrix_render_manifest": (
            review_packet_dir / "compliance_matrix_render_manifest.json",
            "json",
            True,
        ),
        "review_packet_index": (
            review_packet_dir / "review_packet_index.json",
            "json",
            True,
        ),
        "review_packet_index_validation": (
            review_packet_dir / "review_packet_index_validation.json",
            "json",
            True,
        ),
        "review_packet_index_pdf": (
            review_packet_dir / "review_packet_index.pdf",
            "pdf",
            True,
        ),
        "plan_consistency_table_text": (plan_text_path, "text", True),
    }
    return {
        key: _load_artifact(key=key, path=path, artifact_type=artifact_type, required=required)
        for key, (path, artifact_type, required) in specs.items()
    }


def _plan_consistency_source_record_id(config: dict[str, Any]) -> str:
    policy = _dict(config.get("forest_plan_consistency_source"))
    return str(policy.get("package_source_record_id") or "EA-PACKAGE-042")


def _requires_component_eval_contract(config: dict[str, Any]) -> bool:
    policy = _dict(config.get("forest_plan_standard_coverage_policy"))
    return bool(policy.get("require_component_eval_contract"))


def _report_paths(report_dir: Path) -> tuple[Path, Path, Path, Path]:
    return (
        report_dir / "ea_consistency_decision_support.json",
        report_dir / "ea_consistency_decision_support.md",
        report_dir / "ea_consistency_decision_support.pdf",
        report_dir / "ea_consistency_decision_support_manifest.json",
    )


def _load_report_artifacts(
    *,
    report_path: Path,
    markdown_path: Path,
    pdf_path: Path,
    manifest_path: Path,
) -> dict[str, _LoadedArtifact]:
    return {
        "report": _load_artifact(
            key="decision_support_report",
            path=report_path,
            artifact_type="json",
            required=True,
        ),
        "markdown": _load_artifact(
            key="decision_support_markdown",
            path=markdown_path,
            artifact_type="text",
            required=True,
        ),
        "pdf": _load_artifact(
            key="decision_support_pdf",
            path=pdf_path,
            artifact_type="pdf",
            required=True,
        ),
        "manifest": _load_artifact(
            key="decision_support_manifest",
            path=manifest_path,
            artifact_type="json",
            required=True,
        ),
    }


def _selected_review_id_for_validation(
    *,
    review_id: str | None,
    config_path: Path | None,
    expected_summary_path: Path | None,
) -> str:
    if review_id:
        return str(review_id)
    for path in (config_path, expected_summary_path):
        if path is None or not Path(path).exists():
            continue
        try:
            payload = _read_json(Path(path))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        candidate = payload.get("review_id")
        if candidate:
            return str(candidate)
    raise ValueError("review_id is required when no readable decision-support contract exists.")


def _resolve_validation_contract_paths(
    *,
    report_artifacts: dict[str, _LoadedArtifact],
    config_path: Path | None,
    expected_summary_path: Path | None,
) -> tuple[Path, Path]:
    inferred_config, inferred_expected = _contract_paths_from_loaded_report(report_artifacts)
    return (
        Path(config_path or inferred_config or DEFAULT_CONFIG_PATH),
        Path(expected_summary_path or inferred_expected or DEFAULT_EXPECTED_SUMMARY_PATH),
    )


def _contract_paths_from_loaded_report(
    report_artifacts: dict[str, _LoadedArtifact],
) -> tuple[Path | None, Path | None]:
    manifest = _dict(report_artifacts.get("manifest").payload if report_artifacts.get("manifest") else None)
    if not manifest:
        report = _dict(report_artifacts.get("report").payload if report_artifacts.get("report") else None)
        manifest = _dict(report.get("manifest"))
    paths_by_key = {
        str(row.get("artifact_key")): Path(str(row.get("artifact_path")))
        for row in _dict_list(manifest.get("source_dependencies"))
        if row.get("artifact_path")
    }
    return (
        paths_by_key.get("decision_support_config"),
        paths_by_key.get("decision_support_expected_summary"),
    )


def _load_artifact(
    *,
    key: str,
    path: Path,
    artifact_type: str,
    required: bool,
) -> _LoadedArtifact:
    if not path.exists():
        return _LoadedArtifact(
            key=key,
            path=path,
            artifact_type=artifact_type,
            required=required,
            payload=None,
            exists=False,
            parse_ok=False,
            sha256=None,
            failure_category="missing_required_artifact" if required else None,
            error=f"Missing required artifact: {path}",
        )
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    try:
        if artifact_type == "json":
            payload = json.loads(raw.decode("utf-8"))
            parse_ok = isinstance(payload, dict)
        elif artifact_type == "jsonl":
            payload = [
                json.loads(line)
                for line in raw.decode("utf-8").splitlines()
                if line.strip()
            ]
            parse_ok = True
        elif artifact_type == "pdf":
            payload = {"pdf_header_valid": raw.startswith(b"%PDF-")}
            parse_ok = bool(payload["pdf_header_valid"])
        else:
            payload = raw.decode("utf-8")
            parse_ok = True
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return _LoadedArtifact(
            key=key,
            path=path,
            artifact_type=artifact_type,
            required=required,
            payload=None,
            exists=True,
            parse_ok=False,
            sha256=digest,
            failure_category="unparseable_required_artifact" if required else None,
            error=str(exc),
        )
    return _LoadedArtifact(
        key=key,
        path=path,
        artifact_type=artifact_type,
        required=required,
        payload=payload,
        exists=True,
        parse_ok=parse_ok,
        sha256=digest,
        failure_category=None if parse_ok else "unparseable_required_artifact",
        error=None if parse_ok else f"Artifact did not parse as {artifact_type}: {path}",
    )


def _validate_inputs(context: _DecisionSupportContext) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for artifact in context.artifacts.values():
        if artifact.required:
            _record_check(
                checks,
                failures,
                name=f"{artifact.key}_exists_and_parses",
                passed=artifact.exists and artifact.parse_ok,
                failure_category=artifact.failure_category or "missing_required_artifact",
                source_selector=artifact.key,
                expected=True,
                actual=artifact.exists and artifact.parse_ok,
                message=artifact.error,
            )

    if failures:
        return _validation_result(checks, failures, counts={})

    counts = _current_counts(context)
    expected_counts = _dict(context.expected.get("expected_counts"))
    review_packet_validation = context.payload("review_packet_index_validation")
    for key, expected_value in expected_counts.items():
        if key == "authority_finding_status_counts":
            actual_value = counts.get(key)
        else:
            actual_value = counts.get(key)
        bootstrap_allowed = _review_packet_count_bootstrap_allowed(
            key=key,
            actual_value=actual_value,
            expected_value=expected_value,
            validation=review_packet_validation,
        )
        _record_check(
            checks,
            failures,
            name=f"{key}_matches_expected",
            passed=actual_value == expected_value or bootstrap_allowed,
            failure_category="count_drift",
            source_selector=f"expected_counts.{key}",
            expected=expected_value,
            actual=actual_value,
        )

    _validate_hashes(context, checks, failures)
    _validate_review_source_set(context, checks, failures)
    _validate_readiness(context, checks, failures)
    _validate_authority_rows(context, checks, failures)
    _validate_review_packet_index(context, checks, failures)
    _validate_non_applicable_boundary(context, checks, failures)
    _validate_forest_plan_standards(context, checks, failures)
    _validate_confirmation_selectors(context, checks, failures)
    _validate_residual_risks(context, checks, failures)
    return _validation_result(checks, failures, counts=counts)


def _validate_hashes(
    context: _DecisionSupportContext,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> None:
    hash_map = {
        "package_manifest_sha256": "package_manifest",
        "package_chunks_sha256": "package_chunks",
        "compliance_matrix_sha256": "compliance_matrix",
        "compliance_review_sha256": "compliance_review",
        "applicability_validation_sha256": "applicability_validation",
        "applicable_authorities_sha256": "applicable_authorities",
        "non_applicable_authorities_sha256": "non_applicable_authorities",
        "search_coverage_certificates_sha256": "search_coverage_certificates",
        "generated_rule_pack_sha256": "generated_rule_pack",
        "generated_rule_pack_validation_sha256": "generated_rule_pack_validation",
        "forest_plan_component_findings_sha256": "forest_plan_component_findings",
        "forest_plan_applicable_standard_coverage_sha256": (
            "forest_plan_applicable_standard_coverage"
        ),
        "forest_plan_component_eval_results_sha256": "forest_plan_component_eval_results",
        "forest_plan_context_summary_sha256": "forest_plan_context_summary",
        "non_applicable_authority_appendix_sha256": "non_applicable_authority_appendix",
        "non_applicable_authority_appendix_markdown_sha256": (
            "non_applicable_authority_appendix_markdown"
        ),
        "authority_reviewer_resolution_report_sha256": (
            "authority_reviewer_resolution_report"
        ),
        "litigation_risk_summary_sha256": "litigation_risk_summary",
        "plan_consistency_table_text_sha256": "plan_consistency_table_text",
    }
    expected_hashes = _dict(context.expected.get("input_hashes"))
    for hash_key, artifact_key in hash_map.items():
        if hash_key not in expected_hashes:
            continue
        actual = context.artifacts[artifact_key].sha256
        _record_check(
            checks,
            failures,
            name=f"{hash_key}_matches_expected",
            passed=actual == expected_hashes[hash_key],
            failure_category="input_hash_mismatch",
            source_selector=f"input_hashes.{hash_key}",
            expected=expected_hashes[hash_key],
            actual=actual,
        )


def _validate_review_source_set(
    context: _DecisionSupportContext,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> None:
    for key, artifact in context.artifacts.items():
        if not isinstance(artifact.payload, dict):
            continue
        review_id = artifact.payload.get("review_id")
        source_set_id = artifact.payload.get("source_set_id")
        if review_id is not None:
            _record_check(
                checks,
                failures,
                name=f"{key}_review_id_matches",
                passed=review_id == context.review_id,
                failure_category="review_source_set_mismatch",
                source_selector=f"{key}.review_id",
                expected=context.review_id,
                actual=review_id,
            )
        if source_set_id is not None:
            _record_check(
                checks,
                failures,
                name=f"{key}_source_set_id_matches",
                passed=source_set_id == context.source_set_id,
                failure_category="review_source_set_mismatch",
                source_selector=f"{key}.source_set_id",
                expected=context.source_set_id,
                actual=source_set_id,
            )


def _validate_readiness(
    context: _DecisionSupportContext,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> None:
    matrix = context.payload("compliance_matrix")
    app_validation = context.payload("applicability_validation")
    generated_validation = context.payload("generated_rule_pack_validation")
    forest_findings = context.payload("forest_plan_component_findings")
    standard_coverage = context.payload("forest_plan_applicable_standard_coverage")
    component_eval = _dict(context.payload("forest_plan_component_eval_results"))
    forest_context = context.payload("forest_plan_context_summary")
    authority_resolution = context.payload("authority_reviewer_resolution_report")
    forest_queue = context.payload("forest_plan_reviewer_resolution_queue")
    risk_summary = context.payload("litigation_risk_summary")
    coverage_policy = _dict(context.config.get("forest_plan_standard_coverage_policy"))
    require_all_standards_applied = coverage_policy.get(
        "require_all_applicable_standards_applied",
        True,
    )
    component_eval_controls_open_standards = (
        require_all_standards_applied is False
        and coverage_policy.get("accepted_basis") == "component_eval_contract_passed"
        and component_eval.get("passed") is True
    )
    readiness_checks = {
        "compliance_matrix_reviewer_ready": (matrix.get("summary") or {}).get(
            "reviewer_ready"
        ),
        "compliance_matrix_validated": (matrix.get("summary") or {}).get("validated"),
        "applicability_validation_passed": app_validation.get("passed"),
        "applicability_reviewer_ready": app_validation.get("reviewer_ready"),
        "generated_rule_pack_ready": app_validation.get("generated_rule_pack_ready"),
        "generated_rule_pack_validation_passed": generated_validation.get("passed"),
        "forest_plan_findings_reviewer_ready": (forest_findings.get("summary") or {}).get(
            "reviewer_ready"
        )
        is True
        or component_eval_controls_open_standards,
        "forest_plan_findings_validation_passed": (forest_findings.get("summary") or {}).get(
            "validation_passed"
        )
        is True
        or component_eval_controls_open_standards,
        "forest_plan_context_reviewer_ready": forest_context.get("reviewer_ready"),
        "forest_plan_context_validation_passed": forest_context.get("validation_passed"),
        "applicable_standards_applied": (
            standard_coverage.get("all_applicable_standards_applied") is True
            or component_eval_controls_open_standards
        ),
        "applicable_standard_coverage_passed": (
            standard_coverage.get("passed") is True or component_eval_controls_open_standards
        ),
        "authority_resolution_clear": (
            authority_resolution.get("summary") or {}
        ).get("pending_resolution_count")
        == 0,
        "forest_plan_resolution_clear": len(forest_queue.get("items") or []) == 0
        or component_eval_controls_open_standards,
        "risk_summary_deterministic_only": (risk_summary.get("summary") or {}).get(
            "deterministic_only"
        ),
        "risk_summary_has_no_legal_conclusions": (
            risk_summary.get("summary") or {}
        ).get("legal_conclusion_count")
        == 0,
    }
    for name, actual in readiness_checks.items():
        _record_check(
            checks,
            failures,
            name=name,
            passed=actual is True,
            failure_category=(
                "reviewer_resolution_open"
                if name.endswith("_clear")
                else "residual_risk_legal_conclusion"
                if name.endswith("legal_conclusions")
                else "stale_artifact"
            ),
            source_selector=name,
            expected=True,
            actual=actual,
        )


def _validate_authority_rows(
    context: _DecisionSupportContext,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> None:
    rows = _dict_list(context.payload("compliance_matrix").get("rows"))
    findings_by_rule = {
        str(finding.get("rule_id")): finding
        for finding in _dict_list(context.payload("compliance_review").get("findings"))
        if finding.get("rule_id")
    }
    evidence_policy = _dict(context.config.get("authority_evidence_policy"))
    allowed_single_evidence_statuses = {
        str(status)
        for status in _strings(evidence_policy.get("allow_single_evidence_statuses"))
    }
    seen: set[str] = set()
    duplicates: list[str] = []
    missing_evidence: list[str] = []
    for row in rows:
        rule_id = str(row.get("rule_id") or "")
        if rule_id in seen:
            duplicates.append(rule_id)
        seen.add(rule_id)
        missing_dual_evidence_allowed = (
            str(row.get("status") or "") in allowed_single_evidence_statuses
        )
        if (
            not row.get("ea_package_evidence")
            or not _resolved_source_library_evidence(row, findings_by_rule.get(rule_id))
        ) and not missing_dual_evidence_allowed:
            missing_evidence.append(rule_id)
    _record_check(
        checks,
        failures,
        name="applicable_authority_rows_unique",
        passed=not duplicates,
        failure_category="duplicate_applicable_authority_row",
        source_selector="compliance_matrix.rows.rule_id",
        expected=[],
        actual=duplicates,
    )
    _record_check(
        checks,
        failures,
        name="applicable_authority_rows_have_dual_evidence",
        passed=not missing_evidence,
        failure_category="applicable_authority_missing_dual_evidence",
        source_selector="compliance_matrix.rows.evidence",
        expected=[],
        actual=missing_evidence,
    )
    _validate_required_applicable_authority_rows(
        rows=rows,
        expected=context.expected,
        checks=checks,
        failures=failures,
        source_selector="compliance_matrix.rows",
    )


def _validate_review_packet_index(
    context: _DecisionSupportContext,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> None:
    matrix = context.payload("compliance_matrix")
    inventory = context.payload("review_packet_row_inventory")
    render_manifest = context.payload("compliance_matrix_render_manifest")
    packet_index = context.payload("review_packet_index")
    validation = context.payload("review_packet_index_validation")
    matrix_rows = _dict_list(matrix.get("rows"))
    expected_authority_ids = {str(row.get("rule_id")) for row in matrix_rows if row.get("rule_id")}
    inventory_authority_ids = {
        str(row.get("rule_id"))
        for row in _dict_list(inventory.get("applicable_authority_rows"))
        if row.get("rule_id")
    }
    packet_authority_ids = {
        str(row.get("rule_id"))
        for row in _dict_list(packet_index.get("applicable_authority_rows"))
        if row.get("rule_id")
    }
    render_authority_ids = {
        str(_dict(row.get("row_identity")).get("rule_id"))
        for row in _dict_list(render_manifest.get("rows"))
        if row.get("row_class") == "applicable_authority"
        and _dict(row.get("row_identity")).get("rule_id")
    }
    forest_matrix_ids = {
        str(row.get("component_id"))
        for row in _dict_list(_dict(matrix.get("forest_plan_compliance")).get("rows"))
        if row.get("component_id")
    }
    inventory_forest_ids = {
        str(row.get("component_id"))
        for row in _dict_list(inventory.get("forest_plan_component_rows"))
        if row.get("component_id")
    }
    packet_forest_ids = {
        str(row.get("component_id"))
        for row in _dict_list(packet_index.get("forest_plan_component_rows"))
        if row.get("component_id")
    }
    render_forest_ids = {
        str(_dict(row.get("row_identity")).get("component_id"))
        for row in _dict_list(render_manifest.get("rows"))
        if row.get("row_class") == "forest_plan_component"
        and _dict(row.get("row_identity")).get("component_id")
    }
    packet_summary = _dict(packet_index.get("row_inventory_summary"))
    validation_summary = _dict(validation.get("summary"))
    bootstrap_allowed = _review_packet_bootstrap_allowed(validation)
    readiness_checks = {
        "review_packet_index_validation_passed": (
            validation.get("passed") is True or bootstrap_allowed
        ),
        "review_packet_index_validation_reviewer_ready": (
            validation.get("reviewer_ready") is True or bootstrap_allowed
        ),
        "review_packet_index_validation_no_failed_checks": (
            validation_summary.get("failed_check_count") == 0 or bootstrap_allowed
        ),
        "review_packet_index_schema_matches": (
            packet_index.get("schema_version") == "review-packet-index-v1"
        ),
        "review_packet_row_inventory_schema_matches": (
            inventory.get("schema_version") == "review-packet-row-inventory-v1"
        ),
        "compliance_matrix_render_manifest_schema_matches": (
            render_manifest.get("schema_version") == "compliance-matrix-render-manifest-v1"
        ),
        "compliance_matrix_render_manifest_passed": (
            _dict(render_manifest.get("summary")).get("passed") is True
        ),
    }
    for name, passed in readiness_checks.items():
        _record_check(
            checks,
            failures,
            name=name,
            passed=passed,
            failure_category="missing_packet_index_row"
            if name.startswith("review_packet")
            else "missing_matrix_render_row",
            source_selector=f"review_packet_index.{name}",
            expected=True,
            actual=passed,
        )
    row_sets = {
        "inventory": inventory_authority_ids,
        "render_manifest": render_authority_ids,
        "packet_index": packet_authority_ids,
    }
    for name, row_ids in row_sets.items():
        _record_check(
            checks,
            failures,
            name=f"{name}_authority_rows_match_compliance_matrix",
            passed=row_ids == expected_authority_ids,
            failure_category=(
                "missing_matrix_render_row"
                if name == "render_manifest"
                else "missing_packet_index_row"
            ),
            source_selector=f"review_packet_index.{name}.authority_rows",
            expected=sorted(expected_authority_ids),
            actual={
                "missing": sorted(expected_authority_ids - row_ids),
                "extra": sorted(row_ids - expected_authority_ids),
            },
        )
    forest_sets = {
        "inventory": inventory_forest_ids,
        "render_manifest": render_forest_ids,
        "packet_index": packet_forest_ids,
    }
    for name, row_ids in forest_sets.items():
        _record_check(
            checks,
            failures,
            name=f"{name}_forest_plan_rows_match_compliance_matrix",
            passed=row_ids == forest_matrix_ids,
            failure_category=(
                "missing_matrix_render_row"
                if name == "render_manifest"
                else "missing_forest_plan_row"
            ),
            source_selector=f"review_packet_index.{name}.forest_plan_rows",
            expected=sorted(forest_matrix_ids),
            actual={
                "missing": sorted(forest_matrix_ids - row_ids),
                "extra": sorted(row_ids - forest_matrix_ids),
            },
        )
    _record_check(
        checks,
        failures,
        name="review_packet_non_applicable_boundary_present",
        passed=packet_summary.get("non_applicable_authority_count", 0) > 0,
        failure_category="missing_non_applicable_boundary",
        source_selector="review_packet_index.non_applicable_authority_boundary",
        expected="non-applicable boundary rows",
        actual=packet_summary.get("non_applicable_authority_count"),
    )


def _review_packet_bootstrap_allowed(validation: dict[str, Any]) -> bool:
    failed_checks = {
        str(check.get("name") or "")
        for check in _dict_list(validation.get("checks"))
        if check.get("passed") is False
    }
    return bool(failed_checks) and failed_checks <= _REVIEW_PACKET_BOOTSTRAP_ALLOWED_CHECKS


def _review_packet_count_bootstrap_allowed(
    *,
    key: str,
    actual_value: Any,
    expected_value: Any,
    validation: dict[str, Any],
) -> bool:
    return (
        key == "review_packet_index_validation_failed_check_count"
        and expected_value == 0
        and isinstance(actual_value, int)
        and actual_value >= 0
        and _review_packet_bootstrap_allowed(validation)
    )


def _validate_non_applicable_boundary(
    context: _DecisionSupportContext,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> None:
    non_applicable = _dict_list(context.payload("non_applicable_authorities").get("authorities"))
    certificates = _dict_list(context.payload("search_coverage_certificates").get("certificates"))
    certificates_by_id = {
        str(certificate.get("coverage_certificate_id")): certificate
        for certificate in certificates
    }
    missing_coverage: list[str] = []
    for authority in non_applicable:
        certificate_ids = _strings(authority.get("search_coverage_certificate_ids"))
        if not certificate_ids or any(cid not in certificates_by_id for cid in certificate_ids):
            missing_coverage.append(str(authority.get("candidate_authority_id")))
    _record_check(
        checks,
        failures,
        name="non_applicable_authorities_have_search_coverage",
        passed=not missing_coverage,
        failure_category="non_applicable_missing_search_coverage",
        source_selector="non_applicable_authorities.authorities",
        expected=[],
        actual=missing_coverage,
    )


def _validate_forest_plan_standards(
    context: _DecisionSupportContext,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> None:
    coverage_policy = _dict(context.config.get("forest_plan_standard_coverage_policy"))
    require_all_standards_applied = coverage_policy.get(
        "require_all_applicable_standards_applied",
        True,
    )
    findings_by_component = _forest_findings_by_component(context)
    missing: list[str] = []
    for standard in _applicable_standard_rows(context):
        component_id = str(standard.get("component_id"))
        finding = findings_by_component.get(component_id, {})
        if not finding.get("package_evidence") or not finding.get("plan_source_evidence"):
            missing.append(str(standard.get("component_key") or component_id))
    _record_check(
        checks,
        failures,
        name="applicable_standards_have_package_and_plan_evidence",
        passed=not missing or require_all_standards_applied is False,
        failure_category="applicable_standard_missing_evidence",
        source_selector="forest_plan_applicable_standard_coverage.standards",
        expected=[],
        actual=missing,
    )


def _validate_confirmation_selectors(
    context: _DecisionSupportContext,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> None:
    unresolved: list[str] = []
    for confirmation in _dict_list(context.config.get("implementation_confirmations")):
        for selector in _dict_list(confirmation.get("source_selectors")):
            if selector.get("required") is not True:
                continue
            if not _resolve_selector(context, selector):
                unresolved.append(
                    f"{confirmation.get('confirmation_id')}:{selector.get('selector')}"
                )
    _record_check(
        checks,
        failures,
        name="implementation_confirmation_selectors_resolve",
        passed=not unresolved,
        failure_category="implementation_confirmation_selector_unresolved",
        source_selector="config.implementation_confirmations.source_selectors",
        expected=[],
        actual=unresolved,
    )


def _validate_residual_risks(
    context: _DecisionSupportContext,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
) -> None:
    invalid = [
        str(rule.get("risk_source_id"))
        for rule in _dict_list(context.config.get("residual_risk_rules"))
        if rule.get("legal_conclusion") is not False
    ]
    _record_check(
        checks,
        failures,
        name="residual_risk_rules_are_not_legal_conclusions",
        passed=not invalid,
        failure_category="residual_risk_legal_conclusion",
        source_selector="config.residual_risk_rules",
        expected=[],
        actual=invalid,
    )
