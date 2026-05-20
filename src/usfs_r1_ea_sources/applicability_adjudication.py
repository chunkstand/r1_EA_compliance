from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import hashlib
import json
import re

from .records import sha256_file


APPLICABILITY_ADJUDICATION_TEMPLATE_SCHEMA_VERSION = (
    "applicability-adjudication-template-v0"
)
APPLICABILITY_ADJUDICATION_EVAL_SCHEMA_VERSION = "applicability-adjudication-eval-v0"
APPLICABILITY_ADJUDICATION_APPLY_SCHEMA_VERSION = "applicability-adjudication-apply-v0"
SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
UNRESOLVED_STATUSES = {"unresolved", "needs_adjudication"}
FINAL_STATUSES = {"applicable", "not_applicable"}
PENDING_DISPOSITIONS = {"pending"}
RESOLVED_DISPOSITIONS = {"human_applicable", "human_not_applicable"}
ALLOWED_DISPOSITIONS = PENDING_DISPOSITIONS | RESOLVED_DISPOSITIONS
REQUIRED_ADJUDICATION_FIELDS = (
    "adjudicated_at",
    "adjudicated_by",
    "source_type",
    "rationale",
    "supporting_citation_refs",
)


@dataclass(frozen=True)
class ApplicabilityAdjudicationTemplateResult:
    review_id: str
    source_set_id: str | None
    applicability_dir: Path
    output_path: Path
    markdown_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class ApplicabilityAdjudicationEvalResult:
    review_id: str
    source_set_id: str | None
    applicability_dir: Path
    adjudication_file: Path
    output_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class ApplicabilityAdjudicationApplyResult:
    review_id: str
    source_set_id: str | None
    applicability_dir: Path
    adjudication_file: Path
    output_path: Path
    summary: dict[str, Any]


def write_applicability_adjudication_template(
    *,
    output_dir: Path,
    review_id: str,
    source_set_id: str | None = None,
    decisions_path: Path | None = None,
    output_path: Path | None = None,
) -> ApplicabilityAdjudicationTemplateResult:
    """Write a reviewer-fillable template for unresolved applicability decisions."""

    output_dir = Path(output_dir)
    _validate_safe_segment(review_id, "review_id")
    applicability_dir = output_dir / "reviews" / review_id / "applicability"
    decisions_path = Path(decisions_path) if decisions_path else (
        applicability_dir / "applicability_decisions.jsonl"
    )
    decisions = _read_required_jsonl(decisions_path, "applicability decisions")
    if source_set_id is None:
        source_set_id = _source_set_from_decisions(decisions)
    if source_set_id:
        _validate_safe_segment(source_set_id, "source_set_id")
    output_path = Path(output_path) if output_path else (
        applicability_dir / "applicability_adjudication_template.json"
    )
    markdown_path = output_path.with_name("applicability_adjudication_worklist.md")
    items = [
        _adjudication_template_item(decision)
        for decision in decisions
        if _decision_status(decision) in UNRESOLVED_STATUSES
    ]
    summary = {
        "schema_version": "applicability-adjudication-template-summary-v0",
        "created_at": _utc_now(),
        "review_id": review_id,
        "source_set_id": source_set_id,
        "decision_count": len(decisions),
        "adjudication_item_count": len(items),
        "pending_item_count": len(items),
        "decisions_path": str(decisions_path),
        "decisions_sha256": sha256_file(decisions_path),
        "output_path": str(output_path),
        "markdown_path": str(markdown_path),
        "instructions": (
            "Fill final_status, disposition, adjudicated_at, adjudicated_by, source_type, "
            "rationale, and supporting_citation_refs for every item before running "
            "applicability-adjudication-eval or applicability-adjudication-apply."
        ),
    }
    template = {
        "schema_version": APPLICABILITY_ADJUDICATION_TEMPLATE_SCHEMA_VERSION,
        "adjudication_id": f"{review_id}-applicability-adjudication",
        "created_at": summary["created_at"],
        "review_id": review_id,
        "source_set_id": source_set_id,
        "decisions_path": str(decisions_path),
        "applicability_decisions_sha256": summary["decisions_sha256"],
        "allowed_final_statuses": sorted(FINAL_STATUSES),
        "allowed_dispositions": sorted(ALLOWED_DISPOSITIONS),
        "resolved_dispositions": sorted(RESOLVED_DISPOSITIONS),
        "required_adjudication_fields": list(REQUIRED_ADJUDICATION_FIELDS),
        "summary": summary,
        "items": items,
    }
    _write_json(output_path, template)
    _write_text(markdown_path, _adjudication_worklist_markdown(template))
    return ApplicabilityAdjudicationTemplateResult(
        review_id=review_id,
        source_set_id=source_set_id,
        applicability_dir=applicability_dir,
        output_path=output_path,
        markdown_path=markdown_path,
        summary=summary,
    )


def evaluate_applicability_adjudication(
    *,
    output_dir: Path,
    review_id: str,
    source_set_id: str | None = None,
    adjudication_file: Path | None = None,
    decisions_path: Path | None = None,
    output_path: Path | None = None,
) -> ApplicabilityAdjudicationEvalResult:
    """Evaluate a completed applicability adjudication against current decisions."""

    output_dir = Path(output_dir)
    _validate_safe_segment(review_id, "review_id")
    applicability_dir = output_dir / "reviews" / review_id / "applicability"
    adjudication_file = Path(adjudication_file) if adjudication_file else (
        applicability_dir / "applicability_adjudication_template.json"
    )
    decisions_path = Path(decisions_path) if decisions_path else (
        applicability_dir / "applicability_decisions.jsonl"
    )
    output_path = Path(output_path) if output_path else (
        applicability_dir / "applicability_adjudication_eval.json"
    )
    adjudication = _read_required_json(adjudication_file, "applicability adjudication")
    if adjudication.get("schema_version") != APPLICABILITY_ADJUDICATION_TEMPLATE_SCHEMA_VERSION:
        raise ValueError(
            "Applicability adjudication has unsupported schema_version: "
            f"{adjudication.get('schema_version')}"
        )
    decisions = _read_required_jsonl(decisions_path, "applicability decisions")
    if source_set_id is None:
        source_set_id = (
            str(adjudication.get("source_set_id") or "").strip()
            or _source_set_from_decisions(decisions)
        )
    if source_set_id:
        _validate_safe_segment(source_set_id, "source_set_id")
    adjudication_items = _adjudication_items(adjudication)
    item_results = _adjudication_item_results(
        adjudication=adjudication,
        adjudication_items=adjudication_items,
        decisions=decisions,
        decisions_path=decisions_path,
    )
    checks = [
        _check_adjudication_identity(
            adjudication=adjudication,
            review_id=review_id,
            source_set_id=source_set_id,
            decisions_path=decisions_path,
        ),
        _check_adjudication_covers_unresolved(
            adjudication_items=adjudication_items,
            decisions=decisions,
        ),
        _check_adjudication_items_complete(item_results),
    ]
    failure_counts = Counter(
        category
        for result in item_results
        for category in result.get("failure_categories", [])
    )
    passed = all(check["passed"] for check in checks)
    summary = {
        "schema_version": APPLICABILITY_ADJUDICATION_EVAL_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": review_id,
        "source_set_id": source_set_id,
        "passed": passed,
        "adjudication_file": str(adjudication_file),
        "decisions_path": str(decisions_path),
        "output_path": str(output_path),
        "decision_count": len(decisions),
        "unresolved_decision_count": sum(
            1 for decision in decisions if _decision_status(decision) in UNRESOLVED_STATUSES
        ),
        "adjudication_item_count": len(adjudication_items),
        "resolved_adjudication_count": sum(
            1 for result in item_results if result.get("passed")
        ),
        "pending_adjudication_count": failure_counts.get("adjudication_pending", 0),
        "failure_category_counts": dict(sorted(failure_counts.items())),
    }
    payload = {
        "schema_version": APPLICABILITY_ADJUDICATION_EVAL_SCHEMA_VERSION,
        "created_at": summary["created_at"],
        "review_id": review_id,
        "source_set_id": source_set_id,
        "adjudication_file": str(adjudication_file),
        "decisions_path": str(decisions_path),
        "summary": summary,
        "checks": checks,
        "item_results": item_results,
    }
    _write_json(output_path, payload)
    return ApplicabilityAdjudicationEvalResult(
        review_id=review_id,
        source_set_id=source_set_id,
        applicability_dir=applicability_dir,
        adjudication_file=adjudication_file,
        output_path=output_path,
        summary=summary,
    )


def _adjudication_template_item(decision: dict[str, Any]) -> dict[str, Any]:
    evidence_refs = _default_supporting_refs(decision)
    return {
        "item_id": _stable_id(
            "applicability-adjudication-item",
            str(decision.get("decision_id") or ""),
        ),
        "decision_id": decision.get("decision_id"),
        "candidate_authority_id": decision.get("candidate_authority_id"),
        "authority_category": decision.get("authority_category"),
        "authority_document_role": decision.get("authority_document_role"),
        "current_status": decision.get("status"),
        "current_basis_type": decision.get("basis_type"),
        "expected_current": {
            "decision_id": decision.get("decision_id"),
            "candidate_authority_id": decision.get("candidate_authority_id"),
            "status": decision.get("status"),
            "basis_type": decision.get("basis_type"),
        },
        "final_status": "",
        "disposition": "pending",
        "allowed_final_statuses": sorted(FINAL_STATUSES),
        "allowed_dispositions": sorted(ALLOWED_DISPOSITIONS),
        "missing_evidence": decision.get("missing_evidence") or [],
        "contradiction_notes": decision.get("contradiction_notes") or [],
        "package_evidence_spans": decision.get("package_evidence_spans") or [],
        "source_library_evidence_spans": decision.get("source_library_evidence_spans") or [],
        "negative_evidence_spans": decision.get("negative_evidence_spans") or [],
        "search_coverage_certificate_ids": decision.get("search_coverage_certificate_ids") or [],
        "retrieval_trace_ids": decision.get("retrieval_trace_ids") or [],
        "graph_path_ids": decision.get("graph_path_ids") or [],
        "adjudicated_at": "",
        "adjudicated_by": [],
        "source_type": "",
        "rationale": "",
        "supporting_citation_refs": evidence_refs,
        "reviewer_notes": "",
    }


def _adjudication_worklist_markdown(template: dict[str, Any]) -> str:
    summary = template.get("summary") if isinstance(template.get("summary"), dict) else {}
    lines = [
        "# Applicability Adjudication Worklist",
        "",
        f"- Review ID: `{summary.get('review_id')}`",
        f"- Source set ID: `{summary.get('source_set_id')}`",
        f"- Open adjudication items: `{summary.get('adjudication_item_count', 0)}`",
        f"- JSON template: `{summary.get('output_path')}`",
        "",
    ]
    for index, item in enumerate(_adjudication_items(template), start=1):
        lines.extend(
            [
                f"## {index}. `{item.get('candidate_authority_id')}`",
                "",
                f"- Decision ID: `{item.get('decision_id')}`",
                f"- Current status: `{item.get('current_status')}`",
                f"- Current basis: `{item.get('current_basis_type')}`",
                f"- Authority category: `{item.get('authority_category')}`",
                f"- Missing evidence: `{item.get('missing_evidence') or []}`",
                f"- Contradiction notes: `{item.get('contradiction_notes') or []}`",
                "- Required action: set `final_status`, replace `pending`, and complete "
                "`adjudicated_at`, `adjudicated_by`, `source_type`, `rationale`, and "
                "`supporting_citation_refs` in the JSON file.",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _adjudication_item_results(
    *,
    adjudication: dict[str, Any],
    adjudication_items: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    decisions_path: Path,
) -> list[dict[str, Any]]:
    decisions_by_id = {
        str(decision.get("decision_id") or ""): decision
        for decision in decisions
        if decision.get("decision_id")
    }
    unresolved_ids = {
        str(decision.get("decision_id") or "")
        for decision in decisions
        if _decision_status(decision) in UNRESOLVED_STATUSES
    }
    item_counts = Counter(str(item.get("decision_id") or "") for item in adjudication_items)
    results = []
    for decision_id in sorted(unresolved_ids):
        matching_items = [
            item
            for item in adjudication_items
            if str(item.get("decision_id") or "") == decision_id
        ]
        if matching_items:
            for item in matching_items:
                results.append(
                    _adjudication_item_result(
                        item=item,
                        decision=decisions_by_id.get(decision_id, {}),
                        duplicate_count=item_counts[decision_id],
                    )
                )
        else:
            decision = decisions_by_id.get(decision_id, {})
            results.append(
                {
                    "decision_id": decision_id,
                    "candidate_authority_id": decision.get("candidate_authority_id"),
                    "passed": False,
                    "failure_categories": ["adjudication_missing"],
                    "details": {"reason": "current_unresolved_decision_not_adjudicated"},
                }
            )
    for item in adjudication_items:
        decision_id = str(item.get("decision_id") or "")
        if decision_id in unresolved_ids:
            continue
        results.append(
            {
                "decision_id": decision_id,
                "candidate_authority_id": item.get("candidate_authority_id"),
                "passed": False,
                "failure_categories": ["adjudication_unexpected"],
                "details": {"reason": "adjudication_item_not_in_current_unresolved_decisions"},
            }
        )
    if adjudication.get("applicability_decisions_sha256") != sha256_file(decisions_path):
        results.append(
            {
                "decision_id": None,
                "candidate_authority_id": None,
                "passed": False,
                "failure_categories": ["adjudication_stale"],
                "details": {
                    "expected": adjudication.get("applicability_decisions_sha256"),
                    "actual": sha256_file(decisions_path),
                },
            }
        )
    return results


def _adjudication_item_result(
    *,
    item: dict[str, Any],
    decision: dict[str, Any],
    duplicate_count: int,
) -> dict[str, Any]:
    failure_categories = []
    details: dict[str, Any] = {}
    disposition = str(item.get("disposition") or "")
    final_status = str(item.get("final_status") or "")
    expected_current = (
        item.get("expected_current") if isinstance(item.get("expected_current"), dict) else {}
    )
    current_mismatches = _current_status_mismatches(
        expected=expected_current,
        decision=decision,
    )
    if duplicate_count > 1:
        failure_categories.append("adjudication_duplicate")
        details["duplicate_count"] = duplicate_count
    if disposition not in ALLOWED_DISPOSITIONS:
        failure_categories.append("adjudication_invalid_disposition")
    elif disposition in PENDING_DISPOSITIONS:
        failure_categories.append("adjudication_pending")
    if final_status not in FINAL_STATUSES:
        failure_categories.append("adjudication_invalid_status")
    if disposition == "human_applicable" and final_status != "applicable":
        failure_categories.append("adjudication_status_disposition_mismatch")
    if disposition == "human_not_applicable" and final_status != "not_applicable":
        failure_categories.append("adjudication_status_disposition_mismatch")
    missing_fields = _missing_adjudication_fields(item)
    if missing_fields:
        failure_categories.append("adjudication_incomplete")
        details["missing_fields"] = missing_fields
    if current_mismatches:
        failure_categories.append("adjudication_expectation_mismatch")
        details["current_status_mismatches"] = current_mismatches
    return {
        "item_id": item.get("item_id"),
        "decision_id": item.get("decision_id"),
        "candidate_authority_id": item.get("candidate_authority_id"),
        "final_status": final_status or None,
        "disposition": disposition or None,
        "passed": not failure_categories,
        "failure_categories": failure_categories,
        "details": details,
    }


def _check_adjudication_identity(
    *,
    adjudication: dict[str, Any],
    review_id: str,
    source_set_id: str | None,
    decisions_path: Path,
) -> dict[str, Any]:
    failures = []
    if adjudication.get("review_id") != review_id:
        failures.append(
            _failure(
                "adjudication_missing",
                details={
                    "field": "review_id",
                    "expected": review_id,
                    "actual": adjudication.get("review_id"),
                },
            )
        )
    if source_set_id and adjudication.get("source_set_id") != source_set_id:
        failures.append(
            _failure(
                "adjudication_missing",
                details={
                    "field": "source_set_id",
                    "expected": source_set_id,
                    "actual": adjudication.get("source_set_id"),
                },
            )
        )
    if adjudication.get("applicability_decisions_sha256") != sha256_file(decisions_path):
        failures.append(
            _failure(
                "source_set_stale",
                details={"field": "applicability_decisions_sha256"},
            )
        )
    return _check(
        "adjudication_identity_matches_current_decisions",
        not failures,
        failures,
        {"adjudication_id": adjudication.get("adjudication_id")},
    )


def _check_adjudication_covers_unresolved(
    *,
    adjudication_items: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    unresolved_ids = {
        str(decision.get("decision_id") or "")
        for decision in decisions
        if _decision_status(decision) in UNRESOLVED_STATUSES
    }
    item_ids = [str(item.get("decision_id") or "") for item in adjudication_items]
    missing = sorted(unresolved_ids - set(item_ids))
    unexpected = sorted(set(item_ids) - unresolved_ids)
    duplicates = sorted(
        decision_id for decision_id, count in Counter(item_ids).items() if count > 1
    )
    failures = [
        *[_failure("adjudication_missing", details={"decision_id": value}) for value in missing],
        *[
            _failure("adjudication_unexpected", details={"decision_id": value})
            for value in unexpected
        ],
        *[
            _failure("adjudication_duplicate", details={"decision_id": value})
            for value in duplicates
        ],
    ]
    return _check(
        "adjudication_items_cover_unresolved_decisions",
        not failures,
        failures,
        {
            "unresolved_decision_count": len(unresolved_ids),
            "adjudication_item_count": len(adjudication_items),
            "missing": missing,
            "unexpected": unexpected,
            "duplicates": duplicates,
        },
    )


def _check_adjudication_items_complete(
    item_results: list[dict[str, Any]],
) -> dict[str, Any]:
    failures = [
        _failure(
            str(category),
            candidate_authority_id=str(result.get("candidate_authority_id") or ""),
            details={"decision_id": result.get("decision_id")},
        )
        for result in item_results
        for category in result.get("failure_categories", [])
    ]
    return _check(
        "adjudication_items_are_complete_and_replayable",
        not failures,
        failures,
        {"failure_count": len(failures)},
    )


def _default_supporting_refs(decision: dict[str, Any]) -> list[str]:
    refs = []
    for evidence in decision.get("package_evidence_spans") or []:
        ref = evidence.get("citation_label") or evidence.get("evidence_id")
        if ref:
            refs.append(str(ref))
    for evidence in decision.get("source_library_evidence_spans") or []:
        ref = evidence.get("citation_label") or evidence.get("evidence_id")
        if ref:
            refs.append(str(ref))
    for cert_id in decision.get("search_coverage_certificate_ids") or []:
        refs.append(str(cert_id))
    return sorted(set(refs))


def _missing_adjudication_fields(item: dict[str, Any]) -> list[str]:
    missing = []
    for field in REQUIRED_ADJUDICATION_FIELDS:
        value = item.get(field)
        if field in {"adjudicated_by", "supporting_citation_refs"}:
            if not _string_list(value):
                missing.append(field)
        elif not str(value or "").strip():
            missing.append(field)
    return sorted(missing)


def _current_status_mismatches(
    *,
    expected: dict[str, Any],
    decision: dict[str, Any],
) -> list[dict[str, Any]]:
    mismatches = []
    field_map = {
        "decision_id": "decision_id",
        "candidate_authority_id": "candidate_authority_id",
        "status": "status",
        "basis_type": "basis_type",
    }
    for expected_field, decision_field in field_map.items():
        if expected_field not in expected:
            continue
        if expected[expected_field] != decision.get(decision_field):
            mismatches.append(
                {
                    "field": expected_field,
                    "expected": expected[expected_field],
                    "actual": decision.get(decision_field),
                }
            )
    return mismatches


def _matching_adjudication_item_result(
    eval_payload: dict[str, Any],
    ref: dict[str, Any],
) -> dict[str, Any] | None:
    for result in eval_payload.get("item_results") or []:
        if not isinstance(result, dict):
            continue
        if ref.get("item_id") and result.get("item_id") == ref.get("item_id"):
            return result
        if ref.get("decision_id") and result.get("decision_id") == ref.get("decision_id"):
            return result
    return None


def _adjudication_items(adjudication: dict[str, Any]) -> list[dict[str, Any]]:
    items = adjudication.get("items")
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []


def _read_json_if_exists(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return value


def _read_required_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object for {label}: {path}")
    return value


def _read_jsonl_if_exists(path: Path | None) -> list[dict[str, Any]]:
    if path is None or not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _read_required_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    return _read_jsonl_if_exists(path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl_and_hash(path: Path, records: list[dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    return sha256_file(path)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _stable_id(*parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return f"{parts[0]}:{digest[:16]}"


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item or "").strip()]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []


def _validate_safe_segment(value: str | None, label: str) -> None:
    if not value or not SAFE_SEGMENT_RE.fullmatch(value):
        raise ValueError(f"{label} must contain only letters, numbers, dot, underscore, or hyphen.")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _decision_status(decision: dict[str, Any]) -> str:
    return str(decision.get("status") or "")


def _source_set_from_decisions(decisions: list[dict[str, Any]]) -> str | None:
    for decision in decisions:
        source_set_id = str(decision.get("source_set_id") or "").strip()
        if source_set_id:
            return source_set_id
    return None


def _check(
    name: str,
    passed: bool,
    failures: list[dict[str, Any]],
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "name": name,
        "passed": passed,
        "failure_categories": sorted(
            {
                str(failure.get("failure_category") or "")
                for failure in failures
                if failure.get("failure_category")
            }
        ),
        "failures": failures,
        "details": details,
    }


def _failure(
    failure_category: str,
    *,
    candidate_authority_id: str | None = None,
    artifact: str | None = None,
    path: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "failure_category": failure_category,
        "candidate_authority_id": candidate_authority_id,
        "artifact": artifact,
        "path": path,
        "details": details or {},
    }
