from __future__ import annotations

from pathlib import Path
import json
import re

from usfs_r1_ea_sources.forest_plan_profiles import ForestPlanProfile
from usfs_r1_ea_sources.forest_plan_profiles import load_forest_plan_profile
from usfs_r1_ea_sources.retrieval import build_retrieval_index

from tests.support.compliance_review_fixtures import (
    _chunk,
    _write_catalog_sqlite,
    _write_chunks,
    _write_extraction_diagnostics,
)


PROFILE_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "forest_plan_profiles.json"
TRACKING_PROFILE_IDS = (
    "bitterroot-nf",
    "dakota-prairie-grasslands",
    "helena-lewis-and-clark-nf",
    "idaho-panhandle-nfs",
    "kootenai-nf",
    "lolo-nf",
    "nez-perce-clearwater-nfs",
)
TRACKING_PROFILE_REQUIRED_FIXTURE_FAMILY_IDS = (
    "scope_positive",
    "scope_positive_with_ambiguous_context",
    "custer_hard_negative",
    "non_selected_non_custer_hard_negative",
)
CUSTER_HARD_NEGATIVE_TERMS = [
    "Custer Gallatin National Forest",
    "Crazy Mountains Backcountry Area",
    "2022 Land Management Plan",
]
NON_SELECTED_NON_CUSTER_HARD_NEGATIVE_TERMS = [
    "Beaverhead-Deerlodge National Forest",
    "Big Hole Landscape",
    "West Big Hole Management Area",
]
_TRACKING_COMPONENT_TEXT = (
    "Standard (TRK-STD) 01 Projects shall maintain aquatic habitat connectivity and protect "
    "riparian resources."
)


def tracking_profile(forest_unit_id: str) -> ForestPlanProfile:
    return load_forest_plan_profile(forest_unit_id, PROFILE_CONFIG_PATH)


def expected_scope_status(forest_unit_id: str) -> str:
    status = re.sub(r"[^A-Za-z0-9_.-]+", "-", forest_unit_id).strip("-")
    return status.replace("-", "_") or "forest_plan_profile"


def scope_positive_package_terms(forest_unit_id: str) -> list[str]:
    profile = tracking_profile(forest_unit_id)
    return [profile.forest_unit_names[0]]


def scope_positive_with_ambiguous_context_terms(forest_unit_id: str) -> list[str]:
    profile = tracking_profile(forest_unit_id)
    return [
        profile.forest_unit_names[0],
        profile.ambiguous_unit_terms[0],
    ]


def scope_positive_package_text(forest_unit_id: str) -> str:
    profile = tracking_profile(forest_unit_id)
    return "\n".join(
        [
            f"The proposed action is on the {profile.forest_unit_names[0]}.",
            "The environmental assessment references aquatic habitat connectivity and riparian resources.",
        ]
    )


def scope_positive_with_ambiguous_context_text(forest_unit_id: str) -> str:
    profile = tracking_profile(forest_unit_id)
    return "\n".join(
        [
            f"The proposed action is on the {profile.forest_unit_names[0]}.",
            (
                f"The {profile.ambiguous_unit_terms[0]} planning discussion is attached for "
                "background context."
            ),
            "The environmental assessment references aquatic habitat connectivity and riparian resources.",
        ]
    )


def custer_hard_negative_package_text() -> str:
    return (
        "The proposed action is on the Custer Gallatin National Forest in the Crazy Mountains "
        "Backcountry Area under the 2022 Land Management Plan."
    )


def non_selected_non_custer_hard_negative_package_text() -> str:
    return (
        "The proposed action is on the Beaverhead-Deerlodge National Forest in the Big Hole "
        "Landscape and the West Big Hole Management Area."
    )


def build_tracking_profile_source_library(
    output_dir: Path,
    *,
    forest_unit_id: str,
) -> tuple[str, Path]:
    profile = tracking_profile(forest_unit_id)
    source_set_id = f"source-set-{forest_unit_id}-test"
    chunks = []
    for role in profile.required_readiness_source_roles:
        source_record_id = profile.source_record_id_for_role(role)
        title = f"{profile.forest_unit_names[0]} {role.replace('_', ' ')}"
        if source_record_id == profile.active_plan_source_record_id:
            text = f"{profile.forest_unit_names[0]} land management plan. {_TRACKING_COMPONENT_TEXT}"
            document_role = "forest_plan"
        else:
            text = f"{profile.forest_unit_names[0]} {role.replace('_', ' ')} supporting source."
            document_role = "forest_plan_support"
        chunks.append(
            _chunk(
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                title=title,
                document_role=document_role,
                authority_level="forest",
                citation_label=f"{source_record_id} | {title} | artifact test",
                text=text,
            )
        )
    source_record_ids = [chunk["source_record_id"] for chunk in chunks]
    _write_extraction_diagnostics(output_dir, source_set_id, source_record_ids=source_record_ids)
    _write_chunks(output_dir, source_set_id, chunks)
    _write_catalog_sqlite(
        output_dir,
        {source_record_id: ["Forest plan review"] for source_record_id in source_record_ids},
    )
    build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
    inventory_path = output_dir / "test-fixtures" / f"{forest_unit_id}-tracking-component-seed.json"
    _write_tracking_component_inventory(
        inventory_path=inventory_path,
        profile=profile,
        source_set_id=source_set_id,
        plan_chunk=next(
            chunk for chunk in chunks if chunk["source_record_id"] == profile.active_plan_source_record_id
        ),
    )
    return source_set_id, inventory_path


def _write_tracking_component_inventory(
    *,
    inventory_path: Path,
    profile: ForestPlanProfile,
    source_set_id: str,
    plan_chunk: dict,
) -> None:
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "forest-plan-component-inventory-v0",
        "inventory_id": f"{profile.forest_unit_id}-tracking-components",
        "components": [
            {
                "component_id": f"{profile.active_plan_source_record_id}-TRK-STD-01",
                "forest_unit_id": profile.forest_unit_id,
                "plan_version": "test",
                "source_set_id": source_set_id,
                "source_record_id": profile.active_plan_source_record_id,
                "component_type": "standard",
                "section_id": "forestwide-direction",
                "section_heading": "Forestwide Direction",
                "page": 1,
                "citation_label": plan_chunk["citation_label"],
                "component_text": _TRACKING_COMPONENT_TEXT,
                "geographic_area_ids": [],
                "management_area_ids": [],
                "overlay_ids": [],
                "resource_topics": ["riparian"],
                "activity_tags": ["habitat", "connectivity"],
                "source_chunk_ids": [plan_chunk["chunk_id"]],
                "artifact_sha256": plan_chunk["artifact_sha256"],
                "content_sha256": plan_chunk["content_sha256"],
                "provenance": {
                    "entity": {"source_record_id": profile.active_plan_source_record_id},
                    "activity": {"source": plan_chunk["source_text_path"]},
                    "agent": {"name": "tracking-profile-test-builder"},
                },
                "package_evidence_terms": ["riparian habitat connectivity"],
            }
        ],
    }
    inventory_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def tracking_fixture_records() -> list[dict]:
    records = []
    for forest_unit_id in TRACKING_PROFILE_IDS:
        records.append(
            {
                "forest_unit_id": forest_unit_id,
                "fixture_family_id": "scope_positive",
                "fixture_id": f"region1-{forest_unit_id}-profile-positive-scope",
                "fixture_type": "positive",
                "expected_status": "selected_profile_scope_only",
                "package_terms": scope_positive_package_terms(forest_unit_id),
            }
        )
        records.append(
            {
                "forest_unit_id": forest_unit_id,
                "fixture_family_id": "scope_positive_with_ambiguous_context",
                "fixture_id": f"region1-{forest_unit_id}-profile-positive-ambiguous-context",
                "fixture_type": "positive",
                "expected_status": "selected_profile_scope_only",
                "package_terms": scope_positive_with_ambiguous_context_terms(forest_unit_id),
            }
        )
        records.append(
            {
                "forest_unit_id": forest_unit_id,
                "fixture_family_id": "custer_hard_negative",
                "fixture_id": f"region1-{forest_unit_id}-profile-hard-negative-custer-gallatin",
                "fixture_type": "hard_negative",
                "expected_status": f"not_applicable_to_{forest_unit_id.replace('-', '_')}",
                "package_terms": list(CUSTER_HARD_NEGATIVE_TERMS),
            }
        )
        records.append(
            {
                "forest_unit_id": forest_unit_id,
                "fixture_family_id": "non_selected_non_custer_hard_negative",
                "fixture_id": f"region1-{forest_unit_id}-profile-hard-negative-beaverhead",
                "fixture_type": "hard_negative",
                "expected_status": f"not_applicable_to_{forest_unit_id.replace('-', '_')}",
                "package_terms": list(NON_SELECTED_NON_CUSTER_HARD_NEGATIVE_TERMS),
            }
        )
    return records
