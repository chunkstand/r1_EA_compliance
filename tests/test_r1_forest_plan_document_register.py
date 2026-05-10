from __future__ import annotations

from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit
import csv


ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "config" / "r1_forest_plan_document_register_draft.csv"


def _rows() -> list[dict[str, str]]:
    with REGISTER.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_r1_forest_plan_document_register_has_no_placeholder_gaps() -> None:
    rows = _rows()
    ids = [row["proposed_source_record_id"] for row in rows]
    unresolved = {
        "needs_direct_link_resolution",
        "needs_child_document_expansion",
        "missing_official_source_research",
    }

    assert len(rows) == 189
    assert len(ids) == len(set(ids))
    assert not any(row["draft_status"] in unresolved for row in rows)
    assert all(
        row["official_link"] and urlsplit(row["official_link"]).scheme in {"http", "https"}
        for row in rows
    )
    assert Counter(row["draft_status"] for row in rows) == {
        "catalog_confirmed": 28,
        "source_delta_required": 159,
        "official_source_gap_documented": 2,
    }
    assert [
        row["proposed_source_record_id"]
        for row in rows
        if row["draft_status"] == "official_source_gap_documented"
    ] == ["R1PLAN-kootenai-nf-18", "R1PLAN-nez-perce-clearwater-nfs-18"]


def test_r1_forest_plan_document_register_closes_bitterroot_and_kootenai_consultation_gaps() -> None:
    rows = {row["proposed_source_record_id"]: row for row in _rows()}

    assert rows["R1PLAN-bitterroot-nf-12"] == {
        "proposed_source_record_id": "R1PLAN-bitterroot-nf-12",
        "forest_unit_id": "bitterroot-nf",
        "forest_unit_name": "Bitterroot National Forest",
        "document_role": "biological_assessment",
        "document_title": (
            "Biological Assessment for Grizzly Bear Re-consultation for the Bitterroot "
            "Forest Plan, Travel Management Plan, and Forest Plan Elk Amendment"
        ),
        "official_link": "https://usfs-public.app.box.com/v/PinyonPublic/file/1195817909001",
        "existing_source_record_id": "",
        "readiness_tier": "core_required",
        "draft_status": "source_delta_required",
        "required_for": (
            "Plan-level ESA effects analysis and project-level consultation/tiering cues for "
            "grizzly bear."
        ),
        "notes": (
            "Official Forest Service Pinyon Public file from archived project 57302 EA "
            "Supporting folder; PDF text confirms Bitterroot Forest Plan grizzly-bear "
            "re-consultation content."
        ),
    }
    assert rows["R1PLAN-bitterroot-nf-13"]["document_role"] == "biological_opinion"
    assert rows["R1PLAN-bitterroot-nf-13"]["official_link"] == (
        "https://usfs-public.app.box.com/v/PinyonPublic/file/1195801545932"
    )
    assert "06E11000-2021-F-0020" in rows["R1PLAN-bitterroot-nf-13"]["notes"]

    assert rows["R1PLAN-kootenai-nf-14"]["document_title"].endswith("Chapter 1")
    assert rows["R1PLAN-kootenai-nf-14"]["official_link"] == "https://www.fs.usda.gov/media/55208"
    assert rows["R1PLAN-kootenai-nf-15"]["official_link"] == "https://www.fs.usda.gov/media/54974"
    assert rows["R1PLAN-kootenai-nf-16"]["official_link"] == "https://www.fs.usda.gov/media/55087"
    assert rows["R1PLAN-kootenai-nf-17"]["official_link"] == "https://www.fs.usda.gov/media/55037"
    assert rows["R1PLAN-kootenai-nf-18"]["document_role"] == "biological_assessment_gap"


def test_r1_forest_plan_document_register_corrects_nez_perce_clearwater_links() -> None:
    rows = {row["proposed_source_record_id"]: row for row in _rows()}

    assert rows["R1PLAN-nez-perce-clearwater-nfs-14"]["document_role"] == (
        "notice_of_opportunity_to_object"
    )
    assert rows["R1PLAN-nez-perce-clearwater-nfs-14"]["official_link"] == (
        "https://federalregister.gov/d/2023-26162"
    )
    assert "2025-00363" in rows["R1PLAN-nez-perce-clearwater-nfs-14"]["notes"]
    assert "2023-26162" in rows["R1PLAN-nez-perce-clearwater-nfs-14"]["notes"]

    assert rows["R1PLAN-nez-perce-clearwater-nfs-18"]["document_role"] == "project_record_gap"
    assert rows["R1PLAN-nez-perce-clearwater-nfs-18"]["readiness_tier"] == "gap_required"
    assert rows["R1PLAN-nez-perce-clearwater-nfs-18"]["draft_status"] == (
        "official_source_gap_documented"
    )
    assert rows["R1PLAN-nez-perce-clearwater-nfs-18"]["official_link"] == (
        "https://www.fs.usda.gov/r01/nezperce-clearwater/planning/2025-land-management-plan"
    )
    assert "usfs-public.box.com/s/a6tlve91fe1ma9u4hgfggd12oj8xmnwv" in (
        rows["R1PLAN-nez-perce-clearwater-nfs-18"]["notes"]
    )
