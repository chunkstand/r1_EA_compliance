from __future__ import annotations

from pathlib import Path
import copy
import json

from .records import sha256_file
from .rule_packs import GENERATED_RULE_PACK_SCHEMA_VERSION


def applicability_gate_context(
    *,
    output_dir: Path,
    review_id: str,
    source_set_id: str | None,
    rule_pack_path: Path,
    rule_pack: dict,
    allow_base_rule_pack_review: bool,
) -> dict:
    is_generated = rule_pack.get("schema_version") == GENERATED_RULE_PACK_SCHEMA_VERSION
    if not is_generated:
        if not allow_base_rule_pack_review:
            raise ValueError(
                "Reviewer-ready compliance review requires a generated applicability rule pack. "
                "Run applicability validation and applicability-generate-rule-pack first, or pass "
                "--allow-base-rule-pack-review for a non-reviewer-ready diagnostic run."
            )
        return {
            "mode": "base_rule_pack_diagnostic",
            "is_generated_rule_pack": False,
            "reviewer_ready_eligible": False,
            "rule_pack_path": str(rule_pack_path),
            "checks": [
                gate_check(
                    "generated_rule_pack_required",
                    False,
                    {
                        "rule_pack_path": str(rule_pack_path),
                        "rule_pack_schema_version": rule_pack.get("schema_version"),
                        "diagnostic_mode": True,
                    },
                )
            ],
        }

    applicability_dir = applicability_dir_for_rule_pack(
        output_dir=output_dir,
        review_id=review_id,
        rule_pack_path=rule_pack_path,
    )
    validation_path = applicability_dir / "applicability_validation.json"
    generated_validation_path = applicability_dir / "generated_rule_pack_validation.json"
    non_applicable_path = applicability_dir / "non_applicable_authorities.json"
    applicability_validation = read_json_if_exists(validation_path)
    generated_validation = read_json_if_exists(generated_validation_path)
    non_applicable = read_json_if_exists(non_applicable_path)
    validation_paths = (
        applicability_validation.get("artifact_paths")
        if isinstance(applicability_validation.get("artifact_paths"), dict)
        else {}
    )
    coverage_path = path_from_artifact_paths(
        validation_paths,
        "search_coverage_certificates",
        applicability_dir / "search_coverage_certificates.json",
    )
    decisions_path = path_from_artifact_paths(
        validation_paths,
        "decisions",
        applicability_dir / "applicability_decisions.jsonl",
    )
    applicable_path = path_from_artifact_paths(
        validation_paths,
        "applicable_authorities",
        applicability_dir / "applicable_authorities.json",
    )
    provenance_path = path_from_artifact_paths(
        validation_paths,
        "provenance",
        applicability_dir / "applicability_provenance.json",
    )
    coverage = read_json_if_exists(coverage_path)
    current_rule_pack_sha = sha256_file(rule_pack_path)
    non_applicable_sha = sha256_file(non_applicable_path) if non_applicable_path.exists() else None
    generated_summary = generated_validation.get("summary") or {}
    applicability_hashes = (
        applicability_validation.get("hashes")
        if isinstance(applicability_validation.get("hashes"), dict)
        else {}
    )
    expected_generated_hash = (
        generated_summary.get("expected_generated_rule_pack_sha256")
        or generated_summary.get("generated_rule_pack_sha256")
    )
    expected_source_set_id = first_present(
        source_set_id,
        rule_pack.get("source_set_id"),
        applicability_validation.get("source_set_id"),
        generated_summary.get("source_set_id"),
    )
    checks = [
        gate_check(
            "generated_rule_pack_used",
            True,
            {"rule_pack_path": str(rule_pack_path)},
        ),
        gate_check(
            "generated_rule_pack_validation_passed",
            bool(generated_validation.get("passed"))
            and generated_summary.get("generated_rule_pack_ready") is True,
            {
                "path": str(generated_validation_path),
                "exists": generated_validation_path.exists(),
                "passed": bool(generated_validation.get("passed")),
                "generated_rule_pack_ready": generated_summary.get("generated_rule_pack_ready"),
            },
        ),
        gate_check(
            "generated_rule_pack_hash_matches_validation",
            bool(expected_generated_hash) and current_rule_pack_sha == expected_generated_hash,
            {
                "expected": expected_generated_hash,
                "actual": current_rule_pack_sha,
            },
        ),
        gate_check(
            "applicability_validation_passed",
            bool(applicability_validation.get("passed")),
            {
                "path": str(validation_path),
                "exists": validation_path.exists(),
                "passed": bool(applicability_validation.get("passed")),
            },
        ),
        gate_check(
            "generated_rule_pack_source_set_matches",
            values_match_if_present(
                expected_source_set_id,
                rule_pack.get("source_set_id"),
                applicability_validation.get("source_set_id"),
                generated_summary.get("source_set_id"),
            ),
            {
                "expected_source_set_id": expected_source_set_id,
                "rule_pack_source_set_id": rule_pack.get("source_set_id"),
                "applicability_validation_source_set_id": applicability_validation.get(
                    "source_set_id"
                ),
                "generated_validation_source_set_id": generated_summary.get("source_set_id"),
            },
        ),
        gate_check(
            "generated_rule_pack_applicability_run_matches",
            values_match_if_present(
                rule_pack.get("applicability_run_id"),
                applicability_validation.get("applicability_run_id"),
                generated_summary.get("applicability_run_id"),
            ),
            {
                "rule_pack_applicability_run_id": rule_pack.get("applicability_run_id"),
                "validation_applicability_run_id": applicability_validation.get(
                    "applicability_run_id"
                ),
                "generated_validation_applicability_run_id": generated_summary.get(
                    "applicability_run_id"
                ),
            },
        ),
        gate_check(
            "applicability_validation_hash_matches_rule_pack",
            bool(rule_pack.get("applicability_validation_sha256"))
            and rule_pack.get("applicability_validation_sha256") == sha256_file(validation_path)
            if validation_path.exists()
            else False,
            {
                "expected": rule_pack.get("applicability_validation_sha256"),
                "actual": sha256_file(validation_path) if validation_path.exists() else None,
                "path": str(validation_path),
            },
        ),
        gate_check(
            "non_applicable_authorities_artifact_valid",
            bool(non_applicable_path.exists())
            and isinstance(non_applicable.get("authorities"), list)
            and bool(rule_pack.get("non_applicable_authorities_sha256"))
            and rule_pack.get("non_applicable_authorities_sha256") == non_applicable_sha,
            {
                "path": str(non_applicable_path),
                "exists": non_applicable_path.exists(),
                "authority_count": len(non_applicable.get("authorities") or []),
                "sha256": non_applicable_sha,
                "rule_pack_sha256": rule_pack.get("non_applicable_authorities_sha256"),
            },
        ),
        gate_check(
            "non_applicable_authority_search_coverage_exists",
            non_applicable_coverage_passed(non_applicable, coverage),
            non_applicable_coverage_details(
                non_applicable=non_applicable,
                coverage=coverage,
                coverage_path=coverage_path,
            ),
        ),
        gate_check(
            "generated_rule_pack_provenance_matches_applicability_run",
            generated_provenance_matches(
                rule_pack=rule_pack,
                applicability_hashes=applicability_hashes,
                provenance_path=provenance_path,
            ),
            {
                "provenance_path": str(provenance_path),
                "rule_pack_applicability_provenance_sha256": rule_pack.get(
                    "applicability_provenance_sha256"
                ),
                "validation_applicability_provenance_sha256": applicability_hashes.get(
                    "applicability_provenance_sha256"
                ),
                "current_applicability_provenance_sha256": (
                    sha256_file(provenance_path) if provenance_path.exists() else None
                ),
            },
        ),
    ]
    failed = [check["name"] for check in checks if not check["passed"]]
    if failed:
        raise ValueError(
            "Generated applicability rule pack gate failed. Failed checks: "
            + ", ".join(failed)
        )
    return {
        "mode": "generated_rule_pack",
        "is_generated_rule_pack": True,
        "reviewer_ready_eligible": True,
        "rule_pack_path": str(rule_pack_path),
        "applicability_dir": str(applicability_dir),
        "applicability_validation_path": str(validation_path),
        "generated_rule_pack_validation_path": str(generated_validation_path),
        "applicability_decisions_path": str(decisions_path),
        "applicable_authorities_path": str(applicable_path),
        "non_applicable_authorities_path": str(non_applicable_path),
        "non_applicable_authority_count": len(non_applicable.get("authorities") or []),
        "search_coverage_certificates_path": str(coverage_path),
        "applicability_provenance_path": str(provenance_path),
        "expected_package_manifest_sha256": rule_pack.get("package_manifest_sha256"),
        "expected_package_chunks_sha256": rule_pack.get("package_chunks_sha256"),
        "checks": checks,
    }


def write_evaluation_rule_pack(
    *,
    review_dir: Path,
    rule_pack_path: Path,
    rule_pack: dict,
    applicability_gate: dict,
) -> Path:
    if not applicability_gate.get("is_generated_rule_pack"):
        return rule_pack_path
    evaluation_pack = copy.deepcopy(rule_pack)
    for rule in evaluation_pack.get("rules") or []:
        if not isinstance(rule, dict):
            continue
        rule["pre_review_applicability_mode"] = rule.get("applicability_mode")
        rule["pre_review_applicability"] = rule.get("applicability")
        rule["applicability_mode"] = "baseline"
        rule.pop("applies_if_package_terms", None)
        rule.pop("applies_if_package_term_groups", None)
        rule.pop("does_not_apply_if_package_terms", None)
    evaluation_path = review_dir / "applicability" / "compliance_evaluation_rule_pack.json"
    write_json(evaluation_path, evaluation_pack)
    return evaluation_path


def check_applicability_generated_rule_pack_gate(
    *,
    applicability_gate: dict,
    package_manifest_path: Path,
    package_chunks_path: Path,
) -> dict:
    checks = list(applicability_gate.get("checks") or [])
    if applicability_gate.get("is_generated_rule_pack"):
        expected_package_manifest_sha = applicability_gate.get(
            "expected_package_manifest_sha256"
        )
        actual_package_manifest_sha = (
            sha256_file(package_manifest_path) if package_manifest_path.exists() else None
        )
        expected_package_chunks_sha = applicability_gate.get("expected_package_chunks_sha256")
        actual_package_chunks_sha = (
            sha256_file(package_chunks_path) if package_chunks_path.exists() else None
        )
        checks.append(
            gate_check(
                "package_manifest_matches_applicability_run",
                bool(expected_package_manifest_sha)
                and expected_package_manifest_sha == actual_package_manifest_sha,
                {
                    "expected": expected_package_manifest_sha,
                    "actual": actual_package_manifest_sha,
                    "path": str(package_manifest_path),
                },
            )
        )
        checks.append(
            gate_check(
                "package_chunks_match_applicability_run",
                bool(expected_package_chunks_sha)
                and expected_package_chunks_sha == actual_package_chunks_sha,
                {
                    "expected": expected_package_chunks_sha,
                    "actual": actual_package_chunks_sha,
                    "path": str(package_chunks_path),
                },
            )
        )
    failed = [check["name"] for check in checks if not check["passed"]]
    return {
        "name": "applicability_generated_rule_pack_gate",
        "passed": not failed and bool(applicability_gate.get("reviewer_ready_eligible")),
        "details": {
            "mode": applicability_gate.get("mode"),
            "reviewer_ready_eligible": bool(applicability_gate.get("reviewer_ready_eligible")),
            "failed_checks": failed,
            "checks": checks,
        },
    }


def applicability_gate_summary(applicability_gate: dict) -> dict:
    return {
        "mode": applicability_gate.get("mode"),
        "is_generated_rule_pack": bool(applicability_gate.get("is_generated_rule_pack")),
        "reviewer_ready_eligible": bool(applicability_gate.get("reviewer_ready_eligible")),
        "applicability_dir": applicability_gate.get("applicability_dir"),
        "applicability_validation_path": applicability_gate.get("applicability_validation_path"),
        "generated_rule_pack_validation_path": applicability_gate.get(
            "generated_rule_pack_validation_path"
        ),
        "applicability_decisions_path": applicability_gate.get("applicability_decisions_path"),
        "applicable_authorities_path": applicability_gate.get("applicable_authorities_path"),
        "non_applicable_authorities_path": applicability_gate.get(
            "non_applicable_authorities_path"
        ),
        "non_applicable_authority_count": applicability_gate.get(
            "non_applicable_authority_count",
            0,
        ),
        "search_coverage_certificates_path": applicability_gate.get(
            "search_coverage_certificates_path"
        ),
    }


def applicability_dir_for_rule_pack(
    *,
    output_dir: Path,
    review_id: str,
    rule_pack_path: Path,
) -> Path:
    if rule_pack_path.name == "generated_rule_pack.json":
        return rule_pack_path.parent
    return output_dir / "reviews" / review_id / "applicability"


def path_from_artifact_paths(
    artifact_paths: dict,
    key: str,
    default: Path,
) -> Path:
    value = str(artifact_paths.get(key) or "").strip()
    return Path(value) if value else default


def non_applicable_coverage_passed(non_applicable: dict, coverage: dict) -> bool:
    authorities = non_applicable.get("authorities")
    if not isinstance(authorities, list):
        return False
    if not coverage_payload_has_certificate_list(coverage):
        return False
    if not authorities:
        return True
    certificates = coverage_certificate_ids(coverage)
    for authority in authorities:
        if not isinstance(authority, dict):
            return False
        ids = strings(authority.get("search_coverage_certificate_ids"))
        if not ids or any(certificate_id not in certificates for certificate_id in ids):
            return False
    return True


def non_applicable_coverage_details(
    *,
    non_applicable: dict,
    coverage: dict,
    coverage_path: Path,
) -> dict:
    authorities = (
        non_applicable.get("authorities")
        if isinstance(non_applicable.get("authorities"), list)
        else []
    )
    certificate_ids = coverage_certificate_ids(coverage)
    missing = []
    for authority in authorities:
        if not isinstance(authority, dict):
            missing.append({"candidate_authority_id": None, "reason": "invalid_authority"})
            continue
        ids = strings(authority.get("search_coverage_certificate_ids"))
        missing_ids = [
            certificate_id for certificate_id in ids if certificate_id not in certificate_ids
        ]
        if not ids or missing_ids:
            missing.append(
                {
                    "candidate_authority_id": authority.get("candidate_authority_id"),
                    "search_coverage_certificate_ids": ids,
                    "missing_certificate_ids": missing_ids,
                }
            )
    return {
        "path": str(coverage_path),
        "exists": coverage_path.exists(),
        "non_applicable_authority_count": len(authorities),
        "coverage_certificate_count": len(certificate_ids),
        "missing": missing,
    }


def coverage_payload_has_certificate_list(coverage: dict) -> bool:
    return isinstance(coverage.get("certificates"), list) or isinstance(
        coverage.get("search_coverage_certificates"),
        list,
    )


def generated_provenance_matches(
    *,
    rule_pack: dict,
    applicability_hashes: dict,
    provenance_path: Path,
) -> bool:
    expected = rule_pack.get("applicability_provenance_sha256")
    recorded = applicability_hashes.get("applicability_provenance_sha256")
    actual = sha256_file(provenance_path) if provenance_path.exists() else None
    return bool(expected) and expected == recorded and expected == actual


def coverage_certificate_ids(coverage: dict) -> set[str]:
    certificates = coverage.get("certificates")
    if not isinstance(certificates, list):
        certificates = coverage.get("search_coverage_certificates")
    if not isinstance(certificates, list):
        return set()
    return {
        str(
            certificate.get("coverage_certificate_id")
            or certificate.get("certificate_id")
            or certificate.get("search_coverage_certificate_id")
            or ""
        )
        for certificate in certificates
        if isinstance(certificate, dict)
        and str(
            certificate.get("coverage_certificate_id")
            or certificate.get("certificate_id")
            or certificate.get("search_coverage_certificate_id")
            or ""
        ).strip()
    }


def coverage_certificates_by_id(coverage: dict) -> dict[str, dict]:
    certificates = coverage.get("certificates")
    if not isinstance(certificates, list):
        certificates = coverage.get("search_coverage_certificates")
    if not isinstance(certificates, list):
        return {}
    result = {}
    for certificate in certificates:
        if not isinstance(certificate, dict):
            continue
        certificate_id = coverage_certificate_id(certificate)
        if certificate_id:
            result[certificate_id] = certificate
    return result


def coverage_certificate_id(certificate: dict) -> str:
    return str(
        certificate.get("coverage_certificate_id")
        or certificate.get("certificate_id")
        or certificate.get("search_coverage_certificate_id")
        or ""
    ).strip()


def gate_check(name: str, passed: bool, details: dict) -> dict:
    return {"name": name, "passed": bool(passed), "details": details}


def values_match_if_present(*values) -> bool:
    present = [str(value) for value in values if str(value or "").strip()]
    return bool(present) and len(set(present)) == 1


def read_json_if_exists(path: Path) -> dict:
    if not path.exists():
        return {}
    return read_json(path)


def read_json_if_exists_or_empty(path: Path | None) -> dict:
    if path is None or not path.exists():
        return {}
    return read_json(path)


def read_jsonl_if_exists(path: Path | None) -> list[dict]:
    if path is None or not path.exists():
        return []
    return read_jsonl(path)


def optional_path(value: object) -> Path | None:
    if not value:
        return None
    return Path(str(value))


def first_present(*values):
    for value in values:
        if str(value or "").strip():
            return str(value).strip()
    return None


def strings(value) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item or "").strip()]
    if str(value or "").strip():
        return [str(value).strip()]
    return []


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
