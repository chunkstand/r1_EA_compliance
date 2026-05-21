from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import re
from typing import Any

from .real_package_review_coverage_eval import resolve_real_package_review_eval_file


DEFAULT_V1_EA_EVAL_PATH = Path("config/v1_ecid_real_ea_eval.json")
V1_EA_EVAL_RESULTS_SCHEMA_VERSION = "v1-ea-real-review-eval-results-v0"
SAFE_REVIEW_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
EXPECTED_APPLICABILITY_VALUES = {
    "applicable",
    "not_applicable",
    "needs_reviewer_resolution",
    "adjudicate",
}
FOREST_PLAN_ARTIFACTS = {
    "forest_plan_context_summary",
    "forest_plan_context",
    "forest_plan_component_findings",
    "forest_plan_applicable_standard_coverage",
    "forest_plan_reviewer_resolution_queue",
}
FOREST_PLAN_VALIDATION_CHECKS = {
    "forest_plan_component_gate_reviewer_ready",
}


def _resolve_eval_file(
    *,
    review_id: str | None,
    review_dir: Path | None,
    eval_file: Path | None,
    manifest_path: Path,
) -> Path:
    if eval_file is not None:
        return Path(eval_file)
    if review_id:
        return resolve_real_package_review_eval_file(
            review_id=review_id,
            manifest_path=manifest_path,
        )
    raise ValueError(
        "v1-ea-eval requires --eval-file or a tracked --review-id in the real-package "
        "review coverage manifest"
    )


def _preserve_generated_at_when_semantically_unchanged(
    payload: dict[str, Any],
    output_path: Path,
) -> dict[str, Any]:
    if not output_path.exists():
        return payload
    try:
        existing = _read_json(output_path)
    except (OSError, json.JSONDecodeError):
        return payload
    existing_summary = existing.get("summary") if isinstance(existing, dict) else None
    existing_generated_at = (
        existing_summary.get("generated_at")
        if isinstance(existing_summary, dict)
        else None
    )
    if not isinstance(existing_generated_at, str) or not existing_generated_at:
        return payload
    candidate = json.loads(json.dumps(payload))
    candidate["summary"]["generated_at"] = existing_generated_at
    if _without_summary_generated_at(candidate) == _without_summary_generated_at(existing):
        return candidate
    return payload


def _without_summary_generated_at(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = json.loads(json.dumps(payload))
    summary = normalized.get("summary")
    if isinstance(summary, dict):
        summary.pop("generated_at", None)
    return normalized


def _resolve_review_dir(
    *,
    output_dir: Path,
    review_id: str | None,
    review_dir: Path | None,
) -> Path:
    if review_dir is not None:
        return review_dir
    if not review_id:
        raise ValueError("review_id is required when review_dir is not supplied")
    if not SAFE_REVIEW_ID_RE.fullmatch(review_id):
        raise ValueError(f"unsafe review_id: {review_id!r}")
    return output_dir / "reviews" / review_id


def _load_review_artifacts(review_dir: Path, require_forest_plan: bool) -> dict[str, Any]:
    specs = {
        "compliance_review": ("compliance_review.json", True, "json"),
        "compliance_matrix": ("compliance_matrix.json", True, "json"),
        "compliance_validation": ("compliance_validation.json", True, "json"),
        "authority_explanation_paths": ("authority_explanation_paths.json", True, "json"),
        "package_chunks": ("package/package_chunks.jsonl", True, "jsonl"),
        "applicability_decisions": (
            "applicability/applicability_decisions.jsonl",
            False,
            "jsonl",
        ),
        "generated_rule_pack": ("applicability/generated_rule_pack.json", False, "json"),
        "forest_plan_context_summary": (
            "forest_plan_context_summary.json",
            require_forest_plan,
            "json",
        ),
        "forest_plan_context": ("forest_plan_context.json", require_forest_plan, "json"),
        "forest_plan_component_findings": (
            "forest_plan_component_findings.json",
            require_forest_plan,
            "json",
        ),
        "forest_plan_applicable_standard_coverage": (
            "forest_plan_applicable_standard_coverage.json",
            require_forest_plan,
            "json",
        ),
        "forest_plan_component_adjudication_eval": (
            "forest_plan_component_adjudication_eval.json",
            False,
            "json",
        ),
        "forest_plan_reviewer_resolution_queue": (
            "forest_plan_reviewer_resolution_queue.json",
            False,
            "json",
        ),
    }
    artifacts: dict[str, Any] = {
        "artifact_errors": [],
        "artifact_paths": {},
    }
    for name, (relative, required, kind) in specs.items():
        path = review_dir / relative
        artifacts["artifact_paths"][name] = str(path)
        if not path.exists():
            artifacts[name] = [] if kind == "jsonl" else {}
            if required:
                artifacts["artifact_errors"].append(
                    {
                        "artifact": name,
                        "path": str(path),
                        "failure_category": "review_artifact_missing",
                        "message": "Required review artifact is missing.",
                    }
                )
            continue
        try:
            artifacts[name] = _read_jsonl(path) if kind == "jsonl" else _read_json(path)
        except (json.JSONDecodeError, OSError) as exc:
            artifacts[name] = [] if kind == "jsonl" else {}
            artifacts["artifact_errors"].append(
                {
                    "artifact": name,
                    "path": str(path),
                    "failure_category": "review_artifact_unreadable",
                    "message": str(exc),
                }
            )
    return artifacts


def _validate_contract(contract: dict[str, Any]) -> None:
    if not isinstance(contract, dict):
        raise ValueError("V1 EA eval contract must be a JSON object")
    if not contract.get("eval_id"):
        raise ValueError("V1 EA eval contract requires eval_id")
    for index, expectation in enumerate(contract.get("section_expectations", []), start=1):
        if not expectation.get("section_id"):
            raise ValueError(f"section_expectations[{index}] requires section_id")
        if not _expectation_terms(expectation):
            raise ValueError(f"section_expectations[{index}] requires expected_terms or aliases")
    forest_unit_id = contract.get("forest_unit_id")
    if forest_unit_id is not None and not str(forest_unit_id).strip():
        raise ValueError("forest_unit_id must be a non-empty string when provided")
    package_style_tags = contract.get("package_style_tags")
    if package_style_tags is not None and (
        not isinstance(package_style_tags, list)
        or not all(isinstance(tag, str) and tag.strip() for tag in package_style_tags)
    ):
        raise ValueError("package_style_tags must contain only non-empty strings")
    expected_lane_states = contract.get("expected_lane_states")
    normalized_lane_states = _normalized_expected_lane_states(expected_lane_states)
    if expected_lane_states is not None:
        if not isinstance(expected_lane_states, dict):
            raise ValueError("expected_lane_states must be a JSON object when provided")
        if len(normalized_lane_states) != len(expected_lane_states):
            raise ValueError(
                "expected_lane_states may only contain boolean passed/overall_passed/"
                "broader_ea_passed/forest_plan_passed fields"
            )
    allowed_blocker_categories = contract.get("allowed_blocker_categories")
    if allowed_blocker_categories is not None and (
        not isinstance(allowed_blocker_categories, list)
        or not all(
            isinstance(category, str) and category.strip()
            for category in allowed_blocker_categories
        )
    ):
        raise ValueError("allowed_blocker_categories must contain only non-empty strings")
    if any(expected is False for expected in normalized_lane_states.values()):
        if not _string_list(allowed_blocker_categories):
            raise ValueError(
                "allowed_blocker_categories is required when expected_lane_states includes "
                "a false lane state"
            )
    for name in ("rule_review_expectations", "conditional_source_expectations"):
        for index, expectation in enumerate(contract.get(name, []), start=1):
            if not expectation.get("rule_id"):
                raise ValueError(f"{name}[{index}] requires rule_id")
            if name == "conditional_source_expectations":
                value = expectation.get("expected_applicability")
                if value not in EXPECTED_APPLICABILITY_VALUES:
                    raise ValueError(
                        f"{name}[{index}] has invalid expected_applicability: {value!r}"
                    )
                if not str(expectation.get("classification_rationale") or "").strip():
                    raise ValueError(f"{name}[{index}] requires classification_rationale")
    adjudicate_rule_ids = sorted(
        str(expectation["rule_id"])
        for expectation in contract.get("conditional_source_expectations", [])
        if expectation.get("expected_applicability") == "adjudicate"
        and str(expectation.get("rule_id") or "").strip()
    )
    if adjudicate_rule_ids:
        policy = contract.get("conditional_adjudication_policy")
        if not isinstance(policy, dict):
            raise ValueError(
                "conditional_adjudication_policy is required when conditional "
                "expectations use expected_applicability=adjudicate"
            )
        if policy.get("mode") != "accepted_pending_v1":
            raise ValueError("conditional_adjudication_policy.mode must be accepted_pending_v1")
        raw_accepted_rule_ids = policy.get("accepted_pending_rule_ids")
        if not isinstance(raw_accepted_rule_ids, list):
            raise ValueError(
                "conditional_adjudication_policy.accepted_pending_rule_ids must be a list"
            )
        if not all(
            isinstance(rule_id, str) and rule_id.strip()
            for rule_id in raw_accepted_rule_ids
        ):
            raise ValueError(
                "conditional_adjudication_policy.accepted_pending_rule_ids must contain "
                "non-empty strings"
            )
        accepted_rule_ids = _policy_rule_ids(raw_accepted_rule_ids)
        if accepted_rule_ids != adjudicate_rule_ids:
            raise ValueError(
                "conditional_adjudication_policy.accepted_pending_rule_ids must match "
                "adjudicate conditional expectations"
            )
        accepted_pending_count = policy.get("accepted_pending_count")
        if not isinstance(accepted_pending_count, int) or isinstance(
            accepted_pending_count,
            bool,
        ):
            raise ValueError(
                "conditional_adjudication_policy.accepted_pending_count must be an integer"
            )
        if accepted_pending_count != len(adjudicate_rule_ids):
            raise ValueError(
                "conditional_adjudication_policy.accepted_pending_count must match "
                "adjudicate conditional expectation count"
            )
        if not str(policy.get("rationale") or "").strip():
            raise ValueError("conditional_adjudication_policy requires rationale")


def _findings_by_rule(compliance_review: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(finding["rule_id"]): finding
        for finding in compliance_review.get("findings", [])
        if finding.get("rule_id")
    }


def _matrix_by_rule(compliance_matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row["rule_id"]): row
        for row in compliance_matrix.get("rows", [])
        if row.get("rule_id")
    }


def _identity_matches_contract(
    contract: dict[str, Any],
    identity: dict[str, Any],
    review_dir: Path,
) -> bool:
    if contract.get("review_id") and contract["review_id"] != identity.get(
        "review_id",
        review_dir.name,
    ):
        return False
    if contract.get("source_set_id") and contract.get("source_set_id") != identity.get(
        "source_set_id"
    ):
        return False
    return _rule_pack_identity_matches(contract, identity)


def _rule_pack_identity_matches(contract: dict[str, Any], identity: dict[str, Any]) -> bool:
    contract_id = contract.get("rule_pack_id")
    contract_version = contract.get("rule_pack_version")
    if not contract_id and not contract_version:
        return True
    review_pairs = {
        (
            identity.get("rule_pack_id"),
            identity.get("rule_pack_version"),
        ),
        (
            identity.get("base_rule_pack_id"),
            identity.get("base_rule_pack_version"),
        ),
    }
    review_pairs = {(pack_id, version) for pack_id, version in review_pairs if pack_id or version}
    if contract_id and contract_version:
        return (contract_id, contract_version) in review_pairs
    if contract_id:
        return any(contract_id == pack_id for pack_id, _version in review_pairs)
    if contract_version:
        return any(contract_version == version for _pack_id, version in review_pairs)
    return True


def _review_identity(
    compliance_review: dict[str, Any],
    generated_rule_pack: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary = compliance_review.get("summary") or {}
    rule_pack = compliance_review.get("rule_pack") or {}
    generated_rule_pack = generated_rule_pack or {}
    return {
        "review_id": compliance_review.get("review_id") or summary.get("review_id"),
        "source_set_id": compliance_review.get("source_set_id") or summary.get("source_set_id"),
        "rule_pack_id": compliance_review.get("rule_pack_id")
        or summary.get("rule_pack_id")
        or rule_pack.get("rule_pack_id")
        or generated_rule_pack.get("rule_pack_id"),
        "rule_pack_version": compliance_review.get("rule_pack_version")
        or summary.get("rule_pack_version")
        or rule_pack.get("version")
        or generated_rule_pack.get("version"),
        "base_rule_pack_id": compliance_review.get("base_rule_pack_id")
        or summary.get("base_rule_pack_id")
        or rule_pack.get("base_rule_pack_id")
        or generated_rule_pack.get("base_rule_pack_id"),
        "base_rule_pack_version": compliance_review.get("base_rule_pack_version")
        or summary.get("base_rule_pack_version")
        or rule_pack.get("base_rule_pack_version")
        or generated_rule_pack.get("base_rule_pack_version"),
    }


def _contract_identity(contract: dict[str, Any]) -> dict[str, Any]:
    return {
        key: contract.get(key)
        for key in ("review_id", "source_set_id", "rule_pack_id", "rule_pack_version")
        if contract.get(key)
    }


def _normalized_expected_lane_states(value: Any) -> dict[str, bool]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, bool] = {}
    key_aliases = {
        "passed": "passed",
        "overall_passed": "passed",
        "broader_ea_passed": "broader_ea_passed",
        "forest_plan_passed": "forest_plan_passed",
    }
    for raw_key, expected in value.items():
        key = key_aliases.get(str(raw_key))
        if key is None or not isinstance(expected, bool):
            continue
        normalized[key] = expected
    return normalized


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _policy_rule_ids(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted(str(rule_id).strip() for rule_id in value if str(rule_id).strip())


def _expectation_terms(expectation: dict[str, Any]) -> list[str]:
    terms = []
    for key in ("expected_terms", "aliases", "trigger_terms"):
        terms.extend(str(value) for value in expectation.get(key, []) if value)
    return sorted(set(terms))


def _chunk_text(chunk: dict[str, Any]) -> str:
    return " ".join(
        str(value)
        for value in (
            chunk.get("title"),
            chunk.get("section"),
            chunk.get("heading"),
            chunk.get("text"),
        )
        if value
    )


def _evidence_text(evidence: Any) -> str:
    if not isinstance(evidence, dict):
        return ""
    span = evidence.get("evidence_span") or {}
    provenance = evidence.get("provenance") or {}
    return " ".join(
        str(value)
        for value in (
            evidence.get("citation_label"),
            evidence.get("title"),
            evidence.get("section"),
            evidence.get("heading"),
            evidence.get("text"),
            span.get("text"),
            provenance.get("section"),
            provenance.get("heading"),
            provenance.get("title"),
        )
        if value
    )


def _matched_terms(text: str, terms: list[str]) -> set[str]:
    normalized = _normalize(text)
    return {term for term in terms if _normalize(term) in normalized}


def _normalize(value: str) -> str:
    return " ".join(str(value).lower().replace("_", " ").replace("-", " ").split())


def _strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _first_string(value: Any) -> str | None:
    values = _strings(value)
    return values[0] if values else None


def _collect_values_by_key(value: Any, keys: set[str]) -> set[str]:
    values: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key in keys and isinstance(child, (str, int)):
                values.add(str(child))
            values |= _collect_values_by_key(child, keys)
    elif isinstance(value, list):
        for child in value:
            values |= _collect_values_by_key(child, keys)
    return values


def _collect_list_values_by_key(value: Any, key_name: str) -> set[str]:
    values: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key == key_name and isinstance(child, list):
                values.update(str(item) for item in child if isinstance(item, (str, int)))
            else:
                values |= _collect_list_values_by_key(child, key_name)
    elif isinstance(value, list):
        for child in value:
            values |= _collect_list_values_by_key(child, key_name)
    return values


def _nested_get(value: dict[str, Any], path: list[str]) -> Any:
    current: Any = value
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
