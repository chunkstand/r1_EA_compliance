from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import hashlib
import json
import re

from .claim_extraction import default_claims_path
from .forest_plan_profiles import DEFAULT_FOREST_PLAN_PROFILES_PATH
from .forest_plan_profiles import ForestPlanProfileCollection
from .forest_plan_profiles import load_forest_plan_profiles
from .records import sha256_file
from .rule_claim_binding import default_rule_claim_links_path
from .rule_packs import DEFAULT_RULE_PACK_PATH
from .rule_packs import load_rule_pack
from .rule_packs import validate_rule_pack


AUTHORITY_UNIVERSE_SCHEMA_VERSION = "authority-universe-snapshot-v0"
AUTHORITY_FAMILY_RULE_TEMPLATES_SCHEMA_VERSION = "authority-family-rule-templates-v1"
DEFAULT_AUTHORITY_FAMILY_TEMPLATES_PATH = Path(
    "config/authority_family_rule_templates_nepa_ea_v1.json"
)
SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
FOREST_PLAN_COMPONENT_AUTHORITY_FAMILY_ID = "nfma_forest_planning_project_consistency"
BASE_RULE_PACKAGE_FACT_TYPES = (
    "action",
    "agency",
    "decision_posture",
    "nepa_level",
    "package_section",
    "evidence_span",
)
FOREST_PLAN_PACKAGE_FACT_TYPES = (
    "action",
    "agency",
    "geography",
    "management_area",
    "overlay",
    "resource_topic",
    "package_section",
    "evidence_span",
)
RULE_GRAPH_RELATIONSHIP_TYPES = (
    "source_record",
    "authority_category",
    "source_claim",
    "rule_claim_link",
    "package_fact",
    "evidence_span",
    "exception",
    "dependency",
    "supersession",
)
FOREST_PLAN_GRAPH_RELATIONSHIP_TYPES = (
    "forest_plan_profile",
    "component_inventory",
    "source_record",
    "source_chunk",
    "geography",
    "management_area",
    "overlay",
    "package_fact",
    "evidence_span",
)


@dataclass(frozen=True)
class AuthorityUniverseSnapshotResult:
    review_id: str
    source_set_id: str
    applicability_dir: Path
    snapshot_path: Path
    summary: dict


def build_authority_universe_snapshot(
    *,
    output_dir: Path,
    review_id: str,
    source_set_id: str | None = None,
    source_catalog_path: Path | None = None,
    source_set_manifest_path: Path | None = None,
    base_rule_pack_path: Path = DEFAULT_RULE_PACK_PATH,
    forest_plan_profiles_path: Path = DEFAULT_FOREST_PLAN_PROFILES_PATH,
    authority_family_templates_path: Path | None = DEFAULT_AUTHORITY_FAMILY_TEMPLATES_PATH,
    forest_plan_component_inventory_path: Path | None = None,
    claims_path: Path | None = None,
    rule_claim_links_path: Path | None = None,
) -> AuthorityUniverseSnapshotResult:
    """Build the candidate authority universe used by applicability determination."""

    output_dir = Path(output_dir)
    _validate_safe_segment(review_id, "review_id")
    catalog_dir = output_dir / "catalog"
    source_set_manifest_path = (
        Path(source_set_manifest_path)
        if source_set_manifest_path
        else catalog_dir / "source_set_manifest.json"
    )
    source_catalog_path = (
        Path(source_catalog_path)
        if source_catalog_path
        else catalog_dir / "source_catalog.jsonl"
    )
    source_set_manifest = _read_json_if_exists(source_set_manifest_path) or {}
    if source_set_id is None:
        source_set_id = _source_set_id_from_manifest(source_set_manifest_path, source_set_manifest)
    _validate_safe_segment(source_set_id, "source_set_id")
    catalog_records = _load_source_catalog(source_catalog_path, source_set_id)
    catalog_by_source_id = {
        str(record["source_record_id"]): record for record in catalog_records
    }

    base_rule_pack_path = Path(base_rule_pack_path)
    if not base_rule_pack_path.exists():
        raise FileNotFoundError(f"Missing base rule pack: {base_rule_pack_path}")
    base_rule_pack = load_rule_pack(base_rule_pack_path)
    rule_pack_validation = validate_rule_pack(base_rule_pack)
    base_rule_pack_sha256 = sha256_file(base_rule_pack_path)

    forest_plan_profiles_path = Path(forest_plan_profiles_path)
    profiles = load_forest_plan_profiles(forest_plan_profiles_path)
    profiles_sha256 = sha256_file(forest_plan_profiles_path)

    authority_family_templates_path = (
        Path(authority_family_templates_path)
        if authority_family_templates_path
        else None
    )
    authority_family_templates = (
        _load_authority_family_templates(authority_family_templates_path)
        if authority_family_templates_path
        else None
    )
    authority_family_templates_sha256 = (
        sha256_file(authority_family_templates_path)
        if authority_family_templates_path and authority_family_templates_path.exists()
        else None
    )

    claims_path = claims_path or default_claims_path(output_dir, source_set_id)
    rule_claim_links_path = rule_claim_links_path or default_rule_claim_links_path(
        output_dir,
        source_set_id=source_set_id,
        rule_pack_path=base_rule_pack_path,
    )
    rule_claim_gaps_path = rule_claim_links_path.parent / "rule_claim_link_gaps.jsonl"
    source_claim_links = _read_jsonl_if_exists(rule_claim_links_path)
    source_claim_gaps = _read_jsonl_if_exists(rule_claim_gaps_path)
    source_claim_links_by_rule = _records_by_key(source_claim_links, "rule_id")
    source_claim_gaps_by_rule = _records_by_key(source_claim_gaps, "rule_id")

    forest_plan_component_inventory_path = (
        Path(forest_plan_component_inventory_path)
        if forest_plan_component_inventory_path
        else _default_forest_plan_component_inventory_path(output_dir, source_set_id)
    )
    component_inventory = _read_json_if_exists(forest_plan_component_inventory_path)
    component_inventory_sha256 = (
        sha256_file(forest_plan_component_inventory_path)
        if forest_plan_component_inventory_path.exists()
        else None
    )

    created_at = _utc_now()
    rule_candidates = _rule_template_candidates(
        source_set_id=source_set_id,
        rule_pack=base_rule_pack,
        catalog_by_source_id=catalog_by_source_id,
        source_claim_links_by_rule=source_claim_links_by_rule,
        source_claim_gaps_by_rule=source_claim_gaps_by_rule,
    )
    authority_family_candidates = _authority_family_template_candidates(
        source_set_id=source_set_id,
        template_set=authority_family_templates,
        catalog_by_source_id=catalog_by_source_id,
    )
    component_candidates = _forest_plan_component_candidates(
        source_set_id=source_set_id,
        profiles=profiles,
        component_inventory=component_inventory,
        component_inventory_path=forest_plan_component_inventory_path,
        component_inventory_sha256=component_inventory_sha256,
        catalog_by_source_id=catalog_by_source_id,
    )
    candidate_authorities = sorted(
        [*rule_candidates, *authority_family_candidates, *component_candidates],
        key=lambda candidate: str(candidate["candidate_authority_id"]),
    )
    authority_universe_sha256 = _stable_sha256(
        {
            "schema_version": AUTHORITY_UNIVERSE_SCHEMA_VERSION,
            "source_set_id": source_set_id,
            "base_rule_pack_sha256": base_rule_pack_sha256,
            "source_set_manifest_sha256": _optional_file_sha256(source_set_manifest_path),
            "catalog_sha256": _optional_file_sha256(source_catalog_path),
            "profiles_sha256": profiles_sha256,
            "authority_family_templates_sha256": authority_family_templates_sha256,
            "component_inventory_sha256": component_inventory_sha256,
            "source_claims_sha256": _optional_file_sha256(claims_path),
            "rule_claim_links_sha256": _optional_file_sha256(rule_claim_links_path),
            "rule_claim_gaps_sha256": _optional_file_sha256(rule_claim_gaps_path),
            "candidate_authorities": candidate_authorities,
        }
    )
    authority_universe_id = (
        f"authority-universe:{review_id}:{source_set_id}:{authority_universe_sha256[:16]}"
    )
    validation = _authority_universe_validation(
        source_set_id=source_set_id,
        rule_pack=base_rule_pack,
        rule_pack_validation=rule_pack_validation,
        candidate_authorities=candidate_authorities,
        profiles=profiles,
        component_inventory=component_inventory,
        authority_family_templates=authority_family_templates,
    )
    summary = _summary(
        authority_universe_id=authority_universe_id,
        authority_universe_sha256=authority_universe_sha256,
        review_id=review_id,
        source_set_id=source_set_id,
        base_rule_pack=base_rule_pack,
        source_set_manifest_path=source_set_manifest_path,
        source_catalog_path=source_catalog_path,
        forest_plan_profiles_path=forest_plan_profiles_path,
        forest_plan_component_inventory_path=forest_plan_component_inventory_path,
        claims_path=claims_path,
        rule_claim_links_path=rule_claim_links_path,
        rule_claim_gaps_path=rule_claim_gaps_path,
        authority_family_templates_path=authority_family_templates_path,
        candidate_authorities=candidate_authorities,
        validation=validation,
    )
    snapshot = {
        "schema_version": AUTHORITY_UNIVERSE_SCHEMA_VERSION,
        "created_at": created_at,
        "authority_universe_id": authority_universe_id,
        "authority_universe_version": "0.1.0",
        "authority_universe_sha256": authority_universe_sha256,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "source_set_manifest_sha256": _optional_file_sha256(source_set_manifest_path),
        "catalog_sha256": _optional_file_sha256(source_catalog_path),
        "base_rule_pack_id": base_rule_pack.get("rule_pack_id"),
        "base_rule_pack_version": base_rule_pack.get("version"),
        "base_rule_pack_sha256": base_rule_pack_sha256,
        "forest_plan_profiles_sha256": profiles_sha256,
        "forest_plan_profile_ids": _forest_plan_profile_ids(profiles),
        "authority_family_templates_sha256": authority_family_templates_sha256,
        "authority_family_template_set_id": (
            authority_family_templates.get("template_set_id")
            if isinstance(authority_family_templates, dict)
            else None
        ),
        "forest_plan_component_inventory_id": _component_inventory_id(component_inventory),
        "forest_plan_component_inventory_sha256": component_inventory_sha256,
        "source_claims_sha256": _optional_file_sha256(claims_path),
        "rule_claim_links_sha256": _optional_file_sha256(rule_claim_links_path),
        "rule_claim_gaps_sha256": _optional_file_sha256(rule_claim_gaps_path),
        "artifact_paths": {
            "source_set_manifest_path": str(source_set_manifest_path),
            "source_catalog_path": str(source_catalog_path),
            "base_rule_pack_path": str(base_rule_pack_path),
            "forest_plan_profiles_path": str(forest_plan_profiles_path),
            "authority_family_templates_path": (
                str(authority_family_templates_path)
                if authority_family_templates_path
                else None
            ),
            "forest_plan_component_inventory_path": (
                str(forest_plan_component_inventory_path)
                if forest_plan_component_inventory_path.exists()
                else None
            ),
            "claims_path": str(claims_path) if claims_path.exists() else None,
            "rule_claim_links_path": (
                str(rule_claim_links_path) if rule_claim_links_path.exists() else None
            ),
            "rule_claim_gaps_path": (
                str(rule_claim_gaps_path) if rule_claim_gaps_path.exists() else None
            ),
        },
        "summary": summary,
        "validation": validation,
        "candidate_authorities": candidate_authorities,
    }

    applicability_dir = output_dir / "reviews" / review_id / "applicability"
    snapshot_path = applicability_dir / "authority_universe_snapshot.json"
    _write_json(snapshot_path, snapshot)
    return AuthorityUniverseSnapshotResult(
        review_id=review_id,
        source_set_id=source_set_id,
        applicability_dir=applicability_dir,
        snapshot_path=snapshot_path,
        summary=summary,
    )


def _rule_template_candidates(
    *,
    source_set_id: str,
    rule_pack: dict,
    catalog_by_source_id: dict[str, dict],
    source_claim_links_by_rule: dict[str, list[dict]],
    source_claim_gaps_by_rule: dict[str, list[dict]],
) -> list[dict]:
    baseline_source_record_ids = _baseline_source_record_ids(rule_pack)
    candidates = []
    for rule in rule_pack.get("rules", []):
        rule_id = str(rule.get("id") or "")
        source_record_id = _rule_source_record_id(rule)
        catalog_record = catalog_by_source_id.get(source_record_id or "")
        source_claim_links = source_claim_links_by_rule.get(rule_id, [])
        source_claim_gaps = source_claim_gaps_by_rule.get(rule_id, [])
        document_role = _authority_document_role(rule, catalog_record)
        source_role_filters = _rule_source_role_filters(
            rule=rule,
            source_record_id=source_record_id,
            document_role=document_role,
        )
        package_section_filters = _rule_package_section_filters(rule)
        positive_trigger_groups = _rule_positive_trigger_groups(rule)
        negative_trigger_groups = _rule_negative_trigger_groups(rule)
        required_package_fact_types = _rule_required_package_fact_types(rule)
        candidates.append(
            {
                "candidate_authority_id": (
                    "rule-template:"
                    f"{rule_pack.get('rule_pack_id')}:{rule_pack.get('version')}:{rule_id}"
                ),
                "candidate_authority_type": "rule_template",
                "source_set_id": source_set_id,
                "authority_category": rule.get("authority_category"),
                "authority_document_role": document_role,
                "source_record_ids": [source_record_id] if source_record_id else [],
                "source_records": [_source_record_summary(catalog_record)]
                if catalog_record
                else [],
                "required_package_fact_types": required_package_fact_types,
                "positive_trigger_groups": positive_trigger_groups,
                "negative_trigger_groups": negative_trigger_groups,
                "source_role_filters": source_role_filters,
                "package_section_filters": package_section_filters,
                "required_source_evidence": _rule_required_source_evidence(
                    source_record_id=source_record_id,
                    document_role=document_role,
                    source_role_filters=source_role_filters,
                    source_claim_links=source_claim_links,
                    source_claim_gaps=source_claim_gaps,
                ),
                "retrieval_contract": _rule_retrieval_contract(
                    rule=rule,
                    rule_id=rule_id,
                    source_role_filters=source_role_filters,
                    package_section_filters=package_section_filters,
                ),
                "graph_expansion_contract": _rule_graph_expansion_contract(
                    rule=rule,
                    rule_id=rule_id,
                    source_record_id=source_record_id,
                ),
                "dependency_contract": _rule_dependency_contract(rule),
                "search_coverage_requirements": _rule_search_coverage_requirements(
                    rule=rule,
                    positive_trigger_groups=positive_trigger_groups,
                    negative_trigger_groups=negative_trigger_groups,
                ),
                "rule_template": {
                    "base_rule_pack_id": rule_pack.get("rule_pack_id"),
                    "base_rule_pack_version": rule_pack.get("version"),
                    "rule_id": rule_id,
                    "title": rule.get("title"),
                    "question": rule.get("question"),
                    "requirement": rule.get("requirement"),
                    "severity": rule.get("severity"),
                    "applicability_mode": rule.get("applicability_mode"),
                },
                "source_evidence_availability": _rule_source_evidence_availability(
                    catalog_record=catalog_record,
                    source_claim_links=source_claim_links,
                    source_claim_gaps=source_claim_gaps,
                ),
                "deterministic_applicability_test_contract": _rule_applicability_contract(
                    rule=rule,
                    baseline_source_record_ids=baseline_source_record_ids,
                ),
                "source_claim_link_ids": [
                    str(link.get("link_id"))
                    for link in source_claim_links
                    if link.get("link_id")
                ],
                "rule_claim_gap_ids": [
                    str(gap.get("gap_id")) for gap in source_claim_gaps if gap.get("gap_id")
                ],
            }
        )
    return candidates


def _authority_family_template_candidates(
    *,
    source_set_id: str,
    template_set: dict | None,
    catalog_by_source_id: dict[str, dict],
) -> list[dict]:
    if not isinstance(template_set, dict):
        return []
    templates = template_set.get("templates")
    if not isinstance(templates, list):
        return []
    candidates = []
    template_set_id = str(template_set.get("template_set_id") or "")
    template_set_version = str(template_set.get("version") or "")
    for template in templates:
        if not isinstance(template, dict):
            continue
        template_id = str(template.get("template_id") or "")
        family_id = str(template.get("authority_family_id") or "")
        rule_id = str(template.get("rule_id") or template_id)
        source_record_id = str(template.get("authority_source_record_id") or "").strip()
        catalog_record = catalog_by_source_id.get(source_record_id)
        document_role = _authority_family_document_role(template, catalog_record)
        authority_category = str(template.get("authority_category") or "").strip()
        source_record_ids = _template_source_record_ids(template, source_record_id)
        source_records = [
            _source_record_summary(catalog_by_source_id.get(record_id))
            for record_id in source_record_ids
            if catalog_by_source_id.get(record_id)
        ]
        source_role_filters = _authority_family_source_role_filters(
            template=template,
            source_record_ids=source_record_ids,
            document_role=document_role,
            authority_category=authority_category,
        )
        package_section_filters = _authority_family_package_section_filters(template)
        positive_trigger_groups = _authority_family_positive_trigger_groups(template)
        negative_trigger_groups = _authority_family_negative_trigger_groups(template)
        required_package_fact_types = _strings(template.get("package_fact_types"))
        candidates.append(
            {
                "candidate_authority_id": (
                    "authority-family-template:"
                    f"{template_set_id}:{template_set_version}:{family_id}:{rule_id}"
                ),
                "candidate_authority_type": "authority_family_rule_template",
                "source_set_id": source_set_id,
                "authority_family_id": family_id,
                "authority_category": authority_category,
                "authority_document_role": document_role,
                "source_record_ids": source_record_ids,
                "source_records": source_records,
                "required_package_fact_types": required_package_fact_types,
                "positive_trigger_groups": positive_trigger_groups,
                "negative_trigger_groups": negative_trigger_groups,
                "source_role_filters": source_role_filters,
                "package_section_filters": package_section_filters,
                "required_source_evidence": _authority_family_required_source_evidence(
                    template=template,
                    source_record_id=source_record_id,
                    document_role=document_role,
                    source_role_filters=source_role_filters,
                ),
                "retrieval_contract": _authority_family_retrieval_contract(
                    template=template,
                    rule_id=rule_id,
                    source_role_filters=source_role_filters,
                    package_section_filters=package_section_filters,
                ),
                "graph_expansion_contract": _authority_family_graph_expansion_contract(
                    template=template,
                    rule_id=rule_id,
                    source_record_id=source_record_id,
                ),
                "dependency_contract": _authority_family_dependency_contract(template),
                "search_coverage_requirements": _authority_family_search_coverage_requirements(
                    template=template,
                    positive_trigger_groups=positive_trigger_groups,
                    negative_trigger_groups=negative_trigger_groups,
                ),
                "rule_template": _authority_family_rule_template_metadata(
                    template=template,
                    template_set=template_set,
                    rule_id=rule_id,
                ),
                "source_evidence_availability": _authority_family_source_evidence_availability(
                    catalog_record=catalog_record,
                    source_records=source_records,
                ),
                "deterministic_applicability_test_contract": (
                    _authority_family_applicability_contract(template=template)
                ),
                "source_claim_link_ids": [],
                "rule_claim_gap_ids": [],
            }
        )
    return candidates


def _forest_plan_component_candidates(
    *,
    source_set_id: str,
    profiles: ForestPlanProfileCollection,
    component_inventory: dict | None,
    component_inventory_path: Path,
    component_inventory_sha256: str | None,
    catalog_by_source_id: dict[str, dict],
) -> list[dict]:
    if not isinstance(component_inventory, dict):
        return []
    if str(component_inventory.get("source_set_id") or "") != source_set_id:
        return []
    forest_unit_id = str(component_inventory.get("forest_unit_id") or "")
    try:
        profile = profiles.get(forest_unit_id)
    except KeyError:
        return []
    inventory_id = str(component_inventory.get("inventory_id") or "")
    components = component_inventory.get("components")
    if not isinstance(components, list):
        return []
    candidates = []
    for component in components:
        if not isinstance(component, dict):
            continue
        component_id = str(component.get("component_id") or "")
        source_record_id = str(
            component.get("source_record_id") or profile.active_plan_source_record_id
        )
        catalog_record = catalog_by_source_id.get(source_record_id)
        source_role_filters = _component_source_role_filters(
            source_record_id=source_record_id,
        )
        package_section_filters = _component_package_section_filters(component)
        positive_trigger_groups = _component_positive_trigger_groups(component)
        negative_trigger_groups = _component_negative_trigger_groups()
        required_package_fact_types = _component_required_package_fact_types(component)
        candidates.append(
            {
                "candidate_authority_id": (
                    f"forest-plan-component:{inventory_id}:{component_id}"
                ),
                "candidate_authority_type": "forest_plan_component",
                "source_set_id": source_set_id,
                "authority_category": "forest_plan",
                "authority_family_id": FOREST_PLAN_COMPONENT_AUTHORITY_FAMILY_ID,
                "authority_family_ids": [FOREST_PLAN_COMPONENT_AUTHORITY_FAMILY_ID],
                "authority_document_role": "forest_plan",
                "source_record_ids": [source_record_id] if source_record_id else [],
                "source_records": [_source_record_summary(catalog_record)]
                if catalog_record
                else [],
                "required_package_fact_types": required_package_fact_types,
                "positive_trigger_groups": positive_trigger_groups,
                "negative_trigger_groups": negative_trigger_groups,
                "source_role_filters": source_role_filters,
                "package_section_filters": package_section_filters,
                "required_source_evidence": _component_required_source_evidence(
                    source_record_id=source_record_id,
                    source_role_filters=source_role_filters,
                    component=component,
                ),
                "retrieval_contract": _component_retrieval_contract(
                    component=component,
                    component_id=component_id,
                    source_role_filters=source_role_filters,
                    package_section_filters=package_section_filters,
                ),
                "graph_expansion_contract": _component_graph_expansion_contract(
                    component=component,
                    component_id=component_id,
                    profile=profile,
                    inventory_id=inventory_id,
                ),
                "dependency_contract": _component_dependency_contract(profile),
                "search_coverage_requirements": _component_search_coverage_requirements(
                    component=component,
                    positive_trigger_groups=positive_trigger_groups,
                ),
                "forest_plan": {
                    "forest_unit_id": profile.forest_unit_id,
                    "forest_unit_names": list(profile.forest_unit_names),
                    "active_plan_source_record_id": profile.active_plan_source_record_id,
                    "profile_data_source": profile.profile_data_source,
                    "component_inventory_id": inventory_id,
                    "component_inventory_path": str(component_inventory_path),
                    "component_inventory_sha256": component_inventory_sha256,
                    "plan_version": component_inventory.get("plan_version"),
                    "component_id": component_id,
                    "component_type": component.get("component_type"),
                    "section_id": component.get("section_id"),
                    "section_heading": component.get("section_heading"),
                    "geographic_area_ids": component.get("geographic_area_ids", []),
                    "management_area_ids": component.get("management_area_ids", []),
                    "overlay_ids": component.get("overlay_ids", []),
                },
                "source_evidence_availability": _component_source_evidence_availability(
                    catalog_record=catalog_record,
                    component=component,
                ),
                "deterministic_applicability_test_contract": {
                    "contract_type": "forest_plan_component",
                    "component_type": component.get("component_type"),
                    "source_chunk_ids": component.get("source_chunk_ids", []),
                    "package_evidence_terms": component.get("package_evidence_terms", []),
                    "resource_topics": component.get("resource_topics", []),
                    "activity_tags": component.get("activity_tags", []),
                    "geographic_area_ids": component.get("geographic_area_ids", []),
                    "management_area_ids": component.get("management_area_ids", []),
                    "overlay_ids": component.get("overlay_ids", []),
                },
            }
        )
    return candidates


def _rule_source_evidence_availability(
    *,
    catalog_record: dict | None,
    source_claim_links: list[dict],
    source_claim_gaps: list[dict],
) -> dict:
    artifact_sha256 = str((catalog_record or {}).get("artifact_sha256") or "")
    source_status = str((catalog_record or {}).get("source_status") or "")
    catalog_present = catalog_record is not None
    return {
        "available": catalog_present and bool(artifact_sha256),
        "catalog_record_present": catalog_present,
        "artifact_sha256_present": bool(artifact_sha256),
        "source_status": source_status or None,
        "source_claim_link_count": len(source_claim_links),
        "rule_claim_gap_count": len(source_claim_gaps),
        "source_claim_linkage_recorded": bool(source_claim_links or source_claim_gaps),
        "rule_claim_gap_reasons": sorted(
            {
                str(gap.get("reason"))
                for gap in source_claim_gaps
                if gap.get("reason")
            }
        ),
    }


def _component_source_evidence_availability(
    *,
    catalog_record: dict | None,
    component: dict,
) -> dict:
    source_chunk_ids = [
        str(chunk_id)
        for chunk_id in component.get("source_chunk_ids", [])
        if str(chunk_id or "").strip()
    ]
    artifact_sha256 = str(component.get("artifact_sha256") or "")
    return {
        "available": catalog_record is not None and bool(source_chunk_ids) and bool(artifact_sha256),
        "catalog_record_present": catalog_record is not None,
        "artifact_sha256_present": bool(artifact_sha256),
        "source_chunk_count": len(source_chunk_ids),
        "source_status": str((catalog_record or {}).get("source_status") or "") or None,
    }


def _authority_family_source_evidence_availability(
    *,
    catalog_record: dict | None,
    source_records: list[dict],
) -> dict:
    return {
        "available": catalog_record is not None
        and bool(catalog_record.get("artifact_sha256")),
        "catalog_record_present": catalog_record is not None,
        "artifact_sha256_present": bool((catalog_record or {}).get("artifact_sha256")),
        "source_record_count": len(source_records),
        "source_status": str((catalog_record or {}).get("source_status") or "") or None,
        "source_claim_linkage_recorded": False,
        "source_claim_linkage_required": False,
    }


def _rule_required_package_fact_types(rule: dict) -> list[str]:
    fact_types = set(BASE_RULE_PACKAGE_FACT_TYPES)
    if rule.get("applicability_mode") == "conditional":
        fact_types.add("resource_topic")
    if rule.get("authority_category") == "forest_plan":
        fact_types.update({"geography", "management_area", "overlay"})
    return sorted(fact_types)


def _component_required_package_fact_types(component: dict) -> list[str]:
    fact_types = set(FOREST_PLAN_PACKAGE_FACT_TYPES)
    if not component.get("geographic_area_ids"):
        fact_types.discard("geography")
    if not component.get("management_area_ids"):
        fact_types.discard("management_area")
    if not component.get("overlay_ids"):
        fact_types.discard("overlay")
    return sorted(fact_types)


def _authority_family_document_role(
    template: dict,
    catalog_record: dict | None,
) -> str | None:
    filters = (
        template.get("source_filters")
        if isinstance(template.get("source_filters"), dict)
        else {}
    )
    value = (
        template.get("authority_document_role")
        or filters.get("document_role")
        or (catalog_record or {}).get("document_role")
    )
    return str(value).strip() if str(value or "").strip() else None


def _template_source_record_ids(template: dict, source_record_id: str) -> list[str]:
    explicit = _strings(template.get("source_record_ids"))
    if explicit:
        return explicit
    return _dedupe_strings(
        [
            source_record_id,
            *_strings(template.get("supporting_source_record_ids")),
            *_strings(template.get("excluded_source_record_ids")),
        ]
    )


def _authority_family_source_role_filters(
    *,
    template: dict,
    source_record_ids: list[str],
    document_role: str | None,
    authority_category: str | None,
) -> dict:
    source_filters = (
        template.get("source_filters")
        if isinstance(template.get("source_filters"), dict)
        else {}
    )
    supporting_source_record_ids = _strings(template.get("supporting_source_record_ids"))
    return {
        "source_record_ids": source_record_ids,
        "primary_source_record_id": template.get("authority_source_record_id"),
        "supporting_source_record_ids": supporting_source_record_ids,
        "excluded_source_record_ids": _strings(template.get("excluded_source_record_ids")),
        "document_roles": [document_role] if document_role else [],
        "authority_categories": _strings([authority_category]),
        "source_filters": source_filters,
    }


def _authority_family_package_section_filters(template: dict) -> dict:
    return {
        "package_query": template.get("package_query"),
        "package_terms": _strings(template.get("package_terms")),
        "package_section_terms": _strings(template.get("package_section_terms")),
        "package_section_term_groups": _string_groups(
            template.get("package_section_term_groups")
        ),
        "preferred_section_families": _strings(template.get("package_section_families")),
        "package_fact_types": _strings(template.get("package_fact_types")),
    }


def _authority_family_positive_trigger_groups(template: dict) -> list[list[str]]:
    groups = _string_groups(template.get("applies_if_package_term_groups"))
    terms = _strings(template.get("applies_if_package_terms"))
    if terms:
        groups.append(terms)
    if not groups:
        package_terms = _strings(template.get("package_terms"))
        if package_terms:
            groups.append(package_terms)
    return _dedupe_groups(groups)


def _authority_family_negative_trigger_groups(template: dict) -> list[list[str]]:
    return _dedupe_groups(
        [[term] for term in _strings(template.get("does_not_apply_if_package_terms"))]
    )


def _authority_family_required_source_evidence(
    *,
    template: dict,
    source_record_id: str | None,
    document_role: str | None,
    source_role_filters: dict,
) -> dict:
    return {
        "source_record_ids": _template_source_record_ids(template, source_record_id or ""),
        "primary_source_record_id": source_record_id,
        "supporting_source_record_ids": _strings(template.get("supporting_source_record_ids")),
        "excluded_source_record_ids": _strings(template.get("excluded_source_record_ids")),
        "document_roles": [document_role] if document_role else [],
        "source_role_filters": source_role_filters,
        "requires_catalog_record": True,
        "requires_artifact_sha256": True,
        "requires_source_record": True,
        "requires_source_claim_linkage": False,
        "source_evidence_requirements": _strings(template.get("source_evidence_requirements")),
    }


def _authority_family_retrieval_contract(
    *,
    template: dict,
    rule_id: str,
    source_role_filters: dict,
    package_section_filters: dict,
) -> dict:
    return {
        "contract_type": "authority_family_rule_template_retrieval",
        "query_plan_id": f"retrieval-plan:authority-family-template:{rule_id}",
        "required_query_types": [
            "exact_keyword",
            "bm25",
            "metadata_filter",
            "package_section",
            "source_role",
        ],
        "optional_query_types": ["vector"],
        "source_queries": _strings([template.get("source_query")]),
        "package_queries": _strings([template.get("package_query")]),
        "source_role_filters": source_role_filters,
        "package_section_filters": package_section_filters,
        "fused_ranking_strategy": "reciprocal_rank_fusion",
        "requires_selected_and_rejected_results": True,
        "searched_index_hash_required": True,
    }


def _authority_family_graph_expansion_contract(
    *,
    template: dict,
    rule_id: str,
    source_record_id: str | None,
) -> dict:
    dependency_contract = _authority_family_dependency_contract(template)
    return {
        "contract_type": "authority_family_rule_template_graph_expansion",
        "start_node_types": ["authority_family_rule_template", "source_record", "authority"],
        "relationship_types": list(RULE_GRAPH_RELATIONSHIP_TYPES),
        "max_depth": 2,
        "requires_path_trace": True,
        "required_graph_artifact_types": [
            "source_graph",
            "evidence_graph",
            "claim_graph",
            "authority_family_template_graph",
        ],
        "neighbor_filters": {
            "rule_ids": [rule_id] if rule_id else [],
            "authority_family_ids": _strings([template.get("authority_family_id")]),
            "source_record_ids": _template_source_record_ids(
                template,
                source_record_id or "",
            ),
            "authority_categories": _strings([template.get("authority_category")]),
            "supporting_source_record_ids": dependency_contract[
                "supporting_source_record_ids"
            ],
            "superseded_by_family_ids": dependency_contract["superseded_by_family_ids"],
        },
    }


def _authority_family_dependency_contract(template: dict) -> dict:
    dependency = (
        template.get("dependency_contract")
        if isinstance(template.get("dependency_contract"), dict)
        else {}
    )
    supersession = (
        template.get("supersession")
        if isinstance(template.get("supersession"), dict)
        else {}
    )
    return {
        "dependency_rule_ids": _strings(dependency.get("dependency_rule_ids")),
        "dependency_family_ids": _strings(dependency.get("dependency_family_ids")),
        "exception_rule_ids": _strings(dependency.get("exception_rule_ids")),
        "exception_family_ids": _strings(dependency.get("exception_family_ids")),
        "supersedes_rule_ids": _strings(dependency.get("supersedes_rule_ids")),
        "superseded_by_rule_ids": _strings(dependency.get("superseded_by_rule_ids")),
        "superseded_by_family_ids": _strings(
            dependency.get("superseded_by_family_ids")
        )
        or _strings([supersession.get("replacement_family_id")]),
        "supporting_source_record_ids": _strings(template.get("supporting_source_record_ids")),
        "excluded_source_record_ids": _strings(template.get("excluded_source_record_ids")),
        "supersession": supersession or None,
    }


def _authority_family_search_coverage_requirements(
    *,
    template: dict,
    positive_trigger_groups: list[list[str]],
    negative_trigger_groups: list[list[str]],
) -> list[dict]:
    base = {
        "required_artifacts": [
            "package_fact_graph",
            "applicability_retrieval_trace",
            "applicability_graph_trace",
            "search_coverage_certificates",
        ],
        "required_query_types": ["exact_keyword", "bm25", "metadata_filter", "package_section"],
        "requires_searched_index_hash": True,
        "required_package_fact_types": _strings(template.get("package_fact_types")),
    }
    requirements = [
        {
            **base,
            "coverage_class": "authority_family_positive_trigger_miss",
            "required_trigger_groups": positive_trigger_groups,
        }
    ]
    if negative_trigger_groups:
        requirements.append(
            {
                **base,
                "coverage_class": "authority_family_explicit_negative_trigger",
                "required_trigger_groups": negative_trigger_groups,
            }
        )
    return requirements


def _authority_family_rule_template_metadata(
    *,
    template: dict,
    template_set: dict,
    rule_id: str,
) -> dict:
    return {
        "base_rule_pack_id": template_set.get("base_rule_pack_id"),
        "base_rule_pack_version": template_set.get("base_rule_pack_version"),
        "authority_family_template_set_id": template_set.get("template_set_id"),
        "authority_family_template_set_version": template_set.get("version"),
        "template_id": template.get("template_id"),
        "authority_family_id": template.get("authority_family_id"),
        "rule_id": rule_id,
        "title": template.get("title"),
        "question": template.get("question"),
        "requirement": template.get("requirement"),
        "severity": template.get("severity"),
        "applicability_mode": template.get("applicability_mode"),
        "authority_source_record_id": template.get("authority_source_record_id"),
        "authority_category": template.get("authority_category"),
        "package_query": template.get("package_query"),
        "package_terms": _strings(template.get("package_terms")),
        "package_section_terms": _strings(template.get("package_section_terms")),
        "applies_if_package_terms": _strings(template.get("applies_if_package_terms")),
        "applies_if_package_term_groups": _string_groups(
            template.get("applies_if_package_term_groups")
        ),
        "does_not_apply_if_package_terms": _strings(
            template.get("does_not_apply_if_package_terms")
        ),
        "source_query": template.get("source_query"),
        "source_filters": (
            template.get("source_filters")
            if isinstance(template.get("source_filters"), dict)
            else {}
        ),
        "evidence_expectation": template.get("evidence_expectation"),
    }


def _authority_family_applicability_contract(*, template: dict) -> dict:
    return {
        "contract_type": "rule_template",
        "candidate_authority_type": "authority_family_rule_template",
        "authority_family_id": template.get("authority_family_id"),
        "applicability_mode": template.get("applicability_mode"),
        "baseline_required": False,
        "baseline_source_record_ids": [],
        "package_query": template.get("package_query"),
        "package_terms": _strings(template.get("package_terms")),
        "package_section_terms": _strings(template.get("package_section_terms")),
        "package_section_term_groups": _string_groups(
            template.get("package_section_term_groups")
        ),
        "positive_package_terms": _strings(template.get("applies_if_package_terms")),
        "positive_package_term_groups": _string_groups(
            template.get("applies_if_package_term_groups")
        ),
        "negative_package_terms": _strings(
            template.get("does_not_apply_if_package_terms")
        ),
        "source_query": template.get("source_query"),
        "source_filters": (
            template.get("source_filters")
            if isinstance(template.get("source_filters"), dict)
            else {}
        ),
        "source_evidence_requirements": _strings(template.get("source_evidence_requirements")),
        "evidence_expectation": template.get("evidence_expectation"),
    }


def _rule_applicability_contract(
    *,
    rule: dict,
    baseline_source_record_ids: list[str],
) -> dict:
    source_record_id = _rule_source_record_id(rule)
    return {
        "contract_type": "rule_template",
        "applicability_mode": rule.get("applicability_mode"),
        "baseline_required": source_record_id in baseline_source_record_ids,
        "baseline_source_record_ids": baseline_source_record_ids,
        "package_query": rule.get("package_query"),
        "package_terms": rule.get("package_terms", []),
        "package_section_terms": rule.get("package_section_terms", []),
        "package_section_term_groups": rule.get("package_section_term_groups", []),
        "positive_package_terms": rule.get("applies_if_package_terms", []),
        "positive_package_term_groups": rule.get("applies_if_package_term_groups", []),
        "negative_package_terms": rule.get("does_not_apply_if_package_terms", []),
        "source_query": rule.get("source_query"),
        "source_filters": rule.get("source_filters", {}),
        "evidence_expectation": rule.get("evidence_expectation"),
    }


def _rule_positive_trigger_groups(rule: dict) -> list[list[str]]:
    groups = _string_groups(rule.get("applies_if_package_term_groups"))
    explicit_terms = _strings(rule.get("applies_if_package_terms"))
    if explicit_terms:
        groups.append(explicit_terms)
    if not groups:
        package_terms = _strings(rule.get("package_terms"))
        if package_terms:
            groups.append(package_terms)
    if not groups:
        package_query = str(rule.get("package_query") or "").strip()
        if package_query:
            groups.append([package_query])
    return groups


def _rule_negative_trigger_groups(rule: dict) -> list[list[str]]:
    terms = _strings(rule.get("does_not_apply_if_package_terms"))
    return [[term] for term in terms]


def _component_positive_trigger_groups(component: dict) -> list[list[str]]:
    groups = []
    package_terms = _strings(component.get("package_evidence_terms"))
    if package_terms:
        groups.append(package_terms)
    resource_topics = _strings(component.get("resource_topics"))
    if resource_topics:
        groups.append(resource_topics)
    activity_tags = _strings(component.get("activity_tags"))
    if activity_tags:
        groups.append(activity_tags)
    component_type = str(component.get("component_type") or "").strip()
    if not groups and component_type:
        groups.append([component_type])
    return groups


def _component_negative_trigger_groups() -> list[list[str]]:
    return [["not part of the project area"]]


def _rule_source_role_filters(
    *,
    rule: dict,
    source_record_id: str | None,
    document_role: str | None,
) -> dict:
    source_filters = rule.get("source_filters") if isinstance(rule.get("source_filters"), dict) else {}
    return {
        "source_record_ids": [source_record_id] if source_record_id else [],
        "document_roles": [document_role] if document_role else [],
        "authority_categories": _strings([rule.get("authority_category")]),
        "source_filters": source_filters,
    }


def _component_source_role_filters(*, source_record_id: str | None) -> dict:
    return {
        "source_record_ids": [source_record_id] if source_record_id else [],
        "document_roles": ["forest_plan"],
        "authority_categories": ["forest_plan"],
        "source_filters": {
            "document_role": "forest_plan",
            "source_record_id": source_record_id,
        },
    }


def _rule_package_section_filters(rule: dict) -> dict:
    return {
        "package_query": rule.get("package_query"),
        "package_terms": _strings(rule.get("package_terms")),
        "package_section_terms": _strings(rule.get("package_section_terms")),
        "package_section_term_groups": _string_groups(rule.get("package_section_term_groups")),
        "preferred_section_families": _strings(rule.get("package_section_families")),
    }


def _component_package_section_filters(component: dict) -> dict:
    return {
        "component_section_id": component.get("section_id"),
        "component_section_heading": component.get("section_heading"),
        "package_evidence_terms": _strings(component.get("package_evidence_terms")),
        "resource_topics": _strings(component.get("resource_topics")),
        "activity_tags": _strings(component.get("activity_tags")),
        "geographic_area_ids": _strings(component.get("geographic_area_ids")),
        "management_area_ids": _strings(component.get("management_area_ids")),
        "overlay_ids": _strings(component.get("overlay_ids")),
    }


def _rule_required_source_evidence(
    *,
    source_record_id: str | None,
    document_role: str | None,
    source_role_filters: dict,
    source_claim_links: list[dict],
    source_claim_gaps: list[dict],
) -> dict:
    return {
        "source_record_ids": [source_record_id] if source_record_id else [],
        "document_roles": [document_role] if document_role else [],
        "source_role_filters": source_role_filters,
        "requires_catalog_record": True,
        "requires_artifact_sha256": True,
        "requires_source_claim_linkage": True,
        "source_claim_link_ids": [
            str(link.get("link_id"))
            for link in source_claim_links
            if str(link.get("link_id") or "").strip()
        ],
        "rule_claim_gap_ids": [
            str(gap.get("gap_id"))
            for gap in source_claim_gaps
            if str(gap.get("gap_id") or "").strip()
        ],
    }


def _component_required_source_evidence(
    *,
    source_record_id: str | None,
    source_role_filters: dict,
    component: dict,
) -> dict:
    return {
        "source_record_ids": [source_record_id] if source_record_id else [],
        "document_roles": ["forest_plan"],
        "source_role_filters": source_role_filters,
        "requires_catalog_record": True,
        "requires_artifact_sha256": True,
        "requires_source_chunks": True,
        "source_chunk_ids": _strings(component.get("source_chunk_ids")),
    }


def _rule_retrieval_contract(
    *,
    rule: dict,
    rule_id: str,
    source_role_filters: dict,
    package_section_filters: dict,
) -> dict:
    return {
        "contract_type": "rule_template_retrieval",
        "query_plan_id": f"retrieval-plan:rule-template:{rule_id}",
        "required_query_types": [
            "exact_keyword",
            "bm25",
            "metadata_filter",
            "package_section",
            "source_role",
        ],
        "optional_query_types": ["vector"],
        "source_queries": _strings([rule.get("source_query")]),
        "package_queries": _strings([rule.get("package_query")]),
        "source_role_filters": source_role_filters,
        "package_section_filters": package_section_filters,
        "fused_ranking_strategy": "reciprocal_rank_fusion",
        "requires_selected_and_rejected_results": True,
        "searched_index_hash_required": True,
    }


def _component_retrieval_contract(
    *,
    component: dict,
    component_id: str,
    source_role_filters: dict,
    package_section_filters: dict,
) -> dict:
    query_terms = _strings(component.get("package_evidence_terms")) or _strings(
        [component.get("section_heading")]
    )
    return {
        "contract_type": "forest_plan_component_retrieval",
        "query_plan_id": f"retrieval-plan:forest-plan-component:{component_id}",
        "required_query_types": [
            "exact_keyword",
            "bm25",
            "metadata_filter",
            "package_section",
            "source_role",
        ],
        "optional_query_types": ["vector"],
        "source_queries": _strings([component.get("section_heading")]),
        "package_queries": query_terms,
        "source_role_filters": source_role_filters,
        "package_section_filters": package_section_filters,
        "fused_ranking_strategy": "reciprocal_rank_fusion",
        "requires_selected_and_rejected_results": True,
        "searched_index_hash_required": True,
    }


def _rule_graph_expansion_contract(
    *,
    rule: dict,
    rule_id: str,
    source_record_id: str | None,
) -> dict:
    return {
        "contract_type": "rule_template_graph_expansion",
        "start_node_types": ["rule_template", "source_record", "authority"],
        "relationship_types": list(RULE_GRAPH_RELATIONSHIP_TYPES),
        "max_depth": 2,
        "requires_path_trace": True,
        "required_graph_artifact_types": [
            "source_graph",
            "evidence_graph",
            "claim_graph",
            "rule_claim_graph",
        ],
        "neighbor_filters": {
            "rule_ids": [rule_id] if rule_id else [],
            "source_record_ids": [source_record_id] if source_record_id else [],
            "authority_categories": _strings([rule.get("authority_category")]),
        },
    }


def _component_graph_expansion_contract(
    *,
    component: dict,
    component_id: str,
    profile: object,
    inventory_id: str,
) -> dict:
    return {
        "contract_type": "forest_plan_component_graph_expansion",
        "start_node_types": ["forest_plan_component", "source_record", "package_fact"],
        "relationship_types": list(FOREST_PLAN_GRAPH_RELATIONSHIP_TYPES),
        "max_depth": 3,
        "requires_path_trace": True,
        "required_graph_artifact_types": [
            "source_graph",
            "evidence_graph",
            "forest_plan_component_inventory",
        ],
        "neighbor_filters": {
            "forest_unit_id": getattr(profile, "forest_unit_id", None),
            "component_inventory_id": inventory_id,
            "component_ids": [component_id] if component_id else [],
            "geographic_area_ids": _strings(component.get("geographic_area_ids")),
            "management_area_ids": _strings(component.get("management_area_ids")),
            "overlay_ids": _strings(component.get("overlay_ids")),
        },
    }


def _rule_dependency_contract(rule: dict) -> dict:
    return {
        "dependency_rule_ids": _strings(
            rule.get("dependency_rule_ids")
            or rule.get("depends_on_rule_ids")
            or rule.get("dependencies")
        ),
        "exception_rule_ids": _strings(
            rule.get("exception_rule_ids") or rule.get("exceptions")
        ),
        "supersedes_rule_ids": _strings(rule.get("supersedes_rule_ids")),
        "superseded_by_rule_ids": _strings(rule.get("superseded_by_rule_ids")),
        "supporting_source_record_ids": _strings(rule.get("supporting_source_record_ids")),
    }


def _component_dependency_contract(profile: object) -> dict:
    supporting_records = [
        {
            "role": record.role,
            "source_record_id": record.source_record_id,
            "required_for": record.required_for,
        }
        for record in getattr(profile, "supporting_source_records", ())
    ]
    return {
        "dependency_rule_ids": [],
        "exception_rule_ids": [],
        "supersedes_rule_ids": [],
        "superseded_by_rule_ids": [],
        "supporting_source_record_ids": sorted(
            {record["source_record_id"] for record in supporting_records}
        ),
        "supporting_source_records": supporting_records,
    }


def _rule_search_coverage_requirements(
    *,
    rule: dict,
    positive_trigger_groups: list[list[str]],
    negative_trigger_groups: list[list[str]],
) -> list[dict]:
    base = {
        "required_artifacts": [
            "package_fact_graph",
            "applicability_retrieval_trace",
            "search_coverage_certificates",
        ],
        "required_query_types": ["exact_keyword", "bm25", "metadata_filter", "package_section"],
        "requires_searched_index_hash": True,
    }
    if rule.get("applicability_mode") == "conditional":
        requirements = [
            {
                **base,
                "coverage_class": "positive_trigger_miss",
                "required_trigger_groups": positive_trigger_groups,
            }
        ]
        if negative_trigger_groups:
            requirements.append(
                {
                    **base,
                    "coverage_class": "explicit_negative_trigger",
                    "required_trigger_groups": negative_trigger_groups,
                }
            )
        return requirements
    return [
        {
            **base,
            "coverage_class": "baseline_exclusion_requires_adjudication",
            "requires_adjudication_for_not_applicable": True,
        }
    ]


def _component_search_coverage_requirements(
    *,
    component: dict,
    positive_trigger_groups: list[list[str]],
) -> list[dict]:
    base = {
        "required_artifacts": [
            "package_fact_graph",
            "applicability_retrieval_trace",
            "applicability_graph_trace",
            "search_coverage_certificates",
        ],
        "required_query_types": ["exact_keyword", "bm25", "metadata_filter", "package_section"],
        "requires_searched_index_hash": True,
    }
    return [
        {
            **base,
            "coverage_class": "forest_plan_scope_miss",
            "required_package_fact_types": _component_required_package_fact_types(component),
        },
        {
            **base,
            "coverage_class": "component_trigger_miss",
            "required_trigger_groups": positive_trigger_groups,
        },
    ]


def _authority_universe_validation(
    *,
    source_set_id: str,
    rule_pack: dict,
    rule_pack_validation: dict,
    candidate_authorities: list[dict],
    profiles: ForestPlanProfileCollection,
    component_inventory: dict | None,
    authority_family_templates: dict | None,
) -> dict:
    checks = [
        {
            "name": "rule_pack_valid",
            "passed": bool(rule_pack_validation.get("passed")),
            "details": {
                "failed_checks": [
                    check.get("name")
                    for check in rule_pack_validation.get("checks", [])
                    if not check.get("passed")
                ],
            },
        },
        _check_candidate_ids_unique(candidate_authorities),
        _check_rule_template_candidates_cover_rule_pack(rule_pack, candidate_authorities),
        _check_conditional_rule_candidates_present(rule_pack, candidate_authorities),
        _check_source_record_provenance(candidate_authorities),
        _check_candidate_authority_metadata(candidate_authorities),
        _check_source_evidence_available(candidate_authorities),
        _check_source_claim_linkage_recorded(candidate_authorities),
        _check_applicability_contracts(candidate_authorities),
        _check_candidate_pre_review_contracts(candidate_authorities),
        _check_authority_family_template_candidates(
            authority_family_templates=authority_family_templates,
            candidate_authorities=candidate_authorities,
        ),
        _check_forest_plan_component_candidates(
            source_set_id=source_set_id,
            rule_pack=rule_pack,
            candidate_authorities=candidate_authorities,
            profiles=profiles,
            component_inventory=component_inventory,
        ),
    ]
    return {
        "schema_version": "authority-universe-validation-v0",
        "created_at": _utc_now(),
        "source_set_id": source_set_id,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def _check_candidate_ids_unique(candidate_authorities: list[dict]) -> dict:
    counts = Counter(
        str(candidate.get("candidate_authority_id") or "")
        for candidate in candidate_authorities
    )
    duplicates = sorted(
        candidate_id
        for candidate_id, count in counts.items()
        if candidate_id and count > 1
    )
    missing = sum(1 for candidate_id in counts if not candidate_id)
    return {
        "name": "candidate_authority_ids_unique",
        "passed": not duplicates and missing == 0,
        "details": {
            "candidate_count": len(candidate_authorities),
            "duplicate_candidate_authority_ids": duplicates,
            "missing_candidate_authority_id_count": missing,
        },
    }


def _check_rule_template_candidates_cover_rule_pack(
    rule_pack: dict,
    candidate_authorities: list[dict],
) -> dict:
    expected = {str(rule.get("id") or "") for rule in rule_pack.get("rules", [])}
    actual = {
        str(candidate.get("rule_template", {}).get("rule_id") or "")
        for candidate in candidate_authorities
        if candidate.get("candidate_authority_type") == "rule_template"
    }
    return {
        "name": "rule_template_candidates_cover_rule_pack",
        "passed": expected == actual and bool(expected),
        "details": {
            "expected_rule_count": len(expected),
            "actual_rule_candidate_count": len(actual),
            "missing_rule_ids": sorted(expected - actual),
            "unexpected_rule_ids": sorted(actual - expected),
        },
    }


def _check_conditional_rule_candidates_present(
    rule_pack: dict,
    candidate_authorities: list[dict],
) -> dict:
    expected = {
        str(rule.get("id") or "")
        for rule in rule_pack.get("rules", [])
        if rule.get("applicability_mode") == "conditional"
    }
    actual = {
        str(candidate.get("rule_template", {}).get("rule_id") or "")
        for candidate in candidate_authorities
        if candidate.get("candidate_authority_type") == "rule_template"
        and candidate.get("rule_template", {}).get("applicability_mode") == "conditional"
    }
    return {
        "name": "conditional_rule_candidates_present",
        "passed": expected == actual,
        "details": {
            "expected_conditional_rule_count": len(expected),
            "actual_conditional_candidate_count": len(actual),
            "missing_conditional_rule_ids": sorted(expected - actual),
        },
    }


def _check_source_record_provenance(candidate_authorities: list[dict]) -> dict:
    failures = [
        candidate.get("candidate_authority_id")
        for candidate in candidate_authorities
        if not candidate.get("source_record_ids")
    ]
    return {
        "name": "candidates_have_source_record_provenance",
        "passed": not failures,
        "details": {"candidate_authority_ids": failures[:50], "failure_count": len(failures)},
    }


def _check_candidate_authority_metadata(candidate_authorities: list[dict]) -> dict:
    failures = []
    for candidate in candidate_authorities:
        missing = []
        if not str(candidate.get("authority_category") or "").strip():
            missing.append("authority_category")
        if not str(candidate.get("authority_document_role") or "").strip():
            missing.append("authority_document_role")
        if missing:
            failures.append(
                {
                    "candidate_authority_id": candidate.get("candidate_authority_id"),
                    "missing": missing,
                }
            )
    return {
        "name": "candidates_have_authority_metadata",
        "passed": not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_source_evidence_available(candidate_authorities: list[dict]) -> dict:
    failures = [
        candidate.get("candidate_authority_id")
        for candidate in candidate_authorities
        if not candidate.get("source_evidence_availability", {}).get("available")
    ]
    return {
        "name": "candidates_have_source_evidence_available",
        "passed": not failures,
        "details": {"candidate_authority_ids": failures[:50], "failure_count": len(failures)},
    }


def _check_source_claim_linkage_recorded(candidate_authorities: list[dict]) -> dict:
    failures = [
        candidate.get("candidate_authority_id")
        for candidate in candidate_authorities
        if candidate.get("candidate_authority_type") == "rule_template"
        and not candidate.get("source_evidence_availability", {}).get(
            "source_claim_linkage_recorded"
        )
    ]
    return {
        "name": "rule_template_candidates_have_source_claim_linkage",
        "passed": not failures,
        "details": {"candidate_authority_ids": failures[:50], "failure_count": len(failures)},
    }


def _check_applicability_contracts(candidate_authorities: list[dict]) -> dict:
    failures = [
        candidate.get("candidate_authority_id")
        for candidate in candidate_authorities
        if not _has_applicability_contract(candidate)
    ]
    return {
        "name": "candidates_have_deterministic_applicability_contracts",
        "passed": not failures,
        "details": {"candidate_authority_ids": failures[:50], "failure_count": len(failures)},
    }


def _check_candidate_pre_review_contracts(candidate_authorities: list[dict]) -> dict:
    required_fields = (
        "required_package_fact_types",
        "positive_trigger_groups",
        "negative_trigger_groups",
        "source_role_filters",
        "package_section_filters",
        "required_source_evidence",
        "retrieval_contract",
        "graph_expansion_contract",
        "dependency_contract",
        "search_coverage_requirements",
    )
    failures = []
    for candidate in candidate_authorities:
        missing = [
            field
            for field in required_fields
            if not _candidate_contract_field_present(candidate, field)
        ]
        if not _valid_retrieval_contract(candidate.get("retrieval_contract")):
            missing.append("valid_retrieval_contract")
        if not _valid_graph_expansion_contract(candidate.get("graph_expansion_contract")):
            missing.append("valid_graph_expansion_contract")
        if not _valid_search_coverage_requirements(
            candidate.get("search_coverage_requirements")
        ):
            missing.append("valid_search_coverage_requirements")
        if missing:
            failures.append(
                {
                    "candidate_authority_id": candidate.get("candidate_authority_id"),
                    "missing_or_invalid": sorted(set(missing)),
                }
            )
    return {
        "name": "candidates_have_pre_review_contracts",
        "passed": not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_authority_family_template_candidates(
    *,
    authority_family_templates: dict | None,
    candidate_authorities: list[dict],
) -> dict:
    if not isinstance(authority_family_templates, dict):
        return {
            "name": "authority_family_template_candidates_cover_config",
            "passed": True,
            "details": {"configured": False, "expected_template_count": 0},
        }
    templates = [
        template
        for template in authority_family_templates.get("templates", [])
        if isinstance(template, dict)
    ]
    expected_rule_ids = {str(template.get("rule_id") or "") for template in templates}
    actual_rule_ids = {
        str(candidate.get("rule_template", {}).get("rule_id") or "")
        for candidate in candidate_authorities
        if candidate.get("candidate_authority_type") == "authority_family_rule_template"
    }
    missing_predicates = [
        template.get("template_id")
        for template in templates
        if not (
            _strings(template.get("applies_if_package_terms"))
            or _string_groups(template.get("applies_if_package_term_groups"))
        )
    ]
    missing_negative_triggers = [
        template.get("template_id")
        for template in templates
        if not _strings(template.get("does_not_apply_if_package_terms"))
    ]
    candidates_without_family = [
        candidate.get("candidate_authority_id")
        for candidate in candidate_authorities
        if candidate.get("candidate_authority_type") == "authority_family_rule_template"
        and not candidate.get("authority_family_id")
    ]
    missing_source_records = []
    for candidate in candidate_authorities:
        if candidate.get("candidate_authority_type") != "authority_family_rule_template":
            continue
        expected_source_ids = set(_strings(candidate.get("source_record_ids")))
        actual_source_ids = {
            str(record.get("source_record_id") or "")
            for record in candidate.get("source_records") or []
            if isinstance(record, dict) and record.get("source_record_id")
        }
        missing = sorted(expected_source_ids - actual_source_ids)
        if missing:
            missing_source_records.append(
                {
                    "candidate_authority_id": candidate.get("candidate_authority_id"),
                    "source_record_ids": missing,
                }
            )
    passed = (
        expected_rule_ids == actual_rule_ids
        and bool(expected_rule_ids)
        and not missing_predicates
        and not missing_negative_triggers
        and not candidates_without_family
        and not missing_source_records
    )
    return {
        "name": "authority_family_template_candidates_cover_config",
        "passed": passed,
        "details": {
            "configured": True,
            "expected_template_count": len(expected_rule_ids),
            "actual_template_candidate_count": len(actual_rule_ids),
            "missing_rule_ids": sorted(expected_rule_ids - actual_rule_ids),
            "unexpected_rule_ids": sorted(actual_rule_ids - expected_rule_ids),
            "missing_predicate_template_ids": missing_predicates,
            "missing_negative_trigger_template_ids": missing_negative_triggers,
            "candidates_without_authority_family_id": candidates_without_family,
            "missing_source_records": missing_source_records[:50],
            "missing_source_record_count": len(missing_source_records),
        },
    }


def _check_forest_plan_component_candidates(
    *,
    source_set_id: str,
    rule_pack: dict,
    candidate_authorities: list[dict],
    profiles: ForestPlanProfileCollection,
    component_inventory: dict | None,
) -> dict:
    forest_plan_rule_source_ids = {
        _rule_source_record_id(rule)
        for rule in rule_pack.get("rules", [])
        if rule.get("authority_category") == "forest_plan"
    }
    profile_source_ids = {
        profile.active_plan_source_record_id
        for profile in profiles.profiles
    }
    inventory_profile_source_id = None
    inventory_forest_unit_id = ""
    if isinstance(component_inventory, dict):
        inventory_forest_unit_id = str(component_inventory.get("forest_unit_id") or "")
        if inventory_forest_unit_id:
            try:
                inventory_profile_source_id = profiles.get(
                    inventory_forest_unit_id
                ).active_plan_source_record_id
            except KeyError:
                inventory_profile_source_id = None
    required = bool(
        inventory_profile_source_id
        and inventory_profile_source_id in forest_plan_rule_source_ids
        and inventory_profile_source_id in profile_source_ids
    )
    component_candidates = [
        candidate
        for candidate in candidate_authorities
        if candidate.get("candidate_authority_type") == "forest_plan_component"
    ]
    component_records = (
        component_inventory.get("components", [])
        if isinstance(component_inventory, dict)
        and component_inventory.get("source_set_id") == source_set_id
        and required
        and isinstance(component_inventory.get("components"), list)
        else []
    )
    passed = (not required and not component_candidates) or (
        bool(component_records) and len(component_candidates) == len(component_records)
    )
    return {
        "name": "forest_plan_component_candidates_use_profile_inventory",
        "passed": passed,
        "details": {
            "required": required,
            "forest_plan_rule_source_record_ids": sorted(
                source_id for source_id in forest_plan_rule_source_ids if source_id
            ),
            "profile_active_plan_source_record_ids": sorted(profile_source_ids),
            "inventory_forest_unit_id": inventory_forest_unit_id or None,
            "inventory_profile_source_record_id": inventory_profile_source_id,
            "component_inventory_present": bool(component_records),
            "component_inventory_count": len(component_records),
            "component_candidate_count": len(component_candidates),
        },
    }


def _has_applicability_contract(candidate: dict) -> bool:
    contract = candidate.get("deterministic_applicability_test_contract")
    if not isinstance(contract, dict):
        return False
    contract_type = contract.get("contract_type")
    if contract_type == "rule_template":
        mode = str(contract.get("applicability_mode") or "")
        if not contract.get("package_query") or not contract.get("source_query"):
            return False
        if not contract.get("source_filters"):
            return False
        if mode == "conditional":
            return bool(
                contract.get("positive_package_terms")
                or contract.get("positive_package_term_groups")
            )
        return mode == "baseline"
    if contract_type == "forest_plan_component":
        return bool(
            contract.get("component_type")
            and contract.get("source_chunk_ids")
            and (contract.get("package_evidence_terms") or contract.get("resource_topics"))
        )
    return False


def _candidate_contract_field_present(candidate: dict, field: str) -> bool:
    value = candidate.get(field)
    if isinstance(value, dict):
        return bool(value)
    if isinstance(value, list):
        if field == "negative_trigger_groups":
            return True
        return bool(value)
    return value is not None


def _valid_retrieval_contract(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    return bool(
        value.get("contract_type")
        and value.get("required_query_types")
        and value.get("source_role_filters")
        and value.get("package_section_filters")
        and value.get("requires_selected_and_rejected_results") is True
        and value.get("searched_index_hash_required") is True
    )


def _valid_graph_expansion_contract(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    return bool(
        value.get("contract_type")
        and value.get("start_node_types")
        and value.get("relationship_types")
        and value.get("max_depth")
        and value.get("requires_path_trace") is True
    )


def _valid_search_coverage_requirements(value: object) -> bool:
    if not isinstance(value, list) or not value:
        return False
    for requirement in value:
        if not isinstance(requirement, dict):
            return False
        if not requirement.get("coverage_class"):
            return False
        if not requirement.get("required_query_types"):
            return False
        if not requirement.get("required_artifacts"):
            return False
    return True


def _summary(
    *,
    authority_universe_id: str,
    authority_universe_sha256: str,
    review_id: str,
    source_set_id: str,
    base_rule_pack: dict,
    source_set_manifest_path: Path,
    source_catalog_path: Path,
    forest_plan_profiles_path: Path,
    forest_plan_component_inventory_path: Path,
    claims_path: Path,
    rule_claim_links_path: Path,
    rule_claim_gaps_path: Path,
    authority_family_templates_path: Path | None,
    candidate_authorities: list[dict],
    validation: dict,
) -> dict:
    type_counts = Counter(
        str(candidate.get("candidate_authority_type") or "")
        for candidate in candidate_authorities
    )
    applicability_modes = Counter(
        str(candidate.get("rule_template", {}).get("applicability_mode") or "")
        for candidate in candidate_authorities
        if candidate.get("candidate_authority_type") == "rule_template"
    )
    authority_family_template_modes = Counter(
        str(candidate.get("rule_template", {}).get("applicability_mode") or "")
        for candidate in candidate_authorities
        if candidate.get("candidate_authority_type") == "authority_family_rule_template"
    )
    return {
        "schema_version": "authority-universe-summary-v0",
        "authority_universe_id": authority_universe_id,
        "authority_universe_sha256": authority_universe_sha256,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "base_rule_pack_id": base_rule_pack.get("rule_pack_id"),
        "base_rule_pack_version": base_rule_pack.get("version"),
        "base_rule_count": len(base_rule_pack.get("rules", [])),
        "candidate_authority_count": len(candidate_authorities),
        "rule_template_candidate_count": type_counts.get("rule_template", 0),
        "authority_family_rule_template_candidate_count": type_counts.get(
            "authority_family_rule_template",
            0,
        ),
        "forest_plan_component_candidate_count": type_counts.get("forest_plan_component", 0),
        "candidate_type_counts": dict(type_counts),
        "rule_applicability_mode_counts": {
            key: value for key, value in dict(applicability_modes).items() if key
        },
        "authority_family_template_applicability_mode_counts": {
            key: value
            for key, value in dict(authority_family_template_modes).items()
            if key
        },
        "candidate_contract_counts": _candidate_contract_counts(candidate_authorities),
        "source_set_manifest_path": str(source_set_manifest_path),
        "source_catalog_path": str(source_catalog_path),
        "forest_plan_profiles_path": str(forest_plan_profiles_path),
        "forest_plan_component_inventory_path": (
            str(forest_plan_component_inventory_path)
            if forest_plan_component_inventory_path.exists()
            else None
        ),
        "claims_path": str(claims_path) if claims_path.exists() else None,
        "rule_claim_links_path": (
            str(rule_claim_links_path) if rule_claim_links_path.exists() else None
        ),
        "rule_claim_gaps_path": (
            str(rule_claim_gaps_path) if rule_claim_gaps_path.exists() else None
        ),
        "authority_family_templates_path": (
            str(authority_family_templates_path) if authority_family_templates_path else None
        ),
        "validation_passed": bool(validation.get("passed")),
        "passed": bool(validation.get("passed")),
    }


def _candidate_contract_counts(candidate_authorities: list[dict]) -> dict:
    return {
        "with_required_package_fact_types": sum(
            1 for candidate in candidate_authorities if candidate.get("required_package_fact_types")
        ),
        "with_retrieval_contract": sum(
            1 for candidate in candidate_authorities if candidate.get("retrieval_contract")
        ),
        "with_graph_expansion_contract": sum(
            1 for candidate in candidate_authorities if candidate.get("graph_expansion_contract")
        ),
        "with_dependency_contract": sum(
            1 for candidate in candidate_authorities if candidate.get("dependency_contract")
        ),
        "with_search_coverage_requirements": sum(
            1
            for candidate in candidate_authorities
            if candidate.get("search_coverage_requirements")
        ),
    }


def _source_record_summary(record: dict | None) -> dict:
    if not record:
        return {}
    return {
        "source_record_id": record.get("source_record_id"),
        "title": record.get("title"),
        "citation_label": record.get("citation_label"),
        "document_role": record.get("document_role"),
        "authority_level": record.get("authority_level"),
        "issuer": record.get("issuer"),
        "scope": record.get("scope"),
        "layer": record.get("layer"),
        "document_type": record.get("document_type"),
        "unit_or_overlay": record.get("unit_or_overlay"),
        "applies_to": record.get("applies_to"),
        "trigger": record.get("trigger"),
        "review_topics": record.get("review_topics", []),
        "currentness_notes": record.get("currentness_notes"),
        "source_status": record.get("source_status"),
        "artifact_sha256": record.get("artifact_sha256"),
        "artifact_path": record.get("artifact_path"),
        "artifact_byte_size": record.get("artifact_byte_size"),
        "content_type": record.get("content_type"),
        "retrieved_at": record.get("retrieved_at"),
    }


def _forest_plan_profile_ids(profiles: ForestPlanProfileCollection) -> list[str]:
    return sorted(profile.forest_unit_id for profile in profiles.profiles)


def _component_inventory_id(component_inventory: dict | None) -> str | None:
    if not isinstance(component_inventory, dict):
        return None
    value = str(component_inventory.get("inventory_id") or "").strip()
    return value or None


def _load_authority_family_templates(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing authority-family templates: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Authority-family templates must be a JSON object.")
    if value.get("schema_version") != AUTHORITY_FAMILY_RULE_TEMPLATES_SCHEMA_VERSION:
        raise ValueError(
            "Authority-family templates schema_version must be "
            f"{AUTHORITY_FAMILY_RULE_TEMPLATES_SCHEMA_VERSION}."
        )
    templates = value.get("templates")
    if not isinstance(templates, list) or not templates:
        raise ValueError("Authority-family templates must contain a non-empty templates list.")
    failures = []
    seen_rule_ids = set()
    for index, template in enumerate(templates):
        if not isinstance(template, dict):
            failures.append({"index": index, "missing": ["template_object"]})
            continue
        required = {
            "template_id",
            "authority_family_id",
            "rule_id",
            "title",
            "authority_category",
            "authority_source_record_id",
            "applicability_mode",
            "question",
            "requirement",
            "severity",
            "package_query",
            "package_terms",
            "source_query",
            "source_filters",
            "evidence_expectation",
        }
        missing = sorted(
            field for field in required if not _template_field_present(template, field)
        )
        if not (
            _strings(template.get("applies_if_package_terms"))
            or _string_groups(template.get("applies_if_package_term_groups"))
        ):
            missing.append("positive_applicability_predicate")
        if not _strings(template.get("does_not_apply_if_package_terms")):
            missing.append("does_not_apply_if_package_terms")
        if not _strings(template.get("package_fact_types")):
            missing.append("package_fact_types")
        rule_id = str(template.get("rule_id") or "")
        if rule_id in seen_rule_ids:
            missing.append("unique_rule_id")
        seen_rule_ids.add(rule_id)
        if missing:
            failures.append(
                {
                    "index": index,
                    "template_id": template.get("template_id"),
                    "missing_or_invalid": sorted(set(missing)),
                }
            )
    if failures:
        raise ValueError(
            "Authority-family templates are invalid: "
            + json.dumps(failures[:20], sort_keys=True)
        )
    return value


def _template_field_present(template: dict, field: str) -> bool:
    value = template.get(field)
    if isinstance(value, dict):
        return bool(value)
    if isinstance(value, list):
        return any(str(item or "").strip() for item in value)
    return bool(str(value or "").strip())


def _load_source_catalog(path: Path, source_set_id: str) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Missing source catalog: {path}")
    records = _read_jsonl(path)
    filtered = [
        record
        for record in records
        if str(record.get("source_set_id") or "") == source_set_id
    ]
    if not filtered:
        raise ValueError(f"No source catalog records found for source set: {source_set_id}")
    return filtered


def _source_set_id_from_manifest(path: Path, manifest: dict) -> str:
    value = manifest.get("source_set_id")
    if not str(value or "").strip():
        raise ValueError(f"Missing source_set_id in source-set manifest: {path}")
    return str(value).strip()


def _default_forest_plan_component_inventory_path(output_dir: Path, source_set_id: str) -> Path:
    return (
        output_dir
        / "derived"
        / source_set_id
        / "forest_plan_components"
        / "component_inventory.json"
    )


def _records_by_key(records: list[dict], key: str) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        value = str(record.get(key) or "")
        if value:
            grouped[value].append(record)
    return dict(grouped)


def _authority_document_role(rule: dict, catalog_record: dict | None) -> str | None:
    filters = rule.get("source_filters") if isinstance(rule.get("source_filters"), dict) else {}
    value = (
        rule.get("authority_document_role")
        or filters.get("document_role")
        or (catalog_record or {}).get("document_role")
    )
    return str(value).strip() if str(value or "").strip() else None


def _rule_source_record_id(rule: dict) -> str | None:
    filters = rule.get("source_filters") if isinstance(rule.get("source_filters"), dict) else {}
    value = rule.get("authority_source_record_id") or filters.get("source_record_id")
    return str(value).strip() if str(value or "").strip() else None


def _baseline_source_record_ids(rule_pack: dict) -> list[str]:
    raw = rule_pack.get("baseline_source_record_ids")
    if not isinstance(raw, list):
        return []
    return [str(value).strip() for value in raw if str(value or "").strip()]


def _strings(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            if isinstance(item, (list, tuple)):
                values.extend(_strings(item))
                continue
            text = str(item or "").strip()
            if text:
                values.append(text)
        return values
    text = str(value or "").strip()
    return [text] if text else []


def _dedupe_strings(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in _strings(values):
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _dedupe_groups(groups: list[list[str]]) -> list[list[str]]:
    seen = set()
    result = []
    for group in groups:
        normalized = tuple(_strings(group))
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(list(normalized))
    return result


def _string_groups(value: object) -> list[list[str]]:
    if not isinstance(value, list):
        return []
    groups = []
    for item in value:
        if isinstance(item, list):
            group = _strings(item)
            if group:
                groups.append(group)
            continue
        text = str(item or "").strip()
        if text:
            groups.append([text])
    return groups


def _validate_safe_segment(value: str, field_name: str) -> None:
    if not SAFE_SEGMENT_RE.fullmatch(str(value or "")):
        raise ValueError(
            f"{field_name} must contain only letters, numbers, dots, underscores, or hyphens."
        )


def _optional_file_sha256(path: Path) -> str | None:
    return sha256_file(path) if path.exists() else None


def _stable_sha256(value: dict) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _read_json_if_exists(path: Path) -> dict | None:
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return value


def _read_jsonl(path: Path) -> list[dict]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"Expected JSON object lines in {path}")
        records.append(value)
    return records


def _read_jsonl_if_exists(path: Path) -> list[dict]:
    return _read_jsonl(path) if path.exists() else []


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
