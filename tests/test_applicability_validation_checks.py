from __future__ import annotations

from pathlib import Path
import json
import tempfile

from usfs_r1_ea_sources.applicability_decisions import build_applicability_decisions
from usfs_r1_ea_sources.applicability_validation_checks import build_validation_checks
from usfs_r1_ea_sources.applicability_validation_checks import check_candidate_decisions
from usfs_r1_ea_sources.applicability_validation_checks import check_human_adjudication_replay
from usfs_r1_ea_sources.applicability_validation_support import read_json_if_exists
from usfs_r1_ea_sources.applicability_validation_support import read_jsonl_if_exists

from tests.test_applicability_decisions import _build_adjudicated_applicability_dir
from tests.test_applicability_decisions import _write_decision_fixture


def test_check_candidate_decisions_reports_missing_duplicate_and_unexpected() -> None:
    check = check_candidate_decisions(
        candidates=[
            {"candidate_authority_id": "cand-a"},
            {"candidate_authority_id": "cand-b"},
        ],
        decisions=[
            {"candidate_authority_id": "cand-a"},
            {"candidate_authority_id": "cand-a"},
            {"candidate_authority_id": "cand-extra"},
        ],
    )

    assert not check["passed"]
    assert sorted(check["failure_categories"]) == [
        "duplicate_decision",
        "missing_candidate_decision",
        "partition_gap",
    ]


def test_build_validation_checks_pins_moved_check_family() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        fixture = _write_decision_fixture(Path(tmp))
        build_applicability_decisions(
            output_dir=fixture["output_dir"],
            review_id=fixture["review_id"],
            source_set_id=fixture["source_set_id"],
        )
        applicability_dir = (
            fixture["output_dir"] / "reviews" / fixture["review_id"] / "applicability"
        )
        paths = {
            "authority_universe": applicability_dir / "authority_universe_snapshot.json",
            "package_fact_graph": applicability_dir / "package_fact_graph.json",
            "package_applicability_context": applicability_dir / "package_applicability_context.json",
            "package_fact_graph_validation": applicability_dir / "package_fact_graph_validation.json",
            "retrieval_trace": applicability_dir / "applicability_retrieval_trace.jsonl",
            "graph_trace": applicability_dir / "applicability_graph_trace.jsonl",
            "decisions": applicability_dir / "applicability_decisions.jsonl",
            "applicable_authorities": applicability_dir / "applicable_authorities.json",
            "non_applicable_authorities": applicability_dir / "non_applicable_authorities.json",
            "search_coverage_certificates": applicability_dir / "search_coverage_certificates.json",
            "provenance": applicability_dir / "applicability_provenance.json",
        }
        artifacts = {
            "authority_universe": read_json_if_exists(paths["authority_universe"]),
            "package_fact_graph": read_json_if_exists(paths["package_fact_graph"]),
            "package_applicability_context": read_json_if_exists(
                paths["package_applicability_context"]
            ),
            "package_fact_graph_validation": read_json_if_exists(
                paths["package_fact_graph_validation"]
            ),
            "retrieval_rows": read_jsonl_if_exists(paths["retrieval_trace"]),
            "graph_rows": read_jsonl_if_exists(paths["graph_trace"]),
            "decisions": read_jsonl_if_exists(paths["decisions"]),
            "applicable_authorities": read_json_if_exists(paths["applicable_authorities"]),
            "non_applicable_authorities": read_json_if_exists(paths["non_applicable_authorities"]),
            "search_coverage_certificates": read_json_if_exists(
                paths["search_coverage_certificates"]
            ),
            "provenance": read_json_if_exists(paths["provenance"]),
        }

        checks = build_validation_checks(
            review_id=fixture["review_id"],
            source_set_id=fixture["source_set_id"],
            paths=paths,
            artifacts=artifacts,
        )

        names = {check["name"] for check in checks}
        assert "candidate_universe_has_exactly_one_decision" in names
        assert "human_adjudication_references_are_replayable" in names
        assert "retrieval_backed_decisions_have_trace_rows" in names


def test_check_human_adjudication_replay_accepts_applied_fixture() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        fixture = _write_decision_fixture(Path(tmp))
        applicability_dir = _build_adjudicated_applicability_dir(fixture)
        decisions = [
            json.loads(line)
            for line in (applicability_dir / "applicability_decisions.jsonl").read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        ]

        check = check_human_adjudication_replay(decisions)

        assert check["passed"]
