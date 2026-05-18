from __future__ import annotations

from collections import Counter, defaultdict, deque
from dataclasses import dataclass, replace
from pathlib import Path
import json
import re

from .catalog import build_review_catalog
from .config import DEFAULT_CONFIG_PATH
from .config import SOURCE_REGISTER_WORKBOOK_LOADER_CONTRACT
from .config import load_config
from .dry_run import new_run_id
from .preflight import PreflightFetchResult
from .preflight import run_preflight
from .records import planned_artifact_path, sha256_file, slugify
from .source_register import (
    DEFAULT_CITATION_ALIAS_REGISTER_PATH,
    load_citation_alias_register,
    load_source_register_rows,
    read_source_register_tables,
)


PROVING_SLICE_REPORT_SCHEMA_VERSION = "source-register-proving-slice-report-v1"
PROVING_SLICE_MANIFEST_SCHEMA_VERSION = "source-register-proving-slice-v1"
LATEST_PROVING_CONTEXT_SCHEMA_VERSION = "source-register-proving-context-v1"
DEFAULT_SOURCE_REGISTER_PROVING_SLICE_MANIFEST_PATH = Path(
    "config/source_register_proving_slice_v1.json"
)
DEFAULT_LATEST_PROVING_CONTEXT_RELATIVE_PATH = Path(
    "derived/source_register_proving/latest_context.json"
)


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


def default_proving_output_path(output_dir: Path, filename: str) -> Path:
    context = resolve_latest_proving_context(output_dir)
    report_path = Path(context["report_path"])
    return report_path.parent / filename


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


def _build_graph_summary(
    *,
    manifest: dict,
    selected_rows: list,
    selected_queue_rows: list[dict],
    catalog_by_source_record_id: dict[str, dict],
    relationships: list[dict],
    alias_report: dict,
    source_set_id: str,
) -> dict:
    nodes: dict[str, dict] = {}
    edges: dict[str, dict] = {}
    source_set_node_id = f"source_set:{source_set_id}"
    nodes[source_set_node_id] = {
        "node_id": source_set_node_id,
        "class_id": "source_set",
        "label": source_set_id,
    }
    justification_paths = []
    authority_paths = []

    for row in selected_rows:
        catalog_row = catalog_by_source_record_id[row.source_record_id]
        source_record_node_id = f"source_record:{row.source_record_id}"
        nodes[source_record_node_id] = {
            "node_id": source_record_node_id,
            "class_id": "source_record",
            "label": row.title,
            "source_record_id": row.source_record_id,
        }
        _add_edge(edges, source_set_node_id, source_record_node_id, "IN_SOURCE_SET")
        authority_node_id = row.authority_document_id
        nodes.setdefault(
            authority_node_id,
            {
                "node_id": authority_node_id,
                "class_id": row.authority_document_class_id,
                "label": row.title,
            },
        )
        _add_edge(edges, source_record_node_id, authority_node_id, "CAPTURES_AUTHORITY")
        if row.authority_section_id:
            nodes.setdefault(
                row.authority_section_id,
                {
                    "node_id": row.authority_section_id,
                    "class_id": "authority_section",
                    "label": row.authority_section_id,
                },
            )
            _add_edge(edges, authority_node_id, row.authority_section_id, "HAS_SECTION")
        nodes.setdefault(
            row.jurisdiction_scope_id,
            {
                "node_id": row.jurisdiction_scope_id,
                "class_id": "jurisdiction_scope",
                "label": row.jurisdiction_scope_id,
            },
        )
        _add_edge(edges, authority_node_id, row.jurisdiction_scope_id, "APPLIES_WITHIN_SCOPE")
        artifact_sha256 = str(catalog_row.get("artifact_sha256") or "")
        artifact_node_id = f"source_artifact:{artifact_sha256}"
        nodes[artifact_node_id] = {
            "node_id": artifact_node_id,
            "class_id": "source_artifact",
            "label": artifact_sha256[:12],
            "artifact_sha256": artifact_sha256,
        }
        _add_edge(edges, source_record_node_id, artifact_node_id, "HAS_ARTIFACT")
        evidence_span_node_id = f"evidence_span:{row.source_record_id}:0"
        nodes[evidence_span_node_id] = {
            "node_id": evidence_span_node_id,
            "class_id": "evidence_span",
            "label": f"{row.source_record_id} proving evidence span",
            "source_record_id": row.source_record_id,
        }
        _add_edge(edges, artifact_node_id, evidence_span_node_id, "HAS_EVIDENCE_SPAN")
        if row.authority_document_class_id == "forest_plan" and row.jurisdiction_or_unit:
            forest_unit_id = _forest_unit_id(row.jurisdiction_or_unit)
            nodes.setdefault(
                forest_unit_id,
                {
                    "node_id": forest_unit_id,
                    "class_id": "forest_unit",
                    "label": row.jurisdiction_or_unit,
                },
            )
            _add_edge(edges, authority_node_id, forest_unit_id, "GOVERNS_FOREST_UNIT")

    for relationship in relationships:
        _add_edge(
            edges,
            relationship["source_id"],
            relationship["target_id"],
            relationship["relationship_type"],
        )
        authority_path_id = f"authority_path:{relationship['relationship_id']}"
        justification_path_id = f"justification_path:{relationship['relationship_id']}"
        nodes[authority_path_id] = {
            "node_id": authority_path_id,
            "class_id": "authority_path",
            "label": relationship["relationship_id"],
            "path_pattern_id": relationship["path_pattern_id"],
        }
        nodes[justification_path_id] = {
            "node_id": justification_path_id,
            "class_id": "justification_path",
            "label": relationship["relationship_id"],
        }
        _add_edge(edges, authority_path_id, relationship["source_id"], "PATH_SOURCE")
        _add_edge(edges, authority_path_id, relationship["target_id"], "PATH_TARGET")
        _add_edge(
            edges,
            justification_path_id,
            authority_path_id,
            "JUSTIFIES_AUTHORITY_PATH",
        )
        supporting_source_record_id = relationship["supporting_source_record_ids"][0]
        catalog_row = catalog_by_source_record_id[supporting_source_record_id]
        artifact_sha256 = str(catalog_row.get("artifact_sha256") or "")
        artifact_node_id = f"source_artifact:{artifact_sha256}"
        evidence_span_node_id = f"evidence_span:{supporting_source_record_id}:0"
        source_record_node_id = f"source_record:{supporting_source_record_id}"
        _add_edge(
            edges,
            justification_path_id,
            source_record_node_id,
            "HAS_SOURCE_RECORD",
        )
        _add_edge(
            edges,
            justification_path_id,
            artifact_node_id,
            "HAS_SOURCE_ARTIFACT",
        )
        _add_edge(
            edges,
            justification_path_id,
            evidence_span_node_id,
            "HAS_EVIDENCE_SPAN",
        )
        authority_paths.append(
            {
                "authority_path_id": authority_path_id,
                "relationship_id": relationship["relationship_id"],
                "path_pattern_id": relationship["path_pattern_id"],
                "source_id": relationship["source_id"],
                "target_id": relationship["target_id"],
            }
        )
        justification_paths.append(
            {
                "justification_path_id": justification_path_id,
                "authority_path_id": authority_path_id,
                "relationship_id": relationship["relationship_id"],
                "source_record_id": supporting_source_record_id,
                "artifact_sha256": artifact_sha256,
                "evidence_span_id": evidence_span_node_id,
                "conclusion": "source-register-proving-slice",
            }
        )

    orphan_node_ids = _orphan_node_ids(nodes=list(nodes.values()), edges=list(edges.values()))
    disconnected_components = _disconnected_components(
        nodes=list(nodes.values()),
        edges=list(edges.values()),
    )
    relationship_type_counts = Counter(
        relationship["relationship_type"] for relationship in relationships
    )
    lens_metadata = [
        {
            "lens_id": "source-provenance",
            "node_class_ids": ["source_record", "source_artifact", "evidence_span"],
            "edge_types": [
                "IN_SOURCE_SET",
                "HAS_ARTIFACT",
                "HAS_EVIDENCE_SPAN",
                "HAS_SOURCE_RECORD",
                "HAS_SOURCE_ARTIFACT",
            ],
        },
        {
            "lens_id": "authority-currentness",
            "node_class_ids": ["authority_document", "forest_plan", "jurisdiction_scope"],
            "edge_types": ["APPLIES_WITHIN_SCOPE", "SUPERSEDES"],
        },
        {
            "lens_id": "forest-plan-lineage",
            "node_class_ids": ["forest_plan", "forest_unit", "authority_path"],
            "edge_types": [
                "REQUIRES_CONSISTENCY_WITH",
                "GOVERNS_FOREST_UNIT",
                "PATH_SOURCE",
                "PATH_TARGET",
            ],
        },
        {
            "lens_id": "package-applicability",
            "node_class_ids": ["jurisdiction_scope", "authority_document", "forest_plan"],
            "edge_types": ["APPLIES_WITHIN_SCOPE"],
        },
        {
            "lens_id": "evidence-path",
            "node_class_ids": [
                "authority_path",
                "justification_path",
                "source_artifact",
                "evidence_span",
            ],
            "edge_types": [
                "JUSTIFIES_AUTHORITY_PATH",
                "HAS_SOURCE_RECORD",
                "HAS_SOURCE_ARTIFACT",
                "HAS_EVIDENCE_SPAN",
            ],
        },
        {
            "lens_id": "readiness-blockers",
            "queue_source_record_ids": [row["Source_ID"] for row in selected_queue_rows],
            "blocked_alias_row_ids": [
                row["source_record_id"]
                for row in alias_report["rows"]
                if row["blocked_alias_terms"]
            ],
            "edge_types": [],
            "node_class_ids": [],
        },
    ]
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "relationship_type_counts": dict(relationship_type_counts),
        "node_class_counts": dict(
            Counter(node["class_id"] for node in nodes.values())
        ),
        "nodes": list(nodes.values()),
        "edges": list(edges.values()),
        "authority_paths": authority_paths,
        "justification_paths": justification_paths,
        "orphan_node_ids": orphan_node_ids,
        "disconnected_components": disconnected_components,
        "lens_metadata": lens_metadata,
    }


def _validation_checks(
    *,
    manifest: dict,
    selected_rows: list,
    selected_queue_rows: list[dict],
    alias_report: dict,
    relationships: list[dict],
    graph: dict,
    preflight_result: dict,
    catalog_result: dict,
    download_manifest_path: Path,
) -> list[dict]:
    coverage_checks = []
    rows_by_id = {row.source_record_id: row for row in selected_rows}
    queue_by_id = {str(row["Source_ID"]).strip(): row for row in selected_queue_rows}
    for group in manifest.get("coverage_groups", []):
        group_id = str(group["coverage_id"])
        selected_ids = [str(source_record_id) for source_record_id in group["source_record_ids"]]
        if group.get("row_state") == "queue":
            entries = [queue_by_id[source_record_id] for source_record_id in selected_ids]
            actual_value = sorted({str(entry.get("URL_Class") or "") for entry in entries})
            expected_value = sorted(group.get("expected_url_classes", []))
            passed = set(expected_value).issubset(set(actual_value))
        else:
            entries = [rows_by_id[source_record_id] for source_record_id in selected_ids]
            expected_parser_classes = set(group.get("expected_parser_admission_classes", []))
            actual_parser_classes = {entry.parser_admission_class for entry in entries}
            expected_parsers = set(group.get("expected_expected_parsers", []))
            actual_parsers = {entry.expected_parser for entry in entries}
            expected_tiers = set(group.get("expected_authority_tiers", []))
            actual_tiers = {entry.authority_tier for entry in entries}
            passed = (
                (not expected_parser_classes or expected_parser_classes.issubset(actual_parser_classes))
                and (not expected_parsers or expected_parsers.issubset(actual_parsers))
                and (not expected_tiers or expected_tiers.issubset(actual_tiers))
            )
            actual_value = {
                "authority_tiers": sorted(actual_tiers),
                "expected_parsers": sorted(actual_parsers),
                "parser_admission_classes": sorted(actual_parser_classes),
            }
            expected_value = {
                "authority_tiers": sorted(expected_tiers),
                "expected_parsers": sorted(expected_parsers),
                "parser_admission_classes": sorted(expected_parser_classes),
            }
        coverage_checks.append(
            _check(
                f"coverage_group_{group_id}",
                passed,
                expected_value,
                actual_value,
            )
        )
    expected_alias_rows = {
        str(entry["source_record_id"]) for entry in manifest.get("alias_expectations", [])
    }
    resolved_alias_rows = {
        row["source_record_id"]
        for row in alias_report["expected_rows"]
        if row["resolved_with_context"]
    }
    return [
        _check(
            "load_ready_slice_has_expected_row_count",
            24 <= len(selected_rows) <= 40,
            "24-40",
            len(selected_rows),
        ),
        _check(
            "queue_slice_has_expected_rows",
            bool(selected_queue_rows),
            True,
            bool(selected_queue_rows),
        ),
        *coverage_checks,
        _check(
            "alias_stress_rows_resolve_with_context",
            expected_alias_rows == resolved_alias_rows,
            sorted(expected_alias_rows),
            sorted(resolved_alias_rows),
        ),
        _check(
            "identity_keys_do_not_collide",
            alias_report["identity_collision_count"] == 0,
            0,
            alias_report["identity_collision_count"],
        ),
        _check(
            "relationship_expectations_materialized",
            len(relationships) == len(manifest.get("relationship_expectations", [])),
            len(manifest.get("relationship_expectations", [])),
            len(relationships),
        ),
        _check(
            "preflight_contract_passed",
            bool(preflight_result.get("validation_passed")),
            True,
            preflight_result.get("validation_passed"),
        ),
        _check(
            "synthetic_download_manifest_written",
            download_manifest_path.exists(),
            True,
            download_manifest_path.exists(),
        ),
        _check(
            "catalog_validation_passed",
            bool(catalog_result.get("validation_passed")),
            True,
            catalog_result.get("validation_passed"),
        ),
        _check(
            "graph_has_no_orphans",
            not graph["orphan_node_ids"],
            [],
            graph["orphan_node_ids"],
        ),
        _check(
            "graph_has_single_connected_component",
            len(graph["disconnected_components"]) == 1,
            1,
            len(graph["disconnected_components"]),
        ),
    ]


def _write_synthetic_download_run(
    *,
    workbook_path: Path,
    output_dir: Path,
    run_id: str,
    rows: list,
    preflight_records: list[dict],
) -> Path:
    run_dir = output_dir / "runs" / run_id
    manifest_dir = output_dir / "manifests"
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    rows_by_id = {row.source_record_id: row for row in rows}
    artifact_details_by_source_record_id: dict[str, dict] = {}
    records = []
    workbook_sha256 = sha256_file(workbook_path)
    for preflight_record in preflight_records:
        source_record_id = str(preflight_record["source_record_id"])
        row = rows_by_id[source_record_id]
        source = row.to_workbook_source()
        status = str(preflight_record["status"])
        if status not in {"preflight_ok", "duplicate_url"}:
            raise ValueError(
                "Proving slice preflight produced non-admissible status for "
                f"{source_record_id}: {status!r}"
            )
        if status == "duplicate_url":
            duplicate_of = str(preflight_record["duplicate_of"] or "")
            if duplicate_of not in artifact_details_by_source_record_id:
                raise ValueError(
                    "Duplicate preflight record referenced missing primary source: "
                    f"{source_record_id} -> {duplicate_of}"
                )
            artifact_details = artifact_details_by_source_record_id[duplicate_of]
            record_status = "duplicate_url"
        else:
            artifact_path = planned_artifact_path(output_dir, source)
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_bytes = json.dumps(
                {
                    "schema_version": "source-register-proving-artifact-v1",
                    "source_record_id": source_record_id,
                    "title": row.title,
                    "expected_parser": row.expected_parser,
                    "parser_admission_class": row.parser_admission_class,
                    "authority_document_id": row.authority_document_id,
                    "direct_file_readiness_class": row.direct_file_readiness_class,
                    "original_url": row.original_url,
                },
                indent=2,
                sort_keys=True,
            ).encode("utf-8")
            artifact_path.write_bytes(artifact_bytes)
            artifact_details = {
                "artifact_path": str(artifact_path),
                "artifact_sha256": sha256_file(artifact_path),
                "artifact_byte_size": artifact_path.stat().st_size,
                "content_type": _content_type_for_parser(row.expected_parser),
            }
            artifact_details_by_source_record_id[source_record_id] = artifact_details
            record_status = "downloaded_existing"
        records.append(
            {
                "run_id": run_id,
                "source_record_id": source_record_id,
                "workbook_path": str(workbook_path),
                "workbook_sha256": workbook_sha256,
                "sheet": source.sheet,
                "excel_row": source.excel_row,
                "source_id": source.source_id,
                "title": source.title,
                "original_url": source.original_url,
                "effective_url": source.effective_url,
                "normalized_url": source.normalized_url,
                "final_url": preflight_record["final_url"],
                "redirect_chain": preflight_record["redirect_chain"],
                "status": record_status,
                "planned_artifact_path": str(planned_artifact_path(output_dir, source)),
                "artifact_path": artifact_details["artifact_path"],
                "artifact_sha256": artifact_details["artifact_sha256"],
                "artifact_byte_size": artifact_details["artifact_byte_size"],
                "content_type": artifact_details["content_type"],
                "content_length": preflight_record.get("content_length"),
                "http_status": 200,
                "attempt_count": 1,
                "fetch_timestamp": preflight_record.get("fetch_timestamp"),
                "validation": {
                    "mode": "source-register-proving-slice",
                    "passed": True,
                    "reason": "Synthetic proving artifact created from canonical row contract.",
                },
                "duplicate_of": preflight_record.get("duplicate_of"),
                "failure": None,
                "metadata": source.metadata,
            }
        )
    manifest_path = manifest_dir / f"download_{run_id}.jsonl"
    _write_jsonl(manifest_path, records)
    summary_path = run_dir / "summary.json"
    summary = {
        "run_id": run_id,
        "mode": "download",
        "manifest_path": str(manifest_path),
        "workbook_path": str(workbook_path),
        "workbook_sha256": workbook_sha256,
        "filtered_rows": len(records),
        "downloaded_existing_count": sum(
            1 for record in records if record["status"] == "downloaded_existing"
        ),
        "duplicate_url_count": sum(1 for record in records if record["status"] == "duplicate_url"),
        "validation_passed": True,
    }
    _write_json(summary_path, summary)
    return manifest_path


def _proving_fetcher(selected_rows: list):
    rows_by_url = {row.original_url: row for row in selected_rows}

    def fetcher(url, network, validation):  # noqa: ANN001, ARG001
        row = rows_by_url[url]
        return PreflightFetchResult(
            status="preflight_ok",
            http_status=200,
            final_url=url,
            redirect_chain=[],
            content_type=_content_type_for_parser(row.expected_parser),
            content_length=2048,
            method="HEAD",
            failure=None,
            validation={
                "mode": "source-register-proving-slice",
                "passed": True,
                "reason": None,
            },
            attempt_count=1,
        )

    return fetcher


def _write_latest_context(
    *,
    output_dir: Path,
    source_set_id: str,
    report_path: Path,
    catalog_dir: Path,
    source_catalog_path: Path,
    source_set_manifest_path: Path,
    authority_inventory_path: Path,
    source_addition_decisions_path: Path,
) -> None:
    context_path = output_dir / DEFAULT_LATEST_PROVING_CONTEXT_RELATIVE_PATH
    context_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(
        context_path,
        {
            "schema_version": LATEST_PROVING_CONTEXT_SCHEMA_VERSION,
            "source_set_id": source_set_id,
            "report_path": str(report_path),
            "catalog_dir": str(catalog_dir),
            "source_catalog_path": str(source_catalog_path),
            "source_set_manifest_path": str(source_set_manifest_path),
            "authority_inventory_path": str(authority_inventory_path),
            "source_addition_decisions_path": str(source_addition_decisions_path),
        },
    )


def _content_type_for_parser(expected_parser: str) -> str:
    parser_to_content_type = {
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "html": "text/html",
        "pdf": "application/pdf",
        "xml": "application/xml",
    }
    return parser_to_content_type.get(expected_parser, "application/octet-stream")


def _forest_unit_id(value: str) -> str:
    return f"forest_unit:{slugify(value, max_length=96)}"


def _normalize_identity_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _orphan_node_ids(*, nodes: list[dict], edges: list[dict]) -> list[str]:
    connected_node_ids = set()
    for edge in edges:
        connected_node_ids.add(str(edge["source"]))
        connected_node_ids.add(str(edge["target"]))
    return sorted(
        str(node["node_id"])
        for node in nodes
        if str(node["node_id"]) not in connected_node_ids
    )


def _disconnected_components(*, nodes: list[dict], edges: list[dict]) -> list[list[str]]:
    adjacency: dict[str, set[str]] = defaultdict(set)
    for node in nodes:
        adjacency[str(node["node_id"])]
    for edge in edges:
        source = str(edge["source"])
        target = str(edge["target"])
        adjacency[source].add(target)
        adjacency[target].add(source)
    visited: set[str] = set()
    components: list[list[str]] = []
    for node_id in sorted(adjacency):
        if node_id in visited:
            continue
        component = []
        queue = deque([node_id])
        visited.add(node_id)
        while queue:
            current = queue.popleft()
            component.append(current)
            for neighbor in sorted(adjacency[current]):
                if neighbor in visited:
                    continue
                visited.add(neighbor)
                queue.append(neighbor)
        components.append(sorted(component))
    return components


def _add_edge(edges: dict[str, dict], source: str, target: str, relationship: str) -> None:
    edge_id = f"{source}|{relationship}|{target}"
    edges.setdefault(
        edge_id,
        {
            "edge_id": edge_id,
            "source": source,
            "target": target,
            "relationship": relationship,
        },
    )


def _check(name: str, passed: bool, expected, actual) -> dict:
    return {
        "name": name,
        "passed": passed,
        "expected": expected,
        "actual": actual,
    }


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
