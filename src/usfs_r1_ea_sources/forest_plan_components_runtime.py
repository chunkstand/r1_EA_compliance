from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from .forest_plan_components_common import _finding_provenance, _utc_now
from .forest_plan_components_coverage import _applicable_standard_coverage, _component_inventory_coverage, _markdown_report, _summary
from .forest_plan_components_determination import _component_package_determination, _component_reference_key, _context_matches_component, _matched_context, _merge_package_evidence, _package_determination_basis, _reviewer_resolution_items_for_finding, _reviewer_resolution_queue
from .forest_plan_components_models import DEFAULT_FOREST_PLAN_COMPONENT_INVENTORY_PATH, FOREST_PLAN_COMPONENT_FINDINGS_SCHEMA_VERSION, FOREST_PLAN_COMPONENT_INVENTORY_SCHEMA_VERSION, ForestPlanComponentEvaluationResult, VALID_COMPONENT_TYPES
from .forest_plan_components_package_search import _component_package_search, _component_plan_source_evidence
from .forest_plan_components_validation import _reject_duplicate, _require_hex_string, _require_list, _require_object, _require_provenance, _require_safe_string, _require_string, _require_string_list, _validation_report, _write_json


def run_forest_plan_component_evaluation(
    *,
    review_id: str,
    review_dir: Path,
    context: dict,
    package_chunks: list[dict],
    component_inventory_path: Path,
    forest_unit_id: str,
    source_set_id: str | None,
    index_path: Path | None,
    package_top_k: int = 3,
    source_top_k: int = 3,
) -> ForestPlanComponentEvaluationResult:
    """Evaluate profile-selected forest-plan components against package evidence."""

    if package_top_k < 1:
        raise ValueError("package_top_k must be at least 1")
    if source_top_k < 1:
        raise ValueError("source_top_k must be at least 1")

    review_dir = Path(review_dir)
    component_inventory_path = Path(component_inventory_path)
    findings_path = review_dir / "forest_plan_component_findings.json"
    markdown_path = review_dir / "forest_plan_component_findings.md"
    queue_path = review_dir / "forest_plan_reviewer_resolution_queue.json"
    inventory_coverage_path = review_dir / "forest_plan_component_inventory_coverage.json"
    standard_coverage_path = review_dir / "forest_plan_applicable_standard_coverage.json"
    components = load_forest_plan_component_inventory(
        component_inventory_path,
        forest_unit_id=forest_unit_id,
    )
    component_applicability_decisions = _load_component_applicability_decisions(
        review_dir / "applicability" / "applicability_decisions.jsonl",
        source_set_id=source_set_id,
    )
    findings = [
        _component_finding(
            review_id=review_id,
            component=component,
            context=context,
            package_chunks=package_chunks,
            source_set_id=source_set_id,
            index_path=index_path,
            package_top_k=package_top_k,
            source_top_k=source_top_k,
            component_applicability_decisions=component_applicability_decisions,
        )
        for component in components
    ]
    queue = _reviewer_resolution_queue(
        review_id=review_id,
        source_set_id=source_set_id,
        findings=findings,
    )
    inventory_coverage = _component_inventory_coverage(
        review_id=review_id,
        source_set_id=source_set_id,
        component_inventory_path=component_inventory_path,
        components=components,
    )
    standard_coverage = _applicable_standard_coverage(
        review_id=review_id,
        source_set_id=source_set_id,
        components=components,
        findings=findings,
    )
    validation = _validation_report(
        source_set_id=source_set_id,
        components=components,
        findings=findings,
        queue=queue,
        inventory_coverage=inventory_coverage,
        standard_coverage=standard_coverage,
    )
    summary = _summary(
        review_id=review_id,
        source_set_id=source_set_id,
        component_inventory_path=component_inventory_path,
        findings_path=findings_path,
        markdown_path=markdown_path,
        queue_path=queue_path,
        inventory_coverage_path=inventory_coverage_path,
        standard_coverage_path=standard_coverage_path,
        components=components,
        findings=findings,
        queue=queue,
        validation=validation,
        inventory_coverage=inventory_coverage,
        standard_coverage=standard_coverage,
    )
    summary["applicability_decision_filter"] = _component_applicability_decision_summary(
        component_applicability_decisions
    )
    report = {
        "schema_version": FOREST_PLAN_COMPONENT_FINDINGS_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": review_id,
        "source_set_id": source_set_id,
        "component_inventory_path": str(component_inventory_path),
        "applicability_decision_filter": summary["applicability_decision_filter"],
        "summary": summary,
        "validation": validation,
        "component_inventory_coverage": inventory_coverage,
        "applicable_standard_coverage": standard_coverage,
        "components": components,
        "findings": findings,
    }

    review_dir.mkdir(parents=True, exist_ok=True)
    _write_json(findings_path, report)
    _write_json(queue_path, queue)
    _write_json(inventory_coverage_path, inventory_coverage)
    _write_json(standard_coverage_path, standard_coverage)
    markdown_path.write_text(_markdown_report(report, queue), encoding="utf-8")
    return ForestPlanComponentEvaluationResult(
        findings_path=findings_path,
        markdown_path=markdown_path,
        reviewer_resolution_queue_path=queue_path,
        component_inventory_coverage_path=inventory_coverage_path,
        applicable_standard_coverage_path=standard_coverage_path,
        summary=summary,
    )


def load_forest_plan_component_inventory(
    path: Path = DEFAULT_FOREST_PLAN_COMPONENT_INVENTORY_PATH,
    *,
    forest_unit_id: str | None = None,
) -> list[dict]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Forest-plan component inventory must be a JSON object.")
    schema_version = _require_string(payload, "schema_version", "component inventory")
    if schema_version != FOREST_PLAN_COMPONENT_INVENTORY_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported forest-plan component inventory schema_version: "
            f"{schema_version!r}; expected {FOREST_PLAN_COMPONENT_INVENTORY_SCHEMA_VERSION!r}"
        )
    _require_safe_string(payload, "inventory_id", "component inventory")
    components = _require_list(payload, "components", "component inventory")
    parsed = []
    for index, raw_component in enumerate(components):
        component = _parse_component(raw_component, f"components[{index}]")
        if forest_unit_id is not None and component["forest_unit_id"] != forest_unit_id:
            continue
        parsed.append(component)
    if not parsed:
        raise ValueError("Forest-plan component inventory contains no selected components.")
    _reject_duplicate(
        [component["component_id"] for component in parsed],
        "component_id",
        "component inventory",
    )
    return parsed


def _parse_component(raw_component: object, context: str) -> dict:
    component = _require_object(raw_component, context)
    component_id = _require_safe_string(component, "component_id", context)
    component_type = _require_string(component, "component_type", context)
    if component_type not in VALID_COMPONENT_TYPES:
        raise ValueError(f"{context}.component_type is unsupported: {component_type!r}.")
    page = component.get("page")
    if page is not None and (not isinstance(page, int) or page < 1):
        raise ValueError(f"{context}.page must be a positive integer or null.")
    parsed = {
        "component_id": component_id,
        "forest_unit_id": _require_safe_string(component, "forest_unit_id", context),
        "plan_version": _require_string(component, "plan_version", context),
        "source_set_id": _require_safe_string(component, "source_set_id", context),
        "source_record_id": _require_safe_string(component, "source_record_id", context),
        "component_type": component_type,
        "section_id": _require_safe_string(component, "section_id", context),
        "section_heading": _require_string(component, "section_heading", context),
        "page": page,
        "citation_label": _require_string(component, "citation_label", context),
        "component_text": _require_string(component, "component_text", context),
        "geographic_area_ids": _require_string_list(
            component,
            "geographic_area_ids",
            context,
            required=False,
        ),
        "management_area_ids": _require_string_list(
            component,
            "management_area_ids",
            context,
            required=False,
        ),
        "overlay_ids": _require_string_list(component, "overlay_ids", context, required=False),
        "resource_topics": _require_string_list(
            component,
            "resource_topics",
            context,
            required=False,
        ),
        "activity_tags": _require_string_list(
            component,
            "activity_tags",
            context,
            required=False,
        ),
        "source_chunk_ids": _require_string_list(component, "source_chunk_ids", context),
        "artifact_sha256": _require_hex_string(component, "artifact_sha256", context),
        "content_sha256": _require_hex_string(component, "content_sha256", context),
        "provenance": _require_provenance(component.get("provenance"), f"{context}.provenance"),
        "package_evidence_terms": _require_string_list(
            component,
            "package_evidence_terms",
            context,
            required=False,
        ),
    }
    if not (
        parsed["geographic_area_ids"]
        or parsed["management_area_ids"]
        or parsed["overlay_ids"]
        or parsed["resource_topics"]
        or parsed["activity_tags"]
    ):
        raise ValueError(
            f"{context} must include at least one context id, resource_topic, or activity_tag."
        )
    if not parsed["source_chunk_ids"]:
        raise ValueError(f"{context}.source_chunk_ids cannot be empty.")
    return parsed


def _component_finding(
    *,
    review_id: str,
    component: dict,
    context: dict,
    package_chunks: list[dict],
    source_set_id: str | None,
    index_path: Path | None,
    package_top_k: int,
    source_top_k: int,
    component_applicability_decisions: dict[str, dict] | None,
) -> dict:
    source_set_matches = bool(source_set_id and component["source_set_id"] == source_set_id)
    context_match = _context_matches_component(context, component)
    applicability_decision = (
        component_applicability_decisions.get(component["component_id"])
        if component_applicability_decisions is not None
        else None
    )
    decision_status = (
        str(applicability_decision.get("status") or "")
        if isinstance(applicability_decision, dict)
        else None
    )
    decision_filter_active = component_applicability_decisions is not None
    should_search_package = (
        decision_status == "applicable"
        or (
            not decision_filter_active
            and (context_match or bool(context.get("needs_reviewer_resolution")))
        )
    )
    if should_search_package:
        package_search = _component_package_search(
            component=component,
            package_chunks=package_chunks,
            limit=package_top_k,
        )
        package_determination = _component_package_determination(
            component=component,
            package_chunks=package_chunks,
        )
    else:
        package_search = _skipped_component_package_search(
            reason="component_context_not_matched",
        )
        package_determination = None
    if package_determination and package_determination.get("component_applies") == "no":
        package_evidence = [package_determination]
    else:
        package_evidence = _merge_package_evidence(
            [package_determination] if package_determination else [],
            package_search["results"],
            limit=package_top_k,
        )
    if (
        not package_evidence
        and decision_status == "applicable"
        and isinstance(applicability_decision, dict)
    ):
        package_evidence = _component_decision_package_evidence(
            applicability_decision,
            limit=package_top_k,
        )
    plan_source_evidence = []
    should_bind_plan_source = (
        context_match
        or component["component_type"] == "standard"
        or package_determination is not None
    )
    if source_set_matches and should_bind_plan_source and index_path is not None:
        plan_source_evidence = _component_plan_source_evidence(
            component=component,
            index_path=index_path,
            limit=source_top_k,
        )

    if not source_set_matches:
        applicability_status = "needs_reviewer_resolution"
        finding_status = "needs_reviewer_resolution"
        rationale = "The component inventory source set does not match the review source set."
    elif package_determination and package_determination.get("component_applies") == "no":
        applicability_status = "not_applicable"
        finding_status = "not_applicable"
        rationale = "The EA package explicitly marks this plan component not applicable."
    elif decision_filter_active and applicability_decision is None:
        applicability_status = "needs_reviewer_resolution"
        finding_status = "needs_reviewer_resolution"
        rationale = "The review-scoped applicability run did not decide this Forest Plan component."
    elif decision_filter_active and decision_status == "not_applicable":
        applicability_status = "not_applicable"
        finding_status = "not_applicable"
        rationale = _component_decision_rationale(
            applicability_decision,
            fallback=(
                "The review-scoped applicability decision marks this Forest Plan component "
                "not applicable."
            ),
        )
    elif decision_filter_active and decision_status not in {"applicable", "not_applicable"}:
        applicability_status = "needs_reviewer_resolution"
        finding_status = "needs_reviewer_resolution"
        rationale = _component_decision_rationale(
            applicability_decision,
            fallback=(
                "The review-scoped applicability decision did not reach a final applicable "
                "or not-applicable status for this Forest Plan component."
            ),
        )
    elif context.get("needs_reviewer_resolution"):
        applicability_status = "needs_reviewer_resolution"
        finding_status = "needs_reviewer_resolution"
        rationale = "The forest-plan context resolver requires reviewer resolution before component findings can be trusted."
    elif not context_match:
        applicability_status = "not_applicable"
        finding_status = "not_applicable"
        rationale = "The resolved package context does not match this component's geography, management area, or overlay."
    elif not plan_source_evidence:
        applicability_status = "needs_reviewer_resolution"
        finding_status = "needs_reviewer_resolution"
        rationale = "The component could not be verified against current source-library plan evidence."
    elif package_evidence:
        applicability_status = "applicable"
        finding_status = "supported"
        if package_determination:
            rationale = "The component is applicable and the EA package contains an explicit plan-consistency determination."
        else:
            rationale = "The component is applicable and the EA package contains matching evidence."
    elif _requires_reviewer_resolution_without_scope_binding(
        component=component,
        package_determination=package_determination,
    ):
        applicability_status = "needs_reviewer_resolution"
        finding_status = "needs_reviewer_resolution"
        rationale = (
            "The component inventory does not deterministically bind this standard to a "
            "resolved geography, management area, or overlay, so reviewer resolution is "
            "required before treating it as applicable."
        )
    else:
        applicability_status = "applicable"
        finding_status = "gap"
        rationale = "The component is applicable and source-library plan evidence exists, but matching EA package evidence was not found."

    compliance_status = _compliance_status(
        component=component,
        finding_status=finding_status,
    )
    reviewer_items = _reviewer_resolution_items_for_finding(
        review_id=review_id,
        component=component,
        finding_status=finding_status,
        applicability_status=applicability_status,
        rationale=rationale,
        source_set_id=source_set_id,
        source_set_matches=source_set_matches,
        plan_source_evidence=plan_source_evidence,
        package_evidence=package_evidence,
    )
    return {
        "finding_id": f"{component['component_id']}-finding",
        "review_id": review_id,
        "component_id": component["component_id"],
        "component_type": component["component_type"],
        "applicability_status": applicability_status,
        "finding_status": finding_status,
        "compliance_status": compliance_status,
        "applicability_basis": {
            "source_set_id": source_set_id,
            "component_source_set_id": component["source_set_id"],
            "source_set_matches": source_set_matches,
            "matched_context": _matched_context(context, component),
            "component_context": {
                "geographic_area_ids": component["geographic_area_ids"],
                "management_area_ids": component["management_area_ids"],
                "overlay_ids": component["overlay_ids"],
                "resource_topics": component["resource_topics"],
                "activity_tags": component["activity_tags"],
            },
            "package_query": package_search["query"],
            "package_evidence_terms": package_search["required_terms"],
            "component_key": _component_reference_key(component),
            "package_component_determination": (
                _package_determination_basis(package_determination)
                if package_determination
                else None
            ),
            "applicability_decision": _component_decision_basis(applicability_decision),
        },
        "plan_source_evidence": plan_source_evidence,
        "package_evidence": package_evidence,
        "rationale": rationale,
        "reviewer_resolution_items": reviewer_items,
        "provenance": _finding_provenance(
            review_id=review_id,
            component=component,
            source_set_id=source_set_id,
            finding_status=finding_status,
        ),
    }


def _requires_reviewer_resolution_without_scope_binding(
    *,
    component: dict,
    package_determination: dict | None,
) -> bool:
    has_topic_or_activity_binding = bool(
        component.get("resource_topics")
        or component.get("activity_tags")
        or component.get("package_evidence_terms")
    )
    return (
        component["component_type"] == "standard"
        and not component.get("geographic_area_ids")
        and not component.get("management_area_ids")
        and not component.get("overlay_ids")
        and not has_topic_or_activity_binding
        and package_determination is None
    )


def _load_component_applicability_decisions(
    path: Path,
    *,
    source_set_id: str | None,
) -> dict[str, dict] | None:
    if not path.exists():
        return None
    decisions: dict[str, dict] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid applicability decision JSONL at line {line_number}.") from exc
        if not isinstance(row, dict):
            continue
        if row.get("candidate_authority_type") != "forest_plan_component":
            continue
        if source_set_id and row.get("source_set_id") and row.get("source_set_id") != source_set_id:
            continue
        component_id = _component_id_from_applicability_decision(row)
        if component_id:
            decisions[component_id] = row
    return decisions or None


def _component_id_from_applicability_decision(decision: dict) -> str | None:
    rule_template = decision.get("rule_template")
    if isinstance(rule_template, dict):
        for field in ("component_id", "rule_id"):
            value = str(rule_template.get(field) or "").strip()
            if value:
                return value
    candidate_id = str(decision.get("candidate_authority_id") or "").strip()
    if candidate_id.startswith("forest-plan-component:") and ":" in candidate_id:
        return candidate_id.rsplit(":", 1)[-1]
    return None


def _component_applicability_decision_summary(
    decisions: dict[str, dict] | None,
) -> dict:
    if decisions is None:
        return {"active": False, "decision_count": 0, "status_counts": {}}
    return {
        "active": True,
        "decision_count": len(decisions),
        "status_counts": dict(Counter(str(row.get("status") or "") for row in decisions.values())),
    }


def _component_decision_basis(decision: dict | None) -> dict | None:
    if not isinstance(decision, dict):
        return None
    return {
        "candidate_authority_id": decision.get("candidate_authority_id"),
        "decision_id": decision.get("decision_id"),
        "status": decision.get("status"),
        "basis_type": decision.get("basis_type"),
        "rationale": _component_decision_rationale(decision, fallback=None),
    }


def _component_decision_rationale(decision: dict | None, *, fallback: str | None) -> str:
    if isinstance(decision, dict):
        for container_name in ("applicability_basis", "non_applicability_basis"):
            container = decision.get(container_name)
            if isinstance(container, dict):
                value = str(container.get("rationale") or "").strip()
                if value:
                    return value
        value = str(decision.get("rationale") or "").strip()
        if value:
            return value
    return fallback or ""


def _component_decision_package_evidence(decision: dict, *, limit: int) -> list[dict]:
    evidence = []
    for span in decision.get("package_evidence_spans") or []:
        if not isinstance(span, dict):
            continue
        evidence.append(
            {
                "rank": len(evidence) + 1,
                "score": 1.0,
                "source_record_id": span.get("source_record_id"),
                "title": span.get("title"),
                "citation_label": span.get("citation_label"),
                "review_section": span.get("review_section"),
                "determination_source": "applicability_decision",
                "applicability_decision_id": decision.get("decision_id"),
                "candidate_authority_id": decision.get("candidate_authority_id"),
                "chunk_id": span.get("source_chunk_id") or span.get("package_chunk_id"),
                "evidence_span": {
                    "text": span.get("text_excerpt") or span.get("text") or "",
                    "chunk_char_start": span.get("chunk_char_start"),
                    "chunk_char_end": span.get("chunk_char_end"),
                    "source_char_start": span.get("source_char_start"),
                    "source_char_end": span.get("source_char_end"),
                },
                "provenance": {
                    "artifact_sha256": span.get("artifact_sha256"),
                    "content_sha256": span.get("content_sha256"),
                    "source_record_id": span.get("source_record_id"),
                    "parser_name": "applicability_decision",
                    "parser_version": "applicability-decisions-v0",
                },
            }
        )
        if len(evidence) >= limit:
            break
    return evidence


def _skipped_component_package_search(*, reason: str) -> dict:
    return {
        "query": "",
        "required_terms": [],
        "section_families": [],
        "raw_hit_count": 0,
        "rejected_count": 0,
        "hit_count": 0,
        "results": [],
        "skipped": True,
        "skipped_reason": reason,
    }


def _compliance_status(*, component: dict, finding_status: str) -> str:
    if component["component_type"] != "standard":
        return "not_evaluated_for_compliance"
    if finding_status == "supported":
        return "complies"
    if finding_status == "not_applicable":
        return "not_applicable"
    if finding_status in {"gap", "partial"}:
        return "insufficient_evidence"
    return "needs_reviewer_resolution"
