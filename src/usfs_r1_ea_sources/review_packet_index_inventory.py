from __future__ import annotations

from pathlib import Path
from typing import Any

from .review_packet_index_common import _Artifact
from .review_packet_index_common import _dict
from .review_packet_index_common import _dict_list
from .review_packet_index_common import _matrix_row_marker
from .review_packet_index_common import _OutputPaths
from .review_packet_index_common import _row_set_sha256
from .review_packet_index_common import _safe_marker_id
from .review_packet_index_common import _selector
from .review_packet_index_common import _sha256_json
from .review_packet_index_common import _strings
from .review_packet_index_common import _utc_now
from .review_packet_index_common import GENERATOR_VERSION
from .review_packet_index_common import LAND_EXCHANGE_RULE_SOURCES
from .review_packet_index_common import PACKET_INDEX_SCHEMA_VERSION
from .review_packet_index_common import RENDER_MANIFEST_SCHEMA_VERSION
from .review_packet_index_common import ROW_INVENTORY_SCHEMA_VERSION


def _build_render_manifest(*, matrix: dict, markdown: str, pdf_path: Path) -> dict[str, Any]:
    rows = []
    for index, row in enumerate(_dict_list(matrix.get("rows")), start=1):
        rule_id = str(row.get("rule_id") or "")
        rows.append(
            _render_manifest_row(
                row_class="applicable_authority",
                row=row,
                row_order=index,
                section="NEPA / Authority Compliance",
                table_id="nepa_authority_compliance",
                json_selector=f"rows[rule_id={rule_id}]",
                markdown_marker=_matrix_row_marker("authority", rule_id),
                row_identity={"rule_id": rule_id},
            )
        )
    forest_rows = _dict_list(_dict(matrix.get("forest_plan_compliance")).get("rows"))
    for index, row in enumerate(forest_rows, start=1):
        component_id = str(row.get("component_id") or "")
        rows.append(
            _render_manifest_row(
                row_class="forest_plan_component",
                row=row,
                row_order=index,
                section="Forest Plan Compliance",
                table_id="forest_plan_compliance",
                json_selector=f"forest_plan_compliance.rows[component_id={component_id}]",
                markdown_marker=_matrix_row_marker("forest-plan", component_id),
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
    sidecar_lineage: dict[str, Any],
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
    forest_plan_summary = _dict(_dict(matrix.get("forest_plan_compliance")).get("summary"))
    forest_component_evaluation = _dict(forest_plan_summary.get("component_evaluation"))
    forest_standard_coverage = _dict(artifacts["forest_plan_applicable_standard_coverage"].payload)
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
    land_exchange_rows = _land_exchange_ledger_rows(authority_rows)
    return {
        "schema_version": ROW_INVENTORY_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": review_id,
        "source_set_id": matrix.get("source_set_id"),
        "summary": {
            "applicable_authority_count": len(applicable_rule_ids),
            "land_exchange_row_count": len(land_exchange_rows),
            "non_applicable_authority_count": len(non_applicable_rows),
            "forest_plan_component_row_count": len(forest_rows),
            "applicable_standard_count": len(standard_rows),
            "forest_plan_reviewer_ready": bool(forest_plan_summary.get("reviewer_ready")),
            "forest_plan_component_reviewer_ready": bool(
                forest_component_evaluation.get("reviewer_ready")
            ),
            "forest_plan_expected_applicable_standard_count": int(
                forest_component_evaluation.get("applicable_standard_count")
                or forest_plan_summary.get("applicable_standard_row_count")
                or 0
            ),
            "forest_plan_applicable_standard_coverage_passed": bool(
                forest_standard_coverage.get("passed")
            ),
            "search_coverage_certificate_count": len(certificates),
            "row_set_sha256": _sha256_json(
                {
                    "authority_rule_ids": applicable_rule_ids,
                    "forest_plan_component_ids": sorted(forest_matrix_component_ids),
                    "applicable_standard_component_ids": sorted(standard_component_ids),
                }
            ),
            "sidecar_rule_claim_links_used": bool(
                sidecar_lineage.get("sidecar_rule_claim_links_used")
            ),
        },
        "artifact_paths": {
            key: str(artifact.path) for key, artifact in sorted(artifacts.items())
        },
        "sidecar_rule_claim_lineage": sidecar_lineage,
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
        "land_exchange_rows": land_exchange_rows,
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
    sidecar_lineage: dict[str, Any],
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
        "sidecar_rule_claim_lineage": sidecar_lineage,
        "applicable_authority_rows": inventory["applicable_authority_rows"],
        "land_exchange_rows": inventory["land_exchange_rows"],
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


def _forest_ledger_row(
    *,
    row: dict[str, Any],
    review_dir: Path,
    render_manifest_path: Path,
) -> dict[str, Any]:
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


def _land_exchange_ledger_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if str(row.get("rule_id")) in LAND_EXCHANGE_RULE_SOURCES
    ]


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
