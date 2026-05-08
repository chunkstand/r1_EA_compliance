from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any


ROW_INVENTORY_SCHEMA_VERSION = "review-packet-row-inventory-v1"
RENDER_MANIFEST_SCHEMA_VERSION = "compliance-matrix-render-manifest-v1"
PACKET_INDEX_SCHEMA_VERSION = "review-packet-index-v1"
VALIDATION_SCHEMA_VERSION = "review-packet-index-validation-v1"
GENERATOR_VERSION = "review-packet-index-v1"

ROW_INVENTORY_FILENAME = "review_packet_row_inventory.json"
ROW_INVENTORY_MARKDOWN_FILENAME = "review_packet_row_inventory.md"
RENDER_MANIFEST_FILENAME = "compliance_matrix_render_manifest.json"
PACKET_INDEX_FILENAME = "review_packet_index.json"
PACKET_INDEX_MARKDOWN_FILENAME = "review_packet_index.md"
PACKET_INDEX_PDF_FILENAME = "review_packet_index.pdf"
VALIDATION_FILENAME = "review_packet_index_validation.json"

LAND_EXCHANGE_RULE_SOURCES = {
    "flpma_section_206_land_exchange": "R1EA-146",
    "land_exchange_statutory_authorities": "R1EA-137",
    "land_exchange_regulatory_requirements": "R1EA-124",
    "land_exchange_fs_policy_and_project_references": "R1EA-150",
}


@dataclass(frozen=True)
class ReviewPacketIndexResult:
    output_dir: Path
    row_inventory_path: Path
    row_inventory_markdown_path: Path
    render_manifest_path: Path
    packet_index_path: Path
    packet_index_markdown_path: Path
    packet_index_pdf_path: Path
    validation_path: Path
    summary: dict[str, Any]


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


@dataclass(frozen=True)
class _OutputPaths:
    row_inventory_path: Path
    row_inventory_markdown_path: Path
    render_manifest_path: Path
    packet_index_path: Path
    packet_index_markdown_path: Path
    packet_index_pdf_path: Path
    validation_path: Path


@dataclass(frozen=True)
class _Artifact:
    key: str
    path: Path
    required: bool
    artifact_type: str
    payload: Any
    text: str
    exists: bool
    parse_ok: bool
    sha256: str | None
    error: str | None = None


def _output_paths(index_dir: Path) -> _OutputPaths:
    return _OutputPaths(
        row_inventory_path=index_dir / ROW_INVENTORY_FILENAME,
        row_inventory_markdown_path=index_dir / ROW_INVENTORY_MARKDOWN_FILENAME,
        render_manifest_path=index_dir / RENDER_MANIFEST_FILENAME,
        packet_index_path=index_dir / PACKET_INDEX_FILENAME,
        packet_index_markdown_path=index_dir / PACKET_INDEX_MARKDOWN_FILENAME,
        packet_index_pdf_path=index_dir / PACKET_INDEX_PDF_FILENAME,
        validation_path=index_dir / VALIDATION_FILENAME,
    )


def _load_artifacts(*, review_dir: Path) -> dict[str, _Artifact]:
    specs = {
        "compliance_matrix": (review_dir / "compliance_matrix.json", "json", True),
        "compliance_matrix_markdown": (review_dir / "compliance_matrix.md", "text", True),
        "compliance_matrix_pdf": (review_dir / "compliance_matrix.pdf", "pdf", True),
        "compliance_review": (review_dir / "compliance_review.json", "json", True),
        "applicable_authorities": (
            review_dir / "applicability" / "applicable_authorities.json",
            "json",
            True,
        ),
        "generated_rule_pack": (
            review_dir / "applicability" / "generated_rule_pack.json",
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
        "non_applicable_authority_appendix": (
            review_dir / "non_applicable_authority_appendix.json",
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
        "decision_support_report": (
            review_dir / "decision_support" / "ea_consistency_decision_support.json",
            "json",
            True,
        ),
        "final_qa_report": (
            review_dir / "final_qa" / "east_crazies_final_qa_certification.json",
            "json",
            True,
        ),
    }
    return {
        key: _load_artifact(key=key, path=path, artifact_type=artifact_type, required=required)
        for key, (path, artifact_type, required) in specs.items()
    }


def _load_artifact(
    *,
    key: str,
    path: Path,
    artifact_type: str,
    required: bool,
) -> _Artifact:
    if not path.exists():
        return _Artifact(
            key=key,
            path=path,
            required=required,
            artifact_type=artifact_type,
            payload=None,
            text="",
            exists=False,
            parse_ok=False,
            sha256=None,
            error=f"Missing artifact: {path}",
        )
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    try:
        text = raw.decode("utf-8") if artifact_type != "pdf" else ""
        if artifact_type == "json":
            payload = json.loads(text)
            parse_ok = isinstance(payload, dict)
        elif artifact_type == "text":
            payload = text
            parse_ok = True
        elif artifact_type == "pdf":
            payload = {"pdf_header_valid": raw.startswith(b"%PDF-")}
            parse_ok = bool(payload["pdf_header_valid"])
        else:
            payload = text
            parse_ok = True
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return _Artifact(
            key=key,
            path=path,
            required=required,
            artifact_type=artifact_type,
            payload=None,
            text="",
            exists=True,
            parse_ok=False,
            sha256=digest,
            error=str(exc),
        )
    return _Artifact(
        key=key,
        path=path,
        required=required,
        artifact_type=artifact_type,
        payload=payload,
        text=text,
        exists=True,
        parse_ok=parse_ok,
        sha256=digest,
        error=None if parse_ok else f"Artifact did not parse as {artifact_type}: {path}",
    )


def _build_render_manifest(*, matrix: dict, markdown: str, pdf_path: Path) -> dict[str, Any]:
    rows = []
    for index, row in enumerate(_dict_list(matrix.get("rows")), start=1):
        rule_id = str(row.get("rule_id") or "")
        marker = _matrix_row_marker("authority", rule_id)
        rows.append(
            _render_manifest_row(
                row_class="applicable_authority",
                row=row,
                row_order=index,
                section="NEPA / Authority Compliance",
                table_id="nepa_authority_compliance",
                json_selector=f"rows[rule_id={rule_id}]",
                markdown_marker=marker,
                row_identity={"rule_id": rule_id},
            )
        )
    forest_rows = _dict_list((_dict(matrix.get("forest_plan_compliance")).get("rows")))
    for index, row in enumerate(forest_rows, start=1):
        component_id = str(row.get("component_id") or "")
        marker = _matrix_row_marker("forest-plan", component_id)
        rows.append(
            _render_manifest_row(
                row_class="forest_plan_component",
                row=row,
                row_order=index,
                section="Forest Plan Compliance",
                table_id="forest_plan_compliance",
                json_selector=f"forest_plan_compliance.rows[component_id={component_id}]",
                markdown_marker=marker,
                row_identity={
                    "component_id": component_id,
                    "component_key": row.get("component_key"),
                    "component_type": row.get("component_type"),
                },
            )
        )
    missing_markers = [row["markdown_marker"] for row in rows if row["markdown_marker"] not in markdown]
    pdf_header_valid = (
        pdf_path.exists()
        and pdf_path.stat().st_size > 0
        and pdf_path.read_bytes().startswith(b"%PDF-")
    )
    authority_row_count = sum(1 for row in rows if row["row_class"] == "applicable_authority")
    forest_plan_row_count = sum(1 for row in rows if row["row_class"] == "forest_plan_component")
    return {
        "schema_version": RENDER_MANIFEST_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": matrix.get("review_id"),
        "source_set_id": matrix.get("source_set_id"),
        "matrix_schema_version": matrix.get("schema_version"),
        "summary": {
            "passed": not missing_markers and pdf_header_valid,
            "row_count": len(rows),
            "authority_row_count": authority_row_count,
            "forest_plan_row_count": forest_plan_row_count,
            "markdown_marker_count": len(rows) - len(missing_markers),
            "missing_markdown_markers": missing_markers,
            "pdf_path": str(pdf_path),
            "pdf_header_valid": pdf_header_valid,
            "row_set_sha256": _row_set_sha256(rows),
        },
        "rows": rows,
    }


def _build_row_inventory(
    *,
    review_id: str,
    review_dir: Path,
    artifacts: dict[str, _Artifact],
    render_manifest: dict[str, Any],
    render_manifest_path: Path,
) -> dict[str, Any]:
    matrix = _dict(artifacts["compliance_matrix"].payload)
    applicable_authorities = _dict_list(
        _dict(artifacts["applicable_authorities"].payload).get("authorities")
    )
    generated_rules = _dict_list(_dict(artifacts["generated_rule_pack"].payload).get("rules"))
    compliance_findings = _dict_list(_dict(artifacts["compliance_review"].payload).get("findings"))
    matrix_rows = _dict_list(matrix.get("rows"))
    decision_rows = _dict_list(_dict(artifacts["decision_support_report"].payload).get("authority_findings"))
    final_rows = _dict_list(
        _dict(_dict(artifacts["final_qa_report"].payload).get("finding_qa")).get("findings")
    )
    forest_matrix_rows = _dict_list(_dict(matrix.get("forest_plan_compliance")).get("rows"))
    forest_findings = _applicable_forest_plan_findings(
        _dict(artifacts["forest_plan_component_findings"].payload)
    )
    applicable_standards = _applicable_standards(
        _dict(artifacts["forest_plan_applicable_standard_coverage"].payload)
    )
    non_applicable = _dict_list(
        _dict(artifacts["non_applicable_authorities"].payload).get("authorities")
    )
    certificates = _dict_list(
        _dict(artifacts["search_coverage_certificates"].payload).get("certificates")
    )
    source_sets = {
        "applicable_authorities": _rule_id_set(applicable_authorities, _applicable_authority_rule_id),
        "generated_rule_pack": _rule_id_set(generated_rules, _rule_id),
        "compliance_review": _rule_id_set(compliance_findings, _rule_id),
        "compliance_matrix": _rule_id_set(matrix_rows, _rule_id),
        "decision_support": _rule_id_set(decision_rows, _rule_id),
        "final_qa": _rule_id_set(final_rows, _rule_id),
    }
    applicable_rule_ids = sorted(source_sets["applicable_authorities"])
    render_authority_rule_ids = _render_authority_rule_ids(render_manifest)
    forest_matrix_component_ids = _component_id_set(forest_matrix_rows)
    forest_finding_component_ids = _component_id_set(forest_findings)
    render_forest_component_ids = _render_forest_component_ids(render_manifest)
    standard_component_ids = _component_id_set(applicable_standards)
    rule_indexes = {
        "applicable_authorities": {
            _applicable_authority_rule_id(row): row for row in applicable_authorities
        },
        "generated_rule_pack": {_rule_id(row): row for row in generated_rules},
        "compliance_review": {_rule_id(row): row for row in compliance_findings},
        "compliance_matrix": {_rule_id(row): row for row in matrix_rows},
        "decision_support": {_rule_id(row): row for row in decision_rows},
        "final_qa": {_rule_id(row): row for row in final_rows},
    }
    authority_rows = [
        _authority_ledger_row(
            rule_id=rule_id,
            review_dir=review_dir,
            render_manifest_path=render_manifest_path,
            rows_by_artifact={key: index.get(rule_id, {}) for key, index in rule_indexes.items()},
        )
        for rule_id in applicable_rule_ids
    ]
    non_applicable_rows = [
        {
            "row_ledger_id": "row-ledger:non-applicable:" + _safe_marker_id(
                authority.get("decision_id") or authority.get("candidate_authority_id")
            ),
            "row_class": "non_applicable_authority_boundary",
            "candidate_authority_id": authority.get("candidate_authority_id"),
            "decision_id": authority.get("decision_id"),
            "authority_category": authority.get("authority_category"),
            "authority_family_ids": _strings(authority.get("authority_family_ids")),
            "source_record_ids": _strings(authority.get("source_record_ids")),
            "search_coverage_certificate_ids": _strings(
                authority.get("search_coverage_certificate_ids")
            ),
            "canonical_selectors": [
                _selector(
                    review_dir / "applicability" / "non_applicable_authorities.json",
                    f"authorities[decision_id={authority.get('decision_id')}]",
                )
            ],
        }
        for authority in non_applicable
    ]
    forest_rows = [
        _forest_ledger_row(row=row, review_dir=review_dir, render_manifest_path=render_manifest_path)
        for row in sorted(forest_matrix_rows, key=lambda value: str(value.get("component_id")))
    ]
    standard_rows = [
        _standard_ledger_row(row=row, review_dir=review_dir)
        for row in sorted(applicable_standards, key=lambda value: str(value.get("component_key")))
    ]
    return {
        "schema_version": ROW_INVENTORY_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": review_id,
        "source_set_id": matrix.get("source_set_id"),
        "summary": {
            "applicable_authority_count": len(applicable_rule_ids),
            "non_applicable_authority_count": len(non_applicable_rows),
            "forest_plan_component_row_count": len(forest_rows),
            "applicable_standard_count": len(standard_rows),
            "search_coverage_certificate_count": len(certificates),
            "row_set_sha256": _sha256_json(
                {
                    "authority_rule_ids": applicable_rule_ids,
                    "forest_plan_component_ids": sorted(forest_matrix_component_ids),
                    "applicable_standard_component_ids": sorted(standard_component_ids),
                }
            ),
        },
        "artifact_paths": {
            key: str(artifact.path) for key, artifact in sorted(artifacts.items())
        },
        "authority_row_sets": {
            key: sorted(values) for key, values in sorted(source_sets.items())
        },
        "authority_row_comparisons": _row_set_comparisons(source_sets),
        "render_manifest_row_sets": {
            "applicable_authority": sorted(render_authority_rule_ids),
            "forest_plan_component": sorted(render_forest_component_ids),
        },
        "forest_plan_row_sets": {
            "matrix_component_ids": sorted(forest_matrix_component_ids),
            "component_finding_ids": sorted(forest_finding_component_ids),
            "render_manifest_component_ids": sorted(render_forest_component_ids),
            "applicable_standard_component_ids": sorted(standard_component_ids),
        },
        "applicable_authority_rows": authority_rows,
        "non_applicable_authority_rows": non_applicable_rows,
        "forest_plan_component_rows": forest_rows,
        "applicable_forest_plan_standard_rows": standard_rows,
    }


def _build_packet_index(
    *,
    review_id: str,
    review_dir: Path,
    artifacts: dict[str, _Artifact],
    inventory: dict[str, Any],
    render_manifest: dict[str, Any],
    paths: _OutputPaths,
) -> dict[str, Any]:
    decision_support = _dict(artifacts["decision_support_report"].payload)
    final_qa = _dict(artifacts["final_qa_report"].payload)
    return {
        "schema_version": PACKET_INDEX_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "generator_version": GENERATOR_VERSION,
        "review_id": review_id,
        "source_set_id": inventory.get("source_set_id"),
        "review_boundary": {
            "review_id": review_id,
            "review_dir": str(review_dir),
            "root_east_crazies_drafts_are_canonical": False,
        },
        "artifact_inventory": {
            "row_inventory_path": str(paths.row_inventory_path),
            "render_manifest_path": str(paths.render_manifest_path),
            "decision_support_path": str(artifacts["decision_support_report"].path),
            "final_qa_path": str(artifacts["final_qa_report"].path),
            "artifact_hashes": {
                key + "_sha256": artifact.sha256
                for key, artifact in sorted(artifacts.items())
                if artifact.sha256 and key != "final_qa_report"
            },
        },
        "row_inventory_summary": inventory["summary"],
        "render_manifest_summary": render_manifest["summary"],
        "applicable_authority_rows": inventory["applicable_authority_rows"],
        "non_applicable_authority_boundary": {
            "non_applicable_authority_count": inventory["summary"][
                "non_applicable_authority_count"
            ],
            "coverage_certificate_count": inventory["summary"][
                "search_coverage_certificate_count"
            ],
            "appendix_path": str(artifacts["non_applicable_authority_appendix"].path),
            "rows": inventory["non_applicable_authority_rows"],
        },
        "forest_plan_component_rows": inventory["forest_plan_component_rows"],
        "applicable_forest_plan_standard_rows": inventory[
            "applicable_forest_plan_standard_rows"
        ],
        "implementation_confirmation_checklist": _dict_list(
            decision_support.get("implementation_confirmation_checklist")
        ),
        "residual_risk_register": _residual_risk_rows(decision_support, final_qa),
        "validation_and_replay": {
            "replay_commands": [
                (
                    "PYTHONPATH=src python -m usfs_r1_ea_sources review-packet-index "
                    f"--output-dir source_library --review-id {review_id}"
                ),
                (
                    "PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval "
                    f"--output-dir source_library --review-id {review_id}"
                ),
            ],
        },
    }


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
            category="missing_required_artifact" if not artifact.exists else "unparseable_required_artifact",
            details={"path": str(artifact.path), "error": artifact.error},
        )
    authority_sets = {
        key: set(values) for key, values in _dict(inventory.get("authority_row_sets")).items()
    }
    expected_authority_set = authority_sets.get("applicable_authorities", set())
    for key, values in sorted(authority_sets.items()):
        _add_check(
            checks,
            name=f"{key}_authority_rows_match_applicability",
            passed=values == expected_authority_set,
            category="missing_applicable_authority_row",
            details={
                "expected_count": len(expected_authority_set),
                "actual_count": len(values),
                "missing": sorted(expected_authority_set - values),
                "extra": sorted(values - expected_authority_set),
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
            str(row.get("rule_id")) for row in _dict_list(packet_index.get("applicable_authority_rows"))
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
        "generator_version": GENERATOR_VERSION,
        "passed": passed,
        "reviewer_ready": passed,
        "summary": summary,
        "checks": checks,
    }


def _authority_ledger_row(
    *,
    rule_id: str,
    review_dir: Path,
    render_manifest_path: Path,
    rows_by_artifact: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    matrix_row = rows_by_artifact.get("compliance_matrix") or {}
    applicable_row = rows_by_artifact.get("applicable_authorities") or {}
    return {
        "row_ledger_id": f"row-ledger:applicable-authority:{rule_id}",
        "row_class": "applicable_authority",
        "rule_id": rule_id,
        "rule_title": matrix_row.get("rule_title") or matrix_row.get("title"),
        "candidate_authority_id": matrix_row.get("candidate_authority_id")
        or applicable_row.get("candidate_authority_id"),
        "applicability_decision_id": matrix_row.get("applicability_decision_id")
        or applicable_row.get("decision_id"),
        "authority_category": matrix_row.get("authority_category")
        or applicable_row.get("authority_category"),
        "authority_source_record_id": matrix_row.get("authority_source_record_id"),
        "authority_family_ids": _strings(matrix_row.get("authority_family_ids"))
        or _strings(applicable_row.get("authority_family_ids")),
        "compliance_status": matrix_row.get("status"),
        "applicability_status": matrix_row.get("applicability_status")
        or applicable_row.get("status"),
        "applicability_mode": matrix_row.get("applicability_mode"),
        "ea_package_citation": matrix_row.get("ea_package_citation"),
        "source_library_citation": matrix_row.get("source_library_citation"),
        "source_claim_ids": _strings(matrix_row.get("source_claim_ids")),
        "canonical_selectors": [
            _selector(review_dir / "applicability" / "applicable_authorities.json", f"rule_id={rule_id}"),
            _selector(review_dir / "applicability" / "generated_rule_pack.json", f"rules[id={rule_id}]"),
            _selector(review_dir / "compliance_review.json", f"findings[rule_id={rule_id}]"),
            _selector(review_dir / "compliance_matrix.json", f"rows[rule_id={rule_id}]"),
            _selector(render_manifest_path, f"rows[row_identity.rule_id={rule_id}]"),
            _selector(
                review_dir / "decision_support" / "ea_consistency_decision_support.json",
                f"authority_findings[rule_id={rule_id}]",
            ),
            _selector(
                review_dir / "final_qa" / "east_crazies_final_qa_certification.json",
                f"finding_qa.findings[rule_id={rule_id}]",
            ),
        ],
        "render_markdown_marker": _matrix_row_marker("authority", rule_id),
    }


def _forest_ledger_row(*, row: dict[str, Any], review_dir: Path, render_manifest_path: Path) -> dict[str, Any]:
    component_id = str(row.get("component_id") or "")
    return {
        "row_ledger_id": f"row-ledger:forest-plan-component:{_safe_marker_id(component_id)}",
        "row_class": "forest_plan_component",
        "component_id": component_id,
        "component_key": row.get("component_key"),
        "component_type": row.get("component_type"),
        "applicability_status": row.get("applicability_status"),
        "compliance_status": row.get("compliance_status"),
        "finding_status": row.get("finding_status"),
        "standard_applied": row.get("standard_applied"),
        "ea_package_citation": row.get("ea_package_citation"),
        "forest_plan_citation": row.get("forest_plan_citation"),
        "canonical_selectors": [
            _selector(review_dir / "forest_plan_component_findings.json", f"findings[component_id={component_id}]"),
            _selector(review_dir / "compliance_matrix.json", f"forest_plan_compliance.rows[component_id={component_id}]"),
            _selector(render_manifest_path, f"rows[row_identity.component_id={component_id}]"),
        ],
        "render_markdown_marker": _matrix_row_marker("forest-plan", component_id),
    }


def _standard_ledger_row(*, row: dict[str, Any], review_dir: Path) -> dict[str, Any]:
    component_id = str(row.get("component_id") or "")
    return {
        "row_ledger_id": f"row-ledger:forest-plan-standard:{_safe_marker_id(component_id)}",
        "row_class": "forest_plan_standard",
        "component_id": component_id,
        "component_key": row.get("component_key"),
        "applicability_status": row.get("applicability_status"),
        "compliance_status": row.get("compliance_status"),
        "finding_status": row.get("finding_status"),
        "standard_applied": row.get("standard_applied"),
        "canonical_selectors": [
            _selector(
                review_dir / "forest_plan_applicable_standard_coverage.json",
                f"standards[component_id={component_id}]",
            )
        ],
    }


def _render_manifest_row(
    *,
    row_class: str,
    row: dict[str, Any],
    row_order: int,
    section: str,
    table_id: str,
    json_selector: str,
    markdown_marker: str,
    row_identity: dict[str, Any],
) -> dict[str, Any]:
    return {
        "row_render_id": f"render:{row_class}:{_safe_marker_id(row.get('row_id') or json_selector)}",
        "row_class": row_class,
        "row_id": row.get("row_id"),
        "row_order": row_order,
        "section": section,
        "table_id": table_id,
        "json_selector": json_selector,
        "markdown_marker": markdown_marker,
        "pdf_render_contract": "pdf_generated_from_manifested_matrix_rows",
        "row_identity": row_identity,
        "source_record_ids": _render_source_record_ids(row),
        "status": row.get("status") or row.get("compliance_status"),
        "applicability_status": row.get("applicability_status"),
        "row_hash": _sha256_json(row),
    }


def _inventory_markdown(inventory: dict[str, Any]) -> str:
    summary = inventory["summary"]
    lines = [
        "# Review Packet Row Inventory",
        "",
        f"- Review ID: `{inventory['review_id']}`",
        f"- Source set: `{inventory['source_set_id']}`",
        f"- Applicable authority rows: `{summary['applicable_authority_count']}`",
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
        f"Non-applicable authority boundary rows: {summary['non_applicable_authority_count']}",
        f"Forest Plan component rows: {summary['forest_plan_component_row_count']}",
        f"Applicable Forest Plan standards: {summary['applicable_standard_count']}",
        "Root-level East_Crazies_* draft exports are not canonical review artifacts.",
    ]


def _applicable_authority_rule_id(row: dict[str, Any]) -> str:
    rule_template = _dict(row.get("rule_template"))
    metadata = _dict(row.get("generated_rule_metadata"))
    return str(
        rule_template.get("rule_id")
        or metadata.get("source_base_rule_id")
        or row.get("rule_id")
        or row.get("id")
        or ""
    )


def _rule_id(row: dict[str, Any]) -> str:
    return str(row.get("rule_id") or row.get("id") or row.get("generated_rule_id") or "")


def _rule_id_set(rows: list[dict[str, Any]], resolver) -> set[str]:
    return {rule_id for row in rows if (rule_id := resolver(row))}


def _component_id_set(rows: list[dict[str, Any]]) -> set[str]:
    return {str(row.get("component_id")) for row in rows if row.get("component_id")}


def _applicable_forest_plan_findings(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for finding in _dict_list(payload.get("findings")):
        compliance_status = finding.get("compliance_status")
        if finding.get("applicability_status") == "applicable" or compliance_status in {
            "complies",
            "does_not_comply",
            "partial",
            "uncertain",
        }:
            rows.append(finding)
    return rows


def _applicable_standards(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for row in _dict_list(payload.get("standards"))
        if row.get("applicability_status") == "applicable"
    ]


def _row_set_comparisons(row_sets: dict[str, set[str]]) -> dict[str, Any]:
    base = row_sets.get("applicable_authorities", set())
    return {
        key: {
            "matches_applicable_authorities": values == base,
            "missing_from_artifact": sorted(base - values),
            "extra_in_artifact": sorted(values - base),
        }
        for key, values in sorted(row_sets.items())
    }


def _render_authority_rule_ids(render_manifest: dict[str, Any]) -> set[str]:
    return {
        str(_dict(row.get("row_identity")).get("rule_id"))
        for row in _dict_list(render_manifest.get("rows"))
        if row.get("row_class") == "applicable_authority"
    }


def _render_forest_component_ids(render_manifest: dict[str, Any]) -> set[str]:
    return {
        str(_dict(row.get("row_identity")).get("component_id"))
        for row in _dict_list(render_manifest.get("rows"))
        if row.get("row_class") == "forest_plan_component"
    }


def _render_source_record_ids(row: dict[str, Any]) -> list[str]:
    values = []
    for key in ("authority_source_record_id", "applied_source_record_ids"):
        value = row.get(key)
        if isinstance(value, list):
            values.extend(str(item) for item in value if item)
        elif value:
            values.append(str(value))
    return sorted(set(values))


def _residual_risk_rows(decision_support: dict[str, Any], final_qa: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    rows.extend(_dict_list(decision_support.get("residual_risk_register")))
    blockers = _dict(_dict(final_qa.get("residual_blockers_and_stop_conditions")))
    for blocker in _dict_list(blockers.get("blockers")):
        rows.append(
            {
                "risk_id": blocker.get("id") or blocker.get("name"),
                "category": blocker.get("category") or "final_qa_blocker",
                "source": "final_qa",
            }
        )
    return rows


def _land_exchange_rows_present(inventory: dict[str, Any]) -> bool:
    rows = {
        str(row.get("rule_id")): row
        for row in _dict_list(inventory.get("applicable_authority_rows"))
    }
    if not (set(rows) & set(LAND_EXCHANGE_RULE_SOURCES)):
        return True
    for rule_id, source_record_id in LAND_EXCHANGE_RULE_SOURCES.items():
        row = rows.get(rule_id)
        if row is None or row.get("authority_source_record_id") != source_record_id:
            return False
    return True


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


def _selector(path: Path, selector: str) -> dict[str, str]:
    return {"artifact_path": str(path), "selector": selector}


def _matrix_row_marker(row_class: str, row_id: object) -> str:
    return f"matrix-row:{row_class}:{_safe_marker_id(row_id)}"


def _safe_marker_id(value: object) -> str:
    text = str(value or "unknown")
    return re.sub(r"[^A-Za-z0-9_.:-]+", "-", text).strip("-") or "unknown"


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _dict_list(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _strings(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item not in (None, "")]
    if value in (None, ""):
        return []
    return [str(value)]


def _md_cell(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _row_set_sha256(rows: list[dict[str, Any]]) -> str:
    return _sha256_json(
        [
            {
                "row_class": row.get("row_class"),
                "row_identity": row.get("row_identity"),
                "row_hash": row.get("row_hash"),
            }
            for row in rows
        ]
    )


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_simple_pdf(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content_lines = ["BT", "/F1 12 Tf", "72 740 Td"]
    for line in lines:
        content_lines.append(f"({_escape_pdf_text(line)}) Tj")
        content_lines.append("0 -18 Td")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length "
        + str(len(stream)).encode("ascii")
        + b" >>\nstream\n"
        + stream
        + b"\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for index, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode("ascii"))
        output.extend(body)
        output.extend(b"\nendobj\n")
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode("ascii")
    )
    path.write_bytes(bytes(output))


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
