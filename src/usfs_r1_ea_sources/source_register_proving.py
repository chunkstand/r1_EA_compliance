from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from pathlib import Path
import json

from .catalog_surface import resolve_catalog_dir_for_source_set
from .catalog import build_review_catalog
from .config import DEFAULT_CONFIG_PATH
from .config import SOURCE_REGISTER_WORKBOOK_LOADER_CONTRACT
from .config import load_config
from .dry_run import new_run_id
from .preflight import run_preflight
from .records import sha256_file, slugify
from .source_register import (
    DEFAULT_CITATION_ALIAS_REGISTER_PATH,
    load_citation_alias_register,
    load_source_register_rows,
    read_source_register_tables,
)
from .source_register_proving_graph import _build_graph_summary, _validation_checks
from .source_register_proving_io import (
    DEFAULT_LATEST_PROVING_CONTEXT_RELATIVE_PATH,
    LATEST_PROVING_CONTEXT_SCHEMA_VERSION,
    _normalize_identity_text,
    _proving_fetcher,
    _read_jsonl,
    _write_json,
    _write_latest_context,
    _write_synthetic_download_run,
)


PROVING_SLICE_REPORT_SCHEMA_VERSION = "source-register-proving-slice-report-v1"
PROVING_SLICE_MANIFEST_SCHEMA_VERSION = "source-register-proving-slice-v1"
DEFAULT_SOURCE_REGISTER_PROVING_SLICE_MANIFEST_PATH = Path(
    "config/source_register_proving_slice_v1.json"
)
REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class SourceRegisterProvingResult:
    report_path: Path
    summary: dict


def load_source_register_proving_manifest(
    path: Path | str = DEFAULT_SOURCE_REGISTER_PROVING_SLICE_MANIFEST_PATH,
) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != PROVING_SLICE_MANIFEST_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported source-register proving-slice schema_version: "
            f"{payload.get('schema_version')!r}"
        )
    return payload


def build_source_register_proving_slice(
    *,
    workbook_path: Path,
    manifest_path: Path = DEFAULT_SOURCE_REGISTER_PROVING_SLICE_MANIFEST_PATH,
    output_dir: Path = Path("source_library"),
    config_path: Path = DEFAULT_CONFIG_PATH,
    report_path: Path | None = None,
) -> SourceRegisterProvingResult:
    workbook_path = Path(workbook_path)
    manifest_path = Path(manifest_path)
    output_dir = Path(output_dir)
    manifest = load_source_register_proving_manifest(manifest_path)
    rows = load_source_register_rows(workbook_path)
    tables = read_source_register_tables(workbook_path)
    queue_rows = list(
        (tables.get("Direct_File_Capture_Queue") or {}).get("rows", [])
    )
    rows_by_id = {row.source_record_id: row for row in rows}
    queue_rows_by_id = {str(row["Source_ID"]).strip(): row for row in queue_rows}
    load_source_record_ids = list(manifest.get("load_ready_source_record_ids", []))
    queue_source_record_ids = list(manifest.get("queue_source_record_ids", []))
    selected_rows = [rows_by_id[source_record_id] for source_record_id in load_source_record_ids]
    selected_queue_rows = [
        queue_rows_by_id[source_record_id] for source_record_id in queue_source_record_ids
    ]

    config = load_config(config_path)
    proving_config = replace(
        config,
        workbook=replace(
            config.workbook,
            loader_contract=SOURCE_REGISTER_WORKBOOK_LOADER_CONTRACT,
            overrides_path=None,
        ),
    )
    preflight_run_id = f"source-register-proving-preflight-{new_run_id()}"
    download_run_id = f"source-register-proving-download-{new_run_id()}"
    preflight_result = run_preflight(
        workbook_path=workbook_path,
        output_dir=output_dir,
        config=proving_config,
        run_id=preflight_run_id,
        source_record_ids=set(load_source_record_ids),
        fetcher=_proving_fetcher(selected_rows),
        sleep_fn=lambda _: None,
    )
    preflight_records = _read_jsonl(preflight_result.manifest_path)
    download_manifest_path = _write_synthetic_download_run(
        workbook_path=workbook_path,
        output_dir=output_dir,
        run_id=download_run_id,
        rows=selected_rows,
        preflight_records=preflight_records,
    )
    catalog_result = build_review_catalog(
        workbook_path=workbook_path,
        output_dir=output_dir,
        config=proving_config,
        config_path=config_path,
        run_id=download_run_id,
        source_record_ids=set(load_source_record_ids),
    )
    catalog_records = _read_jsonl(catalog_result.source_catalog_path)
    catalog_by_source_record_id = {
        str(record["source_record_id"]): record for record in catalog_records
    }
    proving_dir = (
        output_dir
        / "derived"
        / catalog_result.source_set_id
        / "source_register_proving"
    )
    proving_dir.mkdir(parents=True, exist_ok=True)
    authority_inventory_path = proving_dir / "authority_inventory.json"
    source_addition_decisions_path = proving_dir / "source_addition_decisions.json"
    relationships_path = proving_dir / "relationships.json"
    report_path = report_path or proving_dir / "proving_slice_report.json"

    authority_inventory = _build_authority_inventory(
        manifest=manifest,
        selected_rows=selected_rows,
        source_set_id=catalog_result.source_set_id,
    )
    source_addition_decisions = {
        "schema_version": "source-register-proving-source-addition-decisions-v1",
        "source_set_id": catalog_result.source_set_id,
        "decisions": [],
    }
    alias_report = _build_alias_report(
        manifest=manifest,
        selected_rows=selected_rows,
    )
    relationships = _build_relationships(
        manifest=manifest,
        rows_by_id=rows_by_id,
    )
    graph = _build_graph_summary(
        manifest=manifest,
        selected_rows=selected_rows,
        selected_queue_rows=selected_queue_rows,
        catalog_by_source_record_id=catalog_by_source_record_id,
        relationships=relationships,
        alias_report=alias_report,
        source_set_id=catalog_result.source_set_id,
    )

    checks = _validation_checks(
        manifest=manifest,
        selected_rows=selected_rows,
        selected_queue_rows=selected_queue_rows,
        alias_report=alias_report,
        relationships=relationships,
        graph=graph,
        preflight_result=preflight_result.summary,
        catalog_result=catalog_result.summary,
        download_manifest_path=download_manifest_path,
    )
    validation_passed = all(check["passed"] for check in checks)

    report = {
        "schema_version": PROVING_SLICE_REPORT_SCHEMA_VERSION,
        "created_at": preflight_result.summary["completed_at"],
        "workbook_path": str(workbook_path),
        "workbook_sha256": sha256_file(workbook_path),
        "manifest_path": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "source_set_id": catalog_result.source_set_id,
        "no_bulk_ingest_until_passed": True,
        "inputs": {
            "config_path": str(config_path),
            "config_sha256": sha256_file(config_path),
            "preflight_run_id": preflight_run_id,
            "preflight_manifest_path": str(preflight_result.manifest_path),
            "download_run_id": download_run_id,
            "download_manifest_path": str(download_manifest_path),
            "catalog_dir": str(catalog_result.catalog_dir),
            "source_catalog_path": str(catalog_result.source_catalog_path),
            "source_set_manifest_path": str(catalog_result.source_set_manifest_path),
            "authority_inventory_path": str(authority_inventory_path),
            "source_addition_decisions_path": str(source_addition_decisions_path),
            "citation_alias_register_path": str(DEFAULT_CITATION_ALIAS_REGISTER_PATH),
        },
        "slice": {
            "load_ready_source_record_ids": load_source_record_ids,
            "queue_source_record_ids": queue_source_record_ids,
            "load_ready_source_count": len(load_source_record_ids),
            "queue_source_count": len(queue_source_record_ids),
            "coverage_groups": manifest.get("coverage_groups", []),
            "supersession_expectations": manifest.get("supersession_expectations", []),
            "relationship_expectations": manifest.get("relationship_expectations", []),
        },
        "queue_rows": selected_queue_rows,
        "alias_report": alias_report,
        "semantic_relationships": {
            "relationship_count": len(relationships),
            "relationship_type_counts": dict(
                Counter(relationship["relationship_type"] for relationship in relationships)
            ),
            "path_pattern_counts": dict(
                Counter(relationship["path_pattern_id"] for relationship in relationships)
            ),
            "relationships": relationships,
        },
        "graph": graph,
        "validation": {
            "passed": validation_passed,
            "checks": checks,
        },
        "summary": {
            "validation_passed": validation_passed,
            "source_set_id": catalog_result.source_set_id,
            "load_ready_source_count": len(load_source_record_ids),
            "queue_source_count": len(queue_source_record_ids),
            "preflight_validation_passed": bool(
                preflight_result.summary.get("validation_passed")
            ),
            "catalog_validation_passed": bool(
                catalog_result.summary.get("validation_passed")
            ),
            "relationship_count": len(relationships),
            "graph_node_count": len(graph["nodes"]),
            "graph_edge_count": len(graph["edges"]),
            "orphan_node_count": len(graph["orphan_node_ids"]),
            "justification_path_count": len(graph["justification_paths"]),
            "report_path": str(report_path),
            "bulk_ingest_blocked": True,
        },
    }

    _write_json(authority_inventory_path, authority_inventory)
    _write_json(source_addition_decisions_path, source_addition_decisions)
    _write_json(relationships_path, {"relationships": relationships})
    _write_json(report_path, report)
    _write_latest_context(
        output_dir=output_dir,
        source_set_id=catalog_result.source_set_id,
        report_path=report_path,
        catalog_dir=catalog_result.catalog_dir,
        source_catalog_path=catalog_result.source_catalog_path,
        source_set_manifest_path=catalog_result.source_set_manifest_path,
        authority_inventory_path=authority_inventory_path,
        source_addition_decisions_path=source_addition_decisions_path,
    )
    return SourceRegisterProvingResult(
        report_path=report_path,
        summary=report["summary"],
    )


def resolve_latest_proving_context(output_dir: Path) -> dict:
    output_dir = Path(output_dir)
    context_path = output_dir / DEFAULT_LATEST_PROVING_CONTEXT_RELATIVE_PATH
    if not context_path.exists():
        raise FileNotFoundError(
            "Missing source-register proving context. Run "
            "`source-register-proving-slice` first."
        )
    payload = json.loads(context_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != LATEST_PROVING_CONTEXT_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported source-register proving context schema_version: "
            f"{payload.get('schema_version')!r}"
        )
    return payload


def resolve_authority_currentness_inputs(
    *,
    output_dir: Path,
    source_set_id: str | None,
    authority_inventory_path: Path,
    source_addition_decisions_path: Path,
    catalog_path: Path | None,
    source_set_manifest_path: Path | None,
) -> dict:
    if source_set_id or catalog_path or source_set_manifest_path:
        return {
            "source_set_id": source_set_id,
            "authority_inventory_path": authority_inventory_path,
            "source_addition_decisions_path": source_addition_decisions_path,
            "catalog_path": catalog_path,
            "source_set_manifest_path": source_set_manifest_path,
        }
    defaults_used = (
        authority_inventory_path == Path("config/authority_universe_families_nepa_ea_v1.json")
        and source_addition_decisions_path
        == Path("config/authority_source_addition_decisions_nepa_ea_v1.json")
    )
    if not defaults_used:
        return {
            "source_set_id": source_set_id,
            "authority_inventory_path": authority_inventory_path,
            "source_addition_decisions_path": source_addition_decisions_path,
            "catalog_path": catalog_path,
            "source_set_manifest_path": source_set_manifest_path,
        }
    active_manifest_path = Path(output_dir) / "catalog" / "source_set_manifest.json"
    active_catalog_path = Path(output_dir) / "catalog" / "source_catalog.jsonl"
    if active_manifest_path.exists() and active_catalog_path.exists():
        active_manifest = json.loads(active_manifest_path.read_text(encoding="utf-8"))
        active_rows = [
            json.loads(line)
            for line in active_catalog_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        if any(
            str((row.get("metadata") or {}).get("loader_contract") or "") == "source_register_v1"
            for row in active_rows
        ):
            return {
                "source_set_id": str(active_manifest.get("source_set_id") or ""),
                "authority_inventory_path": authority_inventory_path,
                "source_addition_decisions_path": source_addition_decisions_path,
                "catalog_path": active_catalog_path,
                "source_set_manifest_path": active_manifest_path,
            }
    context = resolve_latest_proving_context(output_dir)
    return {
        "source_set_id": context["source_set_id"],
        "authority_inventory_path": Path(context["authority_inventory_path"]),
        "source_addition_decisions_path": Path(context["source_addition_decisions_path"]),
        "catalog_path": Path(context["source_catalog_path"]),
        "source_set_manifest_path": Path(context["source_set_manifest_path"]),
    }


def load_proving_report(output_dir: Path, report_path: Path | None = None) -> dict:
    if report_path is not None:
        path = Path(report_path)
    else:
        context = resolve_latest_proving_context(output_dir)
        path = Path(context["report_path"])
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != PROVING_SLICE_REPORT_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported source-register proving report schema_version: "
            f"{payload.get('schema_version')!r}"
        )
    return payload


def build_source_set_semantic_proving_report(
    *,
    output_dir: Path,
    source_set_id: str,
    manifest_path: Path = DEFAULT_SOURCE_REGISTER_PROVING_SLICE_MANIFEST_PATH,
    source_set_manifest_path: Path | None = None,
    catalog_path: Path | None = None,
    report_path: Path | None = None,
) -> SourceRegisterProvingResult:
    output_dir = Path(output_dir)
    manifest_path = Path(manifest_path)
    explicit_catalog_dir = None
    if catalog_path is not None:
        explicit_catalog_dir = Path(catalog_path).parent
    elif source_set_manifest_path is not None:
        explicit_catalog_dir = Path(source_set_manifest_path).parent
    catalog_dir = resolve_catalog_dir_for_source_set(
        output_dir=output_dir,
        source_set_id=source_set_id,
        catalog_dir=explicit_catalog_dir,
    )
    resolved_source_set_manifest_path = (
        Path(source_set_manifest_path)
        if source_set_manifest_path is not None
        else catalog_dir / "source_set_manifest.json"
    )
    resolved_catalog_path = (
        Path(catalog_path) if catalog_path is not None else catalog_dir / "source_catalog.jsonl"
    )
    manifest = load_source_register_proving_manifest(manifest_path)
    source_set_manifest = json.loads(
        resolved_source_set_manifest_path.read_text(encoding="utf-8")
    )
    workbook_path = _workbook_path_from_source_set_manifest(
        source_set_manifest=source_set_manifest,
        source_set_manifest_path=resolved_source_set_manifest_path,
    )
    workbook_rows = load_source_register_rows(workbook_path)
    workbook_rows_by_id = {row.source_record_id: row for row in workbook_rows}
    catalog_rows = _read_jsonl(resolved_catalog_path)
    catalog_source_record_ids = {
        str(row.get("source_record_id") or "")
        for row in catalog_rows
        if str(row.get("source_set_id") or source_set_id) == source_set_id
        and str(row.get("source_record_id") or "").strip()
    }
    load_ready_source_record_ids = [
        str(source_record_id)
        for source_record_id in manifest.get("load_ready_source_record_ids", [])
        if str(source_record_id or "").strip()
    ]
    queue_source_record_ids = [
        str(source_record_id)
        for source_record_id in manifest.get("queue_source_record_ids", [])
        if str(source_record_id or "").strip()
    ]
    missing_workbook_source_record_ids = sorted(
        source_record_id
        for source_record_id in load_ready_source_record_ids
        if source_record_id not in workbook_rows_by_id
    )
    missing_catalog_source_record_ids = sorted(
        source_record_id
        for source_record_id in load_ready_source_record_ids
        if source_record_id not in catalog_source_record_ids
    )
    selected_rows = [
        workbook_rows_by_id[source_record_id]
        for source_record_id in load_ready_source_record_ids
        if source_record_id in workbook_rows_by_id
    ]
    relationships = _build_relationships(
        manifest=manifest,
        rows_by_id=workbook_rows_by_id,
    )
    alias_report = _build_alias_report(
        manifest=manifest,
        selected_rows=selected_rows,
    )
    validation_checks = [
        {
            "name": "source_set_manifest_source_set_matches",
            "passed": str(source_set_manifest.get("source_set_id") or "") == source_set_id,
            "expected": source_set_id,
            "actual": source_set_manifest.get("source_set_id"),
        },
        {
            "name": "semantic_proving_slice_load_ready_rows_present_in_workbook",
            "passed": not missing_workbook_source_record_ids,
            "expected": [],
            "actual": missing_workbook_source_record_ids,
        },
        {
            "name": "semantic_proving_slice_load_ready_rows_present_in_catalog",
            "passed": not missing_catalog_source_record_ids,
            "expected": [],
            "actual": missing_catalog_source_record_ids,
        },
    ]
    validation_passed = all(check["passed"] for check in validation_checks)
    resolved_report_path = (
        Path(report_path)
        if report_path is not None
        else output_dir
        / "derived"
        / source_set_id
        / "source_register_proving"
        / "proving_slice_report.json"
    )
    relationships_path = resolved_report_path.parent / "relationships.json"
    report = {
        "schema_version": PROVING_SLICE_REPORT_SCHEMA_VERSION,
        "source_set_id": source_set_id,
        "manifest_path": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "workbook_path": str(workbook_path),
        "workbook_sha256": sha256_file(workbook_path),
        "inputs": {
            "catalog_dir": str(catalog_dir),
            "source_catalog_path": str(resolved_catalog_path),
            "source_set_manifest_path": str(resolved_source_set_manifest_path),
        },
        "slice": {
            "load_ready_source_record_ids": load_ready_source_record_ids,
            "queue_source_record_ids": queue_source_record_ids,
            "load_ready_source_count": len(load_ready_source_record_ids),
            "queue_source_count": len(queue_source_record_ids),
            "coverage_groups": manifest.get("coverage_groups", []),
            "supersession_expectations": manifest.get("supersession_expectations", []),
            "relationship_expectations": manifest.get("relationship_expectations", []),
        },
        "alias_report": alias_report,
        "semantic_relationships": {
            "relationship_count": len(relationships),
            "relationship_type_counts": dict(
                Counter(relationship["relationship_type"] for relationship in relationships)
            ),
            "path_pattern_counts": dict(
                Counter(relationship["path_pattern_id"] for relationship in relationships)
            ),
            "relationships": relationships,
        },
        "validation": {
            "passed": validation_passed,
            "checks": validation_checks,
        },
        "summary": {
            "validation_passed": validation_passed,
            "source_set_id": source_set_id,
            "load_ready_source_count": len(load_ready_source_record_ids),
            "relationship_count": len(relationships),
            "report_path": str(resolved_report_path),
        },
    }
    _write_json(relationships_path, {"relationships": relationships})
    _write_json(resolved_report_path, report)
    return SourceRegisterProvingResult(
        report_path=resolved_report_path,
        summary=report["summary"],
    )


def default_proving_output_path(output_dir: Path, filename: str) -> Path:
    context = resolve_latest_proving_context(output_dir)
    report_path = Path(context["report_path"])
    return report_path.parent / filename


def _workbook_path_from_source_set_manifest(
    *,
    source_set_manifest: dict,
    source_set_manifest_path: Path,
) -> Path:
    workbook_path_value = str(source_set_manifest.get("workbook_path") or "").strip()
    if not workbook_path_value:
        raise FileNotFoundError(
            "source_set_manifest.json is missing workbook_path for semantic proving reuse: "
            f"{source_set_manifest_path}"
        )
    workbook_path = Path(workbook_path_value)
    if not workbook_path.is_absolute():
        workbook_path = REPO_ROOT / workbook_path
    if not workbook_path.exists():
        raise FileNotFoundError(
            "Workbook declared by source-set manifest does not exist: "
            f"{workbook_path}"
        )
    return workbook_path


def _build_authority_inventory(
    *,
    manifest: dict,
    selected_rows: list,
    source_set_id: str,
) -> dict:
    family_rows: dict[str, list] = defaultdict(list)
    family_status: dict[str, str] = {}
    supersession_map = {
        str(entry["source_record_id"]): str(entry["replacement_source_record_id"])
        for entry in manifest.get("supersession_expectations", [])
    }
    family_id_by_source_record_id: dict[str, str] = {}
    for row in selected_rows:
        family_id = f"proving_family:{slugify(row.authority_document_id, max_length=96)}"
        family_rows[family_id].append(row)
        family_id_by_source_record_id[row.source_record_id] = family_id
        family_status[family_id] = (
            "superseded"
            if row.source_record_id in supersession_map or row.authority_tier == "Superseded"
            else "source_only"
        )

    authority_families = []
    for family_id, rows in sorted(family_rows.items()):
        source_record_ids = [row.source_record_id for row in rows]
        family = {
            "family_id": family_id,
            "status": family_status[family_id],
            "authority_document_ids": sorted({row.authority_document_id for row in rows}),
            "source_record_ids": source_record_ids,
            "open_inventory_gaps": [],
        }
        superseded_source_ids = [
            source_record_id
            for source_record_id in source_record_ids
            if source_record_id in supersession_map
        ]
        if superseded_source_ids:
            replacement_source_record_id = supersession_map[superseded_source_ids[0]]
            family["supersession"] = {
                "replacement_family_id": family_id_by_source_record_id[
                    replacement_source_record_id
                ],
                "current_source_record_ids": [replacement_source_record_id],
            }
        authority_families.append(family)

    return {
        "schema_version": "source-register-proving-authority-inventory-v1",
        "source_set": {"source_set_id": source_set_id},
        "summary": {
            "authority_family_count": len(authority_families),
            "families_requiring_milestone_2_source_currentness": 0,
        },
        "authority_families": authority_families,
    }


def _build_alias_report(*, manifest: dict, selected_rows: list) -> dict:
    alias_register = load_citation_alias_register()
    blocked_terms = {
        _normalize_identity_text(term)
        for term in alias_register.get("ambiguity_policy", {}).get("blocked_without_context", [])
    }
    rows = []
    identity_key_to_authority_ids: dict[str, set[str]] = defaultdict(set)
    collisions = []
    for row in selected_rows:
        candidate_texts = [
            value
            for value in (row.citation_or_code, row.title)
            if value
        ]
        normalized_candidates = [
            _normalize_identity_text(value) for value in candidate_texts if value
        ]
        blocked_alias_terms = [
            blocked_term
            for blocked_term in sorted(blocked_terms)
            if any(blocked_term in candidate for candidate in normalized_candidates)
        ]
        context_fields_present = {
            "issuing_entity": bool(row.issuing_entity),
            "jurisdiction_or_unit": bool(row.jurisdiction_or_unit),
            "issue_or_effective_date": bool(row.issue_or_effective_date),
        }
        identity_key = "|".join(
            [
                _normalize_identity_text(row.title),
                _normalize_identity_text(row.citation_or_code),
                _normalize_identity_text(row.issuing_entity),
                _normalize_identity_text(row.jurisdiction_or_unit),
            ]
        )
        identity_key_to_authority_ids[identity_key].add(row.authority_document_id)
        rows.append(
            {
                "source_record_id": row.source_record_id,
                "candidate_texts": candidate_texts,
                "blocked_alias_terms": blocked_alias_terms,
                "context_fields_present": context_fields_present,
                "authority_document_id": row.authority_document_id,
                "authority_document_class_id": row.authority_document_class_id,
                "identity_key": identity_key,
                "resolved_with_context": bool(blocked_alias_terms) and any(
                    context_fields_present.values()
                ),
            }
        )
    for identity_key, authority_document_ids in sorted(identity_key_to_authority_ids.items()):
        if len(authority_document_ids) > 1:
            collisions.append(
                {
                    "identity_key": identity_key,
                    "authority_document_ids": sorted(authority_document_ids),
                }
            )
    alias_expectations = manifest.get("alias_expectations", [])
    expected_source_record_ids = {entry["source_record_id"] for entry in alias_expectations}
    expectation_rows = [
        row for row in rows if row["source_record_id"] in expected_source_record_ids
    ]
    return {
        "row_count": len(rows),
        "blocked_alias_row_count": sum(1 for row in rows if row["blocked_alias_terms"]),
        "identity_collision_count": len(collisions),
        "identity_collisions": collisions,
        "rows": rows,
        "expected_rows": expectation_rows,
    }


def _build_relationships(*, manifest: dict, rows_by_id: dict[str, object]) -> list[dict]:
    relationships = []
    for expectation in manifest.get("relationship_expectations", []):
        source_row = rows_by_id[str(expectation["source_source_record_id"])]
        target_source_record_id = expectation.get("target_source_record_id")
        if target_source_record_id:
            target_row = rows_by_id[str(target_source_record_id)]
            target_id = target_row.authority_document_id
            target_class_id = target_row.authority_document_class_id
            supporting_source_record_ids = sorted(
                {
                    source_row.source_record_id,
                    target_row.source_record_id,
                    *expectation.get("supporting_source_record_ids", []),
                }
            )
        elif expectation.get("target_scope_id"):
            target_id = str(expectation["target_scope_id"])
            target_class_id = "jurisdiction_scope"
            supporting_source_record_ids = [source_row.source_record_id]
        elif expectation.get("target_forest_unit_id"):
            target_id = str(expectation["target_forest_unit_id"])
            target_class_id = "forest_unit"
            supporting_source_record_ids = [source_row.source_record_id]
        else:
            raise ValueError(
                "Relationship expectation must define target_source_record_id, "
                "target_scope_id, or target_forest_unit_id."
            )
        relationships.append(
            {
                "relationship_id": str(expectation["relationship_id"]),
                "source_id": source_row.authority_document_id,
                "source_class_id": source_row.authority_document_class_id,
                "relationship_type": str(expectation["relationship_type"]),
                "target_id": target_id,
                "target_class_id": target_class_id,
                "status": "proving_slice_verified",
                "evidence_basis_type": str(expectation["evidence_basis_type"]),
                "relationship_basis": str(expectation["relationship_basis"]),
                "supporting_source_record_ids": supporting_source_record_ids,
                "path_pattern_id": str(expectation["path_pattern_id"]),
            }
        )
    return relationships
