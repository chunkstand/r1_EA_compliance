from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import re

from .project_sow_package_common import _is_empty
from .project_sow_package_common import _list
from .project_sow_package_common import _normalize_token
from .project_sow_package_common import _resource_area_ids
from .project_sow_package_common import _searchable_text
from .project_sow_package_common import _slug
from .project_sow_package_common import _strings
from .project_sow_package_common import _title_from_id
from .project_sow_package_common import _truncate

def _resource_scopes(resource_config: dict[str, Any]) -> list[dict[str, Any]]:
    scopes = resource_config.get("resource_scopes")
    if not isinstance(scopes, list):
        return []
    return [scope for scope in scopes if isinstance(scope, dict)]


def _authority_family_ids(authority_inventory: dict[str, Any]) -> set[str]:
    family_ids = {
        str(family.get("family_id"))
        for family in _list(authority_inventory.get("authority_families"))
        if isinstance(family, dict) and family.get("family_id")
    }
    for family in _list(authority_inventory.get("authority_families")):
        if isinstance(family, dict) and family.get("authority_family_id"):
            family_ids.add(str(family["authority_family_id"]))
    return family_ids


def _indicator_keys(intake: dict[str, Any]) -> set[str]:
    indicators = intake.get("resource_indicators")
    keys = set()
    if isinstance(indicators, dict):
        keys.update(_normalize_token(str(key)) for key in indicators)
    for element in _proposed_action_elements(intake):
        keys.update(
            _normalize_token(value)
            for value in _strings(element.get("resource_indicator_keys"))
        )
    return keys


def _resource_area_catalog(intake: dict[str, Any]) -> dict[str, dict[str, Any]]:
    catalog: dict[str, dict[str, Any]] = {}
    for area in _list(intake.get("resource_analysis_expectations")):
        if isinstance(area, dict) and area.get("resource_area_id"):
            area_id = _normalize_token(str(area["resource_area_id"]))
            catalog[area_id] = {**area, "resource_area_id": area_id}
    for element in _proposed_action_elements(intake):
        for area_id in _resource_area_ids(element.get("resource_area_ids")):
            catalog.setdefault(
                area_id,
                {
                    "resource_area_id": area_id,
                    "resource_area_name": _title_from_id(area_id),
                },
            )
    return catalog


def _expected_resource_area_ids(intake: dict[str, Any]) -> set[str]:
    area_ids = _resource_area_ids(intake.get("expected_resource_area_ids"))
    area_ids.update(_resource_area_catalog(intake))
    for element in _proposed_action_elements(intake):
        area_ids.update(_resource_area_ids(element.get("resource_area_ids")))
    return area_ids


def _covered_resource_area_ids(scopes: list[dict[str, Any]]) -> set[str]:
    return {
        area_id
        for scope in scopes
        for area_id in _resource_area_ids(scope.get("covered_resource_area_ids"))
    }


def _observed_report_resource_area_ids(intake: dict[str, Any]) -> set[str]:
    return {
        area_id
        for report in _observed_specialist_reports(intake)
        for area_id in _resource_area_ids(report.get("resource_area_ids"))
    }


def _draft_project_sow_intake(
    *,
    proposed_action_text: str,
    proposed_action_path: Path,
    draft_rules: dict[str, Any],
    project_id: str | None,
    project_name: str | None,
    forest: str | None,
    districts: list[str] | None,
    project_type: str,
    nepa_level: str,
    source_title: str | None,
) -> dict[str, Any]:
    source_title = source_title or proposed_action_path.name
    inferred_project_name = project_name or _infer_project_name(proposed_action_text)
    selected_project_id = _slug(project_id or inferred_project_name)
    selected_project_type = _normalize_token(project_type or "land_exchange") or "land_exchange"
    selected_districts = [district for district in districts or [] if district.strip()]
    if not selected_districts:
        selected_districts = ["review_needed"]

    federal_actions, federal_action_flags = _draft_federal_land_actions(
        proposed_action_text=proposed_action_text,
        draft_rules=draft_rules,
        project_type=selected_project_type,
    )
    action_elements, resource_candidates, element_flags = _draft_action_elements(
        proposed_action_text=proposed_action_text,
        source_title=source_title,
        draft_rules=draft_rules,
        project_type=selected_project_type,
    )
    resource_expectations = _draft_resource_expectations(resource_candidates)
    resource_indicators = _draft_resource_indicators(resource_candidates)
    uncertainty_flags = sorted(
        {
            "draft_requires_reviewer_confirmation",
            "resource_area_candidates_require_review",
            *federal_action_flags,
            *element_flags,
        }
    )
    return {
        "consultation_indicators": _draft_consultation_indicators(resource_candidates),
        "districts": selected_districts,
        "draft_metadata": {
            "candidate_federal_land_action_types": [
                str(action.get("action_type")) for action in federal_actions
            ],
            "candidate_resource_area_ids": sorted(resource_candidates),
            "draft_notice": (
                "Deterministic draft for reviewer intake authoring. It does not decide "
                "authority applicability, compliance, or final agency action."
            ),
            "review_status": "unreviewed",
            "reviewer_confirmation_required": True,
            "schema_version": "project-sow-intake-draft-v0",
            "source_text_sha256": hashlib.sha256(
                proposed_action_text.encode("utf-8")
            ).hexdigest(),
            "source_text_path": str(proposed_action_path),
            "uncertainty_flags": uncertainty_flags,
        },
        "federal_land_actions": federal_actions,
        "forest": forest or "review_needed",
        "forest_plan_profile": "review_needed",
        "geography": [],
        "management_context": [],
        "nepa_level": nepa_level or "environmental_assessment",
        "observed_specialist_reports": [],
        "project_id": selected_project_id,
        "project_name": inferred_project_name,
        "project_type": selected_project_type,
        "proponent": "review_needed",
        "proposed_action_elements": action_elements,
        "proposed_action_summary": _proposed_action_summary_from_text(proposed_action_text),
        "resource_analysis_expectations": resource_expectations,
        "resource_indicators": resource_indicators,
        "schema_version": "project-sow-intake-v0",
    }


def _draft_federal_land_actions(
    *,
    proposed_action_text: str,
    draft_rules: dict[str, Any],
    project_type: str,
) -> tuple[list[dict[str, str]], list[str]]:
    text = _searchable_text(proposed_action_text)
    actions: list[dict[str, str]] = []
    flags: list[str] = []
    for rule in _list(draft_rules.get("federal_land_action_rules")):
        if not isinstance(rule, dict):
            continue
        terms = _strings(rule.get("trigger_terms"))
        matched_terms = _matched_terms(text, terms)
        if not matched_terms:
            continue
        action_type = str(rule.get("action_type") or "review_needed")
        actions.append(
            {
                "action_type": action_type,
                "description": (
                    f"Draft candidate {action_type} action matched from proposed-action "
                    f"text terms: {', '.join(matched_terms)}. Reviewer must confirm."
                ),
            }
        )
    if not actions:
        flags.append("federal_land_actions_need_review")
        actions.append(
            {
                "action_type": "review_needed",
                "description": (
                    "Reviewer must identify the federal land disposal, acquisition, "
                    "reservation, or other land action before package generation."
                ),
            }
        )
    if project_type == "land_exchange" and not {
        str(action.get("action_type")) for action in actions
    }.intersection({"dispose", "acquire"}):
        flags.append("land_exchange_action_types_uncertain")
    return actions, flags


def _draft_action_elements(
    *,
    proposed_action_text: str,
    source_title: str,
    draft_rules: dict[str, Any],
    project_type: str,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], list[str]]:
    passages = _candidate_action_passages(proposed_action_text)
    resource_candidates: dict[str, dict[str, Any]] = {}
    elements: list[dict[str, Any]] = []
    flags: list[str] = []
    for index, passage in enumerate(passages, start=1):
        matched_resources = _draft_resource_candidates(
            text=passage,
            draft_rules=draft_rules,
            project_type=project_type,
        )
        if not matched_resources:
            continue
        for area_id, candidate in matched_resources.items():
            existing = resource_candidates.setdefault(area_id, candidate)
            existing.setdefault("matched_terms", [])
            existing["matched_terms"] = sorted(
                set(_strings(existing.get("matched_terms")) + _strings(candidate.get("matched_terms")))
            )
        element_id = f"draft_action_element_{index:02d}"
        elements.append(
            {
                "action_element_id": element_id,
                "description": _truncate(passage, 300),
                "draft_status": "candidate_reviewer_confirmation_required",
                "evidence_refs": [
                    {
                        "citation_label": f"Draft proposed action paragraph {index}",
                        "evidence_ref_id": f"draft-proposed-action-paragraph-{index:02d}",
                        "locator": f"paragraph {index}",
                        "source_record_id": "DRAFT-PROPOSED-ACTION",
                        "summary": _truncate(passage, 240),
                        "title": source_title,
                    }
                ],
                "resource_area_ids": sorted(matched_resources),
                "resource_indicator_keys": sorted(
                    {
                        str(candidate.get("indicator_key"))
                        for candidate in matched_resources.values()
                        if candidate.get("indicator_key")
                    }
                ),
            }
        )
    if not elements:
        flags.append("resource_area_candidates_need_review")
        fallback_resources = _draft_resource_candidates(
            text="land exchange",
            draft_rules=draft_rules,
            project_type=project_type,
        )
        resource_candidates.update(fallback_resources)
        elements.append(
            {
                "action_element_id": "draft_action_element_01",
                "description": (
                    "Reviewer must identify proposed-action elements and resource areas "
                    "from the source narrative."
                ),
                "draft_status": "candidate_reviewer_confirmation_required",
                "evidence_refs": [
                    {
                        "citation_label": "Draft proposed action narrative",
                        "evidence_ref_id": "draft-proposed-action-narrative",
                        "locator": "full proposed action text",
                        "source_record_id": "DRAFT-PROPOSED-ACTION",
                        "summary": _truncate(proposed_action_text, 240),
                        "title": source_title,
                    }
                ],
                "resource_area_ids": sorted(fallback_resources) or ["land_exchange_case"],
                "resource_indicator_keys": ["lands_realty"],
            }
        )
    return elements, resource_candidates, flags


def _draft_resource_candidates(
    *,
    text: str,
    draft_rules: dict[str, Any],
    project_type: str,
) -> dict[str, dict[str, Any]]:
    searchable_text = _searchable_text(text)
    candidates: dict[str, dict[str, Any]] = {}
    for rule in _list(draft_rules.get("resource_area_rules")):
        if not isinstance(rule, dict):
            continue
        area_id = _normalize_token(str(rule.get("resource_area_id") or ""))
        if not area_id:
            continue
        matched_terms = _matched_terms(searchable_text, _strings(rule.get("trigger_terms")))
        always_project_types = {
            _normalize_token(value) for value in _strings(rule.get("always_for_project_types"))
        }
        if not matched_terms and project_type not in always_project_types:
            continue
        candidates[area_id] = {
            "indicator_key": rule.get("indicator_key"),
            "matched_terms": matched_terms or [f"project_type:{project_type}"],
            "resource_area_id": area_id,
            "resource_area_name": rule.get("resource_area_name") or _title_from_id(area_id),
        }
    return candidates


def _draft_resource_expectations(
    resource_candidates: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "draft_status": "candidate_reviewer_confirmation_required",
            "proposed_action_basis": [
                "Draft candidate from proposed-action source text; reviewer must confirm.",
                "Matched terms: " + ", ".join(_strings(candidate.get("matched_terms"))),
            ],
            "resource_area_id": area_id,
            "resource_area_name": str(candidate.get("resource_area_name") or _title_from_id(area_id)),
        }
        for area_id, candidate in sorted(resource_candidates.items())
    ]


def _draft_resource_indicators(
    resource_candidates: dict[str, dict[str, Any]],
) -> dict[str, list[str]]:
    indicators: dict[str, set[str]] = {}
    for candidate in resource_candidates.values():
        indicator_key = str(candidate.get("indicator_key") or "").strip()
        if not indicator_key:
            continue
        indicators.setdefault(indicator_key, set()).update(
            _strings(candidate.get("matched_terms"))
        )
    return {key: sorted(values) for key, values in sorted(indicators.items())}


def _draft_consultation_indicators(
    resource_candidates: dict[str, dict[str, Any]],
) -> list[str]:
    indicators = []
    if "species_consultation" in resource_candidates:
        indicators.append("ESA Section 7 review needed")
    if "cultural_resources" in resource_candidates or "tribal_relations" in resource_candidates:
        indicators.append("NHPA/tribal consultation review needed")
    return indicators


def _candidate_action_passages(text: str) -> list[str]:
    passages = []
    for raw in re.split(r"\n\s*\n", text):
        passage = re.sub(r"^\s*[-*]\s*", "", raw.strip())
        passage = re.sub(r"\s+", " ", passage)
        if passage:
            passages.append(passage)
    return passages or [text.strip()]


def _matched_terms(text: str, terms: list[str]) -> list[str]:
    return sorted({term for term in terms if term.lower() in text})


def _infer_project_name(text: str) -> str:
    for line in text.splitlines():
        value = line.strip(" #\t")
        if value:
            return _truncate(value, 90)
    return "Draft Project SOW Intake"


def _proposed_action_summary_from_text(text: str) -> str:
    for passage in _candidate_action_passages(text):
        if passage:
            return _truncate(passage, 700)
    return "Draft proposed action summary requires reviewer completion."


def _draft_reviewer_confirmation_errors(intake: dict[str, Any]) -> list[str]:
    draft_metadata = intake.get("draft_metadata")
    if not isinstance(draft_metadata, dict):
        return []
    errors = []
    if draft_metadata.get("review_status") != "reviewer_confirmed":
        errors.append("draft_metadata.review_status must be reviewer_confirmed")
    if draft_metadata.get("reviewer_confirmation_required") is not False:
        errors.append("draft_metadata.reviewer_confirmation_required must be false")
    if _strings(draft_metadata.get("uncertainty_flags")):
        errors.append("draft_metadata.uncertainty_flags must be empty")
    return errors


def _intake_schema_shape_errors(intake: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    errors.extend(
        _required_object_field_errors(
            _list(intake.get("federal_land_actions")),
            path="federal_land_actions",
            required_fields=("action_type", "description"),
        )
    )
    for element_index, element in enumerate(_proposed_action_elements(intake)):
        element_path = f"proposed_action_elements[{element_index}]"
        errors.extend(
            _required_fields_for_record(
                element,
                path=element_path,
                required_fields=("action_element_id", "description"),
            )
        )
        if not _resource_area_ids(element.get("resource_area_ids")):
            errors.append(f"{element_path}.resource_area_ids: must contain at least one item")
        evidence_refs = _list(element.get("evidence_refs"))
        if not evidence_refs:
            errors.append(f"{element_path}.evidence_refs: must contain at least one item")
        errors.extend(_evidence_ref_shape_errors(evidence_refs, path=f"{element_path}.evidence_refs"))

    errors.extend(
        _required_object_field_errors(
            _list(intake.get("resource_analysis_expectations")),
            path="resource_analysis_expectations",
            required_fields=("resource_area_id", "resource_area_name"),
        )
    )
    for report_index, report in enumerate(_observed_specialist_reports_raw(intake)):
        report_path = f"observed_specialist_reports[{report_index}]"
        errors.extend(
            _required_fields_for_record(
                report,
                path=report_path,
                required_fields=("report_id", "resource_area_ids", "title"),
            )
        )
        if not _resource_area_ids(report.get("resource_area_ids")):
            errors.append(f"{report_path}.resource_area_ids: must contain at least one item")
        errors.extend(
            _evidence_ref_shape_errors(
                _list(report.get("evidence_refs")),
                path=f"{report_path}.evidence_refs",
            )
        )
    return errors


def _required_object_field_errors(
    records: list[Any],
    *,
    path: str,
    required_fields: tuple[str, ...],
) -> list[str]:
    errors: list[str] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"{path}[{index}]: must be an object")
            continue
        errors.extend(
            _required_fields_for_record(
                record,
                path=f"{path}[{index}]",
                required_fields=required_fields,
            )
        )
    return errors


def _evidence_ref_shape_errors(records: list[Any], *, path: str) -> list[str]:
    return _required_object_field_errors(
        records,
        path=path,
        required_fields=("evidence_ref_id", "locator", "source_record_id", "summary", "title"),
    )


def _required_fields_for_record(
    record: dict[str, Any],
    *,
    path: str,
    required_fields: tuple[str, ...],
) -> list[str]:
    return [
        f"{path}.{field}: required"
        for field in required_fields
        if _is_empty(record.get(field))
    ]


def _proposed_action_elements(intake: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        element
        for element in _list(intake.get("proposed_action_elements"))
        if isinstance(element, dict)
    ]


def _observed_specialist_reports_raw(intake: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        report
        for report in _list(intake.get("observed_specialist_reports"))
        if isinstance(report, dict)
    ]


def _observed_specialist_reports(intake: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for report in _observed_specialist_reports_raw(intake):
        records.append(
            {
                "document_role": report.get("document_role") or "specialist_report",
                "evidence_refs": _evidence_refs(report),
                "report_id": report.get("report_id"),
                "resource_area_ids": sorted(
                    _resource_area_ids(report.get("resource_area_ids"))
                ),
                "source_record_id": report.get("source_record_id"),
                "title": report.get("title"),
            }
        )
    return records


def _evidence_refs(record: dict[str, Any]) -> list[dict[str, Any]]:
    refs = []
    for evidence_ref in _list(record.get("evidence_refs")):
        if not isinstance(evidence_ref, dict):
            continue
        refs.append(
            {
                "citation_label": evidence_ref.get("citation_label"),
                "evidence_ref_id": evidence_ref.get("evidence_ref_id"),
                "locator": evidence_ref.get("locator"),
                "source_record_id": evidence_ref.get("source_record_id"),
                "summary": evidence_ref.get("summary"),
                "title": evidence_ref.get("title"),
            }
        )
    return refs
