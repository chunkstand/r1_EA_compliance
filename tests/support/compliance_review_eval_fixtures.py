from __future__ import annotations

from pathlib import Path
import hashlib
import json
import unittest

from usfs_r1_ea_sources.rule_claim_binding import default_rule_claim_links_dir

_UNIT_RULE_PACK_ID = "unit-nepa-ea"
_UNIT_RULE_PACK_VERSION = "0.1.0"


def _write_downstream_direct_eval_phase_outputs(output_dir: Path, source_set_id: str) -> None:
    contracts = {
        output_dir / "derived" / source_set_id / "retrieval" / "retrieval_eval_results.json": (
            Path("config/retrieval_eval_seed.json"),
            "retrieval-direct-eval-v1",
        ),
        output_dir / "derived" / source_set_id / "claims" / "claim_eval_results.json": (
            Path("config/claim_eval_seed.json"),
            "claim-direct-eval-v1",
        ),
        output_dir / "reviews" / "compliance_review_eval" / "compliance_review_eval_results.json": (
            Path("config/compliance_review_eval_seed.json"),
            "compliance-review-direct-eval-v1",
        ),
    }
    rule_claim_root = output_dir / "derived" / source_set_id / "rule_claim_links"
    candidates = sorted(rule_claim_root.glob("*/*/summary.json"))
    rule_claim_result_paths = {
        candidate.parent / "rule_claim_link_eval_results.json" for candidate in candidates
    }
    fallback_rule_claim_dirs = {
        default_rule_claim_links_dir(
            output_dir,
            source_set_id=source_set_id,
        ),
        _unit_rule_claim_links_dir(output_dir, source_set_id),
    }
    rule_claim_result_paths.update(
        rule_claim_dir / "rule_claim_link_eval_results.json"
        for rule_claim_dir in fallback_rule_claim_dirs
    )
    for rule_claim_result_path in sorted(rule_claim_result_paths):
        contracts[rule_claim_result_path] = (
            Path("config/rule_claim_link_eval_seed.json"),
            "rule-claim-direct-eval-v1",
        )
    for result_path, (contract_path, eval_id) in contracts.items():
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(
            json.dumps(
                _direct_eval_result_payload(
                    contract_path=contract_path,
                    eval_id=eval_id,
                    source_set_id=source_set_id,
                ),
                sort_keys=True,
            ),
            encoding="utf-8",
        )


def _direct_eval_result_payload(
    *,
    contract_path: Path,
    eval_id: str,
    source_set_id: str,
) -> dict:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    coverage_requirements = contract.get("coverage_requirements", {})
    case_count = int(
        coverage_requirements.get("case_count")
        or ((contract.get("metric_thresholds") or {}).get("case_count") or {}).get("min")
        or 1
    )
    metrics = {}
    for metric_name, threshold in (contract.get("metric_thresholds") or {}).items():
        if not isinstance(threshold, dict):
            continue
        if "min" in threshold:
            metrics[metric_name] = threshold["min"]
        elif "max" in threshold:
            metrics[metric_name] = threshold["max"]
    payload = {
        "schema_version": "unit-direct-eval-result",
        "eval_id": eval_id,
        "source_set_id": source_set_id,
        "passed": True,
        "checks": [
            {
                "name": "eval_cases_pass",
                "passed": True,
                "details": {"case_count": case_count, "failed_case_ids": []},
            },
            {
                "name": "metric_thresholds_met",
                "passed": True,
                "details": {"failures": []},
            },
        ],
        "contract": {"sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest()},
        "metrics": metrics,
    }
    for key, value in coverage_requirements.items():
        payload[key] = value
    payload.setdefault("case_count", case_count)
    payload.setdefault(
        "hard_negative_case_count",
        coverage_requirements.get("hard_negative_case_count", 0),
    )
    if eval_id == "retrieval-direct-eval-v1":
        payload["query_count"] = case_count
    return payload


def _unit_rule_claim_links_dir(output_dir: Path, source_set_id: str) -> Path:
    return (
        output_dir
        / "derived"
        / source_set_id
        / "rule_claim_links"
        / _UNIT_RULE_PACK_ID
        / _UNIT_RULE_PACK_VERSION
    )


def _write_compliance_eval_file(
    directory: Path,
    cases: list[dict],
    *,
    path: Path | None = None,
) -> Path:
    eval_path = path or directory / "compliance-eval.json"
    eval_path.write_text(json.dumps(cases, sort_keys=True), encoding="utf-8")
    return eval_path


def _write_coverage_matrix(directory: Path, rule_ids: list[str] | None = None) -> Path:
    items = [
        {
            "rule_id": "purpose_need",
            "obligation_area": "Purpose and need",
            "expected_package_evidence": "Purpose and need or proposed action text.",
            "source_record_ids": ["R1EA-001"],
            "source_claim_terms": ["purpose", "need"],
            "eval_case_ids": ["coverage-case"],
        },
        {
            "rule_id": "mitigation",
            "obligation_area": "Mitigation",
            "expected_package_evidence": "Mitigation or FONSI support text.",
            "source_record_ids": ["R1EA-002"],
            "source_claim_terms": ["mitigation"],
            "eval_case_ids": ["coverage-case"],
        },
    ]
    if rule_ids is not None:
        wanted = set(rule_ids)
        items = [item for item in items if item["rule_id"] in wanted]
    path = directory / "coverage-matrix.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "compliance-rule-pack-coverage-v0",
                "rule_pack_id": "unit-nepa-ea",
                "rule_pack_version": "0.1.0",
                "title": "Unit coverage matrix",
                "coverage_items": items,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def _write_gold_eval_file(directory: Path, profiles: list[str] | None = None) -> Path:
    profiles = profiles or ["positive", "mixed", "negative"]
    cases = [
        {
            "id": "gold-positive",
            "profile": profiles[0],
            "package_text": (
                "Purpose and Need. The proposed action improves trail access. "
                "Alternatives include no action. Mitigation measures support a FONSI."
            ),
            "expected_statuses": {
                "purpose_need": "pass",
                "mitigation": "pass",
            },
            "expected_finding_status_counts": {"pass": 2},
            "min_findings": 2,
        },
        {
            "id": "gold-mixed",
            "profile": profiles[1],
            "package_text": "Purpose and Need. The proposed action improves trail access.",
            "expected_statuses": {
                "purpose_need": "pass",
                "mitigation": "gap",
            },
            "expected_finding_status_counts": {"gap": 1, "pass": 1},
            "min_findings": 2,
        },
        {
            "id": "gold-negative",
            "profile": profiles[2],
            "package_text": "Routing slip. Staff contacts and a meeting date.",
            "expected_statuses": {
                "purpose_need": "gap",
                "mitigation": "gap",
            },
            "expected_finding_status_counts": {"gap": 2},
            "min_findings": 2,
        },
    ]
    for case in cases:
        case["adjudication"] = {
            "status": "adjudicated_seed",
            "source_type": "realistic_synthetic",
            "adjudicated_by": ["unit-test"],
            "adjudicated_at": "2026-04-30",
            "rationale": f"Unit adjudication for {case['id']}.",
        }
        case["expected_unsupported_finding_ids"] = []
        case["expected_source_record_ids"] = {
            "purpose_need": ["R1EA-001"],
            "mitigation": ["R1EA-002"],
        }
        case["expected_source_document_roles"] = {
            "purpose_need": ["regulation"],
            "mitigation": ["regulation"],
        }
    path = directory / "gold-eval.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "compliance-gold-eval-v0",
                "id": "unit-gold-v0.1",
                "version": "0.1.0",
                "title": "Unit Gold Eval",
                "rule_pack_id": "unit-nepa-ea",
                "rule_pack_version": "0.1.0",
                "adjudication": {
                    "status": "seed_gold",
                    "method": "Unit test adjudication.",
                    "adjudicated_by": ["unit-test"],
                    "adjudicated_at": "2026-04-30",
                    "promotion_gate": True,
                },
                "cases": cases,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def _phase(summary: dict, name: str) -> dict:
    return next(phase for phase in summary["phases"] if phase["name"] == name)


def _rule_by_id(rule_pack: dict, rule_id: str) -> dict:
    return next(rule for rule in rule_pack["rules"] if rule["id"] == rule_id)


def _coverage_item_by_rule_id(coverage: dict, rule_id: str) -> dict:
    return next(item for item in coverage["coverage_items"] if item["rule_id"] == rule_id)


def _assert_v1_land_exchange_contract(testcase: unittest.TestCase) -> None:
    rule_pack = json.loads(
        Path("config/compliance_rule_pack_nepa_ea_v0.json").read_text(encoding="utf-8")
    )
    coverage = json.loads(
        Path("config/compliance_rule_pack_coverage_nepa_ea_v0.json").read_text(
            encoding="utf-8"
        )
    )
    eval_contract = json.loads(
        Path("config/compliance_review_eval_seed.json").read_text(encoding="utf-8")
    )
    eval_cases = {case["id"]: case for case in eval_contract["cases"]}
    v1_contract = json.loads(Path("config/v1_ecid_real_ea_eval.json").read_text(encoding="utf-8"))

    rule = _rule_by_id(rule_pack, "flpma_section_206_land_exchange")
    testcase.assertEqual(rule["authority_source_record_id"], "R1EA-146")
    testcase.assertEqual(rule["applicability_mode"], "conditional")
    testcase.assertEqual(
        rule["source_filters"],
        {"document_role": "law", "source_record_id": "R1EA-146"},
    )
    testcase.assertIn("FLPMA", rule["applies_if_package_terms"])
    testcase.assertIn("cash equalization", rule["package_terms"])

    coverage_item = _coverage_item_by_rule_id(
        coverage,
        "flpma_section_206_land_exchange",
    )
    testcase.assertEqual(coverage_item["source_record_ids"], ["R1EA-146"])
    testcase.assertEqual(
        set(coverage_item["eval_case_ids"]),
        {
            "all-authorities-pass",
            "baseline-nepa-only",
            "unrelated-package-produces-baseline-gaps",
        },
    )

    testcase.assertEqual(
        eval_cases["all-authorities-pass"]["expected_statuses"][
            "flpma_section_206_land_exchange"
        ],
        "pass",
    )
    testcase.assertEqual(
        eval_cases["all-authorities-pass"]["expected_source_record_ids"][
            "flpma_section_206_land_exchange"
        ],
        ["R1EA-146"],
    )
    testcase.assertEqual(
        eval_cases["baseline-nepa-only"]["expected_statuses"][
            "flpma_section_206_land_exchange"
        ],
        "not_applicable",
    )
    testcase.assertEqual(
        eval_cases["unrelated-package-produces-baseline-gaps"]["expected_statuses"][
            "flpma_section_206_land_exchange"
        ],
        "not_applicable",
    )

    conditional_expectations = {
        expectation["rule_id"]: expectation
        for expectation in v1_contract["conditional_source_expectations"]
    }
    land_exchange_contracts = {
        "flpma_section_206_land_exchange": {
            "source_record_ids": ["R1EA-146"],
            "document_roles": ["law"],
            "family_id": "land_exchange_statutory_authorities",
            "mode": "conditional",
        },
        "land_exchange_statutory_authorities": {
            "source_record_ids": ["R1EA-137"],
            "document_roles": ["law"],
            "family_id": "land_exchange_statutory_authorities",
            "mode": "conditional",
        },
        "land_exchange_regulatory_requirements": {
            "source_record_ids": ["R1EA-124"],
            "document_roles": ["regulation"],
            "family_id": "land_exchange_regulatory_requirements",
            "mode": "conditional",
        },
        "land_exchange_fs_policy_and_project_references": {
            "source_record_ids": ["R1EA-150"],
            "document_roles": ["agency_policy"],
            "family_id": "land_exchange_fs_policy_and_project_references",
            "mode": "conditional",
        },
    }
    generic_exchange_terms = {
        "acquisition",
        "appraisal",
        "cash equalization",
        "closing",
        "disposal",
        "easement",
        "equal value",
        "feasibility analysis",
        "mineral reservation",
        "outstanding rights",
        "public interest determination",
        "reservation",
        "reservations",
        "segregation",
        "title evidence",
    }
    for rule_id, expected in land_exchange_contracts.items():
        rule = _rule_by_id(rule_pack, rule_id)
        testcase.assertEqual(rule["authority_source_record_id"], expected["source_record_ids"][0])
        testcase.assertEqual(rule["applicability_mode"], expected["mode"])
        testcase.assertEqual(rule["authority_family_id"], expected["family_id"])
        testcase.assertIn("land exchange", [term.lower() for term in rule["package_terms"]])
        singleton_trigger_groups = {
            tuple(term.lower() for term in group)
            for group in rule.get("applies_if_package_term_groups", [])
            if len(group) == 1
        }
        testcase.assertFalse(
            {(term,) for term in generic_exchange_terms} & singleton_trigger_groups
        )

        coverage_item = _coverage_item_by_rule_id(coverage, rule_id)
        testcase.assertEqual(coverage_item["source_record_ids"], expected["source_record_ids"])
        testcase.assertEqual(
            set(coverage_item["eval_case_ids"]),
            {
                "all-authorities-pass",
                "baseline-nepa-only",
                "unrelated-package-produces-baseline-gaps",
            },
        )

        testcase.assertEqual(eval_cases["all-authorities-pass"]["expected_statuses"][rule_id], "pass")
        testcase.assertEqual(
            eval_cases["baseline-nepa-only"]["expected_statuses"][rule_id],
            "not_applicable",
        )
        testcase.assertEqual(
            eval_cases["unrelated-package-produces-baseline-gaps"]["expected_statuses"][rule_id],
            "not_applicable",
        )

        v1_expectation = conditional_expectations[rule_id]
        testcase.assertEqual(v1_expectation["expected_applicability"], "applicable")
        testcase.assertEqual(
            v1_expectation["expected_source_record_ids"],
            expected["source_record_ids"],
        )
        testcase.assertEqual(
            v1_expectation["expected_source_document_roles"],
            expected["document_roles"],
        )
