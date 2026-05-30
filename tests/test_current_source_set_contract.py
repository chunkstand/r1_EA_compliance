from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CURRENT_SOURCE_SET_ID = "source-set-f70ea11e04ae3d53"
HISTORICAL_FULL_CANONICAL_SOURCE_SET_ID = "source-set-4fb59e9eb43045cb"
CURRENT_SOURCE_SET_CONTRACT = REPO_ROOT / "config" / "current_source_set_v1.json"
PROMOTION_SUITE = REPO_ROOT / "config" / "promotion_suite_v1.json"


def test_current_source_set_contract_names_f70_as_repo_current() -> None:
    contract = _read_json(CURRENT_SOURCE_SET_CONTRACT)

    assert contract["schema_version"] == "repo-current-source-set-v1"
    assert contract["source_set_id"] == CURRENT_SOURCE_SET_ID
    assert contract["catalog_dir"] == "source_library/catalog"
    assert contract["source_set_manifest_path"] == "source_library/catalog/source_set_manifest.json"
    assert contract["promoted_from_catalog_gate"] == (
        "source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate"
    )
    assert contract["historical_full_canonical_catalog_gate"] == (
        "source_library/runs/full-canonical-4fb-catalog-archive-20260529/catalog_gate"
    )
    assert contract["source_count"] == 719
    assert contract["artifact_count"] == 707
    assert contract["supplemental_source_count"] == 11
    assert contract["status"] == "current_repo_source_set"


def test_local_root_catalog_manifest_matches_current_source_set_when_present() -> None:
    contract = _read_json(CURRENT_SOURCE_SET_CONTRACT)
    manifest_path = REPO_ROOT / contract["source_set_manifest_path"]
    if not manifest_path.exists():
        return

    manifest = _read_json(manifest_path)

    assert manifest["source_set_id"] == CURRENT_SOURCE_SET_ID
    assert manifest["source_count"] == contract["source_count"]
    assert manifest["artifact_count"] == contract["artifact_count"]


def test_full_canonical_catalog_checks_use_historical_archive_not_repo_root() -> None:
    manifest = _read_json(PROMOTION_SUITE)
    suite_results = {result["id"]: result for result in manifest["suite_results"]}
    catalog_manifest = suite_results["full_canonical_catalog_manifest"]
    catalog_validation = suite_results["full_canonical_catalog_validation"]

    assert manifest["source_set_id"] == CURRENT_SOURCE_SET_ID
    assert manifest["full_canonical_source_set_id"] == HISTORICAL_FULL_CANONICAL_SOURCE_SET_ID
    assert catalog_manifest["path"] != "catalog/source_set_manifest.json"
    assert catalog_validation["path"] != "catalog/catalog_validation.json"
    assert catalog_manifest["path"].startswith(
        "runs/full-canonical-4fb-catalog-archive-20260529/catalog_gate/"
    )
    assert catalog_validation["path"].startswith(
        "runs/full-canonical-4fb-catalog-archive-20260529/catalog_gate/"
    )


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
