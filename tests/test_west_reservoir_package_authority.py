from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERIFICATION_PATH = (
    ROOT / "config" / "review_package_authority_verifications" / "west-reservoir-67436.json"
)
REPLAY_CONTEXT_PATH = ROOT / "config" / "replay_contexts" / "west-reservoir-67436.json"
PACKAGE_MANIFEST_PATH = (
    ROOT / "source_library" / "reviews" / "west-reservoir-67436" / "package" / "package_manifest.jsonl"
)
REAL_PACKAGE_COVERAGE_PATH = ROOT / "config" / "v1_real_package_review_coverage_v1.json"
FOREST_SPECIFIC_REGISTRY_PATH = (
    ROOT / "config" / "forest_specific_example_package_registry_v1.json"
)


def test_west_reservoir_public_pinyon_verification_matches_package_manifest() -> None:
    verification = _load_json(VERIFICATION_PATH)
    package_rows = _load_jsonl_by_title(PACKAGE_MANIFEST_PATH)

    assert verification["review_id"] == "west-reservoir-67436"
    assert verification["official_project_page"] == (
        "https://www.fs.usda.gov/r01/flathead/projects/67436"
    )
    assert verification["official_documents_page"] == (
        "https://usfs-public.app.box.com/v/PinyonPublic/folder/299363475796"
    )

    summary = verification["summary"]
    assert summary["official_file_count"] == 12
    assert summary["local_manifest_count"] == len(package_rows) == 12
    assert summary["omitted_document_count"] == 0
    assert summary["extra_local_document_count"] == 0
    assert summary["missing_from_local_manifest"] == []
    assert summary["extra_in_local_manifest"] == []
    assert summary["all_documents_verified"] is True

    verified_documents = {row["title"]: row for row in verification["documents"]}
    assert set(verified_documents) == set(package_rows)
    for title, verified_row in verified_documents.items():
        package_row = package_rows[title]
        assert verified_row["source_record_id"] == package_row["source_record_id"]
        assert verified_row["byte_size"] == package_row["artifact_byte_size"]
        assert verified_row["sha256"] == package_row["artifact_sha256"]
        assert verified_row["local_manifest_byte_size_match"] is True
        assert verified_row["local_manifest_sha256_match"] is True
        assert verified_row["verified"] is True
        assert verified_row["official_url"].startswith(
            "https://usfs-public.app.box.com/v/PinyonPublic/file/"
        )


def test_west_reservoir_authority_surfaces_point_to_verification_manifest() -> None:
    replay_context = _load_json(REPLAY_CONTEXT_PATH)
    coverage = _load_json(REAL_PACKAGE_COVERAGE_PATH)
    registry = _load_json(FOREST_SPECIFIC_REGISTRY_PATH)

    replay_authority = replay_context["package_authority"]
    assert replay_authority["official_project_page"] == (
        "https://www.fs.usda.gov/r01/flathead/projects/67436"
    )
    assert replay_authority["official_documents_page"] == (
        "https://usfs-public.app.box.com/v/PinyonPublic/folder/299363475796"
    )
    assert replay_authority["document_verification_path"] == (
        "config/review_package_authority_verifications/west-reservoir-67436.json"
    )
    assert (ROOT / replay_authority["document_verification_path"]).exists()

    slot = next(
        row for row in coverage["slots"] if row["review_id"] == "west-reservoir-67436"
    )
    example = next(
        row for row in registry["review_examples"] if row["review_id"] == "west-reservoir-67436"
    )
    assert slot["package_authority"]["document_verification_path"] == (
        "review_package_authority_verifications/west-reservoir-67436.json"
    )
    assert example["package_authority"]["document_verification_path"] == (
        "config/review_package_authority_verifications/west-reservoir-67436.json"
    )


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl_by_title(path: Path) -> dict[str, dict]:
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        rows[row["title"]] = row
    return rows
