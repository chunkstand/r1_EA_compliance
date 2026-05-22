from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .project_sow_package_assembly import _project_sow_resource_scope_records
from .project_sow_package_common import _check
from .project_sow_package_common import _duplicates
from .project_sow_package_common import _is_empty
from .project_sow_package_common import _list
from .project_sow_package_common import _now
from .project_sow_package_common import _read_json
from .project_sow_package_common import _sha256_file
from .project_sow_package_common import _strings
from .project_sow_package_common import _title_from_id
from .project_sow_package_common import _write_json
from .project_sow_package_models import DEFAULT_PROJECT_SOW_EA_HANDOFF_RULES_CONFIG_PATH
from .project_sow_package_models import PACKAGE_SCHEMA_VERSION
from .project_sow_package_models import PROJECT_SOW_EA_HANDOFF_ALLOWED_CATEGORY_APPLIES_TO
from .project_sow_package_models import PROJECT_SOW_EA_HANDOFF_REQUIRED_BOUNDARY_IDS
from .project_sow_package_models import PROJECT_SOW_EA_HANDOFF_RULES_SCHEMA_VERSION
from .project_sow_package_models import PROJECT_SOW_EA_HANDOFF_SCHEMA_VERSION
from .project_sow_package_models import PROJECT_SOW_EA_HANDOFF_SUMMARY_SCHEMA_VERSION
from .project_sow_package_models import ProjectSowEaPackageHandoffResult

def run_project_sow_ea_package_handoff(
    *,
    package_path: Path,
    output_path: Path | None = None,
    markdown_path: Path | None = None,
    handoff_rules_config_path: Path = DEFAULT_PROJECT_SOW_EA_HANDOFF_RULES_CONFIG_PATH,
) -> ProjectSowEaPackageHandoffResult:
    package_path = Path(package_path)
    output_path = (
        Path(output_path)
        if output_path is not None
        else package_path.with_name("project_sow_ea_package_handoff.json")
    )
    markdown_path = (
        Path(markdown_path)
        if markdown_path is not None
        else package_path.with_name("project_sow_ea_package_handoff.md")
    )
    handoff_rules_config_path = Path(handoff_rules_config_path)
    package = _read_json(package_path)
    rules_config = _read_json(handoff_rules_config_path)
    validation = _validate_project_sow_ea_handoff_inputs(
        package=package,
        rules_config=rules_config,
    )
    summary = _project_sow_ea_handoff_summary(
        handoff={},
        markdown_path=markdown_path,
        output_path=output_path,
        package=package,
        package_path=package_path,
        rules_config_path=handoff_rules_config_path,
        validation=validation,
    )
    if not validation["passed"]:
        return ProjectSowEaPackageHandoffResult(
            output_path=output_path,
            markdown_path=markdown_path,
            summary=summary,
        )
    handoff = _build_project_sow_ea_handoff(
        package=package,
        package_path=package_path,
        rules_config=rules_config,
        rules_config_path=handoff_rules_config_path,
        validation=validation,
    )
    markdown = _render_project_sow_ea_handoff_markdown(handoff)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(output_path, handoff)
    markdown_path.write_text(markdown, encoding="utf-8")
    summary = _project_sow_ea_handoff_summary(
        handoff=handoff,
        markdown_path=markdown_path,
        output_path=output_path,
        package=package,
        package_path=package_path,
        rules_config_path=handoff_rules_config_path,
        validation=validation,
    )
    summary["output_written"] = True
    summary["output_hashes"] = {
        "project_sow_ea_package_handoff_markdown_sha256": _sha256_file(markdown_path),
        "project_sow_ea_package_handoff_sha256": _sha256_file(output_path),
    }
    return ProjectSowEaPackageHandoffResult(
        output_path=output_path,
        markdown_path=markdown_path,
        summary=summary,
    )

def _validate_project_sow_ea_handoff_inputs(
    *,
    package: dict[str, Any],
    rules_config: dict[str, Any],
) -> dict[str, Any]:
    categories = _project_sow_ea_handoff_categories(rules_config)
    category_ids = {str(category.get("category_id") or "") for category in categories}
    category_errors = _project_sow_ea_handoff_category_errors(categories)
    rules = _project_sow_ea_handoff_category_rules(rules_config)
    rule_errors = _project_sow_ea_handoff_rule_errors(
        categories=categories,
        rules=rules,
    )
    unknown_rule_category_ids = sorted(
        {
            str(rule.get("category_id") or "")
            for rule in rules
            if str(rule.get("category_id") or "") not in category_ids
        }
    )
    required_category_ids = _strings(rules_config.get("required_category_ids"))
    missing_required_category_ids = sorted(set(required_category_ids) - category_ids)
    boundary_errors = _project_sow_ea_handoff_boundary_errors(rules_config)
    boundary_ids = {
        str(boundary.get("boundary_id") or "")
        for boundary in _project_sow_ea_handoff_boundaries(rules_config)
    }
    missing_boundary_ids = sorted(
        set(PROJECT_SOW_EA_HANDOFF_REQUIRED_BOUNDARY_IDS) - boundary_ids
    )
    resource_scopes = _project_sow_resource_scope_records(package)
    slots = _project_sow_ea_handoff_slots(package=package, rules_config=rules_config)
    slot_errors = _project_sow_ea_handoff_slot_errors(slots)
    checks = [
        _check(
            name="project_sow_package_schema_supported",
            passed=package.get("schema_version") == PACKAGE_SCHEMA_VERSION,
            details={"schema_version": package.get("schema_version")},
        ),
        _check(
            name="project_sow_package_validation_passed",
            passed=package.get("validation", {}).get("passed") is True,
            details={"validation_passed": package.get("validation", {}).get("passed")},
        ),
        _check(
            name="project_sow_package_has_resource_scopes",
            passed=bool(resource_scopes),
            details={"resource_scope_count": len(resource_scopes)},
        ),
        _check(
            name="ea_handoff_rules_schema_supported",
            passed=rules_config.get("schema_version")
            == PROJECT_SOW_EA_HANDOFF_RULES_SCHEMA_VERSION,
            details={"schema_version": rules_config.get("schema_version")},
        ),
        _check(
            name="ea_handoff_categories_complete",
            passed=not category_errors,
            details={"errors": category_errors},
        ),
        _check(
            name="ea_handoff_required_categories_present",
            passed=bool(required_category_ids) and not missing_required_category_ids,
            details={
                "configured_category_ids": sorted(category_ids),
                "missing_category_ids": missing_required_category_ids,
                "required_category_ids": required_category_ids,
            },
        ),
        _check(
            name="ea_handoff_category_rules_resolve",
            passed=not unknown_rule_category_ids,
            details={"unknown_category_ids": unknown_rule_category_ids},
        ),
        _check(
            name="ea_handoff_category_rules_complete",
            passed=not rule_errors,
            details={"errors": rule_errors},
        ),
        _check(
            name="ea_handoff_boundaries_complete",
            passed=not boundary_errors,
            details={"errors": boundary_errors},
        ),
        _check(
            name="ea_handoff_boundaries_explicit",
            passed=not missing_boundary_ids,
            details={
                "configured_boundary_ids": sorted(boundary_ids),
                "missing_boundary_ids": missing_boundary_ids,
            },
        ),
        _check(
            name="ea_handoff_slots_present",
            passed=bool(slots),
            details={"slot_count": len(slots)},
        ),
        _check(
            name="ea_handoff_slots_have_future_artifacts",
            passed=not slot_errors,
            details={"errors": slot_errors},
        ),
    ]
    return {
        "checks": checks,
        "failure_count": sum(1 for check in checks if not check["passed"]),
        "passed": all(check["passed"] for check in checks),
        "schema_version": "project-sow-ea-package-handoff-validation-v0",
    }


def _build_project_sow_ea_handoff(
    *,
    package: dict[str, Any],
    package_path: Path,
    rules_config: dict[str, Any],
    rules_config_path: Path,
    validation: dict[str, Any],
) -> dict[str, Any]:
    slots = _project_sow_ea_handoff_slots(package=package, rules_config=rules_config)
    category_counts = dict(
        sorted(Counter(str(slot.get("slot_category") or "") for slot in slots).items())
    )
    return {
        "assembly_categories": _project_sow_ea_handoff_category_summary(
            rules_config=rules_config,
            category_counts=category_counts,
        ),
        "assembly_slots": slots,
        "created_at": _now(),
        "derived_from": {
            "canonical_package_path": str(package_path),
            "canonical_package_schema_version": package.get("schema_version"),
            "project_sow_package_validation_passed": package.get("validation", {}).get(
                "passed"
            )
            is True,
            "source_fields": [
                "project_id",
                "project_name",
                "source_set_id",
                "scope_set_id",
                "resource_scope_records",
                "resource_analysis_matrix",
                "authority_requirement_matrix",
                "validation",
            ],
        },
        "downstream_consumption_contract": _project_sow_ea_handoff_consumption_contract(),
        "downstream_boundaries": _project_sow_ea_handoff_boundaries(rules_config),
        "input_hashes": {
            "project_sow_ea_handoff_rules_sha256": _sha256_file(rules_config_path),
            "project_sow_package_sha256": _sha256_file(package_path),
        },
        "input_paths": {
            "project_sow_ea_handoff_rules": str(rules_config_path),
            "project_sow_package": str(package_path),
        },
        "package_identity": {
            "package_schema_version": package.get("schema_version"),
            "project_id": package.get("project_id"),
            "project_name": package.get("project_name"),
            "scope_set_id": package.get("scope_set_id"),
            "source_set_id": package.get("source_set_id"),
        },
        "schema_version": PROJECT_SOW_EA_HANDOFF_SCHEMA_VERSION,
        "summary": {
            "boundary_count": len(_project_sow_ea_handoff_boundaries(rules_config)),
            "resource_scope_count": len(_project_sow_resource_scope_records(package)),
            "slot_category_counts": category_counts,
            "slot_count": len(slots),
        },
        "validation": validation,
    }


def _project_sow_ea_handoff_slots(
    *,
    package: dict[str, Any],
    rules_config: dict[str, Any],
) -> list[dict[str, Any]]:
    categories = {
        str(category.get("category_id") or ""): category
        for category in _project_sow_ea_handoff_categories(rules_config)
    }
    scopes = _project_sow_resource_scope_records(package)
    slots: dict[str, dict[str, Any]] = {}
    for category_id, category in sorted(categories.items()):
        if category.get("applies_to") != "all_selected_scopes":
            continue
        for scope in scopes:
            _add_project_sow_ea_handoff_slot(
                slots,
                category=category,
                scope=scope,
                matched_resource_area_ids=_strings(scope.get("covered_resource_area_ids")),
            )
    for rule in _project_sow_ea_handoff_category_rules(rules_config):
        category = categories.get(str(rule.get("category_id") or ""))
        if not category:
            continue
        for scope in scopes:
            matched_area_ids = _project_sow_ea_handoff_rule_matched_area_ids(
                rule=rule,
                scope=scope,
            )
            if not matched_area_ids:
                continue
            _add_project_sow_ea_handoff_slot(
                slots,
                category=category,
                scope=scope,
                matched_resource_area_ids=matched_area_ids,
            )
    return [slots[slot_id] for slot_id in sorted(slots)]


def _add_project_sow_ea_handoff_slot(
    slots: dict[str, dict[str, Any]],
    *,
    category: dict[str, Any],
    scope: dict[str, Any],
    matched_resource_area_ids: list[str],
) -> None:
    category_id = str(category.get("category_id") or "")
    scope_id = str(scope.get("resource_scope_id") or "")
    if not category_id or not scope_id:
        return
    slot_id = f"{category_id}:{scope_id}"
    expected_types = _strings(category.get("expected_artifact_types"))
    slots[slot_id] = {
        "category_description": category.get("description"),
        "category_title": category.get("title") or _title_from_id(category_id),
        "covered_resource_area_ids": _strings(scope.get("covered_resource_area_ids")),
        "current_status": "expected_future_artifact",
        "discipline": scope.get("discipline"),
        "expected_future_artifacts": [
            {
                "artifact_type": artifact_type,
                "required_now": False,
                "status": "not_started",
            }
            for artifact_type in expected_types
        ],
        "expected_future_artifact_types": expected_types,
        "future_artifact_required_now": False,
        "matched_resource_area_ids": sorted(set(matched_resource_area_ids)),
        "optional_sow_deliverables": _strings(scope.get("optional_deliverables")),
        "required_sow_deliverables": _strings(scope.get("required_deliverables")),
        "resource_name": scope.get("resource_name"),
        "resource_scope_id": scope_id,
        "selected_authority_family_ids": _strings(scope.get("authority_family_ids")),
        "slot_category": category_id,
        "slot_id": slot_id,
        "slot_title": f"{category.get('title') or _title_from_id(category_id)}: "
        f"{scope.get('resource_name') or scope_id}",
        "source_package_fields": [
            "resource_scope_records",
            "resource_analysis_matrix",
            "authority_requirement_matrix",
        ],
    }


def _project_sow_ea_handoff_rule_matched_area_ids(
    *,
    rule: dict[str, Any],
    scope: dict[str, Any],
) -> list[str]:
    scope_id = str(scope.get("resource_scope_id") or "")
    rule_scope_ids = set(_strings(rule.get("resource_scope_ids")))
    scope_area_ids = set(_strings(scope.get("covered_resource_area_ids")))
    rule_area_ids = set(_strings(rule.get("resource_area_ids")))
    if scope_id in rule_scope_ids:
        return sorted(scope_area_ids.intersection(rule_area_ids) or scope_area_ids)
    matched_area_ids = sorted(scope_area_ids.intersection(rule_area_ids))
    return matched_area_ids


def _project_sow_ea_handoff_category_summary(
    *,
    rules_config: dict[str, Any],
    category_counts: dict[str, int],
) -> list[dict[str, Any]]:
    return [
        {
            "applies_to": category.get("applies_to"),
            "category_id": category.get("category_id"),
            "description": category.get("description"),
            "expected_artifact_types": _strings(category.get("expected_artifact_types")),
            "slot_count": category_counts.get(str(category.get("category_id") or ""), 0),
            "title": category.get("title"),
        }
        for category in _project_sow_ea_handoff_categories(rules_config)
    ]


def _project_sow_ea_handoff_consumption_contract() -> dict[str, Any]:
    return {
        "allowed_downstream_inputs": [
            {
                "field": "package_identity",
                "use": "Identify the project SOW package that seeded assembly planning.",
            },
            {
                "field": "input_hashes",
                "use": "Detect stale handoffs when the source package or handoff rules change.",
            },
            {
                "field": "assembly_categories",
                "use": "Understand configured future EA package work categories and slot counts.",
            },
            {
                "field": "assembly_slots",
                "use": "Seed future EA package assembly checklists for selected SOW scopes.",
            },
            {
                "field": "downstream_boundaries",
                "use": "Preserve non-review, non-compliance, and non-legal-sufficiency limits.",
            },
        ],
        "must_not_infer": [
            "Expected future artifacts already exist.",
            "Expected future artifacts are complete, sufficient, or reviewer-ready.",
            "Authority applicability or non-applicability has been decided.",
            "A generated rule pack may be created from this handoff alone.",
            "Compliance findings, legal advice, legal sufficiency conclusions, or final agency decisions have been made.",
        ],
        "required_preconditions_for_review_commands": [
            "Verify the source package hash before consuming the handoff.",
            "Require actual source, consultation, specialist-report, public-involvement, Forest Plan, and decision-record artifacts before downstream review commands assess them.",
            "Regenerate the handoff after the project SOW package or handoff rules change.",
        ],
        "schema_version": "project-sow-ea-package-handoff-consumption-contract-v0",
    }


def _project_sow_ea_handoff_categories(
    rules_config: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        category
        for category in _list(rules_config.get("assembly_categories"))
        if isinstance(category, dict)
    ]


def _project_sow_ea_handoff_category_rules(
    rules_config: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        rule
        for rule in _list(rules_config.get("category_rules"))
        if isinstance(rule, dict)
    ]


def _project_sow_ea_handoff_boundaries(
    rules_config: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "boundary_id": boundary.get("boundary_id"),
            "statement": boundary.get("statement"),
        }
        for boundary in _list(rules_config.get("downstream_boundaries"))
        if isinstance(boundary, dict)
    ]


def _project_sow_ea_handoff_category_errors(
    categories: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    category_ids = [str(category.get("category_id") or "") for category in categories]
    for duplicate_id in _duplicates(category_ids):
        errors.append(f"assembly_categories: duplicate category_id {duplicate_id}")
    for index, category in enumerate(categories):
        path = f"assembly_categories[{index}]"
        for field in ("category_id", "title", "description"):
            if _is_empty(category.get(field)):
                errors.append(f"{path}.{field}: required")
        applies_to = str(category.get("applies_to") or "")
        if applies_to not in PROJECT_SOW_EA_HANDOFF_ALLOWED_CATEGORY_APPLIES_TO:
            errors.append(f"{path}.applies_to: unsupported")
        if not _strings(category.get("expected_artifact_types")):
            errors.append(f"{path}.expected_artifact_types: must contain at least one item")
    return errors


def _project_sow_ea_handoff_rule_errors(
    *,
    categories: list[dict[str, Any]],
    rules: list[dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    rule_category_ids = {str(rule.get("category_id") or "") for rule in rules}
    rule_match_category_ids = {
        str(category.get("category_id") or "")
        for category in categories
        if category.get("applies_to") == "rule_matches"
    }
    for category_id in sorted(rule_match_category_ids - rule_category_ids):
        if category_id:
            errors.append(f"category_rules: missing rule for {category_id}")
    for index, rule in enumerate(rules):
        path = f"category_rules[{index}]"
        if _is_empty(rule.get("category_id")):
            errors.append(f"{path}.category_id: required")
        if not _strings(rule.get("resource_scope_ids")):
            errors.append(f"{path}.resource_scope_ids: must contain at least one item")
        if not _strings(rule.get("resource_area_ids")):
            errors.append(f"{path}.resource_area_ids: must contain at least one item")
    return errors


def _project_sow_ea_handoff_boundary_errors(
    rules_config: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    boundaries = _project_sow_ea_handoff_boundaries(rules_config)
    boundary_ids = [str(boundary.get("boundary_id") or "") for boundary in boundaries]
    for duplicate_id in _duplicates(boundary_ids):
        errors.append(f"downstream_boundaries: duplicate boundary_id {duplicate_id}")
    for index, boundary in enumerate(boundaries):
        path = f"downstream_boundaries[{index}]"
        for field in ("boundary_id", "statement"):
            if _is_empty(boundary.get(field)):
                errors.append(f"{path}.{field}: required")
    return errors


def _project_sow_ea_handoff_slot_errors(slots: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    slot_ids = [str(slot.get("slot_id") or "") for slot in slots]
    for duplicate_id in _duplicates(slot_ids):
        errors.append(f"assembly_slots: duplicate slot_id {duplicate_id}")
    for slot in slots:
        slot_id = str(slot.get("slot_id") or "unknown")
        if slot.get("future_artifact_required_now") is not False:
            errors.append(f"{slot_id}.future_artifact_required_now: must be false")
        artifacts = [
            artifact
            for artifact in _list(slot.get("expected_future_artifacts"))
            if isinstance(artifact, dict)
        ]
        if not artifacts:
            errors.append(f"{slot_id}.expected_future_artifacts: must contain at least one item")
            continue
        for artifact_index, artifact in enumerate(artifacts):
            artifact_path = f"{slot_id}.expected_future_artifacts[{artifact_index}]"
            if _is_empty(artifact.get("artifact_type")):
                errors.append(f"{artifact_path}.artifact_type: required")
            if artifact.get("required_now") is not False:
                errors.append(f"{artifact_path}.required_now: must be false")
    return errors


def _project_sow_ea_handoff_summary(
    *,
    handoff: dict[str, Any],
    markdown_path: Path,
    output_path: Path,
    package: dict[str, Any],
    package_path: Path,
    rules_config_path: Path,
    validation: dict[str, Any],
) -> dict[str, Any]:
    slots = [
        slot
        for slot in _list(handoff.get("assembly_slots"))
        if isinstance(slot, dict)
    ]
    return {
        "failed_validation_checks": [
            check for check in validation["checks"] if not check["passed"]
        ],
        "handoff_rules_config_path": str(rules_config_path),
        "output_paths": {
            "handoff": str(output_path),
            "markdown": str(markdown_path),
        },
        "output_written": False,
        "package_path": str(package_path),
        "passed": validation["passed"],
        "project_id": package.get("project_id"),
        "schema_version": PROJECT_SOW_EA_HANDOFF_SUMMARY_SCHEMA_VERSION,
        "slot_category_counts": dict(
            sorted(Counter(str(slot.get("slot_category") or "") for slot in slots).items())
        ),
        "slot_count": len(slots),
        "source_set_id": package.get("source_set_id"),
        "validation_check_count": len(validation["checks"]),
        "validation_checks": validation["checks"],
        "validation_failure_count": validation["failure_count"],
    }


def _render_project_sow_ea_handoff_markdown(handoff: dict[str, Any]) -> str:
    identity = handoff.get("package_identity") or {}
    summary = handoff.get("summary") or {}
    slots = [
        slot
        for slot in _list(handoff.get("assembly_slots"))
        if isinstance(slot, dict)
    ]
    lines = [
        f"# {identity.get('project_name')} EA Package Assembly Handoff",
        "",
        "This handoff converts the accepted project SOW package into future EA package assembly checklist slots. It does not require those artifacts to exist yet.",
        "",
        "## Package Identity",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Project ID | `{identity.get('project_id')}` |",
        f"| Source set | `{identity.get('source_set_id')}` |",
        f"| Scope set | `{identity.get('scope_set_id')}` |",
        f"| Package schema | `{identity.get('package_schema_version')}` |",
        f"| Assembly slots | `{summary.get('slot_count')}` |",
        "",
        "## Downstream Boundaries",
        "",
    ]
    lines.extend(
        f"- `{boundary.get('boundary_id')}`: {boundary.get('statement')}"
        for boundary in _list(handoff.get("downstream_boundaries"))
        if isinstance(boundary, dict)
    )
    contract = (
        handoff.get("downstream_consumption_contract")
        if isinstance(handoff.get("downstream_consumption_contract"), dict)
        else {}
    )
    lines.extend(["", "## Downstream Consumption Contract", ""])
    lines.append("May consume:")
    lines.extend(
        f"- `{item.get('field')}`: {item.get('use')}"
        for item in _list(contract.get("allowed_downstream_inputs"))
        if isinstance(item, dict)
    )
    lines.append("")
    lines.append("Must not infer:")
    lines.extend(f"- {item}" for item in _strings(contract.get("must_not_infer")))
    lines.append("")
    lines.append("Required preconditions:")
    lines.extend(
        f"- {item}"
        for item in _strings(contract.get("required_preconditions_for_review_commands"))
    )
    lines.extend(
        [
            "",
            "## Slot Summary",
            "",
            "| Category | Slots |",
            "| --- | ---: |",
        ]
    )
    for category, count in (summary.get("slot_category_counts") or {}).items():
        lines.append(f"| `{category}` | {count} |")
    lines.extend(
        [
            "",
            "## Assembly Checklist",
            "",
            "| Slot | Category | SOW scope | Expected future artifact types | Required now |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for slot in slots:
        expected = ", ".join(slot.get("expected_future_artifact_types") or [])
        required_now = "yes" if slot.get("future_artifact_required_now") else "no"
        lines.append(
            f"| `{slot.get('slot_id')}` | `{slot.get('slot_category')}` | "
            f"`{slot.get('resource_scope_id')}` | {expected} | {required_now} |"
        )
    lines.extend(["", "## Validation"])
    for check in _list((handoff.get("validation") or {}).get("checks")):
        if isinstance(check, dict):
            status = "passed" if check.get("passed") else "failed"
            lines.append(f"- `{check.get('name')}`: `{status}`")
    return "\n".join(lines) + "\n"
