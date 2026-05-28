from __future__ import annotations

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
    report = {
        "schema_version": FOREST_PLAN_COMPONENT_FINDINGS_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "review_id": review_id,
        "source_set_id": source_set_id,
        "component_inventory_path": str(component_inventory_path),
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
) -> dict:
    source_set_matches = bool(source_set_id and component["source_set_id"] == source_set_id)
    context_match = _context_matches_component(context, component)
    package_search = _component_package_search(
        component=component,
        package_chunks=package_chunks,
        limit=package_top_k,
    )
    package_determination = _component_package_determination(
        component=component,
        package_chunks=package_chunks,
    )
    if package_determination and package_determination.get("component_applies") == "no":
        package_evidence = [package_determination]
    else:
        package_evidence = _merge_package_evidence(
            [package_determination] if package_determination else [],
            package_search["results"],
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
    return (
        component["component_type"] == "standard"
        and not component.get("geographic_area_ids")
        and not component.get("management_area_ids")
        and not component.get("overlay_ids")
        and package_determination is None
        and not component.get("resource_topics")
        and not component.get("activity_tags")
    )


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
