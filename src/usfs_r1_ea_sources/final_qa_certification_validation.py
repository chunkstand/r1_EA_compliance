from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any

from .final_qa_certification_common import _add_check
from .final_qa_certification_common import _read_json
from .final_qa_certification_common import _resolve_artifact_path
from .final_qa_certification_common import _safe_int
from .final_qa_certification_common import _selector_value
from .final_qa_certification_common import _validation_output_hashes
from .final_qa_certification_common import HUMAN_JUDGMENT_CAVEAT
from .final_qa_certification_common import MANIFEST_FILENAME
from .final_qa_certification_common import MARKDOWN_FILENAME
from .final_qa_certification_common import OutputPaths
from .final_qa_certification_common import PDF_FILENAME
from .final_qa_certification_common import REPORT_FILENAME
from .final_qa_certification_common import VALIDATION_FILENAME
from .final_qa_certification_common import VALIDATION_SCHEMA_VERSION


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
        details={"selector": "applicability_partition.non_applicable_boundary_evidence"},
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
        passed=_finding_trace_ids_present(findings, config),
        category="missing_citation_or_source_selector",
        details={"selector": "finding_qa.findings[].trace_ids"},
    )
    accepted_pending_count = _selector_value(
        report,
        "accepted_v1_risk_ledger.accepted_pending_count",
    )
    expected_accepted_pending_count = expected["accepted_v1_risk_ledger"][
        "accepted_pending_count"
    ]
    _add_check(
        checks,
        name="accepted_v1_risk_visible",
        passed=accepted_pending_count == expected_accepted_pending_count
        and (
            expected_accepted_pending_count == 0
            or bool(_selector_value(report, "accepted_v1_risk_ledger.risks"))
        ),
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
        and _selector_value(report, "decision_support_qa.litigation_risk_legal_conclusion_count") == 0,
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
    if path.exists():
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
    if packet_path.exists():
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


def _finding_trace_ids_present(rows: list[Any], config: Mapping[str, Any]) -> bool:
    if not rows:
        return False
    evidence_policy = config.get("authority_evidence_policy")
    allowed_single_evidence_statuses = {
        str(status)
        for status in (
            evidence_policy.get("allow_single_evidence_statuses", [])
            if isinstance(evidence_policy, Mapping)
            else []
        )
    }
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
        missing_dual_evidence_allowed = (
            str(row.get("status") or "") in allowed_single_evidence_statuses
        )
        for pointer_key in ("ea_package_evidence", "source_library_evidence"):
            pointer = pointers.get(pointer_key)
            if pointer is None and missing_dual_evidence_allowed:
                continue
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
