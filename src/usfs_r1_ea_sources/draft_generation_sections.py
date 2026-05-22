from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from .artifact_utils import _dict
from .artifact_utils import _dict_list
from .draft_generation_common import _check
from .draft_generation_common import _paragraph
from .draft_generation_common import _public_paragraph
from .draft_generation_common import _refusal
from .draft_generation_common import _safe_len
from .draft_generation_common import DraftGenerationContext
from .draft_generation_common import PROHIBITED_LEGAL_OUTPUT_TYPES
from .draft_generation_common import SUPPORTED_SECTION_TYPES
from .draft_generation_common import TRACEABILITY_FILENAME
from .draft_generation_traceability import _accepted_risk_for_rule
from .draft_generation_traceability import _bundles_for_confirmation
from .draft_generation_traceability import _trace_seed_from_accepted_risk
from .draft_generation_traceability import _trace_seed_from_bundles
from .draft_generation_traceability import _trace_seed_from_confirmation
from .draft_generation_traceability import _trace_seed_from_non_applicable_boundary
from .draft_generation_traceability import _trace_seed_from_pending_resolution


def _generate_sections(
    *,
    context: DraftGenerationContext,
    config: dict[str, Any],
    bundle_index: dict[str, Any],
    requested_output_ids: list[str] | None,
) -> dict[str, Any]:
    profiles = {
        str(profile.get("output_id") or ""): profile
        for profile in _dict_list(config.get("section_profiles"))
        if str(profile.get("output_id") or "").strip()
    }
    configured_ids = [str(item) for item in config.get("section_order", []) if str(item).strip()]
    requested = requested_output_ids or configured_ids
    sections: list[dict[str, Any]] = []
    paragraph_traces: list[dict[str, Any]] = []
    refusals: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []

    generators = {
        "citation_bearing_issue_summary": _issue_summary_section,
        "compliance_narrative": _compliance_narrative_section,
        "authority_coverage_appendix": _authority_coverage_appendix_section,
        "environmental_consequences": _environmental_consequences_section,
        "unresolved_issue_statement": _unresolved_issue_statements_section,
    }
    for output_id in requested:
        profile = _dict(profiles.get(output_id))
        if not profile:
            refusals.append(
                _refusal(
                    context=context,
                    output_id=output_id,
                    category="unsupported_legal_conclusion"
                    if output_id in PROHIBITED_LEGAL_OUTPUT_TYPES
                    else "insufficient_evidence",
                    message=f"Requested output '{output_id}' is not a governed draft-generation surface.",
                )
            )
            continue
        section_type = str(profile.get("section_type") or "")
        if section_type not in SUPPORTED_SECTION_TYPES or output_id in PROHIBITED_LEGAL_OUTPUT_TYPES:
            refusals.append(
                _refusal(
                    context=context,
                    output_id=output_id,
                    category="unsupported_legal_conclusion",
                    message=f"Requested section '{output_id}' is outside the governed draft boundary.",
                )
            )
            continue
        generated = generators[section_type](
            context=context,
            profile=profile,
            bundle_index=bundle_index,
        )
        checks.extend(generated["checks"])
        sections.append(generated["section"])
        paragraph_traces.extend(generated["paragraph_traces"])
        refusals.extend(generated["refusals"])
    return {
        "sections": sections,
        "paragraph_traces": paragraph_traces,
        "refusals": refusals,
        "checks": checks,
    }


def _issue_summary_section(
    *,
    context: DraftGenerationContext,
    profile: dict[str, Any],
    bundle_index: dict[str, Any],
) -> dict[str, Any]:
    bundles = _dict(bundle_index.get("bundles"))
    confirmations = _dict_list(bundle_index.get("implementation_confirmations"))
    accepted_risks = _dict_list(bundle_index.get("accepted_risks"))
    paragraphs = []
    checks: list[dict[str, Any]] = []

    summary_bundles = [
        bundle
        for rule_id, bundle in bundles.items()
        if rule_id.startswith("land_exchange_") or rule_id.startswith("flpma_")
    ]
    if not summary_bundles:
        summary_bundles = list(bundles.values())[:3]
    counts = {
        "applicable": len(bundles),
        "non_applicable": _safe_len(_dict_list(_dict(bundle_index.get("non_applicable_boundary")).get("rows"))),
        "confirmations": len(confirmations),
        "accepted_risks": len(accepted_risks),
    }
    paragraphs.append(
        _paragraph(
            section_id=str(profile["output_id"]),
            ordinal=1,
            text=(
                "This draft is limited to reviewed, citation-bearing evidence. "
                f"The current record carries {counts['applicable']} applicable authority findings, "
                f"{counts['non_applicable']} documented non-applicable authority rows, "
                f"{counts['confirmations']} implementation confirmations, and "
                f"{counts['accepted_risks']} accepted pending authority questions that must stay visible to reviewers."
            ),
            trace_seed=_trace_seed_from_bundles(context=context, bundles=summary_bundles),
            warning=True,
        )
    )
    if confirmations:
        confirmation = confirmations[0]
        related = _bundles_for_confirmation(confirmations=[confirmation], bundles=bundles)
        paragraphs.append(
            _paragraph(
                section_id=str(profile["output_id"]),
                ordinal=2,
                text=(
                    "Reviewer warning: implementation-dependent language must remain conditional. "
                    f"{confirmation.get('label') or 'Tracked implementation confirmation'} is still recorded as "
                    f"{confirmation.get('status') or 'requires_confirmation'}, so the draft can describe the planned control "
                    "but must not imply that the underlying instrument is already final."
                ),
                trace_seed=_trace_seed_from_confirmation(
                    context=context,
                    confirmation=confirmation,
                    bundles=related,
                ),
                warning=True,
            )
        )
    if accepted_risks:
        sample = accepted_risks[0]
        matched_bundle = bundles.get(str(sample.get("rule_id") or ""))
        paragraphs.append(
            _paragraph(
                section_id=str(profile["output_id"]),
                ordinal=3,
                text=(
                    "Reviewer warning: accepted pending authority items remain part of the defensibility boundary. "
                    f"The current packet still tracks {len(accepted_risks)} accepted pending items, including "
                    f"{sample.get('rule_id') or 'a pending authority question'}, and their rationale must stay visible "
                    "where the draft references that authority family."
                ),
                trace_seed=_trace_seed_from_accepted_risk(
                    context=context,
                    risk=sample,
                    bundle=matched_bundle,
                ),
                warning=True,
            )
        )
    section, section_checks = _section_payload(
        context=context,
        profile=profile,
        paragraphs=paragraphs,
        warnings=["reviewer_attention_required"] if paragraphs else [],
    )
    checks.extend(section_checks)
    return {
        "section": section,
        "paragraph_traces": [paragraph["_trace"] for paragraph in paragraphs],
        "refusals": [],
        "checks": checks,
    }


def _compliance_narrative_section(
    *,
    context: DraftGenerationContext,
    profile: dict[str, Any],
    bundle_index: dict[str, Any],
) -> dict[str, Any]:
    bundles = list(_dict(bundle_index.get("bundles")).values())
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for bundle in bundles:
        category = str(bundle["decision_support"].get("authority_category") or "authority")
        by_category[category].append(bundle)
    ordered_categories = sorted(by_category, key=lambda item: (-len(by_category[item]), item))
    paragraphs = [
        _paragraph(
            section_id=str(profile["output_id"]),
            ordinal=1,
            text=(
                "The compliance narrative below is limited to audited authority findings that carry both package evidence "
                "and supporting source-library authority. It supports reviewer drafting but does not state legal sufficiency "
                "or final agency approval."
            ),
            trace_seed=_trace_seed_from_bundles(context=context, bundles=bundles[:3]),
        )
    ]
    for ordinal, category in enumerate(ordered_categories, start=2):
        group = by_category[category]
        titles = [str(bundle["decision_support"].get("rule_title") or bundle["rule_id"]) for bundle in group[:3]]
        paragraphs.append(
            _paragraph(
                section_id=str(profile["output_id"]),
                ordinal=ordinal,
                text=(
                    f"The reviewed record contains {len(group)} applicable {category.replace('_', ' ')} findings. "
                    f"Representative governed authorities include {', '.join(titles)}. "
                    "Those findings remain anchored to paired package and source-library evidence and should be drafted as "
                    "review-supported narrative rather than as independent legal conclusions."
                ),
                trace_seed=_trace_seed_from_bundles(context=context, bundles=group),
            )
        )
    section, checks = _section_payload(
        context=context,
        profile=profile,
        paragraphs=paragraphs,
        warnings=[],
    )
    return {
        "section": section,
        "paragraph_traces": [paragraph["_trace"] for paragraph in paragraphs],
        "refusals": [],
        "checks": checks,
    }


def _authority_coverage_appendix_section(
    *,
    context: DraftGenerationContext,
    profile: dict[str, Any],
    bundle_index: dict[str, Any],
) -> dict[str, Any]:
    bundles = list(_dict(bundle_index.get("bundles")).values())
    by_category = Counter(
        str(bundle["decision_support"].get("authority_category") or "authority")
        for bundle in bundles
    )
    non_applicable_boundary = _dict(bundle_index.get("non_applicable_boundary"))
    review_packet = context.payload("review_packet_index")
    summary = _dict(review_packet.get("row_inventory_summary"))
    representative = bundles[:4]
    paragraphs = [
        _paragraph(
            section_id=str(profile["output_id"]),
            ordinal=1,
            text=(
                "Applicable authority coverage remains explicitly partitioned by category and traceable back to reviewed findings. "
                f"The current draft package covers {len(bundles)} applicable authorities across "
                + ", ".join(
                    f"{count} {category.replace('_', ' ')}"
                    for category, count in sorted(by_category.items())
                )
                + "."
            ),
            trace_seed=_trace_seed_from_bundles(context=context, bundles=representative),
        )
    ]
    paragraphs.append(
        _paragraph(
            section_id=str(profile["output_id"]),
            ordinal=2,
            text=(
                "The non-applicable authority boundary remains first class rather than implied by omission. "
                f"The appendix still carries {non_applicable_boundary.get('non_applicable_authority_count') or 0} non-applicable rows "
                f"with {non_applicable_boundary.get('coverage_certificate_count') or 0} search-coverage certificates, and those rows "
                "must stay outside ready compliance narrative unless reviewer adjudication changes the boundary."
            ),
            trace_seed=_trace_seed_from_non_applicable_boundary(
                context=context,
                boundary=non_applicable_boundary,
                representative_rows=_dict_list(non_applicable_boundary.get("rows"))[:3],
            ),
            warning=True,
        )
    )
    paragraphs.append(
        _paragraph(
            section_id=str(profile["output_id"]),
            ordinal=3,
            text=(
                "Forest-plan context remains visible in the appendix boundary. "
                f"The packet currently tracks {summary.get('forest_plan_component_row_count') or 0} applicable forest-plan component rows "
                f"and {summary.get('applicable_standard_count') or 0} applicable standards alongside the authority coverage ledger."
            ),
            trace_seed=_trace_seed_from_bundles(context=context, bundles=representative),
        )
    )
    section, checks = _section_payload(
        context=context,
        profile=profile,
        paragraphs=paragraphs,
        warnings=["non_applicable_boundary_visible"],
    )
    return {
        "section": section,
        "paragraph_traces": [paragraph["_trace"] for paragraph in paragraphs],
        "refusals": [],
        "checks": checks,
    }


def _environmental_consequences_section(
    *,
    context: DraftGenerationContext,
    profile: dict[str, Any],
    bundle_index: dict[str, Any],
) -> dict[str, Any]:
    bundle_map = _dict(bundle_index.get("bundles"))
    rule_ids = [str(value) for value in profile.get("rule_ids", []) if str(value).strip()]
    selected = [bundle_map[rule_id] for rule_id in rule_ids if rule_id in bundle_map]
    minimum_findings = int(profile.get("minimum_findings") or 1)
    if len(selected) < minimum_findings:
        refusal = _refusal(
            context=context,
            output_id=str(profile["output_id"]),
            category="insufficient_evidence",
            message=(
                f"Section '{profile.get('title')}' requires at least {minimum_findings} traced findings "
                f"but only found {len(selected)}."
            ),
        )
        section = _refused_section(profile=profile, refusal=refusal)
        return {"section": section, "paragraph_traces": [], "refusals": [refusal], "checks": []}
    paragraphs = []
    for ordinal, bundle in enumerate(selected, start=1):
        rule_title = str(bundle["decision_support"].get("rule_title") or bundle["rule_id"])
        rationale = str(bundle["decision_support"].get("rationale") or "The reviewed finding remains evidence-backed.")
        accepted_risk = _accepted_risk_for_rule(bundle_index=bundle_index, rule_id=bundle["rule_id"])
        warning_text = ""
        if accepted_risk is not None:
            warning_text = (
                " Reviewer warning: this topic remains in the accepted-pending ledger and should be drafted as a governed "
                "review question rather than as a closed legal conclusion."
            )
        paragraphs.append(
            _paragraph(
                section_id=str(profile["output_id"]),
                ordinal=ordinal,
                text=(
                    f"{rule_title} remains part of the reviewed environmental-consequences record. {rationale}"
                    f"{warning_text}"
                ),
                trace_seed=_trace_seed_from_bundles(context=context, bundles=[bundle]),
                warning=bool(warning_text),
            )
        )
    section, checks = _section_payload(
        context=context,
        profile=profile,
        paragraphs=paragraphs,
        warnings=["accepted_pending_environmental_issue"] if any(
            _accepted_risk_for_rule(bundle_index=bundle_index, rule_id=bundle["rule_id"]) is not None
            for bundle in selected
        ) else [],
    )
    return {
        "section": section,
        "paragraph_traces": [paragraph["_trace"] for paragraph in paragraphs],
        "refusals": [],
        "checks": checks,
    }


def _unresolved_issue_statements_section(
    *,
    context: DraftGenerationContext,
    profile: dict[str, Any],
    bundle_index: dict[str, Any],
) -> dict[str, Any]:
    bundle_map = _dict(bundle_index.get("bundles"))
    confirmations = _dict_list(bundle_index.get("implementation_confirmations"))
    accepted_risks = _dict_list(bundle_index.get("accepted_risks"))
    pending_paths = _dict_list(bundle_index.get("pending_resolution_paths"))
    reviewer_resolution_items = _dict_list(bundle_index.get("reviewer_resolution_items"))

    paragraphs = []
    ordinal = 1
    for confirmation in confirmations:
        if str(confirmation.get("status") or "") == "confirmed":
            continue
        related_bundles = _bundles_for_confirmation(confirmations=[confirmation], bundles=bundle_map)
        paragraphs.append(
            _paragraph(
                section_id=str(profile["output_id"]),
                ordinal=ordinal,
                text=(
                    "Reviewer warning: "
                    f"{confirmation.get('label') or 'Implementation confirmation'} is still "
                    f"{confirmation.get('status') or 'requires_confirmation'}. "
                    "Draft language may describe the planned control, but it must keep the confirmation boundary explicit."
                ),
                trace_seed=_trace_seed_from_confirmation(
                    context=context,
                    confirmation=confirmation,
                    bundles=related_bundles,
                ),
                warning=True,
            )
        )
        ordinal += 1
    for risk in accepted_risks:
        paragraphs.append(
            _paragraph(
                section_id=str(profile["output_id"]),
                ordinal=ordinal,
                text=(
                    "Reviewer warning: "
                    f"{risk.get('rule_id') or 'accepted pending authority item'} remains in the accepted V1 risk ledger. "
                    f"{risk.get('classification_rationale') or 'Reviewer adjudication is still required before the issue can be closed.'}"
                ),
                trace_seed=_trace_seed_from_accepted_risk(
                    context=context,
                    risk=risk,
                    bundle=bundle_map.get(str(risk.get("rule_id") or "")),
                ),
                warning=True,
            )
        )
        ordinal += 1
    for row in pending_paths + reviewer_resolution_items:
        paragraphs.append(
            _paragraph(
                section_id=str(profile["output_id"]),
                ordinal=ordinal,
                text=(
                    "Reviewer warning: unresolved authority review remains open. "
                    f"{row.get('explanation_summary') or row.get('rationale') or 'Pending resolution evidence must be adjudicated before the issue can be treated as closed.'}"
                ),
                trace_seed=_trace_seed_from_pending_resolution(context=context, row=row),
                warning=True,
            )
        )
        ordinal += 1
    if not paragraphs:
        paragraphs.append(
            _paragraph(
                section_id=str(profile["output_id"]),
                ordinal=1,
                text=(
                    "No unresolved reviewer warnings are currently tracked in the reviewed authority packet. "
                    "This absence does not remove the human-review boundary for the generated draft."
                ),
                trace_seed=_trace_seed_from_bundles(
                    context=context,
                    bundles=list(bundle_map.values())[:1],
                ),
            )
        )
    section, checks = _section_payload(
        context=context,
        profile=profile,
        paragraphs=paragraphs,
        warnings=["reviewer_warning_inserted"],
    )
    return {
        "section": section,
        "paragraph_traces": [paragraph["_trace"] for paragraph in paragraphs],
        "refusals": [],
        "checks": checks,
    }


def _section_payload(
    *,
    context: DraftGenerationContext,
    profile: dict[str, Any],
    paragraphs: list[dict[str, Any]],
    warnings: list[str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    section_checks = []
    readiness_status = "ready_with_reviewer_warnings" if warnings else "ready"
    section = {
        "section_id": str(profile.get("output_id") or ""),
        "section_type": str(profile.get("section_type") or ""),
        "title": str(profile.get("title") or ""),
        "readiness_status": readiness_status,
        "human_review_required": True,
        "legal_conclusion": False,
        "warnings": sorted(set(warnings)),
        "paragraphs": [_public_paragraph(paragraph) for paragraph in paragraphs],
        "supporting_authority_family_ids": sorted(
            {
                family_id
                for paragraph in paragraphs
                for family_id in paragraph["_trace"].get("authority_family_ids", [])
            }
        ),
        "supporting_rule_ids": sorted(
            {
                rule_id
                for paragraph in paragraphs
                for rule_id in paragraph["_trace"].get("rule_ids", [])
            }
        ),
        "traceability_path": str(context.review_dir / "draft_generation" / TRACEABILITY_FILENAME),
    }
    for paragraph in paragraphs:
        section_checks.append(
            _check(
                f"{section['section_id']}:{paragraph['paragraph_id']}:has_citations",
                bool(paragraph["citations"]),
                "missing_citation",
                {"paragraph_id": paragraph["paragraph_id"], "citations": paragraph["citations"]},
            )
        )
        section_checks.append(
            _check(
                f"{section['section_id']}:{paragraph['paragraph_id']}:human_boundary",
                "This generated draft" not in paragraph["text"],
                "human_boundary_missing",
                {"paragraph_id": paragraph["paragraph_id"]},
            )
        )
    return section, section_checks


def _refused_section(*, profile: dict[str, Any], refusal: dict[str, Any]) -> dict[str, Any]:
    return {
        "section_id": str(profile.get("output_id") or ""),
        "section_type": str(profile.get("section_type") or ""),
        "title": str(profile.get("title") or ""),
        "readiness_status": "refused",
        "human_review_required": True,
        "legal_conclusion": False,
        "warnings": ["generation_refused"],
        "paragraphs": [],
        "refusal_id": refusal["refusal_id"],
        "refusal_category": refusal["category"],
    }
