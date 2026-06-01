from __future__ import annotations

from importlib import import_module
from pathlib import Path

from .eval_metrics import (
    average,
    contract_snapshot,
    first_relevant_rank,
    metric_threshold_check,
    ndcg_at_k,
    reciprocal_rank,
)
from .claim_extraction_eval_support import (
    _claim_coverage_check as _claim_coverage_check,
    _claim_has_required_provenance as _claim_has_required_provenance,
    _claim_relevance as _claim_relevance,
    _dedupe as _dedupe,
    _eval_failure_reasons as _eval_failure_reasons,
    _expected_terms_found as _expected_terms_found,
    _load_eval_contract as _load_eval_contract,
    _load_validated_claims_for_eval as _load_validated_claims_for_eval,
    _matched_expected_source_record_ids as _matched_expected_source_record_ids,
    _query_claims as _query_claims,
    _source_matched_hits as _source_matched_hits,
    _source_record_matches_expected_ids as _source_record_matches_expected_ids,
    _source_set_id_from_claims_path as _source_set_id_from_claims_path,
)


_CLAIM_EXTRACTION = import_module("usfs_r1_ea_sources.claim_extraction")
CLAIM_EVAL_RESULTS_SCHEMA_VERSION = _CLAIM_EXTRACTION.CLAIM_EVAL_RESULTS_SCHEMA_VERSION
CLAIM_EVAL_SCHEMA_VERSION = _CLAIM_EXTRACTION.CLAIM_EVAL_SCHEMA_VERSION
ClaimEvalResult = _CLAIM_EXTRACTION.ClaimEvalResult
SUPPORTED_CLAIM_EVAL_FILTERS = _CLAIM_EXTRACTION.SUPPORTED_CLAIM_EVAL_FILTERS
SUPPORTED_CLAIM_TYPES = _CLAIM_EXTRACTION.SUPPORTED_CLAIM_TYPES
validate_claim_outputs = _CLAIM_EXTRACTION.validate_claim_outputs
_rate = _CLAIM_EXTRACTION._rate
_read_json = _CLAIM_EXTRACTION._read_json
_read_jsonl = _CLAIM_EXTRACTION._read_jsonl
_utc_now = _CLAIM_EXTRACTION._utc_now
_write_json = _CLAIM_EXTRACTION._write_json


def run_claim_eval(
    *,
    claims_path: Path,
    eval_file: Path,
    top_k: int = 5,
    output_dir: Path | None = None,
) -> ClaimEvalResult:
    """Run deterministic eval cases against extracted source claims."""

    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    claims_path = Path(claims_path)
    eval_file = Path(eval_file)
    claims = _load_validated_claims_for_eval(claims_path)
    contract, cases, legacy_format = _load_eval_contract(eval_file)
    output_dir = output_dir or claims_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "claim_eval_results.json"
    source_set_id = _source_set_id_from_claims_path(claims_path)

    case_results = []
    for case in cases:
        filters = dict(case.get("filters") or {})
        expect_no_hits = bool(case.get("expect_no_hits"))
        expected_sources = _dedupe(
            str(value) for value in case.get("expected_source_record_ids", [])
        )
        expected_terms = [str(value) for value in case.get("expected_terms", [])]
        expected_claim_types = _dedupe(
            str(value)
            for value in case.get(
                "expected_claim_types",
                [case["expected_claim_type"]] if case.get("expected_claim_type") else [],
            )
        )
        forbidden_sources = _dedupe(
            str(value) for value in case.get("forbidden_source_record_ids", [])
        )
        forbidden_claim_types = _dedupe(
            str(value) for value in case.get("forbidden_claim_types", [])
        )
        min_claims = 0 if expect_no_hits else int(case.get("min_claims", 1))
        hits = _query_claims(
            claims,
            query=str(case.get("query") or ""),
            filters=filters,
            limit=int(case.get("top_k") or top_k),
        )
        zero_hits = len(hits) == 0
        relevance = _claim_relevance(
            hits,
            expected_sources=expected_sources,
            expected_claim_types=expected_claim_types,
            expected_terms=expected_terms,
        )
        source_matched_hits = _source_matched_hits(hits, expected_sources)
        relevant_hits = [
            hit
            for hit, is_relevant in zip(hits, relevance, strict=False)
            if is_relevant
        ]
        matched_expected_sources = _matched_expected_source_record_ids(
            expected_sources,
            source_matched_hits,
        )
        missing_expected_sources = [
            source_id for source_id in expected_sources if source_id not in matched_expected_sources
        ]
        source_hit = zero_hits if expect_no_hits else (not expected_sources or not missing_expected_sources)
        type_hit = zero_hits if expect_no_hits else (
            not expected_claim_types
            or any(
                hit["claim_type"] in expected_claim_types
                for hit in (source_matched_hits or hits)
            )
        )
        term_hit = zero_hits if expect_no_hits else (
            not expected_terms or _expected_terms_found(expected_terms, source_matched_hits or hits)
        )
        min_claims_met = len(hits) >= min_claims
        unexpected_sources = [
            hit["source_record_id"]
            for hit in hits
            if _source_record_matches_expected_ids(
                str(hit.get("source_record_id") or ""),
                forbidden_sources,
            )
        ]
        unexpected_claim_types = [
            hit["claim_type"] for hit in hits if hit["claim_type"] in forbidden_claim_types
        ]
        provenance_supported = (
            zero_hits
            if expect_no_hits
            else bool(source_matched_hits or relevant_hits or hits)
            and any(
                _claim_has_required_provenance(hit)
                for hit in (source_matched_hits or relevant_hits or hits)
            )
        )
        first_rank = first_relevant_rank(relevance)
        top_rank_relevant = bool(relevance and relevance[0])
        top_rank_false_positive = bool(hits) if expect_no_hits else bool(hits) and not top_rank_relevant
        required_source_recall = _rate(
            len(matched_expected_sources),
            len(expected_sources),
        )
        passed = (
            min_claims_met
            and source_hit
            and type_hit
            and term_hit
            and provenance_supported
            and not top_rank_false_positive
            and not unexpected_sources
            and not unexpected_claim_types
        )
        case_results.append(
            {
                "id": case["id"],
                "query": case.get("query") or "",
                "filters": filters,
                "hard_negative": bool(case.get("hard_negative") or expect_no_hits),
                "multi_source_or_type_confusion": bool(
                    case.get("multi_source_or_type_confusion")
                    or len(expected_sources) > 1
                ),
                "expected_source_record_ids": expected_sources,
                "expected_claim_types": expected_claim_types,
                "expected_terms": expected_terms,
                "forbidden_source_record_ids": forbidden_sources,
                "forbidden_claim_types": forbidden_claim_types,
                "expect_no_hits": expect_no_hits,
                "top_k": int(case.get("top_k") or top_k),
                "hit_count": len(hits),
                "top_claim_ids": [hit["claim_id"] for hit in hits],
                "top_source_record_ids": [hit["source_record_id"] for hit in hits],
                "source_hit": source_hit,
                "type_hit": type_hit,
                "term_hit": term_hit,
                "matched_expected_source_record_ids": matched_expected_sources,
                "missing_expected_source_record_ids": missing_expected_sources,
                "unexpected_source_record_ids": unexpected_sources,
                "unexpected_claim_types": unexpected_claim_types,
                "required_source_recall": required_source_recall,
                "min_claims_met": min_claims_met,
                "provenance_supported": provenance_supported,
                "relevant_ranks": [
                    index for index, is_relevant in enumerate(relevance, start=1) if is_relevant
                ],
                "first_relevant_rank": first_rank,
                "top_rank_relevant": top_rank_relevant,
                "top_rank_false_positive": top_rank_false_positive,
                "failure_reasons": _eval_failure_reasons(
                    expect_no_hits=expect_no_hits,
                    min_claims_met=min_claims_met,
                    source_hit=source_hit,
                    type_hit=type_hit,
                    term_hit=term_hit,
                    provenance_supported=provenance_supported,
                    top_rank_false_positive=top_rank_false_positive,
                    unexpected_sources=unexpected_sources,
                    unexpected_claim_types=unexpected_claim_types,
                ),
                "passed": passed,
                "top_results": hits,
            }
        )

    case_count = len(case_results)
    passed_count = sum(1 for case in case_results if case["passed"])
    failed_count = case_count - passed_count
    source_hit_count = sum(1 for case in case_results if case["source_hit"])
    type_hit_count = sum(1 for case in case_results if case["type_hit"])
    term_hit_count = sum(1 for case in case_results if case["term_hit"])
    provenance_supported_count = sum(
        1 for case in case_results if case["provenance_supported"]
    )
    zero_result_count = sum(1 for case in case_results if case["hit_count"] == 0)
    hard_negative_cases = [case for case in case_results if case["hard_negative"]]
    complex_cases = [
        case for case in case_results if case["multi_source_or_type_confusion"]
    ]
    ranking_cases = [
        case
        for case in case_results
        if not case["expect_no_hits"] and case["expected_source_record_ids"]
    ]
    total_required_sources = sum(len(case["expected_source_record_ids"]) for case in ranking_cases)
    matched_required_sources = sum(
        len(case["matched_expected_source_record_ids"]) for case in ranking_cases
    )
    metrics = {
        "case_count": case_count,
        "pass_rate": _rate(passed_count, case_count),
        "source_hit_rate": _rate(source_hit_count, case_count),
        "claim_type_hit_rate": _rate(type_hit_count, case_count),
        "expected_term_hit_rate": _rate(term_hit_count, case_count),
        "citation_coverage_rate": _rate(provenance_supported_count, case_count),
        "zero_result_rate": _rate(zero_result_count, case_count),
        "hard_negative_pass_rate": _rate(
            sum(1 for case in hard_negative_cases if case["hit_count"] == 0),
            len(hard_negative_cases),
        ),
        "false_positive_rate": _rate(
            sum(1 for case in case_results if case["top_rank_false_positive"]),
            case_count,
        ),
        "missing_required_source_rate": _rate(
            total_required_sources - matched_required_sources,
            total_required_sources,
        ),
        "recall_at_k": _rate(matched_required_sources, total_required_sources),
        "mrr": average(
            reciprocal_rank(
                _claim_relevance(
                    case["top_results"],
                    expected_sources=case["expected_source_record_ids"],
                    expected_claim_types=case["expected_claim_types"],
                    expected_terms=case["expected_terms"],
                )
            )
            for case in ranking_cases
        ),
        "ndcg_at_k": average(
            ndcg_at_k(
                _claim_relevance(
                    case["top_results"],
                    expected_sources=case["expected_source_record_ids"],
                    expected_claim_types=case["expected_claim_types"],
                    expected_terms=case["expected_terms"],
                ),
                relevant_count=max(1, len(case["expected_source_record_ids"])),
                k=case["top_k"],
            )
            for case in ranking_cases
        ),
    }
    checks = [
        {
            "name": "eval_cases_pass",
            "passed": failed_count == 0,
            "details": {
                "case_count": case_count,
                "failed_case_ids": [case["id"] for case in case_results if not case["passed"]],
            },
        },
        _claim_coverage_check(contract, case_results, legacy_format=legacy_format),
        metric_threshold_check(contract.get("metric_thresholds", {}), metrics),
    ]
    summary = {
        "schema_version": CLAIM_EVAL_RESULTS_SCHEMA_VERSION,
        "eval_id": contract.get("eval_id"),
        "source_set_id": source_set_id,
        "claims_path": str(claims_path),
        "eval_file": str(eval_file),
        "output_path": str(output_path),
        "created_at": _utc_now(),
        "top_k": top_k,
        "case_count": case_count,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "hard_negative_case_count": len(hard_negative_cases),
        "multi_source_or_type_confusion_case_count": len(complex_cases),
        "checks": checks,
        "metrics": metrics,
        "contract": contract_snapshot(
            contract_path=eval_file,
            contract=contract,
            case_count=len(cases),
        ),
        "cases": case_results,
    }
    summary["passed"] = all(check["passed"] for check in checks)
    _write_json(output_path, summary)
    return ClaimEvalResult(
        claims_path=claims_path,
        eval_file=eval_file,
        output_path=output_path,
        summary=summary,
    )
