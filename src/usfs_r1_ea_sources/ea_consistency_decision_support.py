from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import hashlib
import json
import textwrap


REPORT_SCHEMA_VERSION = "ea-consistency-decision-support-report-v1"
MANIFEST_SCHEMA_VERSION = "ea-consistency-decision-support-manifest-v1"
GENERATOR_VERSION = "ea-consistency-decision-support-generator-v1"
DEFAULT_CONFIG_PATH = Path("config/ea_consistency_decision_support_v1.json")
DEFAULT_EXPECTED_SUMMARY_PATH = Path(
    "config/fixtures/decision_support/v1_ecid_decision_support_expected_summary.json"
)


@dataclass(frozen=True)
class EAConsistencyDecisionSupportResult:
    output_dir: Path
    report_path: Path
    markdown_path: Path
    pdf_path: Path
    manifest_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class EAConsistencyDecisionSupportValidationResult:
    output_dir: Path
    report_path: Path
    markdown_path: Path
    pdf_path: Path
    manifest_path: Path
    summary: dict[str, Any]


def run_ea_consistency_decision_support(
    *,
    output_dir: Path = Path("source_library"),
    review_id: str | None = None,
    config_path: Path = DEFAULT_CONFIG_PATH,
    expected_summary_path: Path = DEFAULT_EXPECTED_SUMMARY_PATH,
    results_dir: Path | None = None,
) -> EAConsistencyDecisionSupportResult:
    output_dir = Path(output_dir)
    config_path = Path(config_path)
    expected_summary_path = Path(expected_summary_path)
    config = _read_json(config_path)
    expected = _read_json(expected_summary_path)
    selected_review_id = str(review_id or config.get("review_id") or expected["review_id"])
    source_set_id = str(config.get("source_set_id") or expected["source_set_id"])
    review_dir = output_dir / "reviews" / selected_review_id
    report_dir = Path(results_dir) if results_dir is not None else review_dir / "decision_support"
    report_path = report_dir / "ea_consistency_decision_support.json"
    markdown_path = report_dir / "ea_consistency_decision_support.md"
    pdf_path = report_dir / "ea_consistency_decision_support.pdf"
    manifest_path = report_dir / "ea_consistency_decision_support_manifest.json"

    artifacts = _load_required_artifacts(
        output_dir=output_dir,
        review_dir=review_dir,
        review_id=selected_review_id,
    )
    context = _DecisionSupportContext(
        output_dir=output_dir,
        review_dir=review_dir,
        review_id=selected_review_id,
        source_set_id=source_set_id,
        config_path=config_path,
        expected_summary_path=expected_summary_path,
        config=config,
        expected=expected,
        artifacts=artifacts,
    )
    validation = _validate_inputs(context)
    summary = _generation_summary(
        context=context,
        report_dir=report_dir,
        report_path=report_path,
        markdown_path=markdown_path,
        pdf_path=pdf_path,
        manifest_path=manifest_path,
        validation=validation,
    )
    if not validation["passed"]:
        return EAConsistencyDecisionSupportResult(
            output_dir=report_dir,
            report_path=report_path,
            markdown_path=markdown_path,
            pdf_path=pdf_path,
            manifest_path=manifest_path,
            summary=summary,
        )

    report = _build_report(context, validation)
    markdown = _report_markdown(report)
    pdf_pages = _report_pdf_pages(report)
    report_dir.mkdir(parents=True, exist_ok=True)
    _write_json(report_path, report)
    markdown_path.write_text(markdown, encoding="utf-8")
    _write_simple_pdf(pdf_path, pdf_pages, title="EA Consistency Decision Support")
    _write_json(manifest_path, report["manifest"])
    summary["output_written"] = True
    summary["pdf_header_valid"] = pdf_path.read_bytes().startswith(b"%PDF-")
    return EAConsistencyDecisionSupportResult(
        output_dir=report_dir,
        report_path=report_path,
        markdown_path=markdown_path,
        pdf_path=pdf_path,
        manifest_path=manifest_path,
        summary=summary,
    )


def validate_ea_consistency_decision_support_report(
    *,
    output_dir: Path = Path("source_library"),
    review_id: str | None = None,
    config_path: Path | None = DEFAULT_CONFIG_PATH,
    expected_summary_path: Path | None = DEFAULT_EXPECTED_SUMMARY_PATH,
    results_dir: Path | None = None,
) -> EAConsistencyDecisionSupportValidationResult:
    output_dir = Path(output_dir)
    selected_review_id = _selected_review_id_for_validation(
        review_id=review_id,
        config_path=config_path,
        expected_summary_path=expected_summary_path,
    )
    review_dir = output_dir / "reviews" / selected_review_id
    report_dir = Path(results_dir) if results_dir is not None else review_dir / "decision_support"
    report_path, markdown_path, pdf_path, manifest_path = _report_paths(report_dir)
    report_artifacts = _load_report_artifacts(
        report_path=report_path,
        markdown_path=markdown_path,
        pdf_path=pdf_path,
        manifest_path=manifest_path,
    )
    config_path, expected_summary_path = _resolve_validation_contract_paths(
        report_artifacts=report_artifacts,
        config_path=config_path,
        expected_summary_path=expected_summary_path,
    )
    config_artifact = _load_artifact(
        key="decision_support_config",
        path=Path(config_path),
        artifact_type="json",
        required=True,
    )
    expected_artifact = _load_artifact(
        key="decision_support_expected_summary",
        path=Path(expected_summary_path),
        artifact_type="json",
        required=True,
    )
    source_validation: dict[str, Any] | None = None
    context: _DecisionSupportContext | None = None
    source_set_id = _report_source_set_id(report_artifacts)
    if (
        config_artifact.exists
        and config_artifact.parse_ok
        and expected_artifact.exists
        and expected_artifact.parse_ok
    ):
        config = _dict(config_artifact.payload)
        expected = _dict(expected_artifact.payload)
        selected_review_id = str(
            review_id
            or config.get("review_id")
            or expected.get("review_id")
            or selected_review_id
        )
        source_set_id = str(
            config.get("source_set_id")
            or expected.get("source_set_id")
            or source_set_id
            or ""
        )
        review_dir = output_dir / "reviews" / selected_review_id
        report_dir = (
            Path(results_dir) if results_dir is not None else review_dir / "decision_support"
        )
        report_path, markdown_path, pdf_path, manifest_path = _report_paths(report_dir)
        if report_path != report_artifacts["report"].path:
            report_artifacts = _load_report_artifacts(
                report_path=report_path,
                markdown_path=markdown_path,
                pdf_path=pdf_path,
                manifest_path=manifest_path,
            )
        artifacts = _load_required_artifacts(
            output_dir=output_dir,
            review_dir=review_dir,
            review_id=selected_review_id,
        )
        context = _DecisionSupportContext(
            output_dir=output_dir,
            review_dir=review_dir,
            review_id=selected_review_id,
            source_set_id=source_set_id,
            config_path=Path(config_path),
            expected_summary_path=Path(expected_summary_path),
            config=config,
            expected=expected,
            artifacts=artifacts,
        )
        source_validation = _validate_inputs(context)

    summary = _validate_report_artifact_family(
        output_dir=output_dir,
        report_dir=report_dir,
        report_artifacts=report_artifacts,
        config_artifact=config_artifact,
        expected_artifact=expected_artifact,
        context=context,
        source_validation=source_validation,
        selected_review_id=selected_review_id,
        source_set_id=source_set_id,
    )
    return EAConsistencyDecisionSupportValidationResult(
        output_dir=report_dir,
        report_path=report_path,
        markdown_path=markdown_path,
        pdf_path=pdf_path,
        manifest_path=manifest_path,
        summary=summary,
    )


def infer_decision_support_contract_paths(
    report_dir: Path,
) -> tuple[Path | None, Path | None]:
    report_path, _, _, manifest_path = _report_paths(Path(report_dir))
    manifest = None
    if manifest_path.exists():
        try:
            manifest = _read_json(manifest_path)
        except (OSError, ValueError, json.JSONDecodeError):
            manifest = None
    if manifest is None and report_path.exists():
        try:
            report = _read_json(report_path)
            manifest = _dict(report.get("manifest"))
        except (OSError, ValueError, json.JSONDecodeError):
            manifest = None
    if not isinstance(manifest, dict):
        return None, None
    paths_by_key = {
        str(row.get("artifact_key")): Path(str(row.get("artifact_path")))
        for row in _dict_list(manifest.get("source_dependencies"))
        if row.get("artifact_path")
    }
    return (
        paths_by_key.get("decision_support_config"),
        paths_by_key.get("decision_support_expected_summary"),
    )


@dataclass(frozen=True)
class _LoadedArtifact:
    key: str
    path: Path
    artifact_type: str
    required: bool
    payload: Any
    exists: bool
    parse_ok: bool
    sha256: str | None
    failure_category: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class _DecisionSupportContext:
    output_dir: Path
    review_dir: Path
    review_id: str
    source_set_id: str
    config_path: Path
    expected_summary_path: Path
    config: dict[str, Any]
    expected: dict[str, Any]
    artifacts: dict[str, _LoadedArtifact]

    def payload(self, key: str) -> Any:
        return self.artifacts[key].payload


def _load_required_artifacts(
    *,
    output_dir: Path,
    review_dir: Path,
    review_id: str,
) -> dict[str, _LoadedArtifact]:
    plan_text_candidates = sorted(
        (review_dir / "package" / "extracted_text").glob("EA-PACKAGE-042_*.txt")
    )
    plan_text_path = (
        plan_text_candidates[0]
        if plan_text_candidates
        else review_dir / "package" / "extracted_text" / "EA-PACKAGE-042_missing.txt"
    )
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
        "plan_consistency_table_text": (plan_text_path, "text", True),
    }
    return {
        key: _load_artifact(key=key, path=path, artifact_type=artifact_type, required=required)
        for key, (path, artifact_type, required) in specs.items()
    }


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


def _report_source_set_id(report_artifacts: dict[str, _LoadedArtifact]) -> str:
    for key in ("report", "manifest"):
        payload = _dict(report_artifacts.get(key).payload if report_artifacts.get(key) else None)
        if payload.get("source_set_id"):
            return str(payload["source_set_id"])
        manifest = _dict(payload.get("manifest"))
        if manifest.get("source_set_id"):
            return str(manifest["source_set_id"])
    return ""


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
    for key, expected_value in expected_counts.items():
        if key == "authority_finding_status_counts":
            actual_value = counts.get(key)
        else:
            actual_value = counts.get(key)
        _record_check(
            checks,
            failures,
            name=f"{key}_matches_expected",
            passed=actual_value == expected_value,
            failure_category="count_drift",
            source_selector=f"expected_counts.{key}",
            expected=expected_value,
            actual=actual_value,
        )

    _validate_hashes(context, checks, failures)
    _validate_review_source_set(context, checks, failures)
    _validate_readiness(context, checks, failures)
    _validate_authority_rows(context, checks, failures)
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
    forest_context = context.payload("forest_plan_context_summary")
    authority_resolution = context.payload("authority_reviewer_resolution_report")
    forest_queue = context.payload("forest_plan_reviewer_resolution_queue")
    risk_summary = context.payload("litigation_risk_summary")
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
        ),
        "forest_plan_findings_validation_passed": (forest_findings.get("summary") or {}).get(
            "validation_passed"
        ),
        "forest_plan_context_reviewer_ready": forest_context.get("reviewer_ready"),
        "forest_plan_context_validation_passed": forest_context.get("validation_passed"),
        "applicable_standards_applied": standard_coverage.get(
            "all_applicable_standards_applied"
        ),
        "applicable_standard_coverage_passed": standard_coverage.get("passed"),
        "authority_resolution_clear": (
            authority_resolution.get("summary") or {}
        ).get("pending_resolution_count")
        == 0,
        "forest_plan_resolution_clear": len(forest_queue.get("items") or []) == 0,
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
    seen: set[str] = set()
    duplicates: list[str] = []
    missing_evidence: list[str] = []
    for row in rows:
        rule_id = str(row.get("rule_id") or "")
        if rule_id in seen:
            duplicates.append(rule_id)
        seen.add(rule_id)
        if not row.get("ea_package_evidence") or not row.get("source_library_evidence"):
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
        passed=not missing,
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


def _build_report(
    context: _DecisionSupportContext,
    validation: dict[str, Any],
) -> dict[str, Any]:
    counts = validation["counts"]
    manifest = _manifest(context, validation)
    authority_rows = _authority_findings(context)
    component_rows = _forest_plan_component_rows(context)
    standard_rows = _applicable_standards(context)
    non_applicable = _non_applicable_boundary(context)
    confirmations = _implementation_confirmations(context)
    residual_risks = _residual_risks(context)
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "report_id": f"ea-consistency-decision-support:{context.review_id}",
        "review_id": context.review_id,
        "source_set_id": context.source_set_id,
        "created_at": _utc_now(),
        "generator_version": GENERATOR_VERSION,
        "manifest": manifest,
        "executive_determination": {
            "decision_support_status": "reviewer_ready",
            "decision_use_caveat": context.config["decision_use_caveat"],
            "legal_conclusion": False,
            "review_boundary": {
                "review_id": context.review_id,
                "source_set_id": context.source_set_id,
                "authority_finding_count": counts["authority_finding_count"],
                "non_applicable_authority_count": counts[
                    "non_applicable_authority_count"
                ],
                "forest_plan_component_finding_count": counts[
                    "forest_plan_component_finding_count"
                ],
                "applicable_forest_plan_standard_count": counts[
                    "forest_plan_applicable_standard_count"
                ],
            },
        },
        "record_and_artifact_inventory": _record_inventory(context, validation),
        "applicable_authority_summary": _applicable_authority_summary(
            context,
            authority_rows,
        ),
        "authority_findings": authority_rows,
        "forest_plan_consistency": {
            "component_finding_count": counts["forest_plan_component_finding_count"],
            "supported_component_count": counts["forest_plan_supported_component_count"],
            "not_applicable_component_count": counts[
                "forest_plan_not_applicable_component_count"
            ],
            "gap_count": counts["forest_plan_gap_count"],
            "standard_count": counts["forest_plan_standard_count"],
            "applicable_standard_count": counts["forest_plan_applicable_standard_count"],
            "applied_standard_count": counts["forest_plan_applied_standard_count"],
            "plan_consistency_table_package_record_id": "EA-PACKAGE-042",
            "component_rows": component_rows,
            "source_selectors": [
                _selector(
                    context.artifacts["forest_plan_component_findings"].path,
                    "findings[*]",
                ),
                _selector(
                    context.artifacts["plan_consistency_table_text"].path,
                    "source_record_id=EA-PACKAGE-042",
                ),
            ],
        },
        "applicable_forest_plan_standards": standard_rows,
        "non_applicable_authority_boundary": non_applicable,
        "implementation_confirmation_checklist": confirmations,
        "residual_risk_register": residual_risks,
        "validation_and_replay": {
            "passed": True,
            "checks": validation["checks"],
            "replay_commands": [
                (
                    "PYTHONPATH=src python -m usfs_r1_ea_sources "
                    f"ea-consistency-document --output-dir {context.output_dir} "
                    f"--review-id {context.review_id}"
                ),
                (
                    "PYTHONPATH=src python -m usfs_r1_ea_sources "
                    f"phase-eval --output-dir {context.output_dir} --review-id {context.review_id}"
                ),
            ],
        },
    }


def _record_inventory(
    context: _DecisionSupportContext,
    validation: dict[str, Any],
) -> dict[str, Any]:
    return {
        "review_id": context.review_id,
        "source_set_id": context.source_set_id,
        "package_file_count": validation["counts"]["package_file_count"],
        "package_chunk_count": validation["counts"]["package_chunk_count"],
        "generated_rule_pack_ready": True,
        "source_dependencies": _source_dependencies(context),
        "source_selectors": [
            _selector(context.artifacts["package_manifest"].path, "source_record_id=*"),
            _selector(context.artifacts["package_chunks"].path, "chunk_id=*"),
        ],
    }


def _applicable_authority_summary(
    context: _DecisionSupportContext,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    category_counts = Counter(str(row.get("authority_category") or "unknown") for row in rows)
    status_counts = Counter(str(row.get("compliance_status") or "unknown") for row in rows)
    group_order = _strings(context.config.get("authority_group_order"))
    ordered_categories = {
        category: category_counts[category]
        for category in group_order
        if category in category_counts
    }
    ordered_categories.update(
        {
            category: count
            for category, count in sorted(category_counts.items())
            if category not in ordered_categories
        }
    )
    return {
        "applicable_authority_count": len(rows),
        "status_counts": dict(sorted(status_counts.items())),
        "category_counts": ordered_categories,
    }


def _authority_findings(context: _DecisionSupportContext) -> list[dict[str, Any]]:
    confirmation_by_rule = _confirmation_ids_by_selector(context, "authority_finding", "rule_id")
    rows = []
    for row in sorted(
        _dict_list(context.payload("compliance_matrix").get("rows")),
        key=lambda value: str(value.get("rule_id")),
    ):
        rule_id = str(row.get("rule_id"))
        rows.append(
            {
                "rule_id": rule_id,
                "rule_title": row.get("rule_title"),
                "authority_category": row.get("authority_category"),
                "authority_source_record_id": row.get("authority_source_record_id"),
                "authority_family_ids": _strings(row.get("authority_family_ids")),
                "candidate_authority_id": row.get("candidate_authority_id"),
                "applicability_decision_id": row.get("applicability_decision_id"),
                "applicability_status": row.get("applicability_status"),
                "applicability_mode": row.get("applicability_mode"),
                "compliance_status": row.get("status"),
                "requirement": row.get("requirement"),
                "rationale": row.get("rationale"),
                "implementation_confirmation_ids": confirmation_by_rule.get(rule_id, []),
                "source_claim_ids": _strings(row.get("source_claim_ids")),
                "limitations": _strings(row.get("limitations")),
                "ea_package_evidence": [_evidence(row.get("ea_package_evidence"))],
                "source_library_evidence": [_evidence(row.get("source_library_evidence"))],
                "trace_ids": [
                    _trace(
                        f"trace:authority:{rule_id}",
                        "applicable_authority",
                        context.artifacts["compliance_matrix"].path,
                        f"rule_id={rule_id}",
                    )
                ],
                "source_selectors": [
                    _selector(context.artifacts["compliance_matrix"].path, f"rule_id={rule_id}"),
                    _selector(
                        context.artifacts["applicable_authorities"].path,
                        f"candidate_authority_id={row.get('candidate_authority_id')}",
                    ),
                ],
            }
        )
    return rows


def _forest_plan_component_rows(context: _DecisionSupportContext) -> list[dict[str, Any]]:
    rows = []
    for finding in _dict_list(context.payload("forest_plan_component_findings").get("findings")):
        basis = _dict(finding.get("applicability_basis"))
        component_key = str(basis.get("component_key") or "")
        component_id = str(finding.get("component_id") or "")
        rows.append(
            {
                "component_id": component_id,
                "component_key": component_key,
                "component_type": finding.get("component_type"),
                "applicability_status": finding.get("applicability_status"),
                "compliance_status": finding.get("compliance_status"),
                "finding_status": finding.get("finding_status"),
                "rationale": finding.get("rationale"),
                "package_evidence": _evidence_list(finding.get("package_evidence")),
                "forest_plan_evidence": _evidence_list(finding.get("plan_source_evidence")),
                "trace_ids": [
                    _trace(
                        f"trace:forest-plan:{component_key or component_id}",
                        "forest_plan_component",
                        context.artifacts["forest_plan_component_findings"].path,
                        f"component_id={component_id}",
                    )
                ],
                "source_selectors": [
                    _selector(
                        context.artifacts["forest_plan_component_findings"].path,
                        f"component_id={component_id}",
                    )
                ],
            }
        )
    return sorted(rows, key=lambda row: str(row.get("component_id")))


def _applicable_standards(context: _DecisionSupportContext) -> list[dict[str, Any]]:
    findings = _forest_findings_by_component(context)
    confirmation_by_standard = _confirmation_ids_by_selector(
        context,
        "forest_plan_standard",
        "component_key",
    )
    rows = []
    for standard in _applicable_standard_rows(context):
        component_id = str(standard.get("component_id"))
        component_key = str(standard.get("component_key") or component_id)
        finding = findings.get(component_id, {})
        rows.append(
            {
                "component_id": component_id,
                "component_key": component_key,
                "compliance_status": standard.get("compliance_status"),
                "finding_status": standard.get("finding_status"),
                "standard_applied": standard.get("standard_applied"),
                "implementation_confirmation_ids": confirmation_by_standard.get(
                    component_key,
                    [],
                ),
                "package_evidence": _evidence_list(finding.get("package_evidence")),
                "forest_plan_evidence": _evidence_list(finding.get("plan_source_evidence")),
                "trace_ids": [
                    _trace(
                        f"trace:standard:{component_key}",
                        "applicable_forest_plan_standard",
                        context.artifacts["forest_plan_applicable_standard_coverage"].path,
                        f"component_key={component_key}",
                    )
                ],
                "source_selectors": [
                    _selector(
                        context.artifacts["forest_plan_applicable_standard_coverage"].path,
                        f"component_key={component_key}",
                    ),
                    _selector(
                        context.artifacts["forest_plan_component_findings"].path,
                        f"component_id={component_id}",
                    ),
                ],
            }
        )
    return sorted(rows, key=lambda row: str(row.get("component_key")))


def _non_applicable_boundary(context: _DecisionSupportContext) -> dict[str, Any]:
    non_applicable = _dict_list(context.payload("non_applicable_authorities").get("authorities"))
    certificates = _dict_list(context.payload("search_coverage_certificates").get("certificates"))
    certificates_by_id = {
        str(certificate.get("coverage_certificate_id")): certificate
        for certificate in certificates
    }
    summary_rows = []
    category_counts = Counter()
    family_counts = Counter()
    for authority in sorted(
        non_applicable,
        key=lambda value: str(value.get("candidate_authority_id")),
    ):
        category = str(authority.get("authority_category") or "unknown")
        family = _authority_family_id(authority)
        category_counts[category] += 1
        family_counts[family] += 1
        certificate_ids = _strings(authority.get("search_coverage_certificate_ids"))
        summary_rows.append(
            {
                "candidate_authority_id": authority.get("candidate_authority_id"),
                "decision_id": authority.get("decision_id"),
                "authority_category": category,
                "authority_family_id": family,
                "basis_type": authority.get("basis_type"),
                "status": "not_applicable",
                "rationale": _basis_rationale(authority),
                "source_record_ids": _strings(authority.get("source_record_ids")),
                "search_coverage_certificate_ids": certificate_ids,
                "search_coverage": [
                    _coverage_summary(certificates_by_id[certificate_id])
                    for certificate_id in certificate_ids
                    if certificate_id in certificates_by_id
                ],
                "trace_ids": [
                    _trace(
                        f"trace:non-applicable:{authority.get('decision_id')}",
                        "non_applicable_authority",
                        context.artifacts["non_applicable_authorities"].path,
                        f"decision_id={authority.get('decision_id')}",
                    )
                ],
                "source_selectors": [
                    _selector(
                        context.artifacts["non_applicable_authorities"].path,
                        f"decision_id={authority.get('decision_id')}",
                    )
                ],
            }
        )
    return {
        "non_applicable_authority_count": len(summary_rows),
        "category_counts": dict(sorted(category_counts.items())),
        "authority_family_counts": dict(sorted(family_counts.items())),
        "summary_rows": summary_rows,
        "appendix_path": str(context.artifacts["non_applicable_authority_appendix"].path),
        "appendix_markdown_path": str(
            context.artifacts["non_applicable_authority_appendix_markdown"].path
        ),
        "coverage_certificates_path": str(
            context.artifacts["search_coverage_certificates"].path
        ),
    }


def _implementation_confirmations(context: _DecisionSupportContext) -> list[dict[str, Any]]:
    rows = []
    for confirmation in sorted(
        _dict_list(context.config.get("implementation_confirmations")),
        key=lambda value: int(value.get("display_order") or 0),
    ):
        evidence = []
        selectors = []
        for selector in _dict_list(confirmation.get("source_selectors")):
            selectors.append(
                {
                    "artifact_path": selector.get("artifact_path"),
                    "selector": selector.get("selector"),
                    "selector_type": selector.get("selector_type"),
                }
            )
            resolved = _resolve_selector(context, selector)
            if resolved is not None:
                evidence.extend(_selector_evidence(resolved))
        rows.append(
            {
                "confirmation_id": confirmation.get("confirmation_id"),
                "label": confirmation.get("label"),
                "group": confirmation.get("group"),
                "status": "requires_confirmation",
                "evidence_status": confirmation.get("evidence_status"),
                "config_owner": str(context.config_path),
                "allowed_report_wording": confirmation.get("allowed_report_wording"),
                "source_selectors": selectors,
                "evidence": evidence,
                "trace_ids": [
                    _trace(
                        f"trace:confirmation:{confirmation.get('confirmation_id')}",
                        "implementation_confirmation",
                        context.config_path,
                        (
                            "implementation_confirmations.confirmation_id="
                            f"{confirmation.get('confirmation_id')}"
                        ),
                    )
                ],
            }
        )
    return rows


def _residual_risks(context: _DecisionSupportContext) -> list[dict[str, Any]]:
    risk_summary = context.payload("litigation_risk_summary")
    authority_resolution = context.payload("authority_reviewer_resolution_report")
    forest_queue = context.payload("forest_plan_reviewer_resolution_queue")
    risk_flags = _dict_list(risk_summary.get("risk_flags"))
    return [
        {
            "risk_id": "risk:non-applicable-authority-boundary",
            "category": "non_applicable_authority_boundary",
            "severity": "informational",
            "deterministic_basis": True,
            "legal_conclusion": False,
            "risk_flag_count": len(risk_flags),
            "rationale": (
                "Non-applicable authorities remain excluded from compliance findings by "
                "deterministic applicability decisions with search coverage."
            ),
            "source_artifact_path": str(context.artifacts["litigation_risk_summary"].path),
            "source_selector": "summary.risk_category_counts",
            "trace_ids": [
                _trace(
                    "trace:risk:non-applicable-authority-boundary",
                    "residual_risk",
                    context.artifacts["litigation_risk_summary"].path,
                    "summary.risk_category_counts",
                )
            ],
        },
        {
            "risk_id": "risk:authority-resolution-status",
            "category": "reviewer_resolution",
            "severity": "none",
            "deterministic_basis": True,
            "legal_conclusion": False,
            "pending_resolution_count": (
                authority_resolution.get("summary") or {}
            ).get("pending_resolution_count"),
            "rationale": "No authority reviewer-resolution items are open.",
            "source_artifact_path": str(
                context.artifacts["authority_reviewer_resolution_report"].path
            ),
            "source_selector": "summary.pending_resolution_count",
            "trace_ids": [
                _trace(
                    "trace:risk:authority-resolution-status",
                    "residual_risk",
                    context.artifacts["authority_reviewer_resolution_report"].path,
                    "summary.pending_resolution_count",
                )
            ],
        },
        {
            "risk_id": "risk:forest-plan-resolution-status",
            "category": "reviewer_resolution",
            "severity": "none",
            "deterministic_basis": True,
            "legal_conclusion": False,
            "pending_resolution_count": len(forest_queue.get("items") or []),
            "rationale": "No Forest Plan reviewer-resolution items are open.",
            "source_artifact_path": str(
                context.artifacts["forest_plan_reviewer_resolution_queue"].path
            ),
            "source_selector": "items",
            "trace_ids": [
                _trace(
                    "trace:risk:forest-plan-resolution-status",
                    "residual_risk",
                    context.artifacts["forest_plan_reviewer_resolution_queue"].path,
                    "items",
                )
            ],
        },
    ]


def _manifest(
    context: _DecisionSupportContext,
    validation: dict[str, Any],
) -> dict[str, Any]:
    input_hashes = {
        f"{key}_sha256": artifact.sha256
        for key, artifact in sorted(context.artifacts.items())
        if artifact.sha256 is not None
    }
    input_hashes["decision_support_config_sha256"] = _sha256_file(context.config_path)
    input_hashes["decision_support_expected_summary_sha256"] = _sha256_file(
        context.expected_summary_path
    )
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "review_id": context.review_id,
        "source_set_id": context.source_set_id,
        "generator_version": GENERATOR_VERSION,
        "generated_at": _utc_now(),
        "validation_status": "passed" if validation["passed"] else "failed",
        "input_hashes": input_hashes,
        "source_dependencies": _source_dependencies(context),
        "section_dependencies": _section_dependencies(context),
        "checks": validation["checks"],
        "failure_categories": validation["failure_categories"],
    }


def _source_dependencies(context: _DecisionSupportContext) -> list[dict[str, Any]]:
    dependencies = [
        {
            "artifact_key": key,
            "artifact_path": str(artifact.path),
            "sha256": artifact.sha256,
        }
        for key, artifact in sorted(context.artifacts.items())
    ]
    dependencies.append(
        {
            "artifact_key": "decision_support_config",
            "artifact_path": str(context.config_path),
            "sha256": _sha256_file(context.config_path),
        }
    )
    dependencies.append(
        {
            "artifact_key": "decision_support_expected_summary",
            "artifact_path": str(context.expected_summary_path),
            "sha256": _sha256_file(context.expected_summary_path),
        }
    )
    return dependencies


def _section_dependencies(context: _DecisionSupportContext) -> dict[str, list[str]]:
    return {
        "executive_determination": [
            str(context.artifacts["applicability_validation"].path),
            str(context.artifacts["compliance_matrix"].path),
        ],
        "record_and_artifact_inventory": [
            str(context.artifacts["package_manifest"].path),
            str(context.artifacts["package_chunks"].path),
        ],
        "applicable_authority_summary": [str(context.artifacts["compliance_matrix"].path)],
        "authority_findings": [
            str(context.artifacts["compliance_matrix"].path),
            str(context.artifacts["applicable_authorities"].path),
        ],
        "forest_plan_consistency": [
            str(context.artifacts["forest_plan_component_findings"].path),
            str(context.artifacts["forest_plan_context_summary"].path),
        ],
        "applicable_forest_plan_standards": [
            str(context.artifacts["forest_plan_applicable_standard_coverage"].path),
            str(context.artifacts["forest_plan_component_findings"].path),
        ],
        "non_applicable_authority_boundary": [
            str(context.artifacts["non_applicable_authorities"].path),
            str(context.artifacts["search_coverage_certificates"].path),
            str(context.artifacts["non_applicable_authority_appendix"].path),
        ],
        "implementation_confirmation_checklist": [
            str(context.config_path),
            str(context.artifacts["package_chunks"].path),
            str(context.artifacts["compliance_matrix"].path),
            str(context.artifacts["forest_plan_applicable_standard_coverage"].path),
        ],
        "residual_risk_register": [
            str(context.artifacts["litigation_risk_summary"].path),
            str(context.artifacts["authority_reviewer_resolution_report"].path),
            str(context.artifacts["forest_plan_reviewer_resolution_queue"].path),
        ],
        "validation_and_replay": [str(context.expected_summary_path)],
    }


def _current_counts(context: _DecisionSupportContext) -> dict[str, Any]:
    matrix_rows = _dict_list(context.payload("compliance_matrix").get("rows"))
    applicable = _dict_list(context.payload("applicable_authorities").get("authorities"))
    non_applicable = _dict_list(context.payload("non_applicable_authorities").get("authorities"))
    certificates = _dict_list(context.payload("search_coverage_certificates").get("certificates"))
    forest_summary = _dict(context.payload("forest_plan_component_findings").get("summary"))
    standard_coverage = context.payload("forest_plan_applicable_standard_coverage")
    authority_resolution = context.payload("authority_reviewer_resolution_report")
    forest_queue = context.payload("forest_plan_reviewer_resolution_queue")
    risk_summary = context.payload("litigation_risk_summary")
    return {
        "applicable_authority_count": len(applicable),
        "non_applicable_authority_count": len(non_applicable),
        "candidate_authority_count": len(applicable) + len(non_applicable),
        "authority_finding_count": len(matrix_rows),
        "authority_finding_status_counts": dict(
            sorted(Counter(str(row.get("status")) for row in matrix_rows).items())
        ),
        "non_applicable_search_coverage_certificate_count": len(certificates),
        "forest_plan_component_finding_count": forest_summary.get("finding_count"),
        "forest_plan_supported_component_count": forest_summary.get("supported_count"),
        "forest_plan_not_applicable_component_count": forest_summary.get(
            "not_applicable_count"
        ),
        "forest_plan_gap_count": forest_summary.get("gap_count"),
        "forest_plan_standard_count": standard_coverage.get("standard_count"),
        "forest_plan_applicable_standard_count": standard_coverage.get(
            "applicable_standard_count"
        ),
        "forest_plan_applied_standard_count": standard_coverage.get(
            "applied_standard_count"
        ),
        "authority_reviewer_resolution_pending_count": (
            authority_resolution.get("summary") or {}
        ).get("pending_resolution_count"),
        "forest_plan_reviewer_resolution_item_count": len(forest_queue.get("items") or []),
        "litigation_risk_flag_count": (risk_summary.get("summary") or {}).get(
            "risk_flag_count"
        ),
        "litigation_risk_legal_conclusion_count": (
            risk_summary.get("summary") or {}
        ).get("legal_conclusion_count"),
        "package_file_count": len(_list(context.payload("package_manifest"))),
        "package_chunk_count": len(_list(context.payload("package_chunks"))),
    }


def _generation_summary(
    *,
    context: _DecisionSupportContext,
    report_dir: Path,
    report_path: Path,
    markdown_path: Path,
    pdf_path: Path,
    manifest_path: Path,
    validation: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "ea-consistency-decision-support-generation-summary-v1",
        "created_at": _utc_now(),
        "review_id": context.review_id,
        "source_set_id": context.source_set_id,
        "output_dir": str(report_dir),
        "report_path": str(report_path),
        "markdown_path": str(markdown_path),
        "pdf_path": str(pdf_path),
        "manifest_path": str(manifest_path),
        "passed": validation["passed"],
        "output_written": False,
        "failure_categories": validation["failure_categories"],
        "failure_count": len(validation["failures"]),
        "counts": validation["counts"],
    }


def _validate_report_artifact_family(
    *,
    output_dir: Path,
    report_dir: Path,
    report_artifacts: dict[str, _LoadedArtifact],
    config_artifact: _LoadedArtifact,
    expected_artifact: _LoadedArtifact,
    context: _DecisionSupportContext | None,
    source_validation: dict[str, Any] | None,
    selected_review_id: str,
    source_set_id: str,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    _record_check(
        checks,
        failures,
        name="decision_support_config_exists_and_parses",
        passed=config_artifact.exists and config_artifact.parse_ok,
        failure_category=config_artifact.failure_category or "missing_required_artifact",
        source_selector="decision_support_config",
        expected=True,
        actual=config_artifact.exists and config_artifact.parse_ok,
        message=config_artifact.error,
    )
    _record_check(
        checks,
        failures,
        name="decision_support_expected_summary_exists_and_parses",
        passed=expected_artifact.exists and expected_artifact.parse_ok,
        failure_category=expected_artifact.failure_category or "missing_required_artifact",
        source_selector="decision_support_expected_summary",
        expected=True,
        actual=expected_artifact.exists and expected_artifact.parse_ok,
        message=expected_artifact.error,
    )
    for key, artifact in report_artifacts.items():
        failure_category = artifact.failure_category or "missing_required_artifact"
        if key == "pdf" and not artifact.exists:
            failure_category = "missing_report_pdf"
        elif key == "pdf" and artifact.exists and not artifact.parse_ok:
            failure_category = "invalid_report_pdf_header"
        _record_check(
            checks,
            failures,
            name=f"decision_support_{key}_exists_and_parses",
            passed=artifact.exists and artifact.parse_ok,
            failure_category=failure_category,
            source_selector=f"decision_support.{key}",
            expected=True,
            actual=artifact.exists and artifact.parse_ok,
            message=artifact.error,
        )

    if source_validation is not None:
        _record_check(
            checks,
            failures,
            name="decision_support_source_artifacts_revalidate",
            passed=source_validation["passed"],
            failure_category=(
                source_validation["failure_categories"][0]
                if source_validation["failure_categories"]
                else "stale_artifact"
            ),
            source_selector="decision_support.source_artifacts",
            expected=[],
            actual=source_validation["failure_categories"],
        )
        failures.extend(source_validation["failures"])
    else:
        _record_check(
            checks,
            failures,
            name="decision_support_source_artifacts_revalidate",
            passed=False,
            failure_category="missing_required_artifact",
            source_selector="decision_support.source_artifacts",
            expected=True,
            actual=False,
        )

    report = _dict(report_artifacts["report"].payload)
    manifest = _dict(report_artifacts["manifest"].payload)
    embedded_manifest = _dict(report.get("manifest"))
    expected = _dict(expected_artifact.payload)
    config = _dict(config_artifact.payload)
    counts = _dict(source_validation.get("counts") if source_validation else {})

    _validate_report_identity(
        checks=checks,
        failures=failures,
        report=report,
        manifest=manifest,
        embedded_manifest=embedded_manifest,
        selected_review_id=selected_review_id,
        source_set_id=source_set_id,
    )
    _validate_report_sections(
        checks=checks,
        failures=failures,
        report=report,
        expected=expected,
        config=config,
    )
    _validate_report_counts(
        checks=checks,
        failures=failures,
        report=report,
        counts=counts,
    )
    if context is not None:
        _validate_report_manifest_hashes(
            checks=checks,
            failures=failures,
            manifest=manifest,
            embedded_manifest=embedded_manifest,
            context=context,
        )
    _validate_report_content_boundaries(
        checks=checks,
        failures=failures,
        report=report,
        config=config,
        expected=expected,
    )

    failure_categories = sorted(
        {
            failure["failure_category"]
            for failure in failures
            if failure.get("failure_category")
        }
    )
    return {
        "schema_version": "ea-consistency-decision-support-validation-summary-v1",
        "created_at": _utc_now(),
        "review_id": selected_review_id,
        "source_set_id": source_set_id,
        "output_dir": str(report_dir),
        "report_path": str(report_artifacts["report"].path),
        "markdown_path": str(report_artifacts["markdown"].path),
        "pdf_path": str(report_artifacts["pdf"].path),
        "manifest_path": str(report_artifacts["manifest"].path),
        "passed": not failures,
        "reviewer_ready": not failures,
        "source_artifact_validation_passed": bool(
            source_validation and source_validation["passed"]
        ),
        "pdf_header_valid": bool(
            report_artifacts["pdf"].exists and report_artifacts["pdf"].parse_ok
        ),
        "failure_categories": failure_categories,
        "failure_count": len(failures),
        "counts": counts,
        "checks": checks,
        "failures": failures,
        "validation_status": "passed" if not failures else "failed",
        "phase_eval_integration": {
            "phase_name": "decision_support_report",
            "output_dir": str(output_dir),
            "report_dir": str(report_dir),
        },
    }


def _validate_report_identity(
    *,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    report: dict[str, Any],
    manifest: dict[str, Any],
    embedded_manifest: dict[str, Any],
    selected_review_id: str,
    source_set_id: str,
) -> None:
    identity_checks = {
        "report_schema_version": (
            report.get("schema_version"),
            REPORT_SCHEMA_VERSION,
            "decision_support_report.schema_version",
        ),
        "report_review_id": (
            report.get("review_id"),
            selected_review_id,
            "decision_support_report.review_id",
        ),
        "report_source_set_id": (
            report.get("source_set_id"),
            source_set_id,
            "decision_support_report.source_set_id",
        ),
        "manifest_schema_version": (
            manifest.get("schema_version"),
            MANIFEST_SCHEMA_VERSION,
            "decision_support_manifest.schema_version",
        ),
        "manifest_review_id": (
            manifest.get("review_id"),
            selected_review_id,
            "decision_support_manifest.review_id",
        ),
        "manifest_source_set_id": (
            manifest.get("source_set_id"),
            source_set_id,
            "decision_support_manifest.source_set_id",
        ),
        "manifest_validation_status": (
            manifest.get("validation_status"),
            "passed",
            "decision_support_manifest.validation_status",
        ),
        "embedded_manifest_validation_status": (
            embedded_manifest.get("validation_status"),
            "passed",
            "decision_support_report.manifest.validation_status",
        ),
        "validation_and_replay_passed": (
            _dict(report.get("validation_and_replay")).get("passed"),
            True,
            "decision_support_report.validation_and_replay.passed",
        ),
        "decision_support_status": (
            _dict(report.get("executive_determination")).get("decision_support_status"),
            "reviewer_ready",
            "decision_support_report.executive_determination.decision_support_status",
        ),
    }
    for name, (actual, expected, selector) in identity_checks.items():
        _record_check(
            checks,
            failures,
            name=name,
            passed=actual == expected,
            failure_category="stale_artifact",
            source_selector=selector,
            expected=expected,
            actual=actual,
        )
    _record_check(
        checks,
        failures,
        name="manifest_file_matches_embedded_manifest",
        passed=bool(manifest) and manifest == embedded_manifest,
        failure_category="input_hash_mismatch",
        source_selector="decision_support_report.manifest",
        expected="manifest file equals report.manifest",
        actual="matched" if bool(manifest) and manifest == embedded_manifest else "mismatch",
    )


def _validate_report_sections(
    *,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    report: dict[str, Any],
    expected: dict[str, Any],
    config: dict[str, Any],
) -> None:
    required_sections = _strings(expected.get("required_sections")) or _strings(
        config.get("section_order")
    )
    missing_sections = [section for section in required_sections if section not in report]
    _record_check(
        checks,
        failures,
        name="required_report_sections_present",
        passed=not missing_sections,
        failure_category="missing_required_report_section",
        source_selector="decision_support_report.required_sections",
        expected=required_sections,
        actual=sorted(set(required_sections) - set(missing_sections)),
    )


def _validate_report_counts(
    *,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    report: dict[str, Any],
    counts: dict[str, Any],
) -> None:
    forest = _dict(report.get("forest_plan_consistency"))
    non_applicable = _dict(report.get("non_applicable_authority_boundary"))
    summary = _dict(report.get("applicable_authority_summary"))
    actual_counts = {
        "authority_finding_count": len(_dict_list(report.get("authority_findings"))),
        "applicable_authority_count": summary.get("applicable_authority_count"),
        "non_applicable_authority_count": non_applicable.get(
            "non_applicable_authority_count"
        ),
        "non_applicable_summary_row_count": len(
            _dict_list(non_applicable.get("summary_rows"))
        ),
        "forest_plan_component_finding_count": forest.get("component_finding_count"),
        "forest_plan_component_row_count": len(_dict_list(forest.get("component_rows"))),
        "forest_plan_applicable_standard_count": forest.get("applicable_standard_count"),
        "forest_plan_applied_standard_count": forest.get("applied_standard_count"),
        "applicable_forest_plan_standard_row_count": len(
            _dict_list(report.get("applicable_forest_plan_standards"))
        ),
    }
    expected_counts = {
        "authority_finding_count": counts.get("authority_finding_count"),
        "applicable_authority_count": counts.get("applicable_authority_count"),
        "non_applicable_authority_count": counts.get("non_applicable_authority_count"),
        "non_applicable_summary_row_count": counts.get("non_applicable_authority_count"),
        "forest_plan_component_finding_count": counts.get(
            "forest_plan_component_finding_count"
        ),
        "forest_plan_component_row_count": counts.get("forest_plan_component_finding_count"),
        "forest_plan_applicable_standard_count": counts.get(
            "forest_plan_applicable_standard_count"
        ),
        "forest_plan_applied_standard_count": counts.get("forest_plan_applied_standard_count"),
        "applicable_forest_plan_standard_row_count": counts.get(
            "forest_plan_applicable_standard_count"
        ),
    }
    for key, expected_count in expected_counts.items():
        _record_check(
            checks,
            failures,
            name=f"report_{key}_matches_current_artifacts",
            passed=actual_counts[key] == expected_count,
            failure_category=(
                "non_applicable_summary_missing"
                if key == "non_applicable_summary_row_count"
                else "count_drift"
            ),
            source_selector=f"decision_support_report.counts.{key}",
            expected=expected_count,
            actual=actual_counts[key],
        )


def _validate_report_manifest_hashes(
    *,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    manifest: dict[str, Any],
    embedded_manifest: dict[str, Any],
    context: _DecisionSupportContext,
) -> None:
    current_hashes = _current_input_hashes(context)
    for manifest_name, manifest_payload in (
        ("manifest_file", manifest),
        ("embedded_manifest", embedded_manifest),
    ):
        manifest_hashes = _dict(manifest_payload.get("input_hashes"))
        missing_keys = sorted(set(current_hashes) - set(manifest_hashes))
        mismatches = sorted(
            key
            for key, value in current_hashes.items()
            if manifest_hashes.get(key) != value
        )
        _record_check(
            checks,
            failures,
            name=f"{manifest_name}_input_hashes_are_current",
            passed=not missing_keys and not mismatches,
            failure_category="input_hash_mismatch",
            source_selector=f"decision_support_{manifest_name}.input_hashes",
            expected="current input hashes",
            actual={"missing_keys": missing_keys, "mismatched_keys": mismatches},
        )


def _validate_report_content_boundaries(
    *,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    report: dict[str, Any],
    config: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    non_applicable = _dict(report.get("non_applicable_authority_boundary"))
    non_applicable_rows = _dict_list(non_applicable.get("summary_rows"))
    missing_search_coverage = [
        str(row.get("candidate_authority_id") or row.get("decision_id"))
        for row in non_applicable_rows
        if not row.get("search_coverage")
    ]
    _record_check(
        checks,
        failures,
        name="report_non_applicable_rows_have_search_coverage",
        passed=bool(non_applicable_rows) and not missing_search_coverage,
        failure_category="non_applicable_missing_search_coverage",
        source_selector="decision_support_report.non_applicable_authority_boundary.summary_rows",
        expected=[],
        actual=missing_search_coverage,
    )

    expected_standard_keys = {
        str(row.get("component_key"))
        for row in _dict_list(expected.get("applicable_standards"))
        if row.get("component_key")
    }
    standard_keys = {
        str(row.get("component_key"))
        for row in _dict_list(report.get("applicable_forest_plan_standards"))
        if row.get("component_key")
    }
    missing_standard_keys = sorted(expected_standard_keys - standard_keys)
    _record_check(
        checks,
        failures,
        name="report_applicable_standards_complete",
        passed=not missing_standard_keys,
        failure_category="applicable_standard_missing",
        source_selector="decision_support_report.applicable_forest_plan_standards",
        expected=sorted(expected_standard_keys),
        actual=sorted(standard_keys),
    )

    missing_standard_evidence = [
        str(row.get("component_key") or row.get("component_id"))
        for row in _dict_list(report.get("applicable_forest_plan_standards"))
        if not row.get("package_evidence") or not row.get("forest_plan_evidence")
    ]
    _record_check(
        checks,
        failures,
        name="report_applicable_standards_have_evidence",
        passed=not missing_standard_evidence,
        failure_category="applicable_standard_missing_evidence",
        source_selector="decision_support_report.applicable_forest_plan_standards.evidence",
        expected=[],
        actual=missing_standard_evidence,
    )

    expected_confirmation_ids = {
        str(row.get("confirmation_id"))
        for row in _dict_list(config.get("implementation_confirmations"))
        if row.get("confirmation_id")
    }
    report_confirmation_ids = {
        str(row.get("confirmation_id"))
        for row in _dict_list(report.get("implementation_confirmation_checklist"))
        if row.get("confirmation_id")
    }
    missing_confirmation_ids = sorted(expected_confirmation_ids - report_confirmation_ids)
    _record_check(
        checks,
        failures,
        name="report_implementation_confirmations_complete",
        passed=not missing_confirmation_ids,
        failure_category="implementation_confirmation_selector_unresolved",
        source_selector="decision_support_report.implementation_confirmation_checklist",
        expected=sorted(expected_confirmation_ids),
        actual=sorted(report_confirmation_ids),
    )

    legal_conclusion_risks = [
        str(row.get("risk_id"))
        for row in _dict_list(report.get("residual_risk_register"))
        if row.get("legal_conclusion") is not False
    ]
    _record_check(
        checks,
        failures,
        name="report_residual_risks_are_not_legal_conclusions",
        passed=not legal_conclusion_risks,
        failure_category="residual_risk_legal_conclusion",
        source_selector="decision_support_report.residual_risk_register",
        expected=[],
        actual=legal_conclusion_risks,
    )
    _record_check(
        checks,
        failures,
        name="report_does_not_reference_manual_root_drafts",
        passed="East_Crazies_" not in json.dumps(report, sort_keys=True),
        failure_category="manual_draft_dependency",
        source_selector="decision_support_report",
        expected="no East_Crazies_ manual draft references",
        actual="contains East_Crazies_"
        if "East_Crazies_" in json.dumps(report, sort_keys=True)
        else "clean",
    )


def _current_input_hashes(context: _DecisionSupportContext) -> dict[str, str]:
    input_hashes = {
        f"{key}_sha256": str(artifact.sha256)
        for key, artifact in sorted(context.artifacts.items())
        if artifact.sha256 is not None
    }
    input_hashes["decision_support_config_sha256"] = _sha256_file(context.config_path)
    input_hashes["decision_support_expected_summary_sha256"] = _sha256_file(
        context.expected_summary_path
    )
    return input_hashes


def _validation_result(
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    *,
    counts: dict[str, Any],
) -> dict[str, Any]:
    return {
        "passed": not failures,
        "checks": checks,
        "failures": failures,
        "failure_categories": sorted(
            {failure["failure_category"] for failure in failures}
        ),
        "counts": counts,
    }


def _record_check(
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    *,
    name: str,
    passed: bool,
    failure_category: str,
    source_selector: str,
    expected: Any,
    actual: Any,
    message: str | None = None,
) -> None:
    check = {
        "name": name,
        "passed": bool(passed),
        "failure_category": failure_category,
        "source_selector": source_selector,
        "expected": expected,
        "actual": actual,
    }
    if message:
        check["message"] = message
    checks.append(check)
    if not passed:
        failures.append(check)


def _resolve_selector(
    context: _DecisionSupportContext,
    selector: dict[str, Any],
) -> dict[str, Any] | None:
    selector_type = str(selector.get("selector_type") or "")
    criteria = _parse_selector(str(selector.get("selector") or ""))
    if selector_type == "package_chunk":
        return _find_by_criteria(_list(context.payload("package_chunks")), criteria)
    if selector_type == "package_record":
        return _find_by_criteria(_list(context.payload("package_manifest")), criteria)
    if selector_type == "authority_finding":
        return _find_by_criteria(
            _dict_list(context.payload("compliance_matrix").get("rows")),
            criteria,
        )
    if selector_type == "forest_plan_standard":
        return _find_by_criteria(
            _dict_list(
                context.payload("forest_plan_applicable_standard_coverage").get("standards")
            ),
            criteria,
        )
    return None


def _selector_evidence(resolved: dict[str, Any]) -> list[dict[str, Any]]:
    if resolved.get("ea_package_evidence") or resolved.get("source_library_evidence"):
        evidence = []
        if resolved.get("ea_package_evidence"):
            evidence.append(_evidence(resolved["ea_package_evidence"]))
        if resolved.get("source_library_evidence"):
            evidence.append(_evidence(resolved["source_library_evidence"]))
        return evidence
    if "text" in resolved and "chunk_id" in resolved:
        return [_evidence(resolved)]
    if resolved.get("package_component_determination"):
        determination = resolved["package_component_determination"]
        return [
            {
                "chunk_id": determination.get("chunk_id") or "unknown",
                "source_record_id": determination.get("source_record_id") or "unknown",
                "citation_label": determination.get("citation_label") or "N/A",
                "artifact_sha256": "selector:forest_plan_standard",
                "content_sha256": "selector:forest_plan_standard",
                "text_span": {
                    "char_start": 0,
                    "char_end": len(str(determination.get("determination_explanation") or "")),
                    "excerpt": str(determination.get("determination_explanation") or ""),
                },
            }
        ]
    if resolved.get("citation_label") and resolved.get("source_record_id"):
        return [_evidence(resolved)]
    return []


def _find_by_criteria(rows: list[Any], criteria: dict[str, str]) -> dict[str, Any] | None:
    for row in rows:
        if not isinstance(row, dict):
            continue
        if all(str(row.get(key) or "") == value for key, value in criteria.items()):
            return row
    return None


def _parse_selector(selector: str) -> dict[str, str]:
    criteria = {}
    for item in selector.split(";"):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        criteria[key.strip()] = value.strip()
    return criteria


def _confirmation_ids_by_selector(
    context: _DecisionSupportContext,
    selector_type: str,
    selector_key: str,
) -> dict[str, list[str]]:
    mapping: dict[str, list[str]] = {}
    for confirmation in _dict_list(context.config.get("implementation_confirmations")):
        confirmation_id = str(confirmation.get("confirmation_id") or "")
        for selector in _dict_list(confirmation.get("source_selectors")):
            if selector.get("selector_type") != selector_type:
                continue
            value = _parse_selector(str(selector.get("selector") or "")).get(selector_key)
            if value:
                mapping.setdefault(value, []).append(confirmation_id)
    return {key: sorted(values) for key, values in mapping.items()}


def _forest_findings_by_component(context: _DecisionSupportContext) -> dict[str, dict[str, Any]]:
    return {
        str(finding.get("component_id")): finding
        for finding in _dict_list(context.payload("forest_plan_component_findings").get("findings"))
    }


def _applicable_standard_rows(context: _DecisionSupportContext) -> list[dict[str, Any]]:
    return [
        standard
        for standard in _dict_list(
            context.payload("forest_plan_applicable_standard_coverage").get("standards")
        )
        if standard.get("applicability_status") == "applicable"
    ]


def _coverage_summary(certificate: dict[str, Any]) -> dict[str, Any]:
    return {
        "coverage_certificate_id": certificate.get("coverage_certificate_id"),
        "coverage_class": certificate.get("coverage_class"),
        "coverage_result": certificate.get("coverage_result"),
        "missing_query_variants": certificate.get("missing_query_variants") or [],
    }


def _basis_rationale(authority: dict[str, Any]) -> str:
    basis = _dict(authority.get("applicability_basis"))
    non_applicability = _dict(authority.get("non_applicability_basis"))
    return str(
        basis.get("rationale")
        or non_applicability.get("rationale")
        or "The authority was determined not applicable within the recorded search boundary."
    )


def _authority_family_id(authority: dict[str, Any]) -> str:
    rule_template = _dict(authority.get("rule_template"))
    forest_plan = _dict(authority.get("forest_plan"))
    if rule_template.get("authority_family_id"):
        return str(rule_template["authority_family_id"])
    if forest_plan.get("component_id"):
        return "nfma_forest_planning_project_consistency"
    ids = _strings(authority.get("authority_family_ids"))
    return ids[0] if ids else "unknown"


def _evidence_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [_evidence(item) for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [_evidence(value)]
    return []


def _evidence(value: Any) -> dict[str, Any]:
    evidence = _dict(value)
    span = _dict(evidence.get("evidence_span"))
    provenance = _dict(evidence.get("provenance"))
    text = str(evidence.get("text") or span.get("text") or evidence.get("text_snippet") or "")
    char_start = _int(
        evidence.get("source_char_start"),
        evidence.get("char_start"),
        span.get("source_char_start"),
        span.get("char_start"),
        evidence.get("chunk_char_start"),
        span.get("chunk_char_start"),
        0,
    )
    char_end = _int(
        evidence.get("source_char_end"),
        evidence.get("char_end"),
        span.get("source_char_end"),
        span.get("char_end"),
        evidence.get("chunk_char_end"),
        span.get("chunk_char_end"),
        char_start + len(text),
    )
    if char_end < char_start:
        char_end = char_start
    return {
        "chunk_id": str(evidence.get("chunk_id") or "unknown"),
        "source_record_id": str(
            evidence.get("source_record_id")
            or provenance.get("source_record_id")
            or "unknown"
        ),
        "citation_label": str(evidence.get("citation_label") or "N/A"),
        "artifact_sha256": str(
            evidence.get("artifact_sha256")
            or provenance.get("artifact_sha256")
            or "unknown"
        ),
        "content_sha256": str(
            evidence.get("content_sha256")
            or provenance.get("content_sha256")
            or "unknown"
        ),
        "text_span": {
            "char_start": char_start,
            "char_end": char_end,
            "excerpt": _truncate(text, 500) or "N/A",
        },
    }


def _report_markdown(report: dict[str, Any]) -> str:
    executive = report["executive_determination"]
    inventory = report["record_and_artifact_inventory"]
    authority_summary = report["applicable_authority_summary"]
    forest = report["forest_plan_consistency"]
    non_applicable = report["non_applicable_authority_boundary"]
    confirmation_count = len(report["implementation_confirmation_checklist"])
    residual_risk_count = len(report["residual_risk_register"])
    legal_risk_count = _legal_conclusion_risk_count(report)
    lines = [
        "# EA Consistency Decision Support",
        "",
        f"- Review ID: `{report['review_id']}`",
        f"- Source set: `{report['source_set_id']}`",
        f"- Status: `{executive['decision_support_status']}`",
        f"- Caveat: {executive['decision_use_caveat']}",
        "",
        "## How To Use This Document",
        "",
        _decision_support_use_note(),
        "",
        "## Review Snapshot",
        "",
    ]
    lines.extend(f"- {item}" for item in _review_snapshot_items(report))
    lines.extend(
        [
            "",
            "## Record and Artifact Inventory",
            "",
            (
                "This inventory identifies the generated review package and validation-owned "
                "artifacts used to build the decision-support rendering."
            ),
            "",
            f"- Package files: `{inventory['package_file_count']}`",
            f"- Package chunks: `{inventory['package_chunk_count']}`",
            f"- Generated rule pack ready: `{inventory['generated_rule_pack_ready']}`",
            "",
            "## Applicable Authority Summary",
            "",
            (
                "The authority summary groups generated applicable findings before the full "
                "evidence table. The table is ordered by rule ID and keeps EA package evidence "
                "separate from source-library evidence."
            ),
            "",
            f"- Applicable authorities: `{authority_summary['applicable_authority_count']}`",
            f"- Status counts: `{_format_counts(authority_summary['status_counts'])}`",
            f"- Category counts: `{_format_counts(authority_summary['category_counts'])}`",
            "",
            "## Authority Findings",
            "",
            (
                "Summary: generated applicable authority findings with package and source "
                "citations; implementation-confirmation IDs identify follow-up checks without "
                "creating additional compliance findings."
            ),
            "",
            "| Rule | Category | Status | EA evidence | Source evidence | Implementation confirmations |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in report["authority_findings"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(row["rule_id"]),
                    _md_cell(row.get("authority_category")),
                    _md_cell(row.get("compliance_status")),
                    _md_cell(_evidence_cell(row.get("ea_package_evidence", []))),
                    _md_cell(_evidence_cell(row.get("source_library_evidence", []))),
                    _md_cell(", ".join(row.get("implementation_confirmation_ids", [])) or "None"),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Forest Plan Consistency",
            "",
            f"- Component findings: `{forest['component_finding_count']}`",
            f"- Supported/applicable components: `{forest['supported_component_count']}`",
            f"- Not-applicable components: `{forest['not_applicable_component_count']}`",
            f"- Gap count: `{forest['gap_count']}`",
            f"- Applicable standards: `{forest['applicable_standard_count']}`",
            f"- Applied standards: `{forest['applied_standard_count']}`",
            f"- Plan Consistency Table source: `{forest['plan_consistency_table_package_record_id']}`",
            "",
            "## Applicable Forest Plan Standards",
            "",
            (
                "Summary: generated applicable Forest Plan standards with package evidence "
                "and Forest Plan source evidence; standards remain separate from broader "
                "not-applicable component rows."
            ),
            "",
            "| Standard | Compliance | Package evidence | Forest Plan evidence |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in report["applicable_forest_plan_standards"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(row.get("component_key")),
                    _md_cell(row.get("compliance_status")),
                    _md_cell(_evidence_cell(row.get("package_evidence", []))),
                    _md_cell(_evidence_cell(row.get("forest_plan_evidence", []))),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Non-Applicable Authority Boundary",
            "",
            (
                "Summary: non-applicable authorities stay out of compliance findings and remain "
                "available through the generated appendix and search-coverage certificates."
            ),
            "",
            f"- Non-applicable authorities: `{non_applicable['non_applicable_authority_count']}`",
            f"- Category counts: `{_format_counts(non_applicable['category_counts'])}`",
            f"- Full appendix: `{non_applicable['appendix_path']}`",
            f"- Coverage certificates: `{non_applicable['coverage_certificates_path']}`",
            "",
            "## Implementation Confirmation Checklist",
            "",
            (
                f"Summary: `{confirmation_count}` evidence-linked implementation confirmations "
                "require reviewer confirmation. These rows are not compliance findings and do "
                "not prove final implementation completion."
            ),
            "",
            "| Confirmation | Status | Decision-support wording | Evidence selectors |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in report["implementation_confirmation_checklist"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(row.get("label")),
                    _md_cell(row.get("status")),
                    _md_cell(row.get("allowed_report_wording")),
                    _md_cell(_selector_cell(row.get("source_selectors", []))),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Residual Risk Register",
            "",
            (
                f"Summary: `{residual_risk_count}` deterministic decision-support risk notes; "
                f"legal-conclusion flags: `{legal_risk_count}`. Risk notes preserve source "
                "artifact pointers and do not replace responsible official or counsel judgment."
            ),
            "",
        ]
    )
    for risk in report["residual_risk_register"]:
        lines.append(
            f"- `{risk['risk_id']}`: `{risk['category']}` / `{risk['severity']}` - "
            f"{risk['rationale']} Source: `{risk['source_artifact_path']}` selector "
            f"`{risk['source_selector']}`."
        )
    lines.extend(
        [
            "",
            "## Validation and Replay",
            "",
            "Summary: replay commands regenerate or re-evaluate this report from audited artifacts.",
            "",
            f"- Passed: `{report['validation_and_replay']['passed']}`",
            f"- Manifest: `{report['manifest']['schema_version']}`",
        ]
    )
    for command in report["validation_and_replay"]["replay_commands"]:
        lines.append(f"- `{command}`")
    return "\n".join(lines) + "\n"


def _report_pdf_pages(report: dict[str, Any]) -> list[list[str]]:
    forest = report["forest_plan_consistency"]
    authority_summary = report["applicable_authority_summary"]
    non_applicable = report["non_applicable_authority_boundary"]
    lines = [
        "EA Consistency Decision Support",
        f"Review ID: {report['review_id']}",
        f"Source set: {report['source_set_id']}",
        (
            "Bottom-line determination: "
            f"{report['executive_determination']['decision_support_status']} "
            "decision support from generated artifacts."
        ),
        "Caveat: " + report["executive_determination"]["decision_use_caveat"],
        "",
        "How To Use This Document",
    ]
    lines.extend(_wrap_pdf_line(_decision_support_use_note()))
    lines.extend(["", "Review Snapshot"])
    for item in _review_snapshot_items(report):
        lines.extend(_wrap_pdf_line("- " + item))
    lines.extend(
        [
            "",
            "Table Summaries",
            (
                "Authority Findings: "
                f"{authority_summary['applicable_authority_count']} generated applicable "
                f"findings, categories {_format_counts(authority_summary['category_counts'])}."
            ),
            (
                "Forest Plan Standards: "
                f"{forest['applied_standard_count']} of {forest['applicable_standard_count']} "
                "applicable standards applied with package and plan evidence."
            ),
            (
                "Non-Applicable Authority Boundary: "
                f"{non_applicable['non_applicable_authority_count']} authorities; appendix "
                f"{non_applicable['appendix_path']}."
            ),
            (
                "Implementation Confirmations: "
                f"{len(report['implementation_confirmation_checklist'])} evidence-linked rows "
                "requiring reviewer confirmation."
            ),
            (
                "Residual Risks: "
                f"{len(report['residual_risk_register'])} decision-support notes; "
                f"{_legal_conclusion_risk_count(report)} legal-conclusion flags."
            ),
        ]
    )
    lines.extend(
        [
            "",
            "Record and Artifact Inventory",
            f"Package files: {report['record_and_artifact_inventory']['package_file_count']}",
            f"Package chunks: {report['record_and_artifact_inventory']['package_chunk_count']}",
            (
                "Generated rule pack ready: "
                f"{report['record_and_artifact_inventory']['generated_rule_pack_ready']}"
            ),
        ]
    )
    lines.extend(
        [
            "",
            "Applicable Authority Findings (ordered by rule ID)",
        ]
    )
    for index, row in enumerate(report["authority_findings"], start=1):
        lines.extend(
            _wrap_pdf_line(
                f"{index}. {row['rule_id']} ({row.get('authority_category')}) - "
                f"{row.get('compliance_status')} - EA: "
                f"{_evidence_cell(row.get('ea_package_evidence', []))} - Source: "
                f"{_evidence_cell(row.get('source_library_evidence', []))} - Confirmations: "
                f"{', '.join(row.get('implementation_confirmation_ids', [])) or 'None'}"
            )
        )
    lines.extend(
        [
            "",
            "Applicable Forest Plan Standards",
            (
                "Summary: standards shown here are the applicable subset from generated "
                "Forest Plan coverage."
            ),
        ]
    )
    for index, row in enumerate(report["applicable_forest_plan_standards"], start=1):
        lines.extend(
            _wrap_pdf_line(
                f"{index}. {row.get('component_key')} - {row.get('compliance_status')} - "
                f"Package: {_evidence_cell(row.get('package_evidence', []))} - "
                f"Plan: {_evidence_cell(row.get('forest_plan_evidence', []))}"
            )
        )
    lines.extend(
        [
            "",
            "Non-Applicable Authority Boundary",
            (
                "Summary: non-applicable authorities are excluded from compliance findings; "
                f"full appendix {non_applicable['appendix_path']} and coverage certificates "
                f"{non_applicable['coverage_certificates_path']}."
            ),
            "",
            "Implementation Confirmations",
            "Summary: confirmation rows require reviewer confirmation and are not findings.",
        ]
    )
    for index, row in enumerate(report["implementation_confirmation_checklist"], start=1):
        lines.extend(
            _wrap_pdf_line(
                f"{index}. {row.get('label')} - {row.get('status')} - "
                f"{row.get('allowed_report_wording')}"
            )
        )
    lines.extend(
        [
            "",
            "Residual Risks",
            (
                "Summary: deterministic decision-support risk notes with source artifact "
                "pointers, not legal conclusions."
            ),
        ]
    )
    for row in report["residual_risk_register"]:
        lines.extend(
            _wrap_pdf_line(
                f"{row['risk_id']} - {row['rationale']} Source: "
                f"{row['source_artifact_path']} selector {row['source_selector']}."
            )
        )
    return _paginate_pdf_lines(lines, max_lines=44)


def _decision_support_use_note() -> str:
    return (
        "Use this document to inspect generated authority, Forest Plan, implementation "
        "confirmation, residual-risk, and validation evidence for the review. It supports "
        "review and does not replace responsible official, line officer, counsel, or "
        "specialist judgment."
    )


def _review_snapshot_items(report: dict[str, Any]) -> list[str]:
    executive = report["executive_determination"]
    authority_summary = report["applicable_authority_summary"]
    forest = report["forest_plan_consistency"]
    non_applicable = report["non_applicable_authority_boundary"]
    confirmations = report["implementation_confirmation_checklist"]
    residual_risks = report["residual_risk_register"]
    return [
        (
            "Bottom-line determination: "
            f"{executive['decision_support_status']} decision-support status from generated "
            "artifacts; not a legal sufficiency determination or final agency decision."
        ),
        (
            "Authority categories: "
            f"{_format_counts(authority_summary['category_counts'])}; applicable authority "
            f"findings: {authority_summary['applicable_authority_count']}; status counts: "
            f"{_format_counts(authority_summary['status_counts'])}."
        ),
        (
            "Forest Plan basis: "
            f"{forest['plan_consistency_table_package_record_id']} Plan Consistency Table plus "
            f"{forest['component_finding_count']} generated component rows "
            f"({forest['supported_component_count']} supported/applicable, "
            f"{forest['not_applicable_component_count']} not applicable, "
            f"{forest['gap_count']} gaps)."
        ),
        (
            "Applicable standards: "
            f"{forest['applied_standard_count']} of {forest['applicable_standard_count']} "
            "applicable Forest Plan standards are applied with package and plan evidence."
        ),
        (
            "Non-applicable boundary: "
            f"{non_applicable['non_applicable_authority_count']} authorities remain "
            "non-applicable with search coverage and appendix pointers."
        ),
        (
            "Implementation confirmations: "
            f"{len(confirmations)} evidence-linked checklist rows require confirmation and "
            "are not additional compliance findings."
        ),
        (
            "Residual risks: "
            f"{len(residual_risks)} deterministic decision-support notes; "
            f"{_legal_conclusion_risk_count(report)} legal-conclusion flags."
        ),
        (
            "Validation: "
            f"report validation passed={report['validation_and_replay']['passed']}; "
            f"manifest schema {report['manifest']['schema_version']}."
        ),
    ]


def _legal_conclusion_risk_count(report: dict[str, Any]) -> int:
    return sum(
        1
        for risk in report["residual_risk_register"]
        if risk.get("legal_conclusion") is True
    )


def _format_counts(counts: Any) -> str:
    rows = _dict(counts)
    if not rows:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in rows.items())


def _selector_cell(selectors: Any) -> str:
    parts = []
    for selector in _dict_list(selectors):
        artifact_path = str(selector.get("artifact_path") or "").strip()
        selector_text = str(selector.get("selector") or "").strip()
        if artifact_path and selector_text:
            parts.append(f"{artifact_path} :: {selector_text}")
        elif artifact_path:
            parts.append(artifact_path)
        elif selector_text:
            parts.append(selector_text)
    return "; ".join(parts) or "N/A"


def _evidence_cell(evidence_rows: list[dict[str, Any]]) -> str:
    if not evidence_rows:
        return "N/A"
    evidence = evidence_rows[0]
    return (
        f"{evidence.get('citation_label')} - "
        f"{_truncate((evidence.get('text_span') or {}).get('excerpt', ''), 180)}"
    )


def _trace(
    trace_id: str,
    trace_type: str,
    source_artifact_path: Path,
    source_selector: str,
) -> dict[str, str]:
    return {
        "trace_id": trace_id,
        "trace_type": trace_type,
        "source_artifact_path": str(source_artifact_path),
        "source_selector": source_selector,
    }


def _selector(path: Path, selector: str) -> dict[str, str]:
    return {"artifact_path": str(path), "selector": selector}


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _dict_list(value: Any) -> list[dict[str, Any]]:
    return [item for item in _list(value) if isinstance(item, dict)]


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _strings(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item or "").strip()]
    if str(value or "").strip():
        return [str(value)]
    return []


def _int(*values: Any) -> int:
    for value in values:
        if isinstance(value, bool):
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return 0


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _truncate(value: str, max_chars: int) -> str:
    normalized = " ".join(str(value).split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 3].rstrip() + "..."


def _md_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def _wrap_pdf_line(line: str, width: int = 145) -> list[str]:
    if len(line) <= width:
        return [line]
    return textwrap.wrap(
        line,
        width=width,
        subsequent_indent="    ",
        break_long_words=False,
        break_on_hyphens=False,
    )


def _paginate_pdf_lines(lines: list[str], *, max_lines: int) -> list[list[str]]:
    pages: list[list[str]] = []
    page: list[str] = []
    for line in lines:
        if len(page) >= max_lines:
            pages.append(page)
            page = []
        page.append(line)
    if page:
        pages.append(page)
    return pages or [["EA Consistency Decision Support"]]


def _write_simple_pdf(path: Path, pages: list[list[str]], *, title: str) -> None:
    width = 1008
    height = 612
    margin_x = 34
    start_y = 568
    leading = 12
    font_size = 8
    objects: list[bytes | None] = [None, None, None]

    def add_object(payload: bytes) -> int:
        objects.append(payload)
        return len(objects)

    for page_number, page_lines in enumerate(pages, start=1):
        content = _pdf_page_content(
            page_lines,
            page_number=page_number,
            page_count=len(pages),
            title=title,
            margin_x=margin_x,
            start_y=start_y,
            leading=leading,
            font_size=font_size,
        )
        content_id = add_object(
            b"<< /Length "
            + str(len(content)).encode("ascii")
            + b" >>\nstream\n"
            + content
            + b"\nendstream"
        )
        page_id = add_object(
            (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width} {height}] "
                f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_id} 0 R >>"
            ).encode("ascii")
        )
        objects[1] = (objects[1] or b"") + f"{page_id} 0 R ".encode("ascii")

    kids = objects[1] or b""
    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    objects[1] = (
        b"<< /Type /Pages /Kids ["
        + kids
        + b"] /Count "
        + str(len(pages)).encode("ascii")
        + b" >>"
    )
    objects[2] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
    _write_pdf_objects(path, [obj for obj in objects if obj is not None])


def _pdf_page_content(
    lines: list[str],
    *,
    page_number: int,
    page_count: int,
    title: str,
    margin_x: int,
    start_y: int,
    leading: int,
    font_size: int,
) -> bytes:
    commands = [f"BT /F1 {font_size} Tf {leading} TL {margin_x} {start_y} Td"]
    for line in lines:
        commands.append(f"({_pdf_escape(line)}) Tj T*")
    footer_y = 24 - (start_y - len(lines) * leading)
    commands.append(
        f"0 {footer_y} Td ({_pdf_escape(f'{title} | Page {page_number} of {page_count}')}) Tj"
    )
    commands.append("ET")
    return "\n".join(commands).encode("latin-1", errors="replace")


def _pdf_escape(value: str) -> str:
    return (
        _pdf_text(value)
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )


def _pdf_text(value: str) -> str:
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00a7": "Sec.",
    }
    text = str(value)
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _write_pdf_objects(path: Path, objects: list[bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    offsets = []
    payload = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(payload))
        payload.extend(f"{index} 0 obj\n".encode("ascii"))
        payload.extend(obj)
        payload.extend(b"\nendobj\n")
    xref_offset = len(payload)
    payload.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    payload.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        payload.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    payload.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    path.write_bytes(bytes(payload))
