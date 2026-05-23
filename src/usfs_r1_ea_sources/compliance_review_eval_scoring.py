from __future__ import annotations

from collections import Counter
from copy import deepcopy
from pathlib import Path
import json

from .compliance_findings import claim_type
from .compliance_outputs import finding_source_document_roles
from .compliance_outputs import finding_source_record_ids
from .compliance_review import ComplianceReviewResult
from .compliance_review_eval_generated import _case_has_generated_rule_pack_expectations
from .compliance_review_eval_generated import _case_requires_generated_rule_pack
from .compliance_validation import CLAIM_STATUSES
from .compliance_validation import GRAPH_COVERAGE_CHECKS
from .compliance_validation import failed_check_names
from .compliance_validation import validation_checks_passed
from .rule_packs import aliased_source_record_ids


def eval_package_path(case: dict, *, eval_file: Path, package_dir: Path) -> Path:
    if str(case.get("package_text") or "").strip():
        package_path = package_dir / f"{case['id']}.txt"
        package_path.write_text(str(case["package_text"]).rstrip() + "\n", encoding="utf-8")
        return package_path
    package_path = Path(str(case["package_path"]))
    if not package_path.is_absolute():
        package_path = eval_file.parent / package_path
    if not package_path.exists():
        raise FileNotFoundError(f"Missing compliance review eval package fixture: {package_path}")
    return package_path


def compliance_review_eval_case_result(
    *,
    case: dict,
    package_path: Path,
    result: ComplianceReviewResult,
    report: dict,
    validation: dict,
    source_top_k: int,
    package_top_k: int,
) -> dict:
    findings = list(report.get("findings", []))
    findings_by_rule = {str(finding.get("rule_id")): finding for finding in findings}
    effective_case = effective_eval_case_expectations(
        case=case,
        review_dir=result.review_dir,
        findings_by_rule=findings_by_rule,
    )
    filters = dict(case.get("filters") or {})
    selected_findings = filter_eval_findings(findings, filters)
    expected_statuses = string_map(effective_case["expected_statuses"])
    expected_claim_types = expected_claim_type_map(effective_case, expected_statuses)
    expected_package_evidence = expected_bool_presence_map(
        effective_case,
        "expected_package_evidence",
        expected_statuses,
        lambda status: status == "pass",
    )
    expected_source_evidence = expected_bool_presence_map(
        effective_case,
        "expected_source_evidence",
        expected_statuses,
        lambda status: status in CLAIM_STATUSES,
    )
    expected_source_claim_links = expected_bool_presence_map(
        effective_case,
        "expected_source_claim_links",
        expected_statuses,
        lambda status: status in CLAIM_STATUSES,
    )
    normalized_findings_by_rule = normalized_eval_findings_by_rule(
        findings_by_rule=findings_by_rule,
        expected_statuses=expected_statuses,
        generated_rule_pack_case=_case_requires_generated_rule_pack(effective_case),
    )
    status_mismatches = value_mismatches(
        normalized_findings_by_rule,
        expected_statuses,
        "status",
    )
    claim_type_mismatches = value_mismatches(
        normalized_findings_by_rule,
        expected_claim_types,
        "claim_type",
    )
    package_evidence_mismatches = presence_mismatches(
        normalized_findings_by_rule,
        expected_package_evidence,
        finding_has_package_evidence,
    )
    source_evidence_mismatches = presence_mismatches(
        normalized_findings_by_rule,
        expected_source_evidence,
        finding_has_source_evidence,
    )
    source_claim_link_mismatches = presence_mismatches(
        normalized_findings_by_rule,
        expected_source_claim_links,
        finding_has_source_claim_links,
    )
    expected_source_record_ids = source_backed_expected_string_list_map(
        effective_case,
        "expected_source_record_ids",
        expected_statuses,
    )
    expected_source_document_roles = source_backed_expected_string_list_map(
        effective_case,
        "expected_source_document_roles",
        expected_statuses,
    )
    source_record_mismatches = expected_subset_mismatches(
        normalized_findings_by_rule,
        expected_source_record_ids,
        finding_source_record_ids_with_aliases,
    )
    source_document_role_mismatches = expected_subset_mismatches(
        normalized_findings_by_rule,
        expected_source_document_roles,
        finding_source_document_roles_for_eval,
    )
    expected_status_counts = {
        str(status): int(count)
        for status, count in (effective_case.get("expected_finding_status_counts") or {}).items()
    }
    actual_status_counts = dict(Counter(str(finding.get("status")) for finding in findings))
    status_counts_match = (
        not expected_status_counts or actual_status_counts == expected_status_counts
    )
    expected_unsupported = sorted(
        str(value) for value in effective_case.get("expected_unsupported_finding_ids", [])
    )
    actual_unsupported = sorted(
        str(value)
        for value in report.get("summary", {}).get("unsupported_finding_ids", [])
    )
    unsupported_finding_ids_match = actual_unsupported == expected_unsupported
    summary = report.get("summary", {})
    applicability_gate = summary.get("applicability_gate")
    diagnostic_rule_pack = applicability_gate_is_diagnostic(applicability_gate)
    if "expected_validation_passed" in effective_case:
        expected_validation_passed = bool(effective_case.get("expected_validation_passed"))
    else:
        expected_validation_passed = not diagnostic_rule_pack
    validation_passed_matches = bool(validation.get("passed")) == expected_validation_passed
    if "expected_reviewer_ready" in effective_case:
        expected_reviewer_ready = bool(effective_case.get("expected_reviewer_ready"))
    else:
        expected_reviewer_ready = not diagnostic_rule_pack
    reviewer_ready_matches = bool(summary.get("reviewer_ready")) == expected_reviewer_ready
    require_graph_coverage = bool(effective_case.get("require_graph_coverage", True))
    graph_coverage_supported = (
        not require_graph_coverage or validation_checks_passed(validation, GRAPH_COVERAGE_CHECKS)
    )
    min_findings = int(effective_case.get("min_findings", 1))
    min_findings_met = len(selected_findings) >= min_findings
    citation_coverage_supported = bool(selected_findings) and all(
        finding_has_required_eval_citations(finding) for finding in selected_findings
    )
    authority_explanation_path = summary.get("authority_explanation_paths_path")
    authority_explanation_artifact_present = bool(
        authority_explanation_path and Path(str(authority_explanation_path)).exists()
    )
    authority_path_classification_supported = (not selected_findings) or all(
        finding_has_authority_path_classification(finding) for finding in selected_findings
    )
    authority_trace_coverage_supported = diagnostic_rule_pack or (not selected_findings) or all(
        finding_has_graph_or_retrieval_trace(finding) for finding in selected_findings
    )
    unexpected_positive_rule_ids = sorted(
        rule_id
        for rule_id, actual_status in (
            (rule_id, finding.get("status")) for rule_id, finding in findings_by_rule.items()
        )
        if str(actual_status) == "pass" and expected_statuses.get(rule_id) != "pass"
    )
    missing_required_source_rule_ids = sorted(
        mismatch["rule_id"]
        for mismatch in source_record_mismatches
        if expected_statuses.get(str(mismatch.get("rule_id") or "")) == "pass"
    )

    result_flags = {
        "validation_passed_matches": validation_passed_matches,
        "reviewer_ready_matches": reviewer_ready_matches,
        "min_findings_met": min_findings_met,
        "expected_statuses_match": not status_mismatches,
        "expected_claim_types_match": not claim_type_mismatches,
        "expected_package_evidence_match": not package_evidence_mismatches,
        "expected_source_evidence_match": not source_evidence_mismatches,
        "expected_source_claim_links_match": not source_claim_link_mismatches,
        "expected_source_record_ids_match": not source_record_mismatches,
        "expected_source_document_roles_match": not source_document_role_mismatches,
        "status_counts_match": status_counts_match,
        "unsupported_finding_ids_match": unsupported_finding_ids_match,
        "citation_coverage_supported": citation_coverage_supported,
        "graph_coverage_supported": graph_coverage_supported,
        "authority_explanation_artifact_present": authority_explanation_artifact_present,
        "authority_path_classification_supported": authority_path_classification_supported,
        "authority_trace_coverage_supported": authority_trace_coverage_supported,
        "unexpected_positive_rules_absent": not unexpected_positive_rule_ids,
        "missing_required_source_rules_absent": not missing_required_source_rule_ids,
    }
    failure_reasons = [
        name
        for name, passed in result_flags.items()
        if not passed
    ]
    failure_entries = failure_taxonomy(
        result_flags=result_flags,
        status_mismatches=status_mismatches,
        claim_type_mismatches=claim_type_mismatches,
        package_evidence_mismatches=package_evidence_mismatches,
        source_evidence_mismatches=source_evidence_mismatches,
        source_claim_link_mismatches=source_claim_link_mismatches,
        source_record_mismatches=source_record_mismatches,
        source_document_role_mismatches=source_document_role_mismatches,
        validation_failed_checks=failed_check_names(validation),
        selected_findings=selected_findings,
    )
    return {
        "id": case["id"],
        "review_id": result.review_id,
        "source_set_id": report.get("summary", {}).get("source_set_id"),
        "rule_pack_id": report.get("summary", {}).get("rule_pack_id"),
        "rule_pack_version": report.get("summary", {}).get("rule_pack_version"),
        "package_path": str(package_path),
        "review_dir": str(result.review_dir),
        "compliance_review_path": str(result.compliance_review_path),
        "compliance_matrix_path": str(result.compliance_matrix_path),
        "compliance_matrix_markdown_path": str(result.compliance_matrix_markdown_path),
        "compliance_matrix_pdf_path": str(result.compliance_matrix_pdf_path),
        "compliance_validation_path": str(result.compliance_validation_path),
        "authority_explanation_paths_path": authority_explanation_path,
        "finding_nodes_path": str(result.finding_nodes_path),
        "finding_edges_path": str(result.finding_edges_path),
        "source_top_k": source_top_k,
        "package_top_k": package_top_k,
        "filters": filters,
        "finding_count": len(findings),
        "selected_finding_count": len(selected_findings),
        "finding_status_counts": actual_status_counts,
        "expected_statuses": expected_statuses,
        "actual_statuses": {
            rule_id: finding.get("status") for rule_id, finding in sorted(findings_by_rule.items())
        },
        "status_mismatches": status_mismatches,
        "expected_claim_types": expected_claim_types,
        "actual_claim_types": {
            rule_id: finding.get("claim_type")
            for rule_id, finding in sorted(findings_by_rule.items())
        },
        "claim_type_mismatches": claim_type_mismatches,
        "package_evidence_mismatches": package_evidence_mismatches,
        "source_evidence_mismatches": source_evidence_mismatches,
        "source_claim_link_mismatches": source_claim_link_mismatches,
        "expected_source_record_ids": expected_source_record_ids,
        "source_record_mismatches": source_record_mismatches,
        "expected_source_document_roles": expected_source_document_roles,
        "source_document_role_mismatches": source_document_role_mismatches,
        "unexpected_positive_rule_ids": unexpected_positive_rule_ids,
        "missing_required_source_rule_ids": missing_required_source_rule_ids,
        "expected_finding_status_counts": expected_status_counts,
        "expected_unsupported_finding_ids": expected_unsupported,
        "actual_unsupported_finding_ids": actual_unsupported,
        "expected_validation_passed": expected_validation_passed,
        "actual_validation_passed": bool(validation.get("passed")),
        "expected_reviewer_ready": expected_reviewer_ready,
        "actual_reviewer_ready": bool(report.get("summary", {}).get("reviewer_ready")),
        "require_graph_coverage": require_graph_coverage,
        "validation_failed_checks": failed_check_names(validation),
        "finding_results": [eval_finding_summary(finding) for finding in selected_findings],
        "hard_negative_package": bool(effective_case.get("hard_negative_package")),
        "conditional_subset": bool(effective_case.get("conditional_subset")),
        "all_authorities_control": bool(effective_case.get("all_authorities_control")),
        **result_flags,
        "failure_reasons": failure_reasons,
        "failure_taxonomy": failure_entries,
        "failure_category_counts": dict(Counter(item["category"] for item in failure_entries)),
        "reproduction": case_reproduction(result, package_path),
        "passed": not failure_reasons,
    }


def effective_eval_case_expectations(
    *,
    case: dict,
    review_dir: Path,
    findings_by_rule: dict[str, dict],
) -> dict:
    if not (
        _case_requires_generated_rule_pack(case)
        and _case_has_generated_rule_pack_expectations(case)
    ):
        return deepcopy(case)

    rule_ids = evaluation_rule_ids(review_dir=review_dir) or set(findings_by_rule)
    if not rule_ids:
        return deepcopy(case)

    effective_case = deepcopy(case)
    base_statuses = string_map(case.get("expected_statuses") or {})
    generated_statuses = string_map(case.get("expected_generated_statuses") or {})
    merged_statuses = {rule_id: status for rule_id, status in base_statuses.items() if rule_id in rule_ids}
    merged_statuses.update(
        {rule_id: status for rule_id, status in generated_statuses.items() if rule_id in rule_ids}
    )
    if merged_statuses:
        effective_case["expected_statuses"] = merged_statuses
        effective_case["expected_finding_status_counts"] = dict(Counter(merged_statuses.values()))

    generated_source_claim_links = (
        deepcopy(case.get("expected_generated_source_claim_links"))
        if isinstance(case.get("expected_generated_source_claim_links"), dict)
        else {}
    )
    if generated_source_claim_links:
        effective_case["expected_generated_source_claim_links"] = generated_source_claim_links

    for base_field, generated_field in (
        ("expected_claim_types", "expected_generated_claim_types"),
        ("expected_package_evidence", "expected_generated_package_evidence"),
        ("expected_source_evidence", "expected_generated_source_evidence"),
        ("expected_source_claim_links", "expected_generated_source_claim_links"),
        ("expected_source_record_ids", "expected_generated_source_record_ids"),
        ("expected_source_document_roles", "expected_generated_source_document_roles"),
    ):
        base_value = effective_case.get(base_field)
        generated_value = effective_case.get(generated_field)
        if not isinstance(base_value, dict) and not isinstance(generated_value, dict):
            continue
        merged_value = deepcopy(base_value) if isinstance(base_value, dict) else {}
        if isinstance(generated_value, dict):
            merged_value.update(deepcopy(generated_value))
        effective_case[base_field] = {
            str(rule_id): value for rule_id, value in merged_value.items() if str(rule_id) in rule_ids
        }

    for base_field, generated_field in (
        ("expected_validation_passed", "expected_generated_validation_passed"),
        ("expected_reviewer_ready", "expected_generated_reviewer_ready"),
        ("min_findings", "expected_generated_min_findings"),
    ):
        if generated_field in case:
            effective_case[base_field] = deepcopy(case.get(generated_field))

    return effective_case


def evaluation_rule_ids(*, review_dir: Path) -> set[str]:
    path = review_dir / "applicability" / "compliance_evaluation_rule_pack.json"
    if not path.exists():
        return set()
    payload = read_json(path)
    return {
        str(rule.get("id"))
        for rule in payload.get("rules", [])
        if isinstance(rule, dict) and str(rule.get("id") or "").strip()
    }


def filter_eval_findings(findings: list[dict], filters: dict) -> list[dict]:
    return [
        finding
        for finding in findings
        if all(str(finding.get(key) or "") in set(filter_values(value)) for key, value in filters.items())
    ]


def filter_values(value) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if str(value or "").strip():
        return [str(value)]
    return []


def string_map(value: dict) -> dict[str, str]:
    return {str(key): str(item) for key, item in value.items()}


def expected_claim_type_map(case: dict, expected_statuses: dict[str, str]) -> dict[str, str]:
    expected = {rule_id: claim_type(status) for rule_id, status in expected_statuses.items()}
    expected.update(string_map(case.get("expected_claim_types") or {}))
    return expected


def expected_bool_presence_map(
    case: dict,
    key: str,
    expected_statuses: dict[str, str],
    default_for_status,
) -> dict[str, bool]:
    expected = {
        rule_id: bool(default_for_status(status))
        for rule_id, status in expected_statuses.items()
    }
    expected.update({str(rule_id): bool(value) for rule_id, value in (case.get(key) or {}).items()})
    return expected


def expected_string_list_map(case: dict, key: str) -> dict[str, list[str]]:
    return {
        str(rule_id): sorted({str(value) for value in values if str(value).strip()})
        for rule_id, values in (case.get(key) or {}).items()
    }


def source_backed_expected_string_list_map(
    case: dict,
    key: str,
    expected_statuses: dict[str, str],
) -> dict[str, list[str]]:
    return {
        rule_id: values
        for rule_id, values in expected_string_list_map(case, key).items()
        if expected_statuses.get(rule_id) in CLAIM_STATUSES
    }


def expected_subset_mismatches(
    findings_by_rule: dict[str, dict],
    expected: dict[str, list[str]],
    actual_values,
) -> list[dict]:
    failures = []
    for rule_id, expected_values in expected.items():
        finding = findings_by_rule.get(rule_id)
        actual = actual_values(rule_id, finding) if finding else []
        missing = sorted(set(expected_values) - set(actual))
        if missing:
            failures.append(
                {
                    "rule_id": rule_id,
                    "expected": expected_values,
                    "actual": actual,
                    "missing": missing,
                }
            )
    return failures


def normalized_eval_findings_by_rule(
    *,
    findings_by_rule: dict[str, dict],
    expected_statuses: dict[str, str],
    generated_rule_pack_case: bool,
) -> dict[str, dict]:
    if not generated_rule_pack_case:
        return findings_by_rule
    normalized = dict(findings_by_rule)
    for rule_id, expected_status in expected_statuses.items():
        if expected_status != "not_applicable" or rule_id in normalized:
            continue
        normalized[rule_id] = {
            "rule_id": rule_id,
            "status": "not_applicable",
            "claim_type": claim_type("not_applicable"),
            "package_evidence": [],
            "package_evidence_citation": None,
            "source_library_evidence": [],
            "source_library_evidence_citation": None,
            "source_claim_links": [],
            "source_claim_link_count": 0,
        }
    return normalized


def value_mismatches(
    findings_by_rule: dict[str, dict],
    expected: dict[str, str],
    field: str,
) -> list[dict]:
    failures = []
    for rule_id, expected_value in expected.items():
        finding = findings_by_rule.get(rule_id)
        actual = finding.get(field) if finding else None
        if actual != expected_value:
            failures.append({"rule_id": rule_id, "expected": expected_value, "actual": actual})
    return failures


def presence_mismatches(
    findings_by_rule: dict[str, dict],
    expected: dict[str, bool],
    predicate,
) -> list[dict]:
    failures = []
    for rule_id, expected_value in expected.items():
        finding = findings_by_rule.get(rule_id)
        actual = bool(finding and predicate(finding))
        if actual != expected_value:
            failures.append({"rule_id": rule_id, "expected": expected_value, "actual": actual})
    return failures


def finding_has_package_evidence(finding: dict) -> bool:
    return bool(finding.get("package_evidence_citation") and finding.get("package_evidence"))


def finding_has_source_evidence(finding: dict) -> bool:
    return bool(finding.get("source_library_evidence_citation") and finding.get("source_library_evidence"))


def finding_has_source_claim_links(finding: dict) -> bool:
    return bool(finding.get("source_claim_link_count") and finding.get("source_claim_links"))


def finding_has_required_eval_citations(finding: dict) -> bool:
    status = finding.get("status")
    if status not in CLAIM_STATUSES:
        return True
    if not finding_has_source_evidence(finding) or not finding_has_source_claim_links(finding):
        return False
    if status == "pass" and not finding_has_package_evidence(finding):
        return False
    return True


def finding_has_authority_path_classification(finding: dict) -> bool:
    return bool(finding.get("authority_path_classifications"))


def finding_has_graph_or_retrieval_trace(finding: dict) -> bool:
    return bool(
        finding.get("retrieval_trace_ids")
        or finding.get("graph_path_ids")
        or finding.get("search_coverage_certificate_ids")
    )


def applicability_gate_is_diagnostic(applicability_gate: object) -> bool:
    if not isinstance(applicability_gate, dict):
        return False
    mode = str(applicability_gate.get("mode") or "").strip()
    return mode.endswith("_diagnostic")


def finding_source_record_ids_with_aliases(rule_id: str, finding: dict) -> list[str]:
    del rule_id
    return aliased_source_record_ids(finding_source_record_ids(finding))


def finding_source_document_roles_for_eval(rule_id: str, finding: dict) -> list[str]:
    del rule_id
    return finding_source_document_roles(finding)


def eval_finding_summary(finding: dict) -> dict:
    return {
        "rule_id": finding.get("rule_id"),
        "status": finding.get("status"),
        "claim_type": finding.get("claim_type"),
        "package_evidence_citation": finding.get("package_evidence_citation"),
        "source_library_evidence_citation": finding.get("source_library_evidence_citation"),
        "source_claim_link_count": finding.get("source_claim_link_count", 0),
        "applied_source_record_ids": finding_source_record_ids(finding),
        "applied_source_document_roles": finding_source_document_roles(finding),
        "authority_path_classifications": finding.get("authority_path_classifications") or [],
        "retrieval_trace_ids": finding.get("retrieval_trace_ids") or [],
        "graph_path_ids": finding.get("graph_path_ids") or [],
        "search_coverage_certificate_ids": finding.get("search_coverage_certificate_ids") or [],
    }


def failure_taxonomy(
    *,
    result_flags: dict[str, bool],
    status_mismatches: list[dict],
    claim_type_mismatches: list[dict],
    package_evidence_mismatches: list[dict],
    source_evidence_mismatches: list[dict],
    source_claim_link_mismatches: list[dict],
    source_record_mismatches: list[dict],
    source_document_role_mismatches: list[dict],
    validation_failed_checks: list[str],
    selected_findings: list[dict],
) -> list[dict]:
    taxonomy = []
    if not result_flags["validation_passed_matches"] or not result_flags["reviewer_ready_matches"]:
        taxonomy.append(
            taxonomy_entry(
                "validation_gate_miss",
                validation_failed_checks,
                ["reviewer_ready", "validation_passed"],
            )
        )
    if not result_flags["min_findings_met"]:
        taxonomy.append(taxonomy_entry("rule_wording_issue", [], ["min_findings"]))
    if status_mismatches or claim_type_mismatches:
        taxonomy.append(
            taxonomy_entry(
                "rule_wording_issue",
                status_mismatches + claim_type_mismatches,
            )
        )
    if package_evidence_mismatches:
        taxonomy.append(
            taxonomy_entry("package_evidence_search_miss", package_evidence_mismatches)
        )
    if source_evidence_mismatches:
        taxonomy.append(taxonomy_entry("source_retrieval_miss", source_evidence_mismatches))
    if source_claim_link_mismatches:
        taxonomy.append(taxonomy_entry("rule_claim_binding_miss", source_claim_link_mismatches))
    if source_record_mismatches or source_document_role_mismatches:
        taxonomy.append(
            taxonomy_entry(
                "source_applicability_miss",
                source_record_mismatches + source_document_role_mismatches,
            )
        )
    if not result_flags["authority_explanation_artifact_present"]:
        taxonomy.append(taxonomy_entry("authority_explanation_artifact_miss", []))
    if not result_flags["authority_path_classification_supported"]:
        taxonomy.append(taxonomy_entry("authority_path_classification_miss", []))
    if not result_flags["authority_trace_coverage_supported"]:
        taxonomy.append(taxonomy_entry("authority_trace_coverage_miss", []))
    if not result_flags["citation_coverage_supported"]:
        unsupported = [
            finding.get("rule_id")
            for finding in selected_findings
            if not finding_has_required_eval_citations(finding)
        ]
        taxonomy.append(taxonomy_entry("citation_relevance_issue", unsupported))
    if not result_flags["graph_coverage_supported"]:
        taxonomy.append(
            taxonomy_entry(
                "finding_graph_miss",
                validation_failed_checks,
                sorted(GRAPH_COVERAGE_CHECKS),
            )
        )
    return taxonomy


def taxonomy_entry(
    category: str,
    evidence: list,
    checks: list[str] | None = None,
) -> dict:
    rule_ids = sorted(
        {
            str(item.get("rule_id"))
            for item in evidence
            if isinstance(item, dict) and item.get("rule_id")
        }
    )
    if not rule_ids:
        rule_ids = sorted({str(item) for item in evidence if isinstance(item, str)})
    return {
        "category": category,
        "rule_ids": rule_ids,
        "checks": checks or [],
        "evidence": evidence,
    }


def failure_category_counts(cases: list[dict]) -> dict[str, int]:
    counts = Counter()
    for case in cases:
        for item in case.get("failure_taxonomy", []):
            counts[str(item.get("category"))] += 1
    return dict(sorted(counts.items()))


def case_reproduction(result: ComplianceReviewResult, package_path: Path) -> dict:
    return {
        "command": (
            "PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review "
            f"--package-path {package_path} --output-dir <source_library> "
            f"--review-id {result.review_id}"
        ),
        "review_dir": str(result.review_dir),
        "package_path": str(package_path),
        "compliance_review_path": str(result.compliance_review_path),
        "compliance_matrix_path": str(result.compliance_matrix_path),
        "compliance_matrix_pdf_path": str(result.compliance_matrix_pdf_path),
        "compliance_validation_path": str(result.compliance_validation_path),
    }


def case_rate(cases: list[dict], key: str, *, invert: bool = False) -> float:
    if invert:
        return rate(sum(1 for case in cases if not case.get(key)), len(cases))
    return rate(sum(1 for case in cases if case.get(key)), len(cases))


def rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 6)


def compliance_review_eval_coverage_check(
    contract: dict,
    case_results: list[dict],
    *,
    legacy_format: bool,
) -> dict:
    if legacy_format:
        return {
            "name": "coverage_requirements_met",
            "passed": True,
            "details": {"enabled": False, "legacy_format": True},
        }
    requirements = contract.get("coverage_requirements", {})
    actuals = {
        "case_count": len(case_results),
        "hard_negative_package_case_count": sum(
            1 for case in case_results if case["hard_negative_package"]
        ),
        "conditional_subset_case_count": sum(
            1 for case in case_results if case["conditional_subset"]
        ),
        "all_authorities_control_case_count": sum(
            1 for case in case_results if case["all_authorities_control"]
        ),
    }
    failures = [
        {
            "requirement": key,
            "min": int(requirements.get(key) or 0),
            "actual": actuals[key],
        }
        for key in actuals
        if actuals[key] < int(requirements.get(key) or 0)
    ]
    return {
        "name": "coverage_requirements_met",
        "passed": not failures,
        "details": {
            "enabled": True,
            "requirements": requirements,
            "actuals": actuals,
            "failures": failures,
        },
    }


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
