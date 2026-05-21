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
from .applicability_validation_artifacts import artifact_hashes
from .applicability_validation_artifacts import build_validation_artifact_paths
from .applicability_validation_artifacts import first_present_run_id
from .applicability_validation_artifacts import first_present_source_set_id
from .applicability_validation_artifacts import load_validation_artifacts
from .applicability_validation_checks import build_validation_checks
from .applicability_validation_freshness import build_validation_freshness_checks
from .applicability_validation_support import candidate_ids
from .applicability_validation_support import decision_status
from .applicability_validation_support import partition_ids
from .applicability_validation_support import utc_now
from .applicability_validation_support import validate_safe_segment
from .applicability_validation_support import write_json


APPLICABILITY_VALIDATION_SCHEMA_VERSION = "applicability-validation-v0"
UNRESOLVED_STATUSES = {"unresolved", "needs_adjudication"}


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
    paths = build_validation_artifact_paths(
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

    artifacts = load_validation_artifacts(paths)
    if source_set_id is None:
        source_set_id = first_present_source_set_id(artifacts)
    if source_set_id:
        validate_safe_segment(source_set_id, "source_set_id")

    checks = [
        *build_validation_checks(
            review_id=review_id,
            source_set_id=source_set_id,
            paths=paths,
            artifacts=artifacts,
        ),
        *build_validation_freshness_checks(
            paths=paths,
            artifacts=artifacts,
            decisions=artifacts["decisions"],
        ),
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
    hashes = artifact_hashes(paths, artifacts)
    summary = {
        "schema_version": APPLICABILITY_VALIDATION_SCHEMA_VERSION,
        "created_at": utc_now(),
        "review_id": review_id,
        "source_set_id": source_set_id,
        "applicability_run_id": first_present_run_id(artifacts),
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
