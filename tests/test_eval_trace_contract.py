from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json

import pytest

from usfs_r1_ea_sources.eval_trace_contract import DEFAULT_EVAL_TRACE_CONTRACT_PATH
from usfs_r1_ea_sources.eval_trace_contract import REQUIRED_ARTIFACT_FAMILIES
from usfs_r1_ea_sources.eval_trace_contract import REQUIRED_CANONICAL_OBJECTS
from usfs_r1_ea_sources.eval_trace_contract import REQUIRED_ENUM_VALUES
from usfs_r1_ea_sources.eval_trace_contract import REQUIRED_LINK_CHECK_IDS
from usfs_r1_ea_sources.eval_trace_contract import load_eval_trace_contract
from usfs_r1_ea_sources.eval_trace_contract import validate_eval_trace_contract


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_committed_eval_trace_contract_names_required_objects_and_enums() -> None:
    contract = load_eval_trace_contract()
    enum_values = contract["enum_values"]

    assert Path(DEFAULT_EVAL_TRACE_CONTRACT_PATH).is_file()
    assert contract["schema_version"] == "first-class-eval-trace-inventory-contract-v1"
    assert contract["contract_id"] == "first-class-eval-trace-inventory-contract"
    assert REQUIRED_CANONICAL_OBJECTS <= {entry["name"] for entry in contract["canonical_objects"]}
    for family, required_values in REQUIRED_ENUM_VALUES.items():
        assert set(enum_values[family]) == required_values


def test_committed_eval_trace_contract_tracks_required_artifacts_and_links() -> None:
    contract = load_eval_trace_contract()
    artifact_family_ids = {
        family["family_id"] for family in contract["required_artifact_families"]
    }
    link_check_ids = {check["check_id"] for check in contract["required_link_checks"]}

    assert REQUIRED_ARTIFACT_FAMILIES <= artifact_family_ids
    assert REQUIRED_LINK_CHECK_IDS <= link_check_ids
    for family in contract["required_artifact_families"]:
        assert family["artifact_paths"]
        assert family["source_ref_requirements"]
    for link_check in contract["required_link_checks"]:
        assert link_check["required"] is True
        assert link_check["failure_reason"]


def test_eval_trace_contract_rejects_unsupported_enum_values() -> None:
    contract = _committed_contract()
    contract["enum_values"]["eval_kind"].append("shadow_eval")

    checks = _checks_by_name(validate_eval_trace_contract(contract))

    assert not checks["eval_trace_contract_eval_kind_values_supported"]["passed"]
    assert checks["eval_trace_contract_eval_kind_values_supported"]["actual"][
        "unsupported"
    ] == ["shadow_eval"]


def test_eval_trace_contract_rejects_missing_required_link_checks() -> None:
    contract = _committed_contract()
    contract["required_link_checks"] = [
        check
        for check in contract["required_link_checks"]
        if check["check_id"] != "origin_artifact_ref_present"
    ]

    checks = _checks_by_name(validate_eval_trace_contract(contract))

    assert not checks["eval_trace_contract_required_link_checks_present"]["passed"]
    assert checks["eval_trace_contract_required_link_checks_present"]["actual"] == [
        "origin_artifact_ref_present"
    ]


def test_eval_trace_contract_rejects_premature_global_ratcheting() -> None:
    contract = _committed_contract()
    contract["ratchet_scopes"]["global_fail_closed"] = True
    contract["ratchet_scopes"]["enabled_review_ids"] = ["*"]

    checks = _checks_by_name(validate_eval_trace_contract(contract))

    assert not checks["eval_trace_contract_ratchet_scope_is_explicit"]["passed"]
    assert checks["eval_trace_contract_ratchet_scope_is_explicit"]["actual"] == [
        {"field": "global_fail_closed", "actual": True},
        {"field": "enabled_review_ids", "actual": ["*"]},
    ]


def test_eval_trace_contract_rejects_missing_llm_judge_metadata_contract() -> None:
    contract = _committed_contract()
    contract["scorer_contract"]["llm_judge_metadata_required_fields"].remove("rubric_hash")

    checks = _checks_by_name(validate_eval_trace_contract(contract))

    assert not checks["eval_trace_contract_llm_judge_metadata_required"]["passed"]
    assert checks["eval_trace_contract_llm_judge_metadata_required"]["actual"] == [
        "rubric_hash"
    ]


def test_load_eval_trace_contract_raises_on_invalid_contract_file(tmp_path: Path) -> None:
    contract = _committed_contract()
    contract["enum_values"]["span_kind"].append("opaque_span")
    contract_path = tmp_path / "eval_trace_inventory_contract_v1.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")

    with pytest.raises(ValueError, match="eval_trace_contract_span_kind_values_supported"):
        load_eval_trace_contract(contract_path)


def _committed_contract() -> dict:
    return deepcopy(
        json.loads((REPO_ROOT / DEFAULT_EVAL_TRACE_CONTRACT_PATH).read_text(encoding="utf-8"))
    )


def _checks_by_name(checks: list[dict]) -> dict[str, dict]:
    return {check["name"]: check for check in checks}
