from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.authority_currentness import (
    AUTHORITY_CURRENTNESS_REPORT_SCHEMA_VERSION,
)
from usfs_r1_ea_sources.authority_currentness import build_authority_currentness_report


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

            excluded_record = records[("source_only_family", "R1EA-160")]
            self.assertEqual(excluded_record["currentness_status"], "excluded_no_artifact")
            self.assertEqual(
                excluded_record["supersession_status"],
                "excluded_no_current_authority",
            )
            self.assertFalse(excluded_record["counts_as_current_authority"])

            superseded_record = records[("superseded_family", "R1EA-002")]
            self.assertEqual(
                superseded_record["supersession_status"],
                "superseded_replacement_source",
            )
            self.assertFalse(superseded_record["counts_as_current_authority"])

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


def _write_catalog(output_dir: Path, *, rows: list[dict]) -> None:
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
) -> dict:
    return {
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
