from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import hashlib
import json
import re

from .applicability_authority_family_templates import authority_family_template_candidates
from .applicability_authority_universe_contracts import authority_universe_summary
from .applicability_authority_universe_contracts import authority_universe_validation
from .applicability_authority_universe_contracts import component_inventory_id
from .applicability_authority_universe_contracts import forest_plan_profile_ids
from .applicability_candidate_assembly import forest_plan_component_candidates
from .applicability_candidate_assembly import rule_template_candidates
from .applicability_contract_support import string_groups as _string_groups
from .applicability_contract_support import strings as _strings
from .claim_extraction import default_claims_path
from .forest_plan_profiles import DEFAULT_FOREST_PLAN_PROFILES_PATH
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
    rule_candidates = rule_template_candidates(
        source_set_id=source_set_id,
        rule_pack=base_rule_pack,
        catalog_by_source_id=catalog_by_source_id,
        source_claim_links_by_rule=source_claim_links_by_rule,
        source_claim_gaps_by_rule=source_claim_gaps_by_rule,
    )
    authority_family_candidates = authority_family_template_candidates(
        source_set_id=source_set_id,
        template_set=authority_family_templates,
        catalog_by_source_id=catalog_by_source_id,
    )
    forest_plan_rule_source_ids = _forest_plan_rule_source_record_ids(base_rule_pack)
    component_candidates = forest_plan_component_candidates(
        source_set_id=source_set_id,
        profiles=profiles,
        component_inventory=component_inventory,
        component_inventory_path=forest_plan_component_inventory_path,
        component_inventory_sha256=component_inventory_sha256,
        catalog_by_source_id=catalog_by_source_id,
        allowed_forest_plan_source_record_ids=forest_plan_rule_source_ids,
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
    validation = authority_universe_validation(
        created_at=created_at,
        source_set_id=source_set_id,
        rule_pack=base_rule_pack,
        rule_pack_validation=rule_pack_validation,
        candidate_authorities=candidate_authorities,
        profiles=profiles,
        component_inventory=component_inventory,
        authority_family_templates=authority_family_templates,
    )
    summary = authority_universe_summary(
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
        "forest_plan_profile_ids": forest_plan_profile_ids(profiles),
        "authority_family_templates_sha256": authority_family_templates_sha256,
        "authority_family_template_set_id": (
            authority_family_templates.get("template_set_id")
            if isinstance(authority_family_templates, dict)
            else None
        ),
        "forest_plan_component_inventory_id": component_inventory_id(component_inventory),
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
    if filtered:
        return filtered
    fallback_records = _catalog_records_from_extraction_manifest(path, source_set_id)
    if fallback_records:
        return fallback_records
    raise ValueError(f"No source catalog records found for source set: {source_set_id}")


def _catalog_records_from_extraction_manifest(
    catalog_path: Path,
    source_set_id: str,
) -> list[dict]:
    extraction_manifest_path = (
        catalog_path.parent.parent
        / "derived"
        / source_set_id
        / "diagnostics"
        / "extraction_manifest.jsonl"
    )
    if not extraction_manifest_path.exists():
        return []
    records = _read_jsonl(extraction_manifest_path)
    filtered = [
        record
        for record in records
        if str(record.get("source_set_id") or "") == source_set_id
    ]
    if not filtered:
        return []
    catalog_by_source_record_id: dict[str, dict] = {}
    for record in filtered:
        source_record_id = str(record.get("source_record_id") or "").strip()
        if not source_record_id:
            continue
        catalog_by_source_record_id[source_record_id] = _catalog_record_from_extraction_record(
            record
        )
    return list(catalog_by_source_record_id.values())


def _catalog_record_from_extraction_record(record: dict) -> dict:
    artifact_sha256 = str(record.get("artifact_sha256") or "").strip()
    artifact_path = str(record.get("artifact_path") or "").strip()
    return {
        "source_set_id": record.get("source_set_id"),
        "source_record_id": record.get("source_record_id"),
        "title": record.get("title"),
        "citation_label": record.get("citation_label"),
        "document_role": record.get("document_role"),
        "authority_level": record.get("authority_level"),
        "issuer": None,
        "scope": None,
        "layer": None,
        "document_type": None,
        "unit_or_overlay": None,
        "applies_to": None,
        "trigger": None,
        "review_topics": [],
        "currentness_notes": None,
        "source_status": record.get("source_status") or record.get("status"),
        "artifact_sha256": artifact_sha256 or None,
        "artifact_path": artifact_path or None,
        "artifact_byte_size": record.get("artifact_byte_size"),
        "content_type": record.get("content_type"),
        "retrieved_at": record.get("retrieved_at"),
    }


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


def _forest_plan_rule_source_record_ids(rule_pack: dict) -> set[str]:
    return {
        str(rule.get("authority_source_record_id") or "").strip()
        for rule in rule_pack.get("rules", [])
        if rule.get("authority_category") == "forest_plan"
        and str(rule.get("authority_source_record_id") or "").strip()
    }


def _records_by_key(records: list[dict], key: str) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        value = str(record.get(key) or "")
        if value:
            grouped[value].append(record)
    return dict(grouped)


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
