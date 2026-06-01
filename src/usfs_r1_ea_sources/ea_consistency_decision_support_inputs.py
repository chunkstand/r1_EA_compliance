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
from .ea_consistency_decision_support_models import _validation_result
from .ea_consistency_decision_support_input_validation import (
    _review_packet_bootstrap_allowed as _review_packet_bootstrap_allowed,
)
from .ea_consistency_decision_support_input_validation import (
    _review_packet_count_bootstrap_allowed,
)
from .ea_consistency_decision_support_input_validation import _validate_authority_rows
from .ea_consistency_decision_support_input_validation import _validate_confirmation_selectors
from .ea_consistency_decision_support_input_validation import _validate_forest_plan_standards
from .ea_consistency_decision_support_input_validation import _validate_hashes
from .ea_consistency_decision_support_input_validation import _validate_non_applicable_boundary
from .ea_consistency_decision_support_input_validation import _validate_readiness
from .ea_consistency_decision_support_input_validation import _validate_residual_risks
from .ea_consistency_decision_support_input_validation import _validate_review_packet_index
from .ea_consistency_decision_support_input_validation import _validate_review_source_set
from .ea_consistency_decision_support_report import _current_counts


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
