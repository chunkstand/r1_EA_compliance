from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from .compliance_inputs import coverage_certificate_id
from .compliance_inputs import coverage_certificates_by_id
from .compliance_inputs import optional_path
from .compliance_inputs import read_json_if_exists_or_empty
from .compliance_inputs import read_jsonl_if_exists
from .compliance_inputs import strings
from .compliance_inputs import write_json
from .compliance_outputs import finding_source_record_ids


FOREST_PLAN_COMPONENT_AUTHORITY_FAMILY_ID = "nfma_forest_planning_project_consistency"


def authority_integration_context(
    *,
    review_id: str,
    source_set_id: str,
    rule_pack: dict,
    findings: list[dict],
    applicability_gate: dict,
    authority_provenance_path: Path,
    non_applicable_authority_appendix_path: Path,
    non_applicable_authority_appendix_markdown_path: Path,
    reviewer_resolution_report_path: Path,
    litigation_risk_summary_path: Path,
) -> dict:
    generated_mode = bool(applicability_gate.get("is_generated_rule_pack"))
    decisions = read_jsonl_if_exists(
        optional_path(applicability_gate.get("applicability_decisions_path"))
    )
    applicable = read_json_if_exists_or_empty(
        optional_path(applicability_gate.get("applicable_authorities_path"))
    )
    non_applicable = read_json_if_exists_or_empty(
        optional_path(applicability_gate.get("non_applicable_authorities_path"))
    )
    coverage = read_json_if_exists_or_empty(
        optional_path(applicability_gate.get("search_coverage_certificates_path"))
    )
    coverage_by_id = coverage_certificates_by_id(coverage)
    finding_provenance = [
        _finding_authority_provenance(finding) for finding in findings
    ]
    non_applicable_rows = [
        _non_applicable_authority_row(authority, coverage_by_id)
        for authority in non_applicable.get("authorities") or []
        if isinstance(authority, dict)
    ]
    pending_resolution = [
        _reviewer_resolution_item(decision)
        for decision in decisions
        if str(decision.get("status") or "") in {"unresolved", "needs_adjudication"}
    ]
    adjudicated = [
        _reviewer_resolution_item(decision)
        for decision in decisions
        if _decision_is_adjudicated(decision)
    ]
    risk_flags = _litigation_risk_flags(
        findings=findings,
        non_applicable_rows=non_applicable_rows,
        pending_resolution=pending_resolution,
        adjudicated=adjudicated,
    )
    summary = {
        "schema_version": "authority-review-integration-summary-v0",
        "generated_mode": generated_mode,
        "applicable_authority_count": len(applicable.get("authorities") or []),
        "non_applicable_authority_count": len(non_applicable_rows),
        "pending_resolution_count": len(pending_resolution),
        "adjudicated_authority_count": len(adjudicated),
        "risk_flag_count": len(risk_flags),
        "finding_authority_provenance_count": len(finding_provenance),
        "findings_missing_candidate_authority_ids": [
            row["rule_id"] for row in finding_provenance if not row["candidate_authority_id"]
        ],
        "findings_missing_authority_family_ids": [
            row["rule_id"] for row in finding_provenance if not row["authority_family_ids"]
        ],
        "non_applicable_authorities_missing_coverage": [
            row["candidate_authority_id"]
            for row in non_applicable_rows
            if not row["search_coverage_certificate_ids"]
        ],
        "non_applicable_authorities_missing_rationale": [
            row["candidate_authority_id"] for row in non_applicable_rows if not row["rationale"]
        ],
        "legal_conclusion_count": sum(
            1 for flag in risk_flags if bool(flag.get("legal_conclusion"))
        ),
    }
    return {
        "review_id": review_id,
        "source_set_id": source_set_id,
        "rule_pack_id": rule_pack.get("rule_pack_id"),
        "rule_pack_version": rule_pack.get("version"),
        "generated_mode": generated_mode,
        "authority_provenance_path": str(authority_provenance_path),
        "non_applicable_authority_appendix_path": str(
            non_applicable_authority_appendix_path
        ),
        "non_applicable_authority_appendix_markdown_path": str(
            non_applicable_authority_appendix_markdown_path
        ),
        "reviewer_resolution_report_path": str(reviewer_resolution_report_path),
        "litigation_risk_summary_path": str(litigation_risk_summary_path),
        "applicable_authorities_path": applicability_gate.get("applicable_authorities_path"),
        "non_applicable_authorities_path": applicability_gate.get(
            "non_applicable_authorities_path"
        ),
        "search_coverage_certificates_path": applicability_gate.get(
            "search_coverage_certificates_path"
        ),
        "applicability_decisions_path": applicability_gate.get(
            "applicability_decisions_path"
        ),
        "finding_provenance": finding_provenance,
        "non_applicable_rows": non_applicable_rows,
        "pending_resolution": pending_resolution,
        "adjudicated": adjudicated,
        "risk_flags": risk_flags,
        "summary": summary,
    }


def write_authority_integration_artifacts(
    *,
    context: dict,
    summary: dict,
    validation: dict,
) -> None:
    created_at = _utc_now()
    common = {
        "created_at": created_at,
        "review_id": context["review_id"],
        "source_set_id": context["source_set_id"],
        "rule_pack_id": context.get("rule_pack_id"),
        "rule_pack_version": context.get("rule_pack_version"),
        "compliance_review_path": summary.get("compliance_review_path"),
        "compliance_matrix_path": summary.get("compliance_matrix_path"),
        "compliance_validation_path": summary.get("compliance_validation_path"),
    }
    write_json(
        Path(context["authority_provenance_path"]),
        {
            "schema_version": "authority-family-provenance-v0",
            **common,
            "summary": context["summary"],
            "finding_authority_provenance": context["finding_provenance"],
        },
    )
    appendix = {
        "schema_version": "non-applicable-authority-appendix-v0",
        **common,
        "summary": {
            "non_applicable_authority_count": len(context["non_applicable_rows"]),
            "coverage_certificate_count": sum(
                len(row.get("coverage_certificates") or [])
                for row in context["non_applicable_rows"]
            ),
            "all_have_coverage_certificates": not context["summary"][
                "non_applicable_authorities_missing_coverage"
            ],
            "all_have_rationale": not context["summary"][
                "non_applicable_authorities_missing_rationale"
            ],
            "source_artifact_path": context.get("non_applicable_authorities_path"),
            "search_coverage_certificates_path": context.get(
                "search_coverage_certificates_path"
            ),
        },
        "authorities": context["non_applicable_rows"],
    }
    write_json(Path(context["non_applicable_authority_appendix_path"]), appendix)
    _write_non_applicable_appendix_markdown(
        Path(context["non_applicable_authority_appendix_markdown_path"]),
        appendix,
    )
    write_json(
        Path(context["reviewer_resolution_report_path"]),
        {
            "schema_version": "authority-reviewer-resolution-report-v0",
            **common,
            "summary": {
                "pending_resolution_count": len(context["pending_resolution"]),
                "adjudicated_authority_count": len(context["adjudicated"]),
                "reviewer_ready_blocked": bool(context["pending_resolution"]),
                "passed": not context["pending_resolution"],
            },
            "pending_resolution_items": context["pending_resolution"],
            "adjudicated_authorities": context["adjudicated"],
        },
    )
    write_json(
        Path(context["litigation_risk_summary_path"]),
        {
            "schema_version": "litigation-risk-summary-v0",
            **common,
            "summary": {
                "risk_flag_count": len(context["risk_flags"]),
                "risk_category_counts": dict(
                    sorted(
                        Counter(
                            flag["risk_category"] for flag in context["risk_flags"]
                        ).items()
                    )
                ),
                "legal_conclusion_count": context["summary"]["legal_conclusion_count"],
                "deterministic_only": context["summary"]["legal_conclusion_count"] == 0,
                "validation_passed": bool(validation.get("passed")),
            },
            "risk_flags": context["risk_flags"],
        },
    )


def _finding_authority_provenance(finding: dict) -> dict:
    source_record_ids = set(strings([finding.get("authority_source_record_id")]))
    source_record_ids.update(finding_source_record_ids(finding))
    return {
        "finding_id": finding.get("id"),
        "rule_id": finding.get("rule_id"),
        "status": finding.get("status"),
        "candidate_authority_id": finding.get("candidate_authority_id"),
        "candidate_authority_type": finding.get("candidate_authority_type"),
        "applicability_decision_id": finding.get("applicability_decision_id"),
        "authority_family_ids": strings(finding.get("authority_family_ids")),
        "basis_type": finding.get("applicability_basis_type"),
        "authority_source_record_id": finding.get("authority_source_record_id"),
        "source_record_ids": sorted(source_record_ids),
        "authority_document_role": finding.get("authority_document_role"),
        "applicability_status": finding.get("applicability_status"),
        "applicability_mode": finding.get("applicability_mode"),
        "generated_from_applicability": bool(finding.get("generated_from_applicability")),
        "human_adjudication_refs": finding.get("human_adjudication_refs") or [],
        "search_coverage_certificate_ids": strings(
            finding.get("search_coverage_certificate_ids")
        ),
    }


def _non_applicable_authority_row(authority: dict, coverage_by_id: dict[str, dict]) -> dict:
    certificate_ids = strings(authority.get("search_coverage_certificate_ids"))
    certificates = [
        _compact_coverage_certificate(coverage_by_id[certificate_id])
        for certificate_id in certificate_ids
        if certificate_id in coverage_by_id
    ]
    basis = authority.get("non_applicability_basis") or authority.get("applicability_basis") or {}
    authority_family_ids = strings(authority.get("authority_family_ids"))
    authority_family_ids.extend(
        strings(
            [
                authority.get("authority_family_id"),
                (authority.get("rule_template") or {}).get("authority_family_id"),
            ]
        )
    )
    if (
        not authority_family_ids
        and authority.get("candidate_authority_type") == "forest_plan_component"
    ):
        authority_family_ids.append(FOREST_PLAN_COMPONENT_AUTHORITY_FAMILY_ID)
    authority_family_ids = sorted(set(authority_family_ids))
    return {
        "decision_id": authority.get("decision_id"),
        "candidate_authority_id": authority.get("candidate_authority_id"),
        "candidate_authority_type": authority.get("candidate_authority_type"),
        "authority_family_ids": authority_family_ids,
        "authority_family_id": authority_family_ids[0] if authority_family_ids else None,
        "status": authority.get("status"),
        "basis_type": authority.get("basis_type"),
        "rationale": basis.get("rationale") if isinstance(basis, dict) else None,
        "source_record_ids": strings(authority.get("source_record_ids")),
        "authority_category": authority.get("authority_category"),
        "authority_document_role": authority.get("authority_document_role"),
        "search_coverage_certificate_ids": certificate_ids,
        "coverage_certificates": certificates,
        "negative_evidence_spans": authority.get("negative_evidence_spans") or [],
        "explicit_trigger_miss_evidence": authority.get("explicit_trigger_miss_evidence") or [],
        "human_adjudication_refs": authority.get("human_adjudication_refs") or [],
    }


def _reviewer_resolution_item(decision: dict) -> dict:
    rule_template = (
        decision.get("rule_template")
        if isinstance(decision.get("rule_template"), dict)
        else {}
    )
    basis = decision.get("basis") if isinstance(decision.get("basis"), dict) else {}
    authority_family_ids = strings(decision.get("authority_family_ids"))
    authority_family_ids.extend(
        strings([decision.get("authority_family_id"), rule_template.get("authority_family_id")])
    )
    if (
        not authority_family_ids
        and decision.get("candidate_authority_type") == "forest_plan_component"
    ):
        authority_family_ids.append(FOREST_PLAN_COMPONENT_AUTHORITY_FAMILY_ID)
    authority_family_ids = sorted(set(authority_family_ids))
    return {
        "decision_id": decision.get("decision_id"),
        "candidate_authority_id": decision.get("candidate_authority_id"),
        "candidate_authority_type": decision.get("candidate_authority_type"),
        "authority_family_ids": authority_family_ids,
        "authority_family_id": authority_family_ids[0] if authority_family_ids else None,
        "rule_id": rule_template.get("rule_id"),
        "status": decision.get("status"),
        "basis_type": decision.get("basis_type"),
        "rationale": basis.get("rationale"),
        "adjudication_state": decision.get("adjudication_state"),
        "human_adjudication_refs": decision.get("human_adjudication_refs") or [],
        "missing_evidence": decision.get("missing_evidence") or [],
        "contradiction_notes": decision.get("contradiction_notes") or [],
        "search_coverage_certificate_ids": strings(
            decision.get("search_coverage_certificate_ids")
        ),
    }


def _decision_is_adjudicated(decision: dict) -> bool:
    return (
        str(decision.get("basis_type") or "") == "human_adjudication"
        or bool(decision.get("human_adjudication_refs"))
        or str(decision.get("adjudication_state") or "") == "adjudicated"
    )


def _litigation_risk_flags(
    *,
    findings: list[dict],
    non_applicable_rows: list[dict],
    pending_resolution: list[dict],
    adjudicated: list[dict],
) -> list[dict]:
    flags = []
    for finding in findings:
        if finding.get("status") != "gap":
            continue
        flags.append(
            _risk_flag(
                category="package_evidence_gap",
                severity=str(finding.get("severity") or "medium"),
                rule_ids=[str(finding.get("rule_id"))],
                authority_family_ids=strings(finding.get("authority_family_ids")),
                candidate_authority_ids=strings([finding.get("candidate_authority_id")]),
                evidence_refs=_evidence_refs_for_finding(finding),
                rationale=(
                    "The deterministic compliance review found source authority support but "
                    "did not find matching package evidence for this generated applicable rule."
                ),
            )
        )
    for row in non_applicable_rows:
        flags.append(
            _risk_flag(
                category="non_applicable_authority_coverage_boundary",
                severity="informational",
                rule_ids=[],
                authority_family_ids=strings([row.get("authority_family_id")]),
                candidate_authority_ids=strings([row.get("candidate_authority_id")]),
                evidence_refs=row.get("search_coverage_certificate_ids") or [],
                rationale=(
                    "The authority was excluded from compliance findings by a deterministic "
                    "not-applicable decision with recorded search-coverage certificates."
                ),
            )
        )
    for item in pending_resolution:
        flags.append(
            _risk_flag(
                category="unresolved_authority_family_requires_resolution",
                severity="blocking",
                rule_ids=strings([item.get("rule_id")]),
                authority_family_ids=strings([item.get("authority_family_id")]),
                candidate_authority_ids=strings([item.get("candidate_authority_id")]),
                evidence_refs=item.get("search_coverage_certificate_ids") or [],
                rationale=(
                    "An applicability decision remains unresolved or needs adjudication; "
                    "reviewer-ready compliance output must stay blocked until resolved."
                ),
            )
        )
    for item in adjudicated:
        flags.append(
            _risk_flag(
                category="human_adjudicated_authority_family",
                severity="reviewer_record",
                rule_ids=strings([item.get("rule_id")]),
                authority_family_ids=strings([item.get("authority_family_id")]),
                candidate_authority_ids=strings([item.get("candidate_authority_id")]),
                evidence_refs=[
                    str(ref.get("adjudication_id") or ref.get("source_type") or ref)
                    for ref in item.get("human_adjudication_refs") or []
                ],
                rationale=(
                    "A deterministic weak or conflicting applicability decision was resolved "
                    "through a recorded human-adjudication artifact."
                ),
            )
        )
    return flags


def _risk_flag(
    *,
    category: str,
    severity: str,
    rule_ids: list[str],
    authority_family_ids: list[str],
    candidate_authority_ids: list[str],
    evidence_refs: list[str],
    rationale: str,
) -> dict:
    return {
        "risk_category": category,
        "severity": severity,
        "rule_ids": sorted(set(rule_ids)),
        "authority_family_ids": sorted(set(authority_family_ids)),
        "candidate_authority_ids": sorted(set(candidate_authority_ids)),
        "evidence_refs": sorted({str(ref) for ref in evidence_refs if str(ref or "").strip()}),
        "artifact_refs": sorted({str(ref) for ref in evidence_refs if str(ref or "").strip()}),
        "rationale": rationale,
        "deterministic_basis": True,
        "legal_conclusion": False,
    }


def _evidence_refs_for_finding(finding: dict) -> list[str]:
    refs = strings(
        [
            finding.get("package_evidence_citation"),
            finding.get("source_library_evidence_citation"),
        ]
    )
    refs.extend(strings(finding.get("source_claim_evidence_citations")))
    return refs


def _compact_coverage_certificate(certificate: dict) -> dict:
    return {
        "coverage_certificate_id": coverage_certificate_id(certificate),
        "coverage_class": certificate.get("coverage_class"),
        "coverage_result": certificate.get("coverage_result"),
        "covered_candidate_authority_ids": strings(
            certificate.get("covered_candidate_authority_ids")
        ),
        "covered_decision_ids": strings(certificate.get("covered_decision_ids")),
        "executed_query_variants": strings(certificate.get("executed_query_variants")),
        "missing_query_variants": strings(certificate.get("missing_query_variants")),
        "rationale": certificate.get("rationale"),
    }


def _write_non_applicable_appendix_markdown(path: Path, appendix: dict) -> None:
    summary = appendix.get("summary") or {}
    lines = [
        "# Non-Applicable Authority Appendix",
        "",
        f"- Review ID: `{appendix.get('review_id')}`",
        f"- Source set: `{appendix.get('source_set_id')}`",
        f"- Non-applicable authorities: `{summary.get('non_applicable_authority_count', 0)}`",
        f"- Coverage certificates: `{summary.get('coverage_certificate_count', 0)}`",
        "",
        "| Authority | Basis | Coverage | Rationale |",
        "| --- | --- | --- | --- |",
    ]
    for row in appendix.get("authorities") or []:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("candidate_authority_id") or ""),
                    str(row.get("basis_type") or ""),
                    ", ".join(row.get("search_coverage_certificate_ids") or []),
                    str(row.get("rationale") or ""),
                ]
            )
            + " |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
