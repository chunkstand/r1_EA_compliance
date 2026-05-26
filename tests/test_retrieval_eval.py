from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.retrieval import build_retrieval_index
from usfs_r1_ea_sources.retrieval import run_retrieval_eval
from usfs_r1_ea_sources.retrieval_eval_runtime import _missing_expected_terms

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

    def test_retrieval_eval_treats_aliased_source_record_ids_as_expected_matches(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["FED-001"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="FED-001",
                        title="National Environmental Policy Act",
                        document_role="law",
                        authority_level="federal",
                        citation_label="FED-001 | National Environmental Policy Act | artifact abc123",
                        text="National Environmental Policy Act significance and environmental assessment requirements.",
                    )
                ],
            )
            _write_catalog_sqlite(output_dir, {"FED-001": ["NEPA"]})
            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
            eval_file = output_dir / "eval.json"
            eval_file.write_text(
                json.dumps(
                    [
                        {
                            "id": "nepa-alias",
                            "query": "environmental assessment significance",
                            "expected_source_record_ids": ["R1EA-003"],
                        }
                    ],
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            eval_result = run_retrieval_eval(index_path=result.sqlite_path, eval_file=eval_file)

            self.assertTrue(eval_result.summary["passed"])
            case = eval_result.summary["cases"][0]
            self.assertEqual(case["matched_expected_source_record_ids"], ["R1EA-003"])
            self.assertEqual(case["missing_expected_source_record_ids"], [])

    def test_retrieval_eval_supports_multiple_source_record_filters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["FED-003", "FOR-018"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="FED-003",
                        title="National Forest System Land Management Planning",
                        document_role="regulation",
                        authority_level="federal",
                        citation_label="FED-003 | Planning rule | artifact abc123",
                        text=(
                            "Every project and activity must be consistent with the "
                            "applicable plan components. The plan must describe how the "
                            "project or activity is consistent with the plan."
                        ),
                    ),
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="FOR-018",
                        title="2021 Land Management Plan",
                        document_role="forest_plan",
                        authority_level="federal",
                        citation_label="FOR-018 | Forest plan | artifact def456",
                        text=(
                            "This unrelated forest plan repeats project and activity "
                            "consistency language but is not the tracked authority source."
                        ),
                    ),
                ],
            )
            _write_catalog_sqlite(
                output_dir,
                {
                    "FED-003": ["Planning rule"],
                    "FOR-018": ["Forest plan"],
                },
            )
            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
            eval_file = output_dir / "eval.json"
            eval_file.write_text(
                json.dumps(
                    [
                        {
                            "id": "forest-plan-consistency",
                            "query": "project and activity consistent with applicable plan components",
                            "expected_source_record_ids": ["R1EA-023", "R1EA-024"],
                            "expected_terms": ["project and activity consistency"],
                            "filters": {
                                "authority_level": "federal",
                                "source_record_ids": ["R1EA-023", "R1EA-024"],
                            },
                        }
                    ],
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            eval_result = run_retrieval_eval(index_path=result.sqlite_path, eval_file=eval_file)

            self.assertTrue(eval_result.summary["passed"])
            case = eval_result.summary["cases"][0]
            self.assertEqual(case["matched_expected_source_record_ids"], ["R1EA-023", "R1EA-024"])
            self.assertEqual(case["missing_expected_source_record_ids"], [])
            self.assertEqual(
                case["filters"]["source_record_ids"],
                ["R1EA-023", "R1EA-024"],
            )

    def test_missing_expected_terms_accepts_morphology_tolerant_phrase_matches(self) -> None:
        self.assertEqual(
            _missing_expected_terms(
                ["project and activity consistency"],
                [
                    {
                        "title": "National Forest System Land Management Planning",
                        "citation_label": "FED-003 | Test artifact",
                        "evidence_span": {
                            "text": (
                                "Every project or activity must be consistent with the "
                                "applicable plan components."
                            )
                        },
                        "review_topics": [],
                    }
                ],
            ),
            [],
        )
