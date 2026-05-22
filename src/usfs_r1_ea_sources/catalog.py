from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import cache
from pathlib import Path
from urllib.parse import urlsplit
import hashlib
import json
import subprocess

from .capture_run_support import write_jsonl
from .catalog_outputs import (
    _graph_records,
    _load_manifest_records,
    _validation_report,
    _write_sqlite,
)
from .config import DownloaderConfig, LEGACY_WORKBOOK_LOADER_CONTRACT
from .records import WorkbookSource, sha256_file
from .source_partitions import catalog_source_partition
from .workbook import (
    ensure_supplemental_sources_allowed,
    load_canonical_sources,
    merge_supplemental_sources,
)


@dataclass(frozen=True)
class CatalogBuildResult:
    source_set_id: str
    catalog_dir: Path
    source_catalog_path: Path
    source_set_manifest_path: Path
    validation_path: Path
    sqlite_path: Path
    graph_nodes_path: Path
    graph_edges_path: Path
    summary: dict


DEFAULT_REGION1_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "r1_forest_plan_component_inventory_build_manifest.json"
)


def build_review_catalog(
    *,
    workbook_path: Path,
    output_dir: Path,
    config: DownloaderConfig,
    config_path: Path | None = None,
    run_id: str | None = None,
    batch_run_id: str | None = None,
    batch_run_ids: list[str] | None = None,
    source_record_ids: set[str] | None = None,
    supplemental_sources: list[WorkbookSource] | None = None,
    source_delta_input: dict | None = None,
    catalog_dir: Path | None = None,
) -> CatalogBuildResult:
    if batch_run_id and batch_run_ids:
        raise ValueError("batch_run_id and batch_run_ids are mutually exclusive")
    active_batch_run_ids = list(batch_run_ids or ([batch_run_id] if batch_run_id else []))
    if run_id and active_batch_run_ids:
        raise ValueError("run_id and batch run IDs are mutually exclusive")
    single_batch_run_id = active_batch_run_ids[0] if len(active_batch_run_ids) == 1 else None

    catalog_dir = Path(catalog_dir) if catalog_dir else output_dir / "catalog"
    catalog_dir.mkdir(parents=True, exist_ok=True)
    source_catalog_path = catalog_dir / "source_catalog.jsonl"
    source_set_manifest_path = catalog_dir / "source_set_manifest.json"
    validation_path = catalog_dir / "catalog_validation.json"
    sqlite_path = catalog_dir / "review_sources.sqlite"
    graph_nodes_path = catalog_dir / "source_graph_nodes.jsonl"
    graph_edges_path = catalog_dir / "source_graph_edges.jsonl"

    workbook_sha256 = sha256_file(workbook_path)
    config_sha256 = sha256_file(config_path) if config_path and config_path.exists() else None
    overrides_path = (
        config.workbook.overrides_path
        if config.workbook.loader_contract == LEGACY_WORKBOOK_LOADER_CONTRACT
        else None
    )
    overrides_sha256 = _optional_sha256(overrides_path)
    git_commit = _git_commit(workbook_path.parent)
    workbook_sources = load_canonical_sources(workbook_path, config.workbook)
    ensure_supplemental_sources_allowed(
        config.workbook,
        supplemental_sources=supplemental_sources,
        source_delta_input=source_delta_input,
    )
    sources = merge_supplemental_sources(workbook_sources, supplemental_sources)
    if source_record_ids is not None:
        available_source_ids = {source.source_record_id for source in sources}
        missing_source_ids = sorted(source_record_ids - available_source_ids)
        if missing_source_ids:
            raise ValueError(
                f"Catalog build requested source IDs with no loaded sources: {missing_source_ids}"
            )
        sources = [source for source in sources if source.source_record_id in source_record_ids]

    source_set_id = _source_set_id(
        workbook_sha256=workbook_sha256,
        config_sha256=config_sha256,
        overrides_sha256=overrides_sha256,
        run_id=run_id,
        batch_run_id=single_batch_run_id,
        batch_run_ids=active_batch_run_ids if len(active_batch_run_ids) > 1 else None,
        git_commit=git_commit,
        source_scope=_source_scope(
            source_record_ids=source_record_ids,
            supplemental_sources=supplemental_sources,
            source_delta_input=source_delta_input,
        ),
    )

    manifest_records, manifest_load_checks = _load_manifest_records(
        output_dir,
        run_id,
        single_batch_run_id,
        batch_run_ids=active_batch_run_ids if len(active_batch_run_ids) > 1 else None,
        sources=sources,
    )
    catalog_records = [
        _catalog_record(
            source_set_id=source_set_id,
            source=source,
            manifest_record=manifest_records.get(source.source_record_id),
            run_id=run_id,
            batch_run_id=single_batch_run_id,
            batch_run_scope_present=bool(active_batch_run_ids),
        )
        for source in sources
    ]
    manifest = _source_set_manifest(
        source_set_id=source_set_id,
        workbook_path=workbook_path,
        workbook_sha256=workbook_sha256,
        config_path=config_path,
        config_sha256=config_sha256,
        overrides_path=overrides_path,
        overrides_sha256=overrides_sha256,
        git_commit=git_commit,
        run_id=run_id,
        batch_run_id=single_batch_run_id,
        batch_run_ids=active_batch_run_ids,
        source_record_id_filter_count=(
            len(source_record_ids) if source_record_ids is not None else None
        ),
        supplemental_source_count=len(supplemental_sources or []),
        source_delta_input=source_delta_input,
        records=catalog_records,
    )
    graph_nodes, graph_edges = _graph_records(catalog_records)
    validation_report = _validation_report(
        source_set_id=source_set_id,
        records=catalog_records,
        batch_run_ids=active_batch_run_ids,
        source_delta_input=source_delta_input,
        manifest_load_checks=manifest_load_checks,
    )

    write_jsonl(source_catalog_path, catalog_records)
    _write_json(source_set_manifest_path, manifest)
    _write_json(validation_path, validation_report)
    write_jsonl(graph_nodes_path, graph_nodes)
    write_jsonl(graph_edges_path, graph_edges)
    _write_sqlite(sqlite_path, manifest, catalog_records)

    summary = {
        "source_set_id": source_set_id,
        "source_count": len(catalog_records),
        "artifact_count": _artifact_count(catalog_records),
        "unique_url_count": len({record["normalized_url"] for record in catalog_records}),
        "review_topic_count": _review_topic_count(catalog_records),
        "authority_count": _authority_count(catalog_records),
        "source_partition_counts": manifest["source_partition_counts"],
        "download_run_id": run_id,
        "download_batch_run_id": single_batch_run_id,
        "download_batch_run_ids": active_batch_run_ids,
        "source_record_id_filter_count": (
            len(source_record_ids) if source_record_ids is not None else None
        ),
        "supplemental_source_count": len(supplemental_sources or []),
        "source_delta_input": source_delta_input,
        "validation_passed": validation_report["passed"],
        "validation_path": str(validation_path),
        "source_catalog_path": str(source_catalog_path),
        "source_set_manifest_path": str(source_set_manifest_path),
        "sqlite_path": str(sqlite_path),
        "graph_nodes_path": str(graph_nodes_path),
        "graph_edges_path": str(graph_edges_path),
    }
    return CatalogBuildResult(
        source_set_id=source_set_id,
        catalog_dir=catalog_dir,
        source_catalog_path=source_catalog_path,
        source_set_manifest_path=source_set_manifest_path,
        validation_path=validation_path,
        sqlite_path=sqlite_path,
        graph_nodes_path=graph_nodes_path,
        graph_edges_path=graph_edges_path,
        summary=summary,
    )


def _catalog_record(
    *,
    source_set_id: str,
    source: WorkbookSource,
    manifest_record: dict | None,
    run_id: str | None,
    batch_run_id: str | None,
    batch_run_scope_present: bool = False,
) -> dict:
    metadata = source.metadata
    host = urlsplit(source.normalized_url).netloc.lower()
    document_type = _clean(metadata.get("document_type"))
    issuer = _clean(metadata.get("issuer"))
    applies_to = _first_nonempty(metadata.get("applies_to"), metadata.get("applies_when"))
    review_engine_checks = _clean(metadata.get("review_engine_checks"))
    review_topics = _review_topics(review_engine_checks)
    artifact_sha256 = _from_manifest(manifest_record, "artifact_sha256")
    content_type = _from_manifest(manifest_record, "content_type")
    source_status = _source_status(
        manifest_record,
        bool(run_id or batch_run_id or batch_run_scope_present),
    )
    artifact_run_id = _from_manifest(manifest_record, "run_id") or run_id
    artifact_batch_run_id = _from_manifest(manifest_record, "download_batch_run_id") or batch_run_id
    record = {
        "source_set_id": source_set_id,
        "source_record_id": source.source_record_id,
        "sheet": source.sheet,
        "excel_row": source.excel_row,
        "source_id": source.source_id,
        "title": source.title,
        "document_role": _document_role(source, document_type),
        "authority_level": _authority_level(source, issuer, host),
        "issuer": issuer,
        "scope": _clean(metadata.get("scope")),
        "layer": _clean(metadata.get("layer")),
        "document_type": document_type,
        "unit_or_overlay": _clean(metadata.get("unit_or_overlay")),
        "applies_to": applies_to,
        "trigger": _clean(metadata.get("trigger")),
        "review_engine_checks": review_engine_checks,
        "review_topics": review_topics,
        "currentness_notes": _clean(metadata.get("currentness_notes")),
        "original_url": source.original_url,
        "effective_url": source.effective_url,
        "normalized_url": source.normalized_url,
        "host": host,
        "expected_parser": _expected_parser(source, content_type),
        "source_status": source_status,
        "download_run_id": artifact_run_id,
        "download_batch_run_id": artifact_batch_run_id,
        "final_url": _from_manifest(manifest_record, "final_url"),
        "artifact_sha256": artifact_sha256,
        "artifact_path": _from_manifest(manifest_record, "artifact_path"),
        "artifact_byte_size": _from_manifest(manifest_record, "artifact_byte_size"),
        "content_type": content_type,
        "retrieved_at": _from_manifest(manifest_record, "fetch_timestamp"),
        "duplicate_of": _from_manifest(manifest_record, "duplicate_of"),
        "citation_label": _citation_label(source, artifact_sha256),
        "metadata": metadata,
    }
    source_partition, source_partition_basis = catalog_source_partition(record)
    record["source_partition"] = source_partition
    record["source_partition_basis"] = source_partition_basis
    return record


def _source_set_manifest(
    *,
    source_set_id: str,
    workbook_path: Path,
    workbook_sha256: str,
    config_path: Path | None,
    config_sha256: str | None,
    overrides_path: Path | None,
    overrides_sha256: str | None,
    git_commit: str | None,
    run_id: str | None,
    batch_run_id: str | None,
    batch_run_ids: list[str],
    source_record_id_filter_count: int | None,
    supplemental_source_count: int,
    source_delta_input: dict | None,
    records: list[dict],
) -> dict:
    status_counts = Counter(record["source_status"] for record in records)
    role_counts = Counter(record["document_role"] for record in records)
    host_counts = Counter(record["host"] for record in records)
    parser_counts = Counter(record["expected_parser"] for record in records)
    source_partition_counts = Counter(record["source_partition"] for record in records)
    return {
        "source_set_id": source_set_id,
        "created_at": _utc_now(),
        "workbook_path": str(workbook_path),
        "workbook_sha256": workbook_sha256,
        "config_path": str(config_path) if config_path else None,
        "config_sha256": config_sha256,
        "overrides_path": str(overrides_path) if overrides_path else None,
        "overrides_sha256": overrides_sha256,
        "git_commit": git_commit,
        "download_run_id": run_id,
        "download_batch_run_id": batch_run_id,
        "download_batch_run_ids": batch_run_ids,
        "source_record_id_filter_count": source_record_id_filter_count,
        "supplemental_source_count": supplemental_source_count,
        "source_delta_input": source_delta_input,
        "source_count": len(records),
        "unique_url_count": len({record["normalized_url"] for record in records}),
        "artifact_count": _artifact_count(records),
        "review_topic_count": _review_topic_count(records),
        "authority_count": len({record["issuer"] for record in records if record["issuer"]}),
        "status_counts": dict(status_counts),
        "source_partition_counts": dict(source_partition_counts),
        "document_role_counts": dict(role_counts),
        "host_counts": dict(host_counts),
        "expected_parser_counts": dict(parser_counts),
    }


def _source_set_id(
    *,
    workbook_sha256: str,
    config_sha256: str | None,
    overrides_sha256: str | None,
    run_id: str | None,
    batch_run_id: str | None,
    git_commit: str | None,
    batch_run_ids: list[str] | None = None,
    source_scope: dict | None = None,
) -> str:
    payload = {
        "workbook_sha256": workbook_sha256,
        "config_sha256": config_sha256,
        "overrides_sha256": overrides_sha256,
        "download_run_id": run_id,
        "download_batch_run_id": batch_run_id,
        "git_commit": git_commit,
    }
    if batch_run_ids is not None:
        payload["download_batch_run_ids"] = batch_run_ids
    if source_scope is not None:
        payload["source_scope"] = source_scope
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"source-set-{digest[:16]}"


def _source_scope(
    *,
    source_record_ids: set[str] | None,
    supplemental_sources: list[WorkbookSource] | None,
    source_delta_input: dict | None,
) -> dict | None:
    if source_record_ids is None and not supplemental_sources and not source_delta_input:
        return None
    return {
        "source_record_ids": sorted(source_record_ids) if source_record_ids is not None else None,
        "supplemental_source_record_ids": sorted(
            source.source_record_id for source in supplemental_sources or []
        ),
        "source_delta_input": source_delta_input,
    }


def _optional_sha256(path: Path | None) -> str | None:
    if path and path.exists():
        return sha256_file(path)
    return None


def _git_commit(cwd: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def _source_status(manifest_record: dict | None, run_scope_present: bool) -> str:
    if manifest_record:
        return str(manifest_record.get("status") or "unknown")
    return "not_in_run" if run_scope_present else "planned"


def _document_role(source: WorkbookSource, document_type: str | None) -> str:
    metadata = source.metadata
    if metadata.get("loader_contract") == "source_register_v1":
        authority_document_class_id = (_clean(metadata.get("authority_document_class_id")) or "").lower()
        authority_tier = (_clean(metadata.get("authority_tier")) or "").lower()
        sub_tier = (_clean(metadata.get("sub_tier")) or "").lower()
        document_type_value = (document_type or "").lower()
        title = source.title.lower()
        currentness_notes = (_clean(metadata.get("currentness_notes")) or "").lower()
        citation = (_clean(metadata.get("citation_or_code")) or "").lower()
        combined = " ".join(
            value
            for value in (
                authority_document_class_id,
                authority_tier,
                sub_tier,
                document_type_value,
                title,
                currentness_notes,
                citation,
            )
            if value
        )

        if source.source_record_id in _r1_forest_plan_manifest_primary_component_source_record_ids():
            return "forest_plan"
        if "executive order" in combined:
            return "executive_order"
        if (
            authority_document_class_id == "forest_plan"
            or authority_tier == "forest"
            or "forest plan" in combined
            or sub_tier == "forest plan support"
        ):
            support_tokens = (
                "administrative change",
                "amendment summary",
                "appendices",
                "appendix",
                "appendix maps",
                "assessment",
                "biological opinion",
                "decision",
                "eis",
                "errata",
                "executive summary",
                "feis",
                "final eis",
                "final eis volume",
                "map",
                "monitoring",
                "record of decision",
                "response-to-comments",
                "rod",
                "support",
                "transmittal",
            )
            if any(token in combined for token in support_tokens):
                return "forest_plan_support"
            return "forest_plan"
        if any(token in combined for token in ("public law", "u.s.c", "united states code", "statute")):
            return "law"
        if any(
            token in combined
            for token in (
                "cfr",
                "ecfr",
                "federal register",
                "final rule",
                "planning rule",
                "regulation",
            )
        ):
            return "regulation"
        if authority_tier == "state/partner":
            return "state_requirement"
        if "case" in combined or "court" in combined:
            return "case_law"
        if any(
            token in combined
            for token in (
                "agreement",
                "conservation strategy",
                "directive",
                "ecos report",
                "field guide",
                "forest order",
                "fsh",
                "fsm",
                "guidance",
                "handbook",
                "implementation plan",
                "letter",
                "manual",
                "monitoring guidance",
                "order",
                "outline",
                "page",
                "policy",
                "program page",
                "recovery plan",
                "regional soil handbook",
                "report",
                "rationale",
                "scc",
                "standard",
                "strategy",
                "technical",
            )
        ):
            return "agency_policy"
        if authority_tier in {"federal", "programmatic", "region", "usda", "usfs", "superseded"}:
            return "agency_policy"
    if source.metadata.get("source_input") == "r1_forest_plan_document_register":
        if source.source_record_id in _r1_forest_plan_register_primary_plan_source_record_ids():
            return "forest_plan"
        return "forest_plan_support"
    if source.sheet == "R1_Forest_Plans":
        return "forest_plan"
    value = (document_type or "").lower()
    title = source.title.lower()
    if "executive order" in value or "executive order" in title:
        return "executive_order"
    if "federal register" in value or "final rule" in value or "final rule" in title:
        return "regulation"
    if "regulation" in value or "cfr" in title:
        return "regulation"
    if "directive" in value or "manual" in value or "supplement" in value:
        return "agency_policy"
    if "agency species page" in value or "agency page" in value:
        return "agency_policy"
    if "public law" in value:
        return "law"
    if "plan amendment" in value:
        return "agency_policy"
    if "statute" in value or "u.s.c" in title or "united states code" in title:
        return "law"
    if "state" in value:
        return "state_requirement"
    if "guidance" in value or "policy" in value or "manual" in title or "handbook" in title:
        return "agency_policy"
    if (
        "official project page" in value
        or "news release" in value
        or "repository" in value
        or "project page" in title
        or "news release" in title
        or "project documents" in title
    ):
        return "project_reference"
    if "case" in value or "court" in title:
        return "case_law"
    return "source_document"


@cache
def _r1_forest_plan_register_primary_plan_source_record_ids() -> frozenset[str]:
    try:
        payload = json.loads(
            DEFAULT_REGION1_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH.read_text(
                encoding="utf-8"
            )
        )
    except FileNotFoundError as exc:
        raise ValueError(
            "Missing Region 1 inventory build manifest for catalog role classification: "
            f"{DEFAULT_REGION1_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Invalid Region 1 inventory build manifest JSON for catalog role classification: "
            f"{DEFAULT_REGION1_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH}"
        ) from exc
    profile_rows = payload.get("profile_rows")
    if not isinstance(profile_rows, list):
        raise ValueError(
            "Region 1 inventory build manifest must contain a profile_rows list for "
            "catalog role classification."
        )
    primary_plan_source_record_ids = []
    for index, row in enumerate(profile_rows):
        if not isinstance(row, dict):
            raise ValueError(
                "Region 1 inventory build manifest.profile_rows entries must be objects for "
                "catalog role classification."
            )
        source_record_id = row.get("primary_plan_source_record_id")
        if not isinstance(source_record_id, str) or not source_record_id.strip():
            raise ValueError(
                "Region 1 inventory build manifest.profile_rows"
                f"[{index}].primary_plan_source_record_id must be a non-empty string for "
                "catalog role classification."
            )
        primary_plan_source_record_ids.append(source_record_id.strip())
    return frozenset(primary_plan_source_record_ids)


@cache
def _r1_forest_plan_manifest_primary_component_source_record_ids() -> frozenset[str]:
    try:
        payload = json.loads(
            DEFAULT_REGION1_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH.read_text(
                encoding="utf-8"
            )
        )
    except FileNotFoundError as exc:
        raise ValueError(
            "Missing Region 1 inventory build manifest for catalog role classification: "
            f"{DEFAULT_REGION1_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Invalid Region 1 inventory build manifest JSON for catalog role classification: "
            f"{DEFAULT_REGION1_FOREST_PLAN_INVENTORY_BUILD_MANIFEST_PATH}"
        ) from exc
    profile_rows = payload.get("profile_rows")
    if not isinstance(profile_rows, list):
        raise ValueError(
            "Region 1 inventory build manifest must contain a profile_rows list for "
            "catalog role classification."
        )
    primary_role_source_record_ids = []
    for index, row in enumerate(profile_rows):
        if not isinstance(row, dict):
            raise ValueError(
                "Region 1 inventory build manifest.profile_rows entries must be objects for "
                "catalog role classification."
            )
        raw_source_record_ids_by_role = row.get("build_source_record_ids_by_role")
        if not isinstance(raw_source_record_ids_by_role, dict):
            raise ValueError(
                "Region 1 inventory build manifest.profile_rows"
                f"[{index}].build_source_record_ids_by_role must be an object for "
                "catalog role classification."
            )
        for role in ("primary_land_management_plan", "primary_land_resource_management_plan_part"):
            raw_source_record_ids = raw_source_record_ids_by_role.get(role) or []
            if not isinstance(raw_source_record_ids, list):
                raise ValueError(
                    "Region 1 inventory build manifest.profile_rows"
                    f"[{index}].build_source_record_ids_by_role[{role!r}] must be a list for "
                    "catalog role classification."
                )
            for source_record_id in raw_source_record_ids:
                if not isinstance(source_record_id, str) or not source_record_id.strip():
                    raise ValueError(
                        "Region 1 inventory build manifest.profile_rows"
                        f"[{index}].build_source_record_ids_by_role[{role!r}] entries must be "
                        "non-empty strings for catalog role classification."
                    )
                primary_role_source_record_ids.append(source_record_id.strip())
    return frozenset(primary_role_source_record_ids)


def _authority_level(source: WorkbookSource, issuer: str | None, host: str) -> str:
    if source.metadata.get("loader_contract") == "source_register_v1":
        authority_document_class_id = (_clean(source.metadata.get("authority_document_class_id")) or "").lower()
        authority_tier = (_clean(source.metadata.get("authority_tier")) or "").lower()
        if authority_document_class_id == "forest_plan" or authority_tier == "forest":
            return "forest"
        tier_map = {
            "federal": "federal",
            "programmatic": "federal",
            "region": "regional",
            "state/partner": "state",
            "superseded": "federal",
            "usda": "federal",
            "usfs": "federal",
        }
        if authority_tier in tier_map:
            return tier_map[authority_tier]
    if source.metadata.get("source_input") == "r1_forest_plan_document_register":
        return "forest"
    if source.sheet == "R1_Forest_Plans":
        return "forest"
    value = (issuer or "").lower()
    if "region 1" in value:
        return "regional"
    state_tokens = ["montana", "idaho", "north dakota", "south dakota", "washington"]
    if any(token in value for token in state_tokens):
        return "state"
    if host.endswith(".mt.gov") or host.endswith(".idaho.gov") or host.endswith(".nd.gov"):
        return "state"
    if host.endswith(".sd.gov") or host.endswith(".wa.gov"):
        return "state"
    federal_tokens = ["congress", "president", "usda", "epa", "u.s.", "army corps"]
    if any(token in value for token in federal_tokens):
        return "federal"
    if host.endswith(".gov"):
        return "federal"
    return "unknown"


def _expected_parser(source: WorkbookSource, content_type: str | None) -> str:
    if content_type:
        if content_type == "application/zip":
            return "zip"
        if content_type == "application/pdf":
            return "pdf"
        if content_type == "application/msword":
            return "doc"
        if content_type in {"application/xml", "text/xml"}:
            return "xml"
        if content_type in {"text/html", "application/xhtml+xml"}:
            return "html"
        docx_content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if content_type == docx_content_type:
            return "docx"
        if content_type.startswith("image/"):
            return "image"
    path = urlsplit(source.effective_url).path.lower()
    host = urlsplit(source.normalized_url).netloc.lower()
    if path.endswith(".zip"):
        return "zip"
    if path.endswith(".pdf"):
        return "pdf"
    if path.endswith(".doc"):
        return "doc"
    if path.endswith(".xml"):
        return "xml"
    if path.endswith(".docx"):
        return "docx"
    if path.endswith((".jpg", ".jpeg", ".png")):
        return "image"
    if host in {"www.ecfr.gov", "www.federalregister.gov"}:
        return "structured_web_adapter"
    return "html"


def _review_topics(value: str | None) -> list[str]:
    if not value:
        return []
    parts = []
    for segment in value.replace("\r", "\n").replace(";", "\n").split("\n"):
        segment = " ".join(segment.split())
        if segment:
            parts.append(segment)
    return parts


def _citation_label(source: WorkbookSource, artifact_sha256: str | None) -> str:
    if artifact_sha256:
        return f"{source.source_record_id} ({artifact_sha256[:12]})"
    return source.source_record_id


def _from_manifest(record: dict | None, key: str):
    return record.get(key) if record else None


def _artifact_count(records: list[dict]) -> int:
    return len({record["artifact_sha256"] for record in records if record["artifact_sha256"]})


def _review_topic_count(records: list[dict]) -> int:
    return len({topic for record in records for topic in record["review_topics"]})


def _authority_count(records: list[dict]) -> int:
    return len({record["issuer"] for record in records if record["issuer"]})


def _first_nonempty(*values: str | None) -> str | None:
    for value in values:
        cleaned = _clean(value)
        if cleaned:
            return cleaned
    return None


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(str(value).split())
    return cleaned or None


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
