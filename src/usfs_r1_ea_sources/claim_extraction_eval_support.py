from __future__ import annotations

from importlib import import_module
from pathlib import Path
import re

from .eval_metrics import read_json_payload
from .records import aliased_source_record_ids


_CLAIM_EXTRACTION = import_module("usfs_r1_ea_sources.claim_extraction")
CLAIM_EVAL_SCHEMA_VERSION = _CLAIM_EXTRACTION.CLAIM_EVAL_SCHEMA_VERSION
SUPPORTED_CLAIM_EVAL_FILTERS = _CLAIM_EXTRACTION.SUPPORTED_CLAIM_EVAL_FILTERS
SUPPORTED_CLAIM_TYPES = _CLAIM_EXTRACTION.SUPPORTED_CLAIM_TYPES
validate_claim_outputs = _CLAIM_EXTRACTION.validate_claim_outputs
_read_json = _CLAIM_EXTRACTION._read_json
_read_jsonl = _CLAIM_EXTRACTION._read_jsonl


def _query_claims(
    claims: list[dict],
    *,
    query: str,
    filters: dict,
    limit: int,
) -> list[dict]:
    terms = _tokenize(query)
    phrases = _query_phrases(query)
    scored = []
    for claim in claims:
        if not _claim_matches_filters(claim, filters):
            continue
        score = _score_claim(claim, terms=terms, phrases=phrases, query=query)
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
    if (
        claims_dir.name not in {"claims", "claims_sidecar"}
        or source_dir.name != source_set_id
        or derived_dir.name != "derived"
    ):
        raise ValueError(
            "Claims path must be under source_library/derived/<source_set_id>/claims/ "
            "or source_library/derived/<source_set_id>/claims_sidecar/."
        )
    return derived_dir.parent

def _claim_matches_filters(claim: dict, filters: dict) -> bool:
    source_record_id = filters.get("source_record_id")
    if source_record_id and not _source_record_matches_expected_ids(
        str(claim.get("source_record_id") or ""),
        [str(source_record_id)],
    ):
        return False
    for key in ("claim_type", "document_role", "authority_level", "citation_label"):
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

def _score_claim(claim: dict, *, terms: list[str], phrases: list[str], query: str) -> float:
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
    score += 0.35 * _phrase_hit_fraction(phrases, text=text)
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
    return not _missing_expected_terms(expected_terms, hits)


def _missing_expected_terms(expected_terms: list[str], hits: list[dict]) -> list[str]:
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
    token_set = set(_tokenize(haystack))
    return [
        term
        for term in expected_terms
        if not _expected_term_present(term, token_set=token_set, text=haystack)
    ]


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
    token_set = set(_tokenize(haystack))
    return all(
        _expected_term_present(term, token_set=token_set, text=haystack)
        for term in expected_terms
    )


def _claim_term_signal(expected_terms: list[str], hit: dict) -> bool:
    if not expected_terms:
        return True
    haystack = " ".join(
        [
            hit.get("claim_text", ""),
            hit.get("citation_label", ""),
            " ".join(hit.get("review_topics", [])),
        ]
    ).lower()
    token_set = set(_tokenize(haystack))
    return any(
        _expected_term_present(term, token_set=token_set, text=haystack)
        for term in expected_terms
    )


def _claim_relevance(
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
        term_ok = not expected_terms or _claim_term_signal(expected_terms, hit)
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
    return any(
        token.startswith(term)
        or term.startswith(token)
        or _common_prefix_length(token, term) >= 5
        for token in token_set
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


def _common_prefix_length(left: str, right: str) -> int:
    size = 0
    for left_char, right_char in zip(left, right, strict=False):
        if left_char != right_char:
            break
        size += 1
    return size


def _phrase_hit_fraction(phrases: list[str], *, text: str) -> float:
    if not phrases:
        return 0.0
    lower = text.lower()
    if not lower:
        return 0.0
    match_scores = [
        min(1.0, len(_tokenize(phrase)) / 4.0)
        for phrase in phrases
        if phrase in lower
    ]
    return max(match_scores, default=0.0)


def _query_phrases(query: str) -> list[str]:
    raw_tokens = _tokenize(query)
    phrases: list[str] = []
    seen = set()
    max_size = min(4, len(raw_tokens))
    for size in range(max_size, 1, -1):
        for start in range(0, len(raw_tokens) - size + 1):
            phrase = " ".join(raw_tokens[start : start + size]).strip()
            if phrase and phrase not in seen:
                seen.add(phrase)
                phrases.append(phrase)
    return phrases


def _tokenize(value: str) -> list[str]:
    return [
        token.strip("'-.")
        for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]{1,}", value.lower())
        if len(token.strip("'-.") or "") >= 2
    ]
