from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


FOREST_PLAN_COMPONENT_INVENTORY_SCHEMA_VERSION = "forest-plan-component-inventory-v0"


FOREST_PLAN_COMPONENT_FINDINGS_SCHEMA_VERSION = "forest-plan-component-findings-v0"


FOREST_PLAN_REVIEWER_RESOLUTION_QUEUE_SCHEMA_VERSION = (
    "forest-plan-reviewer-resolution-queue-v0"
)


FOREST_PLAN_COMPONENT_INVENTORY_COVERAGE_SCHEMA_VERSION = (
    "forest-plan-component-inventory-coverage-v0"
)


FOREST_PLAN_APPLICABLE_STANDARD_COVERAGE_SCHEMA_VERSION = (
    "forest-plan-applicable-standard-coverage-v0"
)


FOREST_PLAN_COMPONENT_INVENTORY_BUILD_COVERAGE_SCHEMA_VERSION = (
    "forest-plan-component-inventory-build-coverage-v0"
)


DEFAULT_FOREST_PLAN_COMPONENT_INVENTORY_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "forest_plan_component_inventory_seed.json"
)


VALID_COMPONENT_TYPES = {
    "desired_condition",
    "goal",
    "guideline",
    "monitoring",
    "objective",
    "plan_amendment",
    "standard",
    "suitability",
}


VALID_APPLICABILITY_STATUSES = {
    "applicable",
    "candidate",
    "not_applicable",
    "needs_reviewer_resolution",
}


VALID_FINDING_STATUSES = {
    "supported",
    "partial",
    "gap",
    "not_applicable",
    "needs_reviewer_resolution",
}


VALID_COMPLIANCE_STATUSES = {
    "complies",
    "potential_noncompliance",
    "insufficient_evidence",
    "not_applicable",
    "needs_reviewer_resolution",
    "not_evaluated_for_compliance",
}


SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")


COMPONENT_LABEL_PATTERN = (
    r"Desired Conditions?|Goals?|Guidelines?|Monitoring|Objectives?|Standards?|Suitability"
)


COMPONENT_NUMBER_RE = re.compile(r"^[0-9][A-Za-z0-9.]*$")


COMPONENT_LABEL_RE = re.compile(
    rf"\b(?P<label>{COMPONENT_LABEL_PATTERN})"
    r"\s*\((?P<code>[A-Za-z0-9-]+)\)\s*(?P<number>[0-9][A-Za-z0-9.]*)\s+"
    rf"(?P<text>.*?)(?=\b(?:{COMPONENT_LABEL_PATTERN})"
    r"\s*\([A-Za-z0-9-]+\)\s*[A-Za-z0-9.]+\s+|\bPlan Components[-\u2013\u2014]|\Z)",
    re.DOTALL,
)


COMPONENT_LABEL_CANDIDATE_RE = re.compile(
    rf"\b(?P<label>{COMPONENT_LABEL_PATTERN})"
    r"\s*\((?P<code>[A-Za-z0-9-]+)\)\s*(?P<number>[A-Za-z0-9.]+)\s+"
    rf"(?P<text>.*?)(?=\b(?:{COMPONENT_LABEL_PATTERN})"
    r"\s*\([A-Za-z0-9-]+\)\s*[A-Za-z0-9.]+\s+|\bPlan Components[-\u2013\u2014]|\Z)",
    re.DOTALL,
)


COMPONENT_CODE_ABBREVIATION_PATTERN = r"DC|GO|GDL|GL|MON|OBJ|STD|SUIT"


CODED_COMPONENT_RE = re.compile(
    rf"(?P<label>{COMPONENT_LABEL_PATTERN})\s+"
    r"(?P<code>(?:[A-Z0-9]{1,4})-(?P<abbr>"
    + COMPONENT_CODE_ABBREVIATION_PATTERN
    + r")(?:-[A-Z0-9]+)*)-(?P<number>[0-9]{1,2})[.:]\s+"
    r"(?P<text>.*?)(?=(?:(?:"
    + COMPONENT_LABEL_PATTERN
    + r")\s+)?(?:[A-Z0-9]{1,4})-(?:"
    + COMPONENT_CODE_ABBREVIATION_PATTERN
    + r")(?:-[A-Z0-9]+)*-[0-9]{1,2}[.:]\s+|\b(?:"
    + COMPONENT_LABEL_PATTERN
    + r")\s+[0-9][A-Za-z0-9.:-]*\s*:|\bPlan Components[-\u2013\u2014]|\Z)",
    re.DOTALL,
)


COLON_COMPONENT_RE = re.compile(
    rf"\b(?P<label>{COMPONENT_LABEL_PATTERN})\s+"
    r"(?:(?P<number_prefix>No\.)\s*)?(?P<number>[0-9][A-Za-z0-9.:-]*)\s*(?P<delimiter>[.:])\s+"
    r"(?P<text>.*?)(?=\b(?:"
    + COMPONENT_LABEL_PATTERN
    + r")\s+(?:No\.\s*)?[0-9][A-Za-z0-9.:-]*\s*[.:]|\bPlan Components[-\u2013\u2014]|\Z)",
    re.DOTALL,
)


SECTION_HEADING_RE = re.compile(
    r"Plan Components[-\u2013\u2014]\s*(?P<section>[^.]+)",
    re.IGNORECASE,
)


LEGACY_SECTION_HEADING_RE = re.compile(
    rf"(?P<section>[A-Z][A-Za-z/&,\-]+(?:\s+[A-Z][A-Za-z/&,\-]+){{0,6}})\s+"
    rf"(?:{COMPONENT_LABEL_PATTERN})\b",
)


LEADING_COMPONENT_LABEL_RE = re.compile(
    r"^(?:Desired Conditions?|Goals?|Guidelines?|Monitoring|Objectives?|Standards?|Suitability)"
    r"\s*\([A-Za-z0-9-]+\)\s*[0-9][A-Za-z0-9.]*\s+",
    re.IGNORECASE,
)


COMPONENT_CODE_NUMBER_RE = re.compile(
    r"^(?:Desired Conditions?|Goals?|Guidelines?|Monitoring|Objectives?|Standards?|Suitability)"
    r"\s*\((?P<code>[A-Za-z0-9-]+)\)\s*(?P<number>[0-9][A-Za-z0-9.]*)\b",
    re.IGNORECASE,
)


PLAN_CONSISTENCY_YES_NO = {"yes", "no"}


MODAL_BOUNDARY_RE = re.compile(
    r"\b(?:shall|must|should|may|will|would|is|are|includes?|contains?|allows?|prohibits?)\b",
    re.IGNORECASE,
)


TOKEN_RE = re.compile(r"[a-z][a-z0-9-]*")


TERM_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "component",
    "components",
    "for",
    "forest",
    "forestwide",
    "from",
    "in",
    "is",
    "may",
    "must",
    "new",
    "not",
    "of",
    "or",
    "project",
    "shall",
    "should",
    "that",
    "the",
    "to",
    "will",
    "with",
}


GENERIC_COMPONENT_TERMS = {
    *TERM_STOPWORDS,
    "action",
    "actions",
    "activities",
    "activity",
    "area",
    "areas",
    "authorized",
    "custer",
    "direction",
    "gallatin",
    "management",
    "national",
    "provide",
    "provides",
    "protect",
    "related",
    "resource",
    "resources",
}


LEGACY_SECTION_STOPWORDS = {
    "chapter",
    "direction",
    "forest",
    "forestwide",
    "goals",
    "goal",
    "guidelines",
    "guideline",
    "land",
    "management",
    "monitoring",
    "national",
    "objectives",
    "objective",
    "plan",
    "standards",
    "standard",
}


GENERIC_LEGACY_SECTION_CODES = {
    "NONE",
    "ONE",
    "TWO",
    "THREE",
    "FOUR",
    "FIVE",
    "SIX",
    "SEVEN",
    "EIGHT",
    "NINE",
    "TEN",
}


SECTION_FAMILY_KEYWORDS = {
    "hydrology": {
        "aquatic",
        "aquatics",
        "floodplain",
        "floodplains",
        "hydrology",
        "riparian",
        "river",
        "rivers",
        "stream",
        "streams",
        "water",
        "watershed",
        "watersheds",
        "wetland",
        "wetlands",
    },
    "wildlife": {
        "bat",
        "bear",
        "big game",
        "carnivore",
        "elk",
        "fisheries",
        "grizzly",
        "lynx",
        "prairie dog",
        "sage-grouse",
        "species",
        "wildlife habitat",
        "wildlife",
        "wolverine",
    },
    "botany": {
        "at-risk plant",
        "botany",
        "invasive",
        "plant",
        "plants",
        "vegetation",
        "whitebark",
        "weed",
    },
    "scenery": {
        "aesthetic",
        "aesthetics",
        "landscape character",
        "natural appearing",
        "scenery",
        "scenic",
        "visual",
        "viewshed",
    },
    "sustainability": {
        "carbon",
        "climate",
        "ecosystem services",
        "resilience",
        "resilient",
        "sustainability",
        "sustainable",
    },
    "recreation_access": {
        "access",
        "backcountry",
        "bicycle",
        "event",
        "events",
        "facility",
        "facilities",
        "mechanized",
        "motorized",
        "nonmotorized",
        "recreation",
        "road",
        "roadless",
        "roads",
        "trail",
        "trails",
        "transport",
    },
    "land_exchange": {
        "acquired",
        "acquisition",
        "conveyance",
        "estate",
        "exchange",
        "federal",
        "land exchange",
        "parcel",
        "parcels",
    },
    "minerals": {
        "geologic",
        "mineral",
        "minerals",
        "palladium",
        "platinum",
        "saleable",
    },
}

@dataclass(frozen=True)
class ForestPlanComponentEvaluationResult:
    findings_path: Path
    markdown_path: Path
    reviewer_resolution_queue_path: Path
    component_inventory_coverage_path: Path
    applicable_standard_coverage_path: Path
    summary: dict

@dataclass(frozen=True)
class ForestPlanComponentInventoryBuildResult:
    inventory_path: Path
    components_jsonl_path: Path
    coverage_path: Path
    summary_path: Path
    summary: dict

@dataclass(frozen=True)
class _ForestPlanInventoryProfileBuild:
    forest_unit_id: str
    plan_version: str
    primary_plan_source_record_id: str
    source_record_ids: tuple[str, ...]
    coverage: dict
