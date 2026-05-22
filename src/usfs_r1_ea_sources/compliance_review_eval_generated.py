from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
import json

from .applicability import build_authority_universe_snapshot
from .applicability_decisions import build_applicability_decisions
from .applicability_retrieval import build_applicability_retrieval_traces
from .applicability_rule_pack import generate_applicability_rule_pack
from .applicability_rule_pack_runtime import _authority_family_template_rule
from .applicability_rule_pack_runtime import _source_claim_link_requirements
from .applicability_validation import validate_applicability_run
from .ea_review import run_ea_review
from .package_fact_graph import build_package_fact_graph
from .rule_packs import load_rule_pack
from .rule_packs import validate_rule_pack


GENERATED_RULE_PACK_EXPECTATION_FIELDS = (
    "expected_generated_statuses",
    "expected_generated_claim_types",
    "expected_generated_package_evidence",
    "expected_generated_source_evidence",
    "expected_generated_source_claim_links",
    "expected_generated_source_record_ids",
    "expected_generated_source_document_roles",
    "expected_generated_validation_passed",
    "expected_generated_reviewer_ready",
    "expected_generated_min_findings",
)


@dataclass(frozen=True)
class EvalRulePackResolution:
    rule_pack_path: Path
    allow_generated_rule_pack_diagnostic: bool = False


def _case_requires_generated_rule_pack(case: dict) -> bool:
    return any(
        bool(case.get(field))
        for field in (
            "all_authorities_control",
            "conditional_subset",
            "hard_negative_package",
            "generated_rule_pack_case",
        )
    ) or _case_has_generated_rule_pack_expectations(case)


def _case_has_generated_rule_pack_expectations(case: dict) -> bool:
    for field in GENERATED_RULE_PACK_EXPECTATION_FIELDS:
        if field not in case:
            continue
        value = case.get(field)
        if isinstance(value, dict):
            if value:
                return True
            continue
        if isinstance(value, list):
            if value:
                return True
            continue
        if value is not None:
            return True
    return False


def _generated_rule_pack_for_eval_case(
    *,
    case: dict,
    output_dir: Path,
    package_path: Path,
    base_rule_pack_path: Path,
    source_set_id: str | None,
    index_path: Path | None,
    review_id: str,
    review_dir: Path,
    source_top_k: int,
    package_top_k: int,
    chunk_max_chars: int,
    chunk_overlap_chars: int,
    docling_ocr: bool,
    docling_timeout_seconds: float | None,
) -> EvalRulePackResolution:
    run_ea_review(
        package_path=package_path,
        output_dir=output_dir,
        source_set_id=source_set_id,
        index_path=index_path,
        checklist_path=base_rule_pack_path,
        review_id=review_id,
        source_top_k=source_top_k,
        package_top_k=package_top_k,
        chunk_max_chars=chunk_max_chars,
        chunk_overlap_chars=chunk_overlap_chars,
        docling_ocr=docling_ocr,
        docling_timeout_seconds=docling_timeout_seconds,
    )
    build_authority_universe_snapshot(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=source_set_id,
        base_rule_pack_path=base_rule_pack_path,
    )
    build_package_fact_graph(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=source_set_id,
        package_path=package_path,
    )
    build_applicability_retrieval_traces(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=source_set_id,
        top_k=source_top_k,
    )
    build_applicability_decisions(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=source_set_id,
    )
    validation_result = validate_applicability_run(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=source_set_id,
    )
    if not validation_result.summary.get("passed"):
        if _case_allows_generated_rule_pack_diagnostic(case):
            diagnostic_rule_pack_path = _write_generated_rule_pack_diagnostic(
                case=case,
                review_id=review_id,
                review_dir=review_dir,
                base_rule_pack_path=base_rule_pack_path,
                authority_universe_path=(
                    output_dir
                    / "reviews"
                    / review_id
                    / "applicability"
                    / "authority_universe_snapshot.json"
                ),
                source_set_id=source_set_id,
            )
            return EvalRulePackResolution(
                rule_pack_path=diagnostic_rule_pack_path,
                allow_generated_rule_pack_diagnostic=True,
            )
        failed_checks = [
            str(check.get("name") or "")
            for check in validation_result.summary.get("checks", [])
            if not check.get("passed")
        ]
        failed_text = ", ".join(item for item in failed_checks if item) or "unknown"
        raise ValueError(
            "Applicability validation did not pass for compliance-review eval case "
            f"{review_id}: {failed_text}"
        )
    generated_result = generate_applicability_rule_pack(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=source_set_id,
        base_rule_pack_path=base_rule_pack_path,
    )
    return EvalRulePackResolution(rule_pack_path=generated_result.generated_rule_pack_path)


def _case_allows_generated_rule_pack_diagnostic(case: dict) -> bool:
    if not _case_requires_generated_rule_pack(case):
        return False
    for field in (
        "expected_generated_validation_passed",
        "expected_generated_reviewer_ready",
        "expected_validation_passed",
        "expected_reviewer_ready",
    ):
        if field in case and case.get(field) is False:
            return True
    return False


def _write_generated_rule_pack_diagnostic(
    *,
    case: dict,
    review_id: str,
    review_dir: Path,
    base_rule_pack_path: Path,
    authority_universe_path: Path,
    source_set_id: str | None,
) -> Path:
    base_rule_pack = load_rule_pack(base_rule_pack_path)
    authority_universe = _read_json(authority_universe_path)
    candidate_authorities = authority_universe.get("candidate_authorities") or []
    rule_template_candidates = {
        str((candidate.get("rule_template") or {}).get("rule_id") or ""): candidate
        for candidate in candidate_authorities
        if isinstance(candidate, dict)
        and candidate.get("candidate_authority_type") == "rule_template"
        and str((candidate.get("rule_template") or {}).get("rule_id") or "").strip()
    }
    authority_family_candidates = {
        str((candidate.get("rule_template") or {}).get("rule_id") or ""): candidate
        for candidate in candidate_authorities
        if isinstance(candidate, dict)
        and candidate.get("candidate_authority_type") == "authority_family_rule_template"
        and str((candidate.get("rule_template") or {}).get("rule_id") or "").strip()
    }
    base_rules_by_id = {
        str(rule.get("id") or ""): deepcopy(rule)
        for rule in base_rule_pack.get("rules", [])
        if isinstance(rule, dict) and str(rule.get("id") or "").strip()
    }
    selected_generated_rule_ids = _generated_diagnostic_rule_ids(case)
    selected_base_rule_ids = {
        rule_id
        for rule_id, status in _string_map(case.get("expected_statuses") or {}).items()
        if status != "not_applicable"
    }
    selected_base_rule_ids.update(
        rule_id for rule_id in selected_generated_rule_ids if rule_id in base_rules_by_id
    )
    selected_generated_rule_ids = {
        rule_id for rule_id in selected_generated_rule_ids if rule_id not in base_rules_by_id
    }
    rules: list[dict] = []
    for rule_id in sorted(selected_base_rule_ids):
        base_rule = base_rules_by_id.get(rule_id)
        if base_rule is None:
            raise ValueError(
                "Compliance review eval generated diagnostic rule pack is missing base rule "
                f"{rule_id!r} for review {review_id}."
            )
        rules.append(
            _diagnostic_base_rule(
                rule_id=rule_id,
                base_rule=base_rule,
                candidate=rule_template_candidates.get(rule_id),
            )
        )
    for rule_id in sorted(selected_generated_rule_ids):
        candidate = authority_family_candidates.get(rule_id)
        if candidate is None:
            raise ValueError(
                "Compliance review eval generated diagnostic rule pack is missing generated "
                f"rule template {rule_id!r} for review {review_id}."
            )
        rules.append(_diagnostic_authority_family_rule(candidate))
    diagnostic_rule_pack = {
        "schema_version": "generated-compliance-rule-pack-v0",
        "rule_pack_id": f"generated-diagnostic-{base_rule_pack.get('rule_pack_id')}-{review_id}",
        "version": "applicability-v0",
        "title": f"Generated Diagnostic Rule Pack for {review_id}",
        "description": (
            "Eval-only generated rule pack assembled from explicit generated expectations while "
            "applicability validation remains non-reviewer-ready."
        ),
        "domain": base_rule_pack.get("domain"),
        "jurisdiction": base_rule_pack.get("jurisdiction"),
        "base_rule_pack_id": base_rule_pack.get("rule_pack_id"),
        "base_rule_pack_version": base_rule_pack.get("version"),
        "generated_rule_pack_id": (
            f"generated-diagnostic-{base_rule_pack.get('rule_pack_id')}-{review_id}"
        ),
        "generated_rule_pack_version": "applicability-v0",
        "source_set_id": source_set_id
        or str(authority_universe.get("source_set_id") or "").strip()
        or None,
        "review_id": review_id,
        "rules": rules,
    }
    validation = validate_rule_pack(diagnostic_rule_pack)
    if not validation.get("passed"):
        failed_checks = [
            str(check.get("name") or "")
            for check in validation.get("checks", [])
            if not check.get("passed")
        ]
        raise ValueError(
            "Compliance review eval generated diagnostic rule pack is invalid for review "
            f"{review_id}: {', '.join(failed_checks)}"
        )
    applicability_dir = review_dir / "applicability"
    applicability_dir.mkdir(parents=True, exist_ok=True)
    output_path = applicability_dir / "generated_rule_pack.json"
    _write_json(output_path, diagnostic_rule_pack)
    return output_path


def _generated_diagnostic_rule_ids(case: dict) -> set[str]:
    rule_ids = set()
    for field in (
        "expected_generated_statuses",
        "expected_generated_claim_types",
        "expected_generated_package_evidence",
        "expected_generated_source_evidence",
        "expected_generated_source_claim_links",
        "expected_generated_source_record_ids",
        "expected_generated_source_document_roles",
    ):
        value = case.get(field)
        if isinstance(value, dict):
            rule_ids.update(str(rule_id) for rule_id in value if str(rule_id).strip())
    return rule_ids


def _diagnostic_base_rule(
    *,
    rule_id: str,
    base_rule: dict,
    candidate: dict | None,
) -> dict:
    rule = deepcopy(base_rule)
    if isinstance(candidate, dict):
        rule_template = (
            candidate.get("rule_template") if isinstance(candidate.get("rule_template"), dict) else {}
        )
        authority_source_record_id = str(rule_template.get("authority_source_record_id") or "").strip()
        if authority_source_record_id:
            rule["authority_source_record_id"] = authority_source_record_id
        source_filters = deepcopy(
            rule_template.get("source_filters")
            if isinstance(rule_template.get("source_filters"), dict)
            else rule.get("source_filters") or {}
        )
        if authority_source_record_id and "source_record_id" not in source_filters:
            source_filters["source_record_id"] = authority_source_record_id
        if source_filters:
            rule["source_filters"] = source_filters
        supporting_source_record_ids = (
            (candidate.get("dependency_contract") or {}).get("supporting_source_record_ids")
            if isinstance(candidate.get("dependency_contract"), dict)
            else []
        )
        if supporting_source_record_ids:
            rule["supporting_source_record_ids"] = list(supporting_source_record_ids)
        package_section_expectations = candidate.get("package_section_filters")
        if isinstance(package_section_expectations, dict) and package_section_expectations:
            rule["package_section_expectations"] = deepcopy(package_section_expectations)
        source_claim_link_requirements = _source_claim_link_requirements(candidate)
        if source_claim_link_requirements:
            rule["source_claim_link_requirements"] = source_claim_link_requirements
    rule["generated_from_applicability"] = True
    rule["base_rule_id"] = rule_id
    rule["generated_rule_id"] = rule_id
    return rule


def _diagnostic_authority_family_rule(candidate: dict) -> dict:
    rule = _authority_family_template_rule(authority=candidate, candidate=candidate)
    rule["generated_from_applicability"] = True
    source_claim_link_requirements = _source_claim_link_requirements(candidate)
    if source_claim_link_requirements:
        rule["source_claim_link_requirements"] = source_claim_link_requirements
    package_section_expectations = candidate.get("package_section_filters")
    if isinstance(package_section_expectations, dict) and package_section_expectations:
        rule["package_section_expectations"] = deepcopy(package_section_expectations)
    rule["base_rule_id"] = None
    rule["generated_rule_id"] = str(rule.get("id") or "")
    return rule


def _string_map(value: dict) -> dict[str, str]:
    return {str(key): str(item) for key, item in value.items()}


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
