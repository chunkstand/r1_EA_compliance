from __future__ import annotations

from pathlib import Path

from .applicability_gate_graph import APPLICABILITY_GATE_GRAPH_CONTRACT_SCHEMA_VERSION
from .applicability_gate_graph import APPLICABILITY_GATE_GRAPH_SCHEMA_VERSION
from .applicability_gate_graph import ApplicabilityGateGraphResult
from .applicability_gate_graph import DEFAULT_APPLICABILITY_GATE_GRAPH_CONTRACT_PATH
from .applicability_gate_graph import build_applicability_gate_graph as _build_applicability_gate_graph
from .applicability_authority_universe_builder import AUTHORITY_FAMILY_RULE_TEMPLATES_SCHEMA_VERSION
from .applicability_authority_universe_builder import AUTHORITY_UNIVERSE_SCHEMA_VERSION
from .applicability_authority_universe_builder import AuthorityUniverseSnapshotResult
from .applicability_authority_universe_builder import DEFAULT_AUTHORITY_FAMILY_TEMPLATES_PATH
from .applicability_authority_universe_builder import build_authority_universe_snapshot as _build_authority_universe_snapshot
from .forest_plan_profiles import DEFAULT_FOREST_PLAN_PROFILES_PATH
from .rule_packs import DEFAULT_RULE_PACK_PATH

__all__ = [
    "APPLICABILITY_GATE_GRAPH_CONTRACT_SCHEMA_VERSION",
    "APPLICABILITY_GATE_GRAPH_SCHEMA_VERSION",
    "AUTHORITY_FAMILY_RULE_TEMPLATES_SCHEMA_VERSION",
    "AUTHORITY_UNIVERSE_SCHEMA_VERSION",
    "ApplicabilityGateGraphResult",
    "AuthorityUniverseSnapshotResult",
    "DEFAULT_APPLICABILITY_GATE_GRAPH_CONTRACT_PATH",
    "DEFAULT_AUTHORITY_FAMILY_TEMPLATES_PATH",
    "build_applicability_gate_graph",
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


def build_applicability_gate_graph(
    *,
    output_dir: Path,
    review_id: str,
    source_set_id: str | None = None,
    gate_graph_contract_path: Path = DEFAULT_APPLICABILITY_GATE_GRAPH_CONTRACT_PATH,
    authority_inventory_path: Path | None = None,
    authority_universe_path: Path | None = None,
    decisions_path: Path | None = None,
    output_path: Path | None = None,
) -> ApplicabilityGateGraphResult:
    kwargs = {
        "output_dir": Path(output_dir),
        "review_id": review_id,
        "source_set_id": source_set_id,
        "gate_graph_contract_path": gate_graph_contract_path,
        "authority_universe_path": authority_universe_path,
        "decisions_path": decisions_path,
        "output_path": output_path,
    }
    if authority_inventory_path is not None:
        kwargs["authority_inventory_path"] = authority_inventory_path
    return _build_applicability_gate_graph(**kwargs)
