from __future__ import annotations

from typing import Any

from .nepa_knowledge_graph_export_models import _GraphBuilder
from .nepa_knowledge_graph_export_models import _dict
from .nepa_knowledge_graph_export_models import _dict_list
from .nepa_knowledge_graph_export_models import _first
from .nepa_knowledge_graph_export_models import _forest_unit_node_id
from .nepa_knowledge_graph_export_models import _source_node_id
from .nepa_knowledge_graph_export_region1 import _region1_component_node_id
from .nepa_knowledge_graph_export_region1 import _region1_field_directive_component_id
from .nepa_knowledge_graph_export_region1 import _region1_overlay_component_id
from .nepa_knowledge_graph_export_region1 import _region1_profile_display
from .nepa_knowledge_graph_export_region1 import _region1_profile_readiness_blockers
from .nepa_knowledge_graph_export_region1 import _region1_profile_readiness_by_unit
from .nepa_knowledge_graph_export_region1 import _region1_profile_readiness_rows
from .nepa_knowledge_graph_export_region1 import _region1_requirement_blockers
from .nepa_knowledge_graph_export_region1 import _region1_requirement_source_record_ids
from .nepa_knowledge_graph_export_review_overlay import _add_blocker


def _add_forest_plan_nodes(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    forest_plan_profiles: dict[str, Any],
    region1_forest_plan_readiness: dict[str, Any],
    forest_components: dict[str, Any],
) -> None:
    plan_node_by_unit: dict[str, str] = {}
    readiness_by_unit = _region1_profile_readiness_by_unit(region1_forest_plan_readiness)
    rendered_profile_units: set[str] = set()
    for profile in sorted(
        forest_plan_profiles.get("profiles", []),
        key=lambda item: str(item.get("forest_unit_id") or ""),
    ):
        forest_unit_id = str(profile.get("forest_unit_id") or "")
        if not forest_unit_id:
            continue
        rendered_profile_units.add(forest_unit_id)
        readiness = readiness_by_unit.get(forest_unit_id, {})
        display = _region1_profile_display(readiness)
        blockers = _region1_profile_readiness_blockers(readiness)
        unit_node_id = _forest_unit_node_id(forest_unit_id)
        builder.add_node(
            node_id=unit_node_id,
            node_type="forest_unit",
            label=str(_first(profile.get("forest_unit_names")) or forest_unit_id),
            display_status=display["display_status"],
            review_readiness_status=display["review_readiness_status"],
            provenance={"source_set_id": source_set_id, "forest_code": forest_unit_id},
            readiness_blockers=blockers,
            metadata={
                "forest_unit_names": profile.get("forest_unit_names", []),
                "required_readiness_source_roles": profile.get("required_readiness_source_roles", []),
                "profile_kind": readiness.get("profile_kind"),
                "graph_promotion_status": readiness.get("graph_promotion_status"),
                "source_requirements": readiness.get("source_requirements", []),
                "component_inventory_validation": readiness.get("component_inventory_validation", {}),
                "applicability_eval_coverage": readiness.get("applicability_eval_coverage", {}),
            },
        )
        if blockers:
            _add_blocker(
                builder,
                source_set_id=source_set_id,
                subject_node_id=unit_node_id,
                blockers=blockers,
            )
        plan_source_record_id = str(profile.get("active_plan_source_record_id") or "")
        if plan_source_record_id:
            plan_node_id = f"forest_plan:{forest_unit_id}:{plan_source_record_id}"
            plan_node_by_unit[forest_unit_id] = plan_node_id
            builder.add_node(
                node_id=plan_node_id,
                node_type="forest_plan",
                label=f"{forest_unit_id} active forest plan",
                display_status=display["display_status"],
                review_readiness_status=display["review_readiness_status"],
                provenance={
                    "source_set_id": source_set_id,
                    "forest_code": forest_unit_id,
                    "source_record_id": plan_source_record_id,
                },
                readiness_blockers=blockers,
                metadata={
                    "supporting_source_record_ids_by_role": profile.get(
                        "supporting_source_record_ids_by_role", {}
                    ),
                    "component_inventory_validation": readiness.get(
                        "component_inventory_validation", {}
                    ),
                },
            )
            if blockers:
                _add_blocker(
                    builder,
                    source_set_id=source_set_id,
                    subject_node_id=plan_node_id,
                    blockers=blockers,
                )
            builder.add_edge(
                edge_type="HAS_FOREST_PLAN",
                source_node_id=unit_node_id,
                target_node_id=plan_node_id,
                display_status=display["display_status"],
                review_readiness_status=display["review_readiness_status"],
                provenance={
                    "source_set_id": source_set_id,
                    "forest_code": forest_unit_id,
                    "source_record_id": plan_source_record_id,
                },
                readiness_blockers=blockers,
            )
            active_plan_source_node_id = _source_node_id(plan_source_record_id)
            if active_plan_source_node_id in builder.nodes:
                builder.add_edge(
                    edge_type="HAS_SOURCE_RECORD",
                    source_node_id=plan_node_id,
                    target_node_id=active_plan_source_node_id,
                    display_status=display["display_status"],
                    review_readiness_status=display["review_readiness_status"],
                    provenance={
                        "source_set_id": source_set_id,
                        "forest_code": forest_unit_id,
                        "source_record_id": plan_source_record_id,
                        "source_role": "active_plan",
                    },
                    readiness_blockers=blockers,
                )
            for role, role_record in sorted(
                _dict(profile.get("supporting_source_record_ids_by_role")).items()
            ):
                supporting_source_record_id = str(_dict(role_record).get("source_record_id") or "")
                if not supporting_source_record_id:
                    continue
                supporting_source_node_id = _source_node_id(supporting_source_record_id)
                if supporting_source_node_id not in builder.nodes:
                    continue
                builder.add_edge(
                    edge_type="HAS_SOURCE_RECORD",
                    source_node_id=plan_node_id,
                    target_node_id=supporting_source_node_id,
                    display_status=display["display_status"],
                    review_readiness_status=display["review_readiness_status"],
                    provenance={
                        "source_set_id": source_set_id,
                        "forest_code": forest_unit_id,
                        "source_record_id": supporting_source_record_id,
                        "source_role": role,
                    },
                    readiness_blockers=blockers,
                )
        _add_profile_term_nodes(
            builder,
            source_set_id=source_set_id,
            forest_unit_id=forest_unit_id,
            plan_node_id=plan_node_by_unit.get(forest_unit_id),
            profile=profile,
            display=display,
            blockers=blockers,
        )

    for readiness in _region1_profile_readiness_rows(region1_forest_plan_readiness):
        forest_unit_id = str(readiness.get("forest_unit_id") or "")
        if not forest_unit_id or forest_unit_id in rendered_profile_units:
            continue
        display = _region1_profile_display(readiness)
        blockers = _region1_profile_readiness_blockers(readiness)
        unit_node_id = _forest_unit_node_id(forest_unit_id)
        builder.add_node(
            node_id=unit_node_id,
            node_type="forest_unit",
            label=str(_first(readiness.get("forest_unit_names")) or forest_unit_id),
            display_status=display["display_status"],
            review_readiness_status=display["review_readiness_status"],
            provenance={"source_set_id": source_set_id, "forest_code": forest_unit_id},
            readiness_blockers=blockers,
            metadata={
                "forest_unit_names": readiness.get("forest_unit_names", []),
                "profile_kind": readiness.get("profile_kind"),
                "graph_promotion_status": readiness.get("graph_promotion_status"),
                "source_requirements": readiness.get("source_requirements", []),
                "component_inventory_validation": readiness.get("component_inventory_validation", {}),
                "applicability_eval_coverage": readiness.get("applicability_eval_coverage", {}),
            },
        )
        if blockers:
            _add_blocker(
                builder,
                source_set_id=source_set_id,
                subject_node_id=unit_node_id,
                blockers=blockers,
            )
        plan_source_record_id = str(readiness.get("active_plan_source_record_id") or "")
        if plan_source_record_id:
            plan_node_id = f"forest_plan:{forest_unit_id}:{plan_source_record_id}"
            plan_node_by_unit[forest_unit_id] = plan_node_id
            builder.add_node(
                node_id=plan_node_id,
                node_type="forest_plan",
                label=f"{forest_unit_id} tracked forest plan",
                display_status=display["display_status"],
                review_readiness_status=display["review_readiness_status"],
                provenance={
                    "source_set_id": source_set_id,
                    "forest_code": forest_unit_id,
                    "source_record_id": plan_source_record_id,
                },
                readiness_blockers=blockers,
                metadata={
                    "source_requirements": readiness.get("source_requirements", []),
                    "component_inventory_validation": readiness.get(
                        "component_inventory_validation", {}
                    ),
                },
            )
            if blockers:
                _add_blocker(
                    builder,
                    source_set_id=source_set_id,
                    subject_node_id=plan_node_id,
                    blockers=blockers,
                )
            builder.add_edge(
                edge_type="HAS_FOREST_PLAN",
                source_node_id=unit_node_id,
                target_node_id=plan_node_id,
                display_status=display["display_status"],
                review_readiness_status=display["review_readiness_status"],
                provenance={
                    "source_set_id": source_set_id,
                    "forest_code": forest_unit_id,
                    "source_record_id": plan_source_record_id,
                },
                readiness_blockers=blockers,
            )
            for requirement in _dict_list(readiness.get("source_requirements")):
                source_record_id = str(requirement.get("source_record_id") or "")
                if not source_record_id:
                    continue
                source_node_id = _source_node_id(source_record_id)
                if source_node_id not in builder.nodes:
                    continue
                builder.add_edge(
                    edge_type="HAS_SOURCE_RECORD",
                    source_node_id=plan_node_id,
                    target_node_id=source_node_id,
                    display_status=display["display_status"],
                    review_readiness_status=display["review_readiness_status"],
                    provenance={
                        "source_set_id": source_set_id,
                        "forest_code": forest_unit_id,
                        "source_record_id": source_record_id,
                        "source_role": requirement.get("role"),
                    },
                    readiness_blockers=blockers,
                )

    _add_region1_requirement_nodes(
        builder,
        source_set_id=source_set_id,
        region1_forest_plan_readiness=region1_forest_plan_readiness,
    )

    for component in sorted(
        forest_components.get("components", []),
        key=lambda item: str(item.get("component_id") or ""),
    ):
        component_id = str(component.get("component_id") or "")
        forest_unit_id = str(component.get("forest_unit_id") or "")
        if not component_id or not forest_unit_id:
            continue
        component_node_id = f"forest_plan_component:{component_id}"
        source_record_id = str(component.get("source_record_id") or "")
        builder.add_node(
            node_id=component_node_id,
            node_type="forest_plan_component",
            label=component_id,
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "component_id": component_id,
                "forest_code": forest_unit_id,
                "source_record_id": source_record_id,
                "artifact_sha256": component.get("artifact_sha256"),
                "content_sha256": component.get("content_sha256"),
            },
            metadata={
                "component_type": component.get("component_type"),
                "plan_version": component.get("plan_version"),
                "section_id": component.get("section_id"),
                "source_chunk_ids": component.get("source_chunk_ids", []),
                "text_excerpt": str(component.get("component_text") or "")[:240],
            },
        )
        plan_node_id = plan_node_by_unit.get(forest_unit_id)
        if plan_node_id:
            builder.add_edge(
                edge_type="HAS_FOREST_COMPONENT",
                source_node_id=plan_node_id,
                target_node_id=component_node_id,
                display_status="active",
                review_readiness_status="not_review_specific",
                provenance={
                    "source_set_id": source_set_id,
                    "forest_code": forest_unit_id,
                    "component_id": component_id,
                },
            )
        builder.add_edge(
            edge_type="BELONGS_TO_FOREST_UNIT",
            source_node_id=component_node_id,
            target_node_id=_forest_unit_node_id(forest_unit_id),
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "forest_code": forest_unit_id,
                "component_id": component_id,
            },
        )
        if source_record_id:
            builder.add_edge(
                edge_type="HAS_FOREST_COMPONENT",
                source_node_id=_source_node_id(source_record_id),
                target_node_id=component_node_id,
                display_status="active",
                review_readiness_status="not_review_specific",
                provenance={
                    "source_set_id": source_set_id,
                    "source_record_id": source_record_id,
                    "component_id": component_id,
                },
            )


def _add_source_register_region1_semantic_paths(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    region1_forest_plan_readiness: dict[str, Any],
) -> None:
    for readiness in _region1_profile_readiness_rows(region1_forest_plan_readiness):
        forest_unit_id = str(readiness.get("forest_unit_id") or "")
        plan_source_record_id = str(readiness.get("active_plan_source_record_id") or "")
        if not forest_unit_id or not plan_source_record_id:
            continue
        forest_unit_node_id = _forest_unit_node_id(forest_unit_id)
        forest_plan_node_id = f"forest_plan:{forest_unit_id}:{plan_source_record_id}"
        if forest_plan_node_id not in builder.nodes:
            forest_plan_node_id = _existing_forest_plan_node_id(builder, forest_unit_id)
        if forest_unit_node_id not in builder.nodes or forest_plan_node_id is None:
            continue
        display = _region1_profile_display(readiness)
        blockers = _region1_profile_readiness_blockers(readiness)
        relationship_id = f"region1-readiness-{forest_unit_id}-governs-forest-unit"
        support_ids = [
            str(requirement.get("source_record_id") or "")
            for requirement in _dict_list(readiness.get("source_requirements"))
            if str(requirement.get("source_record_id") or "").strip()
        ]
        if not support_ids:
            continue
        authority_path_node_id = f"authority_path:{relationship_id}"
        justification_path_node_id = f"justification_path:{relationship_id}"
        relationship_basis = (
            "Region 1 readiness binds the active forest plan source to the tracked forest unit."
        )
        builder.add_node(
            node_id=authority_path_node_id,
            node_type="authority_path",
            label="Governs Forest Unit",
            display_status=display["display_status"],
            review_readiness_status=display["review_readiness_status"],
            provenance={
                "source_set_id": source_set_id,
                "authority_path_id": relationship_id,
                "relationship_id": relationship_id,
            },
            readiness_blockers=blockers,
            metadata={
                "relationship_type": "GOVERNS_FOREST_UNIT",
                "path_pattern_id": "scope-and-unit-binding",
                "source_class_id": "forest_plan",
                "source_id": forest_plan_node_id,
                "target_class_id": "forest_unit",
                "target_id": forest_unit_node_id,
                "relationship_basis": relationship_basis,
                "evidence_basis_type": "region1_readiness",
                "status": readiness.get("graph_promotion_status") or "readiness_tracked",
                "confidence": "readiness_governed",
            },
        )
        builder.add_edge(
            edge_type="HAS_AUTHORITY_PATH",
            source_node_id=forest_plan_node_id,
            target_node_id=authority_path_node_id,
            display_status=display["display_status"],
            review_readiness_status=display["review_readiness_status"],
            provenance={
                "source_set_id": source_set_id,
                "relationship_id": relationship_id,
                "relationship_type": "GOVERNS_FOREST_UNIT",
            },
            readiness_blockers=blockers,
        )
        builder.add_edge(
            edge_type="PATH_TARGETS",
            source_node_id=authority_path_node_id,
            target_node_id=forest_unit_node_id,
            display_status=display["display_status"],
            review_readiness_status=display["review_readiness_status"],
            provenance={
                "source_set_id": source_set_id,
                "relationship_id": relationship_id,
                "relationship_type": "GOVERNS_FOREST_UNIT",
            },
            readiness_blockers=blockers,
        )
        builder.add_node(
            node_id=justification_path_node_id,
            node_type="justification_path",
            label=f"Justification for {forest_unit_id} plan binding",
            display_status=display["display_status"],
            review_readiness_status=display["review_readiness_status"],
            provenance={
                "source_set_id": source_set_id,
                "justification_path_id": relationship_id,
                "relationship_id": relationship_id,
            },
            readiness_blockers=blockers,
            metadata={
                "supporting_source_record_ids": support_ids,
                "relationship_basis": relationship_basis,
                "evidence_basis_type": "region1_readiness",
                "confidence": "readiness_governed",
            },
        )
        builder.add_edge(
            edge_type="JUSTIFIED_BY",
            source_node_id=authority_path_node_id,
            target_node_id=justification_path_node_id,
            display_status=display["display_status"],
            review_readiness_status=display["review_readiness_status"],
            provenance={
                "source_set_id": source_set_id,
                "relationship_id": relationship_id,
            },
            readiness_blockers=blockers,
        )
        for supporting_source_record_id in support_ids:
            supporting_source_node_id = _source_node_id(supporting_source_record_id)
            if supporting_source_node_id not in builder.nodes:
                continue
            builder.add_edge(
                edge_type="SUPPORTS_JUSTIFICATION_PATH",
                source_node_id=supporting_source_node_id,
                target_node_id=justification_path_node_id,
                display_status=display["display_status"],
                review_readiness_status=display["review_readiness_status"],
                provenance={
                    "source_set_id": source_set_id,
                    "relationship_id": relationship_id,
                    "source_record_id": supporting_source_record_id,
                },
                readiness_blockers=blockers,
            )


def _existing_forest_plan_node_id(
    builder: _GraphBuilder,
    forest_unit_id: str,
) -> str | None:
    matches = [
        node_id
        for node_id, node in builder.nodes.items()
        if str(node.get("node_type") or "") == "forest_plan"
        and str(_dict(node.get("provenance")).get("forest_code") or "") == forest_unit_id
    ]
    return sorted(matches)[0] if matches else None


def _add_region1_requirement_nodes(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    region1_forest_plan_readiness: dict[str, Any],
) -> None:
    for requirement in _dict_list(region1_forest_plan_readiness.get("field_directive_requirements")):
        requirement_id = str(requirement.get("requirement_id") or "")
        if not requirement_id:
            continue
        source_record_ids = _region1_requirement_source_record_ids(requirement)
        blockers = _region1_requirement_blockers(requirement, source_record_ids)
        component_id = _region1_field_directive_component_id(requirement)
        component_node_id = _region1_component_node_id(component_id)
        builder.add_node(
            node_id=component_node_id,
            node_type="forest_plan_component",
            label=f"Region 1 field directive: {requirement_id}",
            display_status="readiness_blocked" if blockers else "active",
            review_readiness_status="blocked" if blockers else "not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "component_id": component_id,
                "forest_code": "region1",
                "requirement_id": requirement_id,
                "source_record_ids": source_record_ids,
            },
            readiness_blockers=blockers,
            metadata={
                "component_type": "field_directive_requirement",
                "term_source": "region1_forest_plan_readiness",
                "requirement_type": requirement.get("requirement_type"),
                "readiness_status": requirement.get("readiness_status"),
            },
        )
        if blockers:
            _add_blocker(
                builder,
                source_set_id=source_set_id,
                subject_node_id=component_node_id,
                blockers=blockers,
            )
        _add_region1_requirement_source_edges(
            builder,
            source_set_id=source_set_id,
            component_node_id=component_node_id,
            source_record_ids=source_record_ids,
            requirement_kind="field_directive_requirement",
            requirement_id=requirement_id,
            display_status="readiness_blocked" if blockers else "active",
            review_readiness_status="blocked" if blockers else "not_review_specific",
            blockers=blockers,
        )
        _add_region1_requirement_forest_unit_edges(
            builder,
            source_set_id=source_set_id,
            component_node_id=component_node_id,
            region1_forest_plan_readiness=region1_forest_plan_readiness,
            requirement_kind="field_directive_requirement",
            requirement_id=requirement_id,
            display_status="readiness_blocked" if blockers else "active",
            review_readiness_status="blocked" if blockers else "not_review_specific",
            blockers=blockers,
        )

    for requirement in _dict_list(region1_forest_plan_readiness.get("overlay_requirements")):
        overlay_id = str(requirement.get("overlay_id") or "")
        if not overlay_id:
            continue
        source_record_ids = _region1_requirement_source_record_ids(requirement)
        blockers = _region1_requirement_blockers(requirement, source_record_ids)
        component_id = _region1_overlay_component_id(requirement)
        component_node_id = _region1_component_node_id(component_id)
        builder.add_node(
            node_id=component_node_id,
            node_type="forest_plan_component",
            label=f"Region 1 overlay: {overlay_id}",
            display_status="readiness_blocked" if blockers else "active",
            review_readiness_status="blocked" if blockers else "not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "component_id": component_id,
                "forest_code": "region1",
                "overlay_id": overlay_id,
                "source_record_ids": source_record_ids,
            },
            readiness_blockers=blockers,
            metadata={
                "component_type": "overlay",
                "term_source": "region1_forest_plan_readiness",
                "readiness_status": requirement.get("readiness_status"),
            },
        )
        if blockers:
            _add_blocker(
                builder,
                source_set_id=source_set_id,
                subject_node_id=component_node_id,
                blockers=blockers,
            )
        _add_region1_requirement_source_edges(
            builder,
            source_set_id=source_set_id,
            component_node_id=component_node_id,
            source_record_ids=source_record_ids,
            requirement_kind="overlay_requirement",
            requirement_id=overlay_id,
            display_status="readiness_blocked" if blockers else "active",
            review_readiness_status="blocked" if blockers else "not_review_specific",
            blockers=blockers,
        )
        _add_region1_requirement_forest_unit_edges(
            builder,
            source_set_id=source_set_id,
            component_node_id=component_node_id,
            region1_forest_plan_readiness=region1_forest_plan_readiness,
            requirement_kind="overlay_requirement",
            requirement_id=overlay_id,
            display_status="readiness_blocked" if blockers else "active",
            review_readiness_status="blocked" if blockers else "not_review_specific",
            blockers=blockers,
        )


def _add_region1_requirement_source_edges(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    component_node_id: str,
    source_record_ids: list[str],
    requirement_kind: str,
    requirement_id: str,
    display_status: str,
    review_readiness_status: str,
    blockers: list[str],
) -> None:
    for source_record_id in source_record_ids:
        source_node_id = _source_node_id(source_record_id)
        if source_node_id not in builder.nodes:
            continue
        builder.add_edge(
            edge_type="HAS_FOREST_COMPONENT",
            source_node_id=source_node_id,
            target_node_id=component_node_id,
            display_status=display_status,
            review_readiness_status=review_readiness_status,
            provenance={
                "source_set_id": source_set_id,
                "source_record_id": source_record_id,
                "requirement_kind": requirement_kind,
                "requirement_id": requirement_id,
            },
            readiness_blockers=blockers,
        )


def _add_region1_requirement_forest_unit_edges(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    component_node_id: str,
    region1_forest_plan_readiness: dict[str, Any],
    requirement_kind: str,
    requirement_id: str,
    display_status: str,
    review_readiness_status: str,
    blockers: list[str],
) -> None:
    for readiness in _region1_profile_readiness_rows(region1_forest_plan_readiness):
        forest_unit_id = str(readiness.get("forest_unit_id") or "")
        if not forest_unit_id:
            continue
        forest_unit_node_id = _forest_unit_node_id(forest_unit_id)
        if forest_unit_node_id not in builder.nodes:
            continue
        builder.add_edge(
            edge_type="BELONGS_TO_FOREST_UNIT",
            source_node_id=component_node_id,
            target_node_id=forest_unit_node_id,
            display_status=display_status,
            review_readiness_status=review_readiness_status,
            provenance={
                "source_set_id": source_set_id,
                "forest_code": forest_unit_id,
                "requirement_kind": requirement_kind,
                "requirement_id": requirement_id,
            },
            readiness_blockers=blockers,
        )


def _add_profile_term_nodes(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    forest_unit_id: str,
    plan_node_id: str | None,
    profile: dict[str, Any],
    display: dict[str, str],
    blockers: list[str],
) -> None:
    term_fields = (
        ("geographic_area_terms", "geographic_area"),
        ("management_area_terms", "management_area"),
        ("overlay_terms", "overlay"),
    )
    active_plan_source_record_id = str(profile.get("active_plan_source_record_id") or "")
    for field, term_kind in term_fields:
        for term in _dict_list(profile.get(field)):
            entry_id = str(term.get("entry_id") or "")
            if not entry_id:
                continue
            component_id = f"profile-term:{forest_unit_id}:{term_kind}:{entry_id}"
            component_node_id = f"forest_plan_component:{component_id}"
            source_record_id = str(term.get("source_record_id") or active_plan_source_record_id)
            builder.add_node(
                node_id=component_node_id,
                node_type="forest_plan_component",
                label=str(term.get("name") or entry_id),
                display_status=display["display_status"],
                review_readiness_status=display["review_readiness_status"],
                provenance={
                    "source_set_id": source_set_id,
                    "component_id": component_id,
                    "forest_code": forest_unit_id,
                    "source_record_id": source_record_id,
                },
                readiness_blockers=blockers,
                metadata={
                    "component_type": term_kind,
                    "profile_term_field": field,
                    "entry_id": entry_id,
                    "aliases": term.get("aliases", []),
                    "term_source": "forest_plan_profile",
                },
            )
            if blockers:
                _add_blocker(
                    builder,
                    source_set_id=source_set_id,
                    subject_node_id=component_node_id,
                    blockers=blockers,
                )
            if plan_node_id:
                builder.add_edge(
                    edge_type="HAS_FOREST_COMPONENT",
                    source_node_id=plan_node_id,
                    target_node_id=component_node_id,
                    display_status=display["display_status"],
                    review_readiness_status=display["review_readiness_status"],
                    provenance={
                        "source_set_id": source_set_id,
                        "forest_code": forest_unit_id,
                        "component_id": component_id,
                    },
                    readiness_blockers=blockers,
                )
            builder.add_edge(
                edge_type="BELONGS_TO_FOREST_UNIT",
                source_node_id=component_node_id,
                target_node_id=_forest_unit_node_id(forest_unit_id),
                display_status=display["display_status"],
                review_readiness_status=display["review_readiness_status"],
                provenance={
                    "source_set_id": source_set_id,
                    "forest_code": forest_unit_id,
                    "component_id": component_id,
                },
                readiness_blockers=blockers,
            )


def _add_source_set_blockers(
    builder: _GraphBuilder,
    *,
    source_set_node_id: str,
    source_set_id: str,
) -> None:
    _add_blocker(
        builder,
        source_set_id=source_set_id,
        subject_node_id=source_set_node_id,
        blockers=["fsh_chapter_delta_required"],
    )
