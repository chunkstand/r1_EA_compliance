from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from usfs_r1_ea_sources.rule_claim_binding_eval import _load_eval_contract
from usfs_r1_ea_sources.rule_claim_binding_eval import _load_validated_links_for_eval
from usfs_r1_ea_sources.rule_claim_binding_eval import _query_links


class RuleClaimBindingEvalTests(unittest.TestCase):
    def test_load_eval_contract_accepts_legacy_case_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rule_claim_eval.json"
            path.write_text(
                json.dumps(
                    [
                        {
                            "id": "legacy-case",
                            "rule_id": "purpose_need",
                            "expected_source_record_ids": ["R1EA-001"],
                        }
                    ],
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            contract, cases, legacy_format = _load_eval_contract(path)

            self.assertTrue(legacy_format)
            self.assertEqual(contract["schema_version"], "legacy-rule-claim-link-eval-list-v0")
            self.assertEqual(contract["eval_id"], "legacy-rule_claim_eval")
            self.assertEqual(cases[0]["id"], "legacy-case")

    def test_load_eval_contract_rejects_unsupported_or_empty_filters(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rule_claim_eval.json"
            path.write_text(
                json.dumps(
                    {
                        "schema_version": "rule-claim-link-eval-v1",
                        "eval_id": "bad-filters",
                        "coverage_requirements": {
                            "case_count": 0,
                            "hard_negative_case_count": 0,
                            "multi_source_case_count": 0,
                        },
                        "metric_thresholds": {},
                        "cases": [
                            {
                                "id": "bad-filter",
                                "rule_id": "purpose_need",
                                "filters": {
                                    "source_record_ids": ["R1EA-001"],
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

    def test_query_links_applies_filters_and_ranks_exact_matches_first(self) -> None:
        results = _query_links(
            [
                _link(
                    link_id="rule-claim-link:1",
                    claim_id="claim:1",
                    source_record_id="R1EA-001",
                    claim_text="The environmental assessment should describe the purpose and need.",
                    score=0.95,
                    matched_terms=["purpose", "need"],
                ),
                _link(
                    link_id="rule-claim-link:2",
                    claim_id="claim:2",
                    source_record_id="R1EA-001",
                    claim_text="The assessment should describe alternatives and mitigation.",
                    score=0.45,
                    matched_terms=["purpose"],
                    rank=2,
                ),
                _link(
                    link_id="rule-claim-link:3",
                    claim_id="claim:3",
                    source_record_id="R1EA-999",
                    claim_text="Mitigation measures should be described when relevant.",
                    rule_id="mitigation",
                    score=0.9,
                ),
            ],
            rule_id="purpose_need",
            filters={"source_record_id": "R1EA-001"},
            limit=5,
        )

        self.assertEqual([result["claim_id"] for result in results], ["claim:1", "claim:2"])
        self.assertGreater(results[0]["score"], results[1]["score"])

    def test_load_validated_links_for_eval_requires_readiness_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            links_path = (
                Path(tmp)
                / "derived"
                / "source-set-test"
                / "rule_claim_links"
                / "unit-nepa-ea"
                / "0.1.0"
                / "rule_claim_links.jsonl"
            )
            links_path.parent.mkdir(parents=True, exist_ok=True)
            links_path.write_text(
                json.dumps(_link(link_id="rule-claim-link:1", claim_id="claim:1")) + "\n",
                encoding="utf-8",
            )

            with self.assertRaisesRegex(FileNotFoundError, "Missing rule-claim link readiness"):
                _load_validated_links_for_eval(links_path)


def _link(
    *,
    link_id: str,
    claim_id: str,
    source_record_id: str = "R1EA-001",
    claim_text: str = "The environmental assessment should describe the purpose and need.",
    rule_id: str = "purpose_need",
    score: float = 0.8,
    matched_terms: list[str] | None = None,
    rank: int = 1,
) -> dict:
    return {
        "link_id": link_id,
        "source_set_id": "source-set-test",
        "rule_id": rule_id,
        "rule_pack_id": "unit-nepa-ea",
        "rule_pack_version": "0.1.0",
        "rule_requirement": "The EA package should identify the purpose and need.",
        "rank": rank,
        "score": score,
        "matched_terms": matched_terms or ["purpose", "need"],
        "claim_id": claim_id,
        "claim_type": "guidance",
        "claim_text": claim_text,
        "source_record_id": source_record_id,
        "chunk_id": f"chunk:{claim_id}",
        "citation_label": f"{source_record_id} | Test claim | artifact abc123",
        "authority_level": "federal",
        "document_role": "regulation",
        "review_topics": ["EA purpose and need"],
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
    }


def _text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    unittest.main()
