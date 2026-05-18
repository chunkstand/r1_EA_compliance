from __future__ import annotations

import json
from pathlib import Path

from usfs_r1_ea_sources.draft_generation import build_draft_generation_bundle
from usfs_r1_ea_sources.draft_generation import load_draft_generation_context
from usfs_r1_ea_sources.draft_generation import run_draft_generate
from tests.support.draft_generation_fixtures import write_minimal_draft_generation_config
from tests.support.draft_generation_fixtures import write_minimal_draft_generation_review


def test_run_draft_generate_writes_governed_output_family(tmp_path) -> None:
    output_dir = tmp_path / "source_library"
    review_id = "review-test"
    source_set_id = "source-set-test"
    write_minimal_draft_generation_review(output_dir, review_id=review_id, source_set_id=source_set_id)
    config_path = write_minimal_draft_generation_config(
        tmp_path / "draft_generation_config.json",
        review_id=review_id,
        source_set_id=source_set_id,
    )

    result = run_draft_generate(
        output_dir=output_dir,
        review_id=review_id,
        config_path=config_path,
    )

    assert result.summary["passed"] is True
    assert result.package_path.exists()
    assert result.validation_path.exists()
    assert result.traceability_path.exists()
    assert result.refusal_path.exists()
    assert result.defensibility_path.exists()

    package = _read_json(result.package_path)
    validation = _read_json(result.validation_path)
    unresolved = next(
        section for section in package["sections"] if section["section_id"] == "unresolved_issue_statements"
    )
    environmental = next(
        section
        for section in package["sections"]
        if section["section_id"] == "affected_environment_and_environmental_consequences"
    )

    assert package["schema_version"] == "draft-generation-package-v1"
    assert len(package["sections"]) == 5
    assert validation["summary"]["passed"] is True
    assert validation["summary"]["failure_category_counts"] == {}
    assert unresolved["readiness_status"] == "ready_with_reviewer_warnings"
    assert any(paragraph["warning_inserted"] for paragraph in unresolved["paragraphs"])
    assert all(paragraph["citations"] for paragraph in environmental["paragraphs"])


def test_build_draft_generation_bundle_refuses_unsupported_legal_output(tmp_path) -> None:
    output_dir = tmp_path / "source_library"
    review_id = "review-test"
    source_set_id = "source-set-test"
    write_minimal_draft_generation_review(output_dir, review_id=review_id, source_set_id=source_set_id)
    config_path = write_minimal_draft_generation_config(
        tmp_path / "draft_generation_config.json",
        review_id=review_id,
        source_set_id=source_set_id,
    )
    context = load_draft_generation_context(
        output_dir=output_dir,
        review_id=review_id,
        config_path=config_path,
    )

    bundle = build_draft_generation_bundle(
        context=context,
        requested_output_ids=list(context.config["section_order"]) + ["legal_sufficiency_determination"],
    )

    refusal_categories = {
        row["category"]
        for row in bundle.refusals["refusals"]
    }
    summary = bundle.validation["summary"]

    assert "unsupported_legal_conclusion" in refusal_categories
    assert summary["passed"] is False


def test_run_draft_generate_fails_closed_when_citations_are_missing(tmp_path) -> None:
    output_dir = tmp_path / "source_library"
    review_id = "review-test"
    source_set_id = "source-set-test"
    review_dir = write_minimal_draft_generation_review(
        output_dir,
        review_id=review_id,
        source_set_id=source_set_id,
    )
    config_path = write_minimal_draft_generation_config(
        tmp_path / "draft_generation_config.json",
        review_id=review_id,
        source_set_id=source_set_id,
    )
    decision_support_path = review_dir / "decision_support" / "ea_consistency_decision_support.json"
    decision_support = _read_json(decision_support_path)
    decision_support["authority_findings"][0]["ea_package_evidence"][0].pop("citation_label", None)
    decision_support["authority_findings"][0]["source_library_evidence"][0].pop("citation_label", None)
    decision_support_path.write_text(json.dumps(decision_support, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    result = run_draft_generate(
        output_dir=output_dir,
        review_id=review_id,
        config_path=config_path,
    )
    validation = _read_json(result.validation_path)

    assert result.summary["passed"] is False
    assert validation["summary"]["failure_category_counts"]["missing_citation"] >= 1


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
