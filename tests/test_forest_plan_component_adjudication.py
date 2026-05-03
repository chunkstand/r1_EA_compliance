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


def _write_review_artifacts(root: Path) -> Path:
    review_dir = root / "source_library" / "reviews" / "v1-unit"
    review_dir.mkdir(parents=True, exist_ok=True)
    components = [
        {
            "component_id": "fp-std-01",
            "component_type": "standard",
            "component_text": "Standard 01 requires mitigation.",
        },
        {
            "component_id": "fp-gdl-01",
            "component_type": "guideline",
            "component_text": "Guideline 01 should be considered.",
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
        "plan_source_evidence": [{"chunk_id": "chunk-plan"}],
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
