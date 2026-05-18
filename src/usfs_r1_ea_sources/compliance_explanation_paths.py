from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import json


AUTHORITY_EXPLANATION_PATHS_SCHEMA_VERSION = "authority-explanation-paths-v0"
CONTROLLING_DOCUMENT_ROLES = {
    "law",
    "regulation",
    "executive_order",
    "forest_plan",
    "state_requirement",
}
INTERPRETIVE_DOCUMENT_ROLES = {
    "agency_policy",
    "case_law",
}
SUPERSEDED_BASIS_MARKERS = ("supersed", "historical", "archive", "currentness_only")


def build_authority_explanation_context(
    *,
    review_id: str,
    source_set_id: str,
    findings: list[dict[str, Any]],
    authority_integration: dict[str, Any],
    authority_explanation_paths_path: Path,
) -> dict[str, Any]:
    generated_mode = bool(authority_integration.get("generated_mode"))
    risk_flags = authority_integration.get("risk_flags") or []
    enriched_findings = []
    finding_rows = []
    for finding in findings:
        finding_row = _finding_explanation_row(
            finding=finding,
            risk_flags=risk_flags,
        )
        enriched_findings.append(
            {
                **finding,
                "authority_explanation_id": finding_row["authority_explanation_id"],
                "authority_path_classifications": finding_row["authority_path_classifications"],
                "primary_authority_path_classification": finding_row[
                    "primary_authority_path_classification"
                ],
                "retrieval_trace_ids": finding_row["retrieval_trace_ids"],
                "graph_path_ids": finding_row["graph_path_ids"],
                "supporting_source_record_ids": finding_row["supporting_source_record_ids"],
                "residual_risk_categories": finding_row["residual_risk_categories"],
                "unresolved_issue_refs": finding_row["unresolved_issue_refs"],
            }
        )
        finding_rows.append(finding_row)

    non_applicable_rows = [
        _decision_explanation_row(
            row=row,
            row_kind="non_applicable_authority",
            risk_flags=risk_flags,
        )
        for row in authority_integration.get("non_applicable_rows") or []
    ]
    pending_resolution_rows = [
        _decision_explanation_row(
            row=row,
            row_kind="pending_resolution",
            risk_flags=risk_flags,
        )
        for row in authority_integration.get("pending_resolution") or []
    ]
    adjudicated_rows = [
        _decision_explanation_row(
            row=row,
            row_kind="adjudicated_authority",
            risk_flags=risk_flags,
        )
        for row in authority_integration.get("adjudicated") or []
    ]

    summary = _context_summary(
        generated_mode=generated_mode,
        finding_rows=finding_rows,
        non_applicable_rows=non_applicable_rows,
        pending_resolution_rows=pending_resolution_rows,
        adjudicated_rows=adjudicated_rows,
    )
    return {
        "review_id": review_id,
        "source_set_id": source_set_id,
        "generated_mode": generated_mode,
        "authority_explanation_paths_path": str(authority_explanation_paths_path),
        "enriched_findings": enriched_findings,
        "finding_explanation_paths": finding_rows,
        "non_applicable_explanation_paths": non_applicable_rows,
        "pending_resolution_paths": pending_resolution_rows,
        "adjudicated_authority_paths": adjudicated_rows,
        "summary": summary,
    }


def write_authority_explanation_artifact(
    *,
    context: dict[str, Any],
    summary: dict[str, Any],
    validation: dict[str, Any],
) -> None:
    path = Path(context["authority_explanation_paths_path"])
    payload = {
        "schema_version": AUTHORITY_EXPLANATION_PATHS_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": context["review_id"],
        "source_set_id": context["source_set_id"],
        "compliance_review_path": summary.get("compliance_review_path"),
        "compliance_matrix_path": summary.get("compliance_matrix_path"),
        "compliance_validation_path": summary.get("compliance_validation_path"),
        "summary": {
            **(context.get("summary") or {}),
            "validation_passed": bool(validation.get("passed")),
            "reviewer_ready": bool(summary.get("reviewer_ready")),
        },
        "finding_explanation_paths": context.get("finding_explanation_paths") or [],
        "non_applicable_explanation_paths": context.get("non_applicable_explanation_paths")
        or [],
        "pending_resolution_paths": context.get("pending_resolution_paths") or [],
        "adjudicated_authority_paths": context.get("adjudicated_authority_paths") or [],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _context_summary(
    *,
    generated_mode: bool,
    finding_rows: list[dict[str, Any]],
    non_applicable_rows: list[dict[str, Any]],
    pending_resolution_rows: list[dict[str, Any]],
    adjudicated_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    all_rows = [
        *finding_rows,
        *non_applicable_rows,
        *pending_resolution_rows,
        *adjudicated_rows,
    ]
    classification_counts = Counter(
        classification
        for row in all_rows
        for classification in row.get("authority_path_classifications") or []
    )
    risk_category_counts = Counter(
        category
        for row in all_rows
        for category in row.get("residual_risk_categories") or []
    )
    all_findings_have_classification = all(
        bool(row.get("authority_path_classifications")) for row in finding_rows
    )
    all_applicable_findings_have_trace_evidence = all(
        _row_has_trace_evidence(row) for row in finding_rows if _is_applicable_finding_row(row)
    )
    all_non_applicable_paths_have_boundary_evidence = all(
        bool(row.get("search_coverage_certificate_ids") or row.get("human_adjudication_refs"))
        for row in non_applicable_rows
    )
    passed = (
        all_findings_have_classification
        and (not generated_mode or all_applicable_findings_have_trace_evidence)
        and all_non_applicable_paths_have_boundary_evidence
    )
    return {
        "generated_mode": generated_mode,
        "passed": passed,
        "finding_path_count": len(finding_rows),
        "non_applicable_path_count": len(non_applicable_rows),
        "pending_resolution_path_count": len(pending_resolution_rows),
        "adjudicated_path_count": len(adjudicated_rows),
        "path_classification_counts": dict(sorted(classification_counts.items())),
        "risk_category_counts": dict(sorted(risk_category_counts.items())),
        "unresolved_issue_count": sum(
            len(row.get("unresolved_issue_refs") or []) for row in all_rows
        ),
        "all_findings_have_path_classification": all_findings_have_classification,
        "all_applicable_findings_have_trace_evidence": all_applicable_findings_have_trace_evidence,
        "all_non_applicable_paths_have_boundary_evidence": (
            all_non_applicable_paths_have_boundary_evidence
        ),
    }


def _finding_explanation_row(
    *,
    finding: dict[str, Any],
    risk_flags: list[dict[str, Any]],
) -> dict[str, Any]:
    rule_id = str(finding.get("rule_id") or "")
    candidate_authority_id = str(finding.get("candidate_authority_id") or "")
    retrieval_trace_ids = _strings(finding.get("retrieval_trace_ids"))
    graph_path_ids = _strings(finding.get("graph_path_ids"))
    supporting_source_record_ids = _strings(finding.get("supporting_source_record_ids"))
    unresolved_issue_refs = _unresolved_issue_refs(finding)
    residual_risk_categories = _risk_categories_for_row(
        row=finding,
        risk_flags=risk_flags,
    )
    path_classifications = _path_classifications(
        document_role=str(finding.get("authority_document_role") or ""),
        applicability_status=str(finding.get("applicability_status") or ""),
        basis_type=str(finding.get("applicability_basis_type") or ""),
        supporting_source_record_ids=supporting_source_record_ids,
        human_adjudication_refs=finding.get("human_adjudication_refs") or [],
    )
    return {
        "authority_explanation_id": f"authority-explanation:{rule_id or candidate_authority_id}",
        "row_kind": "finding",
        "finding_id": finding.get("id"),
        "rule_id": rule_id,
        "status": finding.get("status"),
        "applicability_status": finding.get("applicability_status"),
        "candidate_authority_id": candidate_authority_id or None,
        "candidate_authority_type": finding.get("candidate_authority_type"),
        "authority_family_ids": _strings(finding.get("authority_family_ids")),
        "authority_source_record_id": finding.get("authority_source_record_id"),
        "source_record_ids": _finding_source_record_ids(finding),
        "supporting_source_record_ids": supporting_source_record_ids,
        "authority_document_role": finding.get("authority_document_role"),
        "primary_authority_path_classification": path_classifications[0]
        if path_classifications
        else None,
        "authority_path_classifications": path_classifications,
        "retrieval_trace_ids": retrieval_trace_ids,
        "graph_path_ids": graph_path_ids,
        "search_coverage_certificate_ids": _strings(
            finding.get("search_coverage_certificate_ids")
        ),
        "human_adjudication_refs": _adjudication_refs(finding.get("human_adjudication_refs")),
        "residual_risk_categories": residual_risk_categories,
        "unresolved_issue_refs": unresolved_issue_refs,
        "package_citation": finding.get("package_evidence_citation"),
        "source_citation": finding.get("source_library_evidence_citation"),
        "source_claim_ids": _strings(finding.get("source_claim_ids")),
        "explanation_summary": _finding_explanation_summary(
            finding=finding,
            path_classifications=path_classifications,
        ),
    }


def _decision_explanation_row(
    *,
    row: dict[str, Any],
    row_kind: str,
    risk_flags: list[dict[str, Any]],
) -> dict[str, Any]:
    basis_type = str(row.get("basis_type") or "")
    path_classifications = _path_classifications(
        document_role=str(row.get("authority_document_role") or ""),
        applicability_status=str(row.get("status") or ""),
        basis_type=basis_type,
        supporting_source_record_ids=[],
        human_adjudication_refs=row.get("human_adjudication_refs") or [],
    )
    unresolved_issue_refs = _decision_unresolved_issue_refs(row)
    return {
        "authority_explanation_id": (
            f"authority-explanation:{row_kind}:{str(row.get('decision_id') or row.get('candidate_authority_id') or '')}"
        ),
        "row_kind": row_kind,
        "decision_id": row.get("decision_id"),
        "rule_id": row.get("rule_id"),
        "status": row.get("status"),
        "candidate_authority_id": row.get("candidate_authority_id"),
        "candidate_authority_type": row.get("candidate_authority_type"),
        "authority_family_ids": _strings(row.get("authority_family_ids")),
        "source_record_ids": _strings(row.get("source_record_ids")),
        "authority_document_role": row.get("authority_document_role"),
        "primary_authority_path_classification": path_classifications[0]
        if path_classifications
        else None,
        "authority_path_classifications": path_classifications,
        "retrieval_trace_ids": _strings(row.get("retrieval_trace_ids")),
        "graph_path_ids": _strings(row.get("graph_path_ids")),
        "search_coverage_certificate_ids": _strings(
            row.get("search_coverage_certificate_ids")
        ),
        "human_adjudication_refs": _adjudication_refs(row.get("human_adjudication_refs")),
        "residual_risk_categories": _risk_categories_for_row(row=row, risk_flags=risk_flags),
        "unresolved_issue_refs": unresolved_issue_refs,
        "explanation_summary": _decision_explanation_summary(
            row_kind=row_kind,
            status=str(row.get("status") or ""),
            basis_type=basis_type,
        ),
    }


def _finding_explanation_summary(
    *,
    finding: dict[str, Any],
    path_classifications: list[str],
) -> str:
    classification_text = ", ".join(path_classifications) or "unclassified"
    return (
        f"{classification_text} authority path for rule "
        f"{finding.get('rule_id') or 'unknown'} with finding status "
        f"{finding.get('status') or 'unknown'}."
    )


def _decision_explanation_summary(
    *,
    row_kind: str,
    status: str,
    basis_type: str,
) -> str:
    return (
        f"{row_kind.replace('_', ' ')} remains {status or 'unknown'} "
        f"with basis {basis_type or 'not-recorded'}."
    )


def _row_has_trace_evidence(row: dict[str, Any]) -> bool:
    return bool(row.get("retrieval_trace_ids") or row.get("graph_path_ids"))


def _is_applicable_finding_row(row: dict[str, Any]) -> bool:
    applicability_status = str(row.get("applicability_status") or "")
    if applicability_status:
        return applicability_status != "not_applicable"
    return str(row.get("status") or "") != "not_applicable"


def _path_classifications(
    *,
    document_role: str,
    applicability_status: str,
    basis_type: str,
    supporting_source_record_ids: list[str],
    human_adjudication_refs: list[Any],
) -> list[str]:
    classifications: list[str] = []
    if _is_superseded_basis(basis_type):
        classifications.append("superseded")
    elif applicability_status == "not_applicable":
        classifications.append("out_of_scope")
    elif document_role in INTERPRETIVE_DOCUMENT_ROLES:
        classifications.append("interpretive")
    else:
        classifications.append("controlling")
    if supporting_source_record_ids:
        classifications.append("supporting")
    if human_adjudication_refs:
        classifications.append("adjudicated")
    return sorted(set(classifications), key=classifications.index)


def _is_superseded_basis(basis_type: str) -> bool:
    normalized = basis_type.lower()
    return any(marker in normalized for marker in SUPERSEDED_BASIS_MARKERS)


def _finding_source_record_ids(finding: dict[str, Any]) -> list[str]:
    source_record_ids = set(
        _strings(
            [
                finding.get("authority_source_record_id"),
                (finding.get("source_library_evidence") or {}).get("source_record_id"),
            ]
        )
    )
    for link in finding.get("source_claim_links", []):
        if isinstance(link, dict) and link.get("source_record_id"):
            source_record_ids.add(str(link["source_record_id"]))
    source_record_ids.update(_strings(finding.get("supporting_source_record_ids")))
    return sorted(source_record_ids)


def _unresolved_issue_refs(finding: dict[str, Any]) -> list[str]:
    refs = [str(item) for item in finding.get("limitations", []) if str(item).strip()]
    refs.extend(_adjudication_refs(finding.get("human_adjudication_refs")))
    return sorted(dict.fromkeys(refs))


def _decision_unresolved_issue_refs(row: dict[str, Any]) -> list[str]:
    refs = []
    refs.extend(str(item) for item in row.get("missing_evidence", []) if str(item).strip())
    refs.extend(
        str(item) for item in row.get("contradiction_notes", []) if str(item).strip()
    )
    refs.extend(_adjudication_refs(row.get("human_adjudication_refs")))
    return sorted(dict.fromkeys(refs))


def _risk_categories_for_row(
    *,
    row: dict[str, Any],
    risk_flags: list[dict[str, Any]],
) -> list[str]:
    rule_id = str(row.get("rule_id") or "")
    candidate_authority_id = str(row.get("candidate_authority_id") or "")
    categories = []
    for flag in risk_flags:
        if rule_id and rule_id in _strings(flag.get("rule_ids")):
            categories.append(str(flag.get("risk_category") or ""))
            continue
        if candidate_authority_id and candidate_authority_id in _strings(
            flag.get("candidate_authority_ids")
        ):
            categories.append(str(flag.get("risk_category") or ""))
    return sorted({value for value in categories if value})


def _adjudication_refs(value: Any) -> list[str]:
    refs = []
    for item in value or []:
        if isinstance(item, dict):
            identifier = (
                item.get("adjudication_id")
                or item.get("source_type")
                or item.get("source_id")
                or item.get("artifact_ref")
            )
            if identifier:
                refs.append(str(identifier))
        elif str(item).strip():
            refs.append(str(item))
    return sorted(dict.fromkeys(refs))


def _strings(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, int, float)):
        text = str(values).strip()
        return [text] if text else []
    results = []
    for value in values:
        text = str(value).strip()
        if text:
            results.append(text)
    return results


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
