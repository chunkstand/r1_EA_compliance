from __future__ import annotations

from pathlib import Path
from typing import Any

from .applicability_validation_support import first_present
from .applicability_validation_support import optional_file_sha256
from .records import sha256_file

REQUIRED_PROVENANCE_ENTITY_IDS = {
    "authority_universe",
    "selected_action",
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

__all__ = [
    "build_validation_freshness_checks",
    "check_artifact_freshness",
    "check_provenance",
]


def build_validation_freshness_checks(
    *,
    paths: dict[str, Path],
    artifacts: dict[str, Any],
    decisions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        check_artifact_freshness(paths=paths, artifacts=artifacts, decisions=decisions),
        check_provenance(artifacts["provenance"], paths, artifacts),
    ]


def check_artifact_freshness(
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
    selected_action_hash = first_present(
        artifacts["selected_action"].get("selected_action_sha256"),
        artifacts["package_applicability_context"].get("selected_action_sha256"),
        artifacts["package_fact_graph"].get("selected_action_sha256"),
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
        "selected_action_sha256": (selected_action_hash, "package_cache_stale"),
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
            "selected_action_sha256": (selected_action_hash, "package_cache_stale"),
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


def check_provenance(
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
        "selected_action": first_present(
            artifacts["selected_action"].get("selected_action_sha256"),
            artifacts["package_applicability_context"].get("selected_action_sha256"),
            artifacts["package_fact_graph"].get("selected_action_sha256"),
        ),
    }
