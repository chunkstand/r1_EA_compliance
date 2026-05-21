from __future__ import annotations

from importlib import import_module
from pathlib import Path
import re
from .eval_metrics import (
    average,
    contract_snapshot,
    first_relevant_rank,
    metric_threshold_check,
    ndcg_at_k,
    read_json_payload,
    reciprocal_rank,
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
        relevant_hits = [
            hit
            for hit, is_relevant in zip(hits, relevance, strict=False)
            if is_relevant
        ]
        matched_expected_sources = _dedupe(hit["source_record_id"] for hit in relevant_hits)
        missing_expected_sources = [
            source_id for source_id in expected_sources if source_id not in matched_expected_sources
        ]
        source_hit = zero_hits if expect_no_hits else (not expected_sources or not missing_expected_sources)
        type_hit = zero_hits if expect_no_hits else (
            not expected_claim_types
            or any(hit["claim_type"] in expected_claim_types for hit in relevant_hits)
        )
        term_hit = zero_hits if expect_no_hits else (
            not expected_terms or _expected_terms_found(expected_terms, relevant_hits or hits)
        )
        min_claims_met = len(hits) >= min_claims
        unexpected_sources = [
            hit["source_record_id"]
            for hit in hits
            if hit["source_record_id"] in forbidden_sources
        ]
        unexpected_claim_types = [
            hit["claim_type"] for hit in hits if hit["claim_type"] in forbidden_claim_types
        ]
        provenance_supported = (
            zero_hits
            if expect_no_hits
            else bool(relevant_hits or hits)
            and any(_claim_has_required_provenance(hit) for hit in (relevant_hits or hits))
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


def _query_claims(
    claims: list[dict],
    *,
    query: str,
    filters: dict,
    limit: int,
) -> list[dict]:
    terms = _tokenize(query)
    scored = []
    for claim in claims:
        if not _claim_matches_filters(claim, filters):
            continue
        score = _score_claim(claim, terms=terms, query=query)
        if terms and score <= 0:
            continue
        scored.append((score, claim))
    scored.sort(
        key=lambda item: (
            -item[0],
            str(item[1]["source_record_id"]),
            int(item[1]["source_char_start"]),
        )
    )
    return [_claim_eval_result(claim, score) for score, claim in scored[:limit]]


def _load_validated_claims_for_eval(
    claims_path: Path,
    *,
    require_reviewer_ready: bool = True,
) -> list[dict]:
    if not claims_path.exists():
        raise FileNotFoundError(f"Missing claims file: {claims_path}")
    claims_path = claims_path.resolve()
    claims_dir = claims_path.parent
    summary_path = claims_dir / "summary.json"
    validation_path = claims_dir / "claim_validation.json"
    missing = [
        str(path)
        for path in (summary_path, validation_path)
        if not path.exists()
    ]
    if missing:
        raise FileNotFoundError(
            "Missing claim readiness artifact(s): " + ", ".join(missing)
        )
    summary = _read_json(summary_path)
    validation = _read_json(validation_path)
    allowed_partial_failures = {
        "extraction_validation_passed",
        "extraction_scope_is_complete",
        "retrieval_is_reviewer_ready",
    }
    if not validation.get("passed"):
        failed = ", ".join(_failed_check_names(validation))
        if require_reviewer_ready or any(
            name not in allowed_partial_failures
            for name in _failed_check_names(validation)
        ):
            raise ValueError(
                f"Claim artifacts failed validation: {claims_dir}. "
                f"Resolve claim_validation.json failures before reuse. Failed checks: {failed}"
            )
    if require_reviewer_ready and not summary.get("reviewer_ready"):
        raise ValueError(
            f"Claim artifacts are not reviewer-ready: {claims_dir}. "
            "Run claim-extract and resolve claim_validation.json failures before claim-eval."
        )
    source_set_id = str(summary.get("source_set_id") or "")
    if not source_set_id:
        raise ValueError(f"Claim summary has no source_set_id: {summary_path}")
    output_dir = _output_dir_from_claims_path(claims_path, source_set_id=source_set_id)
    current_validation = validate_claim_outputs(
        output_dir=output_dir,
        source_set_id=source_set_id,
        claims_path=claims_path,
        entities_path=_required_summary_path(summary, "entities_path"),
        nodes_path=_required_summary_path(summary, "nodes_path"),
        edges_path=_required_summary_path(summary, "edges_path"),
        chunks_path=_required_summary_path(summary, "chunks_path"),
    )
    if not current_validation["passed"]:
        failed = ", ".join(_failed_check_names(current_validation))
        if require_reviewer_ready or any(
            name not in allowed_partial_failures
            for name in _failed_check_names(current_validation)
        ):
            raise ValueError(
                f"Current claim artifacts failed validation before eval: {failed}"
            )
    return _read_jsonl(claims_path)

def _required_summary_path(summary: dict, key: str) -> Path:
    value = summary.get(key)
    if not value:
        raise ValueError(f"Claim summary is missing {key!r}.")
    return Path(str(value))

def _output_dir_from_claims_path(claims_path: Path, *, source_set_id: str) -> Path:
    if claims_path.name != "claims.jsonl":
        raise ValueError(f"Expected claims.jsonl path, got: {claims_path}")
    claims_dir = claims_path.parent
    source_dir = claims_dir.parent
    derived_dir = source_dir.parent
    if claims_dir.name != "claims" or source_dir.name != source_set_id or derived_dir.name != "derived":
        raise ValueError(
            "Claims path must be under source_library/derived/<source_set_id>/claims/."
        )
    return derived_dir.parent

def _claim_matches_filters(claim: dict, filters: dict) -> bool:
    for key in (
        "source_record_id",
        "claim_type",
        "document_role",
        "authority_level",
        "citation_label",
    ):
        value = filters.get(key)
        if value and str(claim.get(key) or "").lower() != str(value).lower():
            return False
    review_topic = filters.get("review_topic") or filters.get("topic")
    if review_topic:
        needle = str(review_topic).lower()
        topics = [str(topic).lower() for topic in claim.get("review_topics", [])]
        if not any(needle == topic or needle in topic for topic in topics):
            return False
    return True

def _score_claim(claim: dict, *, terms: list[str], query: str) -> float:
    if not terms:
        return 0.1
    text = " ".join(
        [
            str(claim.get("claim_text") or ""),
            str(claim.get("title") or ""),
            str(claim.get("citation_label") or ""),
            " ".join(str(topic) for topic in claim.get("review_topics", [])),
        ]
    )
    token_set = set(_tokenize(text))
    term_hits = sum(1 for term in terms if _contains_term(term, token_set, text))
    score = term_hits / len(terms)
    if query.strip() and query.strip().lower() in text.lower():
        score += 0.4
    return score

def _claim_eval_result(claim: dict, score: float) -> dict:
    return {
        "score": round(score, 6),
        "claim_id": claim["claim_id"],
        "claim_type": claim["claim_type"],
        "claim_text": claim["claim_text"],
        "source_record_id": claim["source_record_id"],
        "chunk_id": claim["chunk_id"],
        "citation_label": claim["citation_label"],
        "authority_level": claim["authority_level"],
        "document_role": claim["document_role"],
        "review_topics": claim.get("review_topics", []),
        "provenance": {
            "source_set_id": claim["source_set_id"],
            "artifact_sha256": claim["artifact_sha256"],
            "artifact_path": claim["artifact_path"],
            "parser_name": claim["parser_name"],
            "parser_version": claim["parser_version"],
            "source_text_path": claim.get("source_text_path"),
            "source_char_start": claim["source_char_start"],
            "source_char_end": claim["source_char_end"],
            "chunk_char_start": claim["chunk_char_start"],
            "chunk_char_end": claim["chunk_char_end"],
            "content_sha256": claim["content_sha256"],
        },
    }


def _expected_terms_found(expected_terms: list[str], hits: list[dict]) -> bool:
    haystack = "\n".join(
        " ".join(
            [
                hit.get("claim_text", ""),
                hit.get("citation_label", ""),
                " ".join(hit.get("review_topics", [])),
            ]
        )
        for hit in hits
    ).lower()
    return all(term.lower() in haystack for term in expected_terms)


def _claim_has_required_provenance(claim: dict) -> bool:
    provenance = claim.get("provenance", {})
    return all(
        provenance.get(field) not in (None, "")
        for field in (
            "source_set_id",
            "artifact_sha256",
            "artifact_path",
            "parser_name",
            "parser_version",
            "source_char_start",
            "source_char_end",
            "content_sha256",
        )
    ) and bool(claim.get("citation_label"))


def _eval_failure_reasons(
    *,
    expect_no_hits: bool,
    min_claims_met: bool,
    source_hit: bool,
    type_hit: bool,
    term_hit: bool,
    provenance_supported: bool,
    top_rank_false_positive: bool,
    unexpected_sources: list[str],
    unexpected_claim_types: list[str],
) -> list[str]:
    reasons = []
    if expect_no_hits:
        if not source_hit:
            reasons.append("expected_zero_hits")
        if top_rank_false_positive:
            reasons.append("unexpected_hit_returned")
        return reasons
    if not min_claims_met:
        reasons.append("min_claims_not_met")
    if not source_hit:
        reasons.append("expected_source_not_extracted")
    if not type_hit:
        reasons.append("expected_claim_type_not_extracted")
    if not term_hit:
        reasons.append("expected_terms_not_extracted")
    if not provenance_supported:
        reasons.append("citation_provenance_missing")
    if top_rank_false_positive:
        reasons.append("top_rank_not_relevant")
    if unexpected_sources:
        reasons.append("forbidden_source_extracted")
    if unexpected_claim_types:
        reasons.append("forbidden_claim_type_extracted")
    return reasons


def _load_eval_contract(path: Path) -> tuple[dict, list[dict], bool]:
    payload = read_json_payload(path, label="claim eval file")
    if isinstance(payload, list):
        cases = _validated_eval_cases(payload, legacy_format=True)
        return (
            {
                "schema_version": "legacy-claim-eval-list-v0",
                "eval_id": f"legacy-{path.stem}",
                "coverage_requirements": {},
                "metric_thresholds": {},
                "cases": cases,
            },
            cases,
            True,
        )
    if payload.get("schema_version") != CLAIM_EVAL_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported claim eval schema_version: "
            f"{payload.get('schema_version')!r}"
        )
    if not str(payload.get("eval_id") or "").strip():
        raise ValueError("Claim eval contract missing 'eval_id'.")
    if not isinstance(payload.get("coverage_requirements"), dict):
        raise ValueError("Claim eval contract missing 'coverage_requirements'.")
    if not isinstance(payload.get("metric_thresholds"), dict):
        raise ValueError("Claim eval contract missing 'metric_thresholds'.")
    _validate_claim_coverage_requirements(payload["coverage_requirements"])
    cases = _validated_eval_cases(payload.get("cases"), legacy_format=False)
    return payload, cases, False


def _validated_eval_cases(payload: object, *, legacy_format: bool) -> list[dict]:
    if not isinstance(payload, list) or not payload:
        raise ValueError(
            "Claim eval file must contain a non-empty JSON list."
            if legacy_format
            else "Claim eval contract must contain non-empty cases."
        )
    case_ids = []
    for index, case in enumerate(payload):
        if not isinstance(case, dict):
            raise ValueError(f"Claim eval case {index} must be an object.")
        for field in ("id", "query"):
            if not case.get(field):
                raise ValueError(f"Claim eval case {index} is missing {field!r}.")
        case_ids.append(str(case["id"]))
        _validate_eval_case_filters(index, case)
        _validate_eval_case_expectations(index, case)
        _validate_positive_eval_int(index, case, "min_claims")
        _validate_positive_eval_int(index, case, "top_k")
    duplicates = sorted(case_id for case_id in set(case_ids) if case_ids.count(case_id) > 1)
    if duplicates:
        raise ValueError(f"Duplicate claim eval case IDs: {duplicates}")
    return payload


def _validate_claim_coverage_requirements(requirements: dict) -> None:
    for key in (
        "case_count",
        "hard_negative_case_count",
        "multi_source_or_type_confusion_case_count",
    ):
        value = requirements.get(key)
        if not isinstance(value, int) or value < 0:
            raise ValueError(
                f"Claim eval coverage_requirements.{key} must be a non-negative integer."
            )


def _validate_eval_case_filters(index: int, case: dict) -> None:
    filters = case.get("filters") or {}
    if not isinstance(filters, dict):
        raise ValueError(f"Claim eval case {index} filters must be an object.")
    unknown = sorted(set(filters) - SUPPORTED_CLAIM_EVAL_FILTERS)
    empty = sorted(key for key, value in filters.items() if value in (None, "", []))
    claim_type = filters.get("claim_type")
    if claim_type and claim_type not in SUPPORTED_CLAIM_TYPES:
        raise ValueError(
            f"Claim eval case {index} has unsupported claim_type filter: {claim_type!r}."
        )
    if unknown or empty:
        details = []
        if unknown:
            details.append(f"unknown filters: {unknown}")
        if empty:
            details.append(f"empty filters: {empty}")
        raise ValueError(
            f"Claim eval case {index} has unsupported filters; " + "; ".join(details)
        )


def _validate_eval_case_expectations(index: int, case: dict) -> None:
    expected_claim_types = case.get("expected_claim_types")
    expected_claim_type = case.get("expected_claim_type")
    if expected_claim_types is not None:
        if not isinstance(expected_claim_types, list) or not expected_claim_types:
            raise ValueError(
                f"Claim eval case {index} expected_claim_types must be a non-empty list."
            )
        unsupported = sorted(set(str(value) for value in expected_claim_types) - SUPPORTED_CLAIM_TYPES)
        if unsupported:
            raise ValueError(
                f"Claim eval case {index} has unsupported expected_claim_types: {unsupported}."
            )
    if expected_claim_type is not None and expected_claim_type not in SUPPORTED_CLAIM_TYPES:
        raise ValueError(
            f"Claim eval case {index} has unsupported expected_claim_type: {expected_claim_type!r}."
        )
    for key in (
        "expected_source_record_ids",
        "expected_terms",
        "forbidden_source_record_ids",
        "forbidden_claim_types",
    ):
        value = case.get(key)
        if value is not None and (
            not isinstance(value, list) or any(not str(item).strip() for item in value)
        ):
            raise ValueError(f"Claim eval case {index} {key} must be a non-empty string list.")
    for key in ("expect_no_hits", "hard_negative", "multi_source_or_type_confusion"):
        if key in case and not isinstance(case[key], bool):
            raise ValueError(f"Claim eval case {index} {key} must be a boolean.")


def _validate_positive_eval_int(index: int, case: dict, key: str) -> None:
    if key not in case:
        return
    try:
        value = int(case[key])
    except (TypeError, ValueError) as error:
        raise ValueError(f"Claim eval case {index} {key} must be an integer.") from error
    if value < 1:
        raise ValueError(f"Claim eval case {index} {key} must be at least 1.")


def _source_set_id_from_claims_path(claims_path: Path) -> str:
    if claims_path.parent.name != "claims":
        raise ValueError(f"Claims path must live under a claims directory: {claims_path}")
    return claims_path.parent.parent.name


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


def _claim_term_match(expected_terms: list[str], hit: dict) -> bool:
    if not expected_terms:
        return True
    haystack = " ".join(
        [
            hit.get("claim_text", ""),
            hit.get("citation_label", ""),
            " ".join(hit.get("review_topics", [])),
        ]
    ).lower()
    return all(term.lower() in haystack for term in expected_terms)


def _claim_relevance(
    hits: list[dict],
    *,
    expected_sources: list[str],
    expected_claim_types: list[str],
    expected_terms: list[str],
) -> list[bool]:
    if not (expected_sources or expected_claim_types or expected_terms):
        return [False for _ in hits]
    remaining_sources = set(expected_sources) if expected_sources else None
    relevance = []
    for hit in hits:
        source_record_id = str(hit.get("source_record_id") or "")
        claim_type = str(hit.get("claim_type") or "")
        source_ok = not expected_sources or source_record_id in expected_sources
        type_ok = not expected_claim_types or claim_type in expected_claim_types
        term_ok = _claim_term_match(expected_terms, hit)
        is_relevant = source_ok and type_ok and term_ok
        if is_relevant and remaining_sources is not None:
            is_relevant = source_record_id in remaining_sources
            if is_relevant:
                remaining_sources.remove(source_record_id)
        relevance.append(is_relevant)
    return relevance


def _claim_coverage_check(
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
        "multi_source_or_type_confusion_case_count": sum(
            1 for case in case_results if case["multi_source_or_type_confusion"]
        ),
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


def _failed_check_names(validation: dict) -> list[str]:
    return [
        str(check.get("name"))
        for check in validation.get("checks", [])
        if not check.get("passed")
    ]


def _contains_term(term: str, token_set: set[str], text: str) -> bool:
    if term in token_set:
        return True
    lower = text.lower()
    if term in lower:
        return True
    return any(token.startswith(term) or term.startswith(token) for token in token_set)


def _tokenize(value: str) -> list[str]:
    return [
        token.strip("'-.")
        for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]{1,}", value.lower())
        if len(token.strip("'-.") or "") >= 2
    ]
