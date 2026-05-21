from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.retrieval import build_retrieval_index
from usfs_r1_ea_sources.retrieval import run_retrieval_eval

from tests.support.retrieval_fixtures import _chunk
from tests.support.retrieval_fixtures import _write_catalog_sqlite
from tests.support.retrieval_fixtures import _write_chunks
from tests.support.retrieval_fixtures import _write_extraction_diagnostics


class RetrievalEvalTests(unittest.TestCase):
    def test_retrieval_eval_scores_expected_sources_terms_and_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-003"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-003",
                        title="Scoping rule",
                        document_role="regulation",
                        authority_level="federal_regulation",
                        citation_label="R1EA-003 | Scoping rule | artifact abc123",
                        text="Scoping shall invite public comment about environmental concerns.",
                    )
                ],
            )
            _write_catalog_sqlite(output_dir, {"R1EA-003": ["Scoping"]})
            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
            eval_file = output_dir / "eval.json"
            eval_file.write_text(
                json.dumps(
                    [
                        {
                            "id": "scoping",
                            "query": "scoping public comment",
                            "expected_source_record_ids": ["R1EA-003"],
                            "expected_terms": ["scoping", "public comment"],
                            "filters": {"review_topic": "Scoping"},
                        }
                    ],
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            eval_result = run_retrieval_eval(index_path=result.sqlite_path, eval_file=eval_file)

            self.assertTrue(eval_result.summary["passed"])
            self.assertEqual(eval_result.summary["metrics"]["pass_rate"], 1.0)
            self.assertEqual(eval_result.summary["metrics"]["unsupported_answer_rate"], 0.0)
            self.assertTrue(eval_result.output_path.exists())

    def test_retrieval_eval_supports_expected_zero_hit_cases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-003"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-003",
                        title="Scoping rule",
                        document_role="regulation",
                        authority_level="federal_regulation",
                        citation_label="R1EA-003 | Scoping rule | artifact abc123",
                        text="Scoping shall invite public comment about environmental concerns.",
                    )
                ],
            )
            _write_catalog_sqlite(output_dir, {"R1EA-003": ["Scoping"]})
            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
            eval_file = output_dir / "eval.json"
            eval_file.write_text(
                json.dumps(
                    [
                        {
                            "id": "missing-gap",
                            "query": "missing biological assessment",
                            "expect_no_hits": True,
                            "filters": {"citation": "R1PLAN-missing-gap-001"},
                        }
                    ],
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            eval_result = run_retrieval_eval(index_path=result.sqlite_path, eval_file=eval_file)

            self.assertTrue(eval_result.summary["passed"])
            self.assertEqual(eval_result.summary["passed_count"], 1)
            self.assertEqual(eval_result.summary["metrics"]["unsupported_answer_rate"], 0.0)
            case = eval_result.summary["cases"][0]
            self.assertTrue(case["expect_no_hits"])
            self.assertEqual(case["hit_count"], 0)
            self.assertEqual(case["failure_reasons"], [])
