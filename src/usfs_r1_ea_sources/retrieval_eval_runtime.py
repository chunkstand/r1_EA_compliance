from __future__ import annotations

from pathlib import Path

from .eval_metrics import (
    average,
    contract_snapshot,
    first_relevant_rank,
    metric_threshold_check,
    ndcg_at_k,
    read_json_payload,
    reciprocal_rank,
)
from .retrieval_common import (
    RETRIEVAL_EVAL_RESULTS_SCHEMA_VERSION,
    RETRIEVAL_EVAL_SCHEMA_VERSION,
    RetrievalEvalResult,
    _rate,
    _source_set_id_from_index_path,
    _utc_now,
    _write_json,
)
from .retrieval_query import query_retrieval_index


def run_retrieval_eval(
    *,
    index_path: Path,
    eval_file: Path,
    top_k: int = 5,
    output_dir: Path | None = None,
) -> RetrievalEvalResult:
    """Run a small evidence retrieval eval set against the local index."""

    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    index_path = Path(index_path)
    eval_file = Path(eval_file)
    contract, cases, legacy_format = _load_eval_contract(eval_file)
    output_dir = output_dir or index_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "retrieval_eval_results.json"
    source_set_id = _source_set_id_from_index_path(index_path)

    case_results = []
    for case in cases:
        filters = dict(case.get("filters") or {})
        expect_no_hits = bool(case.get("expect_no_hits"))
        result = query_retrieval_index(
            index_path=index_path,
            query=str(case["query"]),
            limit=int(case.get("top_k") or top_k),
            document_role=filters.get("document_role"),
            support_document_role=filters.get("support_document_role"),
            authority_level=filters.get("authority_level"),
            source_record_id=filters.get("source_record_id"),
            review_topic=filters.get("review_topic") or filters.get("topic"),
            citation=filters.get("citation"),
            host=filters.get("host"),
        )
        hits = result["results"]
        expected_sources = _dedupe(
            str(value) for value in case.get("expected_source_record_ids", [])
        )
        expected_terms = [str(value) for value in case.get("expected_terms", [])]
        forbidden_sources = _dedupe(
            str(value) for value in case.get("forbidden_source_record_ids", [])
        )
        min_hits = 0 if expect_no_hits else int(case.get("min_hits", 1))
        zero_hits = len(hits) == 0
        matched_expected_sources = _matched_expected_source_record_ids(
            expected_sources,
            hits,
        )
        missing_expected_sources = [
            source_id for source_id in expected_sources if source_id not in matched_expected_sources
        ]
        source_hit = zero_hits if expect_no_hits else (not expected_sources or not missing_expected_sources)
        term_hit = zero_hits if expect_no_hits else (
            not expected_terms or _expected_terms_found(expected_terms, hits)
        )
        missing_expected_terms = [] if expect_no_hits else _missing_expected_terms(expected_terms, hits)
        unexpected_sources = [
            hit["source_record_id"]
            for hit in hits
            if hit["source_record_id"] in forbidden_sources
        ]
        relevance = _retrieval_relevance(hits, expected_sources)
        relevant_hits = [
            hit
            for hit, is_relevant in zip(hits, relevance, strict=False)
            if is_relevant
        ]
        first_rank = first_relevant_rank(relevance)
        top_rank_relevant = bool(relevance and relevance[0])
        top_rank_false_positive = bool(hits) if expect_no_hits else bool(hits) and not top_rank_relevant
        required_source_recall = _rate(
            len(matched_expected_sources),
            len(expected_sources),
        )
        min_hits_met = len(hits) >= min_hits
        provenance_supported = (
            zero_hits
            if expect_no_hits
            else bool(relevant_hits or hits)
            and any(_hit_has_required_provenance(hit) for hit in (relevant_hits or hits))
        )
        passed = (
            min_hits_met
            and source_hit
            and term_hit
            and provenance_supported
            and not top_rank_false_positive
            and not unexpected_sources
        )
        failure_reasons = _eval_failure_reasons(
            expect_no_hits=expect_no_hits,
            min_hits_met=min_hits_met,
            source_hit=source_hit,
            term_hit=term_hit,
            provenance_supported=provenance_supported,
            top_rank_false_positive=top_rank_false_positive,
            unexpected_sources=unexpected_sources,
        )
        case_results.append(
            {
                "id": case["id"],
                "query": case["query"],
                "filters": filters,
                "hard_negative": bool(case.get("hard_negative") or expect_no_hits),
                "multi_source": bool(case.get("multi_source") or len(expected_sources) > 1),
                "expected_source_record_ids": expected_sources,
                "expected_terms": expected_terms,
                "forbidden_source_record_ids": forbidden_sources,
                "expect_no_hits": expect_no_hits,
                "top_k": int(case.get("top_k") or top_k),
                "min_hits": min_hits,
                "hit_count": len(hits),
                "matched_expected_source_record_ids": matched_expected_sources,
                "missing_expected_source_record_ids": missing_expected_sources,
                "missing_expected_terms": missing_expected_terms,
                "unexpected_source_record_ids": unexpected_sources,
                "source_hit": source_hit,
                "term_hit": term_hit,
                "required_source_recall": required_source_recall,
                "min_hits_met": min_hits_met,
                "provenance_supported": provenance_supported,
                "relevant_ranks": [
                    index for index, is_relevant in enumerate(relevance, start=1) if is_relevant
                ],
                "first_relevant_rank": first_rank,
                "top_rank_relevant": top_rank_relevant,
                "top_rank_false_positive": top_rank_false_positive,
                "failure_reasons": failure_reasons,
                "passed": passed,
                "top_results": hits,
            }
        )

    query_count = len(case_results)
    passed_count = sum(1 for case in case_results if case["passed"])
    failed_count = query_count - passed_count
    zero_result_count = sum(1 for case in case_results if case["hit_count"] == 0)
    provenance_supported_count = sum(
        1 for case in case_results if case["provenance_supported"]
    )
    source_hit_count = sum(1 for case in case_results if case["source_hit"])
    term_hit_count = sum(1 for case in case_results if case["term_hit"])
    unsupported_answer_count = query_count - provenance_supported_count
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
        "case_count": query_count,
        "pass_rate": _rate(passed_count, query_count),
        "source_hit_rate": _rate(source_hit_count, query_count),
        "expected_term_hit_rate": _rate(term_hit_count, query_count),
        "citation_coverage_rate": _rate(provenance_supported_count, query_count),
        "unsupported_answer_rate": _rate(unsupported_answer_count, query_count),
        "zero_result_rate": _rate(zero_result_count, query_count),
        "hard_negative_pass_rate": _rate(
            sum(1 for case in hard_negative_cases if case["hit_count"] == 0),
            len(hard_negative_cases),
        ),
        "false_positive_rate": _rate(
            sum(1 for case in case_results if case["top_rank_false_positive"]),
            query_count,
        ),
        "missing_required_source_rate": _rate(
            total_required_sources - matched_required_sources,
            total_required_sources,
        ),
        "recall_at_k": _rate(matched_required_sources, total_required_sources),
        "mrr": average(
            reciprocal_rank(
                _retrieval_relevance(
                    case["top_results"],
                    case["expected_source_record_ids"],
                )
            )
            for case in ranking_cases
        ),
        "ndcg_at_k": average(
            ndcg_at_k(
                _retrieval_relevance(
                    case["top_results"],
                    case["expected_source_record_ids"],
                ),
                relevant_count=len(case["expected_source_record_ids"]),
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
                "case_count": query_count,
                "failed_case_ids": [case["id"] for case in case_results if not case["passed"]],
            },
        },
        _retrieval_coverage_check(contract, case_results, legacy_format=legacy_format),
        metric_threshold_check(contract.get("metric_thresholds", {}), metrics),
    ]
    summary = {
        "schema_version": RETRIEVAL_EVAL_RESULTS_SCHEMA_VERSION,
        "eval_id": contract.get("eval_id"),
        "source_set_id": source_set_id,
        "index_path": str(index_path),
        "eval_file": str(eval_file),
        "output_path": str(output_path),
        "created_at": _utc_now(),
        "top_k": top_k,
        "query_count": query_count,
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
    return RetrievalEvalResult(
        index_path=index_path,
        eval_file=eval_file,
        output_path=output_path,
        summary=summary,
    )


def _load_eval_contract(path: Path) -> tuple[dict, list[dict], bool]:
    payload = read_json_payload(path, label="retrieval eval file")
    if isinstance(payload, list):
        cases = _validated_eval_cases(payload, legacy_format=True)
        return (
            {
                "schema_version": "legacy-retrieval-eval-list-v0",
                "eval_id": f"legacy-{path.stem}",
                "coverage_requirements": {},
                "metric_thresholds": {},
                "cases": cases,
            },
            cases,
            True,
        )
    if payload.get("schema_version") != RETRIEVAL_EVAL_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported retrieval eval schema_version: "
            f"{payload.get('schema_version')!r}"
        )
    if not str(payload.get("eval_id") or "").strip():
        raise ValueError("Retrieval eval contract missing 'eval_id'.")
    if not isinstance(payload.get("coverage_requirements"), dict):
        raise ValueError("Retrieval eval contract missing 'coverage_requirements'.")
    if not isinstance(payload.get("metric_thresholds"), dict):
        raise ValueError("Retrieval eval contract missing 'metric_thresholds'.")
    _validate_retrieval_coverage_requirements(payload["coverage_requirements"])
    cases = _validated_eval_cases(payload.get("cases"), legacy_format=False)
    return payload, cases, False


def _validated_eval_cases(payload: object, *, legacy_format: bool) -> list[dict]:
    if not isinstance(payload, list) or not payload:
        raise ValueError(
            "Retrieval eval file must contain a non-empty JSON list."
            if legacy_format
            else "Retrieval eval contract must contain non-empty cases."
        )
    case_ids = []
    for index, case in enumerate(payload):
        if not isinstance(case, dict):
            raise ValueError(f"Retrieval eval case {index} must be an object.")
        for field in ("id", "query"):
            if not case.get(field):
                raise ValueError(f"Retrieval eval case {index} is missing {field!r}.")
        case_ids.append(str(case["id"]))
        _validate_optional_string_list(case, "expected_source_record_ids", index)
        _validate_optional_string_list(case, "expected_terms", index)
        _validate_optional_string_list(case, "forbidden_source_record_ids", index)
        _validate_optional_bool(case, "expect_no_hits", index)
        _validate_optional_bool(case, "hard_negative", index)
        _validate_optional_bool(case, "multi_source", index)
        _validate_positive_eval_int(case, "min_hits", index)
        _validate_positive_eval_int(case, "top_k", index)
    duplicates = sorted(case_id for case_id in set(case_ids) if case_ids.count(case_id) > 1)
    if duplicates:
        raise ValueError(f"Duplicate retrieval eval case IDs: {duplicates}")
    return payload


def _validate_retrieval_coverage_requirements(requirements: dict) -> None:
    for key in (
        "case_count",
        "hard_negative_case_count",
        "multi_source_case_count",
    ):
        value = requirements.get(key)
        if not isinstance(value, int) or value < 0:
            raise ValueError(
                f"Retrieval eval coverage_requirements.{key} must be a non-negative integer."
            )


def _validate_optional_string_list(case: dict, field: str, index: int) -> None:
    if field not in case:
        return
    values = case.get(field)
    if not isinstance(values, list) or any(not str(value).strip() for value in values):
        raise ValueError(f"Retrieval eval case {index} {field} must be a non-empty string list.")


def _validate_optional_bool(case: dict, field: str, index: int) -> None:
    if field in case and not isinstance(case[field], bool):
        raise ValueError(f"Retrieval eval case {index} {field} must be a boolean.")


def _validate_positive_eval_int(case: dict, field: str, index: int) -> None:
    if field not in case:
        return
    value = case[field]
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"Retrieval eval case {index} {field} must be a non-negative integer.")


def _matched_expected_source_record_ids(expected_sources: list[str], hits: list[dict]) -> list[str]:
    return [
        source_id
        for source_id in expected_sources
        if source_id in {hit["source_record_id"] for hit in hits}
    ]


def _dedupe(values: object) -> list[str]:
    result = []
    seen = set()
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _retrieval_relevance(hits: list[dict], expected_sources: list[str]) -> list[bool]:
    if not expected_sources:
        return [False for _ in hits]
    remaining = set(expected_sources)
    relevance = []
    for hit in hits:
        source_record_id = str(hit.get("source_record_id") or "")
        is_relevant = source_record_id in remaining
        relevance.append(is_relevant)
        if is_relevant:
            remaining.remove(source_record_id)
    return relevance


def _retrieval_coverage_check(
    contract: dict,
    case_results: list[dict],
    *,
    legacy_format: bool,
) -> dict:
    if legacy_format:
        return {
            "name": "coverage_requirements_met",
            "passed": True,
            "details": {"enabled": False, "legacy_format": True},
        }
    requirements = contract.get("coverage_requirements", {})
    actuals = {
        "case_count": len(case_results),
        "hard_negative_case_count": sum(1 for case in case_results if case["hard_negative"]),
        "multi_source_case_count": sum(1 for case in case_results if case["multi_source"]),
    }
    failures = [
        {
            "requirement": key,
            "min": int(requirements.get(key) or 0),
            "actual": actuals[key],
        }
        for key in actuals
        if actuals[key] < int(requirements.get(key) or 0)
    ]
    return {
        "name": "coverage_requirements_met",
        "passed": not failures,
        "details": {
            "enabled": True,
            "requirements": requirements,
            "actuals": actuals,
            "failures": failures,
        },
    }


def _expected_terms_found(expected_terms: list[str], hits: list[dict]) -> bool:
    return not _missing_expected_terms(expected_terms, hits)


def _missing_expected_terms(expected_terms: list[str], hits: list[dict]) -> list[str]:
    haystack = "\n".join(
        " ".join(
            [
                hit.get("title", ""),
                hit.get("citation_label", ""),
                hit.get("evidence_span", {}).get("text", ""),
                " ".join(hit.get("review_topics", [])),
            ]
        )
        for hit in hits
    ).lower()
    return [term for term in expected_terms if term.lower() not in haystack]


def _eval_failure_reasons(
    *,
    expect_no_hits: bool,
    min_hits_met: bool,
    source_hit: bool,
    term_hit: bool,
    provenance_supported: bool,
    top_rank_false_positive: bool,
    unexpected_sources: list[str],
) -> list[str]:
    reasons = []
    if expect_no_hits:
        if not source_hit:
            reasons.append("expected_zero_hits")
        if top_rank_false_positive:
            reasons.append("unexpected_hit_returned")
        return reasons
    if not min_hits_met:
        reasons.append("min_hits_not_met")
    if not source_hit:
        reasons.append("expected_source_not_retrieved")
    if not term_hit:
        reasons.append("expected_terms_not_retrieved")
    if not provenance_supported:
        reasons.append("citation_provenance_missing")
    if top_rank_false_positive:
        reasons.append("top_rank_not_relevant")
    if unexpected_sources:
        reasons.append("forbidden_source_retrieved")
    return reasons


def _hit_has_required_provenance(hit: dict) -> bool:
    provenance = hit.get("provenance") or {}
    span = hit.get("evidence_span") or {}
    required = [
        "artifact_sha256",
        "artifact_path",
        "parser_name",
        "parser_version",
        "char_start",
        "char_end",
        "content_sha256",
    ]
    return bool(hit.get("citation_label")) and bool(span.get("text")) and all(
        provenance.get(field) not in (None, "") for field in required
    )
