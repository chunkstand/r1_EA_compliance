from __future__ import annotations

from pathlib import Path
from typing import Any

from .applicability_rule_pack_support import _authority_ids
from .applicability_rule_pack_support import _check
from .applicability_rule_pack_support import _failure
from .applicability_rule_pack_support import _first_present
from .applicability_rule_pack_support import _json_field_from_path
from .applicability_rule_pack_support import _optional_file_sha256
from .applicability_rule_pack_support import _validation_artifact_path
from .rule_packs import GENERATED_RULE_PACK_SCHEMA_VERSION
from .rule_packs import validate_rule_pack


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
