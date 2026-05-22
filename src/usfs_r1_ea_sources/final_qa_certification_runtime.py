from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any

from .final_qa_certification_common import _add_check
from .final_qa_certification_common import _checks_passed
from .final_qa_certification_common import _output_paths
from .final_qa_certification_common import _read_json
from .final_qa_certification_common import _resolve_artifact_path
from .final_qa_certification_common import _selector_value
from .final_qa_certification_common import _sha256_file
from .final_qa_certification_common import _summarize_checks
from .final_qa_certification_common import _validation_result_payload
from .final_qa_certification_common import DEFAULT_CONFIG_PATH
from .final_qa_certification_common import DEFAULT_EXPECTED_SUMMARY_PATH
from .final_qa_certification_common import FinalQACertificationResult
from .final_qa_certification_common import MANIFEST_FILENAME
from .final_qa_certification_common import REPORT_FILENAME
from .final_qa_certification_common import _write_json
from .final_qa_certification_counts import _current_promotion_suite_self_reference_allowed
from .final_qa_certification_counts import _derive_actual_counts
from .final_qa_certification_counts import _outer_gate_hash_drift_allowed
from .final_qa_certification_counts import _validate_actual_counts
from .final_qa_certification_report import _build_report
from .final_qa_certification_report import _pdf_lines
from .final_qa_certification_report import _render_markdown
from .final_qa_certification_report import _write_simple_pdf
from .final_qa_certification_validation import _load_output_bytes
from .final_qa_certification_validation import _load_output_json
from .final_qa_certification_validation import _load_output_text
from .final_qa_certification_validation import _read_required_json
from .final_qa_certification_validation import _validate_configured_source_selectors
from .final_qa_certification_validation import _validate_identity
from .final_qa_certification_validation import _validate_manifest
from .final_qa_certification_validation import _validate_pdf
from .final_qa_certification_validation import _validate_rendered_text
from .final_qa_certification_validation import _validate_report
from .final_qa_certification_validation import _validate_required_applicable_authority_rows
from .final_qa_certification_validation import _validate_source_pdf_header
from .final_qa_certification_validation import _validate_validation_result


def run_final_qa_certification(
    *,
    output_dir: Path = Path("source_library"),
    review_id: str | None = None,
    config_path: Path = DEFAULT_CONFIG_PATH,
    expected_summary_path: Path = DEFAULT_EXPECTED_SUMMARY_PATH,
    results_dir: Path | None = None,
) -> FinalQACertificationResult:
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


def infer_final_qa_contract_paths(report_dir: Path) -> tuple[Path | None, Path | None]:
    report_dir = Path(report_dir)
    report_path = report_dir / REPORT_FILENAME
    manifest_path = report_dir / MANIFEST_FILENAME
    manifest = None
    report = None
    if manifest_path.exists():
        try:
            manifest = _read_json(manifest_path)
        except (OSError, ValueError, json.JSONDecodeError):
            manifest = None
    if report_path.exists():
        try:
            report = _read_json(report_path)
        except (OSError, ValueError, json.JSONDecodeError):
            report = None
    candidates: list[tuple[Any, Any]] = []
    if isinstance(manifest, Mapping):
        candidates.append(
            (
                manifest.get("config_hashes"),
                _selector_value(manifest, "artifact_freshness_ledger"),
            )
        )
    if isinstance(report, Mapping):
        candidates.append(
            (
                _selector_value(report, "manifest.config_hashes"),
                _selector_value(report, "artifact_freshness_ledger"),
            )
        )
    for config_hashes, freshness in candidates:
        if isinstance(config_hashes, Mapping):
            config_path = config_hashes.get("config_path")
            expected_summary_path = config_hashes.get("expected_summary_path")
            if config_path or expected_summary_path:
                return (
                    Path(str(config_path)) if config_path else None,
                    Path(str(expected_summary_path)) if expected_summary_path else None,
                )
        if isinstance(freshness, Mapping):
            config_path = freshness.get("config_path")
            expected_summary_path = freshness.get("expected_summary_path")
            if config_path or expected_summary_path:
                return (
                    Path(str(config_path)) if config_path else None,
                    Path(str(expected_summary_path)) if expected_summary_path else None,
                )
    return None, None


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
