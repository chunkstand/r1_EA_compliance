from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.forest_plan_component_eval import (
    run_forest_plan_component_eval,
)


class ForestPlanComponentEvalTests(unittest.TestCase):
    def test_component_eval_scores_adjudicated_cases_and_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "component-eval"
            _write_review_artifacts(review_dir)
            eval_file = root / "component_eval.json"
            _write_eval_contract(eval_file)

            result = run_forest_plan_component_eval(
                output_dir=root / "source_library",
                review_id="component-eval",
                eval_file=eval_file,
            )

            self.assertTrue(result.summary["passed"])
            self.assertEqual(result.summary["case_count"], 3)
            self.assertEqual(result.summary["passed_case_count"], 3)
            metrics = result.summary["metrics"]
            self.assertEqual(metrics["component_applicability_precision"], 1.0)
            self.assertEqual(metrics["component_applicability_recall"], 1.0)
            self.assertEqual(metrics["applicable_standard_recall"], 1.0)
            self.assertEqual(metrics["false_applicable_component_rate"], 0.0)
            self.assertEqual(metrics["package_section_match_rate"], 1.0)
            self.assertEqual(metrics["plan_source_citation_correctness_rate"], 1.0)
            self.assertEqual(metrics["package_evidence_citation_correctness_rate"], 1.0)
            self.assertEqual(metrics["resolved_compliance_status_rate"], 1.0)
            self.assertEqual(metrics["reviewer_resolution_closure_rate"], 0.666667)
            self.assertEqual(metrics["reviewer_resolution_state_match_rate"], 1.0)
            payload = json.loads(result.output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "forest-plan-component-eval-results-v0")
            self.assertEqual(len(payload["case_results"]), 3)

    def test_component_eval_fails_on_component_level_mismatches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "component-eval"
            _write_review_artifacts(review_dir)
            eval_file = root / "component_eval.json"
            _write_eval_contract(
                eval_file,
                cases=[
                    {
                        "case_id": "std-1-wrong-section",
                        "component_id": "component-std-1",
                        "component_type": "standard",
                        "applicability_status": "applicable",
                        "applicable_standard": True,
                        "compliance_status": "complies",
                        "package_section": "Wrong Section",
                        "plan_source_citations": ["PLAN-001"],
                        "package_evidence_citations": ["PKG-001"],
                        "reviewer_resolution_state": "closed",
                    }
                ],
                thresholds={
                    "package_section_match_rate": {"min": 1.0},
                },
            )

            result = run_forest_plan_component_eval(
                output_dir=root / "source_library",
                review_id="component-eval",
                eval_file=eval_file,
            )

            self.assertFalse(result.summary["passed"])
            self.assertEqual(
                result.summary["failure_category_counts"],
                {"package_section_mismatch": 1},
            )
            checks = {check["name"]: check for check in result.summary["checks"]}
            self.assertFalse(checks["eval_cases_pass"]["passed"])
            self.assertFalse(checks["metric_thresholds_met"]["passed"])

    def test_component_eval_requires_exact_citation_sets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "component-eval"
            _write_review_artifacts(review_dir)
            coverage_path = review_dir / "forest_plan_applicable_standard_coverage.json"
            coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
            coverage["standards"][0]["plan_source_citations"].append("PLAN-EXTRA")
            coverage["standards"][0]["package_evidence_citations"].append("PKG-EXTRA")
            _write_json(coverage_path, coverage)
            eval_file = root / "component_eval.json"
            _write_eval_contract(eval_file)

            result = run_forest_plan_component_eval(
                output_dir=root / "source_library",
                review_id="component-eval",
                eval_file=eval_file,
            )

            self.assertFalse(result.summary["passed"])
            self.assertEqual(
                result.summary["failure_category_counts"],
                {
                    "package_evidence_citation_mismatch": 1,
                    "plan_source_citation_mismatch": 1,
                },
            )

    def test_component_eval_checks_all_review_artifact_identities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            review_dir = root / "source_library" / "reviews" / "component-eval"
            _write_review_artifacts(review_dir)
            coverage_path = review_dir / "forest_plan_applicable_standard_coverage.json"
            coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
            coverage["source_set_id"] = "source-set-stale"
            _write_json(coverage_path, coverage)
            eval_file = root / "component_eval.json"
            _write_eval_contract(eval_file)

            result = run_forest_plan_component_eval(
                output_dir=root / "source_library",
                review_id="component-eval",
                eval_file=eval_file,
            )

            self.assertFalse(result.summary["passed"])
            checks = {check["name"]: check for check in result.summary["checks"]}
            self.assertFalse(checks["review_identity_matches_contract"]["passed"])
            identities = checks["review_identity_matches_contract"]["details"]["artifacts"]
            self.assertIn(
                {
                    "artifact": "standard_coverage",
                    "review_id": "component-eval",
                    "source_set_id": "source-set-stale",
                },
                identities,
            )


def _write_review_artifacts(review_dir: Path) -> None:
    review_dir.mkdir(parents=True, exist_ok=True)
    findings = {
        "schema_version": "forest-plan-component-findings-v0",
        "review_id": "component-eval",
        "source_set_id": "source-set-test",
        "summary": {
            "review_id": "component-eval",
            "source_set_id": "source-set-test",
        },
        "components": [
            _component("component-std-1", "standard"),
            _component("component-std-2", "standard"),
            _component("component-dc-1", "desired_condition"),
        ],
        "findings": [
            _finding(
                "component-std-1",
                component_type="standard",
                applicability_status="applicable",
                finding_status="supported",
                compliance_status="complies",
                package_citation="PKG-001",
            ),
            _finding(
                "component-std-2",
                component_type="standard",
                applicability_status="not_applicable",
                finding_status="not_applicable",
                compliance_status="not_applicable",
                package_citation="PKG-001",
            ),
            _finding(
                "component-dc-1",
                component_type="desired_condition",
                applicability_status="applicable",
                finding_status="gap",
                compliance_status="not_evaluated_for_compliance",
                reviewer_resolution_items=[
                    {"component_id": "component-dc-1", "reason": "missing_package_evidence"}
                ],
            ),
        ],
    }
    coverage = {
        "schema_version": "forest-plan-applicable-standard-coverage-v0",
        "review_id": "component-eval",
        "source_set_id": "source-set-test",
        "passed": True,
        "standards": [
            {
                "component_id": "component-std-1",
                "component_key": "FW-STD-ONE-01",
                "applicability_status": "applicable",
                "compliance_status": "complies",
                "standard_applied": True,
                "ea_review_section": "EA section 3.1",
                "plan_source_citations": ["PLAN-001"],
                "package_evidence_citations": ["PKG-001"],
            },
            {
                "component_id": "component-std-2",
                "component_key": "FW-STD-TWO-01",
                "applicability_status": "not_applicable",
                "compliance_status": "not_applicable",
                "standard_applied": True,
                "ea_review_section": "Plan Consistency Table",
                "plan_source_citations": ["PLAN-001"],
                "package_evidence_citations": ["PKG-001"],
            },
        ],
    }
    queue = {
        "schema_version": "forest-plan-reviewer-resolution-queue-v0",
        "review_id": "component-eval",
        "source_set_id": "source-set-test",
        "item_count": 1,
        "items": [
            {
                "item_id": "component-dc-1-resolution",
                "finding_id": "component-dc-1-finding",
                "component_id": "component-dc-1",
                "reason": "missing_package_evidence",
            }
        ],
    }
    _write_json(review_dir / "forest_plan_component_findings.json", findings)
    _write_json(review_dir / "forest_plan_applicable_standard_coverage.json", coverage)
    _write_json(review_dir / "forest_plan_reviewer_resolution_queue.json", queue)


def _write_eval_contract(
    path: Path,
    *,
    cases: list[dict] | None = None,
    thresholds: dict | None = None,
) -> None:
    payload = {
        "schema_version": "forest-plan-component-eval-v0",
        "eval_id": "component-eval-test",
        "review_id": "component-eval",
        "source_set_id": "source-set-test",
        "metric_thresholds": thresholds
        or {
            "component_applicability_precision": {"min": 1.0},
            "component_applicability_recall": {"min": 1.0},
            "applicable_standard_recall": {"min": 1.0},
            "false_applicable_component_rate": {"max": 0.0},
            "reviewer_resolution_closure_rate": {"min": 0.666667},
            "reviewer_resolution_state_match_rate": {"min": 1.0},
        },
        "cases": cases
        or [
            {
                "case_id": "std-1-applicable",
                "component_id": "component-std-1",
                "component_type": "standard",
                "applicability_status": "applicable",
                "applicable_standard": True,
                "compliance_status": "complies",
                "package_section": "EA section 3.1",
                "plan_source_citations": ["PLAN-001"],
                "package_evidence_citations": ["PKG-001"],
                "reviewer_resolution_state": "closed",
            },
            {
                "case_id": "std-2-not-applicable",
                "component_id": "component-std-2",
                "component_type": "standard",
                "applicability_status": "not_applicable",
                "applicable_standard": False,
                "compliance_status": "not_applicable",
                "package_section": "Plan Consistency Table",
                "plan_source_citations": ["PLAN-001"],
                "package_evidence_citations": ["PKG-001"],
                "reviewer_resolution_state": "closed",
            },
            {
                "case_id": "dc-1-open-gap",
                "component_id": "component-dc-1",
                "component_type": "desired_condition",
                "applicability_status": "applicable",
                "plan_source_citations": ["PLAN-001"],
                "package_evidence_citations": [],
                "reviewer_resolution_state": "open",
            },
        ],
    }
    _write_json(path, payload)


def _component(component_id: str, component_type: str) -> dict:
    return {
        "component_id": component_id,
        "component_type": component_type,
        "component_text": f"{component_type} text",
    }


def _finding(
    component_id: str,
    *,
    component_type: str,
    applicability_status: str,
    finding_status: str,
    compliance_status: str,
    package_citation: str | None = None,
    reviewer_resolution_items: list[dict] | None = None,
) -> dict:
    package_evidence = (
        [
            {
                "citation_label": package_citation,
                "review_section": "EA section 3.1",
            }
        ]
        if package_citation
        else []
    )
    return {
        "finding_id": f"{component_id}-finding",
        "component_id": component_id,
        "component_type": component_type,
        "applicability_status": applicability_status,
        "finding_status": finding_status,
        "compliance_status": compliance_status,
        "plan_source_evidence": [{"citation_label": "PLAN-001"}],
        "package_evidence": package_evidence,
        "reviewer_resolution_items": reviewer_resolution_items or [],
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
