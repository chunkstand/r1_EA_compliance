from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import hashlib
import json
import re

from .claim_extraction import default_claims_path
from .compliance_review import DEFAULT_RULE_PACK_PATH
from .compliance_review import load_rule_pack
from .compliance_review import validate_rule_pack
from .forest_plan_profiles import DEFAULT_FOREST_PLAN_PROFILES_PATH
from .forest_plan_profiles import ForestPlanProfileCollection
from .forest_plan_profiles import load_forest_plan_profiles
from .records import sha256_file
from .rule_claim_binding import default_rule_claim_links_path


AUTHORITY_UNIVERSE_SCHEMA_VERSION = "authority-universe-snapshot-v0"
SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


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
    base_rule_pack_path: Path = DEFAULT_RULE_PACK_PATH,
    forest_plan_profiles_path: Path = DEFAULT_FOREST_PLAN_PROFILES_PATH,
    forest_plan_component_inventory_path: Path | None = None,
    claims_path: Path | None = None,
    rule_claim_links_path: Path | None = None,
) -> AuthorityUniverseSnapshotResult:
    """Build the candidate authority universe used by applicability determination."""

    output_dir = Path(output_dir)
    _validate_safe_segment(review_id, "review_id")
    catalog_dir = output_dir / "catalog"
    source_set_manifest_path = catalog_dir / "source_set_manifest.json"
    source_catalog_path = catalog_dir / "source_catalog.jsonl"
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
    component_candidates = _forest_plan_component_candidates(
        source_set_id=source_set_id,
        profiles=profiles,
        component_inventory=component_inventory,
        component_inventory_path=forest_plan_component_inventory_path,
        component_inventory_sha256=component_inventory_sha256,
        catalog_by_source_id=catalog_by_source_id,
    )
    candidate_authorities = sorted(
        [*rule_candidates, *component_candidates],
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
        candidates.append(
            {
                "candidate_authority_id": (
                    f"forest-plan-component:{inventory_id}:{component_id}"
                ),
                "candidate_authority_type": "forest_plan_component",
                "source_set_id": source_set_id,
                "authority_category": "forest_plan",
                "authority_document_role": "forest_plan",
                "source_record_ids": [source_record_id] if source_record_id else [],
                "source_records": [_source_record_summary(catalog_record)]
                if catalog_record
                else [],
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


def _authority_universe_validation(
    *,
    source_set_id: str,
    rule_pack: dict,
    rule_pack_validation: dict,
    candidate_authorities: list[dict],
    profiles: ForestPlanProfileCollection,
    component_inventory: dict | None,
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
    required = bool(forest_plan_rule_source_ids & profile_source_ids)
    component_candidates = [
        candidate
        for candidate in candidate_authorities
        if candidate.get("candidate_authority_type") == "forest_plan_component"
    ]
    component_records = (
        component_inventory.get("components", [])
        if isinstance(component_inventory, dict)
        and component_inventory.get("source_set_id") == source_set_id
        and isinstance(component_inventory.get("components"), list)
        else []
    )
    passed = (not required and not component_records) or (
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
        "forest_plan_component_candidate_count": type_counts.get("forest_plan_component", 0),
        "candidate_type_counts": dict(type_counts),
        "rule_applicability_mode_counts": {
            key: value for key, value in dict(applicability_modes).items() if key
        },
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
        "validation_passed": bool(validation.get("passed")),
        "passed": bool(validation.get("passed")),
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
