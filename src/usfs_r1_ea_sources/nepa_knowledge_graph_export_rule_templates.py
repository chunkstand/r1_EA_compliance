from __future__ import annotations

from typing import Any

from .nepa_knowledge_graph_export_models import AUTHORITY_TEMPLATE_NODE_PREFIX
from .nepa_knowledge_graph_export_models import BASE_RULE_NODE_PREFIX
from .nepa_knowledge_graph_export_models import _GraphBuilder
from .nepa_knowledge_graph_export_models import _artifact_node_id
from .nepa_knowledge_graph_export_models import _dict
from .nepa_knowledge_graph_export_models import _family_node_id
from .nepa_knowledge_graph_export_models import _source_node_id
from .nepa_knowledge_graph_export_models import _strings


def _add_base_rules(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    rule_pack: dict[str, Any],
    families: list[dict[str, Any]],
) -> dict[str, str]:
    family_ids_by_rule_id: dict[str, set[str]] = {}
    for family in families:
        for rule_id in _strings(family.get("rule_ids")):
            family_ids_by_rule_id.setdefault(rule_id, set()).add(str(family.get("family_id")))

    rule_node_ids: dict[str, str] = {}
    for rule in sorted(rule_pack.get("rules", []), key=lambda item: str(item.get("id") or "")):
        rule_id = str(rule.get("id") or "")
        node_id = f"{BASE_RULE_NODE_PREFIX}:{rule_id}"
        rule_node_ids[rule_id] = node_id
        source_record_id = rule.get("authority_source_record_id") or _dict(rule.get("source_filters")).get(
            "source_record_id"
        )
        builder.add_node(
            node_id=node_id,
            node_type="rule_template",
            label=str(rule.get("title") or rule_id),
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "rule_id": rule_id,
                "rule_pack_id": rule_pack.get("rule_pack_id"),
                "rule_pack_version": rule_pack.get("version"),
                "authority_source_record_id": source_record_id,
            },
            metadata={
                "rule_kind": "base_rule_pack_rule",
                "applicability_mode": rule.get("applicability_mode"),
                "authority_category": rule.get("authority_category"),
                "severity": rule.get("severity"),
                "requirement": rule.get("requirement"),
                "family_ids": sorted(family_ids_by_rule_id.get(rule_id, [])),
            },
        )
        if source_record_id:
            builder.add_edge(
                edge_type="SUPPORTS_RULE_TEMPLATE",
                source_node_id=_source_node_id(str(source_record_id)),
                target_node_id=node_id,
                display_status="active",
                review_readiness_status="not_review_specific",
                provenance={
                    "source_set_id": source_set_id,
                    "source_record_id": source_record_id,
                    "rule_id": rule_id,
                    "rule_pack_id": rule_pack.get("rule_pack_id"),
                    "rule_pack_version": rule_pack.get("version"),
                },
            )
        for family_id in sorted(family_ids_by_rule_id.get(rule_id, [])):
            builder.add_edge(
                edge_type="SUPPORTS_RULE_TEMPLATE",
                source_node_id=_family_node_id(family_id),
                target_node_id=node_id,
                display_status="active",
                review_readiness_status="not_review_specific",
                provenance={
                    "source_set_id": source_set_id,
                    "authority_family_id": family_id,
                    "rule_id": rule_id,
                },
            )
    return rule_node_ids


def _add_authority_family_templates(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    template_config: dict[str, Any],
) -> dict[str, str]:
    template_node_ids: dict[str, str] = {}
    for template in sorted(template_config.get("templates", []), key=lambda item: str(item.get("template_id") or "")):
        template_id = str(template.get("template_id") or template.get("rule_id") or "")
        rule_id = str(template.get("rule_id") or template_id)
        family_id = str(template.get("authority_family_id") or "")
        node_id = f"{AUTHORITY_TEMPLATE_NODE_PREFIX}:{template_id}"
        template_node_ids[template_id] = node_id
        builder.add_node(
            node_id=node_id,
            node_type="rule_template",
            label=str(template.get("title") or template_id),
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "template_id": template_id,
                "rule_id": rule_id,
                "rule_pack_id": template_config.get("base_rule_pack_id"),
                "rule_pack_version": template_config.get("base_rule_pack_version"),
                "authority_family_id": family_id,
            },
            metadata={
                "rule_kind": "authority_family_template",
                "applicability_mode": template.get("applicability_mode"),
                "package_fact_types": template.get("package_fact_types", []),
                "source_record_ids": template.get("source_record_ids", []),
                "supporting_source_record_ids": template.get("supporting_source_record_ids", []),
                "requirement": template.get("requirement"),
            },
        )
        if family_id:
            builder.add_edge(
                edge_type="SUPPORTS_RULE_TEMPLATE",
                source_node_id=_family_node_id(family_id),
                target_node_id=node_id,
                display_status="active",
                review_readiness_status="not_review_specific",
                provenance={
                    "source_set_id": source_set_id,
                    "authority_family_id": family_id,
                    "template_id": template_id,
                    "rule_id": rule_id,
                },
            )
        for source_record_id in sorted(set(_strings(template.get("source_record_ids")))):
            builder.add_edge(
                edge_type="SUPPORTS_RULE_TEMPLATE",
                source_node_id=_source_node_id(source_record_id),
                target_node_id=node_id,
                display_status="active",
                review_readiness_status="not_review_specific",
                provenance={
                    "source_set_id": source_set_id,
                    "source_record_id": source_record_id,
                    "template_id": template_id,
                    "rule_id": rule_id,
                },
            )
    return template_node_ids


def _add_rule_claim_paths(
    builder: _GraphBuilder,
    *,
    source_set_id: str,
    claims_by_id: dict[str, dict[str, Any]],
    rule_claim_links: list[dict[str, Any]],
    base_rule_node_ids: dict[str, str],
) -> None:
    for link in sorted(rule_claim_links, key=lambda item: str(item.get("link_id") or "")):
        claim_id = str(link.get("claim_id") or "")
        rule_id = str(link.get("rule_id") or "")
        if not claim_id or rule_id not in base_rule_node_ids:
            continue
        claim = claims_by_id.get(claim_id, {})
        source_record_id = str(link.get("source_record_id") or claim.get("source_record_id") or "")
        artifact_sha256 = str(link.get("artifact_sha256") or claim.get("artifact_sha256") or "")
        chunk_id = str(link.get("chunk_id") or claim.get("chunk_id") or "")
        if not chunk_id:
            chunk_id = f"chunk:{source_record_id}:{link.get('chunk_index')}:{str(link.get('chunk_content_sha256') or '')[:12]}"
        chunk_node_id = f"chunk:{chunk_id.removeprefix('chunk:')}"
        evidence_node_id = f"evidence_span:{claim_id.removeprefix('claim:')}:{str(link.get('link_id') or '')[-12:]}"
        claim_node_id = f"source_claim:{claim_id.removeprefix('claim:')}"
        artifact_node_id = _artifact_node_id(artifact_sha256) if artifact_sha256 else None

        builder.add_node(
            node_id=chunk_node_id,
            node_type="chunk",
            label=f"{source_record_id} chunk {link.get('chunk_index')}",
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "source_record_id": source_record_id,
                "chunk_index": link.get("chunk_index") or claim.get("chunk_index"),
                "content_sha256": link.get("chunk_content_sha256") or claim.get("chunk_content_sha256"),
                "artifact_sha256": artifact_sha256,
            },
            metadata={
                "citation_label": link.get("citation_label") or claim.get("citation_label"),
                "source_text_path": link.get("source_text_path") or claim.get("source_text_path"),
            },
        )
        builder.add_node(
            node_id=evidence_node_id,
            node_type="evidence_span",
            label=f"{source_record_id} evidence for {rule_id}",
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "source_record_id": source_record_id,
                "chunk_index": link.get("chunk_index") or claim.get("chunk_index"),
                "char_start": link.get("source_char_start") or claim.get("source_char_start"),
                "char_end": link.get("source_char_end") or claim.get("source_char_end"),
                "claim_id": claim_id,
                "link_id": link.get("link_id"),
            },
            metadata={
                "citation_label": link.get("citation_label") or claim.get("citation_label"),
                "page": link.get("page") or claim.get("page"),
                "section": link.get("section") or claim.get("section"),
            },
        )
        builder.add_node(
            node_id=claim_node_id,
            node_type="source_claim",
            label=str((claim.get("claim_text") or link.get("claim_text") or claim_id))[:180],
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "claim_id": claim_id,
                "source_record_id": source_record_id,
                "content_sha256": claim.get("content_sha256") or link.get("content_sha256"),
            },
            metadata={
                "claim_type": claim.get("claim_type") or link.get("claim_type"),
                "validation_status": claim.get("validation_status")
                or link.get("claim_validation_status"),
                "confidence": claim.get("confidence"),
            },
        )
        if artifact_node_id:
            builder.add_edge(
                edge_type="HAS_CHUNK",
                source_node_id=artifact_node_id,
                target_node_id=chunk_node_id,
                display_status="active",
                review_readiness_status="not_review_specific",
                provenance={
                    "source_set_id": source_set_id,
                    "source_record_id": source_record_id,
                    "artifact_sha256": artifact_sha256,
                    "chunk_id": chunk_id,
                },
            )
        builder.add_edge(
            edge_type="HAS_EVIDENCE_SPAN",
            source_node_id=chunk_node_id,
            target_node_id=evidence_node_id,
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "source_record_id": source_record_id,
                "claim_id": claim_id,
                "link_id": link.get("link_id"),
            },
        )
        builder.add_edge(
            edge_type="SUPPORTS_SOURCE_CLAIM",
            source_node_id=evidence_node_id,
            target_node_id=claim_node_id,
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "source_record_id": source_record_id,
                "claim_id": claim_id,
                "link_id": link.get("link_id"),
            },
        )
        builder.add_edge(
            edge_type="SUPPORTS_RULE_TEMPLATE",
            source_node_id=claim_node_id,
            target_node_id=base_rule_node_ids[rule_id],
            display_status="active",
            review_readiness_status="not_review_specific",
            provenance={
                "source_set_id": source_set_id,
                "source_record_id": source_record_id,
                "claim_id": claim_id,
                "rule_id": rule_id,
                "link_id": link.get("link_id"),
                "score": link.get("score"),
            },
        )
