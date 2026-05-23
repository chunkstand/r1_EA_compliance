from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import hashlib
import io
import json
import zipfile

from openpyxl import Workbook

from usfs_r1_ea_sources.config import LEGACY_WORKBOOK_LOADER_CONTRACT
from usfs_r1_ea_sources.config import load_config


ROOT = Path(__file__).resolve().parents[2]
WORKBOOK = ROOT / "usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx"
CANONICAL_WORKBOOK = ROOT / "usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx"
CONFIG = ROOT / "config" / "downloader.toml"
DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def legacy_config():
    config = load_config(CONFIG)
    return replace(
        config,
        workbook=replace(config.workbook, loader_contract=LEGACY_WORKBOOK_LOADER_CONTRACT),
    )


def canonical_config():
    config = load_config(CONFIG)
    return replace(config, workbook=replace(config.workbook, overrides_path=None))


def _write_download_run(
    output_dir: Path,
    run_id: str,
    *,
    source_record_id: str,
    artifact_body: bytes = b"",
    content_type: str = "text/html",
    suffix: str = ".html",
    status: str = "downloaded",
) -> Path:
    run_dir = output_dir / "runs" / run_id
    manifest_dir = output_dir / "manifests"
    run_dir.mkdir(parents=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"download_{run_id}.jsonl"
    artifact = output_dir / "artifacts" / "raw" / f"{run_id}-{source_record_id}{suffix}"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    if status != "skipped_excluded":
        artifact.write_bytes(artifact_body)
    record = {
        "run_id": run_id,
        "source_record_id": source_record_id,
        "status": status,
        "artifact_path": str(artifact) if status != "skipped_excluded" else None,
        "artifact_sha256": _artifact_sha256(artifact_body)
        if status != "skipped_excluded"
        else None,
        "artifact_byte_size": len(artifact_body) if status != "skipped_excluded" else None,
        "content_type": content_type,
        "fetch_timestamp": "2026-04-30T00:00:00Z",
        "final_url": "https://example.test/final",
    }
    manifest_path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        "run_id": run_id,
        "mode": "download",
        "manifest_path": str(manifest_path),
        "filtered_rows": 1,
        "status_counts": {status: 1},
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, sort_keys=True), encoding="utf-8")
    return artifact


def _write_download_run_records(output_dir: Path, run_id: str, records: list[dict]) -> None:
    run_dir = output_dir / "runs" / run_id
    manifest_dir = output_dir / "manifests"
    run_dir.mkdir(parents=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"download_{run_id}.jsonl"
    manifest_records = []
    for record in records:
        artifact = output_dir / "artifacts" / "raw" / f"{run_id}-{record['source_record_id']}{record['suffix']}"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_bytes(record["artifact_body"])
        manifest_records.append(
            {
                "run_id": run_id,
                "source_record_id": record["source_record_id"],
                "status": "downloaded",
                "artifact_path": str(artifact),
                "artifact_sha256": _artifact_sha256(record["artifact_body"]),
                "artifact_byte_size": len(record["artifact_body"]),
                "content_type": record["content_type"],
                "fetch_timestamp": "2026-04-30T00:00:00Z",
                "final_url": "https://example.test/final",
            }
        )
    manifest_path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in manifest_records),
        encoding="utf-8",
    )
    summary = {
        "run_id": run_id,
        "mode": "download",
        "manifest_path": str(manifest_path),
        "filtered_rows": len(manifest_records),
        "status_counts": {"downloaded": len(manifest_records)},
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, sort_keys=True), encoding="utf-8")


def _html_body() -> bytes:
    return (
        b"<html><body><h1>National Environmental Policy Act</h1>"
        b"<p>Agencies shall consider environmental impacts and alternatives.</p>"
        b"<p>Evidence must remain traceable to the administrative record.</p></body></html>"
    )


def _xml_body() -> bytes:
    return (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b"<ECFR><TITLE><HEAD>36 CFR Part 220</HEAD><SECTION>"
        b"<SECTNO>Section 220.4</SECTNO>"
        b"<P>Scoping shall invite public comment and document environmental concerns.</P>"
        b"</SECTION></TITLE></ECFR>"
    )


def _ecfr_part_xml_body() -> bytes:
    return (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<DIV5 N="1b" TYPE="PART">'
        b"<HEAD>PART 1b-NATIONAL ENVIRONMENT POLICY ACT</HEAD>"
        b'<DIV8 N="1b.5" TYPE="SECTION" '
        b' hierarchy_metadata="{&quot;path&quot;:&quot;/on/date/title-7/section-1b.5&quot;}">'
        b"<HEAD>&#xA7; 1b.5 Environmental assessments.</HEAD>"
        b"<P>EA-only sibling content should not leak into section 1b.6.</P>"
        b"</DIV8>"
        b'<DIV8 N="1b.6" TYPE="SECTION" '
        b' hierarchy_metadata="{&quot;path&quot;:&quot;/on/date/title-7/section-1b.6&quot;}">'
        b"<HEAD>&#xA7; 1b.6 Finding of no significant impact.</HEAD>"
        b"<P>FONSI content only.</P>"
        b"</DIV8>"
        b"</DIV5>"
    )


def _xhtml_xml_body() -> bytes:
    return (
        b"<?xml version='1.0' encoding='UTF-8' ?>"
        b'<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" '
        b'"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'
        b"<html><head><title>U.S. Code XHTML</title></head><body>"
        b"<h1>NEPA</h1><p>Text with dash entity &mdash; and traceability.</p>"
        b"</body></html>"
    )


def _docx_body(paragraphs: list[str]) -> bytes:
    namespace = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    paragraph_xml = "".join(
        f"<w:p><w:r><w:t>{_xml_escape(paragraph)}</w:t></w:r></w:p>"
        for paragraph in paragraphs
    )
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{namespace}"><w:body>{paragraph_xml}</w:body></w:document>'
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", document_xml)
    buffer.seek(0)
    return buffer.read()


def _xlsx_body(rows: list[list[object]]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "SCC Evaluation"
    for row in rows:
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer.read()


def _pdf_body() -> bytes:
    return (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [] /Count 0 >> endobj\n"
        b"trailer << /Root 1 0 R >>\n%%EOF\n"
    )


def _xml_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _zip_with_metadata_body() -> bytes:
    metadata_xml = (
        "<metadata>"
        "<idinfo><citation><citeinfo>"
        "<title>Lolo National Forest Grizzly Bear Analysis Unit Shapefile</title>"
        "</citeinfo></citation></idinfo>"
        "<dataqual><lineage><procstep>"
        "<procdesc>Exported GIS layer package for grizzly bear analysis units.</procdesc>"
        "</procstep></lineage></dataqual>"
        "</metadata>"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("GrizAnalysisUnits_LNF_10302023.shp.xml", metadata_xml)
        archive.writestr("GrizAnalysisUnits_LNF_10302023.shp", b"shape-bytes")
        archive.writestr("GrizAnalysisUnits_LNF_10302023.dbf", b"dbf-bytes")
    buffer.seek(0)
    return buffer.read()


def _artifact_sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _check(validation: dict, name: str) -> dict:
    for check in validation["checks"]:
        if check["name"] == name:
            return check
    raise AssertionError(f"Missing validation check {name}")
