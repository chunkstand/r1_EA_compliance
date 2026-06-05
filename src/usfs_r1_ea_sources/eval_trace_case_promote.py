"""Promote first-class eval traces into versioned eval case fixtures."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .eval_trace_inventory import REPO_ROOT

CASE_FILE_SCHEMA_VERSION = "eval-trace-case-file-v1"
CASE_SCHEMA_VERSION = "eval-trace-promoted-case-v1"
SUMMARY_SCHEMA_VERSION = "eval-trace-case-promote-summary-v1"
CASE_FILE_VALIDATION_SUMMARY_SCHEMA_VERSION = (
    "eval-trace-case-file-validation-summary-v1"
)
DEFAULT_EVAL_TRACE_CASE_FILE_PATH = Path(
    "config/eval_trace_cases/system_eval_trace_cases_v1.json"
)
RISK_LEVELS = frozenset({"low", "medium", "high", "critical"})
HUMAN_LABEL_STATUSES = frozenset({"unlabeled", "labeled", "reviewed", "rejected"})
REQUIRED_DETERMINISTIC_SCORERS = frozenset(
    {"retrieval", "groundedness_cited_source_spans", "trace_integrity"}
)


@dataclass(frozen=True)
class EvalTraceCasePromoteResult:
    summary: dict[str, Any]


@dataclass(frozen=True)
class EvalTraceCaseFileValidationResult:
    summary: dict[str, Any]


def validate_eval_trace_case_file(
    *,
    case_file: str | Path = DEFAULT_EVAL_TRACE_CASE_FILE_PATH,
    summary_path: str | Path | None = None,
    require_cases: bool = True,
    repo_root: Path = REPO_ROOT,
) -> EvalTraceCaseFileValidationResult:
    resolved_case_file = _resolve_path(case_file, repo_root=repo_root)
    resolved_summary_path = (
        _resolve_path(summary_path, repo_root=repo_root) if summary_path is not None else None
    )
    failure_reasons: list[str] = []
    checks: dict[str, bool] = {}

    _require_bool(checks, failure_reasons, "case_file_exists", resolved_case_file.exists())
    payload: dict[str, Any] = {}
    if resolved_case_file.exists():
        try:
            payload = json.loads(resolved_case_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            failure_reasons.append("case_file_parses")
    checks["case_file_parses"] = bool(payload)
    checks["case_file_schema_version"] = (
        payload.get("schema_version") == CASE_FILE_SCHEMA_VERSION
    )
    if not checks["case_file_schema_version"]:
        failure_reasons.append("case_file_schema_version")
    cases = payload.get("cases")
    checks["cases_is_list"] = isinstance(cases, list)
    if not checks["cases_is_list"]:
        failure_reasons.append("cases_is_list")
        cases = []
    checks["case_count_present"] = not require_cases or bool(cases)
    if not checks["case_count_present"]:
        failure_reasons.append("case_count_present")

    case_failures: list[dict[str, Any]] = []
    for case in cases:
        if not isinstance(case, dict):
            case_failures.append({"case_id": None, "failure_reasons": ["case_is_object"]})
            continue
        failures = _promoted_case_failure_reasons(case)
        if failures:
            case_failures.append(
                {
                    "case_id": _clean(case.get("case_id")),
                    "failure_reasons": failures,
                }
            )
    checks["promoted_cases_valid"] = not case_failures
    if case_failures:
        failure_reasons.append("promoted_cases_valid")

    summary = {
        "schema_version": CASE_FILE_VALIDATION_SUMMARY_SCHEMA_VERSION,
        "passed": not failure_reasons,
        "command_succeeded": not failure_reasons,
        "case_file_path": _display_path(resolved_case_file, repo_root=repo_root),
        "summary_path": (
            _display_path(resolved_summary_path, repo_root=repo_root)
            if resolved_summary_path is not None
            else None
        ),
        "case_count": len(cases),
        "failure_reasons": failure_reasons,
        "validation_checks": checks,
        "case_failures": case_failures,
    }
    if resolved_summary_path is not None:
        _write_json(resolved_summary_path, summary)
    return EvalTraceCaseFileValidationResult(summary=summary)


def run_eval_trace_case_promote(
    *,
    sqlite_path: str | Path,
    case_file: str | Path = DEFAULT_EVAL_TRACE_CASE_FILE_PATH,
    trace_id: str | None = None,
    span_id: str | None = None,
    case_id: str | None = None,
    owner: str | None = None,
    risk_level: str | None = None,
    tags: list[str] | None = None,
    assertions: list[str] | None = None,
    expected_output: str | None = None,
    review_condition: str | None = None,
    removal_condition: str | None = None,
    replace: bool = False,
    human_label_status: str = "unlabeled",
    human_labeler: str | None = None,
    human_label_note: str | None = None,
    repo_root: Path = REPO_ROOT,
) -> EvalTraceCasePromoteResult:
    """Promote a stored trace/span into a tracked eval case file.

    The command fails closed: it does not write a case unless the selected trace
    carries artifact references and hashes plus the caller-supplied ownership,
    lifecycle, and assertion metadata required by the milestone contract.
    """

    resolved_sqlite_path = _resolve_path(sqlite_path, repo_root=repo_root)
    resolved_case_file = _resolve_path(case_file, repo_root=repo_root)
    normalized_tags = _normalize_many(tags)
    normalized_assertions = _normalize_many(assertions)
    failure_reasons: list[str] = []
    validation_checks: dict[str, bool] = {}

    _require_bool(
        validation_checks,
        failure_reasons,
        "sqlite_path_exists",
        resolved_sqlite_path.exists(),
    )
    _require_bool(
        validation_checks,
        failure_reasons,
        "selector_present",
        bool(_clean(trace_id) or _clean(span_id)),
    )
    _require_bool(
        validation_checks,
        failure_reasons,
        "owner_surface_present",
        bool(_clean(owner)),
    )
    _require_bool(
        validation_checks,
        failure_reasons,
        "risk_level_allowed",
        _clean(risk_level) in RISK_LEVELS,
    )
    _require_bool(
        validation_checks,
        failure_reasons,
        "tags_present",
        bool(normalized_tags),
    )
    _require_bool(
        validation_checks,
        failure_reasons,
        "assertion_contract_present",
        bool(normalized_assertions or _clean(expected_output)),
    )
    _require_bool(
        validation_checks,
        failure_reasons,
        "review_condition_present",
        bool(_clean(review_condition)),
    )
    _require_bool(
        validation_checks,
        failure_reasons,
        "removal_condition_present",
        bool(_clean(removal_condition)),
    )
    _require_bool(
        validation_checks,
        failure_reasons,
        "human_label_status_allowed",
        human_label_status in HUMAN_LABEL_STATUSES,
    )

    selected: dict[str, Any] | None = None
    if not failure_reasons:
        selected, load_failures = _load_selected_trace(
            resolved_sqlite_path,
            trace_id=_clean(trace_id),
            span_id=_clean(span_id),
        )
        failure_reasons.extend(load_failures)
        validation_checks["trace_selection_found"] = selected is not None

    promoted_case: dict[str, Any] | None = None
    if selected is not None and not failure_reasons:
        source_refs = _collect_source_artifact_refs(selected)
        validation_checks["source_artifact_refs_present"] = bool(source_refs)
        validation_checks["source_artifact_hashes_present"] = all(
            bool(ref.get("sha256")) for ref in source_refs
        )
        if not source_refs:
            failure_reasons.append("source_artifact_refs_present")
        elif not validation_checks["source_artifact_hashes_present"]:
            failure_reasons.append("source_artifact_hashes_present")
        else:
            effective_case_id = _clean(case_id) or _stable_case_id(
                selected["trace"]["trace_id"],
                selected.get("span", {}).get("span_id"),
            )
            promoted_case = _build_case(
                case_id=effective_case_id,
                selected=selected,
                source_refs=source_refs,
                sqlite_path=resolved_sqlite_path,
                repo_root=repo_root,
                owner=owner or "",
                risk_level=risk_level or "",
                tags=normalized_tags,
                assertions=normalized_assertions,
                expected_output=_clean(expected_output),
                review_condition=review_condition or "",
                removal_condition=removal_condition or "",
                human_label_status=human_label_status,
                human_labeler=_clean(human_labeler),
                human_label_note=_clean(human_label_note),
            )

    case_count = 0
    replaced_existing = False
    wrote_case = False
    if promoted_case is not None and not failure_reasons:
        case_file_payload, read_failures = _read_case_file(resolved_case_file)
        failure_reasons.extend(read_failures)
        if not failure_reasons:
            case_count = len(case_file_payload["cases"])
            matching_index = next(
                (
                    index
                    for index, existing in enumerate(case_file_payload["cases"])
                    if existing.get("case_id") == promoted_case["case_id"]
                ),
                None,
            )
            if matching_index is not None and not replace:
                failure_reasons.append("case_id_already_exists")
            else:
                if matching_index is not None:
                    case_file_payload["cases"][matching_index] = promoted_case
                    replaced_existing = True
                else:
                    case_file_payload["cases"].append(promoted_case)
                case_file_payload["cases"] = sorted(
                    case_file_payload["cases"], key=lambda item: item["case_id"]
                )
                case_count = len(case_file_payload["cases"])
                _write_json(resolved_case_file, case_file_payload)
                wrote_case = True

    passed = not failure_reasons and wrote_case
    selected_trace_id = (
        selected["trace"]["trace_id"] if selected is not None else _clean(trace_id)
    )
    selected_span_id = (
        selected.get("span", {}).get("span_id") if selected is not None else _clean(span_id)
    )
    summary = {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "command_succeeded": passed,
        "passed": passed,
        "case_file_path": _display_path(resolved_case_file, repo_root=repo_root),
        "case_id": promoted_case["case_id"] if promoted_case is not None else _clean(case_id),
        "trace_id": selected_trace_id,
        "span_id": selected_span_id,
        "case_count": case_count,
        "replaced_existing": replaced_existing,
        "wrote_case": wrote_case,
        "failure_reasons": failure_reasons,
        "validation_checks": validation_checks,
    }
    return EvalTraceCasePromoteResult(summary=summary)


def _load_selected_trace(
    sqlite_path: Path,
    *,
    trace_id: str | None,
    span_id: str | None,
) -> tuple[dict[str, Any] | None, list[str]]:
    failures: list[str] = []
    try:
        with sqlite3.connect(sqlite_path) as conn:
            conn.row_factory = sqlite3.Row
            selected_trace_id = trace_id
            span: dict[str, Any] | None = None
            if span_id:
                row = conn.execute(
                    "SELECT * FROM trace_spans WHERE span_id = ?",
                    (span_id,),
                ).fetchone()
                if row is None:
                    failures.append("span_id_not_found")
                    return None, failures
                span = _row_to_dict(row)
                selected_trace_id = selected_trace_id or span.get("trace_id")
                if trace_id and span.get("trace_id") != trace_id:
                    failures.append("span_trace_id_mismatch")
                    return None, failures

            if not selected_trace_id:
                failures.append("trace_id_not_resolved")
                return None, failures

            trace_row = conn.execute(
                "SELECT * FROM trace_runs WHERE trace_id = ?",
                (selected_trace_id,),
            ).fetchone()
            if trace_row is None:
                failures.append("trace_id_not_found")
                return None, failures
            trace = _row_to_dict(trace_row)

            result_row = conn.execute(
                "SELECT * FROM system_eval_case_results WHERE trace_id = ?",
                (selected_trace_id,),
            ).fetchone()
            result = _row_to_dict(result_row) if result_row is not None else {}

            eval_run: dict[str, Any] = {}
            eval_case: dict[str, Any] = {}
            scores: list[dict[str, Any]] = []
            if result:
                run_row = conn.execute(
                    "SELECT * FROM system_eval_runs WHERE eval_run_id = ?",
                    (result.get("eval_run_id"),),
                ).fetchone()
                case_row = conn.execute(
                    "SELECT * FROM system_eval_cases WHERE eval_case_id = ?",
                    (result.get("eval_case_id"),),
                ).fetchone()
                eval_run = _row_to_dict(run_row) if run_row is not None else {}
                eval_case = _row_to_dict(case_row) if case_row is not None else {}
                score_rows = conn.execute(
                    """
                    SELECT *
                    FROM system_eval_scores
                    WHERE eval_case_result_id = ?
                    ORDER BY score_name
                    """,
                    (result.get("eval_case_result_id"),),
                ).fetchall()
                scores = [_row_to_dict(row) for row in score_rows]
            else:
                failures.append("eval_case_result_not_found")

            return {
                "trace": trace,
                "span": span or {},
                "eval_result": result,
                "eval_run": eval_run,
                "eval_case": eval_case,
                "scores": scores,
            }, failures
    except sqlite3.DatabaseError as exc:
        return None, [f"sqlite_error:{exc}"]


def _build_case(
    *,
    case_id: str,
    selected: dict[str, Any],
    source_refs: list[dict[str, Any]],
    sqlite_path: Path,
    repo_root: Path,
    owner: str,
    risk_level: str,
    tags: list[str],
    assertions: list[str],
    expected_output: str | None,
    review_condition: str,
    removal_condition: str,
    human_label_status: str,
    human_labeler: str | None,
    human_label_note: str | None,
) -> dict[str, Any]:
    trace = selected["trace"]
    span = selected.get("span", {})
    eval_run = selected.get("eval_run", {})
    eval_case = selected.get("eval_case", {})
    eval_result = selected.get("eval_result", {})
    scores = selected.get("scores", [])
    source_record_ids = _dedupe(
        _json_list(eval_run.get("source_record_ids_json"))
        + [
            item
            for score in scores
            for item in _json_list(_json_value(score.get("evidence_refs_json")).get("source_record_ids"))
        ]
    )
    citation_labels = _dedupe(
        [
            item
            for score in scores
            for item in _json_list(_json_value(score.get("evidence_refs_json")).get("citation_labels"))
        ]
    )
    score_names = _dedupe([score.get("score_name") for score in scores if score.get("score_name")])

    return {
        "schema_version": CASE_SCHEMA_VERSION,
        "case_id": case_id,
        "case_version": "1.0.0",
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "source_trace": {
            "sqlite_path": _display_path(sqlite_path, repo_root=repo_root),
            "trace_id": trace.get("trace_id"),
            "span_id": span.get("span_id"),
            "trace_kind": trace.get("trace_kind"),
            "span_kind": span.get("span_kind"),
            "span_name": span.get("span_name") or span.get("name"),
            "eval_run_id": eval_result.get("eval_run_id"),
            "eval_case_id": eval_result.get("eval_case_id"),
            "eval_case_result_id": eval_result.get("eval_case_result_id"),
            "eval_name": eval_run.get("eval_name"),
            "eval_case_name": eval_case.get("case_name"),
            "score_names": score_names,
            "source_artifact_refs": source_refs,
            "source_record_ids": source_record_ids,
            "citation_labels": citation_labels,
        },
        "assertion_contract": {
            "expected_output": expected_output,
            "assertions": assertions,
            "deterministic_scorers": _deterministic_scorers(source_refs, score_names),
            "llm_judge": {
                "status": "reserved_deferred",
                "requires_approved_milestone": True,
                "required_before_enablement": [
                    "model_identity",
                    "prompt_hash",
                    "rubric_hash",
                    "temperature",
                    "calibration_examples",
                    "precision_recall_against_human_labels",
                ],
            },
        },
        "owner_surface": owner,
        "risk_level": risk_level,
        "tags": tags,
        "lifecycle": {
            "review_condition": review_condition,
            "removal_condition": removal_condition,
        },
        "human_label": {
            "status": human_label_status,
            "labeler": human_labeler,
            "labels": [],
            "note": human_label_note,
            "reviewed_at": None,
        },
    }


def _collect_source_artifact_refs(selected: dict[str, Any]) -> list[dict[str, Any]]:
    trace = selected["trace"]
    span = selected.get("span", {})
    eval_run = selected.get("eval_run", {})
    scores = selected.get("scores", [])
    refs: list[dict[str, Any]] = []
    trace_artifacts = _json_list(trace.get("artifact_refs_json"))
    trace_hash = trace.get("output_hash") or trace.get("input_hash")
    for artifact_ref in trace_artifacts:
        if isinstance(artifact_ref, dict):
            _append_ref(
                refs,
                artifact_ref.get("path") or artifact_ref.get("artifact_ref"),
                artifact_ref.get("sha256") or trace_hash,
                artifact_ref.get("source_ref_kind"),
                artifact_ref.get("source_ref_id"),
            )
        else:
            _append_ref(refs, artifact_ref, trace_hash, None, None)

    span_attrs = _json_value(span.get("attributes_json"))
    _append_ref(
        refs,
        span_attrs.get("artifact_ref") or span_attrs.get("path"),
        span_attrs.get("sha256")
        or span_attrs.get("artifact_sha256")
        or span_attrs.get("current_artifact_sha256"),
        span_attrs.get("source_ref_kind"),
        span_attrs.get("source_ref_id"),
    )
    _append_ref(
        refs,
        eval_run.get("origin_artifact_ref"),
        eval_run.get("origin_artifact_sha256") or eval_run.get("current_artifact_sha256"),
        "origin_artifact",
        eval_run.get("source_set_id"),
    )

    for score in scores:
        evidence = _json_value(score.get("evidence_refs_json"))
        _append_ref(
            refs,
            evidence.get("origin_artifact_ref"),
            evidence.get("origin_artifact_sha256")
            or evidence.get("current_artifact_sha256"),
            "score_evidence",
            score.get("score_name"),
        )

    deduped: dict[tuple[str, str, str | None, str | None], dict[str, Any]] = {}
    for ref in refs:
        key = (
            str(ref.get("artifact_ref")),
            str(ref.get("sha256")),
            ref.get("source_ref_kind"),
            ref.get("source_ref_id"),
        )
        deduped[key] = ref
    return list(deduped.values())


def _deterministic_scorers(
    source_refs: list[dict[str, Any]],
    score_names: list[str],
) -> list[dict[str, Any]]:
    return [
        {
            "score_name": "retrieval",
            "score_kind": "retrieval",
            "status": "contract_defined",
            "required": True,
            "inputs": ["query", "retrieved_source_artifact_refs", "citation_labels"],
            "source_artifact_refs": source_refs,
            "store_score_names": score_names,
        },
        {
            "score_name": "groundedness_cited_source_spans",
            "score_kind": "groundedness",
            "status": "contract_defined",
            "required": True,
            "inputs": ["answer", "cited_source_spans", "source_artifact_hashes"],
            "source_artifact_refs": source_refs,
        },
        {
            "score_name": "trace_integrity",
            "score_kind": "trace_integrity",
            "status": "contract_defined",
            "required": True,
            "inputs": ["trace_id", "span_id", "parent_span_id", "artifact_hashes"],
            "source_artifact_refs": source_refs,
        },
        {
            "score_name": "latency",
            "score_kind": "latency_placeholder",
            "status": "placeholder_contract",
            "required": False,
            "units": "milliseconds",
        },
        {
            "score_name": "cost",
            "score_kind": "cost_placeholder",
            "status": "placeholder_contract",
            "required": False,
            "units": "usd",
        },
    ]


def _read_case_file(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {
            "schema_version": CASE_FILE_SCHEMA_VERSION,
            "case_file_id": path.stem,
            "case_file_version": "1.0.0",
            "cases": [],
        }, []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"case_file_read_error:{exc}"]
    if payload.get("schema_version") != CASE_FILE_SCHEMA_VERSION:
        return {}, ["case_file_schema_version_mismatch"]
    cases = payload.get("cases")
    if not isinstance(cases, list):
        return {}, ["case_file_cases_not_list"]
    return payload, []


def _promoted_case_failure_reasons(case: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    source_trace = _json_value(case.get("source_trace"))
    assertion_contract = _json_value(case.get("assertion_contract"))
    lifecycle = _json_value(case.get("lifecycle"))
    human_label = _json_value(case.get("human_label"))
    source_refs = _json_list(source_trace.get("source_artifact_refs"))
    deterministic_scorers = _json_list(assertion_contract.get("deterministic_scorers"))
    scorer_names = {
        str(scorer.get("score_name"))
        for scorer in deterministic_scorers
        if isinstance(scorer, dict) and scorer.get("score_name")
    }
    llm_judge = _json_value(assertion_contract.get("llm_judge"))
    sqlite_path = _clean(source_trace.get("sqlite_path"))
    if case.get("schema_version") != CASE_SCHEMA_VERSION:
        failures.append("case_schema_version")
    if not _clean(case.get("case_id")):
        failures.append("case_id_present")
    if not _clean(source_trace.get("trace_id")):
        failures.append("trace_id_present")
    if sqlite_path and Path(sqlite_path).is_absolute():
        failures.append("sqlite_path_relative")
    if not source_refs:
        failures.append("source_artifact_refs_present")
    if any(
        not isinstance(ref, dict) or not _clean(ref.get("artifact_ref")) or not _clean(ref.get("sha256"))
        for ref in source_refs
    ):
        failures.append("source_artifact_refs_have_hashes")
    if not _clean(case.get("owner_surface")):
        failures.append("owner_surface_present")
    if _clean(case.get("risk_level")) not in RISK_LEVELS:
        failures.append("risk_level_allowed")
    if not _json_list(case.get("tags")):
        failures.append("tags_present")
    if not (
        _json_list(assertion_contract.get("assertions"))
        or _clean(assertion_contract.get("expected_output"))
    ):
        failures.append("assertion_contract_present")
    missing_scorers = REQUIRED_DETERMINISTIC_SCORERS - scorer_names
    if missing_scorers:
        failures.append("required_deterministic_scorers_present")
    if llm_judge.get("status") != "reserved_deferred":
        failures.append("llm_judge_reserved")
    if llm_judge.get("requires_approved_milestone") is not True:
        failures.append("llm_judge_requires_approved_milestone")
    if not _clean(lifecycle.get("review_condition")):
        failures.append("review_condition_present")
    if not _clean(lifecycle.get("removal_condition")):
        failures.append("removal_condition_present")
    if human_label.get("status") not in HUMAN_LABEL_STATUSES:
        failures.append("human_label_status_allowed")
    return sorted(set(failures))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _append_ref(
    refs: list[dict[str, Any]],
    artifact_ref: Any,
    sha256: Any,
    source_ref_kind: Any,
    source_ref_id: Any,
) -> None:
    artifact = _clean(artifact_ref)
    digest = _clean(sha256)
    if not artifact:
        return
    refs.append(
        {
            "artifact_ref": artifact,
            "sha256": digest,
            "source_ref_kind": _clean(source_ref_kind),
            "source_ref_id": _clean(source_ref_id),
        }
    )


def _stable_case_id(trace_id: str, span_id: str | None) -> str:
    digest = hashlib.sha256(f"{trace_id}:{span_id or ''}".encode("utf-8")).hexdigest()
    return f"eval-trace-case-{digest[:12]}"


def _resolve_path(path: str | Path, *, repo_root: Path) -> Path:
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = repo_root / resolved
    return resolved


def _display_path(path: Path, *, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any]:
    return {} if row is None else dict(row)


def _json_value(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    try:
        payload = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _json_list(raw: Any) -> list[Any]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        return [raw]
    if isinstance(raw, str):
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return [raw] if raw else []
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            return [payload]
        return [payload] if payload else []
    return [raw]


def _normalize_many(values: list[str] | None) -> list[str]:
    return _dedupe(_clean(value) for value in values or [])


def _dedupe(values: Any) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        cleaned = _clean(value)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            deduped.append(cleaned)
    return deduped


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _require_bool(
    validation_checks: dict[str, bool],
    failure_reasons: list[str],
    key: str,
    passed: bool,
) -> None:
    validation_checks[key] = passed
    if not passed:
        failure_reasons.append(key)
