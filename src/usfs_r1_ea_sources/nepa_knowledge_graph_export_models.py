from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json
from typing import Any

from .nepa_3d_graph_contract import NEPA_3D_GRAPH_SCHEMA_VERSION
from .records import sha256_file


DEFAULT_AUTHORITY_INVENTORY_PATH = Path("config/authority_universe_families_nepa_ea_v1.json")
DEFAULT_AUTHORITY_FAMILY_RULE_TEMPLATES_PATH = Path(
    "config/authority_family_rule_templates_nepa_ea_v1.json"
)
DEFAULT_FOREST_PLAN_PROFILES_PATH = Path("config/forest_plan_profiles.json")
DEFAULT_REGION1_FOREST_PLAN_READINESS_PATH = Path(
    "config/region1_forest_plan_readiness_nepa_3d_v1.json"
)
REGION1_FOREST_PLAN_READINESS_SCHEMA_VERSION = "region1-forest-plan-readiness-v1"
SOURCE_DELTA_READINESS_SCHEMA_VERSION = "r1-forest-plan-source-delta-readiness-v3"

SOURCE_SET_EXPORT_SCHEMA_VERSION = NEPA_3D_GRAPH_SCHEMA_VERSION
BASE_RULE_NODE_PREFIX = "rule_template:base"
AUTHORITY_TEMPLATE_NODE_PREFIX = "rule_template:authority_family"
REQUIRED_REVIEW_ARTIFACT_INPUT_NAMES = (
    "review_authority_universe_snapshot",
    "review_package_fact_graph",
    "review_applicability_retrieval_trace",
    "review_applicability_graph_trace",
    "review_applicability_decisions",
    "review_search_coverage_certificates",
    "review_generated_rule_pack",
    "review_compliance_matrix",
    "review_finding_graph_nodes",
    "review_finding_graph_edges",
)


@dataclass(frozen=True)
class NepaKnowledgeGraphExportResult:
    source_set_id: str
    graph_dir: Path
    graph_path: Path
    nodes_path: Path
    edges_path: Path
    summary_path: Path
    validation_path: Path
    summary: dict[str, Any]


class _GraphBuilder:
    def __init__(self) -> None:
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: dict[str, dict[str, Any]] = {}

    def add_node(
        self,
        *,
        node_id: str,
        node_type: str,
        label: str,
        display_status: str,
        review_readiness_status: str,
        readiness_semantic_class: str | None = None,
        provenance: dict[str, Any],
        currentness_metadata: dict[str, Any] | None = None,
        readiness_blockers: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        record = {
            "node_id": node_id,
            "node_type": node_type,
            "label": label,
            "display_status": display_status,
            "review_readiness_status": review_readiness_status,
            "readiness_semantic_class": readiness_semantic_class
            or _default_node_readiness_semantic_class(
                node_type=node_type,
                display_status=display_status,
            ),
            "provenance": _compact_dict(provenance),
            "currentness_metadata": _compact_dict(currentness_metadata or {}),
            "readiness_blockers": sorted(set(readiness_blockers or [])),
        }
        if metadata:
            record["metadata"] = _compact_dict(metadata)

        existing = self.nodes.get(node_id)
        if existing is None:
            self.nodes[node_id] = record
            return node_id

        existing["provenance"] = {
            **existing.get("provenance", {}),
            **record.get("provenance", {}),
        }
        existing["currentness_metadata"] = {
            **existing.get("currentness_metadata", {}),
            **record.get("currentness_metadata", {}),
        }
        existing["readiness_blockers"] = sorted(
            set(existing.get("readiness_blockers", [])) | set(record.get("readiness_blockers", []))
        )
        existing["readiness_semantic_class"] = (
            readiness_semantic_class
            or _default_node_readiness_semantic_class(
                node_type=str(existing.get("node_type") or node_type),
                display_status=str(existing.get("display_status") or display_status),
            )
        )
        if metadata:
            existing["metadata"] = {**existing.get("metadata", {}), **record["metadata"]}
        return node_id

    def add_edge(
        self,
        *,
        edge_type: str,
        source_node_id: str,
        target_node_id: str,
        display_status: str,
        review_readiness_status: str,
        readiness_semantic_class: str | None = None,
        provenance: dict[str, Any],
        readiness_blockers: list[str] | None = None,
        edge_key: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        edge_id = "edge:" + _stable_digest(
            edge_key or edge_type,
            source_node_id,
            target_node_id,
            json.dumps(_compact_dict(provenance), sort_keys=True),
        )
        if edge_id in self.edges:
            return edge_id
        record = {
            "edge_id": edge_id,
            "edge_type": edge_type,
            "source_node_id": source_node_id,
            "target_node_id": target_node_id,
            "display_status": display_status,
            "review_readiness_status": review_readiness_status,
            "readiness_semantic_class": readiness_semantic_class
            or _default_edge_readiness_semantic_class(
                display_status=display_status,
                target_node_type=str(
                    _dict(self.nodes.get(target_node_id)).get("node_type") or ""
                ),
            ),
            "provenance": _compact_dict(provenance),
            "readiness_blockers": sorted(set(readiness_blockers or [])),
        }
        if metadata:
            record["metadata"] = _compact_dict(metadata)
        self.edges[edge_id] = record
        return edge_id

    def update_node(
        self,
        node_id: str,
        *,
        display_status: str | None = None,
        review_readiness_status: str | None = None,
        readiness_semantic_class: str | None = None,
        provenance: dict[str, Any] | None = None,
        readiness_blockers: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        record = self.nodes.get(node_id)
        if record is None:
            return
        if display_status:
            record["display_status"] = display_status
        if review_readiness_status:
            record["review_readiness_status"] = review_readiness_status
        record["readiness_semantic_class"] = readiness_semantic_class or _default_node_readiness_semantic_class(
            node_type=str(record.get("node_type") or ""),
            display_status=str(record.get("display_status") or ""),
        )
        if provenance:
            record["provenance"] = {
                **record.get("provenance", {}),
                **_compact_dict(provenance),
            }
        if readiness_blockers:
            record["readiness_blockers"] = sorted(
                set(record.get("readiness_blockers", [])) | set(readiness_blockers)
            )
        if metadata:
            record["metadata"] = {**record.get("metadata", {}), **_compact_dict(metadata)}

    def sorted_nodes(self) -> list[dict[str, Any]]:
        return [self.nodes[node_id] for node_id in sorted(self.nodes)]

    def sorted_edges(self) -> list[dict[str, Any]]:
        return [self.edges[edge_id] for edge_id in sorted(self.edges)]


def _default_node_readiness_semantic_class(*, node_type: str, display_status: str) -> str:
    if node_type == "readiness_blocker":
        return "synthetic_blocker_node"
    if display_status == "readiness_blocked":
        return "blocked_domain_node"
    return "none"


def _default_edge_readiness_semantic_class(*, display_status: str, target_node_type: str) -> str:
    if target_node_type == "readiness_blocker":
        return "blocker_relationship_edge"
    if display_status == "readiness_blocked":
        return "blocked_relationship_edge"
    return "none"


def _empty_rule_pack() -> dict[str, Any]:
    return {
        "schema_version": "compliance-rule-pack-v0",
        "rule_pack_id": "canonical-source-register-semantic-graph",
        "version": "0.0.0",
        "title": "Canonical semantic graph placeholder rule pack",
        "rules": [],
    }


def _empty_template_config() -> dict[str, Any]:
    return {
        "schema_version": "authority-family-rule-templates-v1",
        "base_rule_pack_id": "canonical-source-register-semantic-graph",
        "base_rule_pack_version": "0.0.0",
        "templates": [],
    }


def _empty_forest_plan_profiles() -> dict[str, Any]:
    return {
        "schema_version": "forest-plan-profiles-v0",
        "known_other_forest_units": [],
        "profiles": [],
    }


def _empty_region1_forest_plan_readiness(*, source_set_id: str) -> dict[str, Any]:
    return {
        "schema_version": REGION1_FOREST_PLAN_READINESS_SCHEMA_VERSION,
        "readiness_matrix_id": "canonical-source-register-semantic-graph",
        "source_set_id": source_set_id,
        "region1_completeness_claim": False,
        "field_directive_requirements": [],
        "overlay_requirements": [],
        "profile_rows": [],
    }


def _semantic_label(semantic_id: str) -> str:
    label = semantic_id.split(":", 1)[-1]
    label = label.replace("#section:", " section ")
    return label.replace("-", " ").strip() or semantic_id


def _input_records(paths_by_name: dict[str, Path]) -> list[dict[str, Any]]:
    records = []
    for name, path in sorted(paths_by_name.items()):
        path = Path(path)
        records.append(
            {
                "name": name,
                "path": str(path),
                "exists": path.exists(),
                "sha256": _sha256_or_none(path),
            }
        )
    return records


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
    return records


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _jsonl_count(path: Path) -> int:
    with Path(path).open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def _jsonl_count_if_exists(path: Path) -> int:
    path = Path(path)
    if not path.exists():
        return 0
    return _jsonl_count(path)


def _sha256_or_none(path: Path) -> str | None:
    return sha256_file(path) if Path(path).exists() else None


def _source_set_node_id(source_set_id: str) -> str:
    return f"source_set:{source_set_id}"


def _review_node_id(review_id: str) -> str:
    return f"review:{review_id}"


def _family_node_id(family_id: str) -> str:
    return f"authority_family:{family_id}"


def _source_node_id(source_record_id: str) -> str:
    return f"source_record:{source_record_id}"


def _artifact_node_id(artifact_sha256: str) -> str:
    return f"artifact:{artifact_sha256}"


def _forest_unit_node_id(forest_unit_id: str) -> str:
    return f"forest_unit:{forest_unit_id}"


def _decision_node_id(review_id: str, decision: dict[str, Any]) -> str:
    decision_id = str(decision.get("decision_id") or "")
    if decision_id:
        return f"applicability_decision:{review_id}:{decision_id}"
    return f"applicability_decision:{review_id}:{_stable_digest(decision)}"


def _generated_rule_node_id(review_id: str, generated_rule_id: str) -> str:
    return f"generated_rule:{review_id}:{generated_rule_id}"


def _compliance_finding_node_id(review_id: str, finding_id: str) -> str:
    return f"compliance_finding:{review_id}:{finding_id}"


def _review_blocker_node_id(review_id: str, blocker_type: str, decision: dict[str, Any]) -> str:
    return f"readiness_blocker:{review_id}:{blocker_type}:{_stable_digest(decision)}"


def _review_evidence_node_id(
    review_id: str,
    finding_id: str,
    evidence_kind: str,
    evidence: dict[str, Any],
) -> str:
    return f"evidence_span:review:{review_id}:{finding_id}:{evidence_kind}:{_stable_digest(evidence)}"


def _candidate_authority_node_id(
    candidate: dict[str, Any],
    *,
    base_rule_node_ids: dict[str, str],
    template_node_ids: dict[str, str],
) -> str:
    candidate_type = str(candidate.get("candidate_authority_type") or "")
    candidate_id = str(candidate.get("candidate_authority_id") or "")
    if candidate_type == "forest_plan_component":
        forest_plan = _dict(candidate.get("forest_plan"))
        component_id = str(forest_plan.get("component_id") or candidate_id.rsplit(":", 1)[-1])
        return f"forest_plan_component:{component_id}"
    rule_id = _candidate_rule_id(candidate)
    return (
        base_rule_node_ids.get(rule_id)
        or template_node_ids.get(rule_id)
        or f"{BASE_RULE_NODE_PREFIX}:{rule_id}"
    )


def _candidate_rule_id(candidate: dict[str, Any]) -> str:
    return str(
        _dict(candidate.get("rule_template")).get("rule_id")
        or _dict(candidate.get("deterministic_applicability_test_contract")).get("rule_id")
        or candidate.get("rule_id")
        or str(candidate.get("candidate_authority_id") or "").rsplit(":", 1)[-1]
    )


def _family_ids_by_rule_id(inventory: dict[str, Any]) -> dict[str, set[str]]:
    by_rule: dict[str, set[str]] = {}
    for family in inventory.get("authority_families", []):
        family_id = str(family.get("family_id") or "")
        for rule_id in _strings(family.get("rule_ids")):
            by_rule.setdefault(rule_id, set()).add(family_id)
    return by_rule


def _authority_family_id_for_decision(
    *,
    decision: dict[str, Any],
    candidate: dict[str, Any],
    family_ids_by_rule_id: dict[str, set[str]],
) -> str:
    explicit = (
        decision.get("authority_family_id")
        or _dict(decision.get("rule_template")).get("authority_family_id")
        or candidate.get("authority_family_id")
    )
    if explicit:
        return str(explicit)
    if str(decision.get("candidate_authority_type") or "") == "forest_plan_component":
        return "nfma_forest_planning_project_consistency"
    rule_id = _candidate_rule_id(decision or candidate)
    return _first_sorted(family_ids_by_rule_id.get(rule_id, set())) or "unknown_authority_family"


def _decision_status(decision: dict[str, Any]) -> str:
    return str(decision.get("status") or decision.get("applicability_status") or "")


def _decision_display_status(decision: dict[str, Any]) -> str:
    if decision.get("human_adjudication_refs"):
        return "adjudicated"
    status = _decision_status(decision)
    if status in {"applicable", "not_applicable", "unresolved"}:
        return status
    if status == "needs_adjudication":
        return "unresolved"
    return "readiness_blocked"


def _decision_review_readiness(decision: dict[str, Any]) -> str:
    status = _decision_status(decision)
    if status in {"applicable", "not_applicable"}:
        return "reviewer_ready"
    if status == "needs_adjudication":
        return "needs_adjudication"
    return "blocked"


def _decision_readiness_blockers(decision: dict[str, Any]) -> list[str]:
    status = _decision_status(decision)
    return ["adjudication_needed"] if status in {"needs_adjudication", "unresolved"} else []


def _review_validation_ready(
    applicability_validation: dict[str, Any],
    generated_rule_pack_validation: dict[str, Any],
) -> bool:
    return bool(
        applicability_validation.get("passed")
        and generated_rule_pack_validation.get("passed")
        and (
            applicability_validation.get("reviewer_ready") is not False
            and applicability_validation.get("generated_rule_pack_ready") is not False
        )
    )


def _first_sorted(values: set[str] | list[str] | tuple[str, ...] | None) -> str | None:
    if not values:
        return None
    return sorted(str(value) for value in values if str(value))[0]


def _stable_digest(*parts: object) -> str:
    joined = "\x1f".join(str(part) for part in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:24]


def _compact_dict(value: dict[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if item not in (None, "", [], {})}


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _dict_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def _first(value: object) -> object | None:
    if isinstance(value, list) and value:
        return value[0]
    return None


def _check(name: str, passed: bool, expected: object, actual: object) -> dict[str, Any]:
    return {
        "name": name,
        "passed": bool(passed),
        "expected": expected,
        "actual": actual,
    }
