from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import hashlib
import json
import re

from .applicability_decisions import build_applicability_decisions
from .applicability_retrieval import build_applicability_retrieval_traces
from .applicability_rule_pack import generate_applicability_rule_pack
from .applicability_validation import validate_applicability_run
from .compliance_review import DEFAULT_RULE_PACK_PATH
from .compliance_review import load_rule_pack
from .package_fact_graph import build_package_fact_graph
from .records import sha256_file
from .retrieval import _write_sqlite_index


APPLICABILITY_EVAL_SCHEMA_VERSION = "applicability-eval-v0"
APPLICABILITY_EVAL_RESULT_SCHEMA_VERSION = "applicability-eval-results-v0"
APPLICABILITY_GOLD_EVAL_SCHEMA_VERSION = "applicability-gold-eval-v0"
APPLICABILITY_GOLD_EVAL_RESULT_SCHEMA_VERSION = "applicability-gold-eval-results-v0"
DEFAULT_APPLICABILITY_EVAL_PATH = Path("config/applicability_eval_seed.json")
DEFAULT_APPLICABILITY_GOLD_EVAL_PATH = Path("config/applicability_gold_eval_v0.json")
REQUIRED_GOLD_PROFILES = {"positive", "mixed", "negative"}
SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


@dataclass(frozen=True)
class ApplicabilityEvalResult:
    eval_file: Path
    output_dir: Path
    output_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class ApplicabilityGoldEvalResult:
    gold_file: Path
    output_dir: Path
    output_path: Path
    summary: dict[str, Any]


def run_applicability_eval(
    *,
    output_dir: Path,
    eval_file: Path = DEFAULT_APPLICABILITY_EVAL_PATH,
    base_rule_pack_path: Path = DEFAULT_RULE_PACK_PATH,
    source_set_id: str | None = None,
    results_dir: Path | None = None,
    top_k: int = 5,
) -> ApplicabilityEvalResult:
    """Run deterministic applicability decision-quality eval cases."""

    output_dir = Path(output_dir)
    eval_file = Path(eval_file)
    base_rule_pack_path = Path(base_rule_pack_path)
    eval_payload = _load_eval_payload(eval_file, APPLICABILITY_EVAL_SCHEMA_VERSION)
    base_rule_pack = load_rule_pack(base_rule_pack_path)
    cases = _case_list(eval_payload)
    eval_output_dir = (
        Path(results_dir) if results_dir else output_dir / "reviews" / "applicability_eval"
    )
    eval_output_dir.mkdir(parents=True, exist_ok=True)
    output_path = eval_output_dir / "applicability_eval_results.json"
    inherited_source_chunks = _source_chunk_specs(eval_payload.get("source_chunks"))
    case_results = []
    for index, case in enumerate(cases, start=1):
        case_results.append(
            _run_eval_case(
                output_dir=output_dir,
                eval_output_dir=eval_output_dir,
                eval_file=eval_file,
                eval_payload=eval_payload,
                base_rule_pack_path=base_rule_pack_path,
                base_rule_pack=base_rule_pack,
                source_set_id=source_set_id,
                case=case,
                case_index=index,
                inherited_source_chunks=inherited_source_chunks,
                top_k=top_k,
            )
        )

    passed_count = sum(1 for case in case_results if case["passed"])
    case_count = len(case_results)
    source_set_ids = sorted(
        {str(case["source_set_id"]) for case in case_results if case.get("source_set_id")}
    )
    summary = {
        "schema_version": APPLICABILITY_EVAL_RESULT_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "eval_file": str(eval_file),
        "eval_id": eval_payload.get("id"),
        "eval_version": eval_payload.get("version"),
        "output_dir": str(eval_output_dir),
        "output_path": str(output_path),
        "base_rule_pack_path": str(base_rule_pack_path),
        "base_rule_pack_id": base_rule_pack.get("rule_pack_id"),
        "base_rule_pack_version": base_rule_pack.get("version"),
        "source_set_id": source_set_id or (source_set_ids[0] if len(source_set_ids) == 1 else None),
        "source_set_ids": source_set_ids,
        "case_count": case_count,
        "passed_count": passed_count,
        "failed_count": case_count - passed_count,
        "passed": case_count > 0 and passed_count == case_count,
        "generated_rule_pack_ready_case_count": sum(
            1 for case in case_results if case.get("generated_rule_pack_ready")
        ),
        "metrics": {
            "pass_rate": _rate(passed_count, case_count),
            "status_match_rate": _case_rate(case_results, "expected_statuses_match"),
            "applicable_partition_match_rate": _case_rate(
                case_results,
                "expected_applicable_authorities_match",
            ),
            "non_applicable_partition_match_rate": _case_rate(
                case_results,
                "expected_non_applicable_authorities_match",
            ),
            "coverage_certificate_rate": _case_rate(
                case_results,
                "non_applicable_coverage_supported",
            ),
            "generated_rule_pack_match_rate": _case_rate(
                case_results,
                "generated_rule_pack_matches_applicability",
            ),
        },
        "failure_category_counts": _failure_category_counts(case_results),
        "cases": case_results,
    }
    _write_json(output_path, summary)
    return ApplicabilityEvalResult(
        eval_file=eval_file,
        output_dir=eval_output_dir,
        output_path=output_path,
        summary=summary,
    )


def run_applicability_gold_eval(
    *,
    output_dir: Path,
    gold_file: Path = DEFAULT_APPLICABILITY_GOLD_EVAL_PATH,
    base_rule_pack_path: Path = DEFAULT_RULE_PACK_PATH,
    source_set_id: str | None = None,
    results_dir: Path | None = None,
    top_k: int = 5,
) -> ApplicabilityGoldEvalResult:
    """Run adjudicated applicability gold eval cases through applicability-eval."""

    output_dir = Path(output_dir)
    gold_file = Path(gold_file)
    base_rule_pack_path = Path(base_rule_pack_path)
    gold = _load_eval_payload(gold_file, APPLICABILITY_GOLD_EVAL_SCHEMA_VERSION)
    eval_output_dir = (
        Path(results_dir) if results_dir else output_dir / "reviews" / "applicability_gold_eval"
    )
    eval_output_dir.mkdir(parents=True, exist_ok=True)
    eval_payload = {
        "schema_version": APPLICABILITY_EVAL_SCHEMA_VERSION,
        "id": gold.get("id"),
        "version": gold.get("version"),
        "source_set_id": gold.get("source_set_id"),
        "source_chunks": gold.get("source_chunks") or [],
        "cases": gold.get("cases") or [],
    }
    eval_file = eval_output_dir / "adjudicated_cases.applicability_eval.json"
    _write_json(eval_file, eval_payload)
    checks = [
        _check_gold_identity(gold),
        _check_gold_cases(gold),
        _check_gold_profiles(gold),
        _check_gold_adjudication(gold),
    ]
    adjudication_passed = all(check["passed"] for check in checks)
    eval_summary = None
    eval_error = None
    if adjudication_passed:
        try:
            eval_result = run_applicability_eval(
                output_dir=output_dir,
                eval_file=eval_file,
                base_rule_pack_path=base_rule_pack_path,
                source_set_id=source_set_id,
                results_dir=eval_output_dir / "applicability_eval",
                top_k=top_k,
            )
            eval_summary = eval_result.summary
        except (FileNotFoundError, ValueError) as error:
            eval_error = str(error)

    cases = _case_list(gold)
    profile_counts = dict(Counter(str(case.get("profile") or "") for case in cases))
    eval_passed = bool(eval_summary and eval_summary.get("passed"))
    summary = {
        "schema_version": APPLICABILITY_GOLD_EVAL_RESULT_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "gold_file": str(gold_file),
        "gold_eval_id": gold.get("id"),
        "gold_eval_version": gold.get("version"),
        "output_dir": str(eval_output_dir),
        "output_path": str(eval_output_dir / "applicability_gold_eval_results.json"),
        "applicability_eval_file": str(eval_file),
        "applicability_eval_path": str(
            eval_output_dir / "applicability_eval" / "applicability_eval_results.json"
        ),
        "base_rule_pack_path": str(base_rule_pack_path),
        "source_set_id": source_set_id or (eval_summary or {}).get("source_set_id"),
        "source_set_ids": (eval_summary or {}).get("source_set_ids", []),
        "case_count": len(cases),
        "adjudicated_case_count": sum(
            1 for case in cases if isinstance(case.get("adjudication"), dict)
        ),
        "passed_case_count": int((eval_summary or {}).get("passed_count") or 0),
        "failed_case_count": len(cases) - int((eval_summary or {}).get("passed_count") or 0),
        "profile_counts": profile_counts,
        "required_profiles": sorted(REQUIRED_GOLD_PROFILES),
        "required_profiles_present": sorted(REQUIRED_GOLD_PROFILES.intersection(profile_counts)),
        "adjudication_checks_passed": adjudication_passed,
        "applicability_eval_passed": eval_passed,
        "applicability_eval_error": eval_error,
        "promotion_ready": adjudication_passed and eval_passed,
        "passed": adjudication_passed and eval_passed,
        "checks": checks,
        "metrics": (eval_summary or {}).get("metrics", {}),
        "failure_category_counts": (eval_summary or {}).get("failure_category_counts", {}),
        "cases": (eval_summary or {}).get("cases", []),
    }
    _write_json(Path(summary["output_path"]), summary)
    return ApplicabilityGoldEvalResult(
        gold_file=gold_file,
        output_dir=eval_output_dir,
        output_path=Path(summary["output_path"]),
        summary=summary,
    )


def _run_eval_case(
    *,
    output_dir: Path,
    eval_output_dir: Path,
    eval_file: Path,
    eval_payload: dict[str, Any],
    base_rule_pack_path: Path,
    base_rule_pack: dict[str, Any],
    source_set_id: str | None,
    case: dict[str, Any],
    case_index: int,
    inherited_source_chunks: list[dict[str, Any]],
    top_k: int,
) -> dict[str, Any]:
    case_id = str(case.get("id") or f"case-{case_index}").strip()
    _validate_safe_segment(case_id, "case id")
    case_source_set_id = str(
        source_set_id
        or case.get("source_set_id")
        or eval_payload.get("source_set_id")
        or f"source-set-{case_id}"
    )
    _validate_safe_segment(case_source_set_id, "source_set_id")
    review_id = str(case.get("review_id") or f"applicability-eval-{case_id}")
    _validate_safe_segment(review_id, "review_id")
    review_dir = output_dir / "reviews" / review_id
    applicability_dir = review_dir / "applicability"

    selected_rules = _selected_rules(base_rule_pack, case)
    source_chunks = _case_source_chunks(
        case=case,
        inherited_source_chunks=inherited_source_chunks,
        rules=selected_rules,
        source_set_id=case_source_set_id,
    )
    _write_package_cache(
        review_dir=review_dir,
        review_id=review_id,
        source_set_id=case_source_set_id,
        case=case,
        eval_file=eval_file,
    )
    retrieval_index_path = _write_source_index(
        output_dir=output_dir,
        eval_output_dir=eval_output_dir,
        case_id=case_id,
        source_set_id=case_source_set_id,
        chunks=source_chunks,
    )
    _write_authority_universe(
        applicability_dir=applicability_dir,
        review_id=review_id,
        source_set_id=case_source_set_id,
        base_rule_pack_path=base_rule_pack_path,
        base_rule_pack=base_rule_pack,
        rules=selected_rules,
    )
    build_package_fact_graph(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=case_source_set_id,
        package_path=_case_package_path(case, eval_file),
    )
    build_applicability_retrieval_traces(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=case_source_set_id,
        retrieval_index_path=retrieval_index_path,
        top_k=top_k,
    )
    build_applicability_decisions(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=case_source_set_id,
    )
    validation_result = validate_applicability_run(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=case_source_set_id,
    )
    generated_summary = None
    generated_error = None
    if validation_result.summary.get("passed"):
        try:
            generated_result = generate_applicability_rule_pack(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=case_source_set_id,
                base_rule_pack_path=base_rule_pack_path,
            )
            generated_summary = generated_result.summary
        except (FileNotFoundError, ValueError) as error:
            generated_error = str(error)

    artifacts = _read_case_artifacts(applicability_dir)
    return _score_case(
        case=case,
        case_id=case_id,
        review_id=review_id,
        source_set_id=case_source_set_id,
        review_dir=review_dir,
        retrieval_index_path=retrieval_index_path,
        validation_summary=validation_result.summary,
        generated_summary=generated_summary,
        generated_error=generated_error,
        artifacts=artifacts,
    )


def _score_case(
    *,
    case: dict[str, Any],
    case_id: str,
    review_id: str,
    source_set_id: str,
    review_dir: Path,
    retrieval_index_path: Path,
    validation_summary: dict[str, Any],
    generated_summary: dict[str, Any] | None,
    generated_error: str | None,
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    decisions = artifacts["decisions"]
    generated_rule_pack = artifacts["generated_rule_pack"]
    generated_validation = artifacts["generated_validation"]
    applicable = artifacts["applicable_authorities"]
    non_applicable = artifacts["non_applicable_authorities"]
    coverage = artifacts["search_coverage_certificates"]
    generated_validation_summary = (
        generated_validation.get("summary")
        if isinstance(generated_validation.get("summary"), dict)
        else {}
    )
    package_fact_graph = artifacts["package_fact_graph"]
    retrieval_rows = artifacts["retrieval_rows"]
    graph_rows = artifacts["graph_rows"]
    decisions_by_rule = _decisions_by_rule_id(decisions)
    actual_statuses = {
        rule_id: decision.get("status")
        for rule_id, decision in sorted(decisions_by_rule.items())
    }
    expected_statuses = {
        str(rule_id): str(status)
        for rule_id, status in (case.get("expected_statuses") or {}).items()
    }
    status_mismatches = [
        {
            "rule_id": rule_id,
            "expected": expected,
            "actual": actual_statuses.get(rule_id),
        }
        for rule_id, expected in sorted(expected_statuses.items())
        if actual_statuses.get(rule_id) != expected
    ]
    applicable_rule_ids = _partition_rule_ids(applicable)
    non_applicable_rule_ids = _partition_rule_ids(non_applicable)
    expected_applicable = sorted(_strings(case.get("expected_applicable_rule_ids")))
    expected_non_applicable = sorted(_strings(case.get("expected_non_applicable_rule_ids")))
    expected_generated = sorted(_strings(case.get("expected_generated_rule_ids")))
    generated_rule_ids = sorted(
        str(rule.get("base_rule_id") or rule.get("id"))
        for rule in generated_rule_pack.get("rules") or []
        if isinstance(rule, dict)
    )
    if not expected_generated and generated_rule_pack:
        expected_generated = applicable_rule_ids
    expected_fact_types = sorted(_strings(case.get("expected_package_fact_types")))
    actual_fact_types = sorted(
        {
            str(node.get("node_type"))
            for node in package_fact_graph.get("nodes") or []
            if isinstance(node, dict) and node.get("node_type")
        }
    )
    expected_retrieval = sorted(_strings(case.get("expected_retrieval_rule_ids")))
    expected_graph = sorted(_strings(case.get("expected_graph_rule_ids")))
    expected_absent_graph = sorted(
        _strings(case.get("expected_absent_graph_rule_ids"))
        or _strings(case.get("expected_graph_non_path_rule_ids"))
    )
    expected_negative = sorted(_strings(case.get("expected_negative_evidence_rule_ids")))
    expected_trigger_miss = sorted(_strings(case.get("expected_trigger_miss_rule_ids")))
    expected_source_records = _string_list_mapping(
        case.get("expected_source_record_ids_by_rule_id")
    )
    expected_document_roles = _string_list_mapping(
        case.get("expected_document_roles_by_rule_id")
    )
    expected_package_sections = _string_list_mapping(
        case.get("expected_package_section_families_by_rule_id")
    )
    coverage_ids = _coverage_certificate_ids(coverage)
    non_applicable_coverage_gaps = []
    for authority in non_applicable.get("authorities") or []:
        if not isinstance(authority, dict):
            non_applicable_coverage_gaps.append({"rule_id": None, "reason": "invalid_authority"})
            continue
        cert_ids = _strings(authority.get("search_coverage_certificate_ids"))
        missing = [cert_id for cert_id in cert_ids if cert_id not in coverage_ids]
        if not cert_ids or missing:
            non_applicable_coverage_gaps.append(
                {
                    "rule_id": _authority_rule_id(authority),
                    "search_coverage_certificate_ids": cert_ids,
                    "missing_certificate_ids": missing,
                }
            )
    expected_generated_ready = bool(case.get("expected_generated_rule_pack_ready", True))
    generated_validation_passed = bool(
        generated_summary
        and generated_summary.get("passed")
        and generated_validation_summary.get("generated_rule_pack_ready") is True
    )
    required_artifact_gaps = _required_artifact_gaps(
        artifacts,
        generated_rule_pack_required=expected_generated_ready,
    )
    generated_rule_pack_hash_matches_validation = (
        not expected_generated_ready
        or _file_hash_matches(
            review_dir / "applicability" / "generated_rule_pack.json",
            str(
                generated_validation_summary.get("expected_generated_rule_pack_sha256")
                or generated_validation_summary.get("generated_rule_pack_sha256")
                or ""
            ),
        )
    )
    expected_generated_count = case.get("expected_generated_rule_count")
    if expected_generated_count is not None:
        generated_count_matches = len(generated_rule_ids) == int(expected_generated_count)
    else:
        generated_count_matches = generated_rule_ids == applicable_rule_ids
    result_flags = {
        "validation_passed_matches": bool(validation_summary.get("passed"))
        == bool(case.get("expected_validation_passed", True)),
        "expected_statuses_match": not status_mismatches,
        "expected_applicable_authorities_match": (
            not expected_applicable or applicable_rule_ids == expected_applicable
        ),
        "expected_non_applicable_authorities_match": (
            not expected_non_applicable or non_applicable_rule_ids == expected_non_applicable
        ),
        "package_fact_types_match": set(expected_fact_types).issubset(set(actual_fact_types)),
        "retrieval_trace_coverage_matches": _rules_have_retrieval(
            expected_retrieval,
            retrieval_rows,
        ),
        "graph_trace_coverage_matches": _rules_have_graph(expected_graph, graph_rows),
        "graph_non_path_matches": _rules_lack_graph(expected_absent_graph, graph_rows),
        "source_record_alignment_matches": _rules_match_retrieval_source_records(
            expected_source_records,
            retrieval_rows,
        ),
        "document_role_alignment_matches": _rules_match_retrieval_document_roles(
            expected_document_roles,
            retrieval_rows,
        ),
        "package_section_alignment_matches": _rules_match_package_sections(
            expected_package_sections,
            decisions_by_rule,
        ),
        "negative_evidence_matches": _rules_have_decision_field(
            expected_negative,
            decisions_by_rule,
            "negative_evidence_spans",
        ),
        "trigger_miss_evidence_matches": _rules_have_decision_field(
            expected_trigger_miss,
            decisions_by_rule,
            "explicit_trigger_miss_evidence",
        ),
        "non_applicable_coverage_supported": not non_applicable_coverage_gaps,
        "required_applicability_artifacts_present": not required_artifact_gaps,
        "generated_rule_pack_ready_matches": generated_validation_passed
        == expected_generated_ready,
        "generated_rule_pack_matches_applicability": (
            generated_rule_ids == expected_generated
            and generated_count_matches
            and generated_rule_ids == applicable_rule_ids
        ),
        "generated_rule_pack_hash_matches_validation": generated_rule_pack_hash_matches_validation,
    }
    failure_reasons = [name for name, passed in result_flags.items() if not passed]
    failure_taxonomy = _failure_taxonomy(
        result_flags=result_flags,
        status_mismatches=status_mismatches,
        non_applicable_coverage_gaps=non_applicable_coverage_gaps,
        generated_error=generated_error,
    )
    return {
        "id": case_id,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "profile": case.get("profile"),
        "review_dir": str(review_dir),
        "retrieval_index_path": str(retrieval_index_path),
        "applicability_dir": str(review_dir / "applicability"),
        "authority_universe_path": str(
            review_dir / "applicability" / "authority_universe_snapshot.json"
        ),
        "package_fact_graph_path": str(
            review_dir / "applicability" / "package_fact_graph.json"
        ),
        "retrieval_trace_path": str(
            review_dir / "applicability" / "applicability_retrieval_trace.jsonl"
        ),
        "graph_trace_path": str(
            review_dir / "applicability" / "applicability_graph_trace.jsonl"
        ),
        "applicability_validation_path": str(
            review_dir / "applicability" / "applicability_validation.json"
        ),
        "generated_rule_pack_path": str(
            review_dir / "applicability" / "generated_rule_pack.json"
        ),
        "candidate_authority_count": len(artifacts["authority_universe"].get("candidate_authorities") or []),
        "decision_count": len(decisions),
        "actual_statuses": actual_statuses,
        "expected_statuses": expected_statuses,
        "status_mismatches": status_mismatches,
        "applicable_rule_ids": applicable_rule_ids,
        "non_applicable_rule_ids": non_applicable_rule_ids,
        "generated_rule_ids": generated_rule_ids,
        "expected_generated_rule_ids": expected_generated,
        "package_fact_types": actual_fact_types,
        "expected_package_fact_types": expected_fact_types,
        "expected_absent_graph_rule_ids": expected_absent_graph,
        "expected_source_record_ids_by_rule_id": expected_source_records,
        "expected_document_roles_by_rule_id": expected_document_roles,
        "expected_package_section_families_by_rule_id": expected_package_sections,
        "required_artifact_gaps": required_artifact_gaps,
        "non_applicable_coverage_gaps": non_applicable_coverage_gaps,
        "generated_error": generated_error,
        "generated_rule_pack_ready": generated_validation_passed,
        "validation_passed": bool(validation_summary.get("passed")),
        **result_flags,
        "failure_reasons": failure_reasons,
        "failure_taxonomy": failure_taxonomy,
        "failure_category_counts": dict(Counter(item["category"] for item in failure_taxonomy)),
        "passed": not failure_reasons,
    }


def _write_authority_universe(
    *,
    applicability_dir: Path,
    review_id: str,
    source_set_id: str,
    base_rule_pack_path: Path,
    base_rule_pack: dict[str, Any],
    rules: list[dict[str, Any]],
) -> Path:
    candidates = [
        _candidate_from_rule(
            source_set_id=source_set_id,
            base_rule_pack=base_rule_pack,
            rule=rule,
        )
        for rule in rules
    ]
    without_hash = {
        "schema_version": "authority-universe-snapshot-v0",
        "created_at": _utc_now(),
        "review_id": review_id,
        "source_set_id": source_set_id,
        "base_rule_pack_id": base_rule_pack.get("rule_pack_id"),
        "base_rule_pack_version": base_rule_pack.get("version"),
        "base_rule_pack_sha256": sha256_file(base_rule_pack_path),
        "catalog_sha256": _stable_sha256({"source_set_id": source_set_id, "rules": _rule_ids(rules)}),
        "source_claims_sha256": None,
        "rule_claim_links_sha256": None,
        "forest_plan_component_inventory_sha256": None,
        "artifact_paths": {
            "base_rule_pack_path": str(base_rule_pack_path),
        },
        "validation": {"passed": True, "checks": []},
        "candidate_authorities": candidates,
    }
    authority_universe_sha256 = _stable_sha256(without_hash)
    payload = {
        **without_hash,
        "authority_universe_id": (
            f"authority-universe:{review_id}:{source_set_id}:{authority_universe_sha256[:16]}"
        ),
        "authority_universe_sha256": authority_universe_sha256,
        "summary": {
            "schema_version": "authority-universe-summary-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "candidate_authority_count": len(candidates),
            "rule_template_candidate_count": len(candidates),
            "validation_passed": True,
        },
    }
    path = applicability_dir / "authority_universe_snapshot.json"
    _write_json(path, payload)
    return path


def _candidate_from_rule(
    *,
    source_set_id: str,
    base_rule_pack: dict[str, Any],
    rule: dict[str, Any],
) -> dict[str, Any]:
    rule_id = str(rule.get("id") or "")
    source_record_id = str(
        rule.get("authority_source_record_id")
        or (rule.get("source_filters") or {}).get("source_record_id")
        or ""
    )
    document_role = str(
        rule.get("authority_document_role")
        or (rule.get("source_filters") or {}).get("document_role")
        or rule.get("authority_category")
        or "source"
    )
    positive_groups = _positive_groups(rule)
    negative_terms = _strings(rule.get("does_not_apply_if_package_terms"))
    negative_groups = [[term] for term in negative_terms]
    package_terms = _strings(rule.get("package_terms")) or _strings(
        rule.get("applies_if_package_terms")
    )
    package_query = str(rule.get("package_query") or " ".join(package_terms) or rule_id)
    source_query = str(rule.get("source_query") or rule.get("title") or rule_id)
    return {
        "candidate_authority_id": (
            "rule-template:"
            f"{base_rule_pack.get('rule_pack_id')}:{base_rule_pack.get('version')}:{rule_id}"
        ),
        "candidate_authority_type": "rule_template",
        "source_set_id": source_set_id,
        "authority_category": rule.get("authority_category"),
        "authority_document_role": document_role,
        "source_record_ids": [source_record_id] if source_record_id else [],
        "source_records": [
            {
                "source_record_id": source_record_id,
                "title": rule.get("title"),
                "document_role": document_role,
                "citation_label": f"{source_record_id} | {rule.get('title') or rule_id}",
            }
        ]
        if source_record_id
        else [],
        "required_package_fact_types": [
            "action",
            "agency",
            "decision_posture",
            "nepa_level",
            "package_section",
            "evidence_span",
        ],
        "positive_trigger_groups": positive_groups,
        "negative_trigger_groups": negative_groups,
        "source_role_filters": {
            "source_record_ids": [source_record_id] if source_record_id else [],
            "document_roles": [document_role],
            "authority_categories": [str(rule.get("authority_category") or "")],
        },
        "package_section_filters": {
            "package_query": package_query,
            "package_terms": package_terms,
            "package_section_terms": [],
            "preferred_section_families": _strings(rule.get("preferred_package_sections")),
        },
        "required_source_evidence": {
            "requires_source_record": bool(source_record_id),
            "requires_source_claim_linkage": False,
        },
        "retrieval_contract": {
            "contract_type": "rule_template_retrieval",
            "query_plan_id": f"retrieval-plan:{rule_id}",
            "required_query_types": [
                "exact_keyword",
                "bm25",
                "metadata_filter",
                "package_section",
                "source_role",
            ],
            "source_queries": [source_query],
            "package_queries": [package_query],
            "fused_ranking_strategy": "reciprocal_rank_fusion",
            "requires_selected_and_rejected_results": True,
            "searched_index_hash_required": True,
        },
        "graph_expansion_contract": {
            "contract_type": "rule_template_graph_expansion",
            "start_node_types": ["rule_template", "source_record", "authority"],
            "relationship_types": [
                "source_record",
                "authority_category",
                "source_claim",
                "rule_claim_link",
                "package_fact",
                "evidence_span",
            ],
            "max_depth": 2,
            "requires_path_trace": True,
        },
        "dependency_contract": {
            "dependency_rule_ids": [],
            "exception_rule_ids": [],
            "supersedes_rule_ids": [],
        },
        "search_coverage_requirements": [
            {
                "coverage_class": "positive_trigger_miss",
                "required_query_types": [
                    "exact_keyword",
                    "bm25",
                    "metadata_filter",
                    "package_section",
                    "source_role",
                ],
                "required_artifacts": [
                    "package_fact_graph",
                    "applicability_retrieval_trace",
                    "search_coverage_certificates",
                ],
                "requires_searched_index_hash": True,
            }
        ],
        "rule_template": {
            "base_rule_pack_id": base_rule_pack.get("rule_pack_id"),
            "base_rule_pack_version": base_rule_pack.get("version"),
            "rule_id": rule_id,
            "title": rule.get("title"),
            "question": rule.get("question"),
            "requirement": rule.get("requirement"),
            "severity": rule.get("severity"),
            "applicability_mode": rule.get("applicability_mode"),
        },
        "source_evidence_availability": {
            "available": True,
            "catalog_record_present": True,
            "artifact_sha256_present": True,
            "source_claim_link_count": 0,
            "rule_claim_gap_count": 0,
        },
        "deterministic_applicability_test_contract": {
            "contract_type": "rule_template",
            "applicability_mode": rule.get("applicability_mode"),
            "baseline_required": rule.get("applicability_mode") == "baseline",
            "positive_package_term_groups": positive_groups,
            "negative_package_terms": negative_terms,
        },
        "source_claim_link_ids": [],
        "rule_claim_gap_ids": [],
    }


def _write_package_cache(
    *,
    review_dir: Path,
    review_id: str,
    source_set_id: str,
    case: dict[str, Any],
    eval_file: Path,
) -> None:
    package_dir = review_dir / "package"
    package_path = _case_package_path(case, eval_file)
    text = _case_package_text(case, eval_file)
    artifact_sha256 = hashlib.sha256(f"{review_id}:{text}".encode("utf-8")).hexdigest()
    chunks = []
    for index, chunk_text in enumerate(_split_case_text(text), start=1):
        content_sha256 = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
        chunks.append(
            {
                "chunk_id": f"{review_id}-package-chunk-{index}",
                "source_set_id": f"ea-package-{review_id}",
                "source_record_id": "EA-PACKAGE-001",
                "chunk_index": index - 1,
                "title": str(case.get("package_title") or f"{case.get('id')} package"),
                "document_role": "ea_package",
                "authority_level": "project_record",
                "artifact_sha256": artifact_sha256,
                "artifact_path": str(package_path) if package_path else str(eval_file),
                "citation_label": f"EA-PACKAGE-{index:03d}",
                "parser_name": "applicability-eval-fixture",
                "parser_version": "0.1.0",
                "extracted_at": _utc_now(),
                "source_text_path": str(package_path) if package_path else str(eval_file),
                "char_start": 0,
                "char_end": len(chunk_text),
                "page": index,
                "section": _section_for_chunk(index),
                "heading": _section_for_chunk(index),
                "content_sha256": content_sha256,
                "text": chunk_text,
            }
        )
    manifest = [
        {
            "source_set_id": f"ea-package-{review_id}",
            "source_record_id": "EA-PACKAGE-001",
            "title": str(case.get("package_title") or f"{case.get('id')} package"),
            "artifact_path": str(package_path) if package_path else str(eval_file),
            "artifact_sha256": artifact_sha256,
            "artifact_byte_size": len(text.encode("utf-8")),
            "content_type": "text/plain",
            "citation_label": "EA-PACKAGE-001",
            "extracted_at": _utc_now(),
            "status": "extracted",
            "parser_name": "applicability-eval-fixture",
            "parser_version": "0.1.0",
            "text_path": str(package_path) if package_path else str(eval_file),
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "text_char_count": len(text),
            "chunk_count": len(chunks),
        }
    ]
    _write_jsonl(package_dir / "package_manifest.jsonl", manifest)
    _write_jsonl(package_dir / "package_chunks.jsonl", chunks)


def _write_source_index(
    *,
    output_dir: Path,
    eval_output_dir: Path,
    case_id: str,
    source_set_id: str,
    chunks: list[dict[str, Any]],
) -> Path:
    source_dir = eval_output_dir / "source_indexes" / case_id
    chunks_path = source_dir / "chunks.jsonl"
    sqlite_path = source_dir / "evidence_index.sqlite"
    _write_jsonl(chunks_path, chunks)
    _write_sqlite_index(
        sqlite_path,
        source_set_id=source_set_id,
        chunks=chunks,
        chunks_path=chunks_path,
        catalog_sqlite_path=output_dir / "catalog" / "review_sources.sqlite",
    )
    return sqlite_path


def _case_source_chunks(
    *,
    case: dict[str, Any],
    inherited_source_chunks: list[dict[str, Any]],
    rules: list[dict[str, Any]],
    source_set_id: str,
) -> list[dict[str, Any]]:
    explicit = _source_chunk_specs(case.get("source_chunks"))
    specs = explicit or inherited_source_chunks
    by_source = {str(spec.get("source_record_id")): spec for spec in specs}
    chunks = []
    for rule in rules:
        source_record_id = str(
            rule.get("authority_source_record_id")
            or (rule.get("source_filters") or {}).get("source_record_id")
            or ""
        )
        if not source_record_id:
            continue
        spec = by_source.get(source_record_id, {})
        text = str(
            spec.get("text")
            or rule.get("source_query")
            or rule.get("requirement")
            or rule.get("title")
            or source_record_id
        )
        role = str(
            spec.get("document_role")
            or rule.get("authority_document_role")
            or (rule.get("source_filters") or {}).get("document_role")
            or rule.get("authority_category")
            or "source"
        )
        chunks.append(
            _source_chunk(
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                document_role=role,
                title=str(spec.get("title") or rule.get("title") or source_record_id),
                text=text,
            )
        )
    return chunks


def _source_chunk(
    *,
    source_set_id: str,
    source_record_id: str,
    document_role: str,
    title: str,
    text: str,
) -> dict[str, Any]:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    artifact_sha256 = hashlib.sha256(source_record_id.encode("utf-8")).hexdigest()
    return {
        "chunk_id": f"{source_record_id}-applicability-eval-chunk-0",
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "chunk_index": 0,
        "title": title,
        "document_role": document_role,
        "authority_level": document_role,
        "host": "applicability-eval.local",
        "expected_parser": "text",
        "artifact_sha256": artifact_sha256,
        "artifact_path": f"/applicability-eval/{source_record_id}.txt",
        "citation_label": f"{source_record_id} | {title}",
        "original_url": f"https://applicability-eval.local/{source_record_id}",
        "effective_url": f"https://applicability-eval.local/{source_record_id}",
        "final_url": f"https://applicability-eval.local/{source_record_id}",
        "parser_name": "applicability-eval-fixture",
        "parser_version": "0.1.0",
        "extracted_at": _utc_now(),
        "source_text_path": f"/applicability-eval/{source_record_id}.txt",
        "char_start": 0,
        "char_end": len(text),
        "page": 1,
        "section": "Authority Text",
        "heading": "Authority Text",
        "content_sha256": digest,
        "review_topics": [document_role],
        "text": text,
    }


def _read_case_artifacts(applicability_dir: Path) -> dict[str, Any]:
    return {
        "authority_universe": _read_json_if_exists(
            applicability_dir / "authority_universe_snapshot.json"
        ),
        "package_fact_graph": _read_json_if_exists(applicability_dir / "package_fact_graph.json"),
        "applicability_validation": _read_json_if_exists(
            applicability_dir / "applicability_validation.json"
        ),
        "decisions": _read_jsonl_if_exists(applicability_dir / "applicability_decisions.jsonl"),
        "retrieval_rows": _read_jsonl_if_exists(
            applicability_dir / "applicability_retrieval_trace.jsonl"
        ),
        "graph_rows": _read_jsonl_if_exists(applicability_dir / "applicability_graph_trace.jsonl"),
        "applicable_authorities": _read_json_if_exists(
            applicability_dir / "applicable_authorities.json"
        ),
        "non_applicable_authorities": _read_json_if_exists(
            applicability_dir / "non_applicable_authorities.json"
        ),
        "search_coverage_certificates": _read_json_if_exists(
            applicability_dir / "search_coverage_certificates.json"
        ),
        "generated_rule_pack": _read_json_if_exists(applicability_dir / "generated_rule_pack.json"),
        "generated_validation": _read_json_if_exists(
            applicability_dir / "generated_rule_pack_validation.json"
        ),
    }


def _selected_rules(base_rule_pack: dict[str, Any], case: dict[str, Any]) -> list[dict[str, Any]]:
    rule_ids = _strings(case.get("candidate_rule_ids")) or _strings(case.get("rule_ids"))
    rules = [rule for rule in base_rule_pack.get("rules") or [] if isinstance(rule, dict)]
    if not rule_ids:
        return rules
    wanted = set(rule_ids)
    selected = [rule for rule in rules if str(rule.get("id") or "") in wanted]
    missing = sorted(wanted - {str(rule.get("id") or "") for rule in selected})
    if missing:
        raise ValueError(f"Applicability eval case references unknown rule IDs: {missing}")
    return selected


def _positive_groups(rule: dict[str, Any]) -> list[list[str]]:
    groups = [
        [str(term) for term in group if str(term or "").strip()]
        for group in rule.get("applies_if_package_term_groups") or []
        if isinstance(group, list)
    ]
    if groups:
        return groups
    terms = _strings(rule.get("applies_if_package_terms"))
    return [[term] for term in terms]


def _case_package_text(case: dict[str, Any], eval_file: Path) -> str:
    if case.get("package_text"):
        return str(case["package_text"])
    path = _case_package_path(case, eval_file)
    if path and path.exists():
        return path.read_text(encoding="utf-8")
    raise FileNotFoundError(f"Applicability eval case {case.get('id')} has no package_text/path")


def _case_package_path(case: dict[str, Any], eval_file: Path) -> Path | None:
    package_path = str(case.get("package_path") or "").strip()
    if not package_path:
        return None
    path = Path(package_path)
    if not path.is_absolute():
        path = (eval_file.parent / path).resolve()
    return path


def _split_case_text(text: str) -> list[str]:
    chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n", text) if chunk.strip()]
    return chunks or [text]


def _section_for_chunk(index: int) -> str:
    sections = {
        1: "Purpose and Need",
        2: "Affected Environment",
        3: "Environmental Consequences",
    }
    return sections.get(index, "Appendix")


def _decisions_by_rule_id(decisions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result = {}
    for decision in decisions:
        rule_id = _decision_rule_id(decision)
        if rule_id:
            result[rule_id] = decision
    return result


def _decision_rule_id(decision: dict[str, Any]) -> str:
    rule_template = decision.get("rule_template")
    if isinstance(rule_template, dict) and rule_template.get("rule_id"):
        return str(rule_template["rule_id"])
    candidate_id = str(decision.get("candidate_authority_id") or "")
    return candidate_id.rsplit(":", 1)[-1] if candidate_id else ""


def _authority_rule_id(authority: dict[str, Any]) -> str:
    rule_template = authority.get("rule_template")
    if isinstance(rule_template, dict) and rule_template.get("rule_id"):
        return str(rule_template["rule_id"])
    candidate_id = str(authority.get("candidate_authority_id") or "")
    return candidate_id.rsplit(":", 1)[-1] if candidate_id else ""


def _partition_rule_ids(payload: dict[str, Any]) -> list[str]:
    return sorted(
        _authority_rule_id(authority)
        for authority in payload.get("authorities") or []
        if isinstance(authority, dict) and _authority_rule_id(authority)
    )


def _rules_have_retrieval(rule_ids: list[str], rows: list[dict[str, Any]]) -> bool:
    if not rule_ids:
        return True
    candidate_ids = {
        str(row.get("candidate_authority_id") or "")
        for row in rows
        if row.get("candidate_authority_id")
    }
    return all(any(candidate_id.endswith(f":{rule_id}") for candidate_id in candidate_ids) for rule_id in rule_ids)


def _rules_have_graph(rule_ids: list[str], rows: list[dict[str, Any]]) -> bool:
    if not rule_ids:
        return True
    candidate_ids = {
        str(row.get("candidate_authority_id") or "")
        for row in rows
        if row.get("candidate_authority_id")
    }
    return all(any(candidate_id.endswith(f":{rule_id}") for candidate_id in candidate_ids) for rule_id in rule_ids)


def _rules_lack_graph(rule_ids: list[str], rows: list[dict[str, Any]]) -> bool:
    if not rule_ids:
        return True
    candidate_ids = {
        str(row.get("candidate_authority_id") or "")
        for row in rows
        if row.get("candidate_authority_id")
    }
    return all(not any(candidate_id.endswith(f":{rule_id}") for candidate_id in candidate_ids) for rule_id in rule_ids)


def _rules_match_retrieval_source_records(
    expected_by_rule: dict[str, list[str]],
    rows: list[dict[str, Any]],
) -> bool:
    if not expected_by_rule:
        return True
    actual = _retrieval_source_record_ids_by_rule(rows)
    return all(
        set(expected).issubset(actual.get(rule_id, set()))
        for rule_id, expected in expected_by_rule.items()
    )


def _rules_match_retrieval_document_roles(
    expected_by_rule: dict[str, list[str]],
    rows: list[dict[str, Any]],
) -> bool:
    if not expected_by_rule:
        return True
    actual = _retrieval_document_roles_by_rule(rows)
    return all(
        set(expected).issubset(actual.get(rule_id, set()))
        for rule_id, expected in expected_by_rule.items()
    )


def _rules_match_package_sections(
    expected_by_rule: dict[str, list[str]],
    decisions_by_rule: dict[str, dict[str, Any]],
) -> bool:
    if not expected_by_rule:
        return True
    actual = {
        rule_id: _decision_package_section_families(decision)
        for rule_id, decision in decisions_by_rule.items()
    }
    return all(
        set(expected).issubset(actual.get(rule_id, set()))
        for rule_id, expected in expected_by_rule.items()
    )


def _rules_have_decision_field(
    rule_ids: list[str],
    decisions_by_rule: dict[str, dict[str, Any]],
    field: str,
) -> bool:
    return all(bool((decisions_by_rule.get(rule_id) or {}).get(field)) for rule_id in rule_ids)


def _retrieval_source_record_ids_by_rule(rows: list[dict[str, Any]]) -> dict[str, set[str]]:
    actual: dict[str, set[str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        rule_id = _rule_id_from_candidate_id(str(row.get("candidate_authority_id") or ""))
        if not rule_id:
            continue
        values = actual.setdefault(rule_id, set())
        values.update(_strings(row.get("source_record_filters")))
        source_filters = row.get("source_filters") if isinstance(row.get("source_filters"), dict) else {}
        values.update(_strings(source_filters.get("source_record_ids")))
        for result in row.get("ranked_results") or []:
            if isinstance(result, dict) and result.get("source_record_id"):
                values.add(str(result["source_record_id"]))
    return actual


def _retrieval_document_roles_by_rule(rows: list[dict[str, Any]]) -> dict[str, set[str]]:
    actual: dict[str, set[str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        rule_id = _rule_id_from_candidate_id(str(row.get("candidate_authority_id") or ""))
        if not rule_id:
            continue
        source_filters = row.get("source_filters") if isinstance(row.get("source_filters"), dict) else {}
        actual.setdefault(rule_id, set()).update(_strings(source_filters.get("document_roles")))
    return actual


def _decision_package_section_families(decision: dict[str, Any]) -> set[str]:
    sections = set()
    for field in (
        "package_evidence_spans",
        "negative_evidence_spans",
        "explicit_trigger_miss_evidence",
    ):
        for span in decision.get(field) or []:
            if isinstance(span, dict) and span.get("section_family"):
                sections.add(str(span["section_family"]))
    return sections


def _rule_id_from_candidate_id(candidate_id: str) -> str:
    return candidate_id.rsplit(":", 1)[-1] if candidate_id else ""


def _coverage_certificate_ids(payload: dict[str, Any]) -> set[str]:
    return {
        str(certificate.get("coverage_certificate_id") or certificate.get("certificate_id") or "")
        for certificate in payload.get("certificates") or []
        if isinstance(certificate, dict)
        and str(certificate.get("coverage_certificate_id") or certificate.get("certificate_id") or "").strip()
    }


def _required_artifact_gaps(
    artifacts: dict[str, Any],
    *,
    generated_rule_pack_required: bool,
) -> list[str]:
    required: dict[str, Any] = {
        "authority_universe": artifacts["authority_universe"],
        "package_fact_graph": artifacts["package_fact_graph"],
        "applicability_validation": artifacts["applicability_validation"],
        "applicability_decisions": artifacts["decisions"],
        "applicability_retrieval_trace": artifacts["retrieval_rows"],
        "applicability_graph_trace": artifacts["graph_rows"],
        "applicable_authorities": artifacts["applicable_authorities"],
        "non_applicable_authorities": artifacts["non_applicable_authorities"],
        "search_coverage_certificates": artifacts["search_coverage_certificates"],
    }
    if generated_rule_pack_required:
        required["generated_rule_pack"] = artifacts["generated_rule_pack"]
        required["generated_rule_pack_validation"] = artifacts["generated_validation"]
    return sorted(name for name, value in required.items() if not value)


def _file_hash_matches(path: Path, expected_sha256: str) -> bool:
    return bool(path.exists() and expected_sha256 and sha256_file(path) == expected_sha256)


def _failure_taxonomy(
    *,
    result_flags: dict[str, bool],
    status_mismatches: list[dict[str, Any]],
    non_applicable_coverage_gaps: list[dict[str, Any]],
    generated_error: str | None,
) -> list[dict[str, Any]]:
    taxonomy = []
    for name, passed in sorted(result_flags.items()):
        if passed:
            continue
        category = {
            "expected_statuses_match": "applicability_status_mismatch",
            "expected_applicable_authorities_match": "applicable_partition_mismatch",
            "expected_non_applicable_authorities_match": "non_applicable_partition_mismatch",
            "graph_trace_coverage_matches": "graph_trace_gap",
            "graph_non_path_matches": "graph_trace_gap",
            "source_record_alignment_matches": "source_record_alignment_mismatch",
            "document_role_alignment_matches": "document_role_alignment_mismatch",
            "package_section_alignment_matches": "package_section_alignment_mismatch",
            "package_fact_types_match": "package_fact_gap",
            "retrieval_trace_coverage_matches": "retrieval_trace_gap",
            "non_applicable_coverage_supported": "search_coverage_gap",
            "required_applicability_artifacts_present": "missing_applicability_artifact",
            "generated_rule_pack_matches_applicability": "generated_rule_pack_mismatch",
            "generated_rule_pack_hash_matches_validation": "generated_rule_pack_mismatch",
            "generated_rule_pack_ready_matches": "generated_rule_pack_not_ready",
            "validation_passed_matches": "applicability_validation_mismatch",
        }.get(name, "applicability_eval_mismatch")
        details: dict[str, Any] = {}
        if name == "expected_statuses_match":
            details["status_mismatches"] = status_mismatches
        if name == "non_applicable_coverage_supported":
            details["coverage_gaps"] = non_applicable_coverage_gaps
        if generated_error:
            details["generated_error"] = generated_error
        taxonomy.append({"check": name, "category": category, "details": details})
    return taxonomy


def _failure_category_counts(case_results: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for case in case_results:
        counts.update(case.get("failure_category_counts") or {})
    return dict(sorted(counts.items()))


def _check_gold_identity(gold: dict[str, Any]) -> dict[str, Any]:
    passed = gold.get("schema_version") == APPLICABILITY_GOLD_EVAL_SCHEMA_VERSION
    return _check(
        "gold_eval_identity_valid",
        passed,
        {"schema_version": gold.get("schema_version")},
    )


def _check_gold_cases(gold: dict[str, Any]) -> dict[str, Any]:
    cases = _case_list(gold)
    ids = [str(case.get("id") or "") for case in cases]
    duplicate_ids = sorted({case_id for case_id in ids if ids.count(case_id) > 1})
    unsafe_ids = sorted(case_id for case_id in ids if not SAFE_SEGMENT_RE.match(case_id))
    passed = bool(cases) and not duplicate_ids and not unsafe_ids
    return _check(
        "gold_eval_cases_present",
        passed,
        {
            "case_count": len(cases),
            "duplicate_ids": duplicate_ids,
            "unsafe_ids": unsafe_ids,
        },
    )


def _check_gold_profiles(gold: dict[str, Any]) -> dict[str, Any]:
    profile_counts = Counter(str(case.get("profile") or "") for case in _case_list(gold))
    missing = sorted(REQUIRED_GOLD_PROFILES - set(profile_counts))
    return _check(
        "gold_eval_required_profiles_present",
        not missing,
        {"profile_counts": dict(profile_counts), "missing_profiles": missing},
    )


def _check_gold_adjudication(gold: dict[str, Any]) -> dict[str, Any]:
    failures = []
    for case in _case_list(gold):
        adjudication = case.get("adjudication")
        if not isinstance(adjudication, dict):
            failures.append({"case_id": case.get("id"), "fields": ["adjudication"]})
            continue
        missing = [
            field
            for field in ("status", "rationale", "adjudicated_by", "adjudicated_at")
            if not adjudication.get(field)
        ]
        if missing:
            failures.append({"case_id": case.get("id"), "fields": missing})
    return _check("gold_eval_cases_have_adjudication", not failures, {"failures": failures})


def _check(name: str, passed: bool, details: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "details": details}


def _load_eval_payload(path: Path, schema_version: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing eval file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, list):
        value = {"schema_version": schema_version, "cases": value}
    if not isinstance(value, dict):
        raise ValueError("Applicability eval file must be a JSON object or case list.")
    if value.get("schema_version") != schema_version:
        raise ValueError(
            f"Expected {schema_version} eval file, got {value.get('schema_version')}"
        )
    return value


def _case_list(payload: dict[str, Any]) -> list[dict[str, Any]]:
    cases = payload.get("cases")
    return cases if isinstance(cases, list) else []


def _source_chunk_specs(value: Any) -> list[dict[str, Any]]:
    return [item for item in value or [] if isinstance(item, dict)]


def _rule_ids(rules: list[dict[str, Any]]) -> list[str]:
    return sorted(str(rule.get("id") or "") for rule in rules if rule.get("id"))


def _strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item or "").strip()]
    return [str(value)] if str(value or "").strip() else []


def _string_list_mapping(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key): sorted(_strings(item))
        for key, item in value.items()
        if str(key or "").strip() and _strings(item)
    }


def _rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _case_rate(case_results: list[dict[str, Any]], field: str) -> float:
    return _rate(sum(1 for case in case_results if case.get(field)), len(case_results))


def _validate_safe_segment(value: str, label: str) -> None:
    if not SAFE_SEGMENT_RE.match(value):
        raise ValueError(f"Unsafe {label}: {value!r}")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _stable_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def _read_jsonl_if_exists(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
