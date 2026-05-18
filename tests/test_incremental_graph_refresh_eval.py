from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.incremental_graph_refresh_eval import (
    run_incremental_graph_refresh_eval,
)


class IncrementalGraphRefreshEvalTests(unittest.TestCase):
    def test_incremental_graph_refresh_eval_passes_with_currentness_and_graph_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            currentness_dir = output_dir / "derived" / source_set_id / "authority_currentness"
            knowledge_graph_dir = output_dir / "derived" / source_set_id / "knowledge_graph"
            currentness_dir.mkdir(parents=True, exist_ok=True)
            knowledge_graph_dir.mkdir(parents=True, exist_ok=True)
            (currentness_dir / "authority_currentness_report.json").write_text(
                json.dumps(
                    {
                        "source_set_id": source_set_id,
                        "summary": {
                            "validation_passed": True,
                            "documented_source_gap_count": 1,
                            "documented_source_non_addition_count": 1,
                            "superseded_replacement_confirmed_family_count": 2,
                            "temporal_lineage_record_count": 3,
                        },
                        "validation": {"passed": True, "checks": []},
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            (knowledge_graph_dir / "nepa_3d_graph_summary.json").write_text(
                json.dumps(
                    {
                        "source_set_id": source_set_id,
                        "validation_passed": True,
                        "failed_validation_check_count": 0,
                        "readiness_blocker_counts": {"superseded_source": 1},
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            (knowledge_graph_dir / "graph_health_eval_report.json").write_text(
                json.dumps(
                    {
                        "source_set_id": source_set_id,
                        "summary": {"passed": True},
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            (knowledge_graph_dir / "graph_accuracy_eval_report.json").write_text(
                json.dumps(
                    {
                        "source_set_id": source_set_id,
                        "summary": {"passed": True},
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            eval_path = output_dir / "incremental_graph_refresh_eval.json"
            eval_path.write_text(
                json.dumps(
                    {
                        "schema_version": "incremental-graph-refresh-eval-v1",
                        "contract_id": "incremental-graph-refresh-eval-v1",
                        "version": "1.0.0",
                        "allowed_source_set_ids": [source_set_id],
                        "minimum_documented_source_change_count": 2,
                        "minimum_superseded_replacement_confirmed_family_count": 1,
                        "minimum_temporal_lineage_record_count": 1,
                        "required_blocker_types": ["superseded_source"],
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            result = run_incremental_graph_refresh_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                eval_path=eval_path,
            )

            self.assertTrue(result.summary["passed"])
            self.assertTrue(result.output_path.exists())
            self.assertEqual(result.summary["documented_source_change_count"], 2)

    def test_incremental_graph_refresh_eval_fails_when_required_blocker_type_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            currentness_dir = output_dir / "derived" / source_set_id / "authority_currentness"
            knowledge_graph_dir = output_dir / "derived" / source_set_id / "knowledge_graph"
            currentness_dir.mkdir(parents=True, exist_ok=True)
            knowledge_graph_dir.mkdir(parents=True, exist_ok=True)
            (currentness_dir / "authority_currentness_report.json").write_text(
                json.dumps(
                    {
                        "source_set_id": source_set_id,
                        "summary": {
                            "validation_passed": True,
                            "documented_source_gap_count": 1,
                            "documented_source_non_addition_count": 0,
                            "superseded_replacement_confirmed_family_count": 1,
                            "temporal_lineage_record_count": 1,
                        },
                        "validation": {"passed": True, "checks": []},
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            (knowledge_graph_dir / "nepa_3d_graph_summary.json").write_text(
                json.dumps(
                    {
                        "source_set_id": source_set_id,
                        "validation_passed": True,
                        "failed_validation_check_count": 0,
                        "readiness_blocker_counts": {"candidate_blocked_source": 1},
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )
            (knowledge_graph_dir / "graph_health_eval_report.json").write_text(
                json.dumps({"source_set_id": source_set_id, "summary": {"passed": True}}, sort_keys=True),
                encoding="utf-8",
            )
            (knowledge_graph_dir / "graph_accuracy_eval_report.json").write_text(
                json.dumps({"source_set_id": source_set_id, "summary": {"passed": True}}, sort_keys=True),
                encoding="utf-8",
            )
            eval_path = output_dir / "incremental_graph_refresh_eval.json"
            eval_path.write_text(
                json.dumps(
                    {
                        "schema_version": "incremental-graph-refresh-eval-v1",
                        "contract_id": "incremental-graph-refresh-eval-v1",
                        "version": "1.0.0",
                        "required_blocker_types": ["superseded_source"],
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            result = run_incremental_graph_refresh_eval(
                output_dir=output_dir,
                source_set_id=source_set_id,
                eval_path=eval_path,
            )

            self.assertFalse(result.summary["passed"])
            self.assertEqual(result.summary["observed_blocker_types"], ["candidate_blocked_source"])


if __name__ == "__main__":
    unittest.main()
