from __future__ import annotations

from pathlib import Path
import json


def _write_component_adjudication_eval(
    review_dir: Path,
    *,
    source_set_id: str,
    review_id: str,
    passed: bool,
    pending_count: int = 0,
    queue_item_count: int = 2,
    real_ea_omission_count: int | None = None,
    system_miss_count: int = 0,
) -> None:
    review_dir.mkdir(parents=True, exist_ok=True)
    resolved_count = queue_item_count - pending_count
    real_ea_omission_count = (
        resolved_count if real_ea_omission_count is None else real_ea_omission_count
    )
    failure_counts = {"adjudication_pending": pending_count} if pending_count else {}
    outcome_counts = {}
    if real_ea_omission_count:
        outcome_counts["real_ea_omission"] = real_ea_omission_count
    if system_miss_count:
        outcome_counts["system_miss"] = system_miss_count
    (review_dir / "forest_plan_component_adjudication_eval.json").write_text(
        json.dumps(
            {
                "schema_version": "forest-plan-component-adjudication-eval-v0",
                "review_id": review_id,
                "source_set_id": source_set_id,
                "summary": {
                    "review_id": review_id,
                    "source_set_id": source_set_id,
                    "adjudication_file": str(
                        review_dir / "forest_plan_component_adjudication.json"
                    ),
                    "queue_item_count": queue_item_count,
                    "adjudication_item_count": queue_item_count,
                    "resolved_adjudication_count": resolved_count,
                    "pending_adjudication_count": pending_count,
                    "real_ea_omission_count": real_ea_omission_count,
                    "system_miss_count": system_miss_count,
                    "adjudication_completion_rate": round(resolved_count / queue_item_count, 6),
                    "real_ea_omission_rate": round(
                        real_ea_omission_count / queue_item_count,
                        6,
                    ),
                    "system_miss_rate": round(system_miss_count / queue_item_count, 6),
                    "adjudication_expectation_match_rate": 1.0,
                    "adjudication_outcome_counts": outcome_counts,
                    "disposition_counts": (
                        {"true_ea_omission": real_ea_omission_count}
                        if real_ea_omission_count
                        else {}
                    ),
                    "real_ea_omission_disposition_counts": (
                        {"true_ea_omission": real_ea_omission_count}
                        if real_ea_omission_count
                        else {}
                    ),
                    "system_miss_disposition_counts": (
                        {"retrieval_miss": system_miss_count}
                        if system_miss_count
                        else {}
                    ),
                    "failure_category_counts": failure_counts,
                    "passed": passed,
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _write_component_eval(
    review_dir: Path,
    *,
    source_set_id: str,
    review_id: str,
    passed: bool,
    schema_version: str = "forest-plan-component-eval-results-v0",
) -> None:
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "forest_plan_component_eval_results.json").write_text(
        json.dumps(
            {
                "schema_version": schema_version,
                "summary": {
                    "schema_version": schema_version,
                    "review_id": review_id,
                    "source_set_id": source_set_id,
                    "case_count": 3,
                    "passed_case_count": 3 if passed else 2,
                    "failed_case_count": 0 if passed else 1,
                    "metrics": {
                        "component_applicability_precision": 1.0,
                        "component_applicability_recall": 1.0,
                        "applicable_standard_recall": 1.0,
                    },
                    "failure_category_counts": {} if passed else {"package_section_mismatch": 1},
                    "passed": passed,
                },
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _write_custer_rule_pack(directory: Path) -> Path:
    rule_pack = {
        "schema_version": "compliance-rule-pack-v0",
        "rule_pack_id": "unit-custer-gallatin-ea",
        "version": "0.1.0",
        "title": "Unit Custer Gallatin EA Rule Pack",
        "description": "Unit test Custer Gallatin forest-plan rule pack.",
        "baseline_source_record_ids": ["R1PLAN-custer-gallatin-nf-02"],
        "rules": [
            {
                "id": "custer_gallatin_lmp_2022",
                "title": "Custer Gallatin forest-plan standard is addressed",
                "authority_category": "forest_plan",
                "authority_family_id": "unit_custer_forest_plan",
                "authority_source_record_id": "R1PLAN-custer-gallatin-nf-02",
                "authority_document_role": "forest_plan",
                "applicability_mode": "baseline",
                "question": "Does the EA package address the applicable Custer Gallatin standard?",
                "requirement": (
                    "Custer Gallatin EAs in the Crazy Mountains Backcountry Area must "
                    "address the standard prohibiting new permanent or temporary roads."
                ),
                "package_query": "new permanent or temporary roads",
                "package_terms": ["new permanent or temporary roads"],
                "source_query": "new permanent or temporary roads shall not be allowed",
                "source_filters": {
                    "document_role": "forest_plan",
                    "source_record_id": "R1PLAN-custer-gallatin-nf-02",
                },
                "severity": "high",
            }
        ],
    }
    path = directory / "custer-rule-pack.json"
    path.write_text(json.dumps(rule_pack, sort_keys=True), encoding="utf-8")
    return path


def _write_beaverhead_rule_pack(directory: Path) -> Path:
    rule_pack = {
        "schema_version": "compliance-rule-pack-v0",
        "rule_pack_id": "unit-beaverhead-ea",
        "version": "0.1.0",
        "title": "Unit Beaverhead-Deerlodge EA Rule Pack",
        "description": "Unit test Beaverhead-Deerlodge forest-plan rule pack.",
        "baseline_source_record_ids": ["R1PLAN-beaverhead-deerlodge-nf-02"],
        "rules": [
            {
                "id": "beaverhead_west_big_hole_lmp_2009",
                "title": "Beaverhead-Deerlodge forest-plan standard is addressed",
                "authority_category": "forest_plan",
                "authority_family_id": "unit_beaverhead_forest_plan",
                "authority_source_record_id": "R1PLAN-beaverhead-deerlodge-nf-02",
                "authority_document_role": "forest_plan",
                "applicability_mode": "baseline",
                "question": "Does the EA package address the applicable Beaverhead standard?",
                "requirement": (
                    "Beaverhead-Deerlodge EAs in the West Big Hole Management Area must "
                    "address the standard prohibiting new permanent or temporary roads."
                ),
                "package_query": "new permanent or temporary roads",
                "package_terms": ["new permanent or temporary roads"],
                "source_query": "new permanent or temporary roads shall not be allowed",
                "source_filters": {
                    "document_role": "forest_plan",
                    "source_record_id": "R1PLAN-beaverhead-deerlodge-nf-02",
                },
                "severity": "high",
            }
        ],
    }
    path = directory / "beaverhead-rule-pack.json"
    path.write_text(json.dumps(rule_pack, sort_keys=True), encoding="utf-8")
    return path


def _write_flathead_rule_pack(directory: Path) -> Path:
    rule_pack = {
        "schema_version": "compliance-rule-pack-v0",
        "rule_pack_id": "unit-flathead-ea",
        "version": "0.1.0",
        "title": "Unit Flathead EA Rule Pack",
        "description": "Unit test Flathead forest-plan rule pack.",
        "baseline_source_record_ids": ["FINAL-FLAT-001"],
        "rules": [
            {
                "id": "flathead_fw_std_wtr_2018",
                "title": "Flathead forest-plan stream-screen standard is addressed",
                "authority_category": "forest_plan",
                "authority_family_id": "unit_flathead_forest_plan",
                "authority_source_record_id": "FINAL-FLAT-001",
                "authority_document_role": "forest_plan",
                "applicability_mode": "baseline",
                "question": "Does the EA package address the applicable Flathead standard?",
                "requirement": (
                    "Flathead EAs in the Jewel Basin Hiking Area must address the stream-"
                    "screening standard for new diversions."
                ),
                "package_query": "new stream diversions screens placed on them aquatic organisms",
                "package_terms": ["new stream diversions", "screens placed on them"],
                "source_query": (
                    "new stream diversions and associated ditches shall have screens placed "
                    "on them to prevent capture of fish and other aquatic organisms"
                ),
                "source_filters": {
                    "document_role": "forest_plan",
                    "source_record_id": "FINAL-FLAT-001",
                },
                "severity": "high",
            }
        ],
    }
    path = directory / "flathead-rule-pack.json"
    path.write_text(json.dumps(rule_pack, sort_keys=True), encoding="utf-8")
    return path
