from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.cli import build_parser
from usfs_r1_ea_sources.forest_plan_component_adjudication import (
    run_forest_plan_component_adjudication_eval,
)
from usfs_r1_ea_sources.forest_plan_component_adjudication import (
    write_forest_plan_component_adjudication_template,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMITTED_ADJUDICATION = (
    REPO_ROOT
    / "config"
    / "forest_plan_component_adjudications"
    / "region1-expansion-south-plateau-landscape-treatment.json"
)


class ForestPlanComponentAdjudicationTests(unittest.TestCase):
    def test_template_exports_open_component_queue_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = _write_review_artifacts(root)

            result = write_forest_plan_component_adjudication_template(
                output_dir=root / "source_library",
                review_id="v1-unit",
            )

            self.assertEqual(result.review_dir, review_dir)
            self.assertTrue(result.output_path.exists())
            self.assertTrue(result.markdown_path.exists())
            template = _read_json(result.output_path)
            self.assertEqual(template["schema_version"], "forest-plan-component-adjudication-v0")
            self.assertEqual(template["summary"]["queue_item_count"], 2)
            self.assertEqual(template["summary"]["pending_item_count"], 2)
            self.assertEqual(template["summary"]["markdown_path"], str(result.markdown_path))
            self.assertEqual(template["items"][0]["disposition"], "pending")
            self.assertEqual(
                template["items"][0]["component_source_ref"]["source_record_id"],
                "R1PLAN-unit-fp-std-01",
            )
            self.assertEqual(
                template["items"][0]["plan_source_record_ids"],
                ["R1PLAN-unit-fp-std-01"],
            )
            self.assertEqual(
                template["items"][0]["plan_source_citations"],
                ["Plan Citation fp-std-01"],
            )
            self.assertEqual(
                template["items"][0]["plan_source_evidence_refs"][0]["artifact_sha256"],
                "artifact-fp-std-01",
            )
            self.assertEqual(
                template["items"][0]["expected_current"],
                {
                    "applicability_status": "applicable",
                    "compliance_status": "insufficient_evidence",
                    "finding_status": "gap",
                    "queue_reason": "missing_package_evidence",
                },
            )
            markdown = result.markdown_path.read_text(encoding="utf-8")
            self.assertIn("# Forest Plan Component Adjudication Worklist", markdown)
            self.assertIn("fp-std-01", markdown)
            self.assertIn("Disposition: pending", markdown)

    def test_eval_passes_complete_adjudications(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_review_artifacts(root)
            adjudication_file = root / "adjudication.json"
            _write_adjudication(adjudication_file)

            result = run_forest_plan_component_adjudication_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                adjudication_file=adjudication_file,
            )

            self.assertTrue(result.summary["passed"])
            self.assertEqual(result.summary["queue_item_count"], 2)
            self.assertEqual(result.summary["resolved_adjudication_count"], 2)
            self.assertEqual(result.summary["pending_adjudication_count"], 0)
            self.assertEqual(result.summary["adjudication_completion_rate"], 1.0)
            self.assertEqual(result.summary["real_ea_omission_count"], 1)
            self.assertEqual(result.summary["system_miss_count"], 1)
            self.assertEqual(result.summary["real_ea_omission_rate"], 0.5)
            self.assertEqual(result.summary["system_miss_rate"], 0.5)
            self.assertEqual(
                result.summary["adjudication_outcome_counts"],
                {"real_ea_omission": 1, "system_miss": 1},
            )
            self.assertEqual(
                result.summary["real_ea_omission_disposition_counts"],
                {"true_ea_omission": 1},
            )
            self.assertEqual(
                result.summary["system_miss_disposition_counts"],
                {"component_inventory_overreach": 1},
            )
            report = _read_json(result.output_path)
            outcomes = {
                item["component_id"]: item["adjudication_outcome"]
                for item in report["item_results"]
            }
            self.assertEqual(outcomes["fp-std-01"], "real_ea_omission")
            self.assertEqual(outcomes["fp-gdl-01"], "system_miss")
            first_result = report["item_results"][0]
            self.assertEqual(
                first_result["plan_source_record_ids"],
                ["R1PLAN-unit-fp-std-01"],
            )
            self.assertEqual(
                first_result["plan_source_evidence_refs"][0]["citation_label"],
                "Plan Citation fp-std-01",
            )

    def test_eval_fails_pending_or_mismatched_adjudications(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_review_artifacts(root)
            adjudication_file = root / "adjudication.json"
            _write_adjudication(
                adjudication_file,
                item_updates={
                    "fp-std-01-missing_package_evidence": {
                        "disposition": "pending",
                        "rationale": "",
                        "expected_current": {"finding_status": "supported"},
                    }
                },
            )

            result = run_forest_plan_component_adjudication_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                adjudication_file=adjudication_file,
            )

            self.assertFalse(result.summary["passed"])
            failures = result.summary["failure_category_counts"]
            self.assertEqual(failures["adjudication_pending"], 1)
            self.assertEqual(failures["adjudication_expectation_mismatch"], 1)

    def test_eval_fails_incomplete_resolved_adjudication(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_review_artifacts(root)
            adjudication_file = root / "adjudication.json"
            _write_adjudication(
                adjudication_file,
                item_updates={
                    "fp-std-01-missing_package_evidence": {
                        "rationale": "",
                        "adjudicated_by": [],
                    }
                },
            )

            result = run_forest_plan_component_adjudication_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                adjudication_file=adjudication_file,
            )

            self.assertFalse(result.summary["passed"])
            self.assertEqual(
                result.summary["failure_category_counts"]["adjudication_incomplete"],
                1,
            )

    def test_eval_fails_resolved_adjudication_without_trace_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_review_artifacts(root)
            adjudication_file = root / "adjudication.json"
            _write_adjudication(
                adjudication_file,
                item_updates={
                    "fp-std-01-missing_package_evidence": {
                        "component_source_ref": {},
                        "plan_source_evidence_refs": [],
                    }
                },
            )

            result = run_forest_plan_component_adjudication_eval(
                output_dir=root / "source_library",
                review_id="v1-unit",
                adjudication_file=adjudication_file,
            )

            self.assertFalse(result.summary["passed"])
            self.assertEqual(
                result.summary["failure_category_counts"]["adjudication_trace_incomplete"],
                1,
            )
            missing = result.summary["checks"][2]["details"]["component_ids"]
            self.assertIn("fp-std-01", missing)

    def test_cli_accepts_component_adjudication_commands(self) -> None:
        parser = build_parser()
        template_args = parser.parse_args(
            [
                "forest-plan-component-adjudication-template",
                "--output-dir",
                "source_library",
                "--review-id",
                "v1-unit",
            ]
        )
        eval_args = parser.parse_args(
            [
                "forest-plan-component-adjudication-eval",
                "--output-dir",
                "source_library",
                "--review-id",
                "v1-unit",
                "--adjudication-file",
                "adjudication.json",
            ]
        )

        self.assertEqual(template_args.command, "forest-plan-component-adjudication-template")
        self.assertEqual(eval_args.command, "forest-plan-component-adjudication-eval")

    def test_committed_south_plateau_adjudication_tracks_resolved_queue(self) -> None:
        adjudication = _read_json(COMMITTED_ADJUDICATION)

        self.assertEqual(adjudication["schema_version"], "forest-plan-component-adjudication-v0")
        self.assertEqual(
            adjudication["review_id"],
            "region1-expansion-south-plateau-landscape-treatment",
        )
        self.assertEqual(
            adjudication["source_set_id"],
            "source-set-ba8d0feae79501b8",
        )
        self.assertEqual(
            adjudication["adjudication_id"],
            "region1-expansion-south-plateau-landscape-treatment-component-adjudication",
        )
        self.assertEqual(adjudication["adjudication"]["status"], "completed")
        self.assertEqual(adjudication["adjudication"]["method"], "tracked_replay_artifact_review")
        items = adjudication["items"]
        self.assertEqual(len(items), 31)
        self.assertTrue(all(item["disposition"] == "applicability_false_positive" for item in items))
        self.assertTrue(all(item["source_type"] == "package_scope_review" for item in items))


def _write_review_artifacts(root: Path) -> Path:
    review_dir = root / "source_library" / "reviews" / "v1-unit"
    review_dir.mkdir(parents=True, exist_ok=True)
    components = [
        {
            "component_id": "fp-std-01",
            "component_type": "standard",
            "component_text": "Standard 01 requires mitigation.",
            "source_record_id": "R1PLAN-unit-fp-std-01",
            "citation_label": "Plan Citation fp-std-01",
            "artifact_sha256": "artifact-fp-std-01",
            "content_sha256": "content-fp-std-01",
            "source_chunk_ids": ["chunk-plan-fp-std-01"],
        },
        {
            "component_id": "fp-gdl-01",
            "component_type": "guideline",
            "component_text": "Guideline 01 should be considered.",
            "source_record_id": "R1PLAN-unit-fp-gdl-01",
            "citation_label": "Plan Citation fp-gdl-01",
            "artifact_sha256": "artifact-fp-gdl-01",
            "content_sha256": "content-fp-gdl-01",
            "source_chunk_ids": ["chunk-plan-fp-gdl-01"],
        },
    ]
    findings = [
        _finding("fp-std-01", "standard", "insufficient_evidence"),
        _finding("fp-gdl-01", "guideline", "not_evaluated_for_compliance"),
    ]
    queue_items = [
        _queue_item("fp-std-01"),
        _queue_item("fp-gdl-01"),
    ]
    _write_json(
        review_dir / "forest_plan_component_findings.json",
        {
            "schema_version": "forest-plan-component-findings-v0",
            "review_id": "v1-unit",
            "source_set_id": "source-set-test",
            "summary": {
                "review_id": "v1-unit",
                "source_set_id": "source-set-test",
            },
            "components": components,
            "findings": findings,
        },
    )
    _write_json(
        review_dir / "forest_plan_reviewer_resolution_queue.json",
        {
            "schema_version": "forest-plan-reviewer-resolution-queue-v0",
            "review_id": "v1-unit",
            "source_set_id": "source-set-test",
            "item_count": 2,
            "items": queue_items,
        },
    )
    return review_dir


def _finding(component_id: str, component_type: str, compliance_status: str) -> dict:
    return {
        "finding_id": f"{component_id}-finding",
        "review_id": "v1-unit",
        "component_id": component_id,
        "component_type": component_type,
        "applicability_status": "applicable",
        "finding_status": "gap",
        "compliance_status": compliance_status,
        "applicability_basis": {
            "matched_context": {"management_area_ids": ["mgmt-test"]},
            "component_context": {"management_area_ids": ["mgmt-test"]},
            "package_evidence_terms": ["mitigation"],
        },
        "plan_source_evidence": [
            {
                "chunk_id": f"chunk-plan-{component_id}",
                "citation_label": f"Plan Citation {component_id}",
                "source_record_id": f"R1PLAN-unit-{component_id}",
                "title": "Unit Forest Plan",
                "document_role": "forest_plan",
                "page": 12,
                "provenance": {
                    "artifact_sha256": f"artifact-{component_id}",
                    "content_sha256": f"content-{component_id}",
                    "source_chunk_ids": [f"chunk-plan-{component_id}"],
                    "source_record_id": f"R1PLAN-unit-{component_id}",
                },
                "evidence_span": {
                    "source_char_start": 10,
                    "source_char_end": 40,
                    "text": "Plan component evidence.",
                },
            }
        ],
        "package_evidence": [],
    }


def _queue_item(component_id: str) -> dict:
    return {
        "item_id": f"{component_id}-missing_package_evidence",
        "finding_id": f"{component_id}-finding",
        "component_id": component_id,
        "reason": "missing_package_evidence",
        "severity": "medium",
        "finding_status": "gap",
        "applicability_status": "applicable",
    }


def _write_adjudication(path: Path, *, item_updates: dict[str, dict] | None = None) -> None:
    items = [
        _adjudication_item(
            "fp-std-01",
            disposition="true_ea_omission",
            compliance_status="insufficient_evidence",
        ),
        _adjudication_item(
            "fp-gdl-01",
            disposition="component_inventory_overreach",
            compliance_status="not_evaluated_for_compliance",
        ),
    ]
    item_updates = item_updates or {}
    for item in items:
        item.update(item_updates.get(item["item_id"], {}))
    _write_json(
        path,
        {
            "schema_version": "forest-plan-component-adjudication-v0",
            "adjudication_id": "v1-unit-component-adjudication",
            "review_id": "v1-unit",
            "source_set_id": "source-set-test",
            "adjudication": {
                "status": "complete",
                "method": "unit fixture",
                "adjudicated_by": ["unit-test"],
                "adjudicated_at": "2026-05-03T00:00:00Z",
            },
            "items": items,
        },
    )


def _adjudication_item(
    component_id: str,
    *,
    disposition: str,
    compliance_status: str,
) -> dict:
    return {
        "item_id": f"{component_id}-missing_package_evidence",
        "finding_id": f"{component_id}-finding",
        "component_id": component_id,
        "disposition": disposition,
        "adjudicated_at": "2026-05-03T00:00:00Z",
        "adjudicated_by": ["unit-test"],
        "source_type": "unit_fixture",
        "rationale": "Unit fixture adjudication.",
        "component_source_ref": {
            "source_record_id": f"R1PLAN-unit-{component_id}",
            "citation_label": f"Plan Citation {component_id}",
            "artifact_sha256": f"artifact-{component_id}",
            "content_sha256": f"content-{component_id}",
            "source_chunk_ids": [f"chunk-plan-{component_id}"],
        },
        "plan_source_record_ids": [f"R1PLAN-unit-{component_id}"],
        "plan_source_citations": [f"Plan Citation {component_id}"],
        "plan_source_evidence_refs": [
            {
                "source_record_id": f"R1PLAN-unit-{component_id}",
                "citation_label": f"Plan Citation {component_id}",
                "chunk_id": f"chunk-plan-{component_id}",
                "artifact_sha256": f"artifact-{component_id}",
                "content_sha256": f"content-{component_id}",
            }
        ],
        "package_source_record_ids": [],
        "package_evidence_citations": [],
        "package_evidence_refs": [],
        "expected_current": {
            "finding_status": "gap",
            "applicability_status": "applicable",
            "compliance_status": compliance_status,
            "queue_reason": "missing_package_evidence",
        },
    }


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
