from __future__ import annotations

from pathlib import Path
import json
import sqlite3

from tests.test_eval_trace_inventory import _write_review_fixture
from usfs_r1_ea_sources.eval_trace_inventory import run_eval_trace_inventory
from usfs_r1_ea_sources.eval_trace_store import STORE_SUMMARY_SCHEMA_VERSION
from usfs_r1_ea_sources.eval_trace_store import run_eval_trace_store_build


STORE_TABLES = (
    "system_eval_runs",
    "system_eval_cases",
    "system_eval_case_results",
    "system_eval_scores",
    "trace_runs",
    "trace_spans",
)


def test_store_build_creates_contract_tables_and_rows(tmp_path: Path) -> None:
    inventory_path = _write_inventory(tmp_path)
    sqlite_path = tmp_path / "system_eval_trace.sqlite"
    summary_path = tmp_path / "system_eval_trace_summary.json"

    result = run_eval_trace_store_build(
        inventory_path=inventory_path,
        sqlite_path=sqlite_path,
        summary_path=summary_path,
        repo_root=tmp_path,
    )
    summary = result.summary

    assert summary["schema_version"] == STORE_SUMMARY_SCHEMA_VERSION
    assert summary["passed"] is True
    assert summary["command_succeeded"] is True
    assert summary["blocked_eval_run_count"] == 0
    assert summary["missing_required_link_count"] == 0
    assert all(summary["row_counts"][table] > 0 for table in STORE_TABLES)
    assert json.loads(summary_path.read_text(encoding="utf-8")) == summary

    with sqlite3.connect(sqlite_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        assert set(STORE_TABLES).issubset(tables)
        run_row = connection.execute(
            """
            SELECT contract_id, contract_version, catalog_ref, replay_context_ref,
                   source_record_ids_json
            FROM system_eval_runs
            WHERE eval_name = 'source_catalog'
            """
        ).fetchone()

    assert run_row[0] == "first-class-eval-trace-inventory-contract"
    assert run_row[1] == "0.1.0"
    assert run_row[2] == "source_library/runs/fixture-catalog/catalog_gate"
    assert run_row[3] == "config/replay_contexts/review-a.json"
    assert json.loads(run_row[4]) == ["SRC-001"]


def test_store_rebuild_is_idempotent_without_duplicate_rows(tmp_path: Path) -> None:
    inventory_path = _write_inventory(tmp_path)
    sqlite_path = tmp_path / "system_eval_trace.sqlite"

    first = run_eval_trace_store_build(
        inventory_path=inventory_path,
        sqlite_path=sqlite_path,
        repo_root=tmp_path,
    ).summary
    first_snapshot = _store_snapshot(sqlite_path)
    second = run_eval_trace_store_build(
        inventory_path=inventory_path,
        sqlite_path=sqlite_path,
        repo_root=tmp_path,
    ).summary
    second_snapshot = _store_snapshot(sqlite_path)

    assert first["row_counts"] == second["row_counts"]
    assert first["duplicate_id_counts"] == {table: 0 for table in STORE_TABLES}
    assert second["duplicate_id_counts"] == {table: 0 for table in STORE_TABLES}
    assert first_snapshot == second_snapshot


def test_store_build_flags_deleted_source_artifact_after_inventory(
    tmp_path: Path,
) -> None:
    fixture = _write_review_fixture(tmp_path)
    inventory_path = _write_inventory_from_fixture(tmp_path, fixture)
    (fixture["review_dir"] / "v1_ea_eval_results.json").unlink()

    summary = run_eval_trace_store_build(
        inventory_path=inventory_path,
        sqlite_path=tmp_path / "system_eval_trace.sqlite",
        repo_root=tmp_path,
    ).summary

    assert summary["passed"] is False
    assert summary["source_artifact_deletion_count"] == 1
    assert any(
        run["eval_name"] == "v1_ea_eval"
        and run["failure_reason"] == "missing_origin_artifact"
        for run in summary["blocked_eval_runs"]
    )


def test_store_build_flags_stale_artifact_hash_after_inventory(tmp_path: Path) -> None:
    fixture = _write_review_fixture(tmp_path)
    inventory_path = _write_inventory_from_fixture(tmp_path, fixture)
    fixture["retrieval_trace_path"].write_text('{"trace_id":"changed"}\n', encoding="utf-8")

    summary = run_eval_trace_store_build(
        inventory_path=inventory_path,
        sqlite_path=tmp_path / "system_eval_trace.sqlite",
        repo_root=tmp_path,
    ).summary

    assert summary["passed"] is False
    assert summary["stale_artifact_count"] == 1
    assert any(
        run["eval_name"] == "applicability_trace"
        and run["failure_reason"] == "stale_artifact_hash"
        for run in summary["blocked_eval_runs"]
    )


def test_store_build_allows_phase_eval_trace_gate_bootstrap(tmp_path: Path) -> None:
    fixture = _write_review_fixture(tmp_path)
    phase_eval_path = fixture["review_dir"] / "phase_eval_results.json"
    _write_json(
        phase_eval_path,
        {
            "review_id": fixture["review_id"],
            "source_set_id": fixture["source_set_id"],
            "review_direct_eval_status": "direct_eval_present",
            "passed": False,
            "reviewer_ready": False,
            "blockers": [
                {
                    "phase": "first_class_eval_trace",
                    "reason": "eval_trace_store_stale",
                }
            ],
            "phases": [
                {"name": "evaluation_coverage", "passed": True, "reviewer_ready": True},
                {
                    "name": "first_class_eval_trace",
                    "passed": False,
                    "reviewer_ready": False,
                    "failure_reasons": [
                        "eval_trace_inventory_stale",
                        "eval_trace_store_stale",
                    ],
                },
            ],
        },
    )
    inventory_path = _write_inventory_from_fixture(tmp_path, fixture)

    summary = run_eval_trace_store_build(
        inventory_path=inventory_path,
        sqlite_path=tmp_path / "system_eval_trace.sqlite",
        repo_root=tmp_path,
    ).summary

    assert summary["passed"] is True
    assert summary["blocked_eval_run_count"] == 0


def test_store_build_still_blocks_non_trace_phase_eval_failure(tmp_path: Path) -> None:
    fixture = _write_review_fixture(tmp_path)
    phase_eval_path = fixture["review_dir"] / "phase_eval_results.json"
    _write_json(
        phase_eval_path,
        {
            "review_id": fixture["review_id"],
            "source_set_id": fixture["source_set_id"],
            "review_direct_eval_status": "direct_eval_present",
            "passed": False,
            "reviewer_ready": False,
            "blockers": [{"phase": "evaluation_coverage", "reason": "phase_validation_failed"}],
            "phases": [
                {
                    "name": "evaluation_coverage",
                    "passed": False,
                    "reviewer_ready": False,
                    "failure_reasons": ["phase_validation_failed"],
                }
            ],
        },
    )
    inventory_path = _write_inventory_from_fixture(tmp_path, fixture)

    summary = run_eval_trace_store_build(
        inventory_path=inventory_path,
        sqlite_path=tmp_path / "system_eval_trace.sqlite",
        repo_root=tmp_path,
    ).summary

    assert summary["passed"] is False
    assert any(
        run["eval_name"] == "phase_eval"
        and run["failure_reason"] == "origin_artifact_failed"
        for run in summary["blocked_eval_runs"]
    )


def test_store_build_reports_inventory_missing_required_links(tmp_path: Path) -> None:
    fixture = _write_review_fixture(tmp_path)
    fixture["replay_context_path"].unlink()
    inventory_path = _write_inventory_from_fixture(tmp_path, fixture)

    summary = run_eval_trace_store_build(
        inventory_path=inventory_path,
        sqlite_path=tmp_path / "system_eval_trace.sqlite",
        repo_root=tmp_path,
    ).summary

    assert summary["passed"] is False
    assert summary["inventory_passed"] is False
    assert summary["missing_required_link_count"] > 0
    assert any(
        run["eval_name"] == "replay_context"
        and run["failure_reason"] == "missing_origin_artifact"
        for run in summary["blocked_eval_runs"]
    )


def _write_inventory(tmp_path: Path) -> Path:
    fixture = _write_review_fixture(tmp_path)
    return _write_inventory_from_fixture(tmp_path, fixture)


def _write_inventory_from_fixture(tmp_path: Path, fixture: dict[str, object]) -> Path:
    inventory_path = tmp_path / "eval_trace_inventory.json"
    run_eval_trace_inventory(
        output_dir=fixture["output_dir"],
        source_set_id=str(fixture["source_set_id"]),
        review_id=str(fixture["review_id"]),
        results_path=inventory_path,
        repo_root=tmp_path,
    )
    return inventory_path


def _store_snapshot(sqlite_path: Path) -> dict[str, list[tuple]]:
    snapshot: dict[str, list[tuple]] = {}
    with sqlite3.connect(sqlite_path) as connection:
        for table in STORE_TABLES:
            rows = connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            snapshot[table] = rows
    return snapshot


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
