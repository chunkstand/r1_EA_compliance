from __future__ import annotations

from pathlib import Path
import json
import tempfile

from usfs_r1_ea_sources.applicability_rule_pack_support import _artifact_paths
from usfs_r1_ea_sources.applicability_rule_pack_validation import _check_applicability_validation_matches_current_artifacts
from usfs_r1_ea_sources.applicability_rule_pack_validation import _check_generated_rules_carry_required_metadata
from tests.test_applicability_decisions import _build_adjudicated_applicability_dir
from tests.test_applicability_decisions import _write_decision_fixture
from tests.test_applicability_decisions import _write_json


def test_generated_rule_pack_validation_detects_metadata_gap() -> None:
    check = _check_generated_rules_carry_required_metadata(
        [
            {
                "id": "rule-1",
                "generated_rule_id": "not-rule-1",
                "candidate_authority_id": "candidate-1",
                "applicability_decision_id": "decision-1",
                "base_rule_pack_id": "unit-pack",
                "base_rule_pack_version": "0.1.0",
                "source_claim_link_requirements": {},
                "package_section_expectations": {},
                "applicability_artifact_hashes": {},
                "applicability": {
                    "candidate_authority_type": "rule_template",
                    "decision_id": "decision-1",
                    "artifact_hashes": {},
                },
            }
        ]
    )

    assert not check["passed"]
    assert check["failure_categories"] == ["generated_rule_metadata_gap"]
    failure = check["failures"][0]["details"]
    assert "base_rule_id" in failure["missing_rule_fields"]
    assert "generated_rule_id_matches_id" in failure["missing_rule_fields"]
    assert "applicability.retrieval_trace_ids" in failure["missing_rule_fields"]
    assert "base_rule_pack_sha256" in failure["missing_hash_fields"]


def test_generated_rule_pack_validation_detects_stale_applicable_authority_hash() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        fixture = _write_decision_fixture(Path(tmp))
        _build_adjudicated_applicability_dir(fixture)
        paths = _artifact_paths(
            output_dir=fixture["output_dir"],
            review_id=fixture["review_id"],
            authority_universe_path=None,
            decisions_path=None,
            applicable_authorities_path=None,
            non_applicable_authorities_path=None,
            applicability_validation_path=None,
            generated_rule_pack_path=None,
            validation_output_path=None,
        )
        applicable = _read_json(paths["applicable_authorities"])
        applicable["authorities"][0]["basis_type"] = "changed-after-validation"
        _write_json(paths["applicable_authorities"], applicable)

        check = _check_applicability_validation_matches_current_artifacts(
            applicability_validation=_read_json(paths["applicability_validation"]),
            authority_universe=_read_json(paths["authority_universe"]),
            paths=paths,
        )

        assert not check["passed"]
        assert check["failure_categories"] == ["generated_rule_pack_stale"]
        assert {
            failure["details"]["field"]
            for failure in check["failures"]
        } == {"applicable_authorities_sha256"}


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
