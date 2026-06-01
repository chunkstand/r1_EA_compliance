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
from .rule_claim_binding_eval_support import _dedupe
from .rule_claim_binding_eval_support import _eval_failure_reasons
from .rule_claim_binding_eval_support import _expected_terms_found
from .rule_claim_binding_eval_support import _link_has_required_provenance
from .rule_claim_binding_eval_support import _link_relevance
from .rule_claim_binding_eval_support import _load_eval_contract
from .rule_claim_binding_eval_support import _load_validated_links_for_eval
from .rule_claim_binding_eval_support import _matched_expected_source_record_ids
from .rule_claim_binding_eval_support import _query_links
from .rule_claim_binding_eval_support import _rule_claim_coverage_check
from .rule_claim_binding_eval_support import _source_matched_hits
from .rule_claim_binding_eval_support import _source_record_matches_expected_ids
from .rule_claim_binding_eval_support import _source_set_id_from_links_path


_RULE_CLAIM_BINDING = import_module("usfs_r1_ea_sources.rule_claim_binding")
DEFAULT_TOP_K = _RULE_CLAIM_BINDING.DEFAULT_TOP_K
RULE_CLAIM_LINK_EVAL_RESULTS_SCHEMA_VERSION = (
    _RULE_CLAIM_BINDING.RULE_CLAIM_LINK_EVAL_RESULTS_SCHEMA_VERSION
)
RULE_CLAIM_LINK_EVAL_SCHEMA_VERSION = _RULE_CLAIM_BINDING.RULE_CLAIM_LINK_EVAL_SCHEMA_VERSION
RuleClaimLinkEvalResult = _RULE_CLAIM_BINDING.RuleClaimLinkEvalResult
SUPPORTED_RULE_CLAIM_EVAL_FILTERS = _RULE_CLAIM_BINDING.SUPPORTED_RULE_CLAIM_EVAL_FILTERS
validate_rule_claim_links = _RULE_CLAIM_BINDING.validate_rule_claim_links
_failed_check_names = _RULE_CLAIM_BINDING._failed_check_names
_output_dir_from_links_path = _RULE_CLAIM_BINDING._output_dir_from_links_path
_output_dir_from_link_summary = _RULE_CLAIM_BINDING._output_dir_from_link_summary
_rate = _RULE_CLAIM_BINDING._rate
_read_json = _RULE_CLAIM_BINDING._read_json
_read_jsonl = _RULE_CLAIM_BINDING._read_jsonl
_utc_now = _RULE_CLAIM_BINDING._utc_now
_write_json = _RULE_CLAIM_BINDING._write_json


def run_rule_claim_link_eval(
    *,
    links_path: Path,
    eval_file: Path,
    top_k: int = DEFAULT_TOP_K,
    output_dir: Path | None = None,
) -> RuleClaimLinkEvalResult:
    """Run deterministic eval cases against rule-to-source-claim links."""

    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    links_path = Path(links_path)
    eval_file = Path(eval_file)
    links = _load_validated_links_for_eval(links_path)
    contract, cases, legacy_format = _load_eval_contract(eval_file)
    output_dir = output_dir or links_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "rule_claim_link_eval_results.json"
    source_set_id = _source_set_id_from_links_path(links_path)

    case_results = []
    for case in cases:
        filters = dict(case.get("filters") or {})
        expect_no_hits = bool(case.get("expect_no_hits"))
        rule_id = str(case.get("rule_id") or filters.get("rule_id") or "")
        expected_terms = [str(value) for value in case.get("expected_terms", [])]
        expected_claim_types = _dedupe(
            str(value) for value in case.get("expected_claim_types", [])
        )
        expected_sources = _dedupe(
            str(value) for value in case.get("expected_source_record_ids", [])
        )
        forbidden_sources = _dedupe(
            str(value) for value in case.get("forbidden_source_record_ids", [])
        )
        forbidden_claim_types = _dedupe(
            str(value) for value in case.get("forbidden_claim_types", [])
        )
        min_links = 0 if expect_no_hits else int(case.get("min_links", 1))
        hits = _query_links(
            links,
            rule_id=rule_id,
            filters=filters,
            limit=int(case.get("top_k") or top_k),
        )
        zero_hits = len(hits) == 0
        relevance = _link_relevance(
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
        min_links_met = len(hits) >= min_links
        type_hit = zero_hits if expect_no_hits else (
            not expected_claim_types
            or any(
                hit["claim_type"] in expected_claim_types
                for hit in (source_matched_hits or hits)
            )
        )
        source_hit = zero_hits if expect_no_hits else (
            not expected_sources or not missing_expected_sources
        )
        term_hit = zero_hits if expect_no_hits else (
            not expected_terms or _expected_terms_found(expected_terms, source_matched_hits or hits)
        )
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
                _link_has_required_provenance(hit)
                for hit in (source_matched_hits or relevant_hits or hits)
            )
        )
        first_rank = first_relevant_rank(relevance)
        top_rank_relevant = bool(relevance and relevance[0])
        top_rank_false_positive = (
            bool(hits) if expect_no_hits else bool(hits) and not top_rank_relevant
        )
        required_source_recall = _rate(
            len(matched_expected_sources),
            len(expected_sources),
        )
        passed = (
            min_links_met
            and type_hit
            and source_hit
            and term_hit
            and provenance_supported
            and not top_rank_false_positive
            and not unexpected_sources
            and not unexpected_claim_types
        )
        case_results.append(
            {
                "id": case["id"],
                "rule_id": rule_id,
                "filters": filters,
                "hard_negative": bool(case.get("hard_negative") or expect_no_hits),
                "multi_source": bool(case.get("multi_source")),
                "expected_terms": expected_terms,
                "expected_claim_types": expected_claim_types,
                "expected_source_record_ids": expected_sources,
                "forbidden_source_record_ids": forbidden_sources,
                "forbidden_claim_types": forbidden_claim_types,
                "expect_no_hits": expect_no_hits,
                "top_k": int(case.get("top_k") or top_k),
                "hit_count": len(hits),
                "top_link_ids": [hit["link_id"] for hit in hits],
                "top_claim_ids": [hit["claim_id"] for hit in hits],
                "top_source_record_ids": [hit["source_record_id"] for hit in hits],
                "min_links_met": min_links_met,
                "type_hit": type_hit,
                "source_hit": source_hit,
                "term_hit": term_hit,
                "matched_expected_source_record_ids": matched_expected_sources,
                "missing_expected_source_record_ids": missing_expected_sources,
                "unexpected_source_record_ids": unexpected_sources,
                "unexpected_claim_types": unexpected_claim_types,
                "required_source_recall": required_source_recall,
                "provenance_supported": provenance_supported,
                "relevant_ranks": [
                    index for index, is_relevant in enumerate(relevance, start=1) if is_relevant
                ],
                "first_relevant_rank": first_rank,
                "top_rank_relevant": top_rank_relevant,
                "top_rank_false_positive": top_rank_false_positive,
                "failure_reasons": _eval_failure_reasons(
                    expect_no_hits=expect_no_hits,
                    min_links_met=min_links_met,
                    type_hit=type_hit,
                    source_hit=source_hit,
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
    hard_negative_cases = [case for case in case_results if case["hard_negative"]]
    multi_source_cases = [case for case in case_results if case["multi_source"]]
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
        "min_link_rate": _rate(
            sum(1 for case in case_results if case["min_links_met"]),
            case_count,
        ),
        "claim_type_hit_rate": _rate(
            sum(1 for case in case_results if case["type_hit"]),
            case_count,
        ),
        "source_hit_rate": _rate(
            sum(1 for case in case_results if case["source_hit"]),
            case_count,
        ),
        "expected_term_hit_rate": _rate(
            sum(1 for case in case_results if case["term_hit"]),
            case_count,
        ),
        "citation_coverage_rate": _rate(
            sum(1 for case in case_results if case["provenance_supported"]),
            case_count,
        ),
        "zero_result_rate": _rate(
            sum(1 for case in case_results if case["hit_count"] == 0),
            case_count,
        ),
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
                _link_relevance(
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
                _link_relevance(
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
        _rule_claim_coverage_check(contract, case_results, legacy_format=legacy_format),
        metric_threshold_check(contract.get("metric_thresholds", {}), metrics),
    ]
    summary = {
        "schema_version": RULE_CLAIM_LINK_EVAL_RESULTS_SCHEMA_VERSION,
        "eval_id": contract.get("eval_id"),
        "source_set_id": source_set_id,
        "links_path": str(links_path),
        "eval_file": str(eval_file),
        "output_path": str(output_path),
        "created_at": _utc_now(),
        "top_k": top_k,
        "case_count": case_count,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "hard_negative_case_count": len(hard_negative_cases),
        "multi_source_case_count": len(multi_source_cases),
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
    return RuleClaimLinkEvalResult(
        links_path=links_path,
        eval_file=eval_file,
        output_path=output_path,
        summary=summary,
    )
