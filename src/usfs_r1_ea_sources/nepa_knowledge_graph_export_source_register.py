from __future__ import annotations

from pathlib import Path
from typing import Any

from .nepa_3d_graph_contract import build_nepa_3d_lens_metadata
from .nepa_knowledge_graph_export_common import _currentness_metadata
from .nepa_knowledge_graph_export_common import _family_display_status
from .nepa_knowledge_graph_export_common import _family_readiness_blockers
from .nepa_knowledge_graph_export_common import _source_display_status
from .nepa_knowledge_graph_export_common import _source_readiness_blockers
from .nepa_knowledge_graph_export_models import _GraphBuilder
from .nepa_knowledge_graph_export_models import _artifact_node_id
from .nepa_knowledge_graph_export_models import _dict
from .nepa_knowledge_graph_export_models import _dict_list
from .nepa_knowledge_graph_export_models import _family_node_id
from .nepa_knowledge_graph_export_models import _read_json
from .nepa_knowledge_graph_export_models import _semantic_label
from .nepa_knowledge_graph_export_models import _source_node_id
from .nepa_knowledge_graph_export_models import _strings
from .nepa_knowledge_graph_export_review_overlay import _add_blocker


def _add_lens_nodes(builder: _GraphBuilder, *, contract: dict[str, Any]) -> None:
    for lens in build_nepa_3d_lens_metadata(contract):
        builder.add_node(
            node_id=f"graph_lens:{lens['lens_id']}",
            node_type="graph_lens",
            label=str(lens.get("label") or lens["lens_id"]),
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={"lens_id": lens["lens_id"]},
            metadata=lens,
        )


def _add_source_records_and_artifacts(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    catalog_rows: list[dict[str, Any]],
    source_currentness_by_id: dict[str, dict[str, Any]],
    catalog_partition_by_id: dict[str, dict[str, Any]],
) -> None:
    for row in sorted(catalog_rows, key=lambda item: str(item.get("source_record_id") or "")):
        source_record_id = str(row.get("source_record_id") or "")
        currentness = source_currentness_by_id.get(source_record_id, {})
        partition = catalog_partition_by_id.get(source_record_id, {})
        status = _source_display_status(row=row, currentness=currentness, partition=partition)
        blockers = _source_readiness_blockers(row=row, currentness=currentness, partition=partition)
        source_node_id = _source_node_id(source_record_id)
        builder.add_node(
            node_id=source_node_id,
            node_type="source_record",
            label=str(row.get("title") or currentness.get("source_title") or source_record_id),
            display_status=status["display_status"],
            review_readiness_status=status["review_readiness_status"],
            provenance={
                "source_set_id": source_set_id,
                "source_record_id": source_record_id,
                "citation_label": row.get("citation_label") or currentness.get("citation_label"),
                "artifact_sha256": row.get("artifact_sha256") or currentness.get("artifact_sha256"),
                "artifact_path": row.get("artifact_path") or currentness.get("artifact_path"),
                "url": row.get("effective_url") or row.get("original_url") or currentness.get("url"),
            },
            currentness_metadata=_currentness_metadata(currentness=currentness, partition=partition),
            readiness_blockers=blockers,
            metadata={
                "source_status": row.get("source_status"),
                "document_role": row.get("document_role"),
                "authority_level": row.get("authority_level"),
                "scope": row.get("scope"),
                "issuer": row.get("issuer"),
                "review_topics": row.get("review_topics", []),
            },
        )
        artifact_sha256 = row.get("artifact_sha256") or currentness.get("artifact_sha256")
        if artifact_sha256:
            artifact_node_id = _artifact_node_id(str(artifact_sha256))
            builder.add_node(
                node_id=artifact_node_id,
                node_type="artifact",
                label=f"Artifact {str(artifact_sha256)[:12]}",
                display_status=status["display_status"],
                review_readiness_status=status["review_readiness_status"],
                provenance={
                    "source_set_id": source_set_id,
                    "source_record_id": source_record_id,
                    "artifact_sha256": artifact_sha256,
                    "artifact_path": row.get("artifact_path") or currentness.get("artifact_path"),
                    "citation_label": row.get("citation_label") or currentness.get("citation_label"),
                },
                currentness_metadata=_currentness_metadata(currentness=currentness, partition=partition),
                readiness_blockers=blockers,
            )
            builder.add_edge(
                edge_type="HAS_ARTIFACT",
                source_node_id=source_node_id,
                target_node_id=artifact_node_id,
                display_status=status["display_status"],
                review_readiness_status=status["review_readiness_status"],
                provenance={
                    "source_set_id": source_set_id,
                    "source_record_id": source_record_id,
                    "artifact_sha256": artifact_sha256,
                },
                readiness_blockers=blockers,
            )


def _add_source_register_semantics(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    catalog_rows: list[dict[str, Any]],
    source_currentness_by_id: dict[str, dict[str, Any]],
    catalog_partition_by_id: dict[str, dict[str, Any]],
    jurisdiction_scope_register: dict[str, Any],
    proving_context: dict[str, Any] | None,
) -> None:
    grouped_documents: dict[str, list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]] = {}
    grouped_sections: dict[str, list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]] = {}
    grouped_scopes: dict[str, list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]] = {}
    scope_labels = {
        str(scope.get("scope_id") or ""): str(scope.get("label") or scope.get("name") or "")
        for scope in _dict_list(jurisdiction_scope_register.get("scopes"))
        if scope.get("scope_id")
    }

    for row in sorted(catalog_rows, key=lambda item: str(item.get("source_record_id") or "")):
        source_record_id = str(row.get("source_record_id") or "")
        metadata = _dict(row.get("metadata"))
        currentness = source_currentness_by_id.get(source_record_id, {})
        partition = catalog_partition_by_id.get(source_record_id, {})
        document_id = str(metadata.get("authority_document_id") or "")
        section_id = str(metadata.get("authority_section_id") or "")
        scope_id = str(metadata.get("jurisdiction_scope_id") or "")
        entry = (row, currentness, partition)
        if document_id:
            grouped_documents.setdefault(document_id, []).append(entry)
        if section_id:
            grouped_sections.setdefault(section_id, []).append(entry)
        if scope_id:
            grouped_scopes.setdefault(scope_id, []).append(entry)

    for document_id, entries in sorted(grouped_documents.items()):
        exemplar = entries[0][0]
        metadata = _dict(exemplar.get("metadata"))
        status = _source_register_semantic_status(entries)
        builder.add_node(
            node_id=document_id,
            node_type="authority_document",
            label=str(metadata.get("citation_or_code") or exemplar.get("title") or document_id),
            display_status=status["display_status"],
            review_readiness_status=status["review_readiness_status"],
            provenance={
                "source_set_id": source_set_id,
                "authority_document_id": document_id,
            },
            currentness_metadata=_source_register_semantic_currentness(entries),
            readiness_blockers=status["readiness_blockers"],
            metadata={
                "document_type": metadata.get("document_type"),
                "authority_tier": metadata.get("authority_tier"),
                "issuer": metadata.get("issuer"),
                "jurisdiction_or_unit": metadata.get("jurisdiction_or_unit"),
                "issue_or_effective_date": metadata.get("issue_or_effective_date"),
                "source_record_ids": [
                    str(row.get("source_record_id") or "") for row, _, _ in entries
                ],
            },
        )

    for section_id, entries in sorted(grouped_sections.items()):
        exemplar = entries[0][0]
        metadata = _dict(exemplar.get("metadata"))
        document_id = str(metadata.get("authority_document_id") or "")
        status = _source_register_semantic_status(entries)
        builder.add_node(
            node_id=section_id,
            node_type="authority_section",
            label=str(metadata.get("citation_or_code") or section_id.rsplit("#", 1)[-1]),
            display_status=status["display_status"],
            review_readiness_status=status["review_readiness_status"],
            provenance={
                "source_set_id": source_set_id,
                "authority_section_id": section_id,
            },
            currentness_metadata=_source_register_semantic_currentness(entries),
            readiness_blockers=status["readiness_blockers"],
            metadata={
                "authority_document_id": document_id,
                "source_record_ids": [
                    str(row.get("source_record_id") or "") for row, _, _ in entries
                ],
            },
        )
        if document_id:
            builder.add_edge(
                edge_type="HAS_AUTHORITY_SECTION",
                source_node_id=document_id,
                target_node_id=section_id,
                display_status=status["display_status"],
                review_readiness_status=status["review_readiness_status"],
                provenance={
                    "source_set_id": source_set_id,
                    "authority_document_id": document_id,
                    "authority_section_id": section_id,
                },
                readiness_blockers=status["readiness_blockers"],
            )

    for scope_id, entries in sorted(grouped_scopes.items()):
        status = _source_register_semantic_status(entries)
        builder.add_node(
            node_id=scope_id,
            node_type="jurisdiction_scope",
            label=scope_labels.get(scope_id) or scope_id.replace("scope:", "").replace("-", " "),
            display_status=status["display_status"],
            review_readiness_status=status["review_readiness_status"],
            provenance={
                "source_set_id": source_set_id,
                "jurisdiction_scope_id": scope_id,
            },
            currentness_metadata=_source_register_semantic_currentness(entries),
            readiness_blockers=status["readiness_blockers"],
            metadata={
                "source_record_ids": [
                    str(row.get("source_record_id") or "") for row, _, _ in entries
                ],
            },
        )

    for row in sorted(catalog_rows, key=lambda item: str(item.get("source_record_id") or "")):
        source_record_id = str(row.get("source_record_id") or "")
        metadata = _dict(row.get("metadata"))
        currentness = source_currentness_by_id.get(source_record_id, {})
        partition = catalog_partition_by_id.get(source_record_id, {})
        status = _source_display_status(row=row, currentness=currentness, partition=partition)
        blockers = _source_readiness_blockers(
            row=row,
            currentness=currentness,
            partition=partition,
        )
        document_id = str(metadata.get("authority_document_id") or "")
        section_id = str(metadata.get("authority_section_id") or "")
        scope_id = str(metadata.get("jurisdiction_scope_id") or "")
        if document_id:
            builder.add_edge(
                edge_type="CITES_AUTHORITY_DOCUMENT",
                source_node_id=_source_node_id(source_record_id),
                target_node_id=document_id,
                display_status=status["display_status"],
                review_readiness_status=status["review_readiness_status"],
                provenance={
                    "source_set_id": source_set_id,
                    "source_record_id": source_record_id,
                    "authority_document_id": document_id,
                },
                readiness_blockers=blockers,
            )
        if scope_id:
            builder.add_edge(
                edge_type="HAS_JURISDICTION_SCOPE",
                source_node_id=_source_node_id(source_record_id),
                target_node_id=scope_id,
                display_status=status["display_status"],
                review_readiness_status=status["review_readiness_status"],
                provenance={
                    "source_set_id": source_set_id,
                    "source_record_id": source_record_id,
                    "jurisdiction_scope_id": scope_id,
                },
                readiness_blockers=blockers,
            )
        if section_id and document_id:
            builder.add_edge(
                edge_type="HAS_AUTHORITY_SECTION",
                source_node_id=document_id,
                target_node_id=section_id,
                display_status=status["display_status"],
                review_readiness_status=status["review_readiness_status"],
                provenance={
                    "source_set_id": source_set_id,
                    "source_record_id": source_record_id,
                    "authority_document_id": document_id,
                    "authority_section_id": section_id,
                },
                readiness_blockers=blockers,
            )

    relationships_path = (
        Path(proving_context["report_path"]).parent / "relationships.json"
        if proving_context is not None
        else None
    )
    relationship_rows = (
        _dict_list(_read_json(relationships_path).get("relationships"))
        if relationships_path is not None and relationships_path.exists()
        else []
    )
    for relationship in relationship_rows:
        relationship_id = str(relationship.get("relationship_id") or "")
        if not relationship_id:
            continue
        source_node_id = _ensure_source_register_semantic_endpoint(
            builder,
            source_set_id=source_set_id,
            class_id=str(relationship.get("source_class_id") or ""),
            semantic_id=str(relationship.get("source_id") or ""),
        )
        target_node_id = _ensure_source_register_semantic_endpoint(
            builder,
            source_set_id=source_set_id,
            class_id=str(relationship.get("target_class_id") or ""),
            semantic_id=str(relationship.get("target_id") or ""),
        )
        relationship_basis = str(relationship.get("relationship_basis") or "")
        evidence_basis_type = str(relationship.get("evidence_basis_type") or "")
        relationship_type = str(relationship.get("relationship_type") or "")
        path_pattern_id = str(relationship.get("path_pattern_id") or "")
        support_ids = _strings(relationship.get("supporting_source_record_ids"))
        authority_path_node_id = f"authority_path:{relationship_id}"
        justification_path_node_id = f"justification_path:{relationship_id}"
        builder.add_node(
            node_id=authority_path_node_id,
            node_type="authority_path",
            label=relationship_type.replace("_", " ").title(),
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "authority_path_id": relationship_id,
                "relationship_id": relationship_id,
            },
            metadata={
                "relationship_type": relationship_type,
                "path_pattern_id": path_pattern_id,
                "source_class_id": relationship.get("source_class_id"),
                "source_id": relationship.get("source_id"),
                "target_class_id": relationship.get("target_class_id"),
                "target_id": relationship.get("target_id"),
                "relationship_basis": relationship_basis,
                "evidence_basis_type": evidence_basis_type,
                "status": relationship.get("status"),
                "confidence": "workbook_curated"
                if evidence_basis_type == "workbook_curated"
                else "currentness_adjudicated",
            },
        )
        builder.add_edge(
            edge_type="HAS_AUTHORITY_PATH",
            source_node_id=source_node_id,
            target_node_id=authority_path_node_id,
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "relationship_id": relationship_id,
                "relationship_type": relationship_type,
            },
        )
        builder.add_edge(
            edge_type="PATH_TARGETS",
            source_node_id=authority_path_node_id,
            target_node_id=target_node_id,
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "relationship_id": relationship_id,
                "relationship_type": relationship_type,
            },
        )
        builder.add_node(
            node_id=justification_path_node_id,
            node_type="justification_path",
            label=f"Justification for {relationship_type.replace('_', ' ').title()}",
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "justification_path_id": relationship_id,
                "relationship_id": relationship_id,
            },
            metadata={
                "supporting_source_record_ids": support_ids,
                "relationship_basis": relationship_basis,
                "evidence_basis_type": evidence_basis_type,
                "confidence": "workbook_curated"
                if evidence_basis_type == "workbook_curated"
                else "currentness_adjudicated",
            },
        )
        builder.add_edge(
            edge_type="JUSTIFIED_BY",
            source_node_id=authority_path_node_id,
            target_node_id=justification_path_node_id,
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "relationship_id": relationship_id,
            },
        )
        for supporting_source_record_id in support_ids:
            builder.add_edge(
                edge_type="SUPPORTS_JUSTIFICATION_PATH",
                source_node_id=_source_node_id(supporting_source_record_id),
                target_node_id=justification_path_node_id,
                display_status="active",
                review_readiness_status="not_review_specific",
                provenance={
                    "source_set_id": source_set_id,
                    "relationship_id": relationship_id,
                    "source_record_id": supporting_source_record_id,
                },
            )


def _ensure_source_register_semantic_endpoint(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    class_id: str,
    semantic_id: str,
) -> str:
    if not semantic_id:
        return semantic_id
    node_type = {
        "authority_document": "authority_document",
        "authority_section": "authority_section",
        "jurisdiction_scope": "jurisdiction_scope",
        "forest_plan": "forest_plan",
        "forest_unit": "forest_unit",
    }.get(class_id)
    if node_type is None:
        return semantic_id
    if semantic_id in builder.nodes:
        return semantic_id
    provenance: dict[str, Any] = {"source_set_id": source_set_id}
    if node_type == "authority_document":
        provenance["authority_document_id"] = semantic_id
    elif node_type == "authority_section":
        provenance["authority_section_id"] = semantic_id
    elif node_type == "jurisdiction_scope":
        provenance["jurisdiction_scope_id"] = semantic_id
    elif node_type == "forest_unit":
        provenance["forest_code"] = semantic_id.removeprefix("forest_unit:")
    elif node_type == "forest_plan":
        provenance["forest_code"] = semantic_id.removeprefix("forest_plan:")
        provenance["source_record_id"] = semantic_id
    builder.add_node(
        node_id=semantic_id,
        node_type=node_type,
        label=_semantic_label(semantic_id),
        display_status="active",
        review_readiness_status="not_review_specific",
        provenance=provenance,
        metadata={"semantic_identity": semantic_id},
    )
    return semantic_id


def _source_register_semantic_status(
    entries: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]
) -> dict[str, Any]:
    statuses = [
        _source_display_status(row=row, currentness=currentness, partition=partition)
        for row, currentness, partition in entries
    ]
    blockers = sorted(
        {
            blocker
            for row, currentness, partition in entries
            for blocker in _source_readiness_blockers(
                row=row,
                currentness=currentness,
                partition=partition,
            )
        }
    )
    for display_status in ("active", "candidate", "superseded", "reserved"):
        for status in statuses:
            if status["display_status"] == display_status:
                return {**status, "readiness_blockers": blockers}
    status = statuses[0] if statuses else {
        "display_status": "active",
        "review_readiness_status": "not_review_specific",
    }
    return {**status, "readiness_blockers": blockers}


def _source_register_semantic_currentness(
    entries: list[tuple[dict[str, Any], dict[str, Any], dict[str, Any]]]
) -> dict[str, Any]:
    return {
        "source_record_ids": [
            str(row.get("source_record_id") or "") for row, _, _ in entries
        ],
        "currentness_statuses": sorted(
            {
                str(_dict(row.get("metadata")).get("currentness_status") or currentness.get("currentness_status") or "")
                for row, currentness, _ in entries
                if str(
                    _dict(row.get("metadata")).get("currentness_status")
                    or currentness.get("currentness_status")
                    or ""
                ).strip()
            }
        ),
        "source_partition_ids": sorted(
            {
                str(partition.get("source_partition") or "")
                for _, _, partition in entries
                if str(partition.get("source_partition") or "").strip()
            }
        ),
    }


def _add_authority_families(
    builder: _GraphBuilder,
    *,
    source_set_node_id: str,
    source_set_id: str,
    families: list[dict[str, Any]],
    family_currentness_by_id: dict[str, dict[str, Any]],
    source_currentness_by_id: dict[str, dict[str, Any]],
    catalog_by_id: dict[str, dict[str, Any]],
) -> None:
    for family in sorted(families, key=lambda item: str(item.get("family_id") or "")):
        family_id = str(family.get("family_id") or "")
        currentness = family_currentness_by_id.get(family_id, {})
        status = _family_display_status(family, currentness)
        blockers = _family_readiness_blockers(family, currentness)
        family_node_id = _family_node_id(family_id)
        builder.add_node(
            node_id=family_node_id,
            node_type="authority_family",
            label=str(family.get("name") or family_id),
            display_status=status["display_status"],
            review_readiness_status=status["review_readiness_status"],
            provenance={
                "source_set_id": source_set_id,
                "authority_family_id": family_id,
                "family_status": family.get("status"),
            },
            currentness_metadata={
                "family_status": family.get("status"),
                "currentness_status": currentness.get("currentness_status"),
                "current_source_record_count": currentness.get("current_source_record_count"),
                "replacement_source_record_count": currentness.get("replacement_source_record_count"),
                "source_addition_decision_status": currentness.get("source_addition_decision_status"),
            },
            readiness_blockers=blockers,
            metadata={
                "authority_category": family.get("authority_category"),
                "required_authority_requirement_ids": family.get(
                    "required_authority_requirement_ids", []
                ),
                "rule_ids": family.get("rule_ids", []),
                "open_inventory_gaps": family.get("open_inventory_gaps", []),
            },
        )
        builder.add_edge(
            edge_type="CONTAINS_AUTHORITY_FAMILY",
            source_node_id=source_set_node_id,
            target_node_id=family_node_id,
            display_status=status["display_status"],
            review_readiness_status=status["review_readiness_status"],
            provenance={"source_set_id": source_set_id, "authority_family_id": family_id},
            readiness_blockers=blockers,
        )
        for source_record_id in sorted(set(_strings(family.get("source_record_ids")))):
            if source_record_id not in catalog_by_id and source_record_id not in source_currentness_by_id:
                continue
            source_record = source_currentness_by_id.get(source_record_id, {})
            source_status = _source_display_status(
                row=catalog_by_id.get(source_record_id, {}),
                currentness=source_record,
                partition={},
            )
            source_blockers = _source_readiness_blockers(
                row=catalog_by_id.get(source_record_id, {}),
                currentness=source_record,
                partition={},
            )
            builder.add_edge(
                edge_type="HAS_SOURCE_RECORD",
                source_node_id=family_node_id,
                target_node_id=_source_node_id(source_record_id),
                display_status=source_status["display_status"],
                review_readiness_status=source_status["review_readiness_status"],
                provenance={
                    "source_set_id": source_set_id,
                    "authority_family_id": family_id,
                    "source_record_id": source_record_id,
                    "family_status": family.get("status"),
                    "authority_family_source_role": source_record.get("authority_family_source_role"),
                },
                readiness_blockers=source_blockers,
            )
        if blockers:
            _add_blocker(builder, source_set_id=source_set_id, subject_node_id=family_node_id, blockers=blockers)
