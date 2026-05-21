from __future__ import annotations

import json
from pathlib import Path
import tempfile

from usfs_r1_ea_sources.applicability_validation_artifacts import artifact_hashes
from usfs_r1_ea_sources.applicability_validation_artifacts import (
    build_validation_artifact_paths,
)
from usfs_r1_ea_sources.applicability_validation_artifacts import first_present_run_id
from usfs_r1_ea_sources.applicability_validation_artifacts import first_present_source_set_id
from usfs_r1_ea_sources.applicability_validation_artifacts import load_validation_artifacts
from usfs_r1_ea_sources.applicability_validation_freshness import (
    build_validation_freshness_checks,
)
from usfs_r1_ea_sources.applicability_validation_freshness import check_provenance

from tests.test_applicability_decisions import _build_adjudicated_applicability_dir
from tests.test_applicability_decisions import _write_decision_fixture


def _load_fixture_artifacts(tmp_dir: Path) -> tuple[dict, Path, dict[str, Path], dict]:
    fixture = _write_decision_fixture(tmp_dir)
    applicability_dir = _build_adjudicated_applicability_dir(fixture)
    paths = build_validation_artifact_paths(
        applicability_dir=applicability_dir,
        authority_universe_path=None,
        package_fact_graph_path=None,
        package_applicability_context_path=None,
        package_fact_graph_validation_path=None,
        retrieval_trace_path=None,
        graph_trace_path=None,
        decisions_path=None,
        applicable_authorities_path=None,
        non_applicable_authorities_path=None,
        search_coverage_certificates_path=None,
        provenance_path=None,
    )
    artifacts = load_validation_artifacts(paths)
    return fixture, applicability_dir, paths, artifacts


def test_build_validation_artifact_paths_defaults_to_applicability_dir() -> None:
    applicability_dir = Path("/tmp/unit-applicability")
    custom_provenance = Path("/tmp/custom/applicability_provenance.json")

    paths = build_validation_artifact_paths(
        applicability_dir=applicability_dir,
        authority_universe_path=None,
        package_fact_graph_path=None,
        package_applicability_context_path=None,
        package_fact_graph_validation_path=None,
        retrieval_trace_path=None,
        graph_trace_path=None,
        decisions_path=None,
        applicable_authorities_path=None,
        non_applicable_authorities_path=None,
        search_coverage_certificates_path=None,
        provenance_path=custom_provenance,
    )

    assert paths["authority_universe"] == applicability_dir / "authority_universe_snapshot.json"
    assert paths["package_fact_graph"] == applicability_dir / "package_fact_graph.json"
    assert paths["retrieval_trace"] == applicability_dir / "applicability_retrieval_trace.jsonl"
    assert paths["provenance"] == custom_provenance


def test_load_validation_artifacts_and_hash_helpers_pin_moved_artifact_owner() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        fixture, _applicability_dir, paths, artifacts = _load_fixture_artifacts(Path(tmp))

        assert first_present_source_set_id(artifacts) == fixture["source_set_id"]
        assert first_present_run_id(artifacts)

        hashes = artifact_hashes(paths, artifacts)

        assert hashes["authority_universe_sha256"]
        assert hashes["applicability_decisions_sha256"]
        assert hashes["applicability_provenance_sha256"]
        assert hashes["search_coverage_certificates_sha256"]


def test_build_validation_freshness_checks_pins_moved_freshness_and_provenance_family() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        _fixture, _applicability_dir, paths, artifacts = _load_fixture_artifacts(Path(tmp))

        checks = build_validation_freshness_checks(
            paths=paths,
            artifacts=artifacts,
            decisions=artifacts["decisions"],
        )

        names = {check["name"] for check in checks}
        assert names == {
            "artifact_hashes_match_current_inputs",
            "provenance_covers_required_applicability_artifacts",
        }
        assert all(check["passed"] for check in checks)


def test_check_provenance_reports_stale_decision_ledger_hash() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        _fixture, _applicability_dir, paths, artifacts = _load_fixture_artifacts(Path(tmp))
        provenance = json.loads(json.dumps(artifacts["provenance"]))
        for entity in provenance["entities"]:
            if entity["entity_id"] == "decision_ledger":
                entity["sha256"] = "stale-decision-ledger"

        check = check_provenance(provenance, paths, artifacts)

        assert not check["passed"]
        assert "provenance_gap" in check["failure_categories"]
