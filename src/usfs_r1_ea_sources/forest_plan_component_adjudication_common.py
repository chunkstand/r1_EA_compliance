from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import json

from .forest_plan_component_adjudication_models import (
    FOREST_PLAN_COMPONENT_ADJUDICATION_SCHEMA_VERSION,
)
from .forest_plan_component_adjudication_models import SAFE_ID_RE

def _resolve_review_dir(
    *,
    output_dir: Path,
    review_id: str | None,
    review_dir: Path | None,
) -> Path:
    if review_dir is not None:
        return Path(review_dir)
    if not review_id:
        raise ValueError("Provide either review_id or review_dir.")
    if not SAFE_ID_RE.fullmatch(review_id):
        raise ValueError("review_id must contain only letters, numbers, dot, underscore, or hyphen.")
    return Path(output_dir) / "reviews" / review_id

def _load_review_artifacts(review_dir: Path) -> dict[str, Any]:
    findings_path = review_dir / "forest_plan_component_findings.json"
    queue_path = review_dir / "forest_plan_reviewer_resolution_queue.json"
    findings_report = _read_json(findings_path)
    queue = _read_json(queue_path)
    return {
        "findings_report": findings_report,
        "queue": queue,
    }

def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing forest-plan component adjudication artifact: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return value

def _load_adjudication(path: Path) -> dict[str, Any]:
    adjudication = _read_json(path)
    if adjudication.get("schema_version") != FOREST_PLAN_COMPONENT_ADJUDICATION_SCHEMA_VERSION:
        raise ValueError(
            "Forest-plan component adjudication file has unsupported schema_version: "
            f"{adjudication.get('schema_version')}"
        )
    return adjudication

def _queue_items(queue: dict[str, Any]) -> list[dict[str, Any]]:
    items = queue.get("items")
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []

def _findings_by_id(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    findings = report.get("findings")
    if not isinstance(findings, list):
        return {}
    return {
        str(finding.get("finding_id")): finding
        for finding in findings
        if isinstance(finding, dict) and finding.get("finding_id")
    }

def _components_by_id(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    components = report.get("components")
    if not isinstance(components, list):
        return {}
    return {
        str(component.get("component_id")): component
        for component in components
        if isinstance(component, dict) and component.get("component_id")
    }

def _adjudication_items(adjudication: dict[str, Any]) -> list[dict[str, Any]]:
    items = adjudication.get("items")
    return [item for item in items if isinstance(item, dict)] if isinstance(items, list) else []

def _component_source_ref(
    *,
    component: dict[str, Any],
    plan_source_evidence_refs: list[dict[str, Any]],
) -> dict[str, Any]:
    provenance = component.get("provenance") if isinstance(component.get("provenance"), dict) else {}
    entity = provenance.get("entity") if isinstance(provenance.get("entity"), dict) else {}
    first_plan_ref = plan_source_evidence_refs[0] if plan_source_evidence_refs else {}
    return _compact_dict(
        {
            "source_record_id": component.get("source_record_id")
            or entity.get("source_record_id")
            or first_plan_ref.get("source_record_id"),
            "citation_label": component.get("citation_label")
            or first_plan_ref.get("citation_label"),
            "artifact_sha256": component.get("artifact_sha256")
            or entity.get("artifact_sha256")
            or first_plan_ref.get("artifact_sha256"),
            "content_sha256": component.get("content_sha256")
            or entity.get("content_sha256")
            or first_plan_ref.get("content_sha256"),
            "source_chunk_ids": _string_values(
                component.get("source_chunk_ids")
                or entity.get("source_chunk_ids")
                or first_plan_ref.get("source_chunk_ids")
                or []
            ),
            "page": component.get("page") or first_plan_ref.get("page"),
        }
    )

def _evidence_refs(evidence_items: list[Any]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for item in evidence_items:
        if not isinstance(item, dict):
            continue
        provenance = item.get("provenance") if isinstance(item.get("provenance"), dict) else {}
        span = item.get("evidence_span") if isinstance(item.get("evidence_span"), dict) else {}
        refs.append(
            _compact_dict(
                {
                    "source_record_id": item.get("source_record_id")
                    or provenance.get("source_record_id"),
                    "citation_label": item.get("citation_label"),
                    "title": item.get("title"),
                    "document_role": item.get("document_role"),
                    "authority_level": item.get("authority_level"),
                    "chunk_id": item.get("chunk_id"),
                    "page": item.get("page"),
                    "rank": item.get("rank"),
                    "score": item.get("score"),
                    "artifact_sha256": provenance.get("artifact_sha256"),
                    "content_sha256": provenance.get("content_sha256"),
                    "source_chunk_ids": _string_values(provenance.get("source_chunk_ids")),
                    "source_text_path": provenance.get("source_text_path"),
                    "evidence_span": _compact_dict(
                        {
                            "chunk_char_start": span.get("chunk_char_start"),
                            "chunk_char_end": span.get("chunk_char_end"),
                            "source_char_start": span.get("source_char_start"),
                            "source_char_end": span.get("source_char_end"),
                            "text": span.get("text"),
                        }
                    ),
                }
            )
        )
    return refs

def _unique_ref_values(refs: list[dict[str, Any]], field: str) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for ref in refs:
        value = str(ref.get(field) or "").strip()
        if value and value not in seen:
            seen.add(value)
            values.append(value)
    return values

def _compact_dict(value: dict[str, Any]) -> dict[str, Any]:
    compact: dict[str, Any] = {}
    for key, item in value.items():
        if item is None or item == "" or item == [] or item == {}:
            continue
        compact[key] = item
    return compact

def _current_status(*, finding: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    return {
        "finding_status": finding.get("finding_status") or item.get("finding_status"),
        "applicability_status": finding.get("applicability_status")
        or item.get("applicability_status"),
        "compliance_status": finding.get("compliance_status"),
        "queue_reason": item.get("reason"),
    }

def _key_details(key: tuple[str, str, str]) -> dict[str, str]:
    item_id, finding_id, component_id = key
    return {
        "item_id": item_id,
        "finding_id": finding_id,
        "component_id": component_id,
    }

def _string_list(value: object) -> bool:
    return isinstance(value, list) and any(str(item).strip() for item in value)

def _string_values(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]

def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return round(numerator / denominator, 6)

def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")

def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")
