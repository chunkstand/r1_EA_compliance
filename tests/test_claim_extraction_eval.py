from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from usfs_r1_ea_sources.claim_extraction_eval import _load_eval_contract
from usfs_r1_ea_sources.claim_extraction_eval import _claim_relevance
from usfs_r1_ea_sources.claim_extraction_eval import _expected_terms_found
from usfs_r1_ea_sources.claim_extraction_eval import _load_validated_claims_for_eval
from usfs_r1_ea_sources.claim_extraction_eval import _query_claims


class ClaimExtractionEvalTests(unittest.TestCase):
    def test_load_eval_contract_accepts_legacy_case_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "claim_eval.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "id": "legacy-case",
                            "query": "FONSI public",
                            "expected_source_record_ids": ["R1EA-014"],
                        }
                    ],
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            contract, cases, legacy_format = _load_eval_contract(path)

            self.assertTrue(legacy_format)
            self.assertEqual(contract["schema_version"], "legacy-claim-eval-list-v0")
            self.assertEqual(contract["eval_id"], "legacy-claim_eval")
            self.assertEqual(cases[0]["id"], "legacy-case")

    def test_load_eval_contract_rejects_unsupported_or_empty_filters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "claim_eval.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": "claim-eval-v1",
                        "eval_id": "bad-filters",
                        "coverage_requirements": {
                            "case_count": 0,
                            "hard_negative_case_count": 0,
                            "multi_source_or_type_confusion_case_count": 0,
                        },
                        "metric_thresholds": {},
                        "cases": [
                            {
                                "id": "bad-filter",
                                "query": "FONSI public",
                                "filters": {
                                    "source_record_ids": ["R1EA-014"],
                                    "claim_type": "",
                                },
                            }
                        ],
                    },
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "unsupported filters"):
                _load_eval_contract(path)

    def test_query_claims_applies_filters_and_ranks_exact_matches_first(self) -> None:
        results = _query_claims(
            [
                _claim(
                    claim_id="claim:1",
                    source_record_id="R1EA-014",
                    claim_text="USDA shall make the FONSI available to the public.",
                    review_topics=["FONSI availability"],
                ),
                _claim(
                    claim_id="claim:2",
                    source_record_id="R1EA-014",
                    claim_text="USDA shall make notices available to the public after review.",
                    review_topics=["Public notice timing"],
                    title="Public notices",
                ),
                _claim(
                    claim_id="claim:3",
                    source_record_id="R1EA-999",
                    claim_text="Forest plans should identify public coordination steps.",
                    review_topics=["Forest plan consistency"],
                ),
            ],
            query="FONSI available public",
            filters={"source_record_id": "R1EA-014"},
            limit=5,
        )

        self.assertEqual([result["claim_id"] for result in results], ["claim:1", "claim:2"])
        self.assertGreater(results[0]["score"], results[1]["score"])

    def test_query_claims_source_record_filter_supports_aliases(self) -> None:
        results = _query_claims(
            [
                _claim(
                    claim_id="claim:1",
                    source_record_id="USDA-003",
                    claim_text="Notification shall be in the manner used to consult.",
                )
            ],
            query="notification consult",
            filters={"source_record_id": "R1EA-014"},
            limit=5,
        )

        self.assertEqual([result["claim_id"] for result in results], ["claim:1"])

    def test_claim_relevance_treats_aliased_source_record_ids_as_matches(self) -> None:
        relevance = _claim_relevance(
            [
                _claim(
                    claim_id="claim:1",
                    source_record_id="USDA-003",
                    claim_text="Notification shall be in the manner used to consult.",
                )
            ],
            expected_sources=["R1EA-014"],
            expected_claim_types=[],
            expected_terms=[],
        )

        self.assertEqual(relevance, [True])

    def test_claim_relevance_accepts_term_signal_when_expected_type_is_on_another_hit(self) -> None:
        relevance = _claim_relevance(
            [
                _claim(
                    claim_id="claim:1",
                    source_record_id="USDA-004",
                    claim_text=(
                        "USDA subcomponents shall make documents associated with the NEPA review "
                        "available pursuant to the Freedom of Information Act."
                    ),
                    claim_type="obligation",
                )
            ],
            expected_sources=["R1EA-015"],
            expected_claim_types=["condition"],
            expected_terms=["documents associated with the NEPA review"],
        )

        self.assertEqual(relevance, [True])

    def test_expected_terms_found_accepts_morphology_tolerant_phrase_matches(self) -> None:
        self.assertTrue(
            _expected_terms_found(
                ["independent evaluation"],
                [
                    _claim(
                        claim_id="claim:1",
                        source_record_id="USDA-005",
                        claim_text=(
                            "The subcomponent shall independently evaluate the information "
                            "or documentation submitted."
                        ),
                    )
                ],
            )
        )

    def test_claim_relevance_does_not_double_count_consumed_alias_matches(self) -> None:
        relevance = _claim_relevance(
            [
                _claim(
                    claim_id="claim:1",
                    source_record_id="USDA-003",
                    claim_text="Notification shall be in the manner used to consult.",
                ),
                _claim(
                    claim_id="claim:2",
                    source_record_id="USDA-003",
                    claim_text="Notification shall be in the manner used to consult.",
                ),
            ],
            expected_sources=["R1EA-014"],
            expected_claim_types=[],
            expected_terms=[],
        )

        self.assertEqual(relevance, [True, False])

    def test_load_validated_claims_for_eval_requires_readiness_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            claims_path = Path(tmp) / "derived" / "source-set-test" / "claims" / "claims.jsonl"
            claims_path.parent.mkdir(parents=True, exist_ok=True)
            claims_path.write_text(
                json.dumps(_claim(claim_id="claim:1", source_record_id="R1EA-014")) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(FileNotFoundError, "Missing claim readiness artifact"):
                _load_validated_claims_for_eval(claims_path)


def _claim(
    *,
    claim_id: str,
    source_record_id: str,
    claim_text: str = "USDA shall make the FONSI available to the public.",
    review_topics: list[str] | None = None,
    title: str = "FONSI availability",
    claim_type: str = "obligation",
) -> dict:
    return {
        "claim_id": claim_id,
        "claim_type": claim_type,
        "claim_text": claim_text,
        "source_record_id": source_record_id,
        "chunk_id": f"chunk:{claim_id}",
        "citation_label": f"{source_record_id} | Test claim | artifact abc123",
        "authority_level": "federal_regulation",
        "document_role": "regulation",
        "review_topics": review_topics or [],
        "source_set_id": "source-set-test",
        "artifact_sha256": _text_sha256("artifact"),
        "artifact_path": "artifacts/test.txt",
        "parser_name": "unit",
        "parser_version": "0.1.0",
        "source_text_path": "texts/source.txt",
        "source_char_start": 0,
        "source_char_end": len(claim_text),
        "chunk_char_start": 0,
        "chunk_char_end": len(claim_text),
        "content_sha256": _text_sha256(claim_text),
        "title": title,
    }


def _text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
