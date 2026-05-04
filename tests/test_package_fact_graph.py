from __future__ import annotations

from pathlib import Path
import hashlib
import json
import tempfile
import unittest

from usfs_r1_ea_sources.cli import main
from usfs_r1_ea_sources.package_fact_graph import build_package_fact_graph


class PackageFactGraphTests(unittest.TestCase):
    def test_builds_package_fact_graph_with_span_bound_facts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "source_library"
            review_id = "east-crazy-unit"
            source_set_id = "source-set-unit"
            _write_package_cache(output_dir, review_id)

            result = build_package_fact_graph(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
            )

            self.assertTrue(result.package_fact_graph_path.exists())
            self.assertTrue(result.package_applicability_context_path.exists())
            self.assertTrue(result.validation_summary_path.exists())
            self.assertTrue(result.summary["validation_passed"])

            graph = json.loads(result.package_fact_graph_path.read_text(encoding="utf-8"))
            context = json.loads(
                result.package_applicability_context_path.read_text(encoding="utf-8")
            )
            self.assertEqual(graph["schema_version"], "package-fact-graph-v0")
            self.assertEqual(
                context["schema_version"],
                "package-applicability-context-v0",
            )
            self.assertEqual(graph["source_set_id"], source_set_id)
            self.assertEqual(context["package_fact_graph_sha256"], graph["package_fact_graph_sha256"])

            fact_nodes = [
                node
                for node in graph["nodes"]
                if node["node_type"] not in {"package_section", "evidence_span"}
            ]
            self.assertTrue(fact_nodes)
            for node in fact_nodes:
                self.assertTrue(node["package_chunk_ids"], node["node_id"])
                self.assertTrue(node["section_ids"], node["node_id"])
                self.assertTrue(node["evidence_span_ids"], node["node_id"])
                self.assertTrue(node["content_sha256"], node["node_id"])
                self.assertTrue(node["artifact_sha256"], node["node_id"])
                self.assertTrue(node["parser_provenance"], node["node_id"])

            observed_pairs = {
                (node["node_type"], node["normalized_value"])
                for node in fact_nodes
                if node["confidence_class"] != "negative_context"
            }
            self.assertIn(("action", "land_exchange"), observed_pairs)
            self.assertIn(("agency", "usfs"), observed_pairs)
            self.assertIn(("nepa_level", "environmental_assessment"), observed_pairs)
            self.assertIn(("geography", "custer-gallatin-nf"), observed_pairs)
            self.assertIn(("geography", "geo-bridger-bangtail-crazy"), observed_pairs)
            self.assertIn(("management_area", "mgmt-crazy-mountains-bca"), observed_pairs)
            self.assertIn(("overlay", "overlay-inventoried-roadless"), observed_pairs)
            self.assertIn(("resource_topic", "wildlife"), observed_pairs)
            self.assertIn(("consultation", "esa"), observed_pairs)
            self.assertIn(("consultation", "nhpa"), observed_pairs)
            self.assertIn(("permit", "clean_water_act"), observed_pairs)
            self.assertIn(("public_involvement", "public_comment"), observed_pairs)
            self.assertIn(("alternative", "no_action"), observed_pairs)

            sioux_positive = [
                node
                for node in fact_nodes
                if node["node_type"] == "geography"
                and node["normalized_value"] == "geo-sioux"
                and node["confidence_class"] != "negative_context"
            ]
            sioux_negative = [
                node
                for node in fact_nodes
                if node["node_type"] == "geography"
                and node["normalized_value"] == "geo-sioux"
                and node["confidence_class"] == "negative_context"
            ]
            self.assertEqual(sioux_positive, [])
            self.assertTrue(sioux_negative)

            validation_check = _check(
                graph["validation"],
                "negative_location_statements_do_not_create_positive_location_facts",
            )
            self.assertTrue(validation_check["passed"])
            self.assertGreater(
                validation_check["details"]["negative_location_fact_count"],
                0,
            )
            self.assertFalse(
                (result.applicability_dir / "applicability_decisions.jsonl").exists()
            )
            self.assertFalse((result.applicability_dir / "generated_rule_pack.json").exists())
            self.assertTrue(context["forest_units"])
            self.assertTrue(context["geography"])
            self.assertTrue(context["management_areas"])
            self.assertTrue(context["consultations"])
            self.assertTrue(context["permits"])

    def test_cli_writes_package_context_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "source_library"
            review_id = "cli-context-unit"
            _write_package_cache(output_dir, review_id)

            exit_code = main(
                [
                    "applicability-context-build",
                    "--output-dir",
                    str(output_dir),
                    "--review-id",
                    review_id,
                    "--source-set-id",
                    "source-set-unit",
                ]
            )

            self.assertEqual(exit_code, 0)
            applicability_dir = output_dir / "reviews" / review_id / "applicability"
            graph_path = applicability_dir / "package_fact_graph.json"
            context_path = applicability_dir / "package_applicability_context.json"
            validation_path = applicability_dir / "package_fact_graph_validation.json"
            self.assertTrue(graph_path.exists())
            self.assertTrue(context_path.exists())
            self.assertTrue(validation_path.exists())
            validation = json.loads(validation_path.read_text(encoding="utf-8"))
            self.assertTrue(validation["validation"]["passed"])


def _write_package_cache(output_dir: Path, review_id: str) -> None:
    package_dir = output_dir / "reviews" / review_id / "package"
    package_dir.mkdir(parents=True, exist_ok=True)
    artifact_sha256 = hashlib.sha256(review_id.encode("utf-8")).hexdigest()
    manifest = [
        {
            "source_set_id": f"ea-package-{review_id}",
            "source_record_id": "EA-PACKAGE-001",
            "title": "East Crazy Inspiration Divide Land Exchange EA.pdf",
            "artifact_path": "/tmp/East Crazy Inspiration Divide Land Exchange EA.pdf",
            "artifact_sha256": artifact_sha256,
            "artifact_byte_size": 1000,
            "content_type": "application/pdf",
            "citation_label": "EA-PACKAGE-001",
            "extracted_at": "2026-05-03T00:00:00Z",
            "status": "extracted",
            "parser_name": "unit-parser",
            "parser_version": "1.0",
            "text_path": "/tmp/east-crazy.txt",
            "text_sha256": artifact_sha256,
            "text_char_count": 5000,
            "chunk_count": 4,
        }
    ]
    chunks = [
        _chunk(
            review_id=review_id,
            artifact_sha256=artifact_sha256,
            index=0,
            section="Purpose and Need",
            heading="Purpose and Need",
            text=(
                "The East Crazy Inspiration Divide Land Exchange Project is an "
                "environmental assessment. The Forest Service proposes a land exchange "
                "on the Custer Gallatin National Forest."
            ),
        ),
        _chunk(
            review_id=review_id,
            artifact_sha256=artifact_sha256,
            index=1,
            section="Affected Environment",
            heading="Forest Plan Consistency",
            text=(
                "The project area is in the Bridger, Bangtail, and Crazy Mountains "
                "Geographic Area and the Crazy Mountains Backcountry Area. It also "
                "intersects an Inventoried Roadless Area. The Sioux Geographic Area is "
                "not part of the project area."
            ),
        ),
        _chunk(
            review_id=review_id,
            artifact_sha256=artifact_sha256,
            index=2,
            section="Environmental Consequences",
            heading="Resources and Consultation",
            text=(
                "The analysis discusses wildlife, water quality, recreation, roads, "
                "heritage resources, botany, fire, scenery, and grazing. The package "
                "identifies Endangered Species Act Section 7 consultation, National "
                "Historic Preservation Act Section 106 review, the Migratory Bird "
                "Treaty Act, tribal consultation, wetlands, floodplains, and a Clean "
                "Water Act Section 404 permit."
            ),
        ),
        _chunk(
            review_id=review_id,
            artifact_sha256=artifact_sha256,
            index=3,
            section="Alternatives",
            heading="No Action Alternative",
            text=(
                "The no action alternative and proposed action were compared after "
                "public comment and public scoping. Mitigation, cumulative effects, "
                "and a Finding of No Significant Impact are documented."
            ),
        ),
    ]
    _write_jsonl(package_dir / "package_manifest.jsonl", manifest)
    _write_jsonl(package_dir / "package_chunks.jsonl", chunks)


def _chunk(
    *,
    review_id: str,
    artifact_sha256: str,
    index: int,
    section: str,
    heading: str,
    text: str,
) -> dict:
    content_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "chunk_id": f"chunk-{index}",
        "source_set_id": f"ea-package-{review_id}",
        "source_record_id": "EA-PACKAGE-001",
        "chunk_index": index,
        "title": "East Crazy Inspiration Divide Land Exchange EA.pdf",
        "document_role": "ea_package",
        "authority_level": "project_record",
        "artifact_sha256": artifact_sha256,
        "artifact_path": "/tmp/East Crazy Inspiration Divide Land Exchange EA.pdf",
        "citation_label": "EA-PACKAGE-001",
        "parser_name": "unit-parser",
        "parser_version": "1.0",
        "extracted_at": "2026-05-03T00:00:00Z",
        "source_text_path": "/tmp/east-crazy.txt",
        "char_start": index * 1000,
        "char_end": index * 1000 + len(text),
        "page": index + 1,
        "section": section,
        "heading": heading,
        "content_sha256": content_sha256,
        "text": text,
    }


def _check(validation: dict, name: str) -> dict:
    for check in validation["checks"]:
        if check["name"] == name:
            return check
    raise AssertionError(f"Missing validation check: {name}")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, sort_keys=True) for record in records]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
