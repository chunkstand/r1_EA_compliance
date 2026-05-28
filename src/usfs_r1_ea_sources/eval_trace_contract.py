from __future__ import annotations

from pathlib import Path
from typing import Any
import json


REPO_ROOT = Path(__file__).resolve().parents[2]
EVAL_TRACE_CONTRACT_SCHEMA_VERSION = "first-class-eval-trace-inventory-contract-v1"
DEFAULT_EVAL_TRACE_CONTRACT_PATH = REPO_ROOT / "config" / "eval_trace_inventory_contract_v1.json"

REQUIRED_CANONICAL_OBJECTS = {
    "system_eval_runs",
    "system_eval_cases",
    "system_eval_case_results",
    "system_eval_scores",
    "trace_runs",
    "trace_spans",
}

REQUIRED_ENUM_VALUES = {
    "eval_kind": {
        "applicability",
        "capture",
        "catalog",
        "claim",
        "compliance_gold",
        "compliance_review",
        "decision_support",
        "extraction_fidelity",
        "final_qa",
        "forest_plan_component",
        "forest_plan_profile",
        "gold_coverage",
        "packet_index",
        "phase_eval",
        "project_sow",
        "promotion_suite",
        "real_package_review_coverage",
        "retrieval",
        "rule_claim",
        "semantic_generation",
        "semantic_graph",
        "v1_ea",
    },
    "trace_kind": {
        "agent_task",
        "applicability_graph",
        "applicability_retrieval",
        "capture",
        "evaluation",
        "graph_readiness",
        "replay",
        "review_package",
        "search",
        "semantic_generation",
        "semantic_memory_publication",
        "technical_report",
        "validation",
        "workbook_capture",
    },
    "span_kind": {
        "agent_task",
        "approval",
        "artifact",
        "chunk",
        "embed",
        "error",
        "evaluation",
        "figure_extract",
        "guardrail",
        "ingest",
        "llm",
        "parse",
        "rerank",
        "retrieve",
        "score",
        "search",
        "table_extract",
        "tool",
        "validate",
        "workflow",
    },
    "score_kind": {
        "cost",
        "deterministic_code",
        "groundedness",
        "human_label",
        "latency",
        "llm_judge",
        "retrieval",
        "safety_security",
        "schema",
        "tool_arguments",
        "tool_selection",
        "trace_integrity",
    },
}

REQUIRED_ARTIFACT_FAMILIES = {
    "applicability_trace",
    "decision_support",
    "final_qa",
    "forest_plan_component_eval",
    "forest_plan_component_eval_coverage",
    "phase_eval",
    "promotion_suite",
    "real_package_review_coverage_eval",
    "replay_context",
    "review_packet_index",
    "source_catalog",
    "source_set_manifest",
    "v1_ea_eval",
}

REQUIRED_LINK_CHECK_IDS = {
    "applicability_trace_hash_match",
    "export_local_provenance_preserved",
    "no_hosted_source_of_record",
    "origin_artifact_ref_present",
    "phase_eval_direct_eval_present",
    "ratchet_scope_explicit",
    "replay_context_catalog_match",
    "review_identity_match",
    "source_artifact_hash_present",
    "source_set_identity_match",
}

REQUIRED_SCHEMA_VERSION_KEYS = {
    "canonical_export",
    "case_definition",
    "inventory_report",
    "inventory_result",
    "openinference_export",
    "store",
}

REQUIRED_LLM_JUDGE_METADATA_FIELDS = {
    "examples_hash",
    "judge_model",
    "judge_prompt_hash",
    "output_schema",
    "rubric_hash",
    "temperature",
}

REQUIRED_DETERMINISTIC_SCORE_KINDS = {
    "deterministic_code",
    "groundedness",
    "retrieval",
    "schema",
    "safety_security",
    "trace_integrity",
}

GLOBAL_RATCHET_MARKERS = {"*", "all", "__all__", "global"}


def load_eval_trace_contract(
    path: Path = DEFAULT_EVAL_TRACE_CONTRACT_PATH,
) -> dict[str, Any]:
    payload = _read_json(path)
    failed_checks = [
        check["name"] for check in validate_eval_trace_contract(payload) if not check["passed"]
    ]
    if failed_checks:
        raise ValueError(f"Invalid first-class eval trace contract: {', '.join(failed_checks)}")
    return payload


def validate_eval_trace_contract(contract: dict[str, Any]) -> list[dict[str, Any]]:
    enum_values = _dict(contract.get("enum_values"))
    artifact_families = _dict_list(contract.get("required_artifact_families"))
    link_checks = _dict_list(contract.get("required_link_checks"))
    schema_versions = _dict(contract.get("schema_versions"))
    scorer_contract = _dict(contract.get("scorer_contract"))
    ratchet_scopes = _dict(contract.get("ratchet_scopes"))

    checks = [
        _check(
            "eval_trace_contract_schema_version",
            contract.get("schema_version") == EVAL_TRACE_CONTRACT_SCHEMA_VERSION,
            EVAL_TRACE_CONTRACT_SCHEMA_VERSION,
            contract.get("schema_version"),
        ),
        _check(
            "eval_trace_contract_names_canonical_objects",
            REQUIRED_CANONICAL_OBJECTS <= _ids(contract.get("canonical_objects"), "name"),
            sorted(REQUIRED_CANONICAL_OBJECTS),
            sorted(REQUIRED_CANONICAL_OBJECTS - _ids(contract.get("canonical_objects"), "name")),
        ),
        _check(
            "eval_trace_contract_artifact_families_present",
            REQUIRED_ARTIFACT_FAMILIES <= _ids(artifact_families, "family_id"),
            sorted(REQUIRED_ARTIFACT_FAMILIES),
            sorted(REQUIRED_ARTIFACT_FAMILIES - _ids(artifact_families, "family_id")),
        ),
        _check(
            "eval_trace_contract_artifact_families_are_linkable",
            not _artifact_family_link_gaps(artifact_families),
            "non-empty artifact_paths and source_ref_requirements",
            _artifact_family_link_gaps(artifact_families),
        ),
        _check(
            "eval_trace_contract_required_link_checks_present",
            REQUIRED_LINK_CHECK_IDS <= _ids(link_checks, "check_id"),
            sorted(REQUIRED_LINK_CHECK_IDS),
            sorted(REQUIRED_LINK_CHECK_IDS - _ids(link_checks, "check_id")),
        ),
        _check(
            "eval_trace_contract_required_link_checks_are_fail_closed",
            not _link_check_gaps(link_checks),
            "required=true with failure_reason",
            _link_check_gaps(link_checks),
        ),
        _check(
            "eval_trace_contract_schema_versions_present",
            REQUIRED_SCHEMA_VERSION_KEYS <= set(_dict(contract.get("schema_versions"))),
            sorted(REQUIRED_SCHEMA_VERSION_KEYS),
            sorted(REQUIRED_SCHEMA_VERSION_KEYS - set(schema_versions)),
        ),
        _check(
            "eval_trace_contract_deterministic_scorers_first",
            REQUIRED_DETERMINISTIC_SCORE_KINDS
            <= set(_strings(scorer_contract.get("deterministic_first_score_kinds"))),
            sorted(REQUIRED_DETERMINISTIC_SCORE_KINDS),
            sorted(
                REQUIRED_DETERMINISTIC_SCORE_KINDS
                - set(_strings(scorer_contract.get("deterministic_first_score_kinds")))
            ),
        ),
        _check(
            "eval_trace_contract_llm_judge_metadata_required",
            REQUIRED_LLM_JUDGE_METADATA_FIELDS
            <= set(_strings(scorer_contract.get("llm_judge_metadata_required_fields"))),
            sorted(REQUIRED_LLM_JUDGE_METADATA_FIELDS),
            sorted(
                REQUIRED_LLM_JUDGE_METADATA_FIELDS
                - set(_strings(scorer_contract.get("llm_judge_metadata_required_fields")))
            ),
        ),
        _check(
            "eval_trace_contract_ratchet_scope_is_explicit",
            not _ratchet_scope_violations(ratchet_scopes),
            "no global or wildcard fail-closed scope in Milestone 0",
            _ratchet_scope_violations(ratchet_scopes),
        ),
    ]
    checks.extend(_enum_checks(enum_values))
    return checks


def _enum_checks(enum_values: dict[str, Any]) -> list[dict[str, Any]]:
    checks = []
    for family, required_values in sorted(REQUIRED_ENUM_VALUES.items()):
        actual_values = set(_strings(enum_values.get(family)))
        missing = sorted(required_values - actual_values)
        unsupported = sorted(actual_values - required_values)
        checks.append(
            _check(
                f"eval_trace_contract_{family}_values_supported",
                not missing and not unsupported,
                {"required": sorted(required_values), "unsupported": []},
                {"missing": missing, "unsupported": unsupported},
            )
        )
    return checks


def _artifact_family_link_gaps(artifact_families: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gaps = []
    for family in artifact_families:
        missing = []
        if not str(family.get("family_id") or "").strip():
            missing.append("family_id")
        if not str(family.get("owner_layer") or "").strip():
            missing.append("owner_layer")
        if not _strings(family.get("artifact_paths")):
            missing.append("artifact_paths")
        if not _strings(family.get("source_ref_requirements")):
            missing.append("source_ref_requirements")
        if missing:
            gaps.append({"family_id": family.get("family_id"), "missing": missing})
    return gaps


def _link_check_gaps(link_checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gaps = []
    for link_check in link_checks:
        missing = []
        if not str(link_check.get("check_id") or "").strip():
            missing.append("check_id")
        if not link_check.get("required"):
            missing.append("required")
        if not str(link_check.get("failure_reason") or "").strip():
            missing.append("failure_reason")
        if missing:
            gaps.append({"check_id": link_check.get("check_id"), "missing": missing})
    return gaps


def _ratchet_scope_violations(ratchet_scopes: dict[str, Any]) -> list[dict[str, Any]]:
    violations = []
    if ratchet_scopes.get("global_fail_closed"):
        violations.append({"field": "global_fail_closed", "actual": True})
    for field in ("enabled_source_set_ids", "enabled_review_ids"):
        values = {value.lower() for value in _strings(ratchet_scopes.get(field))}
        wildcard_values = sorted(values & GLOBAL_RATCHET_MARKERS)
        if wildcard_values:
            violations.append({"field": field, "actual": wildcard_values})
    return violations


def _check(name: str, passed: bool, expected: Any, actual: Any) -> dict[str, Any]:
    return {"name": name, "passed": passed, "expected": expected, "actual": actual}


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _ids(value: Any, key: str) -> set[str]:
    return {str(item.get(key)) for item in _dict_list(value) if str(item.get(key) or "").strip()}


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
