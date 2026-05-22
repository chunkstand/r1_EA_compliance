from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
from typing import Any
from typing import Iterable

from .nepa_knowledge_graph_export_models import _dict
from .nepa_knowledge_graph_export_models import _read_json
from .nepa_knowledge_graph_export_models import _strings
from .nepa_knowledge_graph_export_region1 import _region1_readiness_summary
from .source_register_proving import resolve_latest_proving_context


def _source_display_status(
    *,
    row: dict[str, Any],
    currentness: dict[str, Any],
    partition: dict[str, Any],
) -> dict[str, str]:
    source_partition = partition.get("source_partition") or currentness.get("source_partition")
    source_status = row.get("source_status") or currentness.get("source_status")
    supersession_status = currentness.get("supersession_status")
    if source_status == "skipped_excluded":
        return {"display_status": "out_of_scope", "review_readiness_status": "blocked"}
    if source_partition == "candidate_blocked_source":
        return {"display_status": "candidate", "review_readiness_status": "blocked"}
    if source_partition == "currentness_supersession_archive":
        display_status = "reserved" if "reserved" in str(row.get("title") or "").lower() else "superseded"
        return {
            "display_status": display_status,
            "review_readiness_status": "source_currentness_only",
        }
    if supersession_status in {"superseded_replacement_source", "superseded_source_record"}:
        return {"display_status": "superseded", "review_readiness_status": "source_currentness_only"}
    return {"display_status": "active", "review_readiness_status": "reviewer_ready"}


def _source_readiness_blockers(
    *,
    row: dict[str, Any],
    currentness: dict[str, Any],
    partition: dict[str, Any],
) -> list[str]:
    source_partition = partition.get("source_partition") or currentness.get("source_partition")
    source_status = row.get("source_status") or currentness.get("source_status")
    supersession_status = currentness.get("supersession_status")
    if source_status == "skipped_excluded":
        return ["missing_source"]
    if source_partition == "candidate_blocked_source":
        return ["missing_source"]
    if source_partition == "currentness_supersession_archive" or supersession_status in {
        "superseded_replacement_source",
        "superseded_source_record",
    }:
        return ["superseded_source"]
    return []


def _family_display_status(family: dict[str, Any], currentness: dict[str, Any]) -> dict[str, str]:
    status = str(family.get("status") or currentness.get("family_status") or "")
    currentness_status = str(currentness.get("currentness_status") or "")
    if status == "candidate":
        return {"display_status": "candidate", "review_readiness_status": "blocked"}
    if status == "superseded":
        return {"display_status": "superseded", "review_readiness_status": "source_currentness_only"}
    if status == "out_of_scope":
        return {"display_status": "reserved", "review_readiness_status": "source_currentness_only"}
    if currentness_status in {"missing_source_addition_decision", "source_currentness_failed"}:
        return {"display_status": "readiness_blocked", "review_readiness_status": "blocked"}
    return {"display_status": "active", "review_readiness_status": "reviewer_ready"}


def _family_readiness_blockers(family: dict[str, Any], currentness: dict[str, Any]) -> list[str]:
    status = str(family.get("status") or currentness.get("family_status") or "")
    if status == "candidate":
        return ["missing_source"]
    if status == "superseded":
        return ["superseded_source"]
    if status == "out_of_scope":
        return ["superseded_source"]
    if currentness.get("failed_source_record_count"):
        return ["missing_source"]
    return []


def _currentness_metadata(
    *,
    currentness: dict[str, Any],
    partition: dict[str, Any],
) -> dict[str, Any]:
    return {
        "source_partition": partition.get("source_partition") or currentness.get("source_partition"),
        "source_partition_basis": partition.get("source_partition_basis")
        or currentness.get("source_partition_basis"),
        "supersession_status": currentness.get("supersession_status"),
        "currentness_status": currentness.get("currentness_status"),
        "counts_as_current_authority": currentness.get("counts_as_current_authority"),
        "capture_date": currentness.get("capture_date"),
        "effective_date": currentness.get("effective_date"),
    }


def _source_set_readiness_blockers(currentness: dict[str, Any]) -> list[str]:
    contract = _dict(currentness.get("source_partition_contract"))
    delta_plan = _dict(contract.get("workbook_source_delta_plan"))
    return ["fsh_chapter_delta_required"] if delta_plan.get("fsh_1909_15") else []


def _source_currentness_by_id(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        source_record_id = str(record.get("source_record_id") or "")
        if not source_record_id:
            continue
        existing = by_id.get(source_record_id)
        if existing is None or record.get("counts_as_current_authority"):
            by_id[source_record_id] = record
    return by_id


def _node_metadata_counts(
    nodes: list[dict[str, Any]],
    key: str,
    *,
    node_type: str | None = None,
) -> dict[str, int]:
    return _sorted_counts(
        _dict(node.get("metadata")).get(key)
        for node in nodes
        if node_type is None or node.get("node_type") == node_type
    )


def _node_currentness_counts(
    nodes: list[dict[str, Any]],
    key: str,
    *,
    node_type: str | None = None,
) -> dict[str, int]:
    return _sorted_counts(
        _dict(node.get("currentness_metadata")).get(key)
        for node in nodes
        if node_type is None or node.get("node_type") == node_type
    )


def _sorted_counts(values: Iterable[Any]) -> dict[str, int]:
    return dict(
        sorted(
            Counter(
                str(value)
                for value in values
                if value is not None and not isinstance(value, (list, dict, tuple, set))
            ).items()
        )
    )


def _missing_summary_count_fields(graph: dict[str, Any]) -> list[str]:
    summary = _dict(graph.get("summary"))
    required_fields = [
        "node_type_counts",
        "edge_type_counts",
        "authority_category_counts",
        "source_status_counts",
        "source_partition_counts",
        "applicability_status_counts",
        "readiness_blocker_counts",
    ]
    return [
        field
        for field in required_fields
        if not isinstance(summary.get(field), dict)
    ]


def _summary(
    *,
    source_set_id: str,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    catalog_rows: list[dict[str, Any]],
    inventory: dict[str, Any],
    rule_pack: dict[str, Any],
    template_config: dict[str, Any],
    rule_claim_links: list[dict[str, Any]],
    forest_components: dict[str, Any],
    forest_plan_profiles: dict[str, Any],
    region1_forest_plan_readiness: dict[str, Any],
    currentness: dict[str, Any],
    inputs: list[dict[str, Any]],
    catalog_graph_node_count: int,
    catalog_graph_edge_count: int,
) -> dict[str, Any]:
    return {
        "schema_version": "nepa-3d-knowledge-graph-summary-v1",
        "source_set_id": source_set_id,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "node_type_counts": dict(Counter(str(node.get("node_type")) for node in nodes)),
        "edge_type_counts": dict(Counter(str(edge.get("edge_type")) for edge in edges)),
        "display_status_counts": dict(
            Counter(str(record.get("display_status")) for record in nodes + edges)
        ),
        "review_readiness_status_counts": dict(
            Counter(str(record.get("review_readiness_status")) for record in nodes + edges)
        ),
        "authority_category_counts": _node_metadata_counts(nodes, "authority_category"),
        "source_status_counts": _node_metadata_counts(
            nodes,
            "source_status",
            node_type="source_record",
        ),
        "source_partition_counts": _node_currentness_counts(
            nodes,
            "source_partition",
            node_type="source_record",
        ),
        "source_currentness_status_counts": _node_currentness_counts(
            nodes,
            "currentness_status",
            node_type="source_record",
        ),
        "applicability_status_counts": _node_metadata_counts(nodes, "applicability_status"),
        "readiness_blocker_counts": dict(
            Counter(
                blocker
                for record in nodes + edges
                for blocker in _strings(record.get("readiness_blockers"))
            )
        ),
        "catalog_source_record_count": len(catalog_rows),
        "catalog_graph_node_count": catalog_graph_node_count,
        "catalog_graph_edge_count": catalog_graph_edge_count,
        "authority_family_count": len(inventory.get("authority_families", [])),
        "base_rule_count": len(rule_pack.get("rules", [])),
        "authority_family_rule_template_count": len(template_config.get("templates", [])),
        "rule_claim_link_count": len(rule_claim_links),
        "forest_plan_profile_count": len(forest_plan_profiles.get("profiles", [])),
        "forest_plan_component_count": len(forest_components.get("components", [])),
        "currentness_validation_passed": currentness.get("validation", {}).get("passed")
        if isinstance(currentness.get("validation"), dict)
        else currentness.get("summary", {}).get("validation_passed"),
        "input_count": len(inputs),
        **_region1_readiness_summary(region1_forest_plan_readiness),
    }


def _is_source_register_v1_catalog(catalog_rows: list[dict[str, Any]]) -> bool:
    return any(
        str(_dict(row.get("metadata")).get("loader_contract") or "") == "source_register_v1"
        for row in catalog_rows
    )


def _source_register_proving_context_for_source_set(
    *,
    output_dir: Path,
    source_set_id: str,
) -> dict[str, Any] | None:
    try:
        context = resolve_latest_proving_context(output_dir)
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        return None
    if str(context.get("source_set_id") or "") == source_set_id:
        return context
    manifest_path_value = str(context.get("source_set_manifest_path") or "").strip()
    if not manifest_path_value:
        return None
    try:
        manifest = _read_json(manifest_path_value)
    except (FileNotFoundError, ValueError, json.JSONDecodeError):
        return None
    return context if str(manifest.get("source_set_id") or "") == source_set_id else None
