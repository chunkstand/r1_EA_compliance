from __future__ import annotations

from pathlib import Path
import json
import sqlite3
import tempfile

from usfs_r1_ea_sources.forest_plan_source_delta_readiness import (
    build_forest_plan_source_delta_readiness_report,
)
from usfs_r1_ea_sources.workbook import load_r1_forest_plan_document_register


ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "config" / "r1_forest_plan_document_register_draft.csv"
PROFILES = ROOT / "config" / "forest_plan_profiles.json"
GAP_EVIDENCE = ROOT / "config" / "r1_forest_plan_official_source_gap_evidence.json"
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
            official_source_gap_evidence_path=GAP_EVIDENCE,
        )

        report = _read_json(result.report_path)
        assert result.summary["passed"] is True
        assert result.markdown_path.exists()
        assert report["schema_version"] == "r1-forest-plan-source-delta-readiness-v3"
        assert report["register"]["source_delta_count"] == 160
        assert report["register"]["skipped_gap_source_record_ids"] == [
            "R1PLAN-kootenai-nf-18",
        ]
        assert report["scoped_source_delta_catalog"]["source_set_id"] == "source-set-delta-test"
        assert report["active_canonical_catalog"]["source_set_id"] == (
            "source-set-canonical-promoted-test"
        )
        assert report["extraction_readiness"]["status"] == "not_started"
        assert report["retrieval_readiness"]["status"] == "not_started"
        assert report["official_source_gap_evidence"]["source_record_ids"] == [
            "R1PLAN-kootenai-nf-18",
        ]
        assert _check(report, "official_source_gap_evidence_current_for_register")["passed"] is True
        assert "R1PLAN-kootenai-nf-18" in _profile_row(
            report, "kootenai-nf"
        )["blocker_source_record_ids"]
        assert _check(
            report, "forest_profile_readiness_tracks_configured_and_register_units"
        )["passed"] is True
        assert _check(
            report, "forest_profile_readiness_blockers_are_source_specific"
        )["passed"] is True
        assert _check(
            report, "forest_profile_readiness_summary_counts_align"
        )["passed"] is True


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
            official_source_gap_evidence_path=GAP_EVIDENCE,
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
            official_source_gap_evidence_path=GAP_EVIDENCE,
        )

        report = _read_json(result.report_path)
        stale_check = _check(report, "source_delta_catalog_gate_matches_register")
        assert result.summary["passed"] is False
        assert stale_check["passed"] is False
        assert stale_check["details"]["missing_source_delta_ids"] == [missing_id]


def test_forest_plan_source_delta_readiness_fails_when_gap_evidence_missing() -> None:
    register = load_r1_forest_plan_document_register(REGISTER)
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        _write_sequence_zero_fixture(output_dir, register=register)

        result = build_forest_plan_source_delta_readiness_report(
            output_dir=output_dir,
            register_path=REGISTER,
            source_delta_batch_run_id=BATCH_RUN_ID,
            forest_plan_profiles_path=PROFILES,
            official_source_gap_evidence_path=output_dir / "missing_gap_evidence.json",
        )

        report = _read_json(result.report_path)
        gap_check = _check(report, "official_source_gap_evidence_current_for_register")
        assert result.summary["passed"] is False
        assert gap_check["passed"] is False
        assert gap_check["details"]["missing_gap_source_record_ids"] == ["R1PLAN-kootenai-nf-18"]


def test_forest_plan_source_delta_readiness_sequence_four_uses_merged_extraction_coverage() -> None:
    register = load_r1_forest_plan_document_register(REGISTER)
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        _write_sequence_zero_fixture(output_dir, register=register)
        merged_catalog_dir = _write_merged_catalog_fixture(output_dir, register=register)
        merged_source_set_id = "source-set-merged-test"
        blocker_id = register.source_delta_sources[0].source_record_id
        reuse_inventory_path = _write_reuse_inventory_fixture(
            output_dir,
            source_set_id=merged_source_set_id,
            source_record_ids=[source.source_record_id for source in register.source_delta_sources],
        )
        _write_extraction_fixture(
            output_dir,
            source_set_id=merged_source_set_id,
            source_record_ids=[source.source_record_id for source in register.source_delta_sources],
            blocker_id=blocker_id,
        )

        result = build_forest_plan_source_delta_readiness_report(
            output_dir=output_dir,
            register_path=REGISTER,
            source_delta_batch_run_id=BATCH_RUN_ID,
            merged_catalog_gate_dir=merged_catalog_dir,
            extraction_source_set_id=merged_source_set_id,
            reuse_inventory_path=reuse_inventory_path,
            forest_plan_profiles_path=PROFILES,
            official_source_gap_evidence_path=GAP_EVIDENCE,
        )

        report = _read_json(result.report_path)
        assert result.summary["passed"] is True
        assert report["schema_version"] == "r1-forest-plan-source-delta-readiness-v3"
        assert report["merged_source_delta_catalog"]["source_set_id"] == merged_source_set_id
        assert report["extraction_readiness"]["status"] == "ready_with_blockers"
        assert report["extraction_readiness"]["coverage_complete"] is True
        assert report["extraction_readiness"]["blocked_status_counts"] == {"parser_error": 1}
        assert report["extraction_readiness"]["reuse_inventory"]["status"] == "ready"
        assert _check(report, "merged_catalog_gate_validation_passed")["passed"] is True
        assert _check(report, "source_delta_extraction_readiness_covers_expected_rows")["passed"] is True


def test_forest_plan_source_delta_readiness_sequence_five_uses_retrieval_coverage_and_eval() -> None:
    register = load_r1_forest_plan_document_register(REGISTER)
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        _write_sequence_zero_fixture(output_dir, register=register)
        merged_catalog_dir = _write_merged_catalog_fixture(output_dir, register=register)
        merged_source_set_id = "source-set-merged-test"
        blocker_id = register.source_delta_sources[0].source_record_id
        reuse_inventory_path = _write_reuse_inventory_fixture(
            output_dir,
            source_set_id=merged_source_set_id,
            source_record_ids=[source.source_record_id for source in register.source_delta_sources],
        )
        _write_extraction_fixture(
            output_dir,
            source_set_id=merged_source_set_id,
            source_record_ids=[source.source_record_id for source in register.source_delta_sources],
            blocker_id=blocker_id,
        )
        _write_retrieval_fixture(
            output_dir,
            source_set_id=merged_source_set_id,
            indexed_source_record_ids=[
                source.source_record_id
                for source in register.source_delta_sources
                if source.source_record_id != blocker_id
            ],
        )

        result = build_forest_plan_source_delta_readiness_report(
            output_dir=output_dir,
            register_path=REGISTER,
            source_delta_batch_run_id=BATCH_RUN_ID,
            merged_catalog_gate_dir=merged_catalog_dir,
            extraction_source_set_id=merged_source_set_id,
            reuse_inventory_path=reuse_inventory_path,
            forest_plan_profiles_path=PROFILES,
            official_source_gap_evidence_path=GAP_EVIDENCE,
        )

        report = _read_json(result.report_path)
        assert result.summary["passed"] is True
        assert report["retrieval_readiness"]["status"] == "ready_with_blockers"
        assert report["retrieval_readiness"]["retrieval_eval_passed"] is True
        assert report["retrieval_readiness"]["expected_source_record_count"] == 160
        assert report["retrieval_readiness"]["expected_extracted_source_record_count"] == 159
        assert report["retrieval_readiness"]["indexed_source_record_count_for_expected_sources"] == 159
        assert report["retrieval_readiness"]["missing_indexed_extracted_source_record_ids"] == []
        assert report["retrieval_readiness"]["upstream_blocked_source_record_ids"] == [blocker_id]
        assert report["retrieval_readiness"]["document_role_counts"]["expected"][
            "primary_land_management_plan"
        ] == 4
        assert _check(report, "source_delta_retrieval_readiness_covers_extracted_rows")["passed"] is True
        assert _check(report, "source_delta_retrieval_eval_passed")["passed"] is True


def test_forest_plan_source_delta_readiness_sequence_six_emits_concrete_profile_blockers() -> None:
    register = load_r1_forest_plan_document_register(REGISTER)
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        _write_sequence_zero_fixture(output_dir, register=register)
        merged_catalog_dir = _write_merged_catalog_fixture(output_dir, register=register)
        merged_source_set_id = "source-set-merged-test"
        blocker_id = register.source_delta_sources[0].source_record_id
        all_captured_source_ids = register.catalog_confirmed_source_record_ids + [
            source.source_record_id for source in register.source_delta_sources
        ]
        reuse_inventory_path = _write_reuse_inventory_fixture(
            output_dir,
            source_set_id=merged_source_set_id,
            source_record_ids=all_captured_source_ids,
        )
        _write_extraction_fixture(
            output_dir,
            source_set_id=merged_source_set_id,
            source_record_ids=all_captured_source_ids,
            blocker_id=blocker_id,
        )
        _write_retrieval_fixture(
            output_dir,
            source_set_id=merged_source_set_id,
            indexed_source_record_ids=[
                source_record_id
                for source_record_id in all_captured_source_ids
                if source_record_id != blocker_id
            ],
        )

        result = build_forest_plan_source_delta_readiness_report(
            output_dir=output_dir,
            register_path=REGISTER,
            source_delta_batch_run_id=BATCH_RUN_ID,
            merged_catalog_gate_dir=merged_catalog_dir,
            extraction_source_set_id=merged_source_set_id,
            reuse_inventory_path=reuse_inventory_path,
            forest_plan_profiles_path=PROFILES,
            official_source_gap_evidence_path=GAP_EVIDENCE,
        )

        report = _read_json(result.report_path)
        blocker_row = next(
            row for row in register.rows if row["proposed_source_record_id"] == blocker_id
        )
        custer = _profile_row(report, "custer-gallatin-nf")
        blocked_unit = _profile_row(report, blocker_row["forest_unit_id"])
        blocked_requirement = _source_requirement(blocked_unit, blocker_id)
        kootenai = _profile_row(report, "kootenai-nf")

        assert result.summary["passed"] is True
        assert report["forest_profile_readiness"]["status"] == "ready_with_blockers"
        assert custer["profile_readiness_status"] == "ready"
        assert custer["required_retrieval_ready_count"] == custer["required_source_record_count"] == 7
        assert report["forest_profile_readiness"]["ready_profile_ids"] == ["custer-gallatin-nf"]
        assert report["forest_profile_readiness"]["blocked_profile_ids"] == [
            "beaverhead-deerlodge-nf"
        ]
        assert blocker_id in blocked_unit["blocker_source_record_ids"]
        assert blocked_requirement["readiness_status"] == "extraction_blocked"
        assert blocked_requirement["blocker_types"] == ["extraction_blocked"]
        assert "R1PLAN-kootenai-nf-18" in kootenai["blocker_source_record_ids"]
        assert _check(
            report, "forest_profile_readiness_tracks_configured_and_register_units"
        )["passed"] is True
        assert _check(
            report, "forest_profile_readiness_blockers_are_source_specific"
        )["passed"] is True
        assert _check(
            report, "forest_profile_readiness_summary_counts_align"
        )["passed"] is True


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
        source_set_id="source-set-canonical-promoted-test",
        source_ids=register.catalog_confirmed_source_record_ids + source_delta_ids,
        source_count=190 + len(source_delta_ids),
        artifact_count=319,
        download_batch_run_id=None,
        download_batch_run_ids=["canonical-batches", BATCH_RUN_ID],
        source_delta_input=register.summary(),
        source_record_id_filter_count=None,
        supplemental_source_count=len(source_delta_ids),
        source_partition_counts={"active_review_corpus": 349, "candidate_blocked_source": 1},
        document_role_counts={
            "forest_plan": 28,
            "forest_plan_support": len(source_delta_ids),
        },
    )


def _write_catalog_fixture(
    catalog_dir: Path,
    *,
    source_set_id: str,
    source_ids: list[str],
    source_count: int,
    artifact_count: int,
    download_batch_run_id: str | None,
    download_batch_run_ids: list[str] | None = None,
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
            "download_batch_run_ids": download_batch_run_ids,
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


def _write_merged_catalog_fixture(output_dir: Path, *, register) -> Path:
    merged_dir = output_dir / "runs" / BATCH_RUN_ID / "merged_catalog_gate"
    source_ids = register.catalog_confirmed_source_record_ids + [
        source.source_record_id for source in register.source_delta_sources
    ]
    _write_catalog_fixture(
        merged_dir,
        source_set_id="source-set-merged-test",
        source_ids=source_ids,
        source_count=190 + len(register.source_delta_sources),
        artifact_count=319,
        download_batch_run_id=None,
        download_batch_run_ids=["canonical-batches", BATCH_RUN_ID],
        source_delta_input=register.summary(),
        source_record_id_filter_count=None,
        supplemental_source_count=len(register.source_delta_sources),
        source_partition_counts={"active_review_corpus": 349, "candidate_blocked_source": 1},
        document_role_counts={"forest_plan": 28, "forest_plan_support": len(register.source_delta_sources)},
    )
    return merged_dir


def _write_extraction_fixture(
    output_dir: Path,
    *,
    source_set_id: str,
    source_record_ids: list[str],
    blocker_id: str,
) -> None:
    diagnostics_dir = output_dir / "derived" / source_set_id / "diagnostics"
    chunks_dir = output_dir / "derived" / source_set_id / "chunks"
    text_dir = output_dir / "derived" / source_set_id / "extracted_text"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir.mkdir(parents=True, exist_ok=True)
    text_dir.mkdir(parents=True, exist_ok=True)

    manifest_records = []
    chunks = []
    for source_record_id in source_record_ids:
        base_record = {
            "source_set_id": source_set_id,
            "source_record_id": source_record_id,
            "title": source_record_id,
            "document_role": "forest_plan_support",
            "authority_level": "forest_service",
            "expected_parser": "pdf",
            "source_status": "downloaded",
            "artifact_sha256": f"sha-{source_record_id}",
            "artifact_path": f"artifacts/{source_record_id}.pdf",
            "content_type": "application/pdf",
            "text_char_count": 0,
            "chunk_count": 0,
        }
        if source_record_id == blocker_id:
            manifest_records.append(
                {
                    **base_record,
                    "status": "parser_error",
                    "failure": {
                        "error_class": "unsupported_zip_member",
                        "error_message": "Unsupported ZIP entry.",
                    },
                }
            )
            continue

        text_path = text_dir / f"{source_record_id}.txt"
        text = f"Extracted text for {source_record_id}"
        text_path.write_text(text, encoding="utf-8")
        manifest_records.append(
            {
                **base_record,
                "status": "extracted",
                "parser_name": "unit-parser",
                "parser_version": "1",
                "parser_metadata": {"reused_existing": False},
                "text_path": str(text_path),
                "text_char_count": len(text),
                "text_sha256": f"text-sha-{source_record_id}",
                "chunk_count": 1,
                "failure": None,
            }
        )
        chunks.append(
            {
                "chunk_id": f"chunk:{source_record_id}:0",
                "source_set_id": source_set_id,
                "source_record_id": source_record_id,
                "artifact_sha256": f"sha-{source_record_id}",
                "artifact_path": f"artifacts/{source_record_id}.pdf",
                "citation_label": source_record_id,
                "original_url": f"https://example.com/{source_record_id}",
                "effective_url": f"https://example.com/{source_record_id}",
                "final_url": f"https://example.com/{source_record_id}",
                "parser_name": "unit-parser",
                "parser_version": "1",
                "extracted_at": "2026-05-10T00:00:00Z",
                "support_document_role": "primary_land_management_plan",
                "char_start": 0,
                "char_end": len(text),
                "content_sha256": f"content-sha-{source_record_id}",
                "text": text,
            }
        )

    _write_jsonl(diagnostics_dir / "extraction_manifest.jsonl", manifest_records)
    _write_json(
        diagnostics_dir / "extraction_validation.json",
        {"source_set_id": source_set_id, "passed": False, "checks": []},
    )
    _write_json(
        diagnostics_dir / "summary.json",
        {
            "source_set_id": source_set_id,
            "selected_source_count": len(source_record_ids),
            "extracted_count": len(source_record_ids) - 1,
            "failed_count": 1,
            "status_counts": {
                "extracted": len(source_record_ids) - 1,
                "parser_error": 1,
            },
            "validation_passed": False,
        },
    )
    _write_jsonl(chunks_dir / "chunks.jsonl", chunks)


def _write_reuse_inventory_fixture(
    output_dir: Path,
    *,
    source_set_id: str,
    source_record_ids: list[str],
) -> Path:
    inventory_dir = output_dir / "derived" / source_set_id / "reuse_inventory"
    inventory_dir.mkdir(parents=True, exist_ok=True)
    records = [
        {
            "source_record_id": source_record_id,
            "source_set_id": source_set_id,
            "classification": "needs_extract",
        }
        for source_record_id in source_record_ids
    ]
    _write_jsonl(inventory_dir / "reuse_inventory_records.jsonl", records)
    _write_json(
        inventory_dir / "summary.json",
        {
            "source_set_id": source_set_id,
            "classification_counts": {"needs_extract": len(source_record_ids)},
        },
    )
    _write_json(
        inventory_dir / "reuse_inventory.json",
        {
            "summary": {
                "source_set_id": source_set_id,
                "classification_counts": {"needs_extract": len(source_record_ids)},
            },
            "records": records,
        },
    )
    return inventory_dir / "reuse_inventory.json"


def _write_retrieval_fixture(
    output_dir: Path,
    *,
    source_set_id: str,
    indexed_source_record_ids: list[str],
) -> None:
    retrieval_dir = output_dir / "derived" / source_set_id / "retrieval"
    retrieval_dir.mkdir(parents=True, exist_ok=True)
    sqlite_path = retrieval_dir / "evidence_index.sqlite"
    with sqlite3.connect(sqlite_path) as connection:
        connection.execute("CREATE TABLE chunks (source_record_id TEXT NOT NULL)")
        connection.executemany(
            "INSERT INTO chunks(source_record_id) VALUES (?)",
            [(source_record_id,) for source_record_id in indexed_source_record_ids],
        )
        connection.commit()

    _write_json(
        retrieval_dir / "retrieval_validation.json",
        {"source_set_id": source_set_id, "passed": True, "checks": []},
    )
    _write_json(
        retrieval_dir / "summary.json",
        {
            "source_set_id": source_set_id,
            "validation_passed": True,
            "reviewer_ready": True,
            "chunk_count": len(indexed_source_record_ids),
            "source_count": len(indexed_source_record_ids),
        },
    )
    _write_json(
        retrieval_dir / "retrieval_eval_results.json",
        {
            "index_path": str(sqlite_path),
            "query_count": 2,
            "passed_count": 2,
            "failed_count": 0,
            "passed": True,
            "cases": [
                {"id": "flathead-plan", "passed": True},
                {"id": "kootenai-gap", "passed": True, "expect_no_hits": True},
            ],
        },
    )


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _check(report: dict, name: str) -> dict:
    for check in report["checks"]:
        if check["name"] == name:
            return check
    raise AssertionError(f"Missing check {name}")


def _profile_row(report: dict, forest_unit_id: str) -> dict:
    for row in report["forest_profile_readiness"]["profile_rows"]:
        if row["forest_unit_id"] == forest_unit_id:
            return row
    raise AssertionError(f"Missing profile readiness row {forest_unit_id}")


def _source_requirement(profile_row: dict, source_record_id: str) -> dict:
    for requirement in profile_row["source_requirements"]:
        if requirement["source_record_id"] == source_record_id:
            return requirement
    raise AssertionError(f"Missing source requirement {source_record_id}")
