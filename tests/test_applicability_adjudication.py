from __future__ import annotations

from pathlib import Path
import json
import tempfile

from usfs_r1_ea_sources.applicability_adjudication import evaluate_applicability_adjudication
from usfs_r1_ea_sources.applicability_adjudication import (
    write_applicability_adjudication_template,
)
from usfs_r1_ea_sources.applicability_adjudication_apply import (
    apply_applicability_adjudication,
)
from usfs_r1_ea_sources.applicability_decisions import build_applicability_decisions

from tests.test_applicability_decisions import _write_decision_fixture


def test_template_pins_unresolved_decisions_directly() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        fixture = _write_decision_fixture(Path(tmp))
        build_applicability_decisions(
            output_dir=fixture["output_dir"],
            review_id=fixture["review_id"],
            source_set_id=fixture["source_set_id"],
        )

        result = write_applicability_adjudication_template(
            output_dir=fixture["output_dir"],
            review_id=fixture["review_id"],
            source_set_id=fixture["source_set_id"],
        )

        template = json.loads(result.output_path.read_text(encoding="utf-8"))
        assert template["items"]
        assert result.summary["adjudication_item_count"] == len(template["items"])
        assert result.summary["pending_item_count"] == len(template["items"])
        assert all(
            item["current_status"] in {"unresolved", "needs_adjudication"}
            for item in template["items"]
        )
        assert result.markdown_path.exists()
        assert "Applicability Adjudication Worklist" in result.markdown_path.read_text(
            encoding="utf-8"
        )


def test_eval_reports_pending_items_then_passes_after_completion() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        fixture = _write_decision_fixture(Path(tmp))
        build_applicability_decisions(
            output_dir=fixture["output_dir"],
            review_id=fixture["review_id"],
            source_set_id=fixture["source_set_id"],
        )
        template_result = write_applicability_adjudication_template(
            output_dir=fixture["output_dir"],
            review_id=fixture["review_id"],
            source_set_id=fixture["source_set_id"],
        )

        pending_eval = evaluate_applicability_adjudication(
            output_dir=fixture["output_dir"],
            review_id=fixture["review_id"],
            source_set_id=fixture["source_set_id"],
            adjudication_file=template_result.output_path,
        )
        assert not pending_eval.summary["passed"]
        assert pending_eval.summary["pending_adjudication_count"] == len(
            json.loads(template_result.output_path.read_text(encoding="utf-8"))["items"]
        )

        _complete_adjudication(template_result.output_path)
        passing_eval = evaluate_applicability_adjudication(
            output_dir=fixture["output_dir"],
            review_id=fixture["review_id"],
            source_set_id=fixture["source_set_id"],
            adjudication_file=template_result.output_path,
        )
        assert passing_eval.summary["passed"]
        assert passing_eval.summary["resolved_adjudication_count"] == passing_eval.summary[
            "adjudication_item_count"
        ]


def test_apply_rewrites_decisions_and_provenance() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        fixture = _write_decision_fixture(Path(tmp))
        build_applicability_decisions(
            output_dir=fixture["output_dir"],
            review_id=fixture["review_id"],
            source_set_id=fixture["source_set_id"],
        )
        template_result = write_applicability_adjudication_template(
            output_dir=fixture["output_dir"],
            review_id=fixture["review_id"],
            source_set_id=fixture["source_set_id"],
        )
        _complete_adjudication(template_result.output_path)

        apply_result = apply_applicability_adjudication(
            output_dir=fixture["output_dir"],
            review_id=fixture["review_id"],
            source_set_id=fixture["source_set_id"],
            adjudication_file=template_result.output_path,
        )

        assert apply_result.summary["passed"]
        assert apply_result.summary["remaining_unresolved_authority_count"] == 0
        applicability_dir = (
            fixture["output_dir"] / "reviews" / fixture["review_id"] / "applicability"
        )
        decisions = [
            json.loads(line)
            for line in (applicability_dir / "applicability_decisions.jsonl").read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        ]
        assert any(
            decision.get("basis_type") == "human_adjudication"
            and decision.get("human_adjudication_refs")
            for decision in decisions
        )
        provenance = json.loads(
            (applicability_dir / "applicability_provenance.json").read_text(encoding="utf-8")
        )
        entity_ids = {
            entity.get("entity_id")
            for entity in provenance.get("entities", [])
            if isinstance(entity, dict)
        }
        assert {
            "applicability_adjudication",
            "applicability_adjudication_eval",
            "applicability_adjudication_apply",
        }.issubset(entity_ids)


def _complete_adjudication(path: Path) -> None:
    template = json.loads(path.read_text(encoding="utf-8"))
    for item in template["items"]:
        item["final_status"] = "applicable"
        item["disposition"] = "human_applicable"
        item["adjudicated_at"] = "2026-05-20T00:00:00Z"
        item["adjudicated_by"] = ["unit-reviewer"]
        item["source_type"] = "unit-test"
        item["rationale"] = (
            f"Resolved during the adjudication seam test for {item['candidate_authority_id']}."
        )
        item["supporting_citation_refs"] = sorted(
            set(item.get("supporting_citation_refs") or ["UNIT-CITATION-001"])
        )
    path.write_text(json.dumps(template, indent=2, sort_keys=True) + "\n", encoding="utf-8")
