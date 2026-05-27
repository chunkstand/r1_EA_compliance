from __future__ import annotations

from pathlib import Path
import json
import sqlite3

from usfs_r1_ea_sources.records import FOREST_PLAN_IDENTITY_RECONCILIATION_SCHEMA_VERSION
from usfs_r1_ea_sources.records import SOURCE_RECORD_RECONCILIATION_SCHEMA_VERSION
from usfs_r1_ea_sources.records import evaluate_source_record_identity_gate
from usfs_r1_ea_sources.records import expected_source_record_ids_from_v1_eval_contract
from usfs_r1_ea_sources.records import run_source_record_identity_gate


def test_identity_gate_resolves_direct_compliance_and_forest_plan_aliases(
    tmp_path: Path,
) -> None:
    source_record_reconciliation = _write_source_record_reconciliation(
        tmp_path,
        [
            {
                "legacy_source_record_id": "R1EA-OLD",
                "current_source_record_ids": ["FED-001"],
            }
        ],
    )
    forest_plan_identity_reconciliation = _write_forest_plan_identity_reconciliation(
        tmp_path,
        [
            {
                "legacy_source_record_id": "R1PLAN-lolo-nf-02",
                "canonical_source_record_id": "FPS-298",
            }
        ],
    )

    result = evaluate_source_record_identity_gate(
        expected_source_record_ids=(
            "R1EA-DIRECT",
            "R1EA-OLD",
            "R1PLAN-lolo-nf-02",
        ),
        catalog_source_record_ids={"R1EA-DIRECT", "FED-001", "FPS-298"},
        source_record_reconciliation_path=source_record_reconciliation,
        forest_plan_identity_reconciliation_path=forest_plan_identity_reconciliation,
    )

    assert result.summary["passed"] is True
    assert result.summary["direct_current_catalog_hit_count"] == 1
    assert result.summary["compliance_reconciled_source_record_count"] == 1
    assert result.summary["forest_plan_reconciled_source_record_count"] == 1
    assert result.summary["identity_resolved_source_record_count"] == 3
    assert result.summary["ambiguous_mappings"] == {}
    assert result.summary["unmapped_source_record_ids"] == []


def test_identity_gate_fails_closed_on_unmapped_absent_and_ambiguous_ids(
    tmp_path: Path,
) -> None:
    source_record_reconciliation = _write_source_record_reconciliation(
        tmp_path,
        [
            {
                "legacy_source_record_id": "R1EA-AMBIGUOUS",
                "current_source_record_ids": ["FED-001", "FED-002"],
            },
            {
                "legacy_source_record_id": "R1EA-ABSENT",
                "current_source_record_ids": ["FED-MISSING"],
            },
        ],
    )
    forest_plan_identity_reconciliation = _write_forest_plan_identity_reconciliation(
        tmp_path,
        [],
    )

    result = evaluate_source_record_identity_gate(
        expected_source_record_ids=(
            "R1EA-AMBIGUOUS",
            "R1EA-ABSENT",
            "R1EA-UNMAPPED",
        ),
        catalog_source_record_ids={"FED-001", "FED-002"},
        source_record_reconciliation_path=source_record_reconciliation,
        forest_plan_identity_reconciliation_path=forest_plan_identity_reconciliation,
    )

    assert result.summary["passed"] is False
    assert result.summary["ambiguous_mappings"] == {
        "R1EA-AMBIGUOUS": ["FED-001", "FED-002"]
    }
    assert result.summary["mapped_targets_absent_from_catalog"] == {
        "R1EA-ABSENT": ["FED-MISSING"]
    }
    assert result.summary["unmapped_source_record_ids"] == ["R1EA-UNMAPPED"]


def test_expected_source_record_ids_from_v1_eval_contract_dedupes_all_owner_fields() -> None:
    contract = {
        "baseline_policy": {"expected_source_record_ids": ["R1EA-001", "R1EA-002"]},
        "rule_review_expectations": [
            {"expected_source_record_ids": ["R1EA-002", "R1EA-003"]}
        ],
        "conditional_source_expectations": [
            {"expected_source_record_ids": ["R1EA-004", "R1EA-001"]}
        ],
        "forest_plan": {"required_source_record_ids": ["R1PLAN-lolo-nf-02"]},
    }

    assert expected_source_record_ids_from_v1_eval_contract(contract) == [
        "R1EA-001",
        "R1EA-002",
        "R1EA-003",
        "R1EA-004",
        "R1PLAN-lolo-nf-02",
    ]


def test_source_record_identity_gate_runner_stops_on_ambiguous_current_catalog_mapping(
    tmp_path: Path,
) -> None:
    catalog_dir = tmp_path / "catalog"
    _write_catalog(catalog_dir, ["FED-001", "FED-002"])
    eval_file = tmp_path / "eval.json"
    _write_json(
        eval_file,
        {"baseline_policy": {"expected_source_record_ids": ["R1EA-AMBIGUOUS"]}},
    )
    source_record_reconciliation = _write_source_record_reconciliation(
        tmp_path,
        [
            {
                "legacy_source_record_id": "R1EA-AMBIGUOUS",
                "current_source_record_ids": ["FED-001", "FED-002"],
            }
        ],
    )
    forest_plan_identity_reconciliation = _write_forest_plan_identity_reconciliation(
        tmp_path,
        [],
    )

    result = run_source_record_identity_gate(
        output_dir=tmp_path,
        catalog_dir=catalog_dir,
        eval_file=eval_file,
        source_record_reconciliation_path=source_record_reconciliation,
        forest_plan_identity_reconciliation_path=forest_plan_identity_reconciliation,
    )

    assert result.summary["passed"] is False
    assert result.summary["expected_source_record_count"] == 1
    assert result.summary["catalog_covered_source_record_count"] == 1
    assert result.summary["identity_resolved_source_record_count"] == 0
    assert result.summary["ambiguous_mappings"] == {
        "R1EA-AMBIGUOUS": ["FED-001", "FED-002"]
    }


def _write_source_record_reconciliation(
    tmp_path: Path,
    entries: list[dict],
) -> Path:
    path = tmp_path / f"source_record_reconciliation_{len(entries)}.json"
    _write_json(
        path,
        {
            "schema_version": SOURCE_RECORD_RECONCILIATION_SCHEMA_VERSION,
            "entries": entries,
        },
    )
    return path


def _write_forest_plan_identity_reconciliation(
    tmp_path: Path,
    exact_url_matched_source_records: list[dict],
) -> Path:
    path = tmp_path / f"forest_plan_identity_{len(exact_url_matched_source_records)}.json"
    _write_json(
        path,
        {
            "schema_version": FOREST_PLAN_IDENTITY_RECONCILIATION_SCHEMA_VERSION,
            "exact_url_matched_source_records": exact_url_matched_source_records,
            "governed_catalog_rebound_source_records": [],
            "unresolved_source_records": [],
        },
    )
    return path


def _write_catalog(catalog_dir: Path, source_record_ids: list[str]) -> None:
    catalog_dir.mkdir(parents=True)
    with sqlite3.connect(catalog_dir / "review_sources.sqlite") as connection:
        connection.execute("CREATE TABLE sources (source_record_id TEXT)")
        connection.executemany(
            "INSERT INTO sources (source_record_id) VALUES (?)",
            [(source_record_id,) for source_record_id in source_record_ids],
        )


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
