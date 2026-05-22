from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .nepa_knowledge_graph_export_models import REGION1_FOREST_PLAN_READINESS_SCHEMA_VERSION
from .nepa_knowledge_graph_export_models import _check
from .nepa_knowledge_graph_export_models import _dict
from .nepa_knowledge_graph_export_models import _dict_list
from .nepa_knowledge_graph_export_models import _family_node_id
from .nepa_knowledge_graph_export_models import _strings
from .nepa_knowledge_graph_export_common import _missing_summary_count_fields
from .nepa_knowledge_graph_export_region1 import _region1_component_node_id
from .nepa_knowledge_graph_export_region1 import _region1_field_directive_component_id
from .nepa_knowledge_graph_export_region1 import _region1_overlay_component_id
from .nepa_knowledge_graph_export_region1 import _region1_profile_meets_eval_fixture_floor
from .nepa_knowledge_graph_export_region1 import _region1_profile_readiness_blockers
from .nepa_knowledge_graph_export_region1 import _region1_profile_readiness_rows
from .nepa_knowledge_graph_export_region1 import _region1_requirement_edge_gaps
from .nepa_knowledge_graph_export_region1 import _region1_requirement_source_gaps
from .nepa_knowledge_graph_export_review_validation import _forest_plan_inventory_ownership


def _milestone_validation_checks(
    *,
    graph: dict[str, Any],
    inventory: dict[str, Any],
    catalog_rows: list[dict[str, Any]],
    rule_pack: dict[str, Any],
    template_config: dict[str, Any],
    currentness: dict[str, Any],
    rule_claim_links: list[dict[str, Any]],
    forest_components: dict[str, Any],
    forest_plan_profiles: dict[str, Any],
    region1_forest_plan_readiness: dict[str, Any],
    forest_plan_components_path: Path,
    inputs: list[dict[str, Any]],
    catalog_graph_node_count: int,
    catalog_graph_edge_count: int,
    output_dir: Path,
    source_set_id: str,
    is_source_register_v1: bool,
) -> list[dict[str, Any]]:
    node_ids = {node["node_id"] for node in graph["nodes"]}
    edge_tuples = {
        (
            str(edge.get("edge_type") or ""),
            str(edge.get("source_node_id") or ""),
            str(edge.get("target_node_id") or ""),
        )
        for edge in _dict_list(graph.get("edges"))
    }
    display_status_by_node_id = {node["node_id"]: node["display_status"] for node in graph["nodes"]}
    family_ids = {str(family.get("family_id")) for family in inventory.get("authority_families", [])}
    source_record_ids = {str(row.get("source_record_id")) for row in catalog_rows}
    rule_ids = {str(rule.get("id")) for rule in rule_pack.get("rules", [])}
    template_ids = {str(template.get("template_id")) for template in template_config.get("templates", [])}
    exported_family_ids = {
        node["provenance"].get("authority_family_id")
        for node in graph["nodes"]
        if node["node_type"] == "authority_family"
    }
    exported_source_record_ids = {
        node["provenance"].get("source_record_id")
        for node in graph["nodes"]
        if node["node_type"] == "source_record"
    }
    exported_rule_ids = {
        node["provenance"].get("rule_id")
        for node in graph["nodes"]
        if node["node_type"] == "rule_template"
        and node.get("metadata", {}).get("rule_kind") == "base_rule_pack_rule"
    }
    exported_template_ids = {
        node["provenance"].get("template_id")
        for node in graph["nodes"]
        if node["node_type"] == "rule_template"
        and node.get("metadata", {}).get("rule_kind") == "authority_family_template"
    }
    exported_forest_unit_ids = {
        node["provenance"].get("forest_code")
        for node in graph["nodes"]
        if node["node_type"] == "forest_unit"
    }
    active_profile_ids = {
        str(profile.get("forest_unit_id") or "")
        for profile in _dict_list(forest_plan_profiles.get("profiles"))
        if profile.get("forest_unit_id")
    }
    known_region1_unit_ids = {
        str(unit.get("forest_unit_id") or "")
        for unit in _dict_list(forest_plan_profiles.get("known_other_forest_units"))
        if unit.get("forest_unit_id")
    }
    readiness_rows = _region1_profile_readiness_rows(region1_forest_plan_readiness)
    readiness_ids = {
        str(row.get("forest_unit_id") or "") for row in readiness_rows if row.get("forest_unit_id")
    }
    blocked_profile_ids_without_blockers = sorted(
        str(row.get("forest_unit_id") or "")
        for row in readiness_rows
        if row.get("graph_promotion_status") != "promoted"
        and not _region1_profile_readiness_blockers(row)
    )
    promoted_rows = [
        row for row in readiness_rows if row.get("graph_promotion_status") == "promoted"
    ]
    catalog_source_ids = {str(row.get("source_record_id") or "") for row in catalog_rows}
    promoted_missing_sources = {
        str(row.get("forest_unit_id") or ""): sorted(
            source_record_id
            for source_record_id in (
                str(requirement.get("source_record_id") or "")
                for requirement in _dict_list(row.get("source_requirements"))
                if requirement.get("readiness_status") == "catalog_confirmed"
            )
            if source_record_id
            and source_record_id not in catalog_source_ids
            and source_record_id
            not in {
                str(source_id)
                for source_id in _strings(
                    _dict(row.get("identity_reconciliation")).get(
                        "remaining_unresolved_source_record_ids"
                    )
                )
            }
        )
        for row in promoted_rows
    }
    promoted_missing_sources = {
        forest_unit_id: missing
        for forest_unit_id, missing in promoted_missing_sources.items()
        if missing
    }
    component_forest_unit_ids = {
        str(component.get("forest_unit_id") or "")
        for component in _dict_list(forest_components.get("components"))
        if component.get("forest_unit_id")
    }
    promoted_without_inventory = sorted(
        str(row.get("forest_unit_id") or "")
        for row in promoted_rows
        if str(row.get("forest_unit_id") or "") not in component_forest_unit_ids
    )
    overclaim = bool(region1_forest_plan_readiness.get("region1_completeness_claim"))
    non_promoted_readiness_ids = {
        str(row.get("forest_unit_id") or "")
        for row in readiness_rows
        if row.get("graph_promotion_status") != "promoted"
    }
    candidate_family_ids = {
        str(family.get("family_id"))
        for family in inventory.get("authority_families", [])
        if family.get("status") == "candidate"
    }
    superseded_family_ids = {
        str(family.get("family_id"))
        for family in inventory.get("authority_families", [])
        if family.get("status") == "superseded"
    }
    input_failures = [
        input_record["name"] for input_record in inputs if not input_record.get("exists")
    ]
    field_directive_requirement_node_ids = {
        _region1_component_node_id(_region1_field_directive_component_id(requirement))
        for requirement in _dict_list(
            region1_forest_plan_readiness.get("field_directive_requirements")
        )
        if requirement.get("requirement_id")
    }
    overlay_requirement_node_ids = {
        _region1_component_node_id(_region1_overlay_component_id(requirement))
        for requirement in _dict_list(region1_forest_plan_readiness.get("overlay_requirements"))
        if requirement.get("overlay_id")
    }
    support_document_summary = _dict(
        region1_forest_plan_readiness.get("support_document_corpus_summary")
    )
    enforce_region1_requirement_catalog_checks = (
        not is_source_register_v1 or bool(support_document_summary)
    )
    region1_requirement_source_gaps = (
        _region1_requirement_source_gaps(
            region1_forest_plan_readiness,
            catalog_source_ids=catalog_source_ids,
        )
        if enforce_region1_requirement_catalog_checks
        else {}
    )
    region1_requirement_edge_gaps = (
        _region1_requirement_edge_gaps(
            region1_forest_plan_readiness,
            edge_tuples=edge_tuples,
        )
        if enforce_region1_requirement_catalog_checks
        else {}
    )
    inventory_ownership = _forest_plan_inventory_ownership(
        forest_components=forest_components,
        forest_plan_components_path=forest_plan_components_path,
        output_dir=output_dir,
        source_set_id=source_set_id,
    )
    if is_source_register_v1:
        return [
            _check("nepa_3d_graph_inputs_exist", not input_failures, [], input_failures),
            _check(
                "nepa_3d_graph_reads_catalog_graph_seeds",
                catalog_graph_node_count > 0 and catalog_graph_edge_count > 0,
                {"catalog_graph_node_count": "> 0", "catalog_graph_edge_count": "> 0"},
                {
                    "catalog_graph_node_count": catalog_graph_node_count,
                    "catalog_graph_edge_count": catalog_graph_edge_count,
                },
            ),
            _check(
                "nepa_3d_graph_reports_required_summary_count_fields",
                not _missing_summary_count_fields(graph),
                [
                    "node_type_counts",
                    "edge_type_counts",
                    "authority_category_counts",
                    "source_status_counts",
                    "source_partition_counts",
                    "applicability_status_counts",
                    "readiness_blocker_counts",
                ],
                _missing_summary_count_fields(graph),
            ),
            _check(
                "nepa_3d_graph_currentness_gate_passed",
                bool(
                    _dict(currentness.get("validation")).get("passed")
                    or _dict(currentness.get("summary")).get("validation_passed")
                ),
                True,
                {
                    "validation": _dict(currentness.get("validation")).get("passed"),
                    "summary": _dict(currentness.get("summary")).get("validation_passed"),
                },
            ),
            _check(
                "nepa_3d_graph_exports_all_authority_families",
                family_ids <= exported_family_ids,
                sorted(family_ids),
                sorted(family_ids - exported_family_ids),
            ),
            _check(
                "nepa_3d_graph_exports_all_catalog_source_records",
                source_record_ids <= exported_source_record_ids,
                sorted(source_record_ids),
                sorted(source_record_ids - exported_source_record_ids),
            ),
            _check(
                "nepa_3d_graph_exports_candidate_families",
                all(
                    display_status_by_node_id.get(_family_node_id(family_id)) == "candidate"
                    for family_id in candidate_family_ids
                ),
                sorted(candidate_family_ids),
                {
                    family_id: display_status_by_node_id.get(_family_node_id(family_id))
                    for family_id in sorted(candidate_family_ids)
                },
            ),
            _check(
                "nepa_3d_graph_exports_superseded_families",
                all(
                    display_status_by_node_id.get(_family_node_id(family_id)) == "superseded"
                    for family_id in superseded_family_ids
                ),
                sorted(superseded_family_ids),
                {
                    family_id: display_status_by_node_id.get(_family_node_id(family_id))
                    for family_id in sorted(superseded_family_ids)
                },
            ),
            *_region1_graph_checks(
                node_ids=node_ids,
                exported_forest_unit_ids=exported_forest_unit_ids,
                active_profile_ids=active_profile_ids,
                known_region1_unit_ids=known_region1_unit_ids,
                readiness_ids=readiness_ids,
                readiness_rows=readiness_rows,
                blocked_profile_ids_without_blockers=blocked_profile_ids_without_blockers,
                promoted_rows=promoted_rows,
                promoted_missing_sources=promoted_missing_sources,
                promoted_without_inventory=promoted_without_inventory,
                overclaim=overclaim,
                non_promoted_readiness_ids=non_promoted_readiness_ids,
                field_directive_requirement_node_ids=field_directive_requirement_node_ids,
                overlay_requirement_node_ids=overlay_requirement_node_ids,
                region1_requirement_source_gaps=region1_requirement_source_gaps,
                region1_requirement_edge_gaps=region1_requirement_edge_gaps,
                region1_forest_plan_readiness=region1_forest_plan_readiness,
                forest_components=forest_components,
                forest_plan_components_path=forest_plan_components_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
            ),
            *_canonical_source_register_graph_checks(
                graph=graph,
                catalog_rows=catalog_rows,
                edge_tuples=edge_tuples,
            ),
        ]
    return [
        _check("nepa_3d_graph_inputs_exist", not input_failures, [], input_failures),
        _check(
            "nepa_3d_graph_reads_catalog_graph_seeds",
            catalog_graph_node_count > 0 and catalog_graph_edge_count > 0,
            {"catalog_graph_node_count": "> 0", "catalog_graph_edge_count": "> 0"},
            {
                "catalog_graph_node_count": catalog_graph_node_count,
                "catalog_graph_edge_count": catalog_graph_edge_count,
            },
        ),
        _check(
            "nepa_3d_graph_reports_required_summary_count_fields",
            not _missing_summary_count_fields(graph),
            [
                "node_type_counts",
                "edge_type_counts",
                "authority_category_counts",
                "source_status_counts",
                "source_partition_counts",
                "applicability_status_counts",
                "readiness_blocker_counts",
            ],
            _missing_summary_count_fields(graph),
        ),
        _check(
            "nepa_3d_graph_currentness_gate_passed",
            bool(
                _dict(currentness.get("validation")).get("passed")
                or _dict(currentness.get("summary")).get("validation_passed")
            ),
            True,
            {
                "validation": _dict(currentness.get("validation")).get("passed"),
                "summary": _dict(currentness.get("summary")).get("validation_passed"),
            },
        ),
        _check(
            "nepa_3d_graph_exports_all_authority_families",
            family_ids <= exported_family_ids,
            sorted(family_ids),
            sorted(family_ids - exported_family_ids),
        ),
        _check(
            "nepa_3d_graph_exports_all_catalog_source_records",
            source_record_ids <= exported_source_record_ids,
            sorted(source_record_ids),
            sorted(source_record_ids - exported_source_record_ids),
        ),
        _check(
            "nepa_3d_graph_exports_all_base_rules",
            rule_ids <= exported_rule_ids,
            sorted(rule_ids),
            sorted(rule_ids - exported_rule_ids),
        ),
        _check(
            "nepa_3d_graph_exports_all_authority_family_templates",
            template_ids <= exported_template_ids,
            sorted(template_ids),
            sorted(template_ids - exported_template_ids),
        ),
        _check(
            "nepa_3d_graph_exports_candidate_families",
            all(display_status_by_node_id.get(_family_node_id(family_id)) == "candidate" for family_id in candidate_family_ids),
            sorted(candidate_family_ids),
            {
                family_id: display_status_by_node_id.get(_family_node_id(family_id))
                for family_id in sorted(candidate_family_ids)
            },
        ),
        _check(
            "nepa_3d_graph_exports_superseded_families",
            all(display_status_by_node_id.get(_family_node_id(family_id)) == "superseded" for family_id in superseded_family_ids),
            sorted(superseded_family_ids),
            {
                family_id: display_status_by_node_id.get(_family_node_id(family_id))
                for family_id in sorted(superseded_family_ids)
            },
        ),
        _check(
            "nepa_3d_graph_uses_rule_claim_links",
            bool(rule_claim_links),
            "at least one rule claim link",
            len(rule_claim_links),
        ),
        _check(
            "nepa_3d_graph_exports_forest_plan_components",
            bool(forest_components.get("components")),
            "at least one forest plan component",
            len(forest_components.get("components", [])),
        ),
        _check(
            "nepa_3d_graph_forest_plan_inventory_owned_by_source_set",
            inventory_ownership["passed"],
            inventory_ownership["expected"],
            inventory_ownership["actual"],
        ),
        _check(
            "nepa_3d_graph_region1_readiness_matrix_loaded",
            region1_forest_plan_readiness.get("schema_version")
            == REGION1_FOREST_PLAN_READINESS_SCHEMA_VERSION,
            REGION1_FOREST_PLAN_READINESS_SCHEMA_VERSION,
            region1_forest_plan_readiness.get("schema_version"),
        ),
        _check(
            "nepa_3d_graph_region1_readiness_covers_configured_profiles",
            active_profile_ids <= readiness_ids,
            sorted(active_profile_ids),
            sorted(active_profile_ids - readiness_ids),
        ),
        _check(
            "nepa_3d_graph_region1_readiness_tracks_known_region1_units",
            known_region1_unit_ids <= readiness_ids,
            sorted(known_region1_unit_ids),
            sorted(known_region1_unit_ids - readiness_ids),
        ),
        _check(
            "nepa_3d_graph_region1_readiness_prevents_overclaim",
            not overclaim or not non_promoted_readiness_ids,
            "region1_completeness_claim is false until every tracked profile is promoted",
            {
                "region1_completeness_claim": overclaim,
                "non_promoted_profile_ids": sorted(non_promoted_readiness_ids),
            },
        ),
        _check(
            "nepa_3d_graph_exports_region1_forest_units",
            readiness_ids <= exported_forest_unit_ids,
            sorted(readiness_ids),
            sorted(readiness_ids - exported_forest_unit_ids),
        ),
        _check(
            "nepa_3d_graph_region1_promoted_profiles_have_eval_fixtures",
            bool(promoted_rows)
            and all(_region1_profile_meets_eval_fixture_floor(row) for row in promoted_rows),
            "governed eval fixture floor for each promoted Region 1 profile",
            {
                str(row.get("forest_unit_id") or ""): _region1_profile_meets_eval_fixture_floor(row)
                for row in promoted_rows
            },
        ),
        _check(
            "nepa_3d_graph_region1_promoted_profiles_have_inventory",
            not promoted_without_inventory,
            "component inventory for each graph-promoted profile",
            promoted_without_inventory,
        ),
        _check(
            "nepa_3d_graph_region1_promoted_profiles_have_catalog_sources",
            not promoted_missing_sources,
            "catalog-confirmed source records exist for each graph-promoted profile",
            promoted_missing_sources,
        ),
        _check(
            "nepa_3d_graph_exports_region1_field_directive_requirements",
            field_directive_requirement_node_ids <= node_ids,
            sorted(field_directive_requirement_node_ids),
            sorted(field_directive_requirement_node_ids - node_ids),
        ),
        _check(
            "nepa_3d_graph_exports_region1_overlay_requirements",
            overlay_requirement_node_ids <= node_ids,
            sorted(overlay_requirement_node_ids),
            sorted(overlay_requirement_node_ids - node_ids),
        ),
        _check(
            "nepa_3d_graph_region1_requirement_sources_are_cataloged",
            not region1_requirement_source_gaps,
            "catalog-confirmed field directive and overlay source records exist",
            region1_requirement_source_gaps,
        ),
        _check(
            "nepa_3d_graph_region1_requirement_sources_are_linked",
            not region1_requirement_edge_gaps,
            "HAS_FOREST_COMPONENT edges from source records to field directive and overlay nodes",
            region1_requirement_edge_gaps,
        ),
        _check(
            "nepa_3d_graph_region1_blocked_profiles_have_blockers",
            not blocked_profile_ids_without_blockers,
            "readiness blockers for each non-promoted profile",
            blocked_profile_ids_without_blockers,
        ),
        _check(
            "nepa_3d_graph_has_readiness_blocker_nodes",
            any(node_id.startswith("readiness_blocker:") for node_id in node_ids),
            "readiness blocker nodes present",
            sorted(node_id for node_id in node_ids if node_id.startswith("readiness_blocker:")),
        ),
    ]


def _region1_graph_checks(
    *,
    node_ids: set[str],
    exported_forest_unit_ids: set[str],
    active_profile_ids: set[str],
    known_region1_unit_ids: set[str],
    readiness_ids: set[str],
    readiness_rows: list[dict[str, Any]],
    blocked_profile_ids_without_blockers: list[str],
    promoted_rows: list[dict[str, Any]],
    promoted_missing_sources: dict[str, list[str]],
    promoted_without_inventory: list[str],
    overclaim: bool,
    non_promoted_readiness_ids: set[str],
    field_directive_requirement_node_ids: set[str],
    overlay_requirement_node_ids: set[str],
    region1_requirement_source_gaps: dict[str, list[str]],
    region1_requirement_edge_gaps: dict[str, list[str]],
    region1_forest_plan_readiness: dict[str, Any],
    forest_components: dict[str, Any],
    forest_plan_components_path: Path,
    output_dir: Path,
    source_set_id: str,
) -> list[dict[str, Any]]:
    inventory_ownership = _forest_plan_inventory_ownership(
        forest_components=forest_components,
        forest_plan_components_path=forest_plan_components_path,
        output_dir=output_dir,
        source_set_id=source_set_id,
    )
    return [
        _check(
            "nepa_3d_graph_exports_forest_plan_components",
            bool(forest_components.get("components")),
            "at least one forest plan component",
            len(forest_components.get("components", [])),
        ),
        _check(
            "nepa_3d_graph_forest_plan_inventory_owned_by_source_set",
            inventory_ownership["passed"],
            inventory_ownership["expected"],
            inventory_ownership["actual"],
        ),
        _check(
            "nepa_3d_graph_region1_readiness_matrix_loaded",
            region1_forest_plan_readiness.get("schema_version")
            == REGION1_FOREST_PLAN_READINESS_SCHEMA_VERSION,
            REGION1_FOREST_PLAN_READINESS_SCHEMA_VERSION,
            region1_forest_plan_readiness.get("schema_version"),
        ),
        _check(
            "nepa_3d_graph_region1_readiness_covers_configured_profiles",
            active_profile_ids <= readiness_ids,
            sorted(active_profile_ids),
            sorted(active_profile_ids - readiness_ids),
        ),
        _check(
            "nepa_3d_graph_region1_readiness_tracks_known_region1_units",
            known_region1_unit_ids <= readiness_ids,
            sorted(known_region1_unit_ids),
            sorted(known_region1_unit_ids - readiness_ids),
        ),
        _check(
            "nepa_3d_graph_region1_readiness_prevents_overclaim",
            not overclaim or not non_promoted_readiness_ids,
            "region1_completeness_claim is false until every tracked profile is promoted",
            {
                "region1_completeness_claim": overclaim,
                "non_promoted_profile_ids": sorted(non_promoted_readiness_ids),
            },
        ),
        _check(
            "nepa_3d_graph_exports_region1_forest_units",
            readiness_ids <= exported_forest_unit_ids,
            sorted(readiness_ids),
            sorted(readiness_ids - exported_forest_unit_ids),
        ),
        _check(
            "nepa_3d_graph_region1_promoted_profiles_have_eval_fixtures",
            bool(promoted_rows)
            and all(_region1_profile_meets_eval_fixture_floor(row) for row in promoted_rows),
            "governed eval fixture floor for each promoted Region 1 profile",
            {
                str(row.get("forest_unit_id") or ""): _region1_profile_meets_eval_fixture_floor(row)
                for row in promoted_rows
            },
        ),
        _check(
            "nepa_3d_graph_region1_promoted_profiles_have_inventory",
            not promoted_without_inventory,
            "component inventory for each graph-promoted profile",
            promoted_without_inventory,
        ),
        _check(
            "nepa_3d_graph_region1_promoted_profiles_have_catalog_sources",
            not promoted_missing_sources,
            "catalog-confirmed source records exist for each graph-promoted profile",
            promoted_missing_sources,
        ),
        _check(
            "nepa_3d_graph_exports_region1_field_directive_requirements",
            field_directive_requirement_node_ids <= node_ids,
            sorted(field_directive_requirement_node_ids),
            sorted(field_directive_requirement_node_ids - node_ids),
        ),
        _check(
            "nepa_3d_graph_exports_region1_overlay_requirements",
            overlay_requirement_node_ids <= node_ids,
            sorted(overlay_requirement_node_ids),
            sorted(overlay_requirement_node_ids - node_ids),
        ),
        _check(
            "nepa_3d_graph_region1_requirement_sources_are_cataloged",
            not region1_requirement_source_gaps,
            "catalog-confirmed field directive and overlay source records exist",
            region1_requirement_source_gaps,
        ),
        _check(
            "nepa_3d_graph_region1_requirement_sources_are_linked",
            not region1_requirement_edge_gaps,
            "HAS_FOREST_COMPONENT edges from source records to field directive and overlay nodes",
            region1_requirement_edge_gaps,
        ),
        _check(
            "nepa_3d_graph_region1_blocked_profiles_have_blockers",
            not blocked_profile_ids_without_blockers,
            "readiness blockers for each non-promoted profile",
            blocked_profile_ids_without_blockers,
        ),
        _check(
            "nepa_3d_graph_has_readiness_blocker_nodes",
            any(node_id.startswith("readiness_blocker:") for node_id in node_ids),
            "readiness blocker nodes present",
            sorted(node_id for node_id in node_ids if node_id.startswith("readiness_blocker:")),
        ),
    ]


def _canonical_source_register_graph_checks(
    *,
    graph: dict[str, Any],
    catalog_rows: list[dict[str, Any]],
    edge_tuples: set[tuple[str, str, str]],
) -> list[dict[str, Any]]:
    nodes = _dict_list(graph.get("nodes"))
    node_type_counts = Counter(str(node.get("node_type") or "") for node in nodes)
    authority_document_ids = {
        str(_dict(row.get("metadata")).get("authority_document_id") or "")
        for row in catalog_rows
        if str(_dict(row.get("metadata")).get("authority_document_id") or "").strip()
    }
    authority_section_ids = {
        str(_dict(row.get("metadata")).get("authority_section_id") or "")
        for row in catalog_rows
        if str(_dict(row.get("metadata")).get("authority_section_id") or "").strip()
    }
    jurisdiction_scope_ids = {
        str(_dict(row.get("metadata")).get("jurisdiction_scope_id") or "")
        for row in catalog_rows
        if str(_dict(row.get("metadata")).get("jurisdiction_scope_id") or "").strip()
    }
    exported_authority_document_ids = {
        str(node.get("provenance", {}).get("authority_document_id") or "")
        for node in nodes
        if str(node.get("node_type") or "") == "authority_document"
    }
    exported_authority_section_ids = {
        str(node.get("provenance", {}).get("authority_section_id") or "")
        for node in nodes
        if str(node.get("node_type") or "") == "authority_section"
    }
    exported_jurisdiction_scope_ids = {
        str(node.get("provenance", {}).get("jurisdiction_scope_id") or "")
        for node in nodes
        if str(node.get("node_type") or "") == "jurisdiction_scope"
    }
    authority_path_ids = {
        str(node.get("node_id") or "")
        for node in nodes
        if str(node.get("node_type") or "") == "authority_path"
    }
    justification_path_ids = {
        str(node.get("node_id") or "")
        for node in nodes
        if str(node.get("node_type") or "") == "justification_path"
    }
    authority_path_source_gaps = sorted(
        path_id
        for path_id in authority_path_ids
        if not any(
            edge_type == "HAS_AUTHORITY_PATH" and target_node_id == path_id
            for edge_type, _, target_node_id in edge_tuples
        )
    )
    authority_path_target_gaps = sorted(
        path_id
        for path_id in authority_path_ids
        if not any(
            edge_type == "PATH_TARGETS" and source_node_id == path_id
            for edge_type, source_node_id, _ in edge_tuples
        )
    )
    justification_edge_gaps = sorted(
        path_id
        for path_id in authority_path_ids
        if (
            "JUSTIFIED_BY",
            path_id,
            f"justification_path:{path_id.removeprefix('authority_path:')}",
        )
        not in edge_tuples
    )
    supporting_source_gaps = sorted(
        justification_id
        for justification_id in justification_path_ids
        if not any(
            edge_type == "SUPPORTS_JUSTIFICATION_PATH" and target_node_id == justification_id
            for edge_type, _, target_node_id in edge_tuples
        )
    )
    forest_unit_present = node_type_counts.get("forest_unit", 0) > 0

    return [
        _check(
            "nepa_3d_graph_exports_authority_documents",
            authority_document_ids <= exported_authority_document_ids,
            sorted(authority_document_ids),
            sorted(authority_document_ids - exported_authority_document_ids),
        ),
        _check(
            "nepa_3d_graph_exports_authority_sections",
            authority_section_ids <= exported_authority_section_ids,
            sorted(authority_section_ids),
            sorted(authority_section_ids - exported_authority_section_ids),
        ),
        _check(
            "nepa_3d_graph_exports_jurisdiction_scopes",
            jurisdiction_scope_ids <= exported_jurisdiction_scope_ids,
            sorted(jurisdiction_scope_ids),
            sorted(jurisdiction_scope_ids - exported_jurisdiction_scope_ids),
        ),
        _check(
            "nepa_3d_graph_exports_semantic_authority_paths",
            bool(authority_path_ids),
            "at least one authority_path node",
            len(authority_path_ids),
        ),
        _check(
            "nepa_3d_graph_exports_semantic_justification_paths",
            authority_path_ids
            == {
                f"authority_path:{justification_id.removeprefix('justification_path:')}"
                for justification_id in justification_path_ids
            },
            sorted(authority_path_ids),
            sorted(justification_path_ids),
        ),
        _check(
            "nepa_3d_graph_links_authority_paths_to_sources_and_targets",
            not authority_path_source_gaps and not authority_path_target_gaps,
            [],
            {
                "missing_source_edge_authority_paths": authority_path_source_gaps,
                "missing_target_edge_authority_paths": authority_path_target_gaps,
            },
        ),
        _check(
            "nepa_3d_graph_links_authority_paths_to_justification_paths",
            not justification_edge_gaps,
            [],
            justification_edge_gaps,
        ),
        _check(
            "nepa_3d_graph_justification_paths_are_supported_by_source_records",
            not supporting_source_gaps,
            [],
            supporting_source_gaps,
        ),
        _check(
            "nepa_3d_graph_exports_forest_units_from_semantic_relationships",
            forest_unit_present,
            True,
            forest_unit_present,
        ),
    ]
