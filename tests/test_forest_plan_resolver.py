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
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            self.assertTrue(validation["passed"])

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


def _build_custer_source_library(output_dir: Path) -> str:
    source_set_id = "source-set-test"
    source_record_id = "R1PLAN-custer-gallatin-nf-02"
    _write_extraction_diagnostics(output_dir, source_set_id, [source_record_id])
    _write_chunks(
        output_dir,
        source_set_id,
        [
            _chunk(
                source_set_id=source_set_id,
                source_record_id=source_record_id,
                title="2022 Custer Gallatin Land Management Plan PDF",
                document_role="forest_plan",
                authority_level="forest",
                citation_label="R1PLAN-custer-gallatin-nf-02 | 2022 plan | artifact abc123",
                text=(
                    "The Bridger, Bangtail, and Crazy Mountains Geographic Area includes "
                    "several plan land allocations. Plan Components-Crazy Mountains "
                    "Backcountry Area (CMBCA) contain direction for backcountry use. "
                    "The Hyalite Recreation Emphasis Area (HREA) has recreation setting "
                    "direction. Inventoried Roadless Area direction applies where mapped."
                ),
            ),
        ],
    )
    _write_catalog_sqlite(
        output_dir,
        {source_record_id: ["Extract plan components by resource and geography"]},
    )
    build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
    return source_set_id


def _write_extraction_diagnostics(
    output_dir: Path,
    source_set_id: str,
    source_record_ids: list[str],
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
        "catalog_source_count": len(source_record_ids),
        "selected_source_count": len(source_record_ids),
        "extracted_count": len(source_record_ids),
        "filters": {"id": None, "parser": None, "limit": None},
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


def _names(entries: list[dict]) -> list[str]:
    return [entry["name"] for entry in entries]


def _check(validation: dict, name: str) -> dict:
    return next(check for check in validation["checks"] if check["name"] == name)


if __name__ == "__main__":
    unittest.main()
