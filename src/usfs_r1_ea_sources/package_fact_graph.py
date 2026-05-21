from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import hashlib
import json
import re
from typing import Any

from .evidence_strength import evidence_strength_for_confidence
from .forest_plan_profiles import DEFAULT_FOREST_PLAN_PROFILES_PATH
from .forest_plan_profiles import load_forest_plan_profiles
from .package_fact_graph_runtime import _build_extraction_summary
from .package_fact_graph_runtime import _extract_package_facts
from .package_fact_graph_terms import COMMON_PACKAGE_FACT_TYPES
from .package_fact_graph_terms import LOCATION_NODE_TYPES
from .package_fact_graph_terms import PACKAGE_FACT_EXTRACTION_METHOD_VERSION
from .package_fact_graph_terms import UNCERTAINTY_RECORD_STATUSES
from .records import sha256_file


PACKAGE_FACT_GRAPH_SCHEMA_VERSION = "package-fact-graph-v0"
PACKAGE_APPLICABILITY_CONTEXT_SCHEMA_VERSION = "package-applicability-context-v0"
PACKAGE_FACT_GRAPH_VALIDATION_SCHEMA_VERSION = "package-fact-graph-validation-v0"
SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


@dataclass(frozen=True)
class PackageFactGraphResult:
    review_id: str
    source_set_id: str
    applicability_dir: Path
    package_fact_graph_path: Path
    package_applicability_context_path: Path
    validation_summary_path: Path
    summary: dict[str, Any]


def _base_term_specs() -> list[dict[str, Any]]:
    from .package_fact_graph_terms import _base_term_specs as _package_fact_graph_base_term_specs

    return _package_fact_graph_base_term_specs()


def build_package_fact_graph(
    *,
    output_dir: Path,
    review_id: str,
    source_set_id: str | None = None,
    package_path: Path | None = None,
    package_manifest_path: Path | None = None,
    package_chunks_path: Path | None = None,
    forest_plan_profiles_path: Path = DEFAULT_FOREST_PLAN_PROFILES_PATH,
) -> PackageFactGraphResult:
    """Build package fact/context artifacts without deciding authority applicability."""

    output_dir = Path(output_dir)
    _validate_safe_segment(review_id, "review_id")
    review_dir = output_dir / "reviews" / review_id
    package_dir = review_dir / "package"
    applicability_dir = review_dir / "applicability"
    package_manifest_path = package_manifest_path or package_dir / "package_manifest.jsonl"
    package_chunks_path = package_chunks_path or package_dir / "package_chunks.jsonl"
    package_manifest = _read_required_jsonl(package_manifest_path, "package manifest")
    package_chunks = _read_required_jsonl(package_chunks_path, "package chunks")

    if source_set_id is None:
        source_set_id = _source_set_id_from_authority_snapshot(applicability_dir)
    if source_set_id is None:
        source_set_id = _source_set_id_from_package_chunks(package_chunks)
    _validate_safe_segment(source_set_id, "source_set_id")

    forest_plan_profiles_path = Path(forest_plan_profiles_path)
    profiles = load_forest_plan_profiles(forest_plan_profiles_path)
    created_at = _utc_now()
    applicability_run_id = f"applicability-context-{review_id}"
    manifest_sha256 = sha256_file(package_manifest_path)
    chunks_sha256 = sha256_file(package_chunks_path)
    profiles_sha256 = sha256_file(forest_plan_profiles_path)

    extraction = _extract_package_facts(
        package_chunks=package_chunks,
        profiles=profiles,
    )
    summary = _build_extraction_summary(
        package_manifest=package_manifest,
        package_chunks=package_chunks,
        extraction=extraction,
    )
    validation = _validate_package_fact_graph(
        extraction=extraction,
        package_manifest=package_manifest,
        package_chunks=package_chunks,
    )
    graph_without_hash = {
        "schema_version": PACKAGE_FACT_GRAPH_SCHEMA_VERSION,
        "applicability_run_id": applicability_run_id,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "created_at": created_at,
        "package_fact_graph_id": f"package-fact-graph:{review_id}",
        "package_manifest_sha256": manifest_sha256,
        "package_chunks_sha256": chunks_sha256,
        "forest_plan_profiles_sha256": profiles_sha256,
        "extraction_method_versions": {
            "package_fact_extraction": PACKAGE_FACT_EXTRACTION_METHOD_VERSION,
            "forest_plan_profiles": profiles.schema_version,
        },
        "source_package": _source_package_metadata(
            package_path=package_path,
            package_manifest=package_manifest,
        ),
        "artifact_paths": {
            "package_manifest_path": str(package_manifest_path),
            "package_chunks_path": str(package_chunks_path),
            "forest_plan_profiles_path": str(forest_plan_profiles_path),
        },
        "extraction_summary": summary,
        "nodes": extraction["nodes"],
        "edges": extraction["edges"],
        "validation": validation,
    }
    graph_sha256 = _stable_sha256(graph_without_hash)
    graph_payload = {
        **graph_without_hash,
        "package_fact_graph_sha256": graph_sha256,
    }
    context_without_hash = _build_applicability_context(
        review_id=review_id,
        source_set_id=source_set_id,
        applicability_run_id=applicability_run_id,
        package_path=package_path,
        package_manifest=package_manifest,
        package_manifest_sha256=manifest_sha256,
        package_chunks_sha256=chunks_sha256,
        package_fact_graph_sha256=graph_sha256,
        extraction=extraction,
        summary=summary,
    )
    context_sha256 = _stable_sha256(context_without_hash)
    context_payload = {
        **context_without_hash,
        "package_context_sha256": context_sha256,
    }
    validation_payload = {
        "schema_version": PACKAGE_FACT_GRAPH_VALIDATION_SCHEMA_VERSION,
        "applicability_run_id": applicability_run_id,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "package_manifest_sha256": manifest_sha256,
        "package_chunks_sha256": chunks_sha256,
        "package_fact_graph_sha256": graph_sha256,
        "package_context_sha256": context_sha256,
        "created_at": created_at,
        "validation": validation,
        "summary": {
            **summary,
            "validation_passed": validation["passed"],
        },
    }

    package_fact_graph_path = applicability_dir / "package_fact_graph.json"
    package_applicability_context_path = (
        applicability_dir / "package_applicability_context.json"
    )
    validation_summary_path = applicability_dir / "package_fact_graph_validation.json"
    _write_json(package_fact_graph_path, graph_payload)
    _write_json(package_applicability_context_path, context_payload)
    _write_json(validation_summary_path, validation_payload)

    result_summary = {
        "review_id": review_id,
        "source_set_id": source_set_id,
        "validation_passed": validation["passed"],
        "package_manifest_path": str(package_manifest_path),
        "package_chunks_path": str(package_chunks_path),
        "package_fact_graph_path": str(package_fact_graph_path),
        "package_applicability_context_path": str(package_applicability_context_path),
        "package_fact_graph_validation_path": str(validation_summary_path),
        "package_fact_graph_sha256": graph_sha256,
        "package_context_sha256": context_sha256,
        **summary,
    }
    return PackageFactGraphResult(
        review_id=review_id,
        source_set_id=source_set_id,
        applicability_dir=applicability_dir,
        package_fact_graph_path=package_fact_graph_path,
        package_applicability_context_path=package_applicability_context_path,
        validation_summary_path=validation_summary_path,
        summary=result_summary,
    )


def _validate_package_fact_graph(
    *,
    extraction: dict[str, Any],
    package_manifest: list[dict[str, Any]],
    package_chunks: list[dict[str, Any]],
) -> dict[str, Any]:
    fact_nodes = [
        node
        for node in extraction["nodes"]
        if node.get("node_type") not in {"package_section", "evidence_span"}
    ]
    checks = [
        {
            "name": "package_cache_present",
            "passed": bool(package_manifest) and bool(package_chunks),
            "details": {
                "package_file_count": len(package_manifest),
                "package_chunk_count": len(package_chunks),
            },
        },
        _check_fact_nodes_have_evidence(fact_nodes),
        _check_negative_location_context(extraction, fact_nodes),
        _check_uncertainty_records(extraction),
        _check_common_fact_type_coverage(fact_nodes),
    ]
    return {
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "uncertainty_records": extraction["uncertainty_records"],
        "negative_location_facts": extraction["suppressed_location_facts"],
    }


def _check_fact_nodes_have_evidence(fact_nodes: list[dict[str, Any]]) -> dict[str, Any]:
    failures = []
    for node in fact_nodes:
        if (
            not node.get("package_chunk_ids")
            or not node.get("section_ids")
            or not node.get("evidence_span_ids")
            or not node.get("content_sha256")
            or not node.get("artifact_sha256")
            or not node.get("parser_provenance")
        ):
            failures.append(str(node.get("node_id")))
    return {
        "name": "fact_nodes_have_package_spans_sections_provenance_and_hashes",
        "passed": not failures,
        "details": {
            "fact_node_count": len(fact_nodes),
            "failure_count": len(failures),
            "failed_node_ids": failures[:25],
        },
    }


def _check_negative_location_context(
    extraction: dict[str, Any],
    fact_nodes: list[dict[str, Any]],
) -> dict[str, Any]:
    failures = []
    for negative in extraction["suppressed_location_facts"]:
        for node in fact_nodes:
            if node.get("node_type") not in LOCATION_NODE_TYPES:
                continue
            if node.get("confidence_class") == "negative_context":
                continue
            if node.get("normalized_value") != negative["normalized_value"]:
                continue
            same_chunk = negative["chunk_id"] in (node.get("package_chunk_ids") or [])
            same_span = (
                node.get("chunk_char_start") == negative.get("chunk_char_start")
                and node.get("chunk_char_end") == negative.get("chunk_char_end")
            )
            if same_chunk and same_span:
                failures.append(
                    {
                        "negative_chunk_id": negative["chunk_id"],
                        "negative_chunk_char_start": negative.get("chunk_char_start"),
                        "negative_chunk_char_end": negative.get("chunk_char_end"),
                        "positive_node_id": node["node_id"],
                        "normalized_value": negative["normalized_value"],
                    }
                )
    return {
        "name": "negative_location_statements_do_not_create_positive_location_facts",
        "passed": not failures,
        "details": {
            "negative_location_fact_count": len(extraction["suppressed_location_facts"]),
            "failure_count": len(failures),
            "failures": failures[:25],
        },
    }


def _check_uncertainty_records(extraction: dict[str, Any]) -> dict[str, Any]:
    unresolved = [
        record
        for record in extraction["uncertainty_records"]
        if record.get("status") not in UNCERTAINTY_RECORD_STATUSES
    ]
    return {
        "name": "uncertain_facts_are_recorded_without_applicability_decisions",
        "passed": not unresolved,
        "details": {
            "uncertainty_record_count": len(extraction["uncertainty_records"]),
            "invalid_record_count": len(unresolved),
            "uncertainty_classes": dict(
                sorted(
                    Counter(
                        str(record.get("uncertainty_class") or "unspecified")
                        for record in extraction["uncertainty_records"]
                    ).items()
                )
            ),
        },
    }


def _check_common_fact_type_coverage(fact_nodes: list[dict[str, Any]]) -> dict[str, Any]:
    present = {
        str(node.get("node_type"))
        for node in fact_nodes
        if node.get("confidence_class") != "negative_context"
    }
    return {
        "name": "common_package_fact_type_coverage_recorded",
        "passed": True,
        "details": {
            "present_fact_types": sorted(present),
            "missing_common_fact_types": sorted(COMMON_PACKAGE_FACT_TYPES - present),
        },
    }


def _build_applicability_context(
    *,
    review_id: str,
    source_set_id: str,
    applicability_run_id: str,
    package_path: Path | None,
    package_manifest: list[dict[str, Any]],
    package_manifest_sha256: str,
    package_chunks_sha256: str,
    package_fact_graph_sha256: str,
    extraction: dict[str, Any],
    summary: dict[str, Any],
) -> dict[str, Any]:
    fact_nodes = [
        node
        for node in extraction["nodes"]
        if node.get("node_type") not in {"package_section", "evidence_span"}
    ]
    compact_facts = [_compact_fact(node) for node in fact_nodes]
    return {
        "schema_version": PACKAGE_APPLICABILITY_CONTEXT_SCHEMA_VERSION,
        "applicability_run_id": applicability_run_id,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "created_at": _utc_now(),
        "package_path": str(package_path) if package_path else None,
        "source_package": _source_package_metadata(
            package_path=package_path,
            package_manifest=package_manifest,
        ),
        "package_manifest_sha256": package_manifest_sha256,
        "package_chunks_sha256": package_chunks_sha256,
        "package_fact_graph_sha256": package_fact_graph_sha256,
        "package_section_map": extraction["section_map"],
        "section_family_bindings": _section_family_bindings(extraction["section_map"]),
        "project_type": _facts_by_type(compact_facts, "action"),
        "federal_action_signals": _facts_by_types(
            compact_facts,
            {"action", "agency", "nepa_level"},
        ),
        "authority_signals": _facts_by_type(compact_facts, "authority"),
        "forest_units": _facts_by_subtype(compact_facts, "geography", "forest_unit"),
        "project_locations": _facts_by_subtype(compact_facts, "geography", "project_location"),
        "geography": _facts_by_type(compact_facts, "geography"),
        "management_areas": _facts_by_type(compact_facts, "management_area"),
        "overlays": _facts_by_type(compact_facts, "overlay"),
        "resource_topics": _facts_by_type(compact_facts, "resource_topic"),
        "consultations": _facts_by_type(compact_facts, "consultation"),
        "permits": _facts_by_type(compact_facts, "permit"),
        "public_involvement_signals": _facts_by_type(compact_facts, "public_involvement"),
        "decision_posture": _facts_by_type(compact_facts, "decision_posture"),
        "nepa_level": _facts_by_type(compact_facts, "nepa_level"),
        "alternatives": _facts_by_type(compact_facts, "alternative"),
        "supporting_document_signals": _supporting_document_signals(compact_facts),
        "uncertainty_records": extraction["uncertainty_records"],
        "negative_location_facts": extraction["suppressed_location_facts"],
        "extracted_package_facts": compact_facts,
        "summary": summary,
    }


def _compact_fact(node: dict[str, Any]) -> dict[str, Any]:
    return {
        "fact_node_id": node["node_id"],
        "fact_type": node["node_type"],
        "fact_subtype": node.get("fact_subtype"),
        "label": node.get("label"),
        "raw_value": node.get("raw_value"),
        "normalized_value": node.get("normalized_value"),
        "confidence_class": node.get("confidence_class"),
        "evidence_strength": node.get("evidence_strength")
        or evidence_strength_for_confidence(
            node.get("confidence_class"),
            section_family=node.get("section_family"),
        ),
        "source_metadata": node.get("source_metadata") or {},
        "package_chunk_ids": node.get("package_chunk_ids") or [],
        "section_ids": node.get("section_ids") or [],
        "section_family": node.get("section_family"),
        "citation_label": node.get("citation_label"),
        "page_label": node.get("page_label"),
        "char_start": node.get("char_start"),
        "char_end": node.get("char_end"),
        "text_hash": node.get("text_hash"),
        "content_sha256": node.get("content_sha256"),
        "artifact_sha256": node.get("artifact_sha256"),
        "parser_provenance": node.get("parser_provenance"),
        "evidence_span_ids": node.get("evidence_span_ids") or [],
    }


def _facts_by_type(facts: list[dict[str, Any]], fact_type: str) -> list[dict[str, Any]]:
    return [
        fact
        for fact in facts
        if fact["fact_type"] == fact_type
        and fact.get("confidence_class") != "negative_context"
    ]


def _facts_by_types(
    facts: list[dict[str, Any]],
    fact_types: set[str],
) -> list[dict[str, Any]]:
    return [
        fact
        for fact in facts
        if fact["fact_type"] in fact_types
        and fact.get("confidence_class") != "negative_context"
    ]


def _facts_by_subtype(
    facts: list[dict[str, Any]],
    fact_type: str,
    fact_subtype: str,
) -> list[dict[str, Any]]:
    return [
        fact
        for fact in facts
        if fact["fact_type"] == fact_type
        and fact.get("fact_subtype") == fact_subtype
        and fact.get("confidence_class") != "negative_context"
    ]


def _supporting_document_signals(facts: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {
        "purpose_need": [
            fact for fact in facts if fact.get("section_family") == "purpose_need"
        ],
        "alternatives": [
            fact
            for fact in facts
            if fact.get("section_family") in {"alternatives", "no_action"}
        ],
        "cumulative_effects": [
            fact for fact in facts if fact.get("section_family") == "cumulative_effects"
        ],
        "mitigation": [
            fact for fact in facts if fact.get("section_family") == "mitigation"
        ],
        "public_involvement": [
            fact for fact in facts if fact.get("section_family") == "public_involvement"
        ],
        "finding_decision": [
            fact for fact in facts if fact.get("section_family") == "finding_decision"
        ],
    }


def _section_family_bindings(section_map: list[dict[str, Any]]) -> dict[str, list[str]]:
    bindings: dict[str, list[str]] = defaultdict(list)
    for row in section_map:
        bindings[str(row["section_family"])].append(str(row["section_id"]))
    return {
        family: sorted(section_ids)
        for family, section_ids in sorted(bindings.items())
    }


def _source_package_metadata(
    *,
    package_path: Path | None,
    package_manifest: list[dict[str, Any]],
) -> dict[str, Any]:
    artifact_paths = sorted(
        str(record.get("artifact_path"))
        for record in package_manifest
        if str(record.get("artifact_path") or "").strip()
    )
    source_record_ids = sorted(
        str(record.get("source_record_id"))
        for record in package_manifest
        if str(record.get("source_record_id") or "").strip()
    )
    parsers = sorted(
        {
            str(record.get("parser_name"))
            for record in package_manifest
            if str(record.get("parser_name") or "").strip()
        }
    )
    return {
        "package_path": str(package_path) if package_path else None,
        "artifact_paths": artifact_paths,
        "source_record_ids": source_record_ids,
        "parser_names": parsers,
        "extracted_file_count": sum(
            1 for record in package_manifest if record.get("status") == "extracted"
        ),
        "failed_file_count": sum(
            1 for record in package_manifest if record.get("status") != "extracted"
        ),
    }


def _source_set_id_from_authority_snapshot(applicability_dir: Path) -> str | None:
    snapshot_path = applicability_dir / "authority_universe_snapshot.json"
    if not snapshot_path.exists():
        return None
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if not isinstance(snapshot, dict):
        return None
    value = str(snapshot.get("source_set_id") or "").strip()
    return value or None


def _source_set_id_from_package_chunks(package_chunks: list[dict[str, Any]]) -> str:
    values = sorted(
        {
            str(chunk.get("source_set_id"))
            for chunk in package_chunks
            if str(chunk.get("source_set_id") or "").strip()
        }
    )
    if len(values) == 1:
        return values[0]
    if values:
        return values[0]
    return "unknown-source-set"


def _validate_safe_segment(value: str, field_name: str) -> None:
    if not SAFE_SEGMENT_RE.fullmatch(str(value or "")):
        raise ValueError(
            f"{field_name} must contain only letters, numbers, dots, underscores, or hyphens."
        )


def _read_required_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    records = _read_jsonl(path)
    if not records:
        raise ValueError(f"Empty {label}: {path}")
    return records


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"Expected JSON object lines in {path}")
        records.append(value)
    return records


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _stable_sha256(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
