from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.authority_currentness import (
    AUTHORITY_CURRENTNESS_REPORT_SCHEMA_VERSION,
)
from usfs_r1_ea_sources.authority_currentness import build_authority_currentness_report


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_WORKBOOK = ROOT / "usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx"


class AuthorityCurrentnessTests(unittest.TestCase):
    def test_report_records_required_source_currentness_fields_and_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output_dir = tmp_path / "source_library"
            inventory_path = tmp_path / "authority_inventory.json"
            decisions_path = tmp_path / "source_addition_decisions.json"
            _write_catalog(
                output_dir,
                rows=[
                    _catalog_row(
                        source_record_id="R1EA-001",
                        title="7 CFR part 1b",
                        currentness_notes="Effective Apr. 3, 2026",
                    ),
                    _catalog_row(
                        source_record_id="R1EA-002",
                        title="Current USDA NEPA replacement source",
                    ),
                    _catalog_row(
                        source_record_id="R1EA-160",
                        title="Excluded project page",
                        source_status="skipped_excluded",
                        citation_label="R1EA-160",
                        effective_url="https://www.fs.usda.gov/example/excluded",
                        artifact_path=None,
                        artifact_sha256=None,
                        artifact_byte_size=None,
                    ),
                ],
            )
            _write_json(inventory_path, _inventory())
            _write_json(decisions_path, _decisions())

            result = build_authority_currentness_report(
                output_dir=output_dir,
                authority_inventory_path=inventory_path,
                source_addition_decisions_path=decisions_path,
            )

            report = _read_json(result.report_path)
            self.assertEqual(
                report["schema_version"],
                AUTHORITY_CURRENTNESS_REPORT_SCHEMA_VERSION,
            )
            self.assertTrue(report["validation"]["passed"])
            self.assertEqual(result.summary["source_currentness_record_count"], 3)
            self.assertEqual(result.summary["documented_source_non_addition_count"], 1)
            self.assertEqual(result.summary["excluded_source_record_count"], 1)

            records = {
                (record["authority_family_id"], record["source_record_id"]): record
                for record in report["source_currentness_records"]
            }
            current_record = records[("source_only_family", "R1EA-001")]
            self.assertEqual(current_record["source_title"], "7 CFR part 1b")
            self.assertEqual(current_record["citation_label"], "R1EA-001 citation")
            self.assertEqual(current_record["url"], "https://example.test/R1EA-001")
            self.assertEqual(current_record["effective_date"], "2026-04-03")
            self.assertEqual(current_record["capture_date"], "2026-05-01T00:00:00Z")
            self.assertEqual(current_record["supersession_status"], "current_authoritative_source")
            self.assertTrue(current_record["counts_as_current_authority"])
            self.assertEqual(current_record["source_partition"], "active_review_corpus")
            self.assertEqual(
                current_record["authority_family_source_role"],
                "active_authority_source",
            )

            excluded_record = records[("source_only_family", "R1EA-160")]
            self.assertEqual(excluded_record["currentness_status"], "excluded_no_artifact")
            self.assertEqual(excluded_record["source_partition"], "candidate_blocked_source")
            self.assertEqual(
                excluded_record["supersession_status"],
                "excluded_no_current_authority",
            )
            self.assertFalse(excluded_record["counts_as_current_authority"])

            superseded_record = records[("superseded_family", "R1EA-002")]
            self.assertEqual(
                superseded_record["supersession_status"],
                "superseded_source_record",
            )
            self.assertFalse(superseded_record["counts_as_current_authority"])
            self.assertFalse(superseded_record["eligible_for_active_review_rules_for_family"])
            self.assertNotIn(
                "RULE_DERIVES_FROM_AUTHORITY",
                superseded_record["graph_allowed_relationships_for_family"],
            )

            family_statuses = {
                family["authority_family_id"]: family["currentness_status"]
                for family in report["family_currentness"]
            }
            self.assertEqual(
                family_statuses["environmental_justice_civil_rights"],
                "documented_source_non_addition",
            )
            self.assertEqual(
                family_statuses["superseded_family"],
                "superseded_replacement_sources_confirmed",
            )

    def test_failed_web_capture_status_does_not_count_as_current(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output_dir = tmp_path / "source_library"
            inventory_path = tmp_path / "authority_inventory.json"
            decisions_path = tmp_path / "source_addition_decisions.json"
            _write_catalog(
                output_dir,
                rows=[
                    _catalog_row(
                        source_record_id="R1EA-001",
                        source_status="challenge_page",
                    )
                ],
            )
            inventory = _inventory(
                families=[
                    {
                        "family_id": "source_only_family",
                        "status": "source_only",
                        "source_record_ids": ["R1EA-001"],
                        "open_inventory_gaps": [],
                    }
                ]
            )
            _write_json(inventory_path, inventory)
            _write_json(decisions_path, {"schema_version": "test-decisions", "decisions": []})

            result = build_authority_currentness_report(
                output_dir=output_dir,
                authority_inventory_path=inventory_path,
                source_addition_decisions_path=decisions_path,
            )

            report = _read_json(result.report_path)
            self.assertFalse(report["validation"]["passed"])
            record = report["source_currentness_records"][0]
            self.assertEqual(record["currentness_status"], "failed_or_unverified_capture")
            self.assertFalse(record["counts_as_current_authority"])
            checks = {check["name"]: check for check in report["validation"]["checks"]}
            self.assertFalse(checks["non_candidate_families_have_current_source_coverage"]["passed"])
            self.assertFalse(checks["no_family_has_failed_or_missing_capture"]["passed"])

    def test_candidate_family_without_decision_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output_dir = tmp_path / "source_library"
            inventory_path = tmp_path / "authority_inventory.json"
            decisions_path = tmp_path / "source_addition_decisions.json"
            _write_catalog(output_dir, rows=[])
            inventory = _inventory(
                families=[
                    {
                        "family_id": "environmental_justice_civil_rights",
                        "status": "candidate",
                        "source_record_ids": [],
                        "open_inventory_gaps": ["source rows needed"],
                    }
                ]
            )
            _write_json(inventory_path, inventory)
            _write_json(decisions_path, {"schema_version": "test-decisions", "decisions": []})

            result = build_authority_currentness_report(
                output_dir=output_dir,
                authority_inventory_path=inventory_path,
                source_addition_decisions_path=decisions_path,
            )

            report = _read_json(result.report_path)
            self.assertFalse(report["validation"]["passed"])
            family = report["family_currentness"][0]
            self.assertEqual(family["currentness_status"], "missing_source_addition_decision")
            checks = {check["name"]: check for check in report["validation"]["checks"]}
            self.assertFalse(checks["candidate_families_have_source_addition_decisions"]["passed"])

    def test_stale_milestone_2_inventory_gap_fails_alignment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output_dir = tmp_path / "source_library"
            inventory_path = tmp_path / "authority_inventory.json"
            decisions_path = tmp_path / "source_addition_decisions.json"
            _write_catalog(
                output_dir,
                rows=[_catalog_row(source_record_id="R1EA-001")],
            )
            inventory = _inventory(
                families=[
                    {
                        "family_id": "source_only_family",
                        "status": "source_only",
                        "source_record_ids": ["R1EA-001"],
                        "open_inventory_gaps": [
                            "Milestone 2 must confirm current authoritative source coverage and supersession status for this family before promotion."
                        ],
                    }
                ]
            )
            inventory["summary"]["families_requiring_milestone_2_source_currentness"] = 1
            _write_json(inventory_path, inventory)
            _write_json(decisions_path, {"schema_version": "test-decisions", "decisions": []})

            result = build_authority_currentness_report(
                output_dir=output_dir,
                authority_inventory_path=inventory_path,
                source_addition_decisions_path=decisions_path,
            )

            report = _read_json(result.report_path)
            self.assertFalse(report["validation"]["passed"])
            checks = {check["name"]: check for check in report["validation"]["checks"]}
            self.assertFalse(checks["inventory_has_no_stale_milestone_2_currentness_gaps"]["passed"])
            self.assertFalse(
                checks[
                    "inventory_summary_has_no_remaining_milestone_2_currentness_requirements"
                ]["passed"]
            )

    def test_source_partition_contract_allows_archived_reserved_and_fsh_chapters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output_dir = tmp_path / "source_library"
            inventory_path = tmp_path / "authority_inventory.json"
            decisions_path = tmp_path / "source_addition_decisions.json"
            _write_catalog(
                output_dir,
                rows=[
                    _catalog_row(source_record_id="R1EA-001", title="7 CFR part 1b"),
                    _catalog_row(
                        source_record_id="R1EA-220",
                        title="36 CFR part 220 - Reserved Forest Service NEPA regulations",
                        currentness_notes="Reserved and superseded; currentness evidence only.",
                        source_partition="currentness_supersession_archive",
                    ),
                    _catalog_row(
                        source_record_id="R1EA-FSH-1909-15-00",
                        title="FSH 1909.15 Contents and Zero Code",
                    ),
                    _catalog_row(
                        source_record_id="R1EA-FSH-1909-15-30",
                        title="FSH 1909.15 Chapter 30 Environmental Assessment",
                    ),
                ],
            )
            inventory = _inventory(
                families=[
                    {
                        "family_id": "active_nepa_sources",
                        "status": "active",
                        "source_record_ids": [
                            "R1EA-001",
                            "R1EA-FSH-1909-15-00",
                            "R1EA-FSH-1909-15-30",
                        ],
                        "open_inventory_gaps": [],
                    },
                    {
                        "family_id": "superseded_36_cfr_220",
                        "status": "superseded",
                        "source_record_ids": ["R1EA-220"],
                        "open_inventory_gaps": ["Preserve supersession graph relationship."],
                        "supersession": {
                            "replacement_family_id": "active_nepa_sources",
                            "current_source_record_ids": ["R1EA-001"],
                        },
                    },
                ]
            )
            _write_json(inventory_path, inventory)
            _write_json(decisions_path, {"schema_version": "test-decisions", "decisions": []})

            result = build_authority_currentness_report(
                output_dir=output_dir,
                authority_inventory_path=inventory_path,
                source_addition_decisions_path=decisions_path,
            )

            report = _read_json(result.report_path)
            checks = {check["name"]: check for check in report["validation"]["checks"]}
            self.assertTrue(report["validation"]["passed"])
            self.assertTrue(checks["non_current_sources_not_in_active_review_corpus"]["passed"])
            self.assertTrue(
                checks["reserved_or_superseded_authorities_not_active_controlling"]["passed"]
            )
            self.assertTrue(checks["fsh_1909_15_chapter_records_are_not_collapsed"]["passed"])
            self.assertTrue(
                checks[
                    "source_partition_contract_partition_eligibility_matches_boundary"
                ]["passed"]
            )
            self.assertTrue(
                checks[
                    "source_partition_contract_defines_reserved_36_cfr_part_220_boundary"
                ]["passed"]
            )
            partition_records = {
                record["source_record_id"]: record for record in report["catalog_source_partitions"]
            }
            self.assertEqual(
                partition_records["R1EA-220"]["source_partition"],
                "currentness_supersession_archive",
            )
            self.assertEqual(
                partition_records["R1EA-FSH-1909-15-30"]["fsh_1909_15_chapter_kind"],
                "environmental_assessment",
            )

    def test_active_reserved_36_cfr_220_source_partition_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output_dir = tmp_path / "source_library"
            inventory_path = tmp_path / "authority_inventory.json"
            decisions_path = tmp_path / "source_addition_decisions.json"
            _write_catalog(
                output_dir,
                rows=[
                    _catalog_row(
                        source_record_id="R1EA-220",
                        title="36 CFR part 220 - Reserved Forest Service NEPA regulations",
                        currentness_notes="Reserved and superseded; should not be active.",
                        source_partition="active_review_corpus",
                    )
                ],
            )
            inventory = _inventory(
                families=[
                    {
                        "family_id": "bad_active_superseded_source",
                        "status": "active",
                        "source_record_ids": ["R1EA-220"],
                        "open_inventory_gaps": [],
                    }
                ]
            )
            _write_json(inventory_path, inventory)
            _write_json(decisions_path, {"schema_version": "test-decisions", "decisions": []})

            result = build_authority_currentness_report(
                output_dir=output_dir,
                authority_inventory_path=inventory_path,
                source_addition_decisions_path=decisions_path,
            )

            report = _read_json(result.report_path)
            checks = {check["name"]: check for check in report["validation"]["checks"]}
            self.assertFalse(report["validation"]["passed"])
            self.assertFalse(checks["non_current_sources_not_in_active_review_corpus"]["passed"])
            self.assertFalse(
                checks["reserved_or_superseded_authorities_not_active_controlling"]["passed"]
            )

    def test_collapsed_fsh_1909_15_handbook_record_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output_dir = tmp_path / "source_library"
            inventory_path = tmp_path / "authority_inventory.json"
            decisions_path = tmp_path / "source_addition_decisions.json"
            _write_catalog(
                output_dir,
                rows=[
                    _catalog_row(
                        source_record_id="R1EA-FSH-1909-15",
                        title="FSH 1909.15 Environmental Policy and Procedures Handbook",
                    )
                ],
            )
            inventory = _inventory(
                families=[
                    {
                        "family_id": "collapsed_fsh_handbook",
                        "status": "active",
                        "source_record_ids": ["R1EA-FSH-1909-15"],
                        "open_inventory_gaps": [],
                    }
                ]
            )
            _write_json(inventory_path, inventory)
            _write_json(decisions_path, {"schema_version": "test-decisions", "decisions": []})

            result = build_authority_currentness_report(
                output_dir=output_dir,
                authority_inventory_path=inventory_path,
                source_addition_decisions_path=decisions_path,
            )

            report = _read_json(result.report_path)
            checks = {check["name"]: check for check in report["validation"]["checks"]}
            self.assertFalse(report["validation"]["passed"])
            self.assertFalse(checks["fsh_1909_15_chapter_records_are_not_collapsed"]["passed"])

    def test_report_allows_superset_manifest_when_inventory_rows_are_present(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output_dir = tmp_path / "source_library"
            inventory_path = tmp_path / "authority_inventory.json"
            decisions_path = tmp_path / "source_addition_decisions.json"
            catalog_dir = output_dir / "runs" / "merged_catalog"
            manifest_path = catalog_dir / "source_set_manifest.json"
            catalog_path = catalog_dir / "source_catalog.jsonl"
            _write_json(
                manifest_path,
                {
                    "source_set_id": "source-set-merged",
                    "created_at": "2026-05-10T00:00:00Z",
                    "source_count": 4,
                    "artifact_count": 3,
                },
            )
            _write_jsonl(
                catalog_path,
                [
                    {**_catalog_row(source_record_id="R1EA-001"), "source_set_id": "source-set-merged"},
                    {**_catalog_row(source_record_id="R1EA-002"), "source_set_id": "source-set-merged"},
                    {
                        **_catalog_row(
                        source_record_id="R1EA-160",
                        source_status="skipped_excluded",
                        artifact_path=None,
                        artifact_sha256=None,
                        artifact_byte_size=None,
                    ),
                        "source_set_id": "source-set-merged",
                    },
                    {
                        **_catalog_row(
                        source_record_id="R1PLAN-001",
                        title="Forest Plan source row",
                    ),
                        "source_set_id": "source-set-merged",
                    },
                ],
            )
            _write_json(inventory_path, _inventory())
            _write_json(decisions_path, _decisions())

            result = build_authority_currentness_report(
                output_dir=output_dir,
                authority_inventory_path=inventory_path,
                source_addition_decisions_path=decisions_path,
                catalog_path=catalog_path,
                source_set_manifest_path=manifest_path,
                source_set_id="source-set-merged",
            )

            report = _read_json(result.report_path)
            checks = {check["name"]: check for check in report["validation"]["checks"]}
            self.assertTrue(checks["inventory_source_set_matches_manifest"]["passed"])

    def test_canonical_source_register_projection_builds_projected_inputs_and_lineage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output_dir = tmp_path / "source_library"
            _write_catalog(
                output_dir,
                rows=[
                    _canonical_catalog_row(
                        source_record_id="FED-003",
                        title="National Forest System Land Management Planning",
                        authority_document_id="authority_document:federal-planning-rule",
                        citation_label="36 CFR part 219",
                    ),
                    _canonical_catalog_row(
                        source_record_id="SUP-004",
                        title="Older 1982 planning-rule viability citation",
                        authority_document_id="authority_document:superseded-planning-rule-viability",
                        authority_tier="Superseded",
                        citation_label="36 CFR 219.19 legacy use",
                        currentness_status="Superseded or noncurrent controlling authority",
                    ),
                ],
                workbook_path=str(CANONICAL_WORKBOOK),
            )

            result = build_authority_currentness_report(output_dir=output_dir)

            report = _read_json(result.report_path)
            self.assertTrue(report["validation"]["passed"])
            self.assertTrue(
                report["inputs"]["authority_inventory_path"].endswith(
                    "authority_inventory_projected.json"
                )
            )
            self.assertTrue(
                report["inputs"]["source_addition_decisions_path"].endswith(
                    "source_addition_decisions_projected.json"
                )
            )
            self.assertGreater(result.summary["candidate_family_count"], 0)
            self.assertGreater(result.summary["documented_source_gap_count"], 0)
            self.assertGreater(result.summary["temporal_lineage_record_count"], 0)

            superseded_family = next(
                family for family in report["family_currentness"] if family["family_status"] == "superseded"
            )
            self.assertEqual(
                superseded_family["currentness_status"],
                "superseded_replacement_sources_confirmed",
            )
            lineage_record = next(
                record
                for record in report["temporal_lineage_records"]
                if record.get("source_record_id") == "SUP-004"
            )
            self.assertEqual(lineage_record["replacement_source_record_ids"], ["FED-003"])


def _write_catalog(
    output_dir: Path,
    *,
    rows: list[dict],
    workbook_path: str | None = None,
) -> None:
    catalog_dir = output_dir / "catalog"
    catalog_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        catalog_dir / "source_set_manifest.json",
        {
            "source_set_id": "source-set-current",
            "created_at": "2026-05-01T00:00:00Z",
            "source_count": len(rows),
            "artifact_count": sum(1 for row in rows if row.get("artifact_path")),
            "status_counts": {
                status: sum(1 for row in rows if row.get("source_status") == status)
                for status in sorted({row.get("source_status") for row in rows})
            },
            "workbook_path": workbook_path,
        },
    )
    _write_jsonl(catalog_dir / "source_catalog.jsonl", rows)


def _catalog_row(
    *,
    source_record_id: str,
    title: str | None = None,
    source_status: str = "downloaded",
    citation_label: str | None = None,
    effective_url: str | None = None,
    currentness_notes: str | None = "Current source",
    artifact_path: str | None = "source_library/artifacts/raw/example.raw",
    artifact_sha256: str | None = "abc123",
    artifact_byte_size: int | None = 3,
    source_partition: str | None = None,
) -> dict:
    row = {
        "source_set_id": "source-set-current",
        "source_record_id": source_record_id,
        "title": title or source_record_id,
        "source_status": source_status,
        "citation_label": citation_label or f"{source_record_id} citation",
        "effective_url": effective_url or f"https://example.test/{source_record_id}",
        "original_url": effective_url or f"https://example.test/{source_record_id}",
        "retrieved_at": None,
        "currentness_notes": currentness_notes,
        "document_role": "regulation",
        "authority_level": "federal",
        "issuer": "Test issuer",
        "scope": "Conditional",
        "artifact_path": artifact_path,
        "artifact_sha256": artifact_sha256,
        "artifact_byte_size": artifact_byte_size,
    }
    if source_partition:
        row["source_partition"] = source_partition
    return row


def _canonical_catalog_row(
    *,
    source_record_id: str,
    title: str,
    authority_document_id: str,
    authority_tier: str = "Federal",
    citation_label: str,
    currentness_status: str = "Current",
    source_status: str = "downloaded_existing",
) -> dict:
    row = _catalog_row(
        source_record_id=source_record_id,
        title=title,
        source_status=source_status,
        citation_label=citation_label,
        currentness_notes=currentness_status,
    )
    row["metadata"] = {
        "loader_contract": "source_register_v1",
        "authority_document_id": authority_document_id,
        "authority_document_class_id": "authority_document",
        "authority_tier": authority_tier,
        "currentness_status": currentness_status,
        "currentness_notes": currentness_status,
    }
    return row


def _inventory(families: list[dict] | None = None) -> dict:
    return {
        "schema_version": "authority-universe-families-v1",
        "authority_universe_family_inventory_id": "test-inventory",
        "source_set": {"source_set_id": "source-set-current"},
        "summary": {"authority_family_count": len(families or _default_families())},
        "authority_families": families or _default_families(),
    }


def _default_families() -> list[dict]:
    return [
        {
            "family_id": "source_only_family",
            "status": "source_only",
            "source_record_ids": ["R1EA-001", "R1EA-160"],
            "open_inventory_gaps": [],
        },
        {
            "family_id": "environmental_justice_civil_rights",
            "status": "candidate",
            "source_record_ids": [],
            "open_inventory_gaps": ["source rows needed"],
        },
        {
            "family_id": "superseded_family",
            "status": "superseded",
            "source_record_ids": ["R1EA-002"],
            "open_inventory_gaps": [],
            "supersession": {
                "replacement_family_id": "source_only_family",
                "current_source_record_ids": ["R1EA-002"],
            },
        },
    ]


def _decisions() -> dict:
    return {
        "schema_version": "test-decisions",
        "decisions": [
            {
                "authority_family_id": "environmental_justice_civil_rights",
                "decision_status": "documented_non_addition_for_milestone_2",
            }
        ],
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
