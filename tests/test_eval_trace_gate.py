from __future__ import annotations

from pathlib import Path
import json
import sqlite3

from tests.test_eval_trace_inventory import _write_review_fixture
from usfs_r1_ea_sources.eval_trace_contract import DEFAULT_EVAL_TRACE_CONTRACT_PATH
from usfs_r1_ea_sources.eval_trace_gate import EVAL_TRACE_GATE_SCHEMA_VERSION
from usfs_r1_ea_sources.eval_trace_gate import build_eval_trace_gate_phase
from usfs_r1_ea_sources.eval_trace_inventory import run_eval_trace_inventory
from usfs_r1_ea_sources.eval_trace_store import run_eval_trace_store_build


def test_eval_trace_gate_reports_optional_matching_store_without_blocking(
    tmp_path: Path,
) -> None:
    fixture = _write_review_fixture(tmp_path)
    _write_default_inventory_and_store(tmp_path, fixture)

    result = build_eval_trace_gate_phase(
        output_dir=fixture["output_dir"],
        source_set_id=str(fixture["source_set_id"]),
        review_id=str(fixture["review_id"]),
        repo_root=tmp_path,
    )

    assert result.phase is not None
    assert result.phase["passed"] is True
    assert result.phase["reviewer_ready"] is True
    assert result.status["schema_version"] == EVAL_TRACE_GATE_SCHEMA_VERSION
    assert result.status["mode"] == "optional"
    assert result.status["evidence_status"] == "passed"
    assert result.status["inventory"]["target_matches"] is True
    assert result.status["store"]["target_matches"] is True


def test_eval_trace_gate_fails_closed_for_ratcheted_missing_artifacts(
    tmp_path: Path,
) -> None:
    result = build_eval_trace_gate_phase(
        output_dir=tmp_path / "source_library",
        source_set_id="source-set-f70ea11e04ae3d53",
        review_id="west-reservoir-67436",
    )

    assert result.phase is not None
    assert result.phase["passed"] is False
    assert result.status["mode"] == "ratcheted"
    assert result.status["ratchet_scope_reasons"] == ["review_id"]
    assert result.status["failure_reasons"] == [
        "eval_trace_inventory_missing",
        "eval_trace_store_missing",
    ]


def test_eval_trace_gate_fails_ratcheted_stale_inventory(
    tmp_path: Path,
) -> None:
    fixture = _write_review_fixture(tmp_path)
    inventory_path = _write_default_inventory(tmp_path, fixture)
    Path(fixture["retrieval_trace_path"]).write_text('{"trace_id":"changed"}\n', encoding="utf-8")

    result = build_eval_trace_gate_phase(
        output_dir=fixture["output_dir"],
        source_set_id=str(fixture["source_set_id"]),
        review_id=str(fixture["review_id"]),
        contract_path=_ratchet_contract(tmp_path, str(fixture["review_id"])),
        inventory_path=inventory_path,
        repo_root=tmp_path,
    )

    assert result.phase is not None
    assert result.phase["passed"] is False
    assert "eval_trace_inventory_stale" in result.status["failure_reasons"]
    assert "eval_trace_store_missing" in result.status["failure_reasons"]


def test_eval_trace_gate_fails_ratcheted_stale_store(
    tmp_path: Path,
) -> None:
    fixture = _write_review_fixture(tmp_path)
    _, sqlite_path = _write_default_inventory_and_store(tmp_path, fixture)
    with sqlite3.connect(sqlite_path) as connection:
        connection.execute(
            "UPDATE system_eval_runs SET current_artifact_sha256 = ?",
            ("0" * 64,),
        )

    result = build_eval_trace_gate_phase(
        output_dir=fixture["output_dir"],
        source_set_id=str(fixture["source_set_id"]),
        review_id=str(fixture["review_id"]),
        contract_path=_ratchet_contract(tmp_path, str(fixture["review_id"])),
        repo_root=tmp_path,
    )

    assert result.phase is not None
    assert result.phase["passed"] is False
    assert "eval_trace_store_stale" in result.status["failure_reasons"]


def test_eval_trace_gate_allows_phase_eval_self_reference_hash_refresh(
    tmp_path: Path,
) -> None:
    fixture = _write_review_fixture(tmp_path)
    _write_default_inventory_and_store(tmp_path, fixture)
    phase_eval_path = Path(fixture["review_dir"]) / "phase_eval_results.json"
    phase_eval = json.loads(phase_eval_path.read_text(encoding="utf-8"))
    phase_eval["created_at"] = "later"
    phase_eval_path.write_text(json.dumps(phase_eval, indent=2, sort_keys=True) + "\n")

    result = build_eval_trace_gate_phase(
        output_dir=fixture["output_dir"],
        source_set_id=str(fixture["source_set_id"]),
        review_id=str(fixture["review_id"]),
        contract_path=_ratchet_contract(tmp_path, str(fixture["review_id"])),
        repo_root=tmp_path,
    )

    assert result.phase is not None
    assert result.phase["passed"] is True
    assert result.status["failure_reasons"] == []


def test_eval_trace_gate_fails_ratcheted_store_missing_trace_rows(
    tmp_path: Path,
) -> None:
    fixture = _write_review_fixture(tmp_path)
    _, sqlite_path = _write_default_inventory_and_store(tmp_path, fixture)
    with sqlite3.connect(sqlite_path) as connection:
        connection.execute("DELETE FROM trace_spans")

    result = build_eval_trace_gate_phase(
        output_dir=fixture["output_dir"],
        source_set_id=str(fixture["source_set_id"]),
        review_id=str(fixture["review_id"]),
        contract_path=_ratchet_contract(tmp_path, str(fixture["review_id"])),
        repo_root=tmp_path,
    )

    assert result.phase is not None
    assert result.phase["passed"] is False
    assert "eval_trace_store_missing_trace_rows" in result.status["failure_reasons"]


def test_eval_trace_gate_fails_ratcheted_store_missing_eval_rows(
    tmp_path: Path,
) -> None:
    fixture = _write_review_fixture(tmp_path)
    _, sqlite_path = _write_default_inventory_and_store(tmp_path, fixture)
    with sqlite3.connect(sqlite_path) as connection:
        connection.execute("DELETE FROM system_eval_scores")

    result = build_eval_trace_gate_phase(
        output_dir=fixture["output_dir"],
        source_set_id=str(fixture["source_set_id"]),
        review_id=str(fixture["review_id"]),
        contract_path=_ratchet_contract(tmp_path, str(fixture["review_id"])),
        repo_root=tmp_path,
    )

    assert result.phase is not None
    assert result.phase["passed"] is False
    assert "eval_trace_store_missing_eval_rows" in result.status["failure_reasons"]


def _write_default_inventory_and_store(
    tmp_path: Path,
    fixture: dict[str, object],
) -> tuple[Path, Path]:
    inventory_path = _write_default_inventory(tmp_path, fixture)
    sqlite_path = (
        Path(fixture["output_dir"])
        / "evaluations"
        / "eval_trace"
        / "system_eval_trace.sqlite"
    )
    run_eval_trace_store_build(
        inventory_path=inventory_path,
        sqlite_path=sqlite_path,
        repo_root=tmp_path,
    )
    return inventory_path, sqlite_path


def _write_default_inventory(tmp_path: Path, fixture: dict[str, object]) -> Path:
    inventory_path = (
        Path(fixture["output_dir"])
        / "evaluations"
        / "eval_trace_inventory"
        / "eval_trace_inventory_results.json"
    )
    run_eval_trace_inventory(
        output_dir=Path(fixture["output_dir"]),
        source_set_id=str(fixture["source_set_id"]),
        review_id=str(fixture["review_id"]),
        results_path=inventory_path,
        repo_root=tmp_path,
    )
    return inventory_path


def _ratchet_contract(tmp_path: Path, review_id: str) -> Path:
    contract = json.loads(DEFAULT_EVAL_TRACE_CONTRACT_PATH.read_text(encoding="utf-8"))
    contract["ratchet_scopes"]["enabled_review_ids"] = [review_id]
    contract_path = tmp_path / "config" / "eval_trace_inventory_contract_v1.json"
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n")
    return contract_path
