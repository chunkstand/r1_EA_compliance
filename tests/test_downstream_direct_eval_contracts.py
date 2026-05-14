from __future__ import annotations

import csv
from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "config"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_downstream_direct_eval_manifest_tracks_shipped_contracts() -> None:
    manifest = _read_json(CONFIG_DIR / "downstream_direct_eval_v1.json")

    assert manifest["schema_version"] == "downstream-direct-eval-v1"
    lane_ids = {lane["lane_id"] for lane in manifest["required_lanes"]}
    assert lane_ids == {
        "retrieval_eval",
        "claim_eval",
        "rule_claim_eval",
        "compliance_review_eval",
    }
    for lane in manifest["required_lanes"]:
        contract_path = CONFIG_DIR / lane["contract_path"]
        assert contract_path.exists()
        assert lane["eval_id"]
        assert lane["register_rows"]


def test_retrieval_claim_and_rule_contracts_have_required_case_mix() -> None:
    contracts = [
        (
            "retrieval_eval_seed.json",
            "retrieval-eval-v1",
            "hard_negative_case_count",
            "multi_source_case_count",
            "multi_source",
        ),
        (
            "claim_eval_seed.json",
            "claim-eval-v1",
            "hard_negative_case_count",
            "multi_source_or_type_confusion_case_count",
            "multi_source_or_type_confusion",
        ),
        (
            "rule_claim_link_eval_seed.json",
            "rule-claim-link-eval-v1",
            "hard_negative_case_count",
            "multi_source_case_count",
            "multi_source",
        ),
    ]

    required_metric_keys = {
        "case_count",
        "hard_negative_pass_rate",
        "false_positive_rate",
        "missing_required_source_rate",
        "recall_at_k",
        "mrr",
        "ndcg_at_k",
    }

    for filename, schema_version, hard_negative_key, complex_key, complex_flag in contracts:
        contract = _read_json(CONFIG_DIR / filename)
        cases = contract["cases"]
        requirements = contract["coverage_requirements"]
        thresholds = contract["metric_thresholds"]

        assert contract["schema_version"] == schema_version
        assert contract["eval_id"]
        assert len(cases) >= requirements["case_count"]
        assert sum(1 for case in cases if case.get("hard_negative") or case.get("expect_no_hits")) >= requirements[hard_negative_key]
        assert sum(1 for case in cases if case.get(complex_flag)) >= requirements[complex_key]
        assert required_metric_keys <= set(thresholds)


def test_retrieval_contract_avoids_source_delta_only_forest_plan_rows() -> None:
    contract = _read_json(CONFIG_DIR / "retrieval_eval_seed.json")
    delta_register = CONFIG_DIR / "r1_forest_plan_document_register_draft.csv"
    with delta_register.open(encoding="utf-8", newline="") as handle:
        delta_only_source_ids = {
            row["proposed_source_record_id"]
            for row in csv.DictReader(handle)
            if row["draft_status"] == "source_delta_required"
        }

    expected_source_ids = {
        str(source_record_id)
        for case in contract["cases"]
        for source_record_id in case.get("expected_source_record_ids", [])
        if str(source_record_id)
    }

    assert expected_source_ids.isdisjoint(delta_only_source_ids)


def test_compliance_review_contract_has_required_case_mix_and_fixture_paths() -> None:
    contract = _read_json(CONFIG_DIR / "compliance_review_eval_seed.json")
    cases = contract["cases"]
    requirements = contract["coverage_requirements"]
    thresholds = contract["metric_thresholds"]

    assert contract["schema_version"] == "compliance-review-eval-v1"
    assert contract["eval_id"] == "compliance-review-direct-eval-v1"
    assert len(cases) >= requirements["case_count"]
    assert sum(1 for case in cases if case.get("hard_negative_package")) >= requirements["hard_negative_package_case_count"]
    assert sum(1 for case in cases if case.get("conditional_subset")) >= requirements["conditional_subset_case_count"]
    assert sum(1 for case in cases if case.get("all_authorities_control")) >= requirements["all_authorities_control_case_count"]
    assert {
        "case_count",
        "unexpected_positive_finding_rate",
        "missing_required_source_rule_rate",
        "status_match_rate",
        "source_record_match_rate",
        "source_document_role_match_rate",
        "citation_coverage_rate",
        "graph_coverage_rate",
    } <= set(thresholds)

    for case in cases:
        if "package_path" not in case:
            continue
        fixture_path = (CONFIG_DIR / case["package_path"]).resolve()
        assert fixture_path.exists()
