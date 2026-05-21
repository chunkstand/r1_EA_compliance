from __future__ import annotations

from typing import Any

from .forest_plan_profiles import ForestPlanProfileCollection


PACKAGE_FACT_EXTRACTION_METHOD_VERSION = "deterministic-package-fact-extraction-v0"
LOCATION_NODE_TYPES = {"geography", "management_area", "overlay"}
COMMON_PACKAGE_FACT_TYPES = {
    "action",
    "agency",
    "nepa_level",
    "geography",
    "resource_topic",
    "consultation",
    "permit",
}
UNCERTAINTY_RECORD_STATUSES = {
    "requires_adjudication_before_applicability_decision",
    "missing_package_fact_type_recorded_for_later_applicability_context",
}


def _base_term_specs() -> list[dict[str, Any]]:
    return [
        _term_spec(
            "geography",
            "project_location",
            "project_area",
            "Project area",
            ["project area", "analysis area", "project location"],
        ),
        _term_spec(
            "action",
            "project_action_type",
            "land_exchange",
            "Land exchange",
            ["land exchange", "exchange of lands"],
        ),
        _term_spec(
            "authority",
            "statutory_authority",
            "flpma_section_206_land_exchange",
            "FLPMA Section 206 land-exchange authority",
            [
                "Federal Land Policy and Management Act",
                "FLPMA",
                "FLPMA Section 206",
                "FLPMA sec. 206",
                "FLPMA \u00a7 206",
                "Section 206 of FLPMA",
                "43 U.S.C. 1716",
                "43 U.S.C. \u00a7 1716",
                "43 USC 1716",
                "43 U.S.C. section 1716",
            ],
            source_metadata={
                "authority_family_id": "land_exchange_statutory_authorities",
                "rule_id": "flpma_section_206_land_exchange",
                "source_record_id": "R1EA-146",
                "statutory_citation": "43 U.S.C. 1716",
            },
        ),
        _term_spec(
            "authority",
            "statutory_authority",
            "land_exchange_statutory_authorities",
            "Land-exchange statutory authority family",
            [
                "16 U.S.C. 485",
                "16 U.S.C. \u00a7 485",
                "16 USC 485",
                "16 U.S.C. 486",
                "16 U.S.C. \u00a7 486",
                "16 USC 486",
                "16 U.S.C. 516",
                "16 U.S.C. \u00a7 516",
                "16 USC 516",
                "Federal Land Exchange Facilitation Act",
                "FLEFA",
                "exchange of lands in national forests",
                "exchange of lands in the public interest",
            ],
            source_metadata={
                "authority_family_id": "land_exchange_statutory_authorities",
                "rule_id": "land_exchange_statutory_authorities",
                "source_record_id": "R1EA-137",
            },
        ),
        _term_spec(
            "authority",
            "regulatory_authority",
            "land_exchange_regulatory_requirements",
            "36 CFR part 254 land-exchange regulatory authority",
            [
                "36 CFR part 254",
                "36 C.F.R. part 254",
                "36 CFR Part 254",
                "36 CFR 254",
                "36 C.F.R. 254",
                "36 CFR \u00a7 254",
                "36 C.F.R. \u00a7 254",
                "36 CFR 254.3",
                "36 CFR 254.4",
                "36 CFR 254.8",
                "36 CFR 254.9",
                "36 CFR 254.11",
                "36 CFR 254.12",
                "36 CFR 254.13",
                "36 CFR 254.14",
                "36 CFR 254.15",
                "36 CFR 254.16",
            ],
            source_metadata={
                "authority_family_id": "land_exchange_regulatory_requirements",
                "rule_id": "land_exchange_regulatory_requirements",
                "source_record_id": "R1EA-124",
            },
        ),
        _term_spec(
            "authority",
            "agency_policy",
            "land_exchange_fs_policy_and_project_references",
            "Forest Service land-exchange policy authority",
            [
                "FSM 5430",
                "FSM 5430 \u2014 Exchanges",
                "FSM 5430 - Exchanges",
                "FSH 5409.13",
                "FSH 5409.13 Ch. 30",
                "FSH 5409.13 Ch. 50",
                "FSH 5409.13 Ch. 60",
                "Forest Service exchange policy",
                "land exchange handbook",
                "Landownership Adjustment Handbook",
            ],
            source_metadata={
                "authority_family_id": "land_exchange_fs_policy_and_project_references",
                "rule_id": "land_exchange_fs_policy_and_project_references",
                "source_record_id": "R1EA-150",
            },
        ),
        _term_spec(
            "action",
            "project_action_type",
            "road_action",
            "Road action",
            ["road construction", "new road", "road realignment", "road decommissioning"],
        ),
        _term_spec(
            "action",
            "project_action_type",
            "trail_action",
            "Trail action",
            ["trail construction", "trail relocation", "trail reroute"],
        ),
        _term_spec(
            "agency",
            "lead_agency",
            "usfs",
            "USDA Forest Service",
            ["USDA Forest Service", "Forest Service", "United States Forest Service"],
        ),
        _term_spec(
            "agency",
            "lead_agency",
            "usda",
            "USDA",
            ["U.S. Department of Agriculture", "USDA"],
        ),
        _term_spec(
            "agency",
            "cooperating_agency",
            "cooperating_agency",
            "Cooperating agency",
            ["cooperating agency", "cooperating agencies"],
        ),
        _term_spec(
            "decision_posture",
            "decision_document",
            "decision_notice",
            "Decision Notice",
            ["decision notice", "draft decision notice"],
        ),
        _term_spec(
            "decision_posture",
            "finding",
            "fonsi",
            "Finding of No Significant Impact",
            ["finding of no significant impact", "FONSI"],
        ),
        _term_spec(
            "decision_posture",
            "scoping",
            "scoping",
            "Scoping",
            ["scoping notice", "scoping period"],
        ),
        _term_spec(
            "nepa_level",
            "analysis_level",
            "environmental_assessment",
            "Environmental Assessment",
            ["environmental assessment"],
        ),
        _term_spec(
            "nepa_level",
            "analysis_level",
            "environmental_impact_statement",
            "Environmental Impact Statement",
            ["environmental impact statement", "EIS"],
        ),
        _term_spec(
            "nepa_level",
            "analysis_level",
            "categorical_exclusion",
            "Categorical Exclusion",
            ["categorical exclusion"],
        ),
        _term_spec(
            "resource_topic",
            "resource",
            "land_exchange",
            "Land exchange",
            ["land exchange"],
        ),
        _term_spec(
            "resource_topic",
            "resource",
            "road",
            "Roads",
            ["road", "roads", "transportation system"],
        ),
        _term_spec(
            "resource_topic",
            "resource",
            "recreation",
            "Recreation",
            ["recreation", "recreational access"],
        ),
        _term_spec(
            "resource_topic",
            "resource",
            "minerals",
            "Minerals",
            ["minerals", "mineral", "mining"],
        ),
        _term_spec(
            "resource_topic",
            "resource",
            "wildlife",
            "Wildlife",
            ["wildlife", "habitat", "grizzly bear", "lynx"],
        ),
        _term_spec(
            "resource_topic",
            "resource",
            "water",
            "Water",
            ["water quality", "watershed", "stream", "wetland", "wetlands"],
        ),
        _term_spec(
            "resource_topic",
            "resource",
            "heritage",
            "Heritage",
            ["heritage", "cultural resource", "historic property", "archaeological"],
        ),
        _term_spec(
            "resource_topic",
            "resource",
            "botany",
            "Botany",
            ["botany", "botanical", "sensitive plants", "vegetation"],
        ),
        _term_spec(
            "resource_topic",
            "resource",
            "fire",
            "Fire and fuels",
            ["fire", "fuels", "wildfire"],
        ),
        _term_spec(
            "resource_topic",
            "resource",
            "scenery",
            "Scenery",
            ["scenery", "scenic integrity", "visual quality"],
        ),
        _term_spec(
            "resource_topic",
            "resource",
            "grazing",
            "Grazing",
            ["grazing", "range allotment", "allotment"],
        ),
        _term_spec(
            "resource_topic",
            "resource",
            "soils",
            "Soils",
            ["soil", "soils", "erosion"],
        ),
        _term_spec(
            "consultation",
            "esa",
            "esa",
            "Endangered Species Act consultation",
            ["Endangered Species Act", "ESA", "Section 7 consultation"],
        ),
        _term_spec(
            "consultation",
            "nhpa",
            "nhpa",
            "National Historic Preservation Act consultation",
            ["National Historic Preservation Act", "NHPA", "Section 106"],
        ),
        _term_spec(
            "consultation",
            "mbta",
            "mbta",
            "Migratory Bird Treaty Act",
            ["Migratory Bird Treaty Act", "MBTA"],
        ),
        _term_spec(
            "consultation",
            "tribal",
            "tribal_consultation",
            "Tribal consultation",
            ["tribal consultation", "tribes", "Tribal Historic Preservation Officer"],
        ),
        _term_spec(
            "permit",
            "clean_water_act",
            "clean_water_act",
            "Clean Water Act permit cue",
            ["Clean Water Act", "CWA", "Section 404", "404 permit"],
        ),
        _term_spec(
            "permit",
            "wetlands_floodplains",
            "wetlands",
            "Wetlands",
            ["wetlands", "wetland"],
        ),
        _term_spec(
            "permit",
            "wetlands_floodplains",
            "floodplains",
            "Floodplains",
            ["floodplains", "floodplain"],
        ),
        _term_spec(
            "permit",
            "roadless",
            "roadless",
            "Roadless area cue",
            ["roadless", "inventoried roadless area"],
        ),
        _term_spec(
            "permit",
            "wilderness",
            "wilderness",
            "Wilderness cue",
            ["wilderness", "wilderness study area"],
        ),
        _term_spec(
            "permit",
            "permit",
            "permit",
            "Permit cue",
            ["permit", "permits", "authorization"],
        ),
        _term_spec(
            "overlay",
            "designated_area",
            "designated_area",
            "Designated area",
            ["designated area", "special area", "Wild and Scenic River", "National Trail", "recommended wilderness"],
        ),
        _term_spec(
            "public_involvement",
            "public_involvement",
            "public_comment",
            "Public comment",
            ["public comment", "public comments", "comment period"],
        ),
        _term_spec(
            "public_involvement",
            "public_involvement",
            "scoping",
            "Scoping",
            ["public scoping", "scoping"],
        ),
        _term_spec(
            "alternative",
            "alternative",
            "no_action",
            "No Action Alternative",
            ["no action alternative", "no action"],
        ),
        _term_spec(
            "alternative",
            "alternative",
            "proposed_action",
            "Proposed Action",
            ["proposed action"],
        ),
        _term_spec(
            "alternative",
            "alternative",
            "alternatives",
            "Alternatives",
            ["alternatives considered", "range of alternatives", "alternative 1", "alternative 2"],
        ),
    ]


def _profile_term_specs(profiles: ForestPlanProfileCollection) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for profile in profiles.profiles:
        specs.append(
            _term_spec(
                "geography",
                "forest_unit",
                profile.forest_unit_id,
                profile.forest_unit_names[0],
                list(profile.forest_unit_names),
                source_metadata={"forest_unit_id": profile.forest_unit_id},
            )
        )
        for entry in profile.ranger_district_terms:
            specs.append(
                _term_spec(
                    "geography",
                    "ranger_district",
                    entry.entry_id,
                    entry.name,
                    list(entry.terms),
                    source_metadata={
                        "forest_unit_id": profile.forest_unit_id,
                        "profile_entry_id": entry.entry_id,
                    },
                )
            )
        for entry in profile.geographic_area_terms:
            specs.append(
                _term_spec(
                    "geography",
                    "geographic_area",
                    entry.entry_id,
                    entry.name,
                    list(entry.terms),
                    source_metadata={
                        "forest_unit_id": profile.forest_unit_id,
                        "profile_entry_id": entry.entry_id,
                    },
                )
            )
        for entry in profile.management_area_terms:
            specs.append(
                _term_spec(
                    "management_area",
                    "management_area",
                    entry.entry_id,
                    entry.name,
                    list(entry.terms),
                    source_metadata={
                        "forest_unit_id": profile.forest_unit_id,
                        "profile_entry_id": entry.entry_id,
                    },
                )
            )
        for entry in profile.overlay_terms:
            specs.append(
                _term_spec(
                    "overlay",
                    "overlay",
                    entry.entry_id,
                    entry.name,
                    list(entry.terms),
                    source_metadata={
                        "forest_unit_id": profile.forest_unit_id,
                        "profile_entry_id": entry.entry_id,
                    },
                )
            )
    for unit in profiles.known_other_forest_units:
        specs.append(
            _term_spec(
                "geography",
                "forest_unit",
                unit.forest_unit_id,
                unit.names[0],
                list(unit.names),
                source_metadata={"forest_unit_id": unit.forest_unit_id},
            )
        )
    return specs


def _term_spec(
    node_type: str,
    fact_subtype: str,
    normalized_value: str,
    label: str,
    terms: list[str],
    *,
    confidence_class: str = "observed",
    source_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "node_type": node_type,
        "fact_subtype": fact_subtype,
        "normalized_value": normalized_value,
        "label": label,
        "terms": tuple(_dedupe_strings(terms)),
        "confidence_class": confidence_class,
        "source_metadata": source_metadata or {},
    }


def _dedupe_strings(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        text = str(value or "").strip()
        key = text.casefold()
        if not text or key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result
