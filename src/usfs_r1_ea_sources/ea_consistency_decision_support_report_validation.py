from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from .ea_consistency_decision_support_models import MANIFEST_SCHEMA_VERSION
from .ea_consistency_decision_support_models import REPORT_SCHEMA_VERSION
from .ea_consistency_decision_support_models import REVIEW_PACKET_ARTIFACT_KEYS
from .ea_consistency_decision_support_models import _DecisionSupportContext
from .ea_consistency_decision_support_models import _LoadedArtifact
from .ea_consistency_decision_support_models import _dict
from .ea_consistency_decision_support_models import _dict_list
from .ea_consistency_decision_support_models import _record_check
from .ea_consistency_decision_support_models import _sha256_file
from .ea_consistency_decision_support_models import _strings
from .ea_consistency_decision_support_models import _utc_now


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
    _validate_report_renderings(
        checks=checks,
        failures=failures,
        report=report,
        markdown_artifact=report_artifacts["markdown"],
        pdf_artifact=report_artifacts["pdf"],
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

    _validate_required_applicable_authority_rows(
        rows=_dict_list(report.get("authority_findings")),
        expected=expected,
        checks=checks,
        failures=failures,
        source_selector="decision_support_report.authority_findings",
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


def _validate_report_renderings(
    *,
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    report: dict[str, Any],
    markdown_artifact: _LoadedArtifact,
    pdf_artifact: _LoadedArtifact,
) -> None:
    markdown = str(markdown_artifact.payload or "")
    pdf_text = _pdf_rendering_text(pdf_artifact.path) if pdf_artifact.exists else ""
    markdown_missing = _missing_markdown_rendering_items(report, markdown)
    _record_check(
        checks,
        failures,
        name="markdown_supervisor_rendering_contract",
        passed=not markdown_missing,
        failure_category="false_negative_synthesis_omission",
        source_selector="decision_support_markdown.supervisor_rendering_contract",
        expected="front matter, snapshot, summaries, caveat, counts, and evidence tables",
        actual=markdown_missing,
    )
    markdown_order_failures = _rendering_order_failures(
        markdown,
        [
            "## How To Use This Document",
            "## Review Snapshot",
            "## Applicable Authority Summary",
            "## Authority Findings",
            "## Forest Plan Consistency",
            "## Applicable Forest Plan Standards",
            "## Non-Applicable Authority Boundary",
            "## Implementation Confirmation Checklist",
            "## Residual Risk Register",
            "## Validation and Replay",
        ],
    )
    _record_check(
        checks,
        failures,
        name="markdown_supervisor_sections_are_ordered",
        passed=not markdown_order_failures,
        failure_category="false_negative_synthesis_omission",
        source_selector="decision_support_markdown.section_order",
        expected="supervisor summary precedes long evidence tables",
        actual=markdown_order_failures,
    )
    pdf_missing = _missing_pdf_rendering_items(report, pdf_text)
    _record_check(
        checks,
        failures,
        name="pdf_supervisor_rendering_contract",
        passed=not pdf_missing,
        failure_category="false_negative_synthesis_omission",
        source_selector="decision_support_pdf.supervisor_rendering_contract",
        expected="front matter, snapshot, table summaries, caveat, counts, and report sections",
        actual=pdf_missing,
    )


def _missing_markdown_rendering_items(report: dict[str, Any], markdown: str) -> list[str]:
    forest = _dict(report.get("forest_plan_consistency"))
    authority_summary = _dict(report.get("applicable_authority_summary"))
    non_applicable = _dict(report.get("non_applicable_authority_boundary"))
    required_fragments = {
        "how_to_use_heading": "## How To Use This Document",
        "decision_use_caveat": "does not replace responsible official, line officer, counsel",
        "review_snapshot_heading": "## Review Snapshot",
        "bottom_line": "Bottom-line determination:",
        "authority_categories": "Authority categories:",
        "authority_count": (
            f"applicable authority findings: "
            f"{authority_summary.get('applicable_authority_count')}"
        ),
        "forest_plan_basis": (
            f"Forest Plan basis: {forest.get('plan_consistency_table_package_record_id')} "
            "Plan Consistency Table"
        ),
        "applicable_standard_count": (
            f"Applicable standards: {forest.get('applied_standard_count')} of "
            f"{forest.get('applicable_standard_count')} applicable Forest Plan standards"
        ),
        "non_applicable_boundary": (
            f"Non-applicable boundary: "
            f"{non_applicable.get('non_applicable_authority_count')} authorities"
        ),
        "implementation_confirmations": (
            f"Implementation confirmations: "
            f"{len(_dict_list(report.get('implementation_confirmation_checklist')))} "
            "evidence-linked checklist rows"
        ),
        "residual_risks": (
            f"Residual risks: {len(_dict_list(report.get('residual_risk_register')))} "
            "deterministic decision-support notes"
        ),
        "authority_table": (
            "| Rule | Category | Status | EA evidence | Source evidence | "
            "Implementation confirmations |"
        ),
        "standard_table": "| Standard | Compliance | Package evidence | Forest Plan evidence |",
        "confirmation_table": (
            "| Confirmation | Status | Decision-support wording | Evidence selectors |"
        ),
        "risk_source_pointer": "Source: `",
        "validation_heading": "## Validation and Replay",
    }
    return [
        key
        for key, fragment in required_fragments.items()
        if fragment not in markdown
    ]


def _missing_pdf_rendering_items(report: dict[str, Any], pdf_text: str) -> list[str]:
    forest = _dict(report.get("forest_plan_consistency"))
    non_applicable = _dict(report.get("non_applicable_authority_boundary"))
    required_fragments = {
        "title": "EA Consistency Decision Support",
        "bottom_line": "Bottom-line determination:",
        "decision_use_caveat": "does not replace responsible official",
        "how_to_use": "How To Use This Document",
        "review_snapshot": "Review Snapshot",
        "table_summaries": "Table Summaries",
        "authority_findings": "Applicable Authority Findings",
        "forest_plan_standards": "Applicable Forest Plan Standards",
        "non_applicable_boundary": "Non-Applicable Authority Boundary",
        "implementation_confirmations": "Implementation Confirmations",
        "residual_risks": "Residual Risks",
        "applicable_standard_count": (
            f"{forest.get('applied_standard_count')} of "
            f"{forest.get('applicable_standard_count')} applicable standards"
        ),
        "non_applicable_count": (
            f"{non_applicable.get('non_applicable_authority_count')} authorities"
        ),
    }
    return [
        key
        for key, fragment in required_fragments.items()
        if fragment not in pdf_text
    ]


def _rendering_order_failures(text: str, ordered_fragments: list[str]) -> list[str]:
    failures = []
    previous_index = -1
    previous_fragment = ""
    for fragment in ordered_fragments:
        current_index = text.find(fragment)
        if current_index == -1:
            failures.append(f"missing:{fragment}")
        elif current_index < previous_index:
            failures.append(f"out_of_order:{previous_fragment}>{fragment}")
        else:
            previous_index = current_index
            previous_fragment = fragment
    return failures


def _pdf_rendering_text(path: Path) -> str:
    try:
        return path.read_bytes().decode("latin-1", errors="ignore")
    except OSError:
        return ""


def _current_input_hashes(context: _DecisionSupportContext) -> dict[str, str]:
    input_hashes = {
        f"{key}_sha256": str(artifact.sha256)
        for key, artifact in sorted(context.artifacts.items())
        if key not in REVIEW_PACKET_ARTIFACT_KEYS
        if artifact.sha256 is not None
    }
    input_hashes["decision_support_config_sha256"] = _sha256_file(context.config_path)
    input_hashes["decision_support_expected_summary_sha256"] = _sha256_file(
        context.expected_summary_path
    )
    return input_hashes


def _validate_required_applicable_authority_rows(
    *,
    rows: list[dict[str, Any]],
    expected: dict[str, Any],
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    source_selector: str,
) -> None:
    required_rows = _dict_list(expected.get("required_applicable_authority_rows"))
    if not required_rows:
        return
    rows_by_rule_id = {
        str(row.get("rule_id")): row
        for row in rows
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
    _record_check(
        checks,
        failures,
        name="required_applicable_authority_rows_present",
        passed=not missing and not mismatches,
        failure_category="missing_applicable_authority_row",
        source_selector=source_selector,
        expected=[str(row.get("rule_id")) for row in required_rows],
        actual={"missing": missing, "mismatches": mismatches},
    )


def _required_authority_row_mismatch_fields(
    *,
    actual: dict[str, Any],
    required: dict[str, Any],
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
        actual_family_ids = set(_strings(actual.get("authority_family_ids")))
        if actual.get("authority_family_id") != family_id and family_id not in actual_family_ids:
            mismatch_fields.append("authority_family_id")
    return mismatch_fields
