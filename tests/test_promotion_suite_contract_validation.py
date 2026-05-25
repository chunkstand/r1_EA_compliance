from __future__ import annotations

from pathlib import Path
import json

import pytest

from tests.support.promotion_suite_fixtures import write_suite_fixture
from usfs_r1_ea_sources.promotion_suite_validation import _validate_manifest


def _fixture_manifest(tmp_path: Path) -> dict:
    manifest_path, _ = write_suite_fixture(tmp_path)
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def test_validate_manifest_rejects_current_selector_review_id_coupling(
    tmp_path: Path,
) -> None:
    manifest = _fixture_manifest(tmp_path)
    manifest["current_promotion_contract"]["slot_selector"]["review_id"] = "review-1"

    with pytest.raises(ValueError, match="hard-coded review_id selectors"):
        _validate_manifest(manifest)


def test_validate_manifest_rejects_review_slot_family_without_same_slot_binding(
    tmp_path: Path,
) -> None:
    manifest = _fixture_manifest(tmp_path)
    review_family = manifest["current_promotion_contract"]["artifact_families"][1]
    review_family["slot_binding"] = "any_slot"

    with pytest.raises(ValueError, match="slot_binding='same_slot'"):
        _validate_manifest(manifest)


def test_validate_manifest_rejects_inline_packet_checks_in_current_family(
    tmp_path: Path,
) -> None:
    manifest = _fixture_manifest(tmp_path)
    review_family = manifest["current_promotion_contract"]["artifact_families"][1]
    review_family["checks"] = [{"name": "count_guard", "equals": 2}]

    with pytest.raises(ValueError, match="packet-local checks"):
        _validate_manifest(manifest)
