from __future__ import annotations

import json
from pathlib import Path

from usfs_r1_ea_sources.draft_generation import run_draft_generate
from usfs_r1_ea_sources.draft_generation_eval import run_draft_generation_eval
from tests.support.draft_generation_fixtures import write_minimal_draft_generation_config
from tests.support.draft_generation_fixtures import write_minimal_draft_generation_review


def test_draft_generation_eval_runs_fail_closed_fixture_cases(tmp_path) -> None:
    output_dir = tmp_path / "source_library"
    review_id = "review-test"
    source_set_id = "source-set-test"
    write_minimal_draft_generation_review(output_dir, review_id=review_id, source_set_id=source_set_id)
    config_path = write_minimal_draft_generation_config(
        tmp_path / "draft_generation_config.json",
        review_id=review_id,
        source_set_id=source_set_id,
    )
    eval_path = tmp_path / "draft_generation_eval.json"
    eval_path.write_text(
        json.dumps(
            {
                "schema_version": "draft-generation-eval-v1",
                "review_id": review_id,
                "cases": [
                    {
                        "case_id": "unsupported_legal_conclusion_rejected",
                        "mutation": "request_unsupported_legal_conclusion",
                        "required_refusal_category": "unsupported_legal_conclusion",
                        "expected_validation_passed": False,
                    },
                    {
                        "case_id": "missing_citation_rejected",
                        "mutation": "drop_citations_from_first_finding",
                        "required_failure_category": "missing_citation",
                        "expected_validation_passed": False,
                    },
                    {
                        "case_id": "stale_authority_rejected",
                        "mutation": "mark_authority_paths_stale",
                        "required_failure_category": "stale_authority",
                        "expected_validation_passed": False,
                    },
                    {
                        "case_id": "contradictory_evidence_rejected",
                        "mutation": "conflict_first_finding_status",
                        "required_failure_category": "contradictory_evidence",
                        "expected_validation_passed": False,
                    },
                    {
                        "case_id": "reviewer_warning_inserted_for_unresolved_issues",
                        "mutation": "retain_reviewer_warning_inputs",
                        "warning_required": True,
                        "expected_validation_passed": True,
                    },
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    run_draft_generate(output_dir=output_dir, review_id=review_id, config_path=config_path)
    result = run_draft_generation_eval(
        output_dir=output_dir,
        review_id=review_id,
        eval_path=eval_path,
        config_path=config_path,
    )
    payload = _read_json(result.output_path)

    assert result.summary["passed"] is True
    assert result.summary["case_count"] == 5
    assert result.summary["passed_case_count"] == 5
    assert result.summary["live_validation_passed"] is True
    assert payload["schema_version"] == "draft-generation-eval-results-v1"
    assert all(case["passed"] for case in payload["cases"])


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
