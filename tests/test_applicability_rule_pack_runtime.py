from __future__ import annotations

from pathlib import Path
import json
import tempfile

from usfs_r1_ea_sources.applicability_rule_pack_runtime import _generated_rule_pack
from usfs_r1_ea_sources.applicability_rule_pack_support import _artifact_paths
from usfs_r1_ea_sources.rule_packs import load_rule_pack
from tests.test_applicability_decisions import _authority_family_candidate
from tests.test_applicability_decisions import _build_adjudicated_applicability_dir
from tests.test_applicability_decisions import _write_decision_fixture
from tests.test_applicability_decisions import _write_generated_rule_base_pack


def test_generated_rule_pack_runtime_uses_only_applicable_authorities() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        payloads = _prepared_payloads(Path(tmp))

        generated = _generated_rule_pack(
            review_id=payloads["fixture"]["review_id"],
            source_set_id=payloads["fixture"]["source_set_id"],
            base_rule_pack_path=payloads["base_rule_pack_path"],
            base_rule_pack=payloads["base_rule_pack"],
            authority_universe=payloads["authority_universe"],
            applicability_validation=payloads["applicability_validation"],
            applicable_authorities=payloads["applicable_authorities"],
            non_applicable_authorities=payloads["non_applicable_authorities"],
            decisions=payloads["decisions"],
            paths=payloads["paths"],
        )

        assert generated["applicable_authority_count"] == 4
        assert generated["non_applicable_authority_count"] == 2
        assert {rule["id"] for rule in generated["rules"]} == {
            "baseline_nepa",
            "cwa_permit",
            "esa_consultation",
            "forest_plan_component_STD-FP-01",
        }
        assert "ce_fanec" not in {rule["id"] for rule in generated["rules"]}
        first_rule = generated["rules"][0]
        assert first_rule["applicability"]["artifact_hashes"] == first_rule[
            "applicability_artifact_hashes"
        ]
        assert generated["artifact_hashes"]["base_rule_pack_sha256"]
        assert generated["artifact_hashes"]["retrieval_trace_sha256"]


def test_generated_rule_pack_runtime_materializes_authority_family_template_rules() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        payloads = _prepared_payloads(
            Path(tmp),
            extra_candidates=[_authority_family_candidate("source-set-unit")],
        )

        generated = _generated_rule_pack(
            review_id=payloads["fixture"]["review_id"],
            source_set_id=payloads["fixture"]["source_set_id"],
            base_rule_pack_path=payloads["base_rule_pack_path"],
            base_rule_pack=payloads["base_rule_pack"],
            authority_universe=payloads["authority_universe"],
            applicability_validation=payloads["applicability_validation"],
            applicable_authorities=payloads["applicable_authorities"],
            non_applicable_authorities=payloads["non_applicable_authorities"],
            decisions=payloads["decisions"],
            paths=payloads["paths"],
        )

        family_rule = {
            rule["id"]: rule for rule in generated["rules"]
        }["clean_water_family_authority_template"]
        assert family_rule["base_rule_id"] is None
        assert family_rule["authority_source_record_id"] == "R1EA-CWA"
        assert family_rule["package_terms"] == ["wetlands"]
        assert family_rule["package_section_terms"] == ["water resources"]
        assert family_rule["source_filters"]["source_record_id"] == "R1EA-CWA"
        assert family_rule["applicability"]["authority_family_id"] == "clean_water"


def _prepared_payloads(
    root: Path,
    *,
    extra_candidates: list[dict] | None = None,
) -> dict[str, object]:
    fixture = _write_decision_fixture(root, extra_candidates=extra_candidates)
    _build_adjudicated_applicability_dir(fixture)
    base_rule_pack_path = _write_generated_rule_base_pack(root)
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
    return {
        "fixture": fixture,
        "paths": paths,
        "base_rule_pack_path": base_rule_pack_path,
        "base_rule_pack": load_rule_pack(base_rule_pack_path),
        "authority_universe": _read_json(paths["authority_universe"]),
        "applicability_validation": _read_json(paths["applicability_validation"]),
        "applicable_authorities": _read_json(paths["applicable_authorities"]),
        "non_applicable_authorities": _read_json(paths["non_applicable_authorities"]),
        "decisions": _read_jsonl(paths["decisions"]),
    }


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
