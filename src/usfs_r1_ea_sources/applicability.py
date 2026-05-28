from __future__ import annotations

from pathlib import Path

from .applicability_authority_universe_builder import AUTHORITY_FAMILY_RULE_TEMPLATES_SCHEMA_VERSION
from .applicability_authority_universe_builder import AUTHORITY_UNIVERSE_SCHEMA_VERSION
from .applicability_authority_universe_builder import AuthorityUniverseSnapshotResult
from .applicability_authority_universe_builder import DEFAULT_AUTHORITY_FAMILY_TEMPLATES_PATH
from .applicability_authority_universe_builder import build_authority_universe_snapshot as _build_authority_universe_snapshot
from .forest_plan_profiles import DEFAULT_FOREST_PLAN_PROFILES_PATH
from .rule_packs import DEFAULT_RULE_PACK_PATH

__all__ = [
    "AUTHORITY_FAMILY_RULE_TEMPLATES_SCHEMA_VERSION",
    "AUTHORITY_UNIVERSE_SCHEMA_VERSION",
    "AuthorityUniverseSnapshotResult",
    "DEFAULT_AUTHORITY_FAMILY_TEMPLATES_PATH",
    "build_authority_universe_snapshot",
]


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
    forest_unit_id: str | None = None,
    claims_path: Path | None = None,
    rule_claim_links_path: Path | None = None,
) -> AuthorityUniverseSnapshotResult:
    return _build_authority_universe_snapshot(
        output_dir=Path(output_dir),
        review_id=review_id,
        source_set_id=source_set_id,
        source_catalog_path=source_catalog_path,
        source_set_manifest_path=source_set_manifest_path,
        base_rule_pack_path=base_rule_pack_path,
        forest_plan_profiles_path=forest_plan_profiles_path,
        authority_family_templates_path=authority_family_templates_path,
        forest_plan_component_inventory_path=forest_plan_component_inventory_path,
        forest_unit_id=forest_unit_id,
        claims_path=claims_path,
        rule_claim_links_path=rule_claim_links_path,
    )
