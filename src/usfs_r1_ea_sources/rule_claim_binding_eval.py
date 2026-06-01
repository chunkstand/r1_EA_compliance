from __future__ import annotations

from importlib import import_module
from pathlib import Path
import re

from .claim_extraction import SUPPORTED_CLAIM_TYPES
from .eval_metrics import (
    average,
    contract_snapshot,
    first_relevant_rank,
    metric_threshold_check,
    ndcg_at_k,
    read_json_payload,
    reciprocal_rank,
)
from .records import aliased_source_record_ids


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


def _load_validated_links_for_eval(links_path: Path) -> list[dict]:
    if not links_path.exists():
        raise FileNotFoundError(f"Missing rule-claim links file: {links_path}")
    links_path = links_path.resolve()
    links_dir = links_path.parent
    summary_path = links_dir / "summary.json"
    validation_path = links_dir / "rule_claim_link_validation.json"
    gaps_path = links_dir / "rule_claim_link_gaps.jsonl"
    missing = [str(path) for path in (summary_path, validation_path, gaps_path) if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing rule-claim link readiness artifact(s): " + ", ".join(missing)
        )
    summary = _read_json(summary_path)
    validation = _read_json(validation_path)
    if not validation.get("passed") or not summary.get("reviewer_ready"):
        raise ValueError(
            f"Rule-claim link artifacts are not reviewer-ready: {links_dir}. "
            "Run rule-claim-link and resolve validation failures before rule-claim-eval."
        )
    current_validation = validate_rule_claim_links(
        output_dir=_output_dir_from_link_summary(links_path, summary),
        source_set_id=str(summary.get("source_set_id") or ""),
        rule_pack_path=Path(str(summary.get("rule_pack_path") or "")),
        claims_path=Path(str(summary.get("claims_path") or "")),
        links_path=links_path,
        gaps_path=gaps_path,
    )
    if not current_validation["passed"]:
        failed = ", ".join(_failed_check_names(current_validation))
        raise ValueError(
            f"Current rule-claim link artifacts failed validation before eval: {failed}"
        )
    return _read_jsonl(links_path)


def _query_links(
    links: list[dict],
    *,
    rule_id: str,
    filters: dict,
    limit: int,
) -> list[dict]:
    filtered = []
    for link in links:
        if rule_id and str(link.get("rule_id") or "") != rule_id:
            continue
        if not _link_matches_eval_filters(link, filters):
            continue
        filtered.append(link)
    filtered.sort(
        key=lambda link: (
            str(link["rule_id"]),
            int(link["rank"]),
            -float(link["score"]),
            str(link["claim_id"]),
        )
    )
    return [_eval_link_result(link) for link in filtered[:limit]]


def _load_eval_contract(path: Path) -> tuple[dict, list[dict], bool]:
    payload = read_json_payload(path, label="rule-claim link eval file")
    if isinstance(payload, list):
        cases = _validated_eval_cases(payload, legacy_format=True)
        return (
            {
                "schema_version": "legacy-rule-claim-link-eval-list-v0",
                "eval_id": f"legacy-{path.stem}",
                "coverage_requirements": {},
                "metric_thresholds": {},
                "cases": cases,
            },
            cases,
            True,
        )
    if payload.get("schema_version") != RULE_CLAIM_LINK_EVAL_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported rule-claim link eval schema_version: "
            f"{payload.get('schema_version')!r}"
        )
    if not str(payload.get("eval_id") or "").strip():
        raise ValueError("Rule-claim link eval contract missing 'eval_id'.")
    if not isinstance(payload.get("coverage_requirements"), dict):
        raise ValueError("Rule-claim link eval contract missing 'coverage_requirements'.")
    if not isinstance(payload.get("metric_thresholds"), dict):
        raise ValueError("Rule-claim link eval contract missing 'metric_thresholds'.")
    _validate_rule_claim_coverage_requirements(payload["coverage_requirements"])
    cases = _validated_eval_cases(payload.get("cases"), legacy_format=False)
    return payload, cases, False


def _validated_eval_cases(payload: object, *, legacy_format: bool) -> list[dict]:
    if not isinstance(payload, list) or not payload:
        raise ValueError(
            "Rule-claim link eval file must contain a non-empty JSON list."
            if legacy_format
            else "Rule-claim link eval contract must contain non-empty cases."
        )
    case_ids = []
    for index, case in enumerate(payload):
        if not isinstance(case, dict):
            raise ValueError(f"Rule-claim link eval case {index} must be an object.")
        for field in ("id", "rule_id"):
            if not case.get(field):
                raise ValueError(f"Rule-claim link eval case {index} is missing {field!r}.")
        case_ids.append(str(case["id"]))
        _validate_eval_filters(index, case)
        _validate_eval_expectations(index, case)
        _validate_positive_eval_int(index, case, "min_links")
        _validate_positive_eval_int(index, case, "top_k")
    duplicates = sorted(case_id for case_id in set(case_ids) if case_ids.count(case_id) > 1)
    if duplicates:
        raise ValueError(f"Duplicate rule-claim link eval case IDs: {duplicates}")
    return payload


def _validate_rule_claim_coverage_requirements(requirements: dict) -> None:
    for key in (
        "case_count",
        "hard_negative_case_count",
        "multi_source_case_count",
    ):
        value = requirements.get(key)
        if not isinstance(value, int) or value < 0:
            raise ValueError(
                "Rule-claim link eval coverage_requirements."
                f"{key} must be a non-negative integer."
            )


def _validate_eval_filters(index: int, case: dict) -> None:
    filters = case.get("filters") or {}
    if not isinstance(filters, dict):
        raise ValueError(f"Rule-claim link eval case {index} filters must be an object.")
    unknown = sorted(set(filters) - SUPPORTED_RULE_CLAIM_EVAL_FILTERS)
    empty = sorted(key for key, value in filters.items() if value in (None, "", []))
    claim_type = filters.get("claim_type")
    if claim_type and claim_type not in SUPPORTED_CLAIM_TYPES:
        raise ValueError(
            f"Rule-claim link eval case {index} has unsupported claim_type filter: {claim_type!r}."
        )
    if unknown or empty:
        details = []
        if unknown:
            details.append(f"unknown filters: {unknown}")
        if empty:
            details.append(f"empty filters: {empty}")
        raise ValueError(
            f"Rule-claim link eval case {index} has unsupported filters; " + "; ".join(details)
        )


def _validate_eval_expectations(index: int, case: dict) -> None:
    expected_claim_types = case.get("expected_claim_types")
    if expected_claim_types is not None:
        if not isinstance(expected_claim_types, list) or not expected_claim_types:
            raise ValueError(
                f"Rule-claim link eval case {index} expected_claim_types must be a non-empty list."
            )
        unsupported = sorted(set(str(value) for value in expected_claim_types) - SUPPORTED_CLAIM_TYPES)
        if unsupported:
            raise ValueError(
                f"Rule-claim link eval case {index} has unsupported expected_claim_types: {unsupported}."
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
            raise ValueError(
                f"Rule-claim link eval case {index} {key} must be a non-empty string list."
            )
    for key in ("expect_no_hits", "hard_negative", "multi_source"):
        if key in case and not isinstance(case[key], bool):
            raise ValueError(f"Rule-claim link eval case {index} {key} must be a boolean.")


def _validate_positive_eval_int(index: int, case: dict, key: str) -> None:
    if key not in case:
        return
    try:
        value = int(case[key])
    except (TypeError, ValueError) as error:
        raise ValueError(f"Rule-claim link eval case {index} {key} must be an integer.") from error
    if value < 1:
        raise ValueError(f"Rule-claim link eval case {index} {key} must be at least 1.")


def _source_set_id_from_links_path(links_path: Path) -> str:
    summary_path = links_path.parent / "summary.json"
    if summary_path.exists():
        source_set_id = _read_json(summary_path).get("source_set_id")
        if source_set_id:
            return str(source_set_id)
    if links_path.parent.parent.parent.name != "rule_claim_links":
        raise ValueError(f"Rule-claim links path must live under rule_claim_links: {links_path}")
    return links_path.parent.parent.parent.parent.name


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


def _link_matches_eval_filters(link: dict, filters: dict) -> bool:
    source_record_id = filters.get("source_record_id")
    if source_record_id and not _source_record_matches_expected_ids(
        str(link.get("source_record_id") or ""),
        [str(source_record_id)],
    ):
        return False
    for key in ("rule_id", "claim_type"):
        value = filters.get(key)
        if value and str(link.get(key) or "").lower() != str(value).lower():
            return False
    return True


def _expected_terms_found(expected_terms: list[str], hits: list[dict]) -> bool:
    haystack = "\n".join(
        " ".join(
            [
                hit.get("claim_text", ""),
                hit.get("citation_label", ""),
                hit.get("rule_requirement", ""),
                " ".join(hit.get("matched_terms", [])),
                " ".join(hit.get("review_topics", [])),
            ]
        )
        for hit in hits
    ).lower()
    token_set = set(_tokenize(haystack))
    return all(
        _expected_term_present(term, token_set=token_set, text=haystack)
        for term in expected_terms
    )


def _link_term_signal(expected_terms: list[str], hit: dict) -> bool:
    if not expected_terms:
        return True
    haystack = " ".join(
        [
            hit.get("claim_text", ""),
            hit.get("citation_label", ""),
            hit.get("rule_requirement", ""),
            " ".join(hit.get("matched_terms", [])),
            " ".join(hit.get("review_topics", [])),
        ]
    ).lower()
    token_set = set(_tokenize(haystack))
    return any(
        _expected_term_present(term, token_set=token_set, text=haystack)
        for term in expected_terms
    )


def _expected_term_present(term: str, *, token_set: set[str], text: str) -> bool:
    normalized_term = str(term or "").strip().lower()
    if not normalized_term:
        return True
    if normalized_term in text:
        return True
    term_tokens = _tokenize(normalized_term)
    if not term_tokens:
        return False
    return all(_contains_term(token, token_set, text) for token in term_tokens)


def _contains_term(term: str, token_set: set[str], text: str) -> bool:
    if term in token_set:
        return True
    if term in text:
        return True
    return any(
        token.startswith(term)
        or term.startswith(token)
        or _common_prefix_length(token, term) >= 5
        for token in token_set
    )


def _common_prefix_length(left: str, right: str) -> int:
    size = 0
    for left_char, right_char in zip(left, right, strict=False):
        if left_char != right_char:
            break
        size += 1
    return size


def _tokenize(value: str) -> list[str]:
    return [
        token.strip("'-.")
        for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]{1,}", value.lower())
        if len(token.strip("'-.") or "") >= 2
    ]


def _link_relevance(
    hits: list[dict],
    *,
    expected_sources: list[str],
    expected_claim_types: list[str],
    expected_terms: list[str],
) -> list[bool]:
    if not (expected_sources or expected_claim_types or expected_terms):
        return [False for _ in hits]
    remaining_sources = list(expected_sources) if expected_sources else None
    relevance = []
    for hit in hits:
        source_record_id = str(hit.get("source_record_id") or "")
        claim_type = str(hit.get("claim_type") or "")
        candidate_expected_sources = (
            remaining_sources if remaining_sources is not None else expected_sources
        )
        matched_source_id = (
            _matching_expected_source_id(source_record_id, candidate_expected_sources)
            if expected_sources and candidate_expected_sources
            else None
        )
        source_ok = not expected_sources or matched_source_id is not None
        type_ok = not expected_claim_types or claim_type in expected_claim_types
        term_ok = not expected_terms or _link_term_signal(expected_terms, hit)
        content_ok = (not expected_claim_types and not expected_terms) or type_ok or term_ok
        is_relevant = source_ok and content_ok
        if is_relevant and remaining_sources is not None:
            is_relevant = matched_source_id is not None
            if matched_source_id is not None:
                remaining_sources.remove(matched_source_id)
        relevance.append(is_relevant)
    return relevance


def _source_matched_hits(hits: list[dict], expected_sources: list[str]) -> list[dict]:
    if not expected_sources:
        return hits
    return [
        hit
        for hit in hits
        if _source_record_matches_expected_ids(
            str(hit.get("source_record_id") or ""),
            expected_sources,
        )
    ]


def _matched_expected_source_record_ids(expected_sources: list[str], hits: list[dict]) -> list[str]:
    return [
        source_id
        for source_id in expected_sources
        if any(
            _source_record_matches_expected_ids(
                str(hit.get("source_record_id") or ""),
                [source_id],
            )
            for hit in hits
        )
    ]


def _matching_expected_source_id(
    source_record_id: str,
    expected_sources: list[str],
) -> str | None:
    actual_aliases = _source_record_id_aliases(source_record_id)
    for expected_source_id in expected_sources:
        if actual_aliases & _source_record_id_aliases(expected_source_id):
            return expected_source_id
    return None


def _source_record_matches_expected_ids(
    source_record_id: str,
    expected_sources: list[str],
) -> bool:
    return _matching_expected_source_id(source_record_id, expected_sources) is not None


def _source_record_id_aliases(source_record_id: str) -> set[str]:
    return set(aliased_source_record_ids([source_record_id]))


def _link_has_required_provenance(link: dict) -> bool:
    return all(
        link.get(field) not in (None, "")
        for field in (
            "source_set_id",
            "rule_pack_id",
            "rule_pack_version",
            "rule_id",
            "claim_id",
            "citation_label",
            "artifact_sha256",
            "artifact_path",
            "parser_name",
            "parser_version",
            "source_char_start",
            "source_char_end",
            "content_sha256",
        )
    )


def _eval_link_result(link: dict) -> dict:
    return {
        "link_id": link["link_id"],
        "source_set_id": link["source_set_id"],
        "rule_id": link["rule_id"],
        "rule_pack_id": link["rule_pack_id"],
        "rule_pack_version": link["rule_pack_version"],
        "rule_requirement": link.get("rule_requirement"),
        "rank": link["rank"],
        "score": link["score"],
        "matched_terms": link.get("matched_terms", []),
        "claim_id": link["claim_id"],
        "claim_type": link["claim_type"],
        "claim_text": link["claim_text"],
        "source_record_id": link["source_record_id"],
        "chunk_id": link["chunk_id"],
        "citation_label": link["citation_label"],
        "authority_level": link["authority_level"],
        "document_role": link["document_role"],
        "review_topics": link.get("review_topics", []),
        "artifact_sha256": link["artifact_sha256"],
        "artifact_path": link["artifact_path"],
        "parser_name": link["parser_name"],
        "parser_version": link["parser_version"],
        "source_text_path": link.get("source_text_path"),
        "source_char_start": link["source_char_start"],
        "source_char_end": link["source_char_end"],
        "chunk_char_start": link["chunk_char_start"],
        "chunk_char_end": link["chunk_char_end"],
        "content_sha256": link["content_sha256"],
    }


def _eval_failure_reasons(
    *,
    expect_no_hits: bool,
    min_links_met: bool,
    type_hit: bool,
    source_hit: bool,
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
    if not min_links_met:
        reasons.append("min_links_not_met")
    if not type_hit:
        reasons.append("expected_claim_type_not_linked")
    if not source_hit:
        reasons.append("expected_source_not_linked")
    if not term_hit:
        reasons.append("expected_terms_not_linked")
    if not provenance_supported:
        reasons.append("citation_provenance_missing")
    if top_rank_false_positive:
        reasons.append("top_rank_not_relevant")
    if unexpected_sources:
        reasons.append("forbidden_source_linked")
    if unexpected_claim_types:
        reasons.append("forbidden_claim_type_linked")
    return reasons


def _rule_claim_coverage_check(
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
