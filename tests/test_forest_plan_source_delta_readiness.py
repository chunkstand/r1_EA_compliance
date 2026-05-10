from __future__ import annotations

from pathlib import Path
import json
import tempfile

from usfs_r1_ea_sources.forest_plan_source_delta_readiness import (
    build_forest_plan_source_delta_readiness_report,
)
from usfs_r1_ea_sources.workbook import load_r1_forest_plan_document_register


ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "config" / "r1_forest_plan_document_register_draft.csv"
PROFILES = ROOT / "config" / "forest_plan_profiles.json"
BATCH_RUN_ID = "unit-source-delta-batches"


def test_forest_plan_source_delta_readiness_report_passes_sequence_zero_baseline() -> None:
    register = load_r1_forest_plan_document_register(REGISTER)
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        _write_sequence_zero_fixture(output_dir, register=register)

        result = build_forest_plan_source_delta_readiness_report(
            output_dir=output_dir,
            register_path=REGISTER,
            source_delta_batch_run_id=BATCH_RUN_ID,
            forest_plan_profiles_path=PROFILES,
        )

        report = _read_json(result.report_path)
        assert result.summary["passed"] is True
        assert result.markdown_path.exists()
        assert report["register"]["source_delta_count"] == 159
        assert report["register"]["skipped_gap_source_record_ids"] == [
            "R1PLAN-kootenai-nf-18",
            "R1PLAN-nez-perce-clearwater-nfs-18",
        ]
        assert report["scoped_source_delta_catalog"]["source_set_id"] == "source-set-delta-test"
        assert report["active_canonical_catalog"]["source_set_id"] == "source-set-canonical-test"
        assert report["extraction_readiness"]["status"] == "not_started"
        assert report["retrieval_readiness"]["status"] == "not_started"
        assert any(
            unit["official_source_gap_ids"] == ["R1PLAN-kootenai-nf-18"]
            for unit in report["forest_profile_readiness_placeholders"]["forest_units"]
        )


def test_forest_plan_source_delta_readiness_fails_when_scoped_catalog_gate_missing() -> None:
    register = load_r1_forest_plan_document_register(REGISTER)
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        _write_sequence_zero_fixture(output_dir, register=register, write_catalog_gate=False)

        result = build_forest_plan_source_delta_readiness_report(
            output_dir=output_dir,
            register_path=REGISTER,
            source_delta_batch_run_id=BATCH_RUN_ID,
            forest_plan_profiles_path=PROFILES,
        )

        report = _read_json(result.report_path)
        missing_check = _check(report, "source_delta_catalog_gate_artifacts_exist")
        assert result.summary["passed"] is False
        assert missing_check["passed"] is False
        assert any(path.endswith("catalog_gate/source_catalog.jsonl") for path in missing_check["details"]["missing_paths"])


def test_forest_plan_source_delta_readiness_fails_on_stale_catalog_gate_source_ids() -> None:
    register = load_r1_forest_plan_document_register(REGISTER)
    missing_id = register.source_delta_sources[0].source_record_id
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        _write_sequence_zero_fixture(
            output_dir,
            register=register,
            missing_source_delta_id=missing_id,
        )

        result = build_forest_plan_source_delta_readiness_report(
            output_dir=output_dir,
            register_path=REGISTER,
            source_delta_batch_run_id=BATCH_RUN_ID,
            forest_plan_profiles_path=PROFILES,
        )

        report = _read_json(result.report_path)
        stale_check = _check(report, "source_delta_catalog_gate_matches_register")
        assert result.summary["passed"] is False
        assert stale_check["passed"] is False
        assert stale_check["details"]["missing_source_delta_ids"] == [missing_id]


def _write_sequence_zero_fixture(
    output_dir: Path,
    *,
    register,
    write_catalog_gate: bool = True,
    missing_source_delta_id: str | None = None,
) -> None:
    run_dir = output_dir / "runs" / BATCH_RUN_ID
    run_dir.mkdir(parents=True)
    source_delta_ids = [source.source_record_id for source in register.source_delta_sources]
    _write_json(
        run_dir / "summary.json",
        {
            "run_id": BATCH_RUN_ID,
            "all_passed": True,
            "planned_row_count": len(source_delta_ids),
            "batch_count": 1,
            "passed_batch_count": 1,
            "failed_batch_count": 0,
            "needs_repair_batch_count": 0,
            "artifact_count": 158,
            "source_delta_input": register.summary(),
        },
    )
    _write_json(
        run_dir / "batch_ledger.json",
        {
            "run_id": BATCH_RUN_ID,
            "batches": [
                {
                    "batch_id": "unit-batch-001",
                    "status": "passed",
                    "gate_passed": True,
                    "source_record_ids": source_delta_ids,
                }
            ],
        },
    )
    (run_dir / "repair_queue.csv").write_text("batch_id,source_record_id,reason\n", encoding="utf-8")
    if write_catalog_gate:
        catalog_ids = [
            source_id for source_id in source_delta_ids if source_id != missing_source_delta_id
        ]
        _write_catalog_fixture(
            run_dir / "catalog_gate",
            source_set_id="source-set-delta-test",
            source_ids=catalog_ids,
            source_count=len(source_delta_ids),
            artifact_count=158,
            download_batch_run_id=BATCH_RUN_ID,
            source_delta_input=register.summary(),
            source_record_id_filter_count=len(source_delta_ids),
            supplemental_source_count=len(source_delta_ids),
            source_partition_counts={"active_review_corpus": len(source_delta_ids)},
            document_role_counts={"forest_plan_support": len(source_delta_ids)},
        )
    _write_catalog_fixture(
        output_dir / "catalog",
        source_set_id="source-set-canonical-test",
        source_ids=register.catalog_confirmed_source_record_ids,
        source_count=190,
        artifact_count=160,
        download_batch_run_id="canonical-batches",
        source_delta_input=None,
        source_record_id_filter_count=None,
        supplemental_source_count=0,
        source_partition_counts={"active_review_corpus": 189, "candidate_blocked_source": 1},
        document_role_counts={"forest_plan": 28},
    )


def _write_catalog_fixture(
    catalog_dir: Path,
    *,
    source_set_id: str,
    source_ids: list[str],
    source_count: int,
    artifact_count: int,
    download_batch_run_id: str,
    source_delta_input: dict | None,
    source_record_id_filter_count: int | None,
    supplemental_source_count: int,
    source_partition_counts: dict[str, int],
    document_role_counts: dict[str, int],
) -> None:
    catalog_dir.mkdir(parents=True)
    _write_json(
        catalog_dir / "source_set_manifest.json",
        {
            "source_set_id": source_set_id,
            "source_count": source_count,
            "artifact_count": artifact_count,
            "download_batch_run_id": download_batch_run_id,
            "source_delta_input": source_delta_input,
            "source_record_id_filter_count": source_record_id_filter_count,
            "supplemental_source_count": supplemental_source_count,
            "status_counts": {"downloaded": artifact_count},
            "source_partition_counts": source_partition_counts,
            "document_role_counts": document_role_counts,
        },
    )
    _write_json(
        catalog_dir / "catalog_validation.json",
        {"source_set_id": source_set_id, "passed": True, "checks": []},
    )
    records = [{"source_record_id": source_id, "source_set_id": source_set_id} for source_id in source_ids]
    (catalog_dir / "source_catalog.jsonl").write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    (catalog_dir / "review_sources.sqlite").write_bytes(b"")


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _check(report: dict, name: str) -> dict:
    for check in report["checks"]:
        if check["name"] == name:
            return check
    raise AssertionError(f"Missing check {name}")
