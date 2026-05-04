from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import copy
import hashlib
import json
import re

from .records import sha256_file
from .rule_packs import DEFAULT_RULE_PACK_PATH
from .rule_packs import GENERATED_RULE_PACK_SCHEMA_VERSION
from .rule_packs import load_rule_pack
from .rule_packs import validate_rule_pack


GENERATED_RULE_PACK_VALIDATION_SCHEMA_VERSION = "generated-rule-pack-validation-v0"
SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


@dataclass(frozen=True)
class ApplicabilityRulePackResult:
    review_id: str
    source_set_id: str | None
    applicability_dir: Path
    generated_rule_pack_path: Path
    generated_rule_pack_validation_path: Path
    summary: dict[str, Any]


def generate_applicability_rule_pack(
    *,
    output_dir: Path,
    review_id: str,
    source_set_id: str | None = None,
    base_rule_pack_path: Path | None = None,
    authority_universe_path: Path | None = None,
    decisions_path: Path | None = None,
    applicable_authorities_path: Path | None = None,
    non_applicable_authorities_path: Path | None = None,
    applicability_validation_path: Path | None = None,
    output_path: Path | None = None,
    validation_output_path: Path | None = None,
) -> ApplicabilityRulePackResult:
    """Generate a compliance rule pack from passing applicability artifacts."""

    output_dir = Path(output_dir)
    _validate_safe_segment(review_id, "review_id")
    paths = _artifact_paths(
        output_dir=output_dir,
        review_id=review_id,
        authority_universe_path=authority_universe_path,
        decisions_path=decisions_path,
        applicable_authorities_path=applicable_authorities_path,
        non_applicable_authorities_path=non_applicable_authorities_path,
        applicability_validation_path=applicability_validation_path,
        generated_rule_pack_path=output_path,
        validation_output_path=validation_output_path,
    )
    applicability_validation = _read_required_json(
        paths["applicability_validation"],
        "applicability validation",
    )
    if not applicability_validation.get("passed"):
        raise ValueError(
            "Cannot generate a rule pack because applicability_validation.json has not passed."
        )
    if source_set_id is None:
        source_set_id = str(applicability_validation.get("source_set_id") or "").strip()
    if source_set_id:
        _validate_safe_segment(source_set_id, "source_set_id")

    authority_universe = _read_required_json(paths["authority_universe"], "authority universe")
    applicable_authorities = _read_required_json(
        paths["applicable_authorities"],
        "applicable authorities",
    )
    non_applicable_authorities = _read_required_json(
        paths["non_applicable_authorities"],
        "non-applicable authorities",
    )
    decisions = _read_required_jsonl(paths["decisions"], "applicability decisions")
    current_validation_check = _check_applicability_validation_matches_current_artifacts(
        applicability_validation=applicability_validation,
        authority_universe=authority_universe,
        paths=paths,
    )
    if not current_validation_check["passed"]:
        failed_fields = [
            str(failure.get("details", {}).get("field") or "")
            for failure in current_validation_check["failures"]
        ]
        raise ValueError(
            "Cannot generate a rule pack because applicability_validation.json is stale "
            f"for current artifacts: {', '.join(sorted(set(failed_fields)))}"
        )
    base_rule_pack_path = _resolve_base_rule_pack_path(
        base_rule_pack_path=base_rule_pack_path,
        authority_universe=authority_universe,
    )
    base_rule_pack = load_rule_pack(base_rule_pack_path)
    base_rule_pack_validation = validate_rule_pack(base_rule_pack)
    if not base_rule_pack_validation.get("passed"):
        failed = [
            check.get("name")
            for check in base_rule_pack_validation.get("checks", [])
            if not check.get("passed")
        ]
        raise ValueError(f"Base rule pack failed validation: {', '.join(failed)}")

    generated_rule_pack = _generated_rule_pack(
        review_id=review_id,
        source_set_id=source_set_id,
        base_rule_pack_path=base_rule_pack_path,
        base_rule_pack=base_rule_pack,
        authority_universe=authority_universe,
        applicability_validation=applicability_validation,
        applicable_authorities=applicable_authorities,
        non_applicable_authorities=non_applicable_authorities,
        decisions=decisions,
        paths=paths,
    )
    _write_json(paths["generated_rule_pack"], generated_rule_pack)
    return validate_generated_rule_pack(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=source_set_id,
        base_rule_pack_path=base_rule_pack_path,
        authority_universe_path=paths["authority_universe"],
        applicable_authorities_path=paths["applicable_authorities"],
        non_applicable_authorities_path=paths["non_applicable_authorities"],
        applicability_validation_path=paths["applicability_validation"],
        generated_rule_pack_path=paths["generated_rule_pack"],
        validation_output_path=paths["generated_rule_pack_validation"],
        refresh_expected_hash=True,
    )


def validate_generated_rule_pack(
    *,
    output_dir: Path,
    review_id: str,
    source_set_id: str | None = None,
    base_rule_pack_path: Path | None = None,
    authority_universe_path: Path | None = None,
    applicable_authorities_path: Path | None = None,
    non_applicable_authorities_path: Path | None = None,
    applicability_validation_path: Path | None = None,
    generated_rule_pack_path: Path | None = None,
    validation_output_path: Path | None = None,
    refresh_expected_hash: bool = False,
) -> ApplicabilityRulePackResult:
    """Validate an existing generated rule pack against current applicability artifacts."""

    output_dir = Path(output_dir)
    _validate_safe_segment(review_id, "review_id")
    paths = _artifact_paths(
        output_dir=output_dir,
        review_id=review_id,
        authority_universe_path=authority_universe_path,
        decisions_path=None,
        applicable_authorities_path=applicable_authorities_path,
        non_applicable_authorities_path=non_applicable_authorities_path,
        applicability_validation_path=applicability_validation_path,
        generated_rule_pack_path=generated_rule_pack_path,
        validation_output_path=validation_output_path,
    )
    applicability_dir = paths["applicability_dir"]
    generated_rule_pack = _read_json_if_exists(paths["generated_rule_pack"])
    applicability_validation = _read_json_if_exists(paths["applicability_validation"])
    authority_universe = _read_json_if_exists(paths["authority_universe"])
    applicable_authorities = _read_json_if_exists(paths["applicable_authorities"])
    non_applicable_authorities = _read_json_if_exists(paths["non_applicable_authorities"])
    if source_set_id is None:
        source_set_id = _first_present(
            generated_rule_pack.get("source_set_id"),
            applicability_validation.get("source_set_id"),
            applicable_authorities.get("source_set_id"),
            authority_universe.get("source_set_id"),
        )
    if source_set_id:
        _validate_safe_segment(str(source_set_id), "source_set_id")
    base_rule_pack_path = _resolve_base_rule_pack_path(
        base_rule_pack_path=base_rule_pack_path,
        authority_universe=authority_universe,
    )
    previous_validation = _read_json_if_exists(paths["generated_rule_pack_validation"])
    current_rule_pack_hash = (
        sha256_file(paths["generated_rule_pack"])
        if paths["generated_rule_pack"].exists()
        else None
    )
    previous_expected_hash = (
        (previous_validation.get("summary") or {}).get("expected_generated_rule_pack_sha256")
        or (previous_validation.get("summary") or {}).get("generated_rule_pack_sha256")
    )
    expected_rule_pack_hash = (
        current_rule_pack_hash if refresh_expected_hash else previous_expected_hash
    )

    checks = _validation_checks(
        review_id=review_id,
        source_set_id=str(source_set_id) if source_set_id else None,
        paths=paths,
        base_rule_pack_path=base_rule_pack_path,
        generated_rule_pack=generated_rule_pack,
        applicability_validation=applicability_validation,
        authority_universe=authority_universe,
        applicable_authorities=applicable_authorities,
        non_applicable_authorities=non_applicable_authorities,
        current_rule_pack_hash=current_rule_pack_hash,
        expected_rule_pack_hash=expected_rule_pack_hash,
    )
    failures = [
        failure
        for check in checks
        for failure in check.get("failures", [])
        if isinstance(failure, dict)
    ]
    failure_counts = Counter(str(failure.get("failure_category") or "") for failure in failures)
    passed = all(check["passed"] for check in checks)
    generated_rules = (
        generated_rule_pack.get("rules")
        if isinstance(generated_rule_pack.get("rules"), list)
        else []
    )
    summary = {
        "schema_version": GENERATED_RULE_PACK_VALIDATION_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": review_id,
        "source_set_id": source_set_id,
        "passed": passed,
        "generated_rule_pack_ready": passed,
        "generated_rule_pack_id": generated_rule_pack.get("generated_rule_pack_id")
        or generated_rule_pack.get("rule_pack_id"),
        "generated_rule_pack_sha256": current_rule_pack_hash,
        "expected_generated_rule_pack_sha256": expected_rule_pack_hash,
        "applicability_run_id": applicability_validation.get("applicability_run_id"),
        "applicability_validation_sha256": _optional_file_sha256(
            paths["applicability_validation"]
        ),
        "base_rule_pack_id": generated_rule_pack.get("base_rule_pack_id"),
        "base_rule_pack_version": generated_rule_pack.get("base_rule_pack_version"),
        "base_rule_pack_sha256": _optional_file_sha256(base_rule_pack_path),
        "authority_universe_sha256": authority_universe.get("authority_universe_sha256"),
        "applicable_authorities_sha256": _optional_file_sha256(
            paths["applicable_authorities"]
        ),
        "non_applicable_authorities_sha256": _optional_file_sha256(
            paths["non_applicable_authorities"]
        ),
        "package_fact_graph_sha256": _hash_from_validation(
            applicability_validation,
            "package_fact_graph_sha256",
        ),
        "retrieval_trace_sha256": _hash_from_validation(
            applicability_validation,
            "retrieval_trace_sha256",
        ),
        "graph_trace_sha256": _hash_from_validation(
            applicability_validation,
            "graph_trace_sha256",
        ),
        "search_coverage_certificates_sha256": _hash_from_validation(
            applicability_validation,
            "search_coverage_certificates_sha256",
        ),
        "package_manifest_sha256": _hash_from_validation(
            applicability_validation,
            "package_manifest_sha256",
        ),
        "package_chunks_sha256": _hash_from_validation(
            applicability_validation,
            "package_chunks_sha256",
        ),
        "catalog_sha256": _hash_from_validation(applicability_validation, "catalog_sha256"),
        "applicability_provenance_sha256": _hash_from_validation(
            applicability_validation,
            "applicability_provenance_sha256",
        ),
        "generated_rule_count": len(generated_rules),
        "applicable_authority_count": len(_authority_ids(applicable_authorities)),
        "non_applicable_authority_count": len(_authority_ids(non_applicable_authorities)),
        "failure_category_counts": dict(sorted(failure_counts.items())),
        "generated_rule_pack_path": str(paths["generated_rule_pack"]),
        "generated_rule_pack_validation_path": str(paths["generated_rule_pack_validation"]),
    }
    payload = {
        "schema_version": GENERATED_RULE_PACK_VALIDATION_SCHEMA_VERSION,
        "created_at": summary["created_at"],
        "review_id": review_id,
        "source_set_id": source_set_id,
        "passed": passed,
        "summary": summary,
        "artifact_paths": {
            "authority_universe": str(paths["authority_universe"]),
            "applicable_authorities": str(paths["applicable_authorities"]),
            "non_applicable_authorities": str(paths["non_applicable_authorities"]),
            "applicability_validation": str(paths["applicability_validation"]),
            "generated_rule_pack": str(paths["generated_rule_pack"]),
            "base_rule_pack": str(base_rule_pack_path),
        },
        "checks": checks,
        "failures": failures,
    }
    _write_json(paths["generated_rule_pack_validation"], payload)
    return ApplicabilityRulePackResult(
        review_id=review_id,
        source_set_id=str(source_set_id) if source_set_id else None,
        applicability_dir=applicability_dir,
        generated_rule_pack_path=paths["generated_rule_pack"],
        generated_rule_pack_validation_path=paths["generated_rule_pack_validation"],
        summary=summary,
    )


def _generated_rule_pack(
    *,
    review_id: str,
    source_set_id: str | None,
    base_rule_pack_path: Path,
    base_rule_pack: dict[str, Any],
    authority_universe: dict[str, Any],
    applicability_validation: dict[str, Any],
    applicable_authorities: dict[str, Any],
    non_applicable_authorities: dict[str, Any],
    decisions: list[dict[str, Any]],
    paths: dict[str, Path],
) -> dict[str, Any]:
    candidates_by_id = {
        str(candidate.get("candidate_authority_id") or ""): candidate
        for candidate in authority_universe.get("candidate_authorities") or []
        if isinstance(candidate, dict)
    }
    decisions_by_candidate = {
        str(decision.get("candidate_authority_id") or ""): decision
        for decision in decisions
        if isinstance(decision, dict)
    }
    base_rules_by_id = {
        str(rule.get("id") or ""): rule
        for rule in base_rule_pack.get("rules") or []
        if isinstance(rule, dict)
    }
    validation_hashes = applicability_validation.get("hashes") or {}
    artifact_hashes = _generated_artifact_hashes(
        validation_hashes=validation_hashes,
        authority_universe=authority_universe,
        paths=paths,
        base_rule_pack_path=base_rule_pack_path,
    )
    rules = []
    for authority in applicable_authorities.get("authorities") or []:
        if not isinstance(authority, dict):
            continue
        candidate_id = str(authority.get("candidate_authority_id") or "")
        candidate = candidates_by_id.get(candidate_id, {})
        decision = decisions_by_candidate.get(candidate_id, {})
        if authority.get("candidate_authority_type") == "forest_plan_component":
            rule = _forest_plan_component_rule(authority=authority, candidate=candidate)
            base_rule_id = None
        elif authority.get("candidate_authority_type") == "authority_family_rule_template":
            rule = _authority_family_template_rule(authority=authority, candidate=candidate)
            base_rule_id = None
        else:
            rule_id = str((authority.get("rule_template") or {}).get("rule_id") or "")
            base_rule = base_rules_by_id.get(rule_id)
            if not base_rule:
                raise ValueError(f"Missing base rule for applicable authority: {rule_id}")
            rule = copy.deepcopy(base_rule)
            base_rule_id = rule_id
        rule["applicability"] = _rule_applicability_metadata(
            authority=authority,
            candidate=candidate,
            decision=decision,
            artifact_hashes=artifact_hashes,
        )
        rule["source_claim_link_requirements"] = _source_claim_link_requirements(candidate)
        rule["package_section_expectations"] = candidate.get("package_section_filters") or {}
        rule["base_rule_id"] = base_rule_id
        rule["generated_rule_id"] = rule.get("id")
        rule["base_rule_pack_id"] = base_rule_pack.get("rule_pack_id")
        rule["base_rule_pack_version"] = base_rule_pack.get("version")
        rule["applicability_decision_id"] = authority.get("decision_id")
        rule["candidate_authority_id"] = candidate_id
        authority_family_ids = _authority_family_ids_for_authority(
            authority=authority,
            candidate=candidate,
            decision=decision,
        )
        rule["authority_family_ids"] = authority_family_ids
        rule["authority_family_id"] = (
            authority_family_ids[0] if authority_family_ids else None
        )
        rule["applicability_artifact_hashes"] = dict(artifact_hashes)
        rule["generated_from_applicability"] = True
        rules.append(rule)
    rules.sort(key=lambda rule: str(rule.get("id") or ""))
    validation_hash = sha256_file(paths["applicability_validation"])
    applicable_hash = sha256_file(paths["applicable_authorities"])
    non_applicable_hash = sha256_file(paths["non_applicable_authorities"])
    generated_rule_pack_id = _safe_id(
        f"generated-{base_rule_pack.get('rule_pack_id')}-{review_id}"
    )
    generated_version = "applicability-v0"
    baseline_source_record_ids = sorted(
        {
            str(rule.get("authority_source_record_id") or "")
            for rule in rules
            if rule.get("applicability_mode") == "baseline"
            and str(rule.get("authority_source_record_id") or "").strip()
        }
    )
    return {
        "schema_version": GENERATED_RULE_PACK_SCHEMA_VERSION,
        "rule_pack_id": generated_rule_pack_id,
        "version": generated_version,
        "title": f"Generated Applicability Rule Pack for {review_id}",
        "description": (
            "Generated from validated applicable-authorities artifacts. "
            "Non-applicable authorities remain in non_applicable_authorities.json."
        ),
        "domain": base_rule_pack.get("domain"),
        "jurisdiction": base_rule_pack.get("jurisdiction"),
        "base_rule_pack_id": base_rule_pack.get("rule_pack_id"),
        "base_rule_pack_version": base_rule_pack.get("version"),
        "base_rule_pack_sha256": sha256_file(base_rule_pack_path),
        "generated_rule_pack_id": generated_rule_pack_id,
        "generated_rule_pack_version": generated_version,
        "applicability_run_id": applicability_validation.get("applicability_run_id"),
        "applicability_validation_sha256": validation_hash,
        "authority_universe_sha256": validation_hashes.get("authority_universe_sha256"),
        "applicable_authorities_sha256": applicable_hash,
        "non_applicable_authorities_sha256": non_applicable_hash,
        "applicability_provenance_sha256": validation_hashes.get(
            "applicability_provenance_sha256"
        ),
        "package_fact_graph_sha256": validation_hashes.get("package_fact_graph_sha256"),
        "retrieval_trace_sha256": validation_hashes.get("retrieval_trace_sha256"),
        "graph_trace_sha256": validation_hashes.get("graph_trace_sha256"),
        "search_coverage_certificates_sha256": validation_hashes.get(
            "search_coverage_certificates_sha256"
        ),
        "package_manifest_sha256": validation_hashes.get("package_manifest_sha256"),
        "package_chunks_sha256": validation_hashes.get("package_chunks_sha256"),
        "catalog_sha256": validation_hashes.get("catalog_sha256"),
        "source_set_id": source_set_id,
        "review_id": review_id,
        "applicable_authority_count": len(_authority_ids(applicable_authorities)),
        "non_applicable_authority_count": len(_authority_ids(non_applicable_authorities)),
        "baseline_source_record_ids": baseline_source_record_ids,
        "artifact_hashes": artifact_hashes,
        "rules": rules,
    }


def _validation_checks(
    *,
    review_id: str,
    source_set_id: str | None,
    paths: dict[str, Path],
    base_rule_pack_path: Path,
    generated_rule_pack: dict[str, Any],
    applicability_validation: dict[str, Any],
    authority_universe: dict[str, Any],
    applicable_authorities: dict[str, Any],
    non_applicable_authorities: dict[str, Any],
    current_rule_pack_hash: str | None,
    expected_rule_pack_hash: str | None,
) -> list[dict[str, Any]]:
    generated_rules = (
        generated_rule_pack.get("rules")
        if isinstance(generated_rule_pack.get("rules"), list)
        else []
    )
    return [
        _check_required_artifacts(paths, base_rule_pack_path),
        _check_applicability_validation_passed(applicability_validation),
        _check_applicability_validation_matches_current_artifacts(
            applicability_validation=applicability_validation,
            authority_universe=authority_universe,
            paths=paths,
        ),
        _check_generated_rule_pack_schema(generated_rule_pack),
        _check_generated_rule_pack_hash(
            current_hash=current_rule_pack_hash,
            expected_hash=expected_rule_pack_hash,
        ),
        _check_generated_rule_pack_identity(
            review_id=review_id,
            source_set_id=source_set_id,
            generated_rule_pack=generated_rule_pack,
            applicability_validation=applicability_validation,
        ),
        _check_rule_count_matches_applicable_authorities(
            generated_rules=generated_rules,
            applicable_authorities=applicable_authorities,
        ),
        _check_generated_rules_trace_to_applicable_decisions(
            generated_rules=generated_rules,
            applicable_authorities=applicable_authorities,
        ),
        _check_generated_rules_carry_required_metadata(generated_rules),
        _check_non_applicable_authorities_absent(
            generated_rules=generated_rules,
            non_applicable_authorities=non_applicable_authorities,
        ),
        _check_source_claim_links_present(generated_rules),
        _check_hashes_match_current_artifacts(
            generated_rule_pack=generated_rule_pack,
            applicability_validation=applicability_validation,
            authority_universe=authority_universe,
            paths=paths,
            base_rule_pack_path=base_rule_pack_path,
        ),
    ]


def _check_required_artifacts(paths: dict[str, Path], base_rule_pack_path: Path) -> dict[str, Any]:
    required = {
        "authority_universe": paths["authority_universe"],
        "applicable_authorities": paths["applicable_authorities"],
        "non_applicable_authorities": paths["non_applicable_authorities"],
        "applicability_validation": paths["applicability_validation"],
        "generated_rule_pack": paths["generated_rule_pack"],
        "base_rule_pack": base_rule_pack_path,
    }
    missing = [
        {"artifact": name, "path": str(path)}
        for name, path in required.items()
        if not path.exists()
    ]
    return _check(
        "required_generated_rule_pack_artifacts_exist",
        not missing,
        [
            _failure(
                "missing_generated_rule_pack_artifact",
                artifact=entry["artifact"],
                path=entry["path"],
            )
            for entry in missing
        ],
        {"missing": missing},
    )


def _check_applicability_validation_passed(validation: dict[str, Any]) -> dict[str, Any]:
    passed = validation.get("schema_version") == "applicability-validation-v0" and bool(
        validation.get("passed")
    )
    return _check(
        "applicability_validation_passed",
        passed,
        []
        if passed
        else [
            _failure(
                "applicability_validation_failed",
                details={
                    "schema_version": validation.get("schema_version"),
                    "passed": validation.get("passed"),
                },
            )
        ],
        {"passed": validation.get("passed")},
    )


def _check_applicability_validation_matches_current_artifacts(
    *,
    applicability_validation: dict[str, Any],
    authority_universe: dict[str, Any],
    paths: dict[str, Path],
) -> dict[str, Any]:
    recorded_hashes = (
        applicability_validation.get("hashes")
        if isinstance(applicability_validation.get("hashes"), dict)
        else {}
    )
    validation_paths = (
        applicability_validation.get("artifact_paths")
        if isinstance(applicability_validation.get("artifact_paths"), dict)
        else {}
    )
    expected_pairs = {
        "authority_universe_sha256": authority_universe.get("authority_universe_sha256"),
        "applicable_authorities_sha256": _optional_file_sha256(
            paths["applicable_authorities"]
        ),
        "non_applicable_authorities_sha256": _optional_file_sha256(
            paths["non_applicable_authorities"]
        ),
        "applicability_decisions_sha256": _optional_file_sha256(
            _validation_artifact_path(validation_paths, "decisions")
        ),
        "retrieval_trace_sha256": _optional_file_sha256(
            _validation_artifact_path(validation_paths, "retrieval_trace")
        ),
        "graph_trace_sha256": _optional_file_sha256(
            _validation_artifact_path(validation_paths, "graph_trace")
        ),
        "package_manifest_sha256": _first_present(
            _json_field_from_path(
                _validation_artifact_path(validation_paths, "package_applicability_context"),
                "package_manifest_sha256",
            ),
            _json_field_from_path(
                _validation_artifact_path(validation_paths, "package_fact_graph"),
                "package_manifest_sha256",
            ),
        ),
        "package_chunks_sha256": _first_present(
            _json_field_from_path(
                _validation_artifact_path(validation_paths, "package_applicability_context"),
                "package_chunks_sha256",
            ),
            _json_field_from_path(
                _validation_artifact_path(validation_paths, "package_fact_graph"),
                "package_chunks_sha256",
            ),
        ),
        "package_context_sha256": _json_field_from_path(
            _validation_artifact_path(validation_paths, "package_applicability_context"),
            "package_context_sha256",
        ),
        "package_fact_graph_sha256": _json_field_from_path(
            _validation_artifact_path(validation_paths, "package_fact_graph"),
            "package_fact_graph_sha256",
        ),
        "search_coverage_certificates_sha256": _optional_file_sha256(
            _validation_artifact_path(validation_paths, "search_coverage_certificates")
        ),
        "applicability_provenance_sha256": _optional_file_sha256(
            _validation_artifact_path(validation_paths, "provenance")
        ),
        "catalog_sha256": authority_universe.get("catalog_sha256"),
        "source_claims_sha256": authority_universe.get("source_claims_sha256"),
        "rule_claim_links_sha256": authority_universe.get("rule_claim_links_sha256"),
        "forest_plan_component_inventory_sha256": authority_universe.get(
            "forest_plan_component_inventory_sha256"
        ),
    }
    failures = []
    for field, expected in expected_pairs.items():
        actual = recorded_hashes.get(field)
        if expected and actual != expected:
            failures.append(
                _failure(
                    "generated_rule_pack_stale",
                    details={"field": field, "expected": expected, "actual": actual},
                )
            )
    return _check(
        "applicability_validation_hashes_match_current_artifacts",
        not failures,
        failures,
        {"checked_fields": sorted(expected_pairs)},
    )


def _check_generated_rule_pack_schema(rule_pack: dict[str, Any]) -> dict[str, Any]:
    rule_pack_validation = validate_rule_pack(rule_pack) if rule_pack else {"passed": False}
    failures = []
    if rule_pack.get("schema_version") != GENERATED_RULE_PACK_SCHEMA_VERSION:
        failures.append(
            _failure(
                "generated_rule_pack_schema_gap",
                details={
                    "field": "schema_version",
                    "expected": GENERATED_RULE_PACK_SCHEMA_VERSION,
                    "actual": rule_pack.get("schema_version"),
                },
            )
        )
    if not rule_pack_validation.get("passed"):
        failures.append(
            _failure(
                "generated_rule_pack_schema_gap",
                details={
                    "failed_checks": [
                        check.get("name")
                        for check in rule_pack_validation.get("checks", [])
                        if not check.get("passed")
                    ]
                },
            )
        )
    return _check(
        "generated_rule_pack_schema_valid",
        not failures,
        failures,
        {"rule_pack_validation": rule_pack_validation},
    )


def _check_generated_rule_pack_hash(
    *,
    current_hash: str | None,
    expected_hash: str | None,
) -> dict[str, Any]:
    passed = bool(current_hash) and bool(expected_hash) and current_hash == expected_hash
    return _check(
        "generated_rule_pack_hash_matches_recorded_validation",
        passed,
        []
        if passed
        else [
            _failure(
                "generated_rule_pack_mismatch",
                details={
                    "expected": expected_hash,
                    "actual": current_hash,
                    "reason": "missing_or_mismatched_recorded_hash"
                    if not expected_hash or current_hash != expected_hash
                    else None,
                },
            )
        ],
        {"expected": expected_hash, "actual": current_hash},
    )


def _check_generated_rule_pack_identity(
    *,
    review_id: str,
    source_set_id: str | None,
    generated_rule_pack: dict[str, Any],
    applicability_validation: dict[str, Any],
) -> dict[str, Any]:
    failures = []
    expected = {
        "review_id": review_id,
        "source_set_id": source_set_id,
        "applicability_run_id": applicability_validation.get("applicability_run_id"),
    }
    for field, expected_value in expected.items():
        actual = generated_rule_pack.get(field)
        if expected_value and actual != expected_value:
            failures.append(
                _failure(
                    "generated_rule_pack_stale",
                    details={"field": field, "expected": expected_value, "actual": actual},
                )
            )
    return _check(
        "generated_rule_pack_identity_matches_applicability_run",
        not failures,
        failures,
        {"expected": expected},
    )


def _check_rule_count_matches_applicable_authorities(
    *,
    generated_rules: list[dict[str, Any]],
    applicable_authorities: dict[str, Any],
) -> dict[str, Any]:
    expected = len(_authority_ids(applicable_authorities))
    actual = len(generated_rules)
    return _check(
        "generated_rule_count_matches_applicable_authority_count",
        expected == actual and expected > 0,
        []
        if expected == actual and expected > 0
        else [
            _failure(
                "generated_rule_count_mismatch",
                details={"expected": expected, "actual": actual},
            )
        ],
        {"expected": expected, "actual": actual},
    )


def _check_generated_rules_trace_to_applicable_decisions(
    *,
    generated_rules: list[dict[str, Any]],
    applicable_authorities: dict[str, Any],
) -> dict[str, Any]:
    applicable_by_candidate = {
        str(authority.get("candidate_authority_id") or ""): authority
        for authority in applicable_authorities.get("authorities") or []
        if isinstance(authority, dict)
    }
    failures = []
    for rule in generated_rules:
        if not isinstance(rule, dict):
            failures.append(_failure("generated_rule_trace_gap"))
            continue
        metadata = rule.get("applicability") if isinstance(rule.get("applicability"), dict) else {}
        candidate_id = str(
            metadata.get("candidate_authority_id") or rule.get("candidate_authority_id") or ""
        )
        authority = applicable_by_candidate.get(candidate_id)
        if not authority:
            failures.append(
                _failure(
                    "generated_rule_trace_gap",
                    details={"rule_id": rule.get("id"), "candidate_authority_id": candidate_id},
                )
            )
            continue
        if metadata.get("decision_id") != authority.get("decision_id"):
            failures.append(
                _failure(
                    "generated_rule_trace_gap",
                    details={
                        "rule_id": rule.get("id"),
                        "field": "decision_id",
                        "expected": authority.get("decision_id"),
                        "actual": metadata.get("decision_id"),
                    },
                )
            )
    return _check(
        "all_generated_rules_trace_to_applicable_decisions",
        not failures,
        failures,
        {"failure_count": len(failures)},
    )


def _check_generated_rules_carry_required_metadata(
    generated_rules: list[dict[str, Any]],
) -> dict[str, Any]:
    required_scalar_fields = {
        "generated_rule_id",
        "base_rule_pack_id",
        "base_rule_pack_version",
        "applicability_decision_id",
        "candidate_authority_id",
    }
    required_object_fields = {
        "source_claim_link_requirements",
        "package_section_expectations",
        "applicability_artifact_hashes",
    }
    required_hash_fields = {
        "base_rule_pack_sha256",
        "applicability_validation_sha256",
        "authority_universe_sha256",
        "applicable_authorities_sha256",
        "non_applicable_authorities_sha256",
        "package_fact_graph_sha256",
        "retrieval_trace_sha256",
        "graph_trace_sha256",
        "search_coverage_certificates_sha256",
        "package_manifest_sha256",
        "package_chunks_sha256",
        "catalog_sha256",
        "applicability_provenance_sha256",
    }
    failures = []
    for rule in generated_rules:
        if not isinstance(rule, dict):
            failures.append(
                _failure(
                    "generated_rule_metadata_gap",
                    details={"reason": "rule_is_not_object"},
                )
            )
            continue
        missing_rule_fields = []
        missing_rule_fields.extend(
            field for field in required_scalar_fields if not rule.get(field)
        )
        missing_rule_fields.extend(
            field
            for field in required_object_fields
            if field not in rule or not isinstance(rule.get(field), dict)
        )
        metadata = (
            rule.get("applicability") if isinstance(rule.get("applicability"), dict) else {}
        )
        if "base_rule_id" not in rule:
            missing_rule_fields.append("base_rule_id")
        elif (
            metadata.get("candidate_authority_type")
            not in {"forest_plan_component", "authority_family_rule_template"}
            and not rule.get("base_rule_id")
        ):
            missing_rule_fields.append("base_rule_id")
        if rule.get("generated_rule_id") != rule.get("id"):
            missing_rule_fields.append("generated_rule_id_matches_id")
        if not metadata.get("retrieval_trace_ids"):
            missing_rule_fields.append("applicability.retrieval_trace_ids")
        if not metadata.get("source_record_ids"):
            missing_rule_fields.append("applicability.source_record_ids")
        if not metadata.get("document_roles"):
            missing_rule_fields.append("applicability.document_roles")
        hashes = (
            rule.get("applicability_artifact_hashes")
            if isinstance(rule.get("applicability_artifact_hashes"), dict)
            else {}
        )
        missing_hash_fields = sorted(
            field for field in required_hash_fields if not hashes.get(field)
        )
        if metadata.get("artifact_hashes") != hashes:
            missing_rule_fields.append("applicability.artifact_hashes")
        if missing_rule_fields or missing_hash_fields:
            failures.append(
                _failure(
                    "generated_rule_metadata_gap",
                    details={
                        "rule_id": rule.get("id"),
                        "missing_rule_fields": sorted(set(missing_rule_fields)),
                        "missing_hash_fields": missing_hash_fields,
                    },
                )
            )
    return _check(
        "generated_rules_carry_required_applicability_metadata",
        not failures,
        failures,
        {"failure_count": len(failures)},
    )


def _check_non_applicable_authorities_absent(
    *,
    generated_rules: list[dict[str, Any]],
    non_applicable_authorities: dict[str, Any],
) -> dict[str, Any]:
    non_applicable_ids = _authority_ids(non_applicable_authorities)
    present = []
    for rule in generated_rules:
        metadata = rule.get("applicability") if isinstance(rule.get("applicability"), dict) else {}
        candidate_id = str(
            metadata.get("candidate_authority_id") or rule.get("candidate_authority_id") or ""
        )
        if candidate_id in non_applicable_ids:
            present.append({"rule_id": rule.get("id"), "candidate_authority_id": candidate_id})
    return _check(
        "non_applicable_authorities_are_absent_from_generated_rules",
        not present,
        [
            _failure(
                "non_applicable_authority_in_rule_pack",
                details=entry,
            )
            for entry in present
        ],
        {"present": present},
    )


def _check_source_claim_links_present(generated_rules: list[dict[str, Any]]) -> dict[str, Any]:
    failures = []
    for rule in generated_rules:
        requirement = (
            rule.get("source_claim_link_requirements")
            if isinstance(rule.get("source_claim_link_requirements"), dict)
            else {}
        )
        if requirement.get("required") and not requirement.get("source_claim_link_ids"):
            failures.append(
                _failure(
                    "source_claim_link_gap",
                    details={"rule_id": rule.get("id")},
                )
            )
    return _check(
        "source_claim_links_present_for_claim_bearing_rules",
        not failures,
        failures,
        {"failure_count": len(failures)},
    )


def _check_hashes_match_current_artifacts(
    *,
    generated_rule_pack: dict[str, Any],
    applicability_validation: dict[str, Any],
    authority_universe: dict[str, Any],
    paths: dict[str, Path],
    base_rule_pack_path: Path,
) -> dict[str, Any]:
    validation_hashes = applicability_validation.get("hashes") or {}
    expected_pairs = {
        "applicability_validation_sha256": _optional_file_sha256(
            paths["applicability_validation"]
        ),
        "authority_universe_sha256": authority_universe.get("authority_universe_sha256"),
        "applicable_authorities_sha256": _optional_file_sha256(
            paths["applicable_authorities"]
        ),
        "non_applicable_authorities_sha256": _optional_file_sha256(
            paths["non_applicable_authorities"]
        ),
        "base_rule_pack_sha256": _optional_file_sha256(base_rule_pack_path),
        "package_fact_graph_sha256": validation_hashes.get("package_fact_graph_sha256"),
        "retrieval_trace_sha256": validation_hashes.get("retrieval_trace_sha256"),
        "graph_trace_sha256": validation_hashes.get("graph_trace_sha256"),
        "search_coverage_certificates_sha256": validation_hashes.get(
            "search_coverage_certificates_sha256"
        ),
        "applicability_provenance_sha256": validation_hashes.get(
            "applicability_provenance_sha256"
        ),
        "package_manifest_sha256": validation_hashes.get("package_manifest_sha256"),
        "package_chunks_sha256": validation_hashes.get("package_chunks_sha256"),
        "catalog_sha256": validation_hashes.get("catalog_sha256"),
    }
    failures = []
    for field, expected in expected_pairs.items():
        actual = generated_rule_pack.get(field)
        if expected and actual != expected:
            failures.append(
                _failure(
                    "generated_rule_pack_stale",
                    details={"field": field, "expected": expected, "actual": actual},
                )
            )
    return _check(
        "generated_rule_pack_hashes_match_current_applicability_artifacts",
        not failures,
        failures,
        {"checked_fields": sorted(expected_pairs)},
    )


def _rule_applicability_metadata(
    *,
    authority: dict[str, Any],
    candidate: dict[str, Any],
    decision: dict[str, Any],
    artifact_hashes: dict[str, Any],
) -> dict[str, Any]:
    authority_family_ids = _authority_family_ids_for_authority(
        authority=authority,
        candidate=candidate,
        decision=decision,
    )
    return {
        "decision_id": authority.get("decision_id"),
        "candidate_authority_id": authority.get("candidate_authority_id"),
        "candidate_authority_type": authority.get("candidate_authority_type"),
        "authority_family_ids": authority_family_ids,
        "authority_family_id": authority_family_ids[0] if authority_family_ids else None,
        "status": authority.get("status"),
        "basis_type": authority.get("basis_type"),
        "applicability_basis": authority.get("applicability_basis"),
        "retrieval_trace_ids": _strings(authority.get("retrieval_trace_ids")),
        "graph_path_ids": _strings(authority.get("graph_path_ids")),
        "source_record_ids": _strings(authority.get("source_record_ids")),
        "document_roles": _strings([authority.get("authority_document_role")]),
        "package_evidence_refs": _evidence_refs(authority.get("package_evidence_spans")),
        "source_evidence_refs": _evidence_refs(authority.get("source_library_evidence_spans")),
        "search_coverage_certificate_ids": _strings(
            authority.get("search_coverage_certificate_ids")
        ),
        "human_adjudication_refs": authority.get("human_adjudication_refs") or [],
        "source_claim_link_requirements": _source_claim_link_requirements(candidate),
        "package_section_expectations": candidate.get("package_section_filters") or {},
        "forest_plan": authority.get("forest_plan") or None,
        "freshness": decision.get("freshness") if isinstance(decision, dict) else {},
        "artifact_hashes": dict(artifact_hashes),
    }


def _forest_plan_component_rule(
    *,
    authority: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    forest_plan = authority.get("forest_plan") if isinstance(authority.get("forest_plan"), dict) else {}
    filters = candidate.get("package_section_filters") or {}
    terms = _strings(filters.get("package_evidence_terms")) or _strings(
        [
            forest_plan.get("section_heading"),
            *(_strings(forest_plan.get("geographic_area_ids"))),
            *(_strings(forest_plan.get("management_area_ids"))),
            *(_strings(forest_plan.get("overlay_ids"))),
        ]
    )
    component_id = str(forest_plan.get("component_id") or authority.get("candidate_authority_id"))
    source_record_id = _first_present(_strings(authority.get("source_record_ids")))
    section_heading = str(forest_plan.get("section_heading") or component_id)
    rule_id = _safe_id(f"forest_plan_component_{component_id}")
    return {
        "id": rule_id,
        "title": f"Forest Plan component applies: {section_heading}",
        "authority_category": "forest_plan",
        "authority_source_record_id": source_record_id,
        "applicability_mode": "conditional",
        "question": f"Does the EA package address Forest Plan component {component_id}?",
        "requirement": (
            f"The EA package should address the applicable Forest Plan component: {section_heading}."
        ),
        "severity": "medium",
        "package_query": " ".join(terms) if terms else section_heading,
        "package_terms": terms or [section_heading],
        "applies_if_package_terms": terms or [section_heading],
        "source_query": f"{section_heading} Forest Plan component",
        "source_filters": {
            "document_role": "forest_plan",
            "source_record_id": source_record_id,
        },
        "evidence_expectation": (
            "A supported finding requires one source-library Forest Plan span and one package span."
        ),
    }


def _authority_family_template_rule(
    *,
    authority: dict[str, Any],
    candidate: dict[str, Any],
) -> dict[str, Any]:
    rule_template = (
        authority.get("rule_template")
        if isinstance(authority.get("rule_template"), dict)
        else {}
    )
    source_record_id = (
        str(rule_template.get("authority_source_record_id") or "").strip()
        or _first_present(_strings(authority.get("source_record_ids")))
    )
    package_filters = (
        candidate.get("package_section_filters")
        if isinstance(candidate.get("package_section_filters"), dict)
        else {}
    )
    source_filters = (
        rule_template.get("source_filters")
        if isinstance(rule_template.get("source_filters"), dict)
        else {}
    )
    if source_record_id and "source_record_id" not in source_filters:
        source_filters = {**source_filters, "source_record_id": source_record_id}
    return {
        "id": _safe_id(str(rule_template.get("rule_id") or authority["candidate_authority_id"])),
        "title": rule_template.get("title"),
        "authority_category": rule_template.get("authority_category")
        or authority.get("authority_category"),
        "authority_source_record_id": source_record_id,
        "applicability_mode": rule_template.get("applicability_mode") or "conditional",
        "question": rule_template.get("question"),
        "requirement": rule_template.get("requirement"),
        "severity": rule_template.get("severity") or "medium",
        "package_query": rule_template.get("package_query")
        or package_filters.get("package_query")
        or rule_template.get("title"),
        "package_terms": _strings(rule_template.get("package_terms"))
        or _strings(package_filters.get("package_terms")),
        "package_section_terms": _strings(rule_template.get("package_section_terms"))
        or _strings(package_filters.get("package_section_terms")),
        "applies_if_package_terms": _strings(
            rule_template.get("applies_if_package_terms")
        ),
        "applies_if_package_term_groups": rule_template.get(
            "applies_if_package_term_groups",
            [],
        ),
        "does_not_apply_if_package_terms": _strings(
            rule_template.get("does_not_apply_if_package_terms")
        ),
        "source_query": rule_template.get("source_query") or rule_template.get("title"),
        "source_filters": source_filters,
        "supporting_source_record_ids": _strings(
            (candidate.get("dependency_contract") or {}).get("supporting_source_record_ids")
        ),
        "evidence_expectation": rule_template.get("evidence_expectation"),
    }


def _authority_family_ids_for_authority(
    *,
    authority: dict[str, Any],
    candidate: dict[str, Any],
    decision: dict[str, Any],
) -> list[str]:
    family_ids: set[str] = set()
    for payload in (authority, candidate, decision):
        family_ids.update(_strings(payload.get("authority_family_ids")))
        family_ids.update(_strings([payload.get("authority_family_id")]))
        rule_template = payload.get("rule_template")
        if isinstance(rule_template, dict):
            family_ids.update(_strings(rule_template.get("authority_family_ids")))
            family_ids.update(_strings([rule_template.get("authority_family_id")]))
    return sorted(family_ids)


def _source_claim_link_requirements(candidate: dict[str, Any]) -> dict[str, Any]:
    required = (
        candidate.get("required_source_evidence")
        if isinstance(candidate.get("required_source_evidence"), dict)
        else {}
    )
    return {
        "required": bool(required.get("requires_source_claim_linkage")),
        "source_claim_link_ids": _strings(required.get("source_claim_link_ids"))
        or _strings(candidate.get("source_claim_link_ids")),
        "rule_claim_gap_ids": _strings(required.get("rule_claim_gap_ids"))
        or _strings(candidate.get("rule_claim_gap_ids")),
    }


def _generated_artifact_hashes(
    *,
    validation_hashes: dict[str, Any],
    authority_universe: dict[str, Any],
    paths: dict[str, Path],
    base_rule_pack_path: Path,
) -> dict[str, Any]:
    return {
        "base_rule_pack_sha256": _optional_file_sha256(base_rule_pack_path),
        "applicability_validation_sha256": _optional_file_sha256(
            paths["applicability_validation"]
        ),
        "authority_universe_sha256": authority_universe.get("authority_universe_sha256"),
        "applicable_authorities_sha256": _optional_file_sha256(
            paths["applicable_authorities"]
        ),
        "non_applicable_authorities_sha256": _optional_file_sha256(
            paths["non_applicable_authorities"]
        ),
        "package_fact_graph_sha256": validation_hashes.get("package_fact_graph_sha256"),
        "retrieval_trace_sha256": validation_hashes.get("retrieval_trace_sha256"),
        "graph_trace_sha256": validation_hashes.get("graph_trace_sha256"),
        "search_coverage_certificates_sha256": validation_hashes.get(
            "search_coverage_certificates_sha256"
        ),
        "package_manifest_sha256": validation_hashes.get("package_manifest_sha256"),
        "package_chunks_sha256": validation_hashes.get("package_chunks_sha256"),
        "catalog_sha256": validation_hashes.get("catalog_sha256"),
        "applicability_provenance_sha256": validation_hashes.get(
            "applicability_provenance_sha256"
        ),
    }


def _artifact_paths(
    *,
    output_dir: Path,
    review_id: str,
    authority_universe_path: Path | None,
    decisions_path: Path | None,
    applicable_authorities_path: Path | None,
    non_applicable_authorities_path: Path | None,
    applicability_validation_path: Path | None,
    generated_rule_pack_path: Path | None,
    validation_output_path: Path | None,
) -> dict[str, Path]:
    applicability_dir = output_dir / "reviews" / review_id / "applicability"
    return {
        "applicability_dir": applicability_dir,
        "authority_universe": Path(authority_universe_path)
        if authority_universe_path
        else applicability_dir / "authority_universe_snapshot.json",
        "decisions": Path(decisions_path)
        if decisions_path
        else applicability_dir / "applicability_decisions.jsonl",
        "applicable_authorities": Path(applicable_authorities_path)
        if applicable_authorities_path
        else applicability_dir / "applicable_authorities.json",
        "non_applicable_authorities": Path(non_applicable_authorities_path)
        if non_applicable_authorities_path
        else applicability_dir / "non_applicable_authorities.json",
        "applicability_validation": Path(applicability_validation_path)
        if applicability_validation_path
        else applicability_dir / "applicability_validation.json",
        "generated_rule_pack": Path(generated_rule_pack_path)
        if generated_rule_pack_path
        else applicability_dir / "generated_rule_pack.json",
        "generated_rule_pack_validation": Path(validation_output_path)
        if validation_output_path
        else applicability_dir / "generated_rule_pack_validation.json",
    }


def _resolve_base_rule_pack_path(
    *,
    base_rule_pack_path: Path | None,
    authority_universe: dict[str, Any],
) -> Path:
    if base_rule_pack_path:
        return Path(base_rule_pack_path)
    artifact_paths = (
        authority_universe.get("artifact_paths")
        if isinstance(authority_universe.get("artifact_paths"), dict)
        else {}
    )
    inferred = str(artifact_paths.get("base_rule_pack_path") or "").strip()
    return Path(inferred) if inferred else DEFAULT_RULE_PACK_PATH


def _authority_ids(payload: dict[str, Any]) -> set[str]:
    return {
        str(row.get("candidate_authority_id") or "")
        for row in payload.get("authorities") or []
        if isinstance(row, dict) and row.get("candidate_authority_id")
    }


def _evidence_refs(spans: Any) -> list[dict[str, Any]]:
    refs = []
    for span in spans or []:
        if not isinstance(span, dict):
            continue
        refs.append(
            {
                "evidence_id": span.get("evidence_id"),
                "citation_label": span.get("citation_label"),
                "node_id": span.get("node_id"),
                "chunk_id": span.get("chunk_id"),
                "retrieval_result_id": span.get("retrieval_result_id"),
            }
        )
    return refs


def _check(
    name: str,
    passed: bool,
    failures: list[dict[str, Any]],
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "name": name,
        "passed": passed,
        "failure_categories": sorted(
            {
                str(failure.get("failure_category") or "")
                for failure in failures
                if failure.get("failure_category")
            }
        ),
        "failures": failures,
        "details": details,
    }


def _failure(
    failure_category: str,
    *,
    artifact: str | None = None,
    path: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "failure_category": failure_category,
        "artifact": artifact,
        "path": path,
        "details": details or {},
    }


def _read_json_if_exists(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return value


def _read_required_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    return _read_json_if_exists(path)


def _read_required_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _optional_file_sha256(path: Path | None) -> str | None:
    return sha256_file(path) if path is not None and path.exists() else None


def _validation_artifact_path(
    validation_paths: dict[str, Any],
    artifact_name: str,
) -> Path | None:
    value = str(validation_paths.get(artifact_name) or "").strip()
    return Path(value) if value else None


def _json_field_from_path(path: Path | None, field: str) -> Any:
    if path is None or not path.exists():
        return None
    payload = _read_json_if_exists(path)
    return payload.get(field)


def _hash_from_validation(validation: dict[str, Any], field: str) -> Any:
    hashes = validation.get("hashes") if isinstance(validation.get("hashes"), dict) else {}
    return hashes.get(field)


def _safe_id(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._-")
    if not normalized:
        normalized = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return normalized[:160]


def _strings(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item or "").strip()]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []


def _first_present(*values: Any) -> Any:
    for value in values:
        if isinstance(value, list):
            if value:
                return value[0]
        elif value:
            return value
    return None


def _validate_safe_segment(value: str | None, label: str) -> None:
    if not value or not SAFE_SEGMENT_RE.fullmatch(value):
        raise ValueError(f"{label} must contain only letters, numbers, dot, underscore, or hyphen.")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
