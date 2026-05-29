from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from tests.test_eval_trace_export import _write_store
from usfs_r1_ea_sources.eval_trace_case_promote import (
    CASE_FILE_SCHEMA_VERSION,
    CASE_SCHEMA_VERSION,
    SUMMARY_SCHEMA_VERSION,
    run_eval_trace_case_promote,
)


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
