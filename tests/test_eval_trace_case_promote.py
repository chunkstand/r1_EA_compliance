from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from tests.test_eval_trace_export import _write_store
from usfs_r1_ea_sources.eval_trace_case_promote import (
    CASE_FILE_SCHEMA_VERSION,
    CASE_SCHEMA_VERSION,
    DEFAULT_EVAL_TRACE_CASE_FILE_PATH,
    SUMMARY_SCHEMA_VERSION,
    run_eval_trace_case_promote,
    validate_eval_trace_case_file,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
TRACKED_CASE_FILE = REPO_ROOT / DEFAULT_EVAL_TRACE_CASE_FILE_PATH


def test_committed_case_file_contains_promoted_west_reservoir_trace_case() -> None:
    payload = json.loads(TRACKED_CASE_FILE.read_text(encoding="utf-8"))

    assert payload["schema_version"] == CASE_FILE_SCHEMA_VERSION
    cases = {case["case_id"]: case for case in payload["cases"]}
    case = cases["west-reservoir-applicability-retrieval-trace-case-001"]

    assert case["schema_version"] == CASE_SCHEMA_VERSION
    assert case["owner_surface"] == "applicability_eval"
    assert case["risk_level"] == "high"
    assert case["source_trace"]["sqlite_path"] == (
        "source_library/evaluations/eval_trace/system_eval_trace.sqlite"
    )
    assert case["source_trace"]["trace_id"] == "524a4a9ad3229869b77fc39d"
    assert case["source_trace"]["span_id"] == "24737cdb71be82ed8bc0a0d3"
    assert case["source_trace"]["trace_kind"] == "applicability_retrieval"
    assert case["source_trace"]["span_kind"] == "retrieve"
    assert case["source_trace"]["source_artifact_refs"]
    assert all(ref["sha256"] for ref in case["source_trace"]["source_artifact_refs"])
    assert "source-set-f70ea11e04ae3d53" in {
        ref["source_ref_id"] for ref in case["source_trace"]["source_artifact_refs"]
    }
    assert case["human_label"]["status"] == "unlabeled"
    assert case["assertion_contract"]["llm_judge"]["status"] == "reserved_deferred"


def test_committed_case_file_validation_passes() -> None:
    summary = validate_eval_trace_case_file(case_file=TRACKED_CASE_FILE).summary

    assert summary["schema_version"] == "eval-trace-case-file-validation-summary-v1"
    assert summary["passed"] is True
    assert summary["command_succeeded"] is True
    assert summary["case_count"] >= 1
    assert summary["failure_reasons"] == []
    assert summary["case_failures"] == []


def test_case_file_validation_writes_summary_path(tmp_path: Path) -> None:
    source_payload = json.loads(TRACKED_CASE_FILE.read_text(encoding="utf-8"))
    case_file = tmp_path / "config/eval_trace_cases/system_eval_trace_cases_v1.json"
    summary_path = tmp_path / "source_library/evaluations/eval_trace/case_file_validation.json"
    case_file.parent.mkdir(parents=True)
    case_file.write_text(json.dumps(source_payload), encoding="utf-8")

    summary = validate_eval_trace_case_file(
        case_file=case_file,
        summary_path=summary_path,
        repo_root=tmp_path,
    ).summary

    assert summary["passed"] is True
    assert summary["summary_path"] == (
        "source_library/evaluations/eval_trace/case_file_validation.json"
    )
    written = json.loads(summary_path.read_text(encoding="utf-8"))
    assert written == summary


def test_case_promote_writes_versioned_case_with_required_contracts(
    tmp_path: Path,
) -> None:
    sqlite_path = _write_store(tmp_path)
    trace_id, span_id = _source_backed_span(sqlite_path)
    case_file = tmp_path / "config/eval_trace_cases/system_eval_trace_cases_v1.json"

    summary = run_eval_trace_case_promote(
        sqlite_path=sqlite_path,
        case_file=case_file,
        trace_id=trace_id,
        span_id=span_id,
        case_id="west-reservoir-trace-case-001",
        owner="eval_trace_case_promote",
        risk_level="high",
        tags=["first-class-eval-trace", "west-reservoir"],
        assertions=[
            "retrieved citations remain source-backed",
            "trace span keeps parent/child provenance",
        ],
        expected_output="deterministic scorer contract remains replayable",
        review_condition="review when scorer schema changes",
        removal_condition="remove only after superseding adjudicated case exists",
        repo_root=tmp_path,
    ).summary

    assert summary["schema_version"] == SUMMARY_SCHEMA_VERSION
    assert summary["passed"] is True
    assert summary["command_succeeded"] is True
    assert summary["case_id"] == "west-reservoir-trace-case-001"
    assert summary["case_file_path"] == (
        "config/eval_trace_cases/system_eval_trace_cases_v1.json"
    )
    assert summary["case_count"] == 1

    payload = json.loads(case_file.read_text(encoding="utf-8"))
    assert payload["schema_version"] == CASE_FILE_SCHEMA_VERSION
    [case] = payload["cases"]
    assert case["schema_version"] == CASE_SCHEMA_VERSION
    assert case["case_id"] == "west-reservoir-trace-case-001"
    assert case["owner_surface"] == "eval_trace_case_promote"
    assert case["risk_level"] == "high"
    assert case["source_trace"]["trace_id"] == trace_id
    assert case["source_trace"]["span_id"] == span_id
    assert case["source_trace"]["source_artifact_refs"]
    assert all(ref["sha256"] for ref in case["source_trace"]["source_artifact_refs"])
    assert case["source_trace"]["sqlite_path"] == str(sqlite_path.relative_to(tmp_path))
    assert case["human_label"] == {
        "labeler": None,
        "labels": [],
        "note": None,
        "reviewed_at": None,
        "status": "unlabeled",
    }

    scorer_names = {
        scorer["score_name"]
        for scorer in case["assertion_contract"]["deterministic_scorers"]
    }
    assert {
        "retrieval",
        "groundedness_cited_source_spans",
        "trace_integrity",
        "latency",
        "cost",
    }.issubset(scorer_names)
    assert case["assertion_contract"]["llm_judge"] == {
        "required_before_enablement": [
            "model_identity",
            "prompt_hash",
            "rubric_hash",
            "temperature",
            "calibration_examples",
            "precision_recall_against_human_labels",
        ],
        "requires_approved_milestone": True,
        "status": "reserved_deferred",
    }


def test_case_file_validation_fails_closed_for_empty_default_contract(
    tmp_path: Path,
) -> None:
    case_file = tmp_path / "cases.json"
    case_file.write_text(
        json.dumps(
            {
                "schema_version": CASE_FILE_SCHEMA_VERSION,
                "case_file_id": "empty",
                "case_file_version": "1.0.0",
                "cases": [],
            }
        ),
        encoding="utf-8",
    )

    summary = validate_eval_trace_case_file(case_file=case_file, repo_root=tmp_path).summary

    assert summary["passed"] is False
    assert summary["failure_reasons"] == ["case_count_present"]
    assert summary["case_count"] == 0


def test_case_file_validation_rejects_absolute_sqlite_paths(tmp_path: Path) -> None:
    sqlite_path = _write_store(tmp_path)
    trace_id, span_id = _source_backed_span(sqlite_path)
    case_file = tmp_path / "cases.json"
    result = run_eval_trace_case_promote(
        sqlite_path=sqlite_path,
        case_file=case_file,
        trace_id=trace_id,
        span_id=span_id,
        case_id="absolute-path-case",
        owner="eval_trace_case_promote",
        risk_level="medium",
        tags=["first-class-eval-trace"],
        assertions=["trace stays linked to source artifacts"],
        review_condition="review when trace contract changes",
        removal_condition="remove when superseded",
        repo_root=tmp_path,
    )
    assert result.summary["passed"] is True
    payload = json.loads(case_file.read_text(encoding="utf-8"))
    payload["cases"][0]["source_trace"]["sqlite_path"] = str(sqlite_path)
    case_file.write_text(json.dumps(payload), encoding="utf-8")

    summary = validate_eval_trace_case_file(case_file=case_file, repo_root=tmp_path).summary

    assert summary["passed"] is False
    assert summary["failure_reasons"] == ["promoted_cases_valid"]
    assert summary["case_failures"] == [
        {
            "case_id": "absolute-path-case",
            "failure_reasons": ["sqlite_path_relative"],
        }
    ]


def test_case_promote_fails_closed_without_required_metadata(tmp_path: Path) -> None:
    sqlite_path = _write_store(tmp_path)
    trace_id, span_id = _source_backed_span(sqlite_path)
    case_file = tmp_path / "cases.json"

    summary = run_eval_trace_case_promote(
        sqlite_path=sqlite_path,
        case_file=case_file,
        trace_id=trace_id,
        span_id=span_id,
        owner="eval_trace_case_promote",
        risk_level="high",
        tags=[],
        assertions=["trace integrity remains replayable"],
        review_condition="review when store schema changes",
        removal_condition="remove when superseded",
        repo_root=tmp_path,
    ).summary

    assert summary["passed"] is False
    assert summary["command_succeeded"] is False
    assert summary["wrote_case"] is False
    assert summary["failure_reasons"] == ["tags_present"]
    assert not case_file.exists()


def test_case_promote_blocks_duplicate_case_without_replace(tmp_path: Path) -> None:
    sqlite_path = _write_store(tmp_path)
    trace_id, span_id = _source_backed_span(sqlite_path)
    case_file = tmp_path / "cases.json"
    kwargs = {
        "sqlite_path": sqlite_path,
        "case_file": case_file,
        "trace_id": trace_id,
        "span_id": span_id,
        "case_id": "duplicate-case",
        "owner": "eval_trace_case_promote",
        "risk_level": "medium",
        "tags": ["first-class-eval-trace"],
        "assertions": ["trace stays linked to source artifacts"],
        "review_condition": "review when trace contract changes",
        "removal_condition": "remove when superseded",
        "repo_root": tmp_path,
    }

    first = run_eval_trace_case_promote(**kwargs).summary
    second = run_eval_trace_case_promote(**kwargs).summary

    assert first["passed"] is True
    assert second["passed"] is False
    assert second["failure_reasons"] == ["case_id_already_exists"]
    assert second["wrote_case"] is False
    assert len(json.loads(case_file.read_text(encoding="utf-8"))["cases"]) == 1


def _source_backed_span(sqlite_path: Path) -> tuple[str, str]:
    with sqlite3.connect(sqlite_path) as connection:
        row = connection.execute(
            """
            SELECT trace_id, span_id
            FROM trace_spans
            WHERE source_ref_id IS NOT NULL
            ORDER BY span_id
            LIMIT 1
            """
        ).fetchone()
    assert row is not None
    return row[0], row[1]
