from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .applicability_rule_pack_runtime import _generated_rule_pack
from .applicability_rule_pack_support import _artifact_paths
from .applicability_rule_pack_support import _authority_ids
from .applicability_rule_pack_support import _hash_from_validation
from .applicability_rule_pack_support import _optional_file_sha256
from .applicability_rule_pack_support import _read_json_if_exists
from .applicability_rule_pack_support import _read_required_json
from .applicability_rule_pack_support import _read_required_jsonl
from .applicability_rule_pack_support import _resolve_base_rule_pack_path
from .applicability_rule_pack_support import _utc_now
from .applicability_rule_pack_support import _validate_safe_segment
from .applicability_rule_pack_support import _write_json
from .applicability_rule_pack_validation import _check_applicability_validation_matches_current_artifacts
from .applicability_rule_pack_validation import _validation_checks
from .records import sha256_file
from .rule_packs import load_rule_pack
from .rule_packs import validate_rule_pack


GENERATED_RULE_PACK_VALIDATION_SCHEMA_VERSION = "generated-rule-pack-validation-v0"


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
        source_set_id = _first_present_source_set(
            generated_rule_pack,
            applicability_validation,
            applicable_authorities,
            authority_universe,
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


def _first_present_source_set(*payloads: dict[str, Any]) -> Any:
    for payload in payloads:
        value = payload.get("source_set_id")
        if value:
            return value
    return None
