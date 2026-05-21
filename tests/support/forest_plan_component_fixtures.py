from __future__ import annotations

import hashlib
import json
from pathlib import Path


_FOREST_PLAN_TEXT = """
Plan Components-Crazy Mountains Backcountry Area (CMBCA).
Desired Conditions (BC-DC-CMBCA) 01 Quiet, nonmotorized recreation opportunities predominate.
Standards (BC-STD-CMBCA) 01 New permanent or temporary roads shall not be allowed.
Suitability (BC-SUIT-CMBCA) 01 The backcountry area is not suitable for motorized transport.
"""


def _chunk(*, source_set_id: str, source_record_id: str, text: str) -> dict:
    return {
        "chunk_id": f"chunk:{source_record_id}",
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "chunk_index": 0,
        "title": "Custer Gallatin Land Management Plan",
        "document_role": "forest_plan",
        "authority_level": "forest_plan",
        "host": "example.test",
        "expected_parser": "pdf",
        "artifact_sha256": hashlib.sha256(source_record_id.encode("utf-8")).hexdigest(),
        "artifact_path": f"artifacts/raw/{source_record_id}.pdf",
        "citation_label": f"{source_record_id} | Custer Gallatin LMP",
        "original_url": f"https://example.test/{source_record_id}/original",
        "effective_url": f"https://example.test/{source_record_id}",
        "final_url": f"https://example.test/{source_record_id}",
        "parser_name": "unit_parser",
        "parser_version": "1.0",
        "extracted_at": "2026-05-01T00:00:00Z",
        "source_text_path": f"derived/{source_set_id}/extracted_text/{source_record_id}.txt",
        "char_start": 0,
        "char_end": len(text),
        "page": None,
        "section": None,
        "heading": "Plan Components-Crazy Mountains Backcountry Area (CMBCA)",
        "content_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "text": text,
    }


def _package_chunk(*, title: str, text: str) -> dict:
    source_record_id = title.replace(" ", "-")
    return {
        **_chunk(
            source_set_id="source-set-package",
            source_record_id=source_record_id,
            text=text,
        ),
        "title": title,
        "document_role": "environmental_assessment",
        "authority_level": "project",
        "citation_label": f"{source_record_id} package citation",
        "artifact_path": f"package/{source_record_id}.pdf",
        "heading": None,
    }


def _write_chunks(*, output_dir: Path, source_set_id: str, chunks: list[dict]) -> Path:
    path = output_dir / "derived" / source_set_id / "chunks" / "chunks.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(chunk, sort_keys=True) + "\n" for chunk in chunks),
        encoding="utf-8",
    )
    return path


def _write_inventory_build_contract(
    output_dir: Path,
    *,
    source_set_id: str,
    rows: list[dict[str, object]],
) -> tuple[Path, Path]:
    manifest_path = output_dir / "config" / "inventory_build_manifest.json"
    readiness_path = output_dir / "config" / "readiness.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": "region1-forest-plan-component-inventory-build-manifest-v0",
        "manifest_id": "unit-test-build-manifest",
        "source_set_references": [
            {
                "reference_id": "test_source_set",
                "reference_type": "explicit_source_set_id",
                "source_set_id": source_set_id,
                "description": "Unit-test source set.",
            }
        ],
        "profile_rows": [
            {
                "forest_unit_id": row["forest_unit_id"],
                "source_set_reference_id": "test_source_set",
                "primary_plan_source_record_id": row["source_record_id"],
                "plan_version": row["plan_version"],
                "build_source_record_ids_by_role": row.get(
                    "build_source_record_ids_by_role",
                    {
                        "primary_land_management_plan": [row["source_record_id"]],
                    },
                ),
                "promotion_eligibility": {
                    "status": "eligible",
                    "accepted_blockers": [],
                },
            }
            for row in rows
        ],
    }
    readiness = {
        "schema_version": "region1-forest-plan-readiness-nepa-3d-v1",
        "profile_rows": [
            {
                "forest_unit_id": row["forest_unit_id"],
                "source_requirements": [
                    {
                        "source_record_id": row["source_record_id"],
                    }
                ],
            }
            for row in rows
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    readiness_path.write_text(json.dumps(readiness, indent=2, sort_keys=True), encoding="utf-8")
    return manifest_path, readiness_path


def _check(report: dict, name: str) -> dict:
    for check in report["checks"]:
        if check["name"] == name:
            return check
    raise AssertionError(f"Missing check {name!r}")
