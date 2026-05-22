from __future__ import annotations

from pathlib import Path
from typing import Any

from .project_sow_package_common import _check
from .project_sow_package_common import _is_empty
from .project_sow_package_common import _list
from .project_sow_package_common import _read_json
from .project_sow_package_common import _sha256_file
from .project_sow_package_common import _sha256_json_payload
from .project_sow_package_common import _slug
from .project_sow_package_common import _strings
from .project_sow_package_common import _write_json
from .project_sow_package_draft import validate_project_sow_intake
from .project_sow_package_ea_handoff import run_project_sow_ea_package_handoff
from .project_sow_package_eval import run_project_sow_eval
from .project_sow_package_models import DEFAULT_AUTHORITY_INVENTORY_PATH
from .project_sow_package_models import DEFAULT_PROJECT_SOW_EA_HANDOFF_RULES_CONFIG_PATH
from .project_sow_package_models import DEFAULT_PROJECT_SOW_EVAL_CONFIG_PATH
from .project_sow_package_models import DEFAULT_PROJECT_SOW_INTAKE_TEMPLATE_PATH
from .project_sow_package_models import DEFAULT_PROJECT_SOW_OPERATIONAL_GATE_OUTPUT_DIR
from .project_sow_package_models import DEFAULT_RESOURCE_SCOPE_CONFIG_PATH
from .project_sow_package_models import PROJECT_SOW_OPERATIONAL_GATE_CLOSEOUT_CONTRACT_FIELDS
from .project_sow_package_models import PROJECT_SOW_OPERATIONAL_GATE_DOC_REQUIREMENTS
from .project_sow_package_models import PROJECT_SOW_OPERATIONAL_GATE_JSON_PATHS
from .project_sow_package_models import PROJECT_SOW_OPERATIONAL_GATE_SUMMARY_SCHEMA_VERSION
from .project_sow_package_models import ProjectSowOperationalGateResult

def run_project_sow_operational_gate(
    *,
    output_dir: Path = DEFAULT_PROJECT_SOW_OPERATIONAL_GATE_OUTPUT_DIR,
    eval_config_path: Path = DEFAULT_PROJECT_SOW_EVAL_CONFIG_PATH,
    template_intake_path: Path = DEFAULT_PROJECT_SOW_INTAKE_TEMPLATE_PATH,
    resource_scope_config_path: Path = DEFAULT_RESOURCE_SCOPE_CONFIG_PATH,
    authority_inventory_path: Path = DEFAULT_AUTHORITY_INVENTORY_PATH,
    handoff_rules_config_path: Path = DEFAULT_PROJECT_SOW_EA_HANDOFF_RULES_CONFIG_PATH,
    doc_requirements: tuple[tuple[Path, tuple[str, ...]], ...] = PROJECT_SOW_OPERATIONAL_GATE_DOC_REQUIREMENTS,
) -> ProjectSowOperationalGateResult:
    output_dir = Path(output_dir)
    eval_config_path = Path(eval_config_path)
    template_intake_path = Path(template_intake_path)
    resource_scope_config_path = Path(resource_scope_config_path)
    authority_inventory_path = Path(authority_inventory_path)
    handoff_rules_config_path = Path(handoff_rules_config_path)

    summary_path = output_dir / "project_sow_operational_gate_summary.json"
    markdown_path = output_dir / "project_sow_operational_readiness_report.md"
    eval_output_dir = output_dir / "project_sow_eval"
    handoff_output_dir = output_dir / "ea_package_handoff"

    eval_config = _read_json(eval_config_path)
    intake_validations = _project_sow_operational_gate_intake_validations(
        eval_config=eval_config,
        template_intake_path=template_intake_path,
        resource_scope_config_path=resource_scope_config_path,
        authority_inventory_path=authority_inventory_path,
    )
    eval_result = run_project_sow_eval(
        eval_config_path=eval_config_path,
        output_dir=eval_output_dir,
        resource_scope_config_path=resource_scope_config_path,
        authority_inventory_path=authority_inventory_path,
    )
    handoff_smoke = _project_sow_operational_gate_handoff_smoke(
        eval_summary=eval_result.summary,
        output_dir=handoff_output_dir,
        handoff_rules_config_path=handoff_rules_config_path,
    )
    json_doc_checks = _project_sow_operational_gate_json_doc_checks(
        doc_requirements=doc_requirements
    )
    closeout_contract = _project_sow_operational_gate_closeout_contract(
        output_dir=output_dir,
        eval_output_dir=eval_output_dir,
        handoff_output_dir=handoff_output_dir,
        doc_requirements=doc_requirements,
    )
    checks = _project_sow_operational_gate_checks(
        closeout_contract=closeout_contract,
        intake_validations=intake_validations,
        eval_summary=eval_result.summary,
        handoff_smoke=handoff_smoke,
        json_doc_checks=json_doc_checks,
    )
    summary = {
        "artifact_boundaries": [
            "Generated package, eval, and handoff outputs stay under the selected output directory.",
            "The gate does not stage generated source_library artifacts.",
            "The gate does not run downloader, extraction, applicability, generated rule-pack, compliance review, phase-eval, legal sufficiency, or final agency decision workflows.",
        ],
        "authority_inventory_path": str(authority_inventory_path),
        "checks": checks,
        "ci_policy": {
            "reason": "The Sequence 7 gate writes generated reports and package smoke outputs under a caller-selected directory; CI adoption should be a separate explicit milestone.",
            "status": "local-only",
        },
        "closeout_contract": closeout_contract,
        "eval_config_path": str(eval_config_path),
        "failed_checks": [check for check in checks if not check["passed"]],
        "handoff_rules_config_path": str(handoff_rules_config_path),
        "intake_validation_count": len(intake_validations),
        "intake_validations": intake_validations,
        "markdown_path": str(markdown_path),
        "output_dir": str(output_dir),
        "passed": all(check["passed"] for check in checks),
        "proving_eval": _project_sow_operational_gate_eval_summary(eval_result.summary),
        "resource_scope_config_path": str(resource_scope_config_path),
        "schema_version": PROJECT_SOW_OPERATIONAL_GATE_SUMMARY_SCHEMA_VERSION,
        "summary_path": str(summary_path),
        "template_intake_path": str(template_intake_path),
        "tracked_docs_schema_checks": json_doc_checks,
        "written_outputs": {
            "handoff_output_dir": str(handoff_output_dir),
            "project_sow_eval_output_dir": str(eval_output_dir),
        },
    }
    summary["ea_handoff_smoke"] = handoff_smoke
    markdown = _render_project_sow_operational_gate_markdown(summary)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary["output_written"] = True
    summary_content_hash = _sha256_json_payload(summary)
    _write_json(summary_path, summary)
    markdown_path.write_text(markdown, encoding="utf-8")
    summary["output_hashes"] = {
        "project_sow_ea_package_handoff_markdown_sha256": handoff_smoke.get(
            "output_hashes", {}
        ).get("project_sow_ea_package_handoff_markdown_sha256"),
        "project_sow_ea_package_handoff_sha256": handoff_smoke.get(
            "output_hashes", {}
        ).get("project_sow_ea_package_handoff_sha256"),
        "project_sow_eval_summary_sha256": _sha256_file(eval_result.summary_path),
        "project_sow_operational_gate_summary_content_sha256": summary_content_hash,
        "project_sow_operational_readiness_report_sha256": _sha256_file(markdown_path),
    }
    _write_json(summary_path, summary)
    markdown_path.write_text(
        _render_project_sow_operational_gate_markdown(summary),
        encoding="utf-8",
    )
    return ProjectSowOperationalGateResult(
        output_dir=output_dir,
        summary_path=summary_path,
        markdown_path=markdown_path,
        summary=summary,
    )

def _project_sow_operational_gate_intake_validations(
    *,
    eval_config: dict[str, Any],
    template_intake_path: Path,
    resource_scope_config_path: Path,
    authority_inventory_path: Path,
) -> list[dict[str, Any]]:
    targets = [
        {
            "intake_path": str(template_intake_path),
            "target_id": "land-exchange-template",
            "target_type": "template",
        }
    ]
    for case in _list(eval_config.get("eval_cases")):
        if not isinstance(case, dict):
            continue
        intake_path = str(case.get("intake_path") or "")
        case_id = _slug(str(case.get("case_id") or Path(intake_path).stem or "eval-case"))
        targets.append(
            {
                "case_id": case_id,
                "intake_path": intake_path,
                "target_id": case_id,
                "target_type": "proving_intake",
            }
        )
    validations = []
    for target in targets:
        result = validate_project_sow_intake(
            intake_path=Path(str(target["intake_path"])),
            resource_scope_config_path=resource_scope_config_path,
            authority_inventory_path=authority_inventory_path,
        )
        validations.append(
            {
                "failed_validation_check_names": [
                    str(check.get("name"))
                    for check in _list(result.summary.get("failed_validation_checks"))
                    if isinstance(check, dict)
                ],
                "intake_path": str(result.intake_path),
                "output_written": bool(result.summary.get("output_written")),
                "passed": bool(result.summary.get("passed")),
                "project_id": result.summary.get("project_id"),
                "proposed_action_resource_area_count": result.summary.get(
                    "proposed_action_resource_area_count"
                ),
                "resource_scope_count": result.summary.get("resource_scope_count"),
                "target_id": target["target_id"],
                "target_type": target["target_type"],
                "validation_failure_count": result.summary.get("validation_failure_count"),
                "validation_only": bool(result.summary.get("validation_only")),
            }
        )
    return validations


def _project_sow_operational_gate_handoff_smoke(
    *,
    eval_summary: dict[str, Any],
    output_dir: Path,
    handoff_rules_config_path: Path,
) -> dict[str, Any]:
    cases = [
        case
        for case in _list(eval_summary.get("cases"))
        if isinstance(case, dict)
    ]
    east_crazies_case = next(
        (
            case
            for case in cases
            if str(case.get("case_id")) == "east-crazies-land-exchange"
        ),
        cases[0] if cases else {},
    )
    package_path = Path(
        str(
            east_crazies_case.get("output_paths", {}).get("package")
            if isinstance(east_crazies_case.get("output_paths"), dict)
            else ""
        )
    )
    if not package_path.is_file():
        return {
            "case_id": east_crazies_case.get("case_id"),
            "output_written": False,
            "package_path": str(package_path),
            "passed": False,
            "slot_count": 0,
            "validation_failure_count": 1,
        }
    result = run_project_sow_ea_package_handoff(
        package_path=package_path,
        output_path=output_dir / "project_sow_ea_package_handoff.json",
        markdown_path=output_dir / "project_sow_ea_package_handoff.md",
        handoff_rules_config_path=handoff_rules_config_path,
    )
    return {
        "case_id": east_crazies_case.get("case_id"),
        "failed_validation_checks": result.summary.get("failed_validation_checks"),
        "markdown_path": str(result.markdown_path),
        "output_path": str(result.output_path),
        "output_hashes": result.summary.get("output_hashes") or {},
        "output_written": bool(result.summary.get("output_written")),
        "package_path": str(package_path),
        "passed": bool(result.summary.get("passed")),
        "slot_category_counts": result.summary.get("slot_category_counts") or {},
        "slot_count": result.summary.get("slot_count", 0),
        "validation_check_count": result.summary.get("validation_check_count", 0),
        "validation_failure_count": result.summary.get("validation_failure_count", 0),
    }


def _project_sow_operational_gate_json_doc_checks(
    *, doc_requirements: tuple[tuple[Path, tuple[str, ...]], ...]
) -> dict[str, Any]:
    invalid_json_paths = []
    missing_doc_terms = []
    for path in PROJECT_SOW_OPERATIONAL_GATE_JSON_PATHS:
        try:
            _read_json(path)
        except ValueError as exc:
            invalid_json_paths.append({"error": str(exc), "path": str(path)})
    for path, required_terms in doc_requirements:
        try:
            text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            missing_doc_terms.append({"missing_terms": list(required_terms), "path": str(path)})
            continue
        missing_terms = [term for term in required_terms if term not in text]
        if missing_terms:
            missing_doc_terms.append({"missing_terms": missing_terms, "path": str(path)})
    return {
        "checked_doc_paths": [str(path) for path, _terms in doc_requirements],
        "checked_json_paths": [str(path) for path in PROJECT_SOW_OPERATIONAL_GATE_JSON_PATHS],
        "docs_updated": not missing_doc_terms,
        "invalid_json_paths": invalid_json_paths,
        "json_paths_valid": not invalid_json_paths,
        "missing_doc_terms": missing_doc_terms,
    }


def _project_sow_operational_gate_closeout_contract(
    *,
    output_dir: Path,
    eval_output_dir: Path,
    handoff_output_dir: Path,
    doc_requirements: tuple[tuple[Path, tuple[str, ...]], ...],
) -> dict[str, Any]:
    return {
        "artifact_boundaries": [
            "Generated outputs stay under the selected output directory.",
            "Ignored generated source_library outputs remain unstaged.",
            "The command is a planning-lane gate, not a downstream review gate.",
        ],
        "ci_policy": {
            "status": "local-only",
            "promotion_path": "Treat broader CI integration as a separate explicit milestone.",
        },
        "downstream_use": "Use as Project SOW operational-readiness closeout evidence only.",
        "generated_outputs": {
            "ea_handoff_smoke_dir": str(handoff_output_dir),
            "operational_gate_summary": str(
                output_dir / "project_sow_operational_gate_summary.json"
            ),
            "operational_readiness_report": str(
                output_dir / "project_sow_operational_readiness_report.md"
            ),
            "project_sow_eval_dir": str(eval_output_dir),
        },
        "must_not_infer": [
            "Future EA package artifacts exist.",
            "Authority applicability or non-applicability has been decided.",
            "Generated rule-pack readiness has been established.",
            "Compliance findings, legal advice, legal sufficiency conclusions, or final agency decisions have been made.",
        ],
        "required_green_checks": [
            "project_sow_operational_gate_intake_validations_passed",
            "project_sow_operational_gate_intake_validations_no_outputs",
            "project_sow_operational_gate_proving_eval_passed",
            "project_sow_operational_gate_proving_case_count",
            "project_sow_operational_gate_package_outputs_written",
            "project_sow_operational_gate_rendering_checks_passed",
            "project_sow_operational_gate_system_misses_clear",
            "project_sow_operational_gate_intake_omissions_clear",
            "project_sow_operational_gate_ea_handoff_passed",
            "project_sow_operational_gate_ea_handoff_slots_stable",
            "project_sow_operational_gate_json_inputs_valid",
            "project_sow_operational_gate_docs_updated",
            "project_sow_operational_gate_closeout_contract_complete",
        ],
        "schema_version": "project-sow-operational-gate-closeout-contract-v0",
        "tracked_doc_paths": [str(path) for path, _terms in doc_requirements],
        "tracked_json_paths": [str(path) for path in PROJECT_SOW_OPERATIONAL_GATE_JSON_PATHS],
    }


def _project_sow_operational_gate_closeout_contract_errors(
    contract: dict[str, Any],
) -> list[str]:
    errors = []
    for field in PROJECT_SOW_OPERATIONAL_GATE_CLOSEOUT_CONTRACT_FIELDS:
        if _is_empty(contract.get(field)):
            errors.append(f"closeout_contract.{field}: required")
    if contract.get("schema_version") != "project-sow-operational-gate-closeout-contract-v0":
        errors.append("closeout_contract.schema_version: unsupported")
    ci_policy = contract.get("ci_policy") if isinstance(contract.get("ci_policy"), dict) else {}
    if ci_policy.get("status") != "local-only":
        errors.append("closeout_contract.ci_policy.status: must be local-only")
    return errors


def _project_sow_operational_gate_checks(
    *,
    closeout_contract: dict[str, Any],
    intake_validations: list[dict[str, Any]],
    eval_summary: dict[str, Any],
    handoff_smoke: dict[str, Any],
    json_doc_checks: dict[str, Any],
) -> list[dict[str, Any]]:
    cases = [case for case in _list(eval_summary.get("cases")) if isinstance(case, dict)]
    output_failures = [
        str(case.get("case_id"))
        for case in cases
        if not case.get("actual_metrics", {}).get("output_written")
    ]
    rendering_failures = [
        str(case.get("case_id"))
        for case in cases
        if not case.get("actual_metrics", {}).get("rendering_checks_passed")
        or not case.get("actual_metrics", {}).get("pdf_header_valid")
    ]
    system_miss_total = sum(
        len(_strings(case.get("diagnostics", {}).get("system_miss_resource_area_ids")))
        for case in cases
    )
    intake_omission_total = sum(
        len(_strings(case.get("diagnostics", {}).get("intake_omission_resource_area_ids")))
        for case in cases
    )
    closeout_contract_errors = _project_sow_operational_gate_closeout_contract_errors(
        closeout_contract
    )
    return [
        _check(
            name="project_sow_operational_gate_intake_validations_passed",
            passed=all(validation.get("passed") for validation in intake_validations),
            details={
                "failed_target_ids": [
                    str(validation.get("target_id"))
                    for validation in intake_validations
                    if not validation.get("passed")
                ],
                "validation_count": len(intake_validations),
            },
        ),
        _check(
            name="project_sow_operational_gate_intake_validations_no_outputs",
            passed=all(not validation.get("output_written") for validation in intake_validations),
            details={
                "targets_with_outputs": [
                    str(validation.get("target_id"))
                    for validation in intake_validations
                    if validation.get("output_written")
                ],
            },
        ),
        _check(
            name="project_sow_operational_gate_proving_eval_passed",
            passed=bool(eval_summary.get("passed")),
            details={
                "case_count": eval_summary.get("case_count"),
                "failed_cases": eval_summary.get("failed_cases") or [],
            },
        ),
        _check(
            name="project_sow_operational_gate_proving_case_count",
            passed=int(eval_summary.get("case_count") or 0) >= 3,
            details={"case_count": eval_summary.get("case_count")},
        ),
        _check(
            name="project_sow_operational_gate_package_outputs_written",
            passed=not output_failures and bool(cases),
            details={"failed_case_ids": output_failures},
        ),
        _check(
            name="project_sow_operational_gate_rendering_checks_passed",
            passed=not rendering_failures and bool(cases),
            details={"failed_case_ids": rendering_failures},
        ),
        _check(
            name="project_sow_operational_gate_system_misses_clear",
            passed=system_miss_total == 0,
            details={"system_miss_count": system_miss_total},
        ),
        _check(
            name="project_sow_operational_gate_intake_omissions_clear",
            passed=intake_omission_total == 0,
            details={"intake_omission_count": intake_omission_total},
        ),
        _check(
            name="project_sow_operational_gate_ea_handoff_passed",
            passed=bool(handoff_smoke.get("passed"))
            and bool(handoff_smoke.get("output_written")),
            details={
                "case_id": handoff_smoke.get("case_id"),
                "slot_count": handoff_smoke.get("slot_count"),
                "validation_failure_count": handoff_smoke.get("validation_failure_count"),
            },
        ),
        _check(
            name="project_sow_operational_gate_ea_handoff_slots_stable",
            passed=handoff_smoke.get("slot_count") == 27,
            details={
                "expected_slot_count": 27,
                "slot_category_counts": handoff_smoke.get("slot_category_counts") or {},
                "slot_count": handoff_smoke.get("slot_count"),
            },
        ),
        _check(
            name="project_sow_operational_gate_json_inputs_valid",
            passed=bool(json_doc_checks.get("json_paths_valid")),
            details={"invalid_json_paths": json_doc_checks.get("invalid_json_paths") or []},
        ),
        _check(
            name="project_sow_operational_gate_docs_updated",
            passed=bool(json_doc_checks.get("docs_updated")),
            details={"missing_doc_terms": json_doc_checks.get("missing_doc_terms") or []},
        ),
        _check(
            name="project_sow_operational_gate_closeout_contract_complete",
            passed=not closeout_contract_errors,
            details={"errors": closeout_contract_errors},
        ),
    ]


def _project_sow_operational_gate_eval_summary(
    eval_summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "case_count": eval_summary.get("case_count"),
        "category_totals": eval_summary.get("category_totals") or {},
        "failed_cases": eval_summary.get("failed_cases") or [],
        "output_dir": eval_summary.get("output_dir"),
        "passed": bool(eval_summary.get("passed")),
        "summary_path": eval_summary.get("summary_path"),
    }


def _render_project_sow_operational_gate_markdown(summary: dict[str, Any]) -> str:
    status = "passed" if summary.get("passed") else "failed"
    lines = [
        "# Project SOW Operational Readiness Report",
        "",
        f"Gate status: `{status}`",
        "",
        "## Command",
        "",
        "```bash",
        "PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-operational-gate \\",
        "  --output-dir source_library/project_sow_operational_gate",
        "```",
        "",
        "## CI Policy",
        "",
        f"Status: `{summary.get('ci_policy', {}).get('status')}`",
        "",
        str(summary.get("ci_policy", {}).get("reason") or ""),
        "",
        "## Checks",
        "",
        "| Check | Status |",
        "| --- | --- |",
    ]
    lines.extend(
        f"| `{check.get('name')}` | {'passed' if check.get('passed') else 'failed'} |"
        for check in _list(summary.get("checks"))
        if isinstance(check, dict)
    )
    lines.extend(["", "## Intake Validations", "", "| Target | Type | Status | Scopes | Areas |"])
    lines.append("| --- | --- | --- | ---: | ---: |")
    lines.extend(
        (
            f"| `{validation.get('target_id')}` | {validation.get('target_type')} | "
            f"{'passed' if validation.get('passed') else 'failed'} | "
            f"{validation.get('resource_scope_count')} | "
            f"{validation.get('proposed_action_resource_area_count')} |"
        )
        for validation in _list(summary.get("intake_validations"))
        if isinstance(validation, dict)
    )
    proving_eval = summary.get("proving_eval") if isinstance(summary.get("proving_eval"), dict) else {}
    lines.extend(
        [
            "",
            "## Proving Eval",
            "",
            f"Case count: `{proving_eval.get('case_count')}`",
            "",
            f"Failed cases: `{proving_eval.get('failed_cases')}`",
            "",
            f"Category totals: `{proving_eval.get('category_totals')}`",
            "",
            "## EA Handoff Smoke",
            "",
        ]
    )
    handoff = summary.get("ea_handoff_smoke") if isinstance(summary.get("ea_handoff_smoke"), dict) else {}
    lines.extend(
        [
            f"Case: `{handoff.get('case_id')}`",
            "",
            f"Slot count: `{handoff.get('slot_count')}`",
            "",
            f"Validation failures: `{handoff.get('validation_failure_count')}`",
            "",
            "## Boundaries",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in _strings(summary.get("artifact_boundaries")))
    return "\n".join(lines).rstrip() + "\n"
