from __future__ import annotations

from contextlib import closing
from pathlib import Path
import hashlib
import json
import sqlite3
import tempfile
import unittest

from usfs_r1_ea_sources.forest_plan_resolver import run_forest_plan_resolver
from usfs_r1_ea_sources.retrieval import build_retrieval_index


class ForestPlanResolverTests(unittest.TestCase):
    def test_other_configured_profiles_are_out_of_scope_for_selected_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profiles_path = Path(tmp) / "profiles.json"
            _write_resolver_profile_config(
                profiles_path,
                extra_profile_updates={
                    "forest_unit_id": "profile-two-nf",
                    "forest_unit_names": ["Profile Two National Forest"],
                    "ambiguous_unit_terms": ["Profile Two"],
                },
            )
            package_path = _write_package(
                Path(tmp),
                "The proposed action is on Profile Two National Forest.",
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=Path(tmp) / "source_library",
                review_id="other-configured-profile",
                profiles_path=profiles_path,
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "not_custer_gallatin")
            self.assertEqual(context["forest_unit"]["name"], "Profile Two National Forest")
            self.assertFalse(context["needs_reviewer_resolution"])
            self.assertTrue(result.summary["reviewer_ready"])

    def test_scope_resolution_uses_profile_unit_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            profiles_path = Path(tmp) / "profiles.json"
            _write_resolver_profile_config(
                profiles_path,
                forest_unit_names=["Profile Forest"],
            )
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The East Crazy project is on Profile Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="profile-name-driven",
                profiles_path=profiles_path,
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "custer_gallatin")
            self.assertEqual(context["forest_unit"]["name"], "Profile Forest")
            self.assertTrue(result.summary["reviewer_ready"])

    def test_readiness_uses_profile_required_roles(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(
                output_dir,
                missing_source_ids={"R1PLAN-custer-gallatin-nf-07"},
            )
            profiles_path = Path(tmp) / "profiles.json"
            _write_resolver_profile_config(
                profiles_path,
                required_roles=[
                    "planning_page",
                    "primary_land_management_plan",
                ],
            )
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="profile-required-roles",
                profiles_path=profiles_path,
            )

            readiness = result.summary["retrieval_readiness"]["required_source_records"]
            self.assertEqual(
                readiness["required_source_record_ids"],
                [
                    "R1PLAN-custer-gallatin-nf-01",
                    "R1PLAN-custer-gallatin-nf-02",
                ],
            )
            self.assertEqual(readiness["missing_source_record_ids"], [])
            self.assertTrue(result.summary["reviewer_ready"])

    def test_resolves_custer_gallatin_geographic_and_management_areas(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The East Crazy project is on the Custer Gallatin National Forest.",
                        "It is on the Bozeman Ranger District.",
                        "The EA identifies the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        "The action is within the Crazy Mountains Backcountry Area.",
                        "Trail work also crosses the Hyalite Recreation Emphasis Area.",
                        "Mapped Inventoried Roadless Area direction is reviewed.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="cg-positive",
            )

            self.assertTrue(result.context_path.exists())
            self.assertTrue(result.validation_path.exists())
            self.assertTrue(result.summary["reviewer_ready"])
            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "custer_gallatin")
            self.assertFalse(context["needs_reviewer_resolution"])
            self.assertEqual(
                [record["source_record_id"] for record in context["source_records"]],
                [
                    "R1PLAN-custer-gallatin-nf-01",
                    "R1PLAN-custer-gallatin-nf-02",
                    "R1PLAN-custer-gallatin-nf-03",
                    "R1PLAN-custer-gallatin-nf-04",
                    "R1PLAN-custer-gallatin-nf-05",
                    "R1PLAN-custer-gallatin-nf-06",
                    "R1PLAN-custer-gallatin-nf-07",
                ],
            )
            self.assertTrue(context["source_record_readiness"]["ready"])
            self.assertEqual(
                _names(context["geographic_areas"]),
                ["Bridger, Bangtail, and Crazy Mountains Geographic Area"],
            )
            self.assertEqual(
                _names(context["management_areas"]),
                ["Crazy Mountains Backcountry Area", "Hyalite Recreation Emphasis Area"],
            )
            self.assertEqual(_names(context["overlays"]), ["Inventoried Roadless Area"])
            self.assertEqual(_names(context["project_location_signals"]), ["Bozeman Ranger District"])
            for collection in (
                context["geographic_areas"],
                context["management_areas"],
                context["overlays"],
            ):
                for entry in collection:
                    self.assertEqual(entry["resolution_status"], "resolved")
                    self.assertTrue(entry["package_evidence"])
                    self.assertTrue(entry["plan_source_evidence"])
            self.assertIn(
                "R1PLAN-custer-gallatin-nf-05",
                {entry["source_record_id"] for entry in context["supporting_plan_evidence"]},
            )
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            self.assertTrue(validation["passed"])

    def test_allows_partial_custer_slice_when_required_records_are_indexed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir, catalog_source_count=190)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="cg-partial-required",
            )

            self.assertTrue(result.summary["reviewer_ready"])
            readiness = result.summary["retrieval_readiness"]
            self.assertTrue(readiness["passed"])
            self.assertTrue(readiness["required_source_records"]["ready"])
            self.assertTrue(
                _readiness_check(readiness, "retrieval_ready_for_forest_plan_resolver")["passed"]
            )

    def test_requires_all_custer_gallatin_source_records_in_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(
                output_dir,
                missing_source_ids={"R1PLAN-custer-gallatin-nf-07"},
            )
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                    ]
                ),
            )

            with self.assertRaisesRegex(ValueError, "required_custer_source_records_indexed"):
                run_forest_plan_resolver(
                    package_path=package_path,
                    output_dir=output_dir,
                    source_set_id=source_set_id,
                    review_id="cg-missing-source",
                )

    def test_feis_tiering_and_designated_areas_trigger_feis_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        "The EA tiers to the Final Environmental Impact Statement.",
                        "The effects section discusses designated areas and plan allocations.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="cg-feis",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            supporting_source_ids = {
                entry["source_record_id"] for entry in context["supporting_plan_evidence"]
            }
            self.assertIn("R1PLAN-custer-gallatin-nf-04", supporting_source_ids)
            self.assertIn("R1PLAN-custer-gallatin-nf-05", supporting_source_ids)
            for entry in context["supporting_plan_evidence"]:
                self.assertEqual(entry["resolution_status"], "resolved")
                self.assertTrue(entry["trigger_evidence"])
                self.assertTrue(entry["package_evidence"])
                self.assertTrue(entry["plan_source_evidence"])
            self.assertTrue(result.summary["reviewer_ready"])

    def test_broad_section_labels_and_lowercase_acronyms_do_not_trigger_supporting_routes(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        "The EA purpose and need and alternatives sections describe effects.",
                        "A fishing rod was found near the trail and ba and bo are field codes.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="cg-no-broad-trigger",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(context["supporting_plan_evidence"], [])

    def test_uppercase_acronyms_trigger_supporting_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        "The ROD and FEIS are incorporated by reference.",
                        "ESA consultation includes BA and BO records.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="cg-uppercase-triggers",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            supporting_source_ids = {
                entry["source_record_id"] for entry in context["supporting_plan_evidence"]
            }
            self.assertIn("R1PLAN-custer-gallatin-nf-03", supporting_source_ids)
            self.assertIn("R1PLAN-custer-gallatin-nf-04", supporting_source_ids)
            self.assertIn("R1PLAN-custer-gallatin-nf-06", supporting_source_ids)
            self.assertIn("R1PLAN-custer-gallatin-nf-07", supporting_source_ids)
            for entry in context["supporting_plan_evidence"]:
                self.assertTrue(entry["trigger_evidence"])
                self.assertTrue(entry["plan_source_evidence"])
            self.assertTrue(result.summary["reviewer_ready"])

    def test_esa_consultation_triggers_ba_and_bo_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        "The EA discusses Endangered Species Act Section 7 consultation.",
                        "The file includes a biological assessment and biological opinion.",
                        "The analysis references critical habitat, incidental take, and reinitiation.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="cg-esa",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            supporting_source_ids = {
                entry["source_record_id"] for entry in context["supporting_plan_evidence"]
            }
            self.assertIn("R1PLAN-custer-gallatin-nf-06", supporting_source_ids)
            self.assertIn("R1PLAN-custer-gallatin-nf-07", supporting_source_ids)
            self.assertTrue(result.summary["reviewer_ready"])

    def test_triggered_supporting_source_without_evidence_needs_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(
                output_dir,
                weak_supporting_source_ids={
                    "R1PLAN-custer-gallatin-nf-06",
                    "R1PLAN-custer-gallatin-nf-07",
                },
            )
            package_path = _write_package(
                Path(tmp),
                "\n".join(
                    [
                        "The proposed action is on the Custer Gallatin National Forest.",
                        "It is in the Bridger, Bangtail, and Crazy Mountains Geographic Area.",
                        "The EA discusses Endangered Species Act Section 7 consultation.",
                        "The file includes a biological assessment and biological opinion.",
                    ]
                ),
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="cg-weak-esa",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            self.assertTrue(context["needs_reviewer_resolution"])
            self.assertFalse(result.summary["reviewer_ready"])
            self.assertFalse(validation["passed"])
            self.assertFalse(
                _check(
                    validation,
                    "triggered_supporting_plan_evidence_has_source_evidence",
                )["passed"]
            )

    def test_custer_scope_without_area_needs_reviewer_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = _build_custer_source_library(output_dir)
            package_path = _write_package(
                Path(tmp),
                "The proposed action is on the Custer Gallatin National Forest.",
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=output_dir,
                source_set_id=source_set_id,
                review_id="cg-no-area",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "custer_gallatin")
            self.assertTrue(context["needs_reviewer_resolution"])
            self.assertEqual(context["geographic_areas"], [])
            self.assertEqual(context["management_areas"], [])
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            self.assertFalse(validation["passed"])
            self.assertFalse(_check(validation, "custer_scope_has_resolved_area")["passed"])

    def test_ambiguous_gallatin_package_is_not_guessed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_path = _write_package(
                Path(tmp),
                "The project near Gallatin includes road and trail maintenance.",
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=Path(tmp) / "source_library",
                review_id="ambiguous-gallatin",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "ambiguous")
            self.assertTrue(context["needs_reviewer_resolution"])
            self.assertEqual(context["source_records"], [])
            self.assertEqual(context["geographic_areas"], [])
            self.assertEqual(context["management_areas"], [])
            self.assertEqual(context["unresolved_mentions"][0]["reason"], "ambiguous_forest_unit")

    def test_non_custer_package_is_out_of_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package_path = _write_package(
                Path(tmp),
                "The project is on the Beaverhead-Deerlodge National Forest.",
            )

            result = run_forest_plan_resolver(
                package_path=package_path,
                output_dir=Path(tmp) / "source_library",
                review_id="non-custer",
            )

            context = json.loads(result.context_path.read_text(encoding="utf-8"))
            self.assertEqual(context["scope_status"], "not_custer_gallatin")
            self.assertFalse(context["needs_reviewer_resolution"])
            self.assertEqual(context["source_records"], [])
            self.assertTrue(result.summary["reviewer_ready"])


_CUSTER_TEST_SOURCES = (
    (
        "R1PLAN-custer-gallatin-nf-01",
        "Custer Gallatin land management plan page",
        (
            "The Custer Gallatin land management plan page lists the current plan, "
            "record of decision, final environmental impact statement volumes, "
            "biological assessment, and biological opinion."
        ),
    ),
    (
        "R1PLAN-custer-gallatin-nf-02",
        "2022 Custer Gallatin Land Management Plan PDF",
        (
            "The Bridger, Bangtail, and Crazy Mountains Geographic Area includes "
            "several plan land allocations. Plan Components-Crazy Mountains "
            "Backcountry Area (CMBCA) contain direction for backcountry use. "
            "The Hyalite Recreation Emphasis Area (HREA) has recreation setting "
            "direction. Inventoried Roadless Area direction applies where mapped."
        ),
    ),
    (
        "R1PLAN-custer-gallatin-nf-03",
        "Custer Gallatin Land Management Plan Record of Decision PDF",
        (
            "The record of decision identifies the selected alternative, explains "
            "the decision basis, records objection resolution, and documents plan approval."
        ),
    ),
    (
        "R1PLAN-custer-gallatin-nf-04",
        "Custer Gallatin Land Management Plan FEIS Volume 1 PDF",
        (
            "The final environmental impact statement volume 1 describes purpose and need, "
            "alternatives, affected environment, environmental consequences, cumulative "
            "effects, and plan consistency context."
        ),
    ),
    (
        "R1PLAN-custer-gallatin-nf-05",
        "Custer Gallatin Land Management Plan FEIS Volume 2 PDF",
        (
            "The final environmental impact statement volume 2 discusses designated areas, "
            "plan allocations, inventoried roadless areas, backcountry areas, recreation "
            "emphasis areas, and resource effects."
        ),
    ),
    (
        "R1PLAN-custer-gallatin-nf-06",
        "Custer Gallatin LMP Biological Assessment PDF",
        (
            "The biological assessment analyzes threatened, endangered, proposed, and "
            "candidate species, critical habitat, conservation measures, action area, "
            "and species effects."
        ),
    ),
    (
        "R1PLAN-custer-gallatin-nf-07",
        "Custer Gallatin LMP Biological Opinion PDF",
        (
            "The biological opinion documents Endangered Species Act section 7 consultation, "
            "effects determinations, incidental take, reinitiation, and terms and conditions."
        ),
    ),
)

_CUSTER_TEST_REVIEW_TOPICS = {
    "R1PLAN-custer-gallatin-nf-01": "Check current Custer Gallatin plan document set",
    "R1PLAN-custer-gallatin-nf-02": "Extract plan components by resource and geography",
    "R1PLAN-custer-gallatin-nf-03": "Check selected alternative and plan approval",
    "R1PLAN-custer-gallatin-nf-04": "Use FEIS Volume 1 for alternatives and effects context",
    "R1PLAN-custer-gallatin-nf-05": "Use FEIS Volume 2 for designated areas and allocations",
    "R1PLAN-custer-gallatin-nf-06": "Check plan-level species effects analysis",
    "R1PLAN-custer-gallatin-nf-07": "Check plan-level ESA consultation terms",
}

_WEAK_SOURCE_TEXT = (
    "This source chunk is intentionally generic for a negative resolver test. "
    "It has catalog provenance but no matching routed evidence terms."
)


def _build_custer_source_library(
    output_dir: Path,
    *,
    catalog_source_count: int | None = None,
    missing_source_ids: set[str] | None = None,
    weak_supporting_source_ids: set[str] | None = None,
) -> str:
    source_set_id = "source-set-test"
    missing_source_ids = missing_source_ids or set()
    weak_supporting_source_ids = weak_supporting_source_ids or set()
    chunks = [
        _chunk(
            source_set_id=source_set_id,
            source_record_id=source_record_id,
            title=title,
            document_role="forest_plan",
            authority_level="forest",
            citation_label=f"{source_record_id} | {title} | artifact abc123",
            text=(
                _WEAK_SOURCE_TEXT
                if source_record_id in weak_supporting_source_ids
                else text
            ),
        )
        for source_record_id, title, text in _CUSTER_TEST_SOURCES
        if source_record_id not in missing_source_ids
    ]
    source_record_ids = [chunk["source_record_id"] for chunk in chunks]
    _write_extraction_diagnostics(
        output_dir,
        source_set_id,
        source_record_ids,
        catalog_source_count=catalog_source_count,
    )
    _write_chunks(
        output_dir,
        source_set_id,
        chunks,
    )
    _write_catalog_sqlite(
        output_dir,
        {
            source_record_id: [topic]
            for source_record_id, topic in _CUSTER_TEST_REVIEW_TOPICS.items()
            if source_record_id in source_record_ids
        },
    )
    build_retrieval_index(
        output_dir=output_dir,
        source_set_id=source_set_id,
        allow_partial_extraction=(
            catalog_source_count is not None and catalog_source_count != len(source_record_ids)
        ),
    )
    return source_set_id


def _write_extraction_diagnostics(
    output_dir: Path,
    source_set_id: str,
    source_record_ids: list[str],
    *,
    catalog_source_count: int | None = None,
) -> None:
    diagnostics_dir = output_dir / "derived" / source_set_id / "diagnostics"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    (diagnostics_dir / "extraction_validation.json").write_text(
        json.dumps({"passed": True}, sort_keys=True),
        encoding="utf-8",
    )
    manifest_records = [
        {
            "source_set_id": source_set_id,
            "source_record_id": source_record_id,
            "status": "extracted",
        }
        for source_record_id in source_record_ids
    ]
    (diagnostics_dir / "extraction_manifest.jsonl").write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in manifest_records),
        encoding="utf-8",
    )
    summary = {
        "source_set_id": source_set_id,
        "catalog_source_count": catalog_source_count or len(source_record_ids),
        "selected_source_count": len(source_record_ids),
        "extracted_count": len(source_record_ids),
        "filters": {
            "id": source_record_ids if catalog_source_count else None,
            "parser": None,
            "limit": None,
        },
    }
    (diagnostics_dir / "summary.json").write_text(
        json.dumps(summary, sort_keys=True),
        encoding="utf-8",
    )
    catalog_dir = output_dir / "catalog"
    catalog_dir.mkdir(parents=True, exist_ok=True)
    (catalog_dir / "source_set_manifest.json").write_text(
        json.dumps({"source_set_id": source_set_id}, sort_keys=True),
        encoding="utf-8",
    )


def _write_chunks(output_dir: Path, source_set_id: str, chunks: list[dict]) -> Path:
    path = output_dir / "derived" / source_set_id / "chunks" / "chunks.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    for chunk in chunks:
        artifact_path = output_dir / chunk["artifact_path"]
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(f"artifact for {chunk['source_record_id']}", encoding="utf-8")
        text_path = output_dir / chunk["source_text_path"]
        text_path.parent.mkdir(parents=True, exist_ok=True)
        text_path.write_text(chunk["text"], encoding="utf-8")
    path.write_text(
        "".join(json.dumps(chunk, sort_keys=True) + "\n" for chunk in chunks),
        encoding="utf-8",
    )
    return path


def _write_catalog_sqlite(output_dir: Path, topics_by_source: dict[str, list[str]]) -> Path:
    path = output_dir / "catalog" / "review_sources.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as connection:
        connection.executescript(
            """
            CREATE TABLE review_topics (
              topic_id TEXT PRIMARY KEY,
              label TEXT NOT NULL
            );
            CREATE TABLE source_review_topics (
              source_record_id TEXT NOT NULL,
              topic_id TEXT NOT NULL,
              PRIMARY KEY (source_record_id, topic_id)
            );
            """
        )
        for source_record_id, topics in topics_by_source.items():
            for index, topic in enumerate(topics):
                topic_id = f"topic:{source_record_id}:{index}"
                connection.execute("INSERT INTO review_topics VALUES (?, ?)", (topic_id, topic))
                connection.execute(
                    "INSERT INTO source_review_topics VALUES (?, ?)",
                    (source_record_id, topic_id),
                )
        connection.commit()
    return path


def _chunk(
    *,
    source_set_id: str,
    source_record_id: str,
    title: str,
    document_role: str,
    authority_level: str,
    citation_label: str,
    text: str,
) -> dict:
    content_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    artifact_sha256 = hashlib.sha256(source_record_id.encode("utf-8")).hexdigest()
    return {
        "chunk_id": f"chunk:{source_record_id}",
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "chunk_index": 0,
        "title": title,
        "document_role": document_role,
        "authority_level": authority_level,
        "host": "example.test",
        "expected_parser": "html",
        "artifact_sha256": artifact_sha256,
        "artifact_path": f"artifacts/raw/{source_record_id}.html",
        "citation_label": citation_label,
        "original_url": f"https://example.test/{source_record_id}/original",
        "effective_url": f"https://example.test/{source_record_id}",
        "final_url": f"https://example.test/{source_record_id}",
        "parser_name": "unit_parser",
        "parser_version": "1.0",
        "extracted_at": "2026-04-30T00:00:00Z",
        "source_text_path": f"derived/{source_set_id}/extracted_text/{source_record_id}.txt",
        "char_start": 0,
        "char_end": len(text),
        "page": None,
        "section": None,
        "heading": title,
        "content_sha256": content_sha256,
        "text": text,
    }


def _write_package(directory: Path, text: str) -> Path:
    package_path = directory / "ea-package.txt"
    package_path.write_text(text, encoding="utf-8")
    return package_path


def _write_resolver_profile_config(
    path: Path,
    *,
    forest_unit_names: list[str] | None = None,
    required_roles: list[str] | None = None,
    extra_profile_updates: dict | None = None,
) -> None:
    payload = json.loads(Path("config/forest_plan_profiles.json").read_text(encoding="utf-8"))
    profile = payload["profiles"][0]
    if forest_unit_names is not None:
        profile["forest_unit_names"] = forest_unit_names
    if required_roles is not None:
        profile["required_readiness_source_roles"] = required_roles
    if extra_profile_updates is not None:
        extra_profile = dict(profile)
        extra_profile.update(extra_profile_updates)
        payload["profiles"].append(extra_profile)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _names(entries: list[dict]) -> list[str]:
    return [entry["name"] for entry in entries]


def _check(validation: dict, name: str) -> dict:
    return next(check for check in validation["checks"] if check["name"] == name)


def _readiness_check(readiness: dict, name: str) -> dict:
    return next(check for check in readiness["checks"] if check["name"] == name)


if __name__ == "__main__":
    unittest.main()
