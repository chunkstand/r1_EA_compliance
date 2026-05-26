from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .review_packet_index_artifacts import _load_artifacts
from .review_packet_index_artifacts import _output_paths
from .review_packet_index_common import _dict
from .review_packet_index_common import _dict_list
from .review_packet_index_common import _md_cell
from .review_packet_index_common import _Artifact
from .review_packet_index_common import LAND_EXCHANGE_RULE_SOURCES
from .review_packet_index_common import _OutputPaths
from .review_packet_index_common import _sha256_file
from .review_packet_index_common import _utc_now
from .review_packet_index_common import _write_json
from .review_packet_index_common import _write_simple_pdf
from .review_packet_index_common import ReviewPacketIndexResult
from .review_packet_index_common import VALIDATION_SCHEMA_VERSION
from .review_packet_index_inventory import _build_packet_index
from .review_packet_index_inventory import _build_render_manifest
from .review_packet_index_inventory import _build_row_inventory
from .review_packet_index_inventory import _land_exchange_rows_present


_DOWNSTREAM_AUTHORITY_ROW_MIRROR_CHECKS = {
    "decision_support_authority_rows_match_applicability",
    "final_qa_authority_rows_match_applicability",
}


def run_review_packet_index(
    *,
    output_dir: Path = Path("source_library"),
    review_id: str,
    results_dir: Path | None = None,
) -> ReviewPacketIndexResult:
    output_dir = Path(output_dir)
    review_dir = output_dir / "reviews" / review_id
    index_dir = Path(results_dir) if results_dir is not None else review_dir / "review_packet_index"
    paths = _output_paths(index_dir)
    artifacts = _load_artifacts(review_dir=review_dir)

    compliance_matrix = _dict(artifacts["compliance_matrix"].payload)
    compliance_markdown = artifacts["compliance_matrix_markdown"].text
    render_manifest = _build_render_manifest(
        matrix=compliance_matrix,
        markdown=compliance_markdown,
        pdf_path=artifacts["compliance_matrix_pdf"].path,
    )
    inventory = _build_row_inventory(
        review_id=review_id,
        review_dir=review_dir,
        artifacts=artifacts,
        render_manifest=render_manifest,
        render_manifest_path=paths.render_manifest_path,
    )
    packet_index = _build_packet_index(
        review_id=review_id,
        review_dir=review_dir,
        artifacts=artifacts,
        inventory=inventory,
        render_manifest=render_manifest,
        paths=paths,
    )

    index_dir.mkdir(parents=True, exist_ok=True)
    _write_json(paths.row_inventory_path, inventory)
    paths.row_inventory_markdown_path.write_text(
        _inventory_markdown(inventory),
        encoding="utf-8",
    )
    _write_json(paths.render_manifest_path, render_manifest)
    _write_json(paths.packet_index_path, packet_index)
    paths.packet_index_markdown_path.write_text(
        _packet_index_markdown(packet_index),
        encoding="utf-8",
    )
    _write_simple_pdf(paths.packet_index_pdf_path, _packet_index_pdf_lines(packet_index))
    validation = _validate_packet(
        review_id=review_id,
        artifacts=artifacts,
        inventory=inventory,
        render_manifest=render_manifest,
        packet_index=packet_index,
        paths=paths,
    )
    validation["output_files"] = {
        "row_inventory_json": str(paths.row_inventory_path),
        "row_inventory_markdown": str(paths.row_inventory_markdown_path),
        "render_manifest": str(paths.render_manifest_path),
        "packet_index_json": str(paths.packet_index_path),
        "packet_index_markdown": str(paths.packet_index_markdown_path),
        "packet_index_pdf": str(paths.packet_index_pdf_path),
        "validation": str(paths.validation_path),
    }
    validation["output_hashes"] = {
        key + "_sha256": _sha256_file(Path(path))
        for key, path in validation["output_files"].items()
        if key != "validation" and Path(path).exists()
    }
    _write_json(paths.validation_path, validation)
    summary = dict(validation["summary"])
    summary["output_dir"] = str(index_dir)
    summary["validation_path"] = str(paths.validation_path)
    return ReviewPacketIndexResult(
        output_dir=index_dir,
        row_inventory_path=paths.row_inventory_path,
        row_inventory_markdown_path=paths.row_inventory_markdown_path,
        render_manifest_path=paths.render_manifest_path,
        packet_index_path=paths.packet_index_path,
        packet_index_markdown_path=paths.packet_index_markdown_path,
        packet_index_pdf_path=paths.packet_index_pdf_path,
        validation_path=paths.validation_path,
        summary=summary,
    )


def _validate_packet(
    *,
    review_id: str,
    artifacts: dict[str, _Artifact],
    inventory: dict[str, Any],
    render_manifest: dict[str, Any],
    packet_index: dict[str, Any],
    paths: _OutputPaths,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for artifact in artifacts.values():
        _add_check(
            checks,
            name=f"{artifact.key}_exists_and_parses",
            passed=artifact.exists and artifact.parse_ok,
            category=(
                "missing_required_artifact"
                if not artifact.exists
                else "unparseable_required_artifact"
            ),
            details={"path": str(artifact.path), "error": artifact.error},
        )
    authority_sets = {
        key: set(values) for key, values in _dict(inventory.get("authority_row_sets")).items()
    }
    expected_authority_set = authority_sets.get("applicable_authorities", set())
    for key, values in sorted(authority_sets.items()):
        check_name = f"{key}_authority_rows_match_applicability"
        missing = sorted(expected_authority_set - values)
        extra = sorted(values - expected_authority_set)
        self_reference_allowed = (
            check_name in _DOWNSTREAM_AUTHORITY_ROW_MIRROR_CHECKS and not extra
        )
        _add_check(
            checks,
            name=check_name,
            passed=values == expected_authority_set or self_reference_allowed,
            category="missing_applicable_authority_row",
            details={
                "expected_count": len(expected_authority_set),
                "actual_count": len(values),
                "missing": missing,
                "extra": extra,
                "self_reference_allowed": self_reference_allowed,
            },
        )
    render_authority_set = set(
        _dict(inventory.get("render_manifest_row_sets")).get("applicable_authority", [])
    )
    _add_check(
        checks,
        name="render_manifest_authority_rows_match_matrix",
        passed=render_authority_set == expected_authority_set,
        category="missing_matrix_render_row",
        details={
            "missing": sorted(expected_authority_set - render_authority_set),
            "extra": sorted(render_authority_set - expected_authority_set),
        },
    )
    forest_sets = _dict(inventory.get("forest_plan_row_sets"))
    matrix_forest = set(forest_sets.get("matrix_component_ids") or [])
    finding_forest = set(forest_sets.get("component_finding_ids") or [])
    render_forest = set(forest_sets.get("render_manifest_component_ids") or [])
    _add_check(
        checks,
        name="forest_plan_rows_match_component_findings",
        passed=matrix_forest == finding_forest,
        category="missing_forest_plan_row",
        details={
            "missing": sorted(finding_forest - matrix_forest),
            "extra": sorted(matrix_forest - finding_forest),
        },
    )
    _add_check(
        checks,
        name="render_manifest_forest_plan_rows_match_matrix",
        passed=render_forest == matrix_forest,
        category="missing_matrix_render_row",
        details={
            "missing": sorted(matrix_forest - render_forest),
            "extra": sorted(render_forest - matrix_forest),
        },
    )
    _add_check(
        checks,
        name="non_applicable_boundary_present",
        passed=inventory["summary"]["non_applicable_authority_count"] > 0,
        category="missing_non_applicable_boundary",
        details={"count": inventory["summary"]["non_applicable_authority_count"]},
    )
    _add_check(
        checks,
        name="applicable_forest_plan_standards_present",
        passed=inventory["summary"]["applicable_standard_count"] > 0,
        category="missing_forest_plan_row",
        details={"count": inventory["summary"]["applicable_standard_count"]},
    )
    _add_check(
        checks,
        name="land_exchange_rows_present",
        passed=_land_exchange_rows_present(inventory),
        category="missing_applicable_authority_row",
        details={"required_rule_sources": LAND_EXCHANGE_RULE_SOURCES},
    )
    expected_land_exchange = {
        rule_id: source_record_id
        for rule_id, source_record_id in LAND_EXCHANGE_RULE_SOURCES.items()
        if rule_id in expected_authority_set
    }
    packet_land_exchange = {
        str(row.get("rule_id")): str(row.get("authority_source_record_id"))
        for row in _dict_list(packet_index.get("land_exchange_rows"))
    }
    _add_check(
        checks,
        name="land_exchange_rows_first_class_in_packet_index",
        passed=packet_land_exchange == expected_land_exchange,
        category="missing_applicable_authority_row",
        details={
            "expected_rule_sources": expected_land_exchange,
            "packet_rule_sources": packet_land_exchange,
        },
    )
    _add_check(
        checks,
        name="render_manifest_passed",
        passed=_dict(render_manifest.get("summary")).get("passed") is True,
        category="missing_matrix_render_row",
        details=render_manifest.get("summary"),
    )
    _add_check(
        checks,
        name="packet_index_rows_match_inventory",
        passed={
            str(row.get("rule_id"))
            for row in _dict_list(packet_index.get("applicable_authority_rows"))
        }
        == expected_authority_set,
        category="missing_packet_index_row",
        details={"expected_count": len(expected_authority_set)},
    )
    blocked_paths = _blocked_root_draft_paths(packet_index)
    _add_check(
        checks,
        name="non_canonical_root_drafts_not_referenced",
        passed=not blocked_paths,
        category="non_canonical_draft_dependency",
        details={"blocked_paths": blocked_paths},
    )
    pdf_header_valid = (
        paths.packet_index_pdf_path.exists()
        and paths.packet_index_pdf_path.stat().st_size > 0
        and paths.packet_index_pdf_path.read_bytes().startswith(b"%PDF-")
    )
    _add_check(
        checks,
        name="packet_index_pdf_header_valid_after_write",
        passed=pdf_header_valid,
        category="missing_required_artifact",
        details={"path": str(paths.packet_index_pdf_path)},
    )
    passed = all(check["passed"] for check in checks)
    failure_categories = Counter(
        check["failure_category"] for check in checks if not check["passed"]
    )
    summary = {
        "passed": passed,
        "reviewer_ready": passed,
        "review_id": review_id,
        "source_set_id": inventory.get("source_set_id"),
        "applicable_authority_count": inventory["summary"]["applicable_authority_count"],
        "land_exchange_row_count": inventory["summary"]["land_exchange_row_count"],
        "non_applicable_authority_count": inventory["summary"]["non_applicable_authority_count"],
        "forest_plan_component_row_count": inventory["summary"][
            "forest_plan_component_row_count"
        ],
        "applicable_standard_count": inventory["summary"]["applicable_standard_count"],
        "render_manifest_row_count": render_manifest["summary"]["row_count"],
        "render_manifest_authority_row_count": render_manifest["summary"][
            "authority_row_count"
        ],
        "render_manifest_forest_plan_row_count": render_manifest["summary"][
            "forest_plan_row_count"
        ],
        "row_set_sha256": inventory["summary"]["row_set_sha256"],
        "failure_category_counts": dict(sorted(failure_categories.items())),
        "failed_check_count": sum(1 for check in checks if not check["passed"]),
        "check_count": len(checks),
    }
    return {
        "schema_version": VALIDATION_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": review_id,
        "source_set_id": inventory.get("source_set_id"),
        "generator_version": packet_index["generator_version"],
        "passed": passed,
        "reviewer_ready": passed,
        "summary": summary,
        "checks": checks,
    }


def _inventory_markdown(inventory: dict[str, Any]) -> str:
    summary = inventory["summary"]
    lines = [
        "# Review Packet Row Inventory",
        "",
        f"- Review ID: `{inventory['review_id']}`",
        f"- Source set: `{inventory['source_set_id']}`",
        f"- Applicable authority rows: `{summary['applicable_authority_count']}`",
        f"- Land-exchange rows: `{summary.get('land_exchange_row_count', 0)}`",
        f"- Non-applicable authority boundary rows: `{summary['non_applicable_authority_count']}`",
        f"- Forest Plan component rows: `{summary['forest_plan_component_row_count']}`",
        f"- Applicable Forest Plan standards: `{summary['applicable_standard_count']}`",
        f"- Row-set hash: `{summary['row_set_sha256']}`",
        "",
        "## Applicable Authorities",
        "",
        "| Rule ID | Source record | Status | Matrix marker |",
        "| --- | --- | --- | --- |",
    ]
    for row in inventory["applicable_authority_rows"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(row.get("rule_id")),
                    _md_cell(row.get("authority_source_record_id")),
                    _md_cell(row.get("compliance_status")),
                    _md_cell(row.get("render_markdown_marker")),
                ]
            )
            + " |"
        )
    if inventory["land_exchange_rows"]:
        lines.extend(
            [
                "",
                "## Land-Exchange Rows",
                "",
                "| Rule ID | Source record | Status | Matrix marker |",
                "| --- | --- | --- | --- |",
            ]
        )
        for row in inventory["land_exchange_rows"]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md_cell(row.get("rule_id")),
                        _md_cell(row.get("authority_source_record_id")),
                        _md_cell(row.get("compliance_status")),
                        _md_cell(row.get("render_markdown_marker")),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## Forest Plan Rows",
            "",
            "| Component | Type | Compliance status | Matrix marker |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in inventory["forest_plan_component_rows"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(row.get("component_key") or row.get("component_id")),
                    _md_cell(row.get("component_type")),
                    _md_cell(row.get("compliance_status")),
                    _md_cell(row.get("render_markdown_marker")),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def _packet_index_markdown(packet_index: dict[str, Any]) -> str:
    summary = packet_index["row_inventory_summary"]
    lines = [
        "# Review Packet Index",
        "",
        (
            "This index is a deterministic ledger over canonical review artifacts. It is not "
            "legal advice, legal sufficiency certification, or a final agency decision."
        ),
        "",
        f"- Review ID: `{packet_index['review_id']}`",
        f"- Source set: `{packet_index['source_set_id']}`",
        f"- Applicable authority rows: `{summary['applicable_authority_count']}`",
        f"- Land-exchange rows: `{summary.get('land_exchange_row_count', 0)}`",
        f"- Non-applicable authorities: `{summary['non_applicable_authority_count']}`",
        f"- Forest Plan component rows: `{summary['forest_plan_component_row_count']}`",
        f"- Applicable Forest Plan standards: `{summary['applicable_standard_count']}`",
        "",
        "## Applicable Authority Rows",
        "",
        "| Rule ID | Source record | Status | Matrix marker |",
        "| --- | --- | --- | --- |",
    ]
    for row in packet_index["applicable_authority_rows"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(row.get("rule_id")),
                    _md_cell(row.get("authority_source_record_id")),
                    _md_cell(row.get("compliance_status")),
                    _md_cell(row.get("render_markdown_marker")),
                ]
            )
            + " |"
        )
    if packet_index["land_exchange_rows"]:
        lines.extend(
            [
                "",
                "## Land-Exchange Rows",
                "",
                "| Rule ID | Source record | Status | Matrix marker |",
                "| --- | --- | --- | --- |",
            ]
        )
        for row in packet_index["land_exchange_rows"]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md_cell(row.get("rule_id")),
                        _md_cell(row.get("authority_source_record_id")),
                        _md_cell(row.get("compliance_status")),
                        _md_cell(row.get("render_markdown_marker")),
                    ]
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "## Non-Applicable Authority Boundary",
            "",
            "- Boundary artifact: "
            f"`{packet_index['non_applicable_authority_boundary']['appendix_path']}`",
            "- Boundary rows are linked in JSON and are not promoted into compliance findings.",
            "",
            "## Forest Plan Rows",
            "",
            "| Component | Type | Compliance status | Matrix marker |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in packet_index["forest_plan_component_rows"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _md_cell(row.get("component_key") or row.get("component_id")),
                    _md_cell(row.get("component_type")),
                    _md_cell(row.get("compliance_status")),
                    _md_cell(row.get("render_markdown_marker")),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Implementation Confirmations",
            "",
        ]
    )
    for row in packet_index["implementation_confirmation_checklist"]:
        lines.append(f"- `{row.get('confirmation_id')}`: {row.get('label')}")
    lines.extend(
        [
            "",
            "## Residual Risks",
            "",
        ]
    )
    for row in packet_index["residual_risk_register"]:
        lines.append(f"- `{row.get('risk_id')}`: {row.get('category')}")
    return "\n".join(lines) + "\n"


def _packet_index_pdf_lines(packet_index: dict[str, Any]) -> list[str]:
    summary = packet_index["row_inventory_summary"]
    return [
        "Review Packet Index",
        f"Review ID: {packet_index['review_id']}",
        f"Source set: {packet_index['source_set_id']}",
        f"Applicable authority rows: {summary['applicable_authority_count']}",
        f"Land-exchange rows: {summary.get('land_exchange_row_count', 0)}",
        f"Non-applicable authority boundary rows: {summary['non_applicable_authority_count']}",
        f"Forest Plan component rows: {summary['forest_plan_component_row_count']}",
        f"Applicable Forest Plan standards: {summary['applicable_standard_count']}",
        "Root-level East_Crazies_* draft exports are not canonical review artifacts.",
    ]


def _blocked_root_draft_paths(value: Any) -> list[str]:
    blocked: list[str] = []
    if isinstance(value, dict):
        for item in value.values():
            blocked.extend(_blocked_root_draft_paths(item))
    elif isinstance(value, list):
        for item in value:
            blocked.extend(_blocked_root_draft_paths(item))
    elif isinstance(value, str):
        path = value.strip()
        if path.startswith("East_Crazies_"):
            blocked.append(path)
    return sorted(set(blocked))


def _add_check(
    checks: list[dict[str, Any]],
    *,
    name: str,
    passed: bool,
    category: str,
    details: dict[str, Any],
) -> None:
    checks.append(
        {
            "name": name,
            "passed": bool(passed),
            "failure_category": None if passed else category,
            "details": details,
        }
    )
