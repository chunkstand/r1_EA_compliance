from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .applicability_adjudication import APPLICABILITY_ADJUDICATION_APPLY_SCHEMA_VERSION
from .applicability_adjudication import APPLICABILITY_ADJUDICATION_EVAL_SCHEMA_VERSION
from .applicability_adjudication import APPLICABILITY_ADJUDICATION_TEMPLATE_SCHEMA_VERSION
from .applicability_adjudication import ApplicabilityAdjudicationApplyResult
from .applicability_adjudication import ApplicabilityAdjudicationEvalResult
from .applicability_adjudication import ApplicabilityAdjudicationTemplateResult
from .applicability_adjudication import evaluate_applicability_adjudication
from .applicability_adjudication import write_applicability_adjudication_template
from .applicability_adjudication_apply import apply_applicability_adjudication
from .applicability_validation_checks import build_validation_checks
from .applicability_validation_support import candidate_ids
from .applicability_validation_support import decision_status
from .applicability_validation_support import first_present
from .applicability_validation_support import optional_file_sha256
from .applicability_validation_support import partition_ids
from .applicability_validation_support import read_json_if_exists
from .applicability_validation_support import read_jsonl_if_exists
from .applicability_validation_support import utc_now
from .applicability_validation_support import validate_safe_segment
from .applicability_validation_support import write_json
from .records import sha256_file


APPLICABILITY_VALIDATION_SCHEMA_VERSION = "applicability-validation-v0"
UNRESOLVED_STATUSES = {"unresolved", "needs_adjudication"}
REQUIRED_PROVENANCE_ENTITY_IDS = {
    "authority_universe",
    "package_fact_graph",
    "package_applicability_context",
    "retrieval_trace",
    "graph_trace",
    "decision_ledger",
    "search_coverage_certificates",
    "applicable_authorities",
    "non_applicable_authorities",
}
FILE_HASH_PROVENANCE_ENTITY_IDS = {
    "package_applicability_context",
    "retrieval_trace",
    "graph_trace",
    "decision_ledger",
    "applicable_authorities",
    "non_applicable_authorities",
    "applicability_adjudication",
    "applicability_adjudication_eval",
    "applicability_adjudication_apply",
}


@dataclass(frozen=True)
class ApplicabilityValidationResult:
    review_id: str
    source_set_id: str | None
    applicability_dir: Path
    validation_path: Path
    summary: dict[str, Any]


__all__ = [
    "APPLICABILITY_ADJUDICATION_APPLY_SCHEMA_VERSION",
    "APPLICABILITY_ADJUDICATION_EVAL_SCHEMA_VERSION",
    "APPLICABILITY_ADJUDICATION_TEMPLATE_SCHEMA_VERSION",
    "APPLICABILITY_VALIDATION_SCHEMA_VERSION",
    "ApplicabilityAdjudicationApplyResult",
    "ApplicabilityAdjudicationEvalResult",
    "ApplicabilityAdjudicationTemplateResult",
    "ApplicabilityValidationResult",
    "apply_applicability_adjudication",
    "evaluate_applicability_adjudication",
    "validate_applicability_run",
    "write_applicability_adjudication_template",
]


def validate_applicability_run(
    *,
    output_dir: Path,
    review_id: str,
    source_set_id: str | None = None,
    authority_universe_path: Path | None = None,
    package_fact_graph_path: Path | None = None,
    package_applicability_context_path: Path | None = None,
    package_fact_graph_validation_path: Path | None = None,
    retrieval_trace_path: Path | None = None,
    graph_trace_path: Path | None = None,
    decisions_path: Path | None = None,
    applicable_authorities_path: Path | None = None,
    non_applicable_authorities_path: Path | None = None,
    search_coverage_certificates_path: Path | None = None,
    provenance_path: Path | None = None,
    validation_path: Path | None = None,
) -> ApplicabilityValidationResult:
    """Validate the applicability-first artifacts before rule-pack generation."""

    output_dir = Path(output_dir)
    validate_safe_segment(review_id, "review_id")
    applicability_dir = output_dir / "reviews" / review_id / "applicability"
    paths = _artifact_paths(
        applicability_dir=applicability_dir,
        authority_universe_path=authority_universe_path,
        package_fact_graph_path=package_fact_graph_path,
        package_applicability_context_path=package_applicability_context_path,
        package_fact_graph_validation_path=package_fact_graph_validation_path,
        retrieval_trace_path=retrieval_trace_path,
        graph_trace_path=graph_trace_path,
        decisions_path=decisions_path,
        applicable_authorities_path=applicable_authorities_path,
        non_applicable_authorities_path=non_applicable_authorities_path,
        search_coverage_certificates_path=search_coverage_certificates_path,
        provenance_path=provenance_path,
    )
    validation_path = Path(validation_path) if validation_path else (
        applicability_dir / "applicability_validation.json"
    )

    artifacts = _load_validation_artifacts(paths)
    if source_set_id is None:
        source_set_id = _first_present_source_set_id(artifacts)
    if source_set_id:
        validate_safe_segment(source_set_id, "source_set_id")

    checks = [
        *build_validation_checks(
            review_id=review_id,
            source_set_id=source_set_id,
            paths=paths,
            artifacts=artifacts,
        ),
        _check_artifact_freshness(paths=paths, artifacts=artifacts, decisions=artifacts["decisions"]),
        _check_provenance(artifacts["provenance"], paths, artifacts),
    ]
    failures = [
        failure
        for check in checks
        for failure in check.get("failures", [])
        if isinstance(failure, dict)
    ]
    failure_counts = Counter(str(failure.get("failure_category") or "") for failure in failures)
    decisions = artifacts["decisions"]
    status_counts = dict(sorted(Counter(decision_status(row) for row in decisions).items()))
    unresolved_count = sum(status_counts.get(status, 0) for status in UNRESOLVED_STATUSES)
    passed = all(check["passed"] for check in checks)
    candidate_values = candidate_ids(artifacts["authority_universe"])
    applicable_values = partition_ids(artifacts["applicable_authorities"])
    non_applicable_values = partition_ids(artifacts["non_applicable_authorities"])
    hashes = _artifact_hashes(paths, artifacts)
    summary = {
        "schema_version": APPLICABILITY_VALIDATION_SCHEMA_VERSION,
        "created_at": utc_now(),
        "review_id": review_id,
        "source_set_id": source_set_id,
        "applicability_run_id": _first_present_run_id(artifacts),
        "passed": passed,
        "reviewer_ready": passed,
        "generated_rule_pack_ready": passed,
        "candidate_authority_count": len(candidate_values),
        "decision_count": len(decisions),
        "decision_status_counts": status_counts,
        "applicable_authority_count": len(applicable_values),
        "non_applicable_authority_count": len(non_applicable_values),
        "unresolved_authority_count": unresolved_count,
        "needs_adjudication_authority_count": status_counts.get("needs_adjudication", 0),
        "failure_category_counts": dict(sorted(failure_counts.items())),
        "validation_path": str(validation_path),
        "artifact_hashes": hashes,
    }
    validation = {
        "schema_version": APPLICABILITY_VALIDATION_SCHEMA_VERSION,
        "created_at": summary["created_at"],
        "applicability_run_id": summary["applicability_run_id"],
        "review_id": review_id,
        "source_set_id": source_set_id,
        "passed": passed,
        "reviewer_ready": passed,
        "generated_rule_pack_ready": passed,
        "summary": summary,
        "artifact_paths": {name: str(path) for name, path in paths.items()},
        "hashes": hashes,
        "checks": checks,
        "failures": failures,
    }
    write_json(validation_path, validation)
    return ApplicabilityValidationResult(
        review_id=review_id,
        source_set_id=source_set_id,
        applicability_dir=applicability_dir,
        validation_path=validation_path,
        summary=summary,
    )


def _artifact_paths(
    *,
    applicability_dir: Path,
    authority_universe_path: Path | None,
    package_fact_graph_path: Path | None,
    package_applicability_context_path: Path | None,
    package_fact_graph_validation_path: Path | None,
    retrieval_trace_path: Path | None,
    graph_trace_path: Path | None,
    decisions_path: Path | None,
    applicable_authorities_path: Path | None,
    non_applicable_authorities_path: Path | None,
    search_coverage_certificates_path: Path | None,
    provenance_path: Path | None,
) -> dict[str, Path]:
    return {
        "authority_universe": Path(authority_universe_path)
        if authority_universe_path
        else applicability_dir / "authority_universe_snapshot.json",
        "package_fact_graph": Path(package_fact_graph_path)
        if package_fact_graph_path
        else applicability_dir / "package_fact_graph.json",
        "package_applicability_context": Path(package_applicability_context_path)
        if package_applicability_context_path
        else applicability_dir / "package_applicability_context.json",
        "package_fact_graph_validation": Path(package_fact_graph_validation_path)
        if package_fact_graph_validation_path
        else applicability_dir / "package_fact_graph_validation.json",
        "retrieval_trace": Path(retrieval_trace_path)
        if retrieval_trace_path
        else applicability_dir / "applicability_retrieval_trace.jsonl",
        "graph_trace": Path(graph_trace_path)
        if graph_trace_path
        else applicability_dir / "applicability_graph_trace.jsonl",
        "decisions": Path(decisions_path)
        if decisions_path
        else applicability_dir / "applicability_decisions.jsonl",
        "applicable_authorities": Path(applicable_authorities_path)
        if applicable_authorities_path
        else applicability_dir / "applicable_authorities.json",
        "non_applicable_authorities": Path(non_applicable_authorities_path)
        if non_applicable_authorities_path
        else applicability_dir / "non_applicable_authorities.json",
        "search_coverage_certificates": Path(search_coverage_certificates_path)
        if search_coverage_certificates_path
        else applicability_dir / "search_coverage_certificates.json",
        "provenance": Path(provenance_path)
        if provenance_path
        else applicability_dir / "applicability_provenance.json",
    }


def _load_validation_artifacts(paths: dict[str, Path]) -> dict[str, Any]:
    return {
        "authority_universe": read_json_if_exists(paths["authority_universe"]),
        "package_fact_graph": read_json_if_exists(paths["package_fact_graph"]),
        "package_applicability_context": read_json_if_exists(
            paths["package_applicability_context"]
        ),
        "package_fact_graph_validation": read_json_if_exists(
            paths["package_fact_graph_validation"]
        ),
        "retrieval_rows": read_jsonl_if_exists(paths["retrieval_trace"]),
        "graph_rows": read_jsonl_if_exists(paths["graph_trace"]),
        "decisions": read_jsonl_if_exists(paths["decisions"]),
        "applicable_authorities": read_json_if_exists(paths["applicable_authorities"]),
        "non_applicable_authorities": read_json_if_exists(paths["non_applicable_authorities"]),
        "search_coverage_certificates": read_json_if_exists(
            paths["search_coverage_certificates"]
        ),
        "provenance": read_json_if_exists(paths["provenance"]),
    }


def _check_artifact_freshness(
    *,
    paths: dict[str, Path],
    artifacts: dict[str, Any],
    decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    failures = []
    universe_hash = artifacts["authority_universe"].get("authority_universe_sha256")
    package_fact_graph_hash = artifacts["package_fact_graph"].get("package_fact_graph_sha256")
    package_manifest_hash = first_present(
        artifacts["package_applicability_context"].get("package_manifest_sha256"),
        artifacts["package_fact_graph"].get("package_manifest_sha256"),
    )
    package_chunks_hash = first_present(
        artifacts["package_applicability_context"].get("package_chunks_sha256"),
        artifacts["package_fact_graph"].get("package_chunks_sha256"),
    )
    retrieval_hash = optional_file_sha256(paths["retrieval_trace"])
    graph_hash = optional_file_sha256(paths["graph_trace"])
    coverage_hash = artifacts["search_coverage_certificates"].get(
        "search_coverage_certificates_sha256"
    )
    decision_hash = optional_file_sha256(paths["decisions"])
    applicable_decision_hash = artifacts["applicable_authorities"].get(
        "applicability_decisions_sha256"
    )
    non_applicable_decision_hash = artifacts["non_applicable_authorities"].get(
        "applicability_decisions_sha256"
    )
    if decision_hash and applicable_decision_hash and applicable_decision_hash != decision_hash:
        failures.append(
            {
                "failure_category": "source_set_stale",
                "candidate_authority_id": None,
                "artifact": "applicable_authorities",
                "path": None,
                "details": {"field": "applicability_decisions_sha256"},
            }
        )
    if (
        decision_hash
        and non_applicable_decision_hash
        and non_applicable_decision_hash != decision_hash
    ):
        failures.append(
            {
                "failure_category": "source_set_stale",
                "candidate_authority_id": None,
                "artifact": "non_applicable_authorities",
                "path": None,
                "details": {"field": "applicability_decisions_sha256"},
            }
        )
    expected_partition_pairs = {
        "authority_universe_sha256": (universe_hash, "source_set_stale"),
        "package_manifest_sha256": (package_manifest_hash, "package_cache_stale"),
        "package_chunks_sha256": (package_chunks_hash, "package_cache_stale"),
        "package_fact_graph_sha256": (package_fact_graph_hash, "package_cache_stale"),
        "retrieval_trace_sha256": (retrieval_hash, "retrieval_trace_stale"),
        "graph_trace_sha256": (graph_hash, "graph_trace_stale"),
        "search_coverage_certificates_sha256": (coverage_hash, "search_coverage_stale"),
        "catalog_sha256": (
            artifacts["authority_universe"].get("catalog_sha256"),
            "source_set_stale",
        ),
    }
    for artifact_name in ("applicable_authorities", "non_applicable_authorities"):
        artifact = artifacts[artifact_name]
        for field, (expected, category) in expected_partition_pairs.items():
            actual = artifact.get(field)
            if expected and actual and actual != expected:
                failures.append(
                    {
                        "failure_category": category,
                        "candidate_authority_id": None,
                        "artifact": artifact_name,
                        "path": None,
                        "details": {"field": field, "expected": expected, "actual": actual},
                    }
                )
    expected_coverage_pairs = {
        "authority_universe_sha256": (universe_hash, "source_set_stale"),
        "package_fact_graph_sha256": (package_fact_graph_hash, "package_cache_stale"),
        "retrieval_trace_sha256": (retrieval_hash, "retrieval_trace_stale"),
        "graph_trace_sha256": (graph_hash, "graph_trace_stale"),
    }
    for field, (expected, category) in expected_coverage_pairs.items():
        actual = artifacts["search_coverage_certificates"].get(field)
        if expected and actual and actual != expected:
            failures.append(
                {
                    "failure_category": category,
                    "candidate_authority_id": None,
                    "artifact": "search_coverage_certificates",
                    "path": None,
                    "details": {"field": field, "expected": expected, "actual": actual},
                }
            )
    for decision in decisions:
        freshness = decision.get("freshness") if isinstance(decision.get("freshness"), dict) else {}
        candidate_id = str(decision.get("candidate_authority_id") or "")
        expected_pairs = {
            "authority_universe_sha256": (universe_hash, "source_set_stale"),
            "package_manifest_sha256": (package_manifest_hash, "package_cache_stale"),
            "package_chunks_sha256": (package_chunks_hash, "package_cache_stale"),
            "package_fact_graph_sha256": (package_fact_graph_hash, "package_cache_stale"),
            "retrieval_trace_sha256": (retrieval_hash, "retrieval_trace_stale"),
            "graph_trace_sha256": (graph_hash, "graph_trace_stale"),
            "search_coverage_certificates_sha256": (coverage_hash, "search_coverage_stale"),
        }
        for field, (expected, category) in expected_pairs.items():
            actual = freshness.get(field)
            if expected and actual and actual != expected:
                failures.append(
                    {
                        "failure_category": category,
                        "candidate_authority_id": candidate_id,
                        "artifact": None,
                        "path": None,
                        "details": {"field": field, "expected": expected, "actual": actual},
                    }
                )
    return {
        "name": "artifact_hashes_match_current_inputs",
        "passed": not failures,
        "failure_categories": sorted(
            {str(failure.get("failure_category") or "") for failure in failures}
        ),
        "failures": failures,
        "details": {"failure_count": len(failures)},
    }


def _check_provenance(
    provenance: dict[str, Any],
    paths: dict[str, Path],
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    entities = provenance.get("entities") if isinstance(provenance.get("entities"), list) else []
    expected_hashes = _expected_provenance_hashes(paths=paths, artifacts=artifacts)
    entity_ids = {
        str(entity.get("entity_id") or "")
        for entity in entities
        if isinstance(entity, dict)
    }
    missing = sorted(REQUIRED_PROVENANCE_ENTITY_IDS - entity_ids)
    missing_paths = []
    stale_hashes = []
    for entity in entities:
        if not isinstance(entity, dict):
            continue
        entity_id = str(entity.get("entity_id") or "")
        path = entity.get("path")
        if entity_id in REQUIRED_PROVENANCE_ENTITY_IDS and path and not Path(str(path)).exists():
            missing_paths.append({"entity_id": entity_id, "path": str(path)})
        if entity_id in REQUIRED_PROVENANCE_ENTITY_IDS and not entity.get("exists", True):
            missing_paths.append({"entity_id": entity_id, "path": str(path or "")})
        expected_hash = expected_hashes.get(entity_id)
        if (
            not expected_hash
            and entity_id in FILE_HASH_PROVENANCE_ENTITY_IDS
            and path
            and Path(str(path)).exists()
        ):
            expected_hash = sha256_file(Path(str(path)))
        actual_hash = str(entity.get("sha256") or "")
        if expected_hash and actual_hash != expected_hash:
            stale_hashes.append(
                {
                    "entity_id": entity_id,
                    "expected": expected_hash,
                    "actual": actual_hash or None,
                }
            )
    failures = [
        *[
            {
                "failure_category": "provenance_gap",
                "candidate_authority_id": None,
                "artifact": entity_id,
                "path": None,
                "details": {},
            }
            for entity_id in missing
        ],
        *[
            {
                "failure_category": "provenance_gap",
                "candidate_authority_id": None,
                "artifact": row["entity_id"],
                "path": row["path"],
                "details": {},
            }
            for row in missing_paths
        ],
        *[
            {
                "failure_category": "provenance_gap",
                "candidate_authority_id": None,
                "artifact": row["entity_id"],
                "path": None,
                "details": {"expected": row["expected"], "actual": row["actual"]},
            }
            for row in stale_hashes
        ],
    ]
    return {
        "name": "provenance_covers_required_applicability_artifacts",
        "passed": not failures and paths["provenance"].exists(),
        "failure_categories": sorted(
            {str(failure.get("failure_category") or "") for failure in failures}
        ),
        "failures": failures,
        "details": {
            "missing_entity_ids": missing,
            "missing_entity_paths": missing_paths,
            "stale_entity_hashes": stale_hashes,
        },
    }


def _expected_provenance_hashes(
    *,
    paths: dict[str, Path],
    artifacts: dict[str, Any],
) -> dict[str, str | None]:
    return {
        "authority_universe": artifacts["authority_universe"].get(
            "authority_universe_sha256"
        ),
        "package_fact_graph": artifacts["package_fact_graph"].get(
            "package_fact_graph_sha256"
        ),
        "package_applicability_context": optional_file_sha256(
            paths["package_applicability_context"]
        ),
        "retrieval_trace": optional_file_sha256(paths["retrieval_trace"]),
        "graph_trace": optional_file_sha256(paths["graph_trace"]),
        "decision_ledger": optional_file_sha256(paths["decisions"]),
        "search_coverage_certificates": artifacts[
            "search_coverage_certificates"
        ].get("search_coverage_certificates_sha256"),
        "applicable_authorities": optional_file_sha256(paths["applicable_authorities"]),
        "non_applicable_authorities": optional_file_sha256(paths["non_applicable_authorities"]),
        "package_manifest": first_present(
            artifacts["package_applicability_context"].get("package_manifest_sha256"),
            artifacts["package_fact_graph"].get("package_manifest_sha256"),
        ),
        "package_chunks": first_present(
            artifacts["package_applicability_context"].get("package_chunks_sha256"),
            artifacts["package_fact_graph"].get("package_chunks_sha256"),
        ),
    }


def _artifact_hashes(paths: dict[str, Path], artifacts: dict[str, Any]) -> dict[str, Any]:
    return {
        "authority_universe_sha256": artifacts["authority_universe"].get(
            "authority_universe_sha256"
        ),
        "package_manifest_sha256": first_present(
            artifacts["package_applicability_context"].get("package_manifest_sha256"),
            artifacts["package_fact_graph"].get("package_manifest_sha256"),
        ),
        "package_chunks_sha256": first_present(
            artifacts["package_applicability_context"].get("package_chunks_sha256"),
            artifacts["package_fact_graph"].get("package_chunks_sha256"),
        ),
        "package_fact_graph_sha256": artifacts["package_fact_graph"].get(
            "package_fact_graph_sha256"
        ),
        "package_context_sha256": artifacts["package_applicability_context"].get(
            "package_context_sha256"
        ),
        "retrieval_trace_sha256": optional_file_sha256(paths["retrieval_trace"]),
        "graph_trace_sha256": optional_file_sha256(paths["graph_trace"]),
        "search_coverage_certificates_sha256": optional_file_sha256(
            paths["search_coverage_certificates"]
        ),
        "applicability_decisions_sha256": optional_file_sha256(paths["decisions"]),
        "applicable_authorities_sha256": optional_file_sha256(paths["applicable_authorities"]),
        "non_applicable_authorities_sha256": optional_file_sha256(
            paths["non_applicable_authorities"]
        ),
        "applicability_provenance_sha256": optional_file_sha256(paths["provenance"]),
        "catalog_sha256": artifacts["authority_universe"].get("catalog_sha256"),
        "source_claims_sha256": artifacts["authority_universe"].get("source_claims_sha256"),
        "rule_claim_links_sha256": artifacts["authority_universe"].get(
            "rule_claim_links_sha256"
        ),
        "forest_plan_component_inventory_sha256": artifacts["authority_universe"].get(
            "forest_plan_component_inventory_sha256"
        ),
    }


def _source_set_from_decisions(decisions: list[dict[str, Any]]) -> str | None:
    for decision in decisions:
        source_set_id = str(decision.get("source_set_id") or "").strip()
        if source_set_id:
            return source_set_id
    return None


def _first_present_source_set_id(artifacts: dict[str, Any]) -> str | None:
    for key in (
        "authority_universe",
        "package_fact_graph",
        "package_applicability_context",
        "applicable_authorities",
        "non_applicable_authorities",
        "search_coverage_certificates",
        "provenance",
    ):
        value = str((artifacts.get(key) or {}).get("source_set_id") or "").strip()
        if value:
            return value
    return _source_set_from_decisions(artifacts.get("decisions") or [])


def _first_present_run_id(artifacts: dict[str, Any]) -> str | None:
    for key in (
        "applicable_authorities",
        "non_applicable_authorities",
        "search_coverage_certificates",
        "provenance",
    ):
        value = str((artifacts.get(key) or {}).get("applicability_run_id") or "").strip()
        if value:
            return value
    for decision in artifacts.get("decisions") or []:
        value = str(decision.get("applicability_run_id") or "").strip()
        if value:
            return value
    return None
