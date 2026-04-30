from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse
import hashlib
import json
import re
import sqlite3

from .claim_extraction import SUPPORTED_CLAIM_TYPES
from .claim_extraction import _load_validated_claims_for_eval
from .claim_extraction import _source_set_id_from_catalog
from .claim_extraction import default_claims_path
from .compliance_review import DEFAULT_RULE_PACK_PATH
from .compliance_review import load_rule_pack
from .compliance_review import validate_rule_pack
from .extract import _source_derived_dir


RULE_CLAIM_LINK_SCHEMA_VERSION = "rule-claim-links-v0"
RULE_CLAIM_GAP_SCHEMA_VERSION = "rule-claim-link-gaps-v0"
RULE_CLAIM_LINK_VALIDATION_SCHEMA_VERSION = "rule-claim-link-validation-v0"
RULE_CLAIM_LINK_EVAL_SCHEMA_VERSION = "rule-claim-link-eval-v0"
DEFAULT_RULE_CLAIM_EVAL_PATH = Path("config/rule_claim_link_eval_seed.json")
DEFAULT_TOP_K = 5
SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
SUPPORTED_RULE_CLAIM_EVAL_FILTERS = {"rule_id", "claim_type", "source_record_id"}
REQUIRED_LINK_FIELDS = {
    "artifact_path",
    "artifact_sha256",
    "authority_level",
    "chunk_char_end",
    "chunk_char_start",
    "chunk_id",
    "citation_label",
    "claim_id",
    "claim_text",
    "claim_type",
    "content_sha256",
    "document_role",
    "link_id",
    "matched_terms",
    "parser_name",
    "parser_version",
    "rank",
    "rule_id",
    "rule_pack_id",
    "rule_pack_version",
    "rule_query",
    "rule_source_filters",
    "schema_version",
    "score",
    "source_char_end",
    "source_char_start",
    "source_record_id",
    "source_set_id",
    "validation_status",
}
REQUIRED_GAP_FIELDS = {
    "gap_id",
    "reason",
    "rule_id",
    "rule_pack_id",
    "rule_pack_version",
    "rule_query",
    "rule_source_filters",
    "schema_version",
    "source_set_id",
    "validation_status",
}
STOPWORDS = {
    "and",
    "are",
    "for",
    "from",
    "has",
    "have",
    "into",
    "its",
    "not",
    "of",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "under",
    "when",
    "where",
    "with",
}


@dataclass(frozen=True)
class RuleClaimLinkResult:
    source_set_id: str
    links_dir: Path
    links_path: Path
    gaps_path: Path
    sqlite_path: Path
    validation_path: Path
    summary_path: Path
    summary: dict


@dataclass(frozen=True)
class RuleClaimLinkEvalResult:
    links_path: Path
    eval_file: Path
    output_path: Path
    summary: dict


def build_rule_claim_links(
    *,
    output_dir: Path,
    rule_pack_path: Path = DEFAULT_RULE_PACK_PATH,
    source_set_id: str | None = None,
    claims_path: Path | None = None,
    top_k: int = DEFAULT_TOP_K,
) -> RuleClaimLinkResult:
    """Build deterministic links from compliance rules to validated source claims."""

    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    output_dir = Path(output_dir)
    if source_set_id is None:
        source_set_id = _source_set_id_from_catalog(output_dir)
    rule_pack_path = Path(rule_pack_path)
    if not rule_pack_path.exists():
        raise FileNotFoundError(f"Missing compliance rule pack: {rule_pack_path}")
    rule_pack = load_rule_pack(rule_pack_path)
    rule_pack_validation = validate_rule_pack(rule_pack)
    if not rule_pack_validation["passed"]:
        failed = ", ".join(_failed_check_names(rule_pack_validation))
        raise ValueError(f"Compliance rule pack is invalid. Failed checks: {failed}")

    claims_path = claims_path or default_claims_path(output_dir, source_set_id)
    claims = _load_validated_claims_for_eval(claims_path)
    links_dir = default_rule_claim_links_dir(
        output_dir,
        source_set_id=source_set_id,
        rule_pack=rule_pack,
    )
    links_dir.mkdir(parents=True, exist_ok=True)
    links_path = links_dir / "rule_claim_links.jsonl"
    gaps_path = links_dir / "rule_claim_link_gaps.jsonl"
    sqlite_path = links_dir / "rule_claim_links.sqlite"
    validation_path = links_dir / "rule_claim_link_validation.json"
    summary_path = links_dir / "summary.json"

    created_at = _utc_now()
    links, gaps = _build_links(
        source_set_id=source_set_id,
        rule_pack=rule_pack,
        claims=claims,
        top_k=top_k,
        created_at=created_at,
    )
    _write_jsonl(links_path, links)
    _write_jsonl(gaps_path, gaps)
    validation = validate_rule_claim_links(
        output_dir=output_dir,
        source_set_id=source_set_id,
        rule_pack_path=rule_pack_path,
        claims_path=claims_path,
        links_path=links_path,
        gaps_path=gaps_path,
    )
    if validation["passed"]:
        _write_sqlite_links(
            sqlite_path,
            source_set_id=source_set_id,
            rule_pack=rule_pack,
            links=links,
            gaps=gaps,
        )
        validation = _with_additional_checks(
            validation,
            _sqlite_link_checks(
                sqlite_path,
                expected_link_count=len(links),
                expected_gap_count=len(gaps),
            ),
        )
        if not validation["passed"]:
            sqlite_path.unlink(missing_ok=True)
    else:
        sqlite_path.unlink(missing_ok=True)

    rule_ids = [str(rule["id"]) for rule in rule_pack["rules"]]
    linked_rule_ids = sorted({str(link["rule_id"]) for link in links})
    gap_rule_ids = sorted({str(gap["rule_id"]) for gap in gaps})
    link_counts_by_rule = Counter(str(link["rule_id"]) for link in links)
    summary = {
        "schema_version": RULE_CLAIM_LINK_SCHEMA_VERSION,
        "source_set_id": source_set_id,
        "created_at": created_at,
        "links_dir": str(links_dir),
        "links_path": str(links_path),
        "gaps_path": str(gaps_path),
        "sqlite_path": str(sqlite_path),
        "validation_path": str(validation_path),
        "summary_path": str(summary_path),
        "claims_path": str(claims_path),
        "rule_pack_path": str(rule_pack_path),
        "rule_pack_id": rule_pack["rule_pack_id"],
        "rule_pack_version": rule_pack["version"],
        "top_k": top_k,
        "rule_count": len(rule_ids),
        "claim_count": len(claims),
        "link_count": len(links),
        "gap_count": len(gaps),
        "linked_rule_count": len(linked_rule_ids),
        "gap_rule_count": len(gap_rule_ids),
        "rules_without_links": gap_rule_ids,
        "links_per_rule": {rule_id: link_counts_by_rule.get(rule_id, 0) for rule_id in rule_ids},
        "claim_type_counts": dict(Counter(link["claim_type"] for link in links)),
        "source_record_count": len({link["source_record_id"] for link in links}),
        "validation_passed": validation["passed"],
        "reviewer_ready": validation["passed"],
    }
    _write_json(validation_path, validation)
    _write_json(summary_path, summary)
    return RuleClaimLinkResult(
        source_set_id=source_set_id,
        links_dir=links_dir,
        links_path=links_path,
        gaps_path=gaps_path,
        sqlite_path=sqlite_path,
        validation_path=validation_path,
        summary_path=summary_path,
        summary=summary,
    )


def validate_rule_claim_links(
    *,
    output_dir: Path,
    source_set_id: str,
    rule_pack_path: Path,
    claims_path: Path,
    links_path: Path,
    gaps_path: Path,
) -> dict:
    output_dir = Path(output_dir)
    rule_pack_path = Path(rule_pack_path)
    claims_path = Path(claims_path)
    links_path = Path(links_path)
    gaps_path = Path(gaps_path)

    rule_pack = load_rule_pack(rule_pack_path) if rule_pack_path.exists() else {}
    rule_pack_validation = validate_rule_pack(rule_pack) if rule_pack else {"passed": False, "checks": []}
    claims, claim_error = _load_claims_for_validation(claims_path)
    links = _read_jsonl(links_path) if links_path.exists() else []
    gaps = _read_jsonl(gaps_path) if gaps_path.exists() else []
    checks = [
        {
            "name": "rule_pack_valid",
            "passed": bool(rule_pack_validation.get("passed")),
            "details": {
                "path": str(rule_pack_path),
                "exists": rule_pack_path.exists(),
                "failed_checks": _failed_check_names(rule_pack_validation),
            },
        },
        {
            "name": "claims_are_reviewer_ready",
            "passed": claim_error is None and bool(claims),
            "details": {
                "path": str(claims_path),
                "exists": claims_path.exists(),
                "claim_count": len(claims),
                "error": claim_error,
            },
        },
        {
            "name": "rule_claim_link_files_exist",
            "passed": links_path.exists() and gaps_path.exists(),
            "details": {"links_path": str(links_path), "gaps_path": str(gaps_path)},
        },
        _check_links_loaded(links, gaps),
        _check_required_link_fields(links),
        _check_required_gap_fields(gaps),
        _check_unique_ids(links, key="link_id", check_name="rule_claim_link_ids_are_unique"),
        _check_unique_ids(gaps, key="gap_id", check_name="rule_claim_gap_ids_are_unique"),
        _check_link_rule_pack_fields(source_set_id, rule_pack, links, gaps),
        _check_link_and_gap_identities(source_set_id, rule_pack, links, gaps),
        _check_rule_coverage(rule_pack, links, gaps),
        _check_gap_records(rule_pack, links, gaps),
        _check_links_resolve_to_claims(claims, links),
        _check_link_claim_fields_match_claims(claims, links),
        _check_links_match_rule_filters(rule_pack, links),
        _check_link_scores_and_terms(rule_pack, links),
        _check_link_ranks_are_contiguous(links),
    ]
    return {
        "schema_version": RULE_CLAIM_LINK_VALIDATION_SCHEMA_VERSION,
        "source_set_id": source_set_id,
        "created_at": _utc_now(),
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


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
    cases = _load_eval_cases(eval_file)
    output_dir = output_dir or links_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "rule_claim_link_eval_results.json"

    case_results = []
    for case in cases:
        filters = dict(case.get("filters") or {})
        rule_id = str(case.get("rule_id") or filters.get("rule_id") or "")
        expected_terms = [str(value) for value in case.get("expected_terms", [])]
        expected_claim_types = [str(value) for value in case.get("expected_claim_types", [])]
        expected_sources = [str(value) for value in case.get("expected_source_record_ids", [])]
        min_links = int(case.get("min_links", 1))
        hits = _query_links(
            links,
            rule_id=rule_id,
            filters=filters,
            limit=int(case.get("top_k") or top_k),
        )
        min_links_met = len(hits) >= min_links
        type_hit = not expected_claim_types or any(
            hit["claim_type"] in expected_claim_types for hit in hits
        )
        source_hit = not expected_sources or any(
            hit["source_record_id"] in expected_sources for hit in hits
        )
        term_hit = not expected_terms or _expected_terms_found(expected_terms, hits)
        provenance_supported = bool(hits) and any(_link_has_required_provenance(hit) for hit in hits)
        passed = min_links_met and type_hit and source_hit and term_hit and provenance_supported
        case_results.append(
            {
                "id": case["id"],
                "rule_id": rule_id,
                "filters": filters,
                "expected_terms": expected_terms,
                "expected_claim_types": expected_claim_types,
                "expected_source_record_ids": expected_sources,
                "top_k": int(case.get("top_k") or top_k),
                "hit_count": len(hits),
                "top_link_ids": [hit["link_id"] for hit in hits],
                "top_claim_ids": [hit["claim_id"] for hit in hits],
                "top_source_record_ids": [hit["source_record_id"] for hit in hits],
                "min_links_met": min_links_met,
                "type_hit": type_hit,
                "source_hit": source_hit,
                "term_hit": term_hit,
                "provenance_supported": provenance_supported,
                "failure_reasons": _eval_failure_reasons(
                    min_links_met=min_links_met,
                    type_hit=type_hit,
                    source_hit=source_hit,
                    term_hit=term_hit,
                    provenance_supported=provenance_supported,
                ),
                "passed": passed,
                "top_results": hits,
            }
        )

    case_count = len(case_results)
    passed_count = sum(1 for case in case_results if case["passed"])
    summary = {
        "schema_version": RULE_CLAIM_LINK_EVAL_SCHEMA_VERSION,
        "links_path": str(links_path),
        "eval_file": str(eval_file),
        "created_at": _utc_now(),
        "top_k": top_k,
        "case_count": case_count,
        "passed_count": passed_count,
        "failed_count": case_count - passed_count,
        "passed": passed_count == case_count,
        "metrics": {
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
        },
        "cases": case_results,
    }
    _write_json(output_path, summary)
    return RuleClaimLinkEvalResult(
        links_path=links_path,
        eval_file=eval_file,
        output_path=output_path,
        summary=summary,
    )


def default_rule_claim_links_dir(
    output_dir: Path,
    *,
    source_set_id: str | None = None,
    rule_pack: dict | None = None,
    rule_pack_path: Path = DEFAULT_RULE_PACK_PATH,
) -> Path:
    output_dir = Path(output_dir)
    if source_set_id is None:
        source_set_id = _source_set_id_from_catalog(output_dir)
    if rule_pack is None:
        rule_pack = load_rule_pack(rule_pack_path)
    return (
        _source_derived_dir(output_dir / "derived", source_set_id)
        / "rule_claim_links"
        / _safe_segment(str(rule_pack["rule_pack_id"]))
        / _safe_segment(str(rule_pack["version"]))
    )


def default_rule_claim_links_path(
    output_dir: Path,
    *,
    source_set_id: str | None = None,
    rule_pack_path: Path = DEFAULT_RULE_PACK_PATH,
) -> Path:
    return default_rule_claim_links_dir(
        output_dir,
        source_set_id=source_set_id,
        rule_pack_path=rule_pack_path,
    ) / "rule_claim_links.jsonl"


def links_by_rule(links: list[dict], *, limit: int | None = None) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for link in sorted(
        links,
        key=lambda item: (
            str(item.get("rule_id") or ""),
            int(item.get("rank") or 0),
            -float(item.get("score") or 0),
        ),
    ):
        rule_id = str(link.get("rule_id") or "")
        if limit is None or len(grouped[rule_id]) < limit:
            grouped[rule_id].append(link)
    return dict(grouped)


def _build_links(
    *,
    source_set_id: str,
    rule_pack: dict,
    claims: list[dict],
    top_k: int,
    created_at: str,
) -> tuple[list[dict], list[dict]]:
    links = []
    gaps = []
    for rule in rule_pack["rules"]:
        scored = []
        query = _rule_query(rule)
        terms = _tokenize(query)
        for claim in claims:
            if not _claim_matches_rule_filters(claim, rule.get("source_filters") or {}):
                continue
            score, matched_terms = _score_rule_claim(rule, claim, terms=terms, query=query)
            if terms and score <= 0:
                continue
            scored.append((score, matched_terms, claim))
        scored.sort(
            key=lambda item: (
                -item[0],
                str(item[2]["source_record_id"]),
                int(item[2]["source_char_start"]),
                str(item[2]["claim_id"]),
            )
        )
        selected = scored[:top_k]
        if not selected:
            gaps.append(
                _gap_record(
                    source_set_id=source_set_id,
                    rule_pack=rule_pack,
                    rule=rule,
                    created_at=created_at,
                    reason="no_validated_source_claim_match",
                )
            )
            continue
        for rank, (score, matched_terms, claim) in enumerate(selected, start=1):
            links.append(
                _link_record(
                    source_set_id=source_set_id,
                    rule_pack=rule_pack,
                    rule=rule,
                    claim=claim,
                    rank=rank,
                    score=score,
                    matched_terms=matched_terms,
                    created_at=created_at,
                )
            )
    return links, gaps


def _link_record(
    *,
    source_set_id: str,
    rule_pack: dict,
    rule: dict,
    claim: dict,
    rank: int,
    score: float,
    matched_terms: list[str],
    created_at: str,
) -> dict:
    rule_id = str(rule["id"])
    claim_id = str(claim["claim_id"])
    link_id = _link_id(
        source_set_id=source_set_id,
        rule_pack_id=str(rule_pack["rule_pack_id"]),
        rule_pack_version=str(rule_pack["version"]),
        rule_id=rule_id,
        claim_id=claim_id,
    )
    return {
        "schema_version": RULE_CLAIM_LINK_SCHEMA_VERSION,
        "link_id": link_id,
        "source_set_id": source_set_id,
        "rule_pack_id": rule_pack["rule_pack_id"],
        "rule_pack_version": rule_pack["version"],
        "rule_id": rule_id,
        "rule_title": rule["title"],
        "rule_query": _rule_query(rule),
        "rule_requirement": rule.get("requirement"),
        "rule_source_filters": rule.get("source_filters", {}),
        "rank": rank,
        "score": round(score, 6),
        "matched_terms": matched_terms,
        "claim_id": claim_id,
        "claim_type": claim["claim_type"],
        "claim_text": claim["claim_text"],
        "source_record_id": claim["source_record_id"],
        "chunk_id": claim["chunk_id"],
        "citation_label": claim["citation_label"],
        "authority_level": claim["authority_level"],
        "document_role": claim["document_role"],
        "review_topics": claim.get("review_topics", []),
        "title": claim.get("title"),
        "artifact_sha256": claim["artifact_sha256"],
        "artifact_path": claim["artifact_path"],
        "original_url": claim.get("original_url"),
        "effective_url": claim.get("effective_url"),
        "final_url": claim.get("final_url"),
        "parser_name": claim["parser_name"],
        "parser_version": claim["parser_version"],
        "source_text_path": claim.get("source_text_path"),
        "source_char_start": claim["source_char_start"],
        "source_char_end": claim["source_char_end"],
        "chunk_char_start": claim["chunk_char_start"],
        "chunk_char_end": claim["chunk_char_end"],
        "content_sha256": claim["content_sha256"],
        "chunk_content_sha256": claim.get("chunk_content_sha256"),
        "claim_validation_status": claim["validation_status"],
        "validation_status": "valid",
        "created_at": created_at,
    }


def _gap_record(
    *,
    source_set_id: str,
    rule_pack: dict,
    rule: dict,
    created_at: str,
    reason: str,
) -> dict:
    return {
        "schema_version": RULE_CLAIM_GAP_SCHEMA_VERSION,
        "gap_id": _gap_id(
            source_set_id=source_set_id,
            rule_pack_id=str(rule_pack["rule_pack_id"]),
            rule_pack_version=str(rule_pack["version"]),
            rule_id=str(rule["id"]),
            reason=reason,
        ),
        "source_set_id": source_set_id,
        "rule_pack_id": rule_pack["rule_pack_id"],
        "rule_pack_version": rule_pack["version"],
        "rule_id": rule["id"],
        "rule_title": rule["title"],
        "rule_query": _rule_query(rule),
        "rule_requirement": rule.get("requirement"),
        "rule_source_filters": rule.get("source_filters", {}),
        "reason": reason,
        "validation_status": "explicit_no_claim_gap",
        "created_at": created_at,
    }


def _check_links_loaded(links: list[dict], gaps: list[dict]) -> dict:
    return {
        "name": "rule_claim_links_or_gaps_loaded",
        "passed": bool(links or gaps),
        "details": {"link_count": len(links), "gap_count": len(gaps)},
    }


def _check_required_link_fields(links: list[dict]) -> dict:
    failures = []
    for link in links:
        missing = sorted(field for field in REQUIRED_LINK_FIELDS if link.get(field) in (None, ""))
        if missing:
            failures.append({"link_id": link.get("link_id"), "missing_fields": missing})
        if link.get("schema_version") != RULE_CLAIM_LINK_SCHEMA_VERSION:
            failures.append(
                {
                    "link_id": link.get("link_id"),
                    "field": "schema_version",
                    "expected": RULE_CLAIM_LINK_SCHEMA_VERSION,
                    "actual": link.get("schema_version"),
                }
            )
    return {
        "name": "rule_claim_links_have_required_fields",
        "passed": not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_required_gap_fields(gaps: list[dict]) -> dict:
    failures = []
    for gap in gaps:
        missing = sorted(field for field in REQUIRED_GAP_FIELDS if gap.get(field) in (None, ""))
        if missing:
            failures.append({"gap_id": gap.get("gap_id"), "missing_fields": missing})
        if gap.get("schema_version") != RULE_CLAIM_GAP_SCHEMA_VERSION:
            failures.append(
                {
                    "gap_id": gap.get("gap_id"),
                    "field": "schema_version",
                    "expected": RULE_CLAIM_GAP_SCHEMA_VERSION,
                    "actual": gap.get("schema_version"),
                }
            )
    return {
        "name": "rule_claim_gaps_have_required_fields",
        "passed": not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_unique_ids(records: list[dict], *, key: str, check_name: str) -> dict:
    counts = Counter(record.get(key) for record in records)
    duplicates = sorted(record_id for record_id, count in counts.items() if record_id and count > 1)
    return {
        "name": check_name,
        "passed": not duplicates,
        "details": {"duplicate_ids": duplicates[:50], "duplicate_count": len(duplicates)},
    }


def _check_link_rule_pack_fields(
    source_set_id: str,
    rule_pack: dict,
    links: list[dict],
    gaps: list[dict],
) -> dict:
    expected_pack_id = str(rule_pack.get("rule_pack_id") or "")
    expected_version = str(rule_pack.get("version") or "")
    failures = []
    for record in [*links, *gaps]:
        for field, expected in (
            ("source_set_id", source_set_id),
            ("rule_pack_id", expected_pack_id),
            ("rule_pack_version", expected_version),
        ):
            if str(record.get(field) or "") != expected:
                failures.append(
                    {
                        "id": record.get("link_id") or record.get("gap_id"),
                        "field": field,
                        "expected": expected,
                        "actual": record.get(field),
                    }
                )
    return {
        "name": "rule_claim_records_match_requested_scope",
        "passed": not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_link_and_gap_identities(
    source_set_id: str,
    rule_pack: dict,
    links: list[dict],
    gaps: list[dict],
) -> dict:
    rules_by_id = {str(rule["id"]): rule for rule in rule_pack.get("rules", [])}
    failures = []
    for link in links:
        rule_id = str(link.get("rule_id") or "")
        rule = rules_by_id.get(rule_id)
        expected_link_id = _link_id(
            source_set_id=source_set_id,
            rule_pack_id=str(rule_pack.get("rule_pack_id") or ""),
            rule_pack_version=str(rule_pack.get("version") or ""),
            rule_id=rule_id,
            claim_id=str(link.get("claim_id") or ""),
        )
        if link.get("link_id") != expected_link_id:
            failures.append(
                {
                    "id": link.get("link_id"),
                    "field": "link_id",
                    "expected": expected_link_id,
                    "actual": link.get("link_id"),
                }
            )
        if rule and not _rule_metadata_matches_record(rule, link):
            failures.append(
                {
                    "id": link.get("link_id"),
                    "field": "rule_metadata",
                    "expected_rule_id": rule_id,
                }
            )
    for gap in gaps:
        rule_id = str(gap.get("rule_id") or "")
        rule = rules_by_id.get(rule_id)
        expected_gap_id = _gap_id(
            source_set_id=source_set_id,
            rule_pack_id=str(rule_pack.get("rule_pack_id") or ""),
            rule_pack_version=str(rule_pack.get("version") or ""),
            rule_id=rule_id,
            reason=str(gap.get("reason") or ""),
        )
        if gap.get("gap_id") != expected_gap_id:
            failures.append(
                {
                    "id": gap.get("gap_id"),
                    "field": "gap_id",
                    "expected": expected_gap_id,
                    "actual": gap.get("gap_id"),
                }
            )
        if rule and not _rule_metadata_matches_record(rule, gap):
            failures.append(
                {
                    "id": gap.get("gap_id"),
                    "field": "rule_metadata",
                    "expected_rule_id": rule_id,
                }
            )
    return {
        "name": "rule_claim_record_identities_are_deterministic",
        "passed": not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _rule_metadata_matches_record(rule: dict, record: dict) -> bool:
    return (
        record.get("rule_title") == rule.get("title")
        and record.get("rule_query") == _rule_query(rule)
        and record.get("rule_requirement") == rule.get("requirement")
        and record.get("rule_source_filters") == (rule.get("source_filters") or {})
    )


def _check_rule_coverage(rule_pack: dict, links: list[dict], gaps: list[dict]) -> dict:
    expected = {str(rule["id"]) for rule in rule_pack.get("rules", [])}
    linked = {str(link.get("rule_id") or "") for link in links}
    gapped = {str(gap.get("rule_id") or "") for gap in gaps}
    actual = linked | gapped
    return {
        "name": "all_rules_have_claim_link_or_explicit_gap",
        "passed": expected == actual and bool(expected),
        "details": {
            "missing_rule_ids": sorted(expected - actual),
            "unexpected_rule_ids": sorted(actual - expected),
            "linked_rule_ids": sorted(linked & expected),
            "gap_rule_ids": sorted(gapped & expected),
        },
    }


def _check_gap_records(rule_pack: dict, links: list[dict], gaps: list[dict]) -> dict:
    rule_ids = {str(rule["id"]) for rule in rule_pack.get("rules", [])}
    linked = {str(link.get("rule_id") or "") for link in links}
    failures = []
    for gap in gaps:
        rule_id = str(gap.get("rule_id") or "")
        if rule_id not in rule_ids:
            failures.append({"gap_id": gap.get("gap_id"), "reason": "unknown_rule"})
        if rule_id in linked:
            failures.append({"gap_id": gap.get("gap_id"), "reason": "linked_rule_has_gap"})
        if gap.get("validation_status") != "explicit_no_claim_gap":
            failures.append({"gap_id": gap.get("gap_id"), "reason": "invalid_status"})
        if gap.get("reason") != "no_validated_source_claim_match":
            failures.append({"gap_id": gap.get("gap_id"), "reason": "unsupported_gap_reason"})
    return {
        "name": "rule_claim_gap_records_are_explicit",
        "passed": not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_links_resolve_to_claims(claims: list[dict], links: list[dict]) -> dict:
    claim_ids = {str(claim.get("claim_id")) for claim in claims}
    failures = [
        {"link_id": link.get("link_id"), "claim_id": link.get("claim_id")}
        for link in links
        if str(link.get("claim_id") or "") not in claim_ids
    ]
    return {
        "name": "rule_claim_links_resolve_to_current_claims",
        "passed": not failures and bool(claims),
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_link_claim_fields_match_claims(claims: list[dict], links: list[dict]) -> dict:
    claims_by_id = {str(claim.get("claim_id")): claim for claim in claims}
    fields = (
        "claim_type",
        "claim_text",
        "source_record_id",
        "chunk_id",
        "citation_label",
        "authority_level",
        "document_role",
        "artifact_sha256",
        "artifact_path",
        "parser_name",
        "parser_version",
        "source_char_start",
        "source_char_end",
        "chunk_char_start",
        "chunk_char_end",
        "content_sha256",
    )
    failures = []
    for link in links:
        claim = claims_by_id.get(str(link.get("claim_id") or ""))
        if not claim:
            continue
        for field in fields:
            if str(link.get(field) or "") != str(claim.get(field) or ""):
                failures.append(
                    {
                        "link_id": link.get("link_id"),
                        "claim_id": link.get("claim_id"),
                        "field": field,
                        "expected": claim.get(field),
                        "actual": link.get(field),
                    }
                )
        if link.get("validation_status") != "valid" or claim.get("validation_status") != "valid":
            failures.append(
                {
                    "link_id": link.get("link_id"),
                    "claim_id": link.get("claim_id"),
                    "field": "validation_status",
                    "expected": "valid",
                    "actual": link.get("validation_status"),
                }
            )
    return {
        "name": "rule_claim_link_provenance_matches_claims",
        "passed": not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_links_match_rule_filters(rule_pack: dict, links: list[dict]) -> dict:
    rules_by_id = {str(rule["id"]): rule for rule in rule_pack.get("rules", [])}
    failures = []
    for link in links:
        rule = rules_by_id.get(str(link.get("rule_id") or ""))
        if not rule:
            failures.append({"link_id": link.get("link_id"), "reason": "unknown_rule"})
            continue
        if not _claim_matches_rule_filters(link, rule.get("source_filters") or {}):
            failures.append({"link_id": link.get("link_id"), "reason": "filter_mismatch"})
    return {
        "name": "rule_claim_links_match_rule_filters",
        "passed": not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_link_scores_and_terms(rule_pack: dict, links: list[dict]) -> dict:
    rules_by_id = {str(rule["id"]): rule for rule in rule_pack.get("rules", [])}
    failures = []
    for link in links:
        rule = rules_by_id.get(str(link.get("rule_id") or ""))
        terms = _tokenize(_rule_query(rule or {}))
        expected_score = None
        expected_terms = []
        if rule:
            expected_score, expected_terms = _score_rule_claim(rule, link, terms=terms, query=_rule_query(rule))
            expected_score = round(expected_score, 6)
        try:
            score = float(link.get("score"))
            rank = int(link.get("rank"))
        except (TypeError, ValueError):
            failures.append({"link_id": link.get("link_id"), "reason": "invalid_score_or_rank"})
            continue
        if score <= 0 or rank < 1:
            failures.append({"link_id": link.get("link_id"), "reason": "non_positive_score_or_rank"})
        if terms and not link.get("matched_terms"):
            failures.append({"link_id": link.get("link_id"), "reason": "missing_matched_terms"})
        if expected_score is not None and round(score, 6) != expected_score:
            failures.append(
                {
                    "link_id": link.get("link_id"),
                    "reason": "score_mismatch",
                    "expected": expected_score,
                    "actual": round(score, 6),
                }
            )
        if rule and list(link.get("matched_terms") or []) != expected_terms:
            failures.append(
                {
                    "link_id": link.get("link_id"),
                    "reason": "matched_terms_mismatch",
                    "expected": expected_terms,
                    "actual": link.get("matched_terms"),
                }
            )
        if link.get("claim_type") not in SUPPORTED_CLAIM_TYPES:
            failures.append({"link_id": link.get("link_id"), "reason": "unsupported_claim_type"})
    return {
        "name": "rule_claim_link_scores_are_supported",
        "passed": not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


def _check_link_ranks_are_contiguous(links: list[dict]) -> dict:
    ranks_by_rule: dict[str, list[int]] = defaultdict(list)
    failures = []
    for link in links:
        try:
            ranks_by_rule[str(link.get("rule_id") or "")].append(int(link.get("rank")))
        except (TypeError, ValueError):
            failures.append({"link_id": link.get("link_id"), "reason": "invalid_rank"})
    for rule_id, ranks in ranks_by_rule.items():
        expected = list(range(1, len(ranks) + 1))
        actual = sorted(ranks)
        if actual != expected:
            failures.append(
                {
                    "rule_id": rule_id,
                    "reason": "non_contiguous_ranks",
                    "expected": expected,
                    "actual": actual,
                }
            )
    return {
        "name": "rule_claim_link_ranks_are_contiguous",
        "passed": not failures,
        "details": {"failures": failures[:50], "failure_count": len(failures)},
    }


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
        output_dir=_output_dir_from_links_path(
            links_path,
            source_set_id=str(summary.get("source_set_id") or ""),
        ),
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


def _load_claims_for_validation(claims_path: Path) -> tuple[list[dict], str | None]:
    try:
        return _load_validated_claims_for_eval(claims_path), None
    except (FileNotFoundError, ValueError) as error:
        return [], str(error)


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


def _load_eval_cases(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Missing rule-claim link eval file: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not payload:
        raise ValueError("Rule-claim link eval file must contain a non-empty JSON list.")
    for index, case in enumerate(payload):
        if not isinstance(case, dict):
            raise ValueError(f"Rule-claim link eval case {index} must be an object.")
        for field in ("id", "rule_id"):
            if not case.get(field):
                raise ValueError(f"Rule-claim link eval case {index} is missing {field!r}.")
        _validate_eval_filters(index, case)
        _validate_eval_expectations(index, case)
        _validate_positive_eval_int(index, case, "min_links")
        _validate_positive_eval_int(index, case, "top_k")
    return payload


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
    for key in ("expected_source_record_ids", "expected_terms"):
        value = case.get(key)
        if value is not None and not isinstance(value, list):
            raise ValueError(f"Rule-claim link eval case {index} {key} must be a list.")


def _validate_positive_eval_int(index: int, case: dict, key: str) -> None:
    if key not in case:
        return
    try:
        value = int(case[key])
    except (TypeError, ValueError) as error:
        raise ValueError(f"Rule-claim link eval case {index} {key} must be an integer.") from error
    if value < 1:
        raise ValueError(f"Rule-claim link eval case {index} {key} must be at least 1.")


def _link_matches_eval_filters(link: dict, filters: dict) -> bool:
    for key in ("rule_id", "claim_type", "source_record_id"):
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
    return all(term.lower() in haystack for term in expected_terms)


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
    min_links_met: bool,
    type_hit: bool,
    source_hit: bool,
    term_hit: bool,
    provenance_supported: bool,
) -> list[str]:
    reasons = []
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
    return reasons


def _rule_query(rule: dict) -> str:
    return " ".join(
        str(value)
        for value in (
            rule.get("source_query"),
            rule.get("requirement"),
            rule.get("title"),
            " ".join(str(term) for term in rule.get("package_terms", [])),
        )
        if str(value or "").strip()
    )


def _score_rule_claim(
    rule: dict,
    claim: dict,
    *,
    terms: list[str],
    query: str,
) -> tuple[float, list[str]]:
    text = _claim_search_text(claim)
    token_set = set(_tokenize(text))
    matched_terms = [term for term in terms if _contains_term(term, token_set, text)]
    if not terms:
        return 0.1, []
    score = len(matched_terms) / len(terms)
    query_value = str(rule.get("source_query") or "").strip().lower()
    if query_value and query_value in text.lower():
        score += 0.35
    for phrase in rule.get("package_terms", []):
        phrase_value = str(phrase or "").strip().lower()
        if phrase_value and phrase_value in text.lower():
            score += 0.08
    source_filters = rule.get("source_filters") or {}
    review_topic = source_filters.get("review_topic") or source_filters.get("topic")
    if review_topic and _topic_matches(str(review_topic), claim.get("review_topics", [])):
        score += 0.15
    return score, matched_terms


def _claim_search_text(claim: dict) -> str:
    return " ".join(
        str(value)
        for value in (
            claim.get("claim_text"),
            claim.get("title"),
            claim.get("citation_label"),
            " ".join(str(topic) for topic in claim.get("review_topics", [])),
        )
        if str(value or "").strip()
    )


def _claim_matches_rule_filters(claim: dict, filters: dict) -> bool:
    for key in ("document_role", "authority_level", "source_record_id"):
        value = filters.get(key)
        if value and str(claim.get(key) or "").lower() != str(value).lower():
            return False
    review_topic = filters.get("review_topic") or filters.get("topic")
    if review_topic and not _topic_matches(str(review_topic), claim.get("review_topics", [])):
        return False
    citation = filters.get("citation")
    if citation and not _citation_matches(str(citation), claim):
        return False
    host = filters.get("host")
    if host and not _host_matches(str(host), claim):
        return False
    return True


def _topic_matches(filter_value: str, topics: list[str]) -> bool:
    needle = filter_value.lower()
    return any(needle == str(topic).lower() or needle in str(topic).lower() for topic in topics)


def _citation_matches(filter_value: str, claim: dict) -> bool:
    needle = filter_value.lower()
    return any(
        needle in str(claim.get(field) or "").lower()
        for field in ("citation_label", "source_record_id", "title", "artifact_sha256")
    )


def _host_matches(filter_value: str, claim: dict) -> bool:
    needle = filter_value.lower()
    for field in ("final_url", "effective_url", "original_url"):
        value = str(claim.get(field) or "")
        if not value:
            continue
        host = urlparse(value).netloc.lower()
        if needle == host or needle in host:
            return True
    return False


def _contains_term(term: str, token_set: set[str], text: str) -> bool:
    if " " in term:
        return term.lower() in text.lower()
    return term.lower() in token_set


def _tokenize(text: str) -> list[str]:
    tokens = []
    seen = set()
    for match in TOKEN_RE.finditer(text.lower()):
        token = match.group(0).strip("._-")
        if len(token) < 3 or token in STOPWORDS or token in seen:
            continue
        seen.add(token)
        tokens.append(token)
    return tokens


def _write_sqlite_links(
    path: Path,
    *,
    source_set_id: str,
    rule_pack: dict,
    links: list[dict],
    gaps: list[dict],
) -> None:
    if path.exists():
        path.unlink()
    with closing(sqlite3.connect(path)) as connection:
        connection.executescript(
            """
            CREATE TABLE metadata (
              key TEXT PRIMARY KEY,
              value_json TEXT NOT NULL
            );

            CREATE TABLE rule_claim_links (
              link_id TEXT PRIMARY KEY,
              rule_id TEXT NOT NULL,
              claim_id TEXT NOT NULL,
              source_record_id TEXT NOT NULL,
              claim_type TEXT NOT NULL,
              rank INTEGER NOT NULL,
              score REAL NOT NULL,
              citation_label TEXT NOT NULL,
              payload_json TEXT NOT NULL
            );

            CREATE TABLE rule_claim_gaps (
              gap_id TEXT PRIMARY KEY,
              rule_id TEXT NOT NULL,
              reason TEXT NOT NULL,
              payload_json TEXT NOT NULL
            );

            CREATE INDEX idx_rule_claim_links_rule_id ON rule_claim_links(rule_id);
            CREATE INDEX idx_rule_claim_links_claim_id ON rule_claim_links(claim_id);
            CREATE INDEX idx_rule_claim_links_source_record_id ON rule_claim_links(source_record_id);
            CREATE INDEX idx_rule_claim_links_claim_type ON rule_claim_links(claim_type);
            CREATE INDEX idx_rule_claim_gaps_rule_id ON rule_claim_gaps(rule_id);
            """
        )
        metadata = {
            "schema_version": RULE_CLAIM_LINK_SCHEMA_VERSION,
            "source_set_id": source_set_id,
            "rule_pack_id": rule_pack["rule_pack_id"],
            "rule_pack_version": rule_pack["version"],
            "created_at": _utc_now(),
            "link_count": len(links),
            "gap_count": len(gaps),
        }
        for key, value in metadata.items():
            connection.execute(
                "INSERT INTO metadata VALUES (?, ?)",
                (key, json.dumps(value, sort_keys=True)),
            )
        for link in links:
            connection.execute(
                """
                INSERT INTO rule_claim_links VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    link["link_id"],
                    link["rule_id"],
                    link["claim_id"],
                    link["source_record_id"],
                    link["claim_type"],
                    int(link["rank"]),
                    float(link["score"]),
                    link["citation_label"],
                    json.dumps(link, sort_keys=True),
                ),
            )
        for gap in gaps:
            connection.execute(
                "INSERT INTO rule_claim_gaps VALUES (?, ?, ?, ?)",
                (
                    gap["gap_id"],
                    gap["rule_id"],
                    gap["reason"],
                    json.dumps(gap, sort_keys=True),
                ),
            )
        connection.commit()


def _sqlite_link_checks(
    path: Path,
    *,
    expected_link_count: int,
    expected_gap_count: int,
) -> list[dict]:
    if not path.exists():
        return [
            {
                "name": "rule_claim_sqlite_exists",
                "passed": False,
                "details": {"path": str(path)},
            }
        ]
    try:
        with closing(sqlite3.connect(path)) as connection:
            link_count = connection.execute(
                "SELECT COUNT(*) FROM rule_claim_links"
            ).fetchone()[0]
            gap_count = connection.execute(
                "SELECT COUNT(*) FROM rule_claim_gaps"
            ).fetchone()[0]
    except sqlite3.Error as error:
        return [
            {
                "name": "rule_claim_sqlite_readable",
                "passed": False,
                "details": {"path": str(path), "error": str(error)},
            }
        ]
    return [
        {
            "name": "rule_claim_sqlite_link_count_matches_jsonl",
            "passed": link_count == expected_link_count,
            "details": {"expected": expected_link_count, "actual": link_count},
        },
        {
            "name": "rule_claim_sqlite_gap_count_matches_jsonl",
            "passed": gap_count == expected_gap_count,
            "details": {"expected": expected_gap_count, "actual": gap_count},
        },
    ]


def _with_additional_checks(validation: dict, checks: list[dict]) -> dict:
    merged_checks = [*validation["checks"], *checks]
    return {
        **validation,
        "passed": all(check["passed"] for check in merged_checks),
        "checks": merged_checks,
    }


def _output_dir_from_links_path(links_path: Path, *, source_set_id: str) -> Path:
    if not source_set_id:
        raise ValueError("Rule-claim link summary has no source_set_id.")
    if links_path.name != "rule_claim_links.jsonl":
        raise ValueError(f"Expected rule_claim_links.jsonl path, got: {links_path}")
    version_dir = links_path.parent
    pack_dir = version_dir.parent
    links_root = pack_dir.parent
    source_dir = links_root.parent
    derived_dir = source_dir.parent
    if links_root.name != "rule_claim_links" or source_dir.name != source_set_id or derived_dir.name != "derived":
        raise ValueError(
            "Rule-claim links path must be under "
            "source_library/derived/<source_set_id>/rule_claim_links/<rule_pack>/<version>/."
        )
    return derived_dir.parent


def _safe_segment(value: str) -> str:
    if not value or not SAFE_SEGMENT_RE.fullmatch(value):
        raise ValueError(
            "rule_pack_id and version must contain only letters, numbers, dot, underscore, or hyphen."
        )
    return value


def _link_id(
    *,
    source_set_id: str,
    rule_pack_id: str,
    rule_pack_version: str,
    rule_id: str,
    claim_id: str,
) -> str:
    material = "|".join([source_set_id, rule_pack_id, rule_pack_version, rule_id, claim_id])
    return f"rule_claim_link:{hashlib.sha256(material.encode('utf-8')).hexdigest()[:24]}"


def _gap_id(
    *,
    source_set_id: str,
    rule_pack_id: str,
    rule_pack_version: str,
    rule_id: str,
    reason: str,
) -> str:
    material = "|".join([source_set_id, rule_pack_id, rule_pack_version, rule_id, reason])
    return f"rule_claim_gap:{hashlib.sha256(material.encode('utf-8')).hexdigest()[:24]}"


def _failed_check_names(validation: dict) -> list[str]:
    return [
        str(check.get("name"))
        for check in validation.get("checks", [])
        if not check.get("passed")
    ]


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
