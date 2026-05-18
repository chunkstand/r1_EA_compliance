from __future__ import annotations

from pathlib import Path
import tempfile

from usfs_r1_ea_sources.upstream_evaluation import run_upstream_evaluation


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config" / "upstream_evaluation_v1.json"
MISSING_CATEGORY_MANIFEST = ROOT / "tests" / "fixtures" / "upstream_eval" / "missing_category_manifest.json"
OUT_OF_TREE_MANIFEST = ROOT / "tests" / "fixtures" / "upstream_eval" / "out_of_tree_fixture_manifest.json"


def test_upstream_evaluation_rejects_missing_category_coverage() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = run_upstream_evaluation(
            manifest_path=MISSING_CATEGORY_MANIFEST,
            results_dir=Path(tmp) / "upstream-eval",
        )

        assert result.summary["passed"] is False
        check = _check(result.summary, "required_categories_have_expected_and_controlled_cases")
        assert check["passed"] is False
        assert check["details"]["thin_categories"]


def test_upstream_evaluation_rejects_out_of_tree_fixtures() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = run_upstream_evaluation(
            manifest_path=OUT_OF_TREE_MANIFEST,
            results_dir=Path(tmp) / "upstream-eval",
        )

        assert result.summary["passed"] is False
        check = _check(result.summary, "fixture_paths_are_in_tracked_roots")
        assert check["passed"] is False
        assert check["details"]["out_of_tree_fixture_paths"]


def test_upstream_evaluation_runs_real_manifest_and_writes_outputs() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = run_upstream_evaluation(
            manifest_path=MANIFEST,
            results_dir=Path(tmp) / "upstream-eval",
        )

        assert result.summary["passed"] is True
        assert result.output_path.exists()
        assert result.report_path.exists()
        assert result.summary["required_category_count"] == 19
        assert result.summary["case_count"] == 38
        assert result.summary["matched_case_count"] == 38
        assert all(
            lane_summary["status"] == "direct_eval_present"
            for lane_summary in result.summary["lane_summaries"]
        )


def _check(summary: dict, name: str) -> dict:
    return next(check for check in summary["contract_checks"] if check["name"] == name)
