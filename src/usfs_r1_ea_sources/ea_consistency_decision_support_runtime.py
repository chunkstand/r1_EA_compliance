from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from .ea_consistency_decision_support_inputs import _load_artifact
from .ea_consistency_decision_support_inputs import _load_report_artifacts
from .ea_consistency_decision_support_inputs import _load_required_artifacts
from .ea_consistency_decision_support_inputs import _report_paths
from .ea_consistency_decision_support_inputs import _resolve_validation_contract_paths
from .ea_consistency_decision_support_inputs import _selected_review_id_for_validation
from .ea_consistency_decision_support_inputs import _validate_inputs
from .ea_consistency_decision_support_models import DEFAULT_CONFIG_PATH
from .ea_consistency_decision_support_models import DEFAULT_EXPECTED_SUMMARY_PATH
from .ea_consistency_decision_support_models import _DecisionSupportContext
from .ea_consistency_decision_support_models import EAConsistencyDecisionSupportResult
from .ea_consistency_decision_support_models import EAConsistencyDecisionSupportValidationResult
from .ea_consistency_decision_support_models import _dict
from .ea_consistency_decision_support_models import _dict_list
from .ea_consistency_decision_support_models import _read_json
from .ea_consistency_decision_support_models import _write_json
from .ea_consistency_decision_support_models import _write_simple_pdf
from .ea_consistency_decision_support_rendering import _report_markdown
from .ea_consistency_decision_support_rendering import _report_pdf_pages
from .ea_consistency_decision_support_report import _build_report
from .ea_consistency_decision_support_report import _generation_summary
from .ea_consistency_decision_support_report_validation import _validate_report_artifact_family


def _report_source_set_id(report_artifacts: dict[str, Any]) -> str:
    for key in ("report", "manifest"):
        payload = _dict(report_artifacts.get(key).payload if report_artifacts.get(key) else None)
        if payload.get("source_set_id"):
            return str(payload["source_set_id"])
        manifest = _dict(payload.get("manifest"))
        if manifest.get("source_set_id"):
            return str(manifest["source_set_id"])
    return ""


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
        config=config,
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
            config=config,
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
