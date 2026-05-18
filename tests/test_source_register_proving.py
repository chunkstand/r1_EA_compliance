from __future__ import annotations

from pathlib import Path
import tempfile

from usfs_r1_ea_sources.authority_currentness import build_authority_currentness_report
from usfs_r1_ea_sources.source_register_proving import build_source_register_proving_slice
from usfs_r1_ea_sources.source_register_proving import resolve_authority_currentness_inputs
from usfs_r1_ea_sources.source_register_proving import resolve_latest_proving_context


ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx"
MANIFEST = ROOT / "config" / "source_register_proving_slice_v1.json"
CONFIG = ROOT / "config" / "downloader.toml"


def build_test_proving_slice(output_dir: Path):
    return build_source_register_proving_slice(
        workbook_path=WORKBOOK,
        manifest_path=MANIFEST,
        output_dir=output_dir,
        config_path=CONFIG,
    )


def test_source_register_proving_slice_builds_report_and_currentness_inputs() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "source_library"
        result = build_test_proving_slice(output_dir)

        assert result.summary["validation_passed"] is True
        assert result.summary["load_ready_source_count"] == 26
        assert result.summary["queue_source_count"] == 5
        assert result.report_path.exists()

        context = resolve_latest_proving_context(output_dir)
        assert context["source_set_id"] == result.summary["source_set_id"]

        resolved_inputs = resolve_authority_currentness_inputs(
            output_dir=output_dir,
            source_set_id=None,
            authority_inventory_path=Path(
                "config/authority_universe_families_nepa_ea_v1.json"
            ),
            source_addition_decisions_path=Path(
                "config/authority_source_addition_decisions_nepa_ea_v1.json"
            ),
            catalog_path=None,
            source_set_manifest_path=None,
        )
        currentness = build_authority_currentness_report(
            output_dir=output_dir,
            source_set_id=resolved_inputs["source_set_id"],
            authority_inventory_path=resolved_inputs["authority_inventory_path"],
            source_addition_decisions_path=resolved_inputs[
                "source_addition_decisions_path"
            ],
            catalog_path=resolved_inputs["catalog_path"],
            source_set_manifest_path=resolved_inputs["source_set_manifest_path"],
        )

        assert currentness.summary["validation_passed"] is True
