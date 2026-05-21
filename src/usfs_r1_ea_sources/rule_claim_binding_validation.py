from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import closing
from importlib import import_module
from pathlib import Path
import sqlite3

from .claim_extraction import SUPPORTED_CLAIM_TYPES
from .rule_claim_binding_runtime import RULE_CLAIM_GAP_SCHEMA_VERSION
from .rule_claim_binding_runtime import RULE_CLAIM_LINK_SCHEMA_VERSION
from .rule_claim_binding_runtime import _claim_matches_rule_filters
from .rule_claim_binding_runtime import _gap_id
from .rule_claim_binding_runtime import _link_id
from .rule_claim_binding_runtime import _rule_query
from .rule_claim_binding_runtime import _score_rule_claim
from .rule_claim_binding_runtime import _tokenize
from .rule_packs import load_rule_pack
from .rule_packs import validate_rule_pack


_RULE_CLAIM_BINDING = import_module("usfs_r1_ea_sources.rule_claim_binding")
REQUIRED_GAP_FIELDS = _RULE_CLAIM_BINDING.REQUIRED_GAP_FIELDS
REQUIRED_LINK_FIELDS = _RULE_CLAIM_BINDING.REQUIRED_LINK_FIELDS
RULE_CLAIM_LINK_VALIDATION_SCHEMA_VERSION = (
    _RULE_CLAIM_BINDING.RULE_CLAIM_LINK_VALIDATION_SCHEMA_VERSION
)
_claim_artifact_readiness = _RULE_CLAIM_BINDING._claim_artifact_readiness
_failed_check_names = _RULE_CLAIM_BINDING._failed_check_names
_load_validated_claims_for_eval = _RULE_CLAIM_BINDING._load_validated_claims_for_eval
_read_jsonl = _RULE_CLAIM_BINDING._read_jsonl
_utc_now = _RULE_CLAIM_BINDING._utc_now


def validate_rule_claim_links(
    *,
    output_dir: Path,
    source_set_id: str,
    rule_pack_path: Path,
    claims_path: Path,
    links_path: Path,
    gaps_path: Path,
    allow_partial_claims: bool = False,
) -> dict:
    output_dir = Path(output_dir)
    rule_pack_path = Path(rule_pack_path)
    claims_path = Path(claims_path)
    links_path = Path(links_path)
    gaps_path = Path(gaps_path)

    rule_pack = load_rule_pack(rule_pack_path) if rule_pack_path.exists() else {}
    rule_pack_validation = validate_rule_pack(rule_pack) if rule_pack else {"passed": False, "checks": []}
    claims, claim_error, claim_validation_passed, claim_reviewer_ready = _load_claims_for_validation(
        claims_path,
        allow_partial_claims=allow_partial_claims,
    )
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
            "name": "claims_validation_passed",
            "passed": claim_error is None and claim_validation_passed and bool(claims),
            "details": {
                "path": str(claims_path),
                "exists": claims_path.exists(),
                "claim_count": len(claims),
                "validation_passed": claim_validation_passed,
                "reviewer_ready": claim_reviewer_ready,
                "allow_partial_claims": allow_partial_claims,
                "error": claim_error,
            },
        },
        {
            "name": "claims_are_reviewer_ready",
            "passed": claim_error is None and claim_reviewer_ready,
            "details": {
                "path": str(claims_path),
                "exists": claims_path.exists(),
                "claim_count": len(claims),
                "validation_passed": claim_validation_passed,
                "reviewer_ready": claim_reviewer_ready,
                "allow_partial_claims": allow_partial_claims,
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
    strict_blockers = {"claims_are_reviewer_ready"}
    passed = all(check["passed"] for check in checks)
    if allow_partial_claims:
        passed = all(check["passed"] or check["name"] in strict_blockers for check in checks)
    return {
        "schema_version": RULE_CLAIM_LINK_VALIDATION_SCHEMA_VERSION,
        "source_set_id": source_set_id,
        "created_at": _utc_now(),
        "passed": passed,
        "checks": checks,
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
            expected_score, expected_terms = _score_rule_claim(
                rule,
                link,
                terms=terms,
                query=_rule_query(rule),
            )
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


def _load_claims_for_validation(
    claims_path: Path,
    *,
    allow_partial_claims: bool = False,
) -> tuple[list[dict], str | None, bool, bool]:
    summary, validation = _claim_artifact_readiness(claims_path)
    claim_validation_failed_checks = _failed_check_names(validation)
    claim_validation_passed = bool(validation and validation.get("passed")) or (
        allow_partial_claims
        and bool(claim_validation_failed_checks)
        and all(
            name
            in {
                "extraction_validation_passed",
                "extraction_scope_is_complete",
                "retrieval_is_reviewer_ready",
            }
            for name in claim_validation_failed_checks
        )
    )
    claim_reviewer_ready = bool(summary and summary.get("reviewer_ready"))
    try:
        return (
            _load_validated_claims_for_eval(
                claims_path,
                require_reviewer_ready=not allow_partial_claims,
            ),
            None,
            claim_validation_passed,
            claim_reviewer_ready,
        )
    except (FileNotFoundError, ValueError) as error:
        return [], str(error), claim_validation_passed, claim_reviewer_ready


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
            link_count = connection.execute("SELECT COUNT(*) FROM rule_claim_links").fetchone()[0]
            gap_count = connection.execute("SELECT COUNT(*) FROM rule_claim_gaps").fetchone()[0]
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


def _with_additional_checks(
    validation: dict,
    checks: list[dict],
    *,
    allow_partial_claims: bool,
) -> dict:
    merged_checks = [*validation["checks"], *checks]
    ignored = {"claims_are_reviewer_ready"}
    passed = all(
        check["passed"] or (allow_partial_claims and check["name"] in ignored)
        for check in merged_checks
    )
    return {
        **validation,
        "passed": passed,
        "checks": merged_checks,
    }
