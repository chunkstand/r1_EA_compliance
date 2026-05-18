from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile

from openpyxl import load_workbook

from usfs_r1_ea_sources.config import (
    LEGACY_WORKBOOK_LOADER_CONTRACT,
    SOURCE_REGISTER_WORKBOOK_LOADER_CONTRACT,
    load_config,
)
from usfs_r1_ea_sources.source_register import load_source_register_rows
from usfs_r1_ea_sources.workbook import load_canonical_sources


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "downloader.toml"
CANONICAL_WORKBOOK = ROOT / "usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx"


def test_active_config_stays_on_legacy_loader_contract() -> None:
    config = load_config(CONFIG)
    assert config.workbook.loader_contract == LEGACY_WORKBOOK_LOADER_CONTRACT


def test_source_register_loader_dispatch_returns_workbook_source_compatibility_rows() -> None:
    config = load_config(CONFIG)
    workbook_config = replace(
        config.workbook,
        loader_contract=SOURCE_REGISTER_WORKBOOK_LOADER_CONTRACT,
        overrides_path=None,
    )

    sources = load_canonical_sources(CANONICAL_WORKBOOK, workbook_config)

    assert len(sources) == 635
    assert all(source.sheet == "Document_Register_Master" for source in sources)
    assert all(source.metadata["loader_contract"] == SOURCE_REGISTER_WORKBOOK_LOADER_CONTRACT for source in sources)
    assert all(source.metadata["row_state"] == "load_ready_master_row" for source in sources)
    assert all(source.metadata["direct_file_readiness_class"] == "load_ready" for source in sources)
    assert all(source.metadata["authority_document_id"] for source in sources)
    assert all(source.metadata["source_authority_link_id"] for source in sources)


def test_source_register_loader_exposes_semantic_identity_and_scope_seams() -> None:
    rows = {
        row.source_record_id: row for row in load_source_register_rows(CANONICAL_WORKBOOK)
    }

    nepa_row = rows["FED-001"]
    assert nepa_row.authority_document_id == "authority_document:nepa-act"
    assert nepa_row.authority_document_class_id == "authority_document"
    assert nepa_row.jurisdiction_scope_id == "scope:federal-us"
    assert nepa_row.parser_admission_class == "structured_web_source"
    assert nepa_row.expected_parser == "html"

    handbook_row = rows["SUP-003"]
    assert handbook_row.authority_document_id == "authority_document:fsh-1909-15"

    pdf_row = rows["WILD-ESA-087"]
    assert pdf_row.parser_admission_class == "direct_document"
    assert pdf_row.expected_parser == "pdf"

    forest_plan_row = rows["FPS-002"]
    assert forest_plan_row.authority_document_class_id == "forest_plan"
    assert forest_plan_row.jurisdiction_scope_id == "scope:region1-forest-unit"
    assert forest_plan_row.authority_section_id is not None


def test_source_register_loader_rejects_blocked_alias_without_context() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        workbook_path = Path(tmp_dir) / "ambiguous-source-register.xlsx"
        workbook = load_workbook(CANONICAL_WORKBOOK)
        sheet = workbook["Document_Register_Master"]
        headers = {
            str(sheet.cell(4, column).value).strip(): column
            for column in range(1, sheet.max_column + 1)
        }
        target_row = 5
        sheet.cell(target_row, headers["Document_Title"]).value = "Forest Plan"
        sheet.cell(target_row, headers["Citation_or_Code"]).value = ""
        sheet.cell(target_row, headers["Issuing_Entity"]).value = ""
        sheet.cell(target_row, headers["Jurisdiction_or_Unit"]).value = ""
        sheet.cell(target_row, headers["Issue_or_Effective_Date"]).value = ""
        workbook.save(workbook_path)

        try:
            load_source_register_rows(workbook_path)
        except ValueError as exc:
            assert "requires more context before resolving blocked alias" in str(exc)
        else:
            raise AssertionError("Expected canonical loader to fail on blocked alias without context")
