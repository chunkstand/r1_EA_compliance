from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ONTOLOGY_PATH = REPO_ROOT / "config" / "authority_document_ontology_v1.json"
RELATIONSHIP_TYPES_PATH = REPO_ROOT / "config" / "authority_relationship_types_v1.json"
RELATIONSHIP_REGISTER_PATH = REPO_ROOT / "config" / "authority_relationship_register_v1.json"
ALIAS_REGISTER_PATH = REPO_ROOT / "config" / "citation_alias_register_v1.json"
SCOPE_REGISTER_PATH = REPO_ROOT / "config" / "jurisdiction_scope_register_v1.json"
ONTOLOGY_EVAL_PATH = REPO_ROOT / "config" / "authority_ontology_eval_v1.json"
RELATIONSHIP_EVAL_PATH = REPO_ROOT / "config" / "authority_relationship_eval_v1.json"
GRAPH_ACCURACY_EVAL_PATH = REPO_ROOT / "config" / "graph_accuracy_eval_v1.json"
GRAPH_HEALTH_CONTRACT_PATH = REPO_ROOT / "config" / "graph_health_contract_v1.json"


def test_authority_ontology_starter_defines_required_semantic_layers() -> None:
    ontology = _load_json(ONTOLOGY_PATH)

    assert ontology["schema_version"] == "authority-document-ontology-v1"
    class_ids = _ids(ontology["classes"], "class_id")
    assert {
        "authority_document",
        "authority_expression",
        "authority_fragment",
        "authority_section",
        "jurisdiction_scope",
        "source_record",
        "source_artifact",
        "evidence_span",
        "forest_plan",
        "forest_plan_component",
        "review",
        "applicability_decision",
        "generated_rule",
        "compliance_finding",
        "authority_path",
        "justification_path",
    }.issubset(class_ids)

    disjoint_sets = {
        entry["set_id"]: set(entry["class_ids"]) for entry in ontology["disjoint_class_sets"]
    }
    assert "semantic-vs-provenance" in disjoint_sets
    assert "semantic-vs-reasoning" in disjoint_sets
    assert "authority_document" in disjoint_sets["semantic-vs-provenance"]
    assert "source_record" in disjoint_sets["semantic-vs-provenance"]
    assert "compliance_finding" in disjoint_sets["semantic-vs-reasoning"]


def test_authority_relationship_contract_uses_known_ontology_classes() -> None:
    ontology = _load_json(ONTOLOGY_PATH)
    relationship_types = _load_json(RELATIONSHIP_TYPES_PATH)

    class_ids = _ids(ontology["classes"], "class_id")
    required_relationship_types = {
        "IMPLEMENTS",
        "INTERPRETS",
        "AMENDS",
        "SUPERSEDES",
        "RESCINDS",
        "INCORPORATES_BY_REFERENCE",
        "DELEGATES_AUTHORITY_TO",
        "REQUIRES_CONSISTENCY_WITH",
        "PROVIDES_GUIDANCE_FOR",
        "IS_SUPPORTING_DOCUMENT_FOR",
        "SUPPORTS_FOREST_PLAN_COMPONENT",
        "APPLIES_WITHIN_SCOPE",
        "GOVERNS_FOREST_UNIT",
    }
    relationship_type_ids = _ids(relationship_types["relationship_types"], "relationship_type")

    assert relationship_types["schema_version"] == "authority-relationship-types-v1"
    assert required_relationship_types.issubset(relationship_type_ids)

    for relationship in relationship_types["relationship_types"]:
        assert set(relationship["source_class_ids"]).issubset(class_ids)
        assert set(relationship["target_class_ids"]).issubset(class_ids)
        assert {"relationship_basis", "evidence_basis_type"}.issubset(
            set(relationship["required_provenance_fields"])
        )


def test_authority_relationship_register_keeps_examples_out_of_runtime_rows() -> None:
    register = _load_json(RELATIONSHIP_REGISTER_PATH)

    assert register["schema_version"] == "authority-relationship-register-v1"
    assert register["rows"] == []
    assert len(register["starter_rows"]) >= 6
    assert "Only rows listed under rows are canonical runtime inputs." in register["activation_rule"]


def test_alias_and_scope_starters_define_required_baselines() -> None:
    alias_register = _load_json(ALIAS_REGISTER_PATH)
    scope_register = _load_json(SCOPE_REGISTER_PATH)

    assert alias_register["schema_version"] == "citation-alias-register-v1"
    assert scope_register["schema_version"] == "jurisdiction-scope-register-v1"
    assert "forest plan" in alias_register["ambiguity_policy"]["blocked_without_context"]
    assert len(alias_register["starter_alias_groups"]) >= 5

    scope_class_ids = _ids(scope_register["scope_classes"], "scope_class_id")
    assert {
        "legal_jurisdiction_scope",
        "administrative_scope",
        "forest_unit_scope",
        "project_scope",
        "resource_topic_scope",
    }.issubset(scope_class_ids)
    scope_ids = _ids(scope_register["scopes"], "scope_id")
    assert {
        "scope:federal-us",
        "scope:usfs-region-1",
        "scope:region1-forest-unit",
        "scope:ea-project-review",
    }.issubset(scope_ids)


def test_ontology_and_relationship_eval_manifests_stay_aligned() -> None:
    ontology = _load_json(ONTOLOGY_PATH)
    relationship_types = _load_json(RELATIONSHIP_TYPES_PATH)
    ontology_eval = _load_json(ONTOLOGY_EVAL_PATH)
    relationship_eval = _load_json(RELATIONSHIP_EVAL_PATH)

    class_ids = _ids(ontology["classes"], "class_id")
    object_property_ids = _ids(ontology["object_properties"], "property_id")
    disjoint_set_ids = _ids(ontology["disjoint_class_sets"], "set_id")
    competency_question_ids = _ids(ontology["competency_questions"], "question_id")
    relationship_type_ids = _ids(relationship_types["relationship_types"], "relationship_type")
    path_pattern_ids = _ids(relationship_types["starter_path_patterns"], "path_pattern_id")

    assert ontology_eval["schema_version"] == "authority-ontology-eval-v1"
    assert relationship_eval["schema_version"] == "authority-relationship-eval-v1"
    assert set(ontology_eval["required_class_ids"]).issubset(class_ids)
    assert set(ontology_eval["source_set_required_class_ids"]).issubset(class_ids)
    assert set(ontology_eval["required_object_property_ids"]).issubset(object_property_ids)
    assert set(ontology_eval["required_disjoint_set_ids"]).issubset(disjoint_set_ids)
    assert set(relationship_eval["required_relationship_types"]).issubset(relationship_type_ids)
    assert set(relationship_eval["required_path_patterns"]).issubset(path_pattern_ids)

    for coverage in ontology_eval["competency_question_coverage"]:
        assert coverage["question_id"] in competency_question_ids
        assert set(coverage["required_class_ids"]).issubset(class_ids)
        assert set(coverage["required_relationship_types"]).issubset(relationship_type_ids)


def test_graph_accuracy_and_health_manifests_define_canonical_source_set_scope() -> None:
    ontology = _load_json(ONTOLOGY_PATH)
    accuracy_eval = _load_json(GRAPH_ACCURACY_EVAL_PATH)
    health_contract = _load_json(GRAPH_HEALTH_CONTRACT_PATH)

    class_ids = _ids(ontology["classes"], "class_id")

    assert accuracy_eval["schema_version"] == "graph-accuracy-eval-v1"
    assert health_contract["schema_version"] == "graph-health-contract-v1"
    assert set(accuracy_eval["required_node_class_ids"]).issubset(class_ids)
    assert set(accuracy_eval["source_set_required_node_class_ids"]).issubset(class_ids)
    assert set(health_contract["knowledge_graph_required_lens_ids"]) == {
        "authority_currentness",
        "forest_plan",
        "package_applicability",
        "evidence_path",
        "semantic_relationships",
        "readiness_blockers",
    }


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _ids(entries: list[dict], key: str) -> set[str]:
    return {entry[key] for entry in entries}
