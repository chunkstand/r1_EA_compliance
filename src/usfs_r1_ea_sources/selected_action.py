from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import hashlib
import json
import re
from typing import Any

from .records import sha256_file


SELECTED_ACTION_SCHEMA_VERSION = "selected-action-v0"
SELECTED_ACTION_VALIDATION_SCHEMA_VERSION = "selected-action-validation-v0"
SELECTED_ACTION_EXTRACTION_METHOD_VERSION = "selected-action-extraction-v0"
SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


@dataclass(frozen=True)
class SelectedActionResult:
    review_id: str
    source_set_id: str
    selected_action_dir: Path
    selected_action_path: Path
    selected_action_validation_path: Path
    summary: dict[str, Any]


def build_selected_action_artifact(
    *,
    output_dir: Path,
    review_id: str,
    source_set_id: str | None = None,
    package_manifest_path: Path | None = None,
    package_chunks_path: Path | None = None,
    package_manifest: list[dict[str, Any]] | None = None,
    package_chunks: list[dict[str, Any]] | None = None,
    package_manifest_sha256: str | None = None,
    package_chunks_sha256: str | None = None,
    package_path: Path | None = None,
    created_at: str | None = None,
) -> SelectedActionResult:
    output_dir = Path(output_dir)
    _validate_safe_segment(review_id, "review_id")
    review_dir = output_dir / "reviews" / review_id
    package_dir = review_dir / "package"
    selected_action_dir = review_dir / "selected_action"
    package_manifest_path = package_manifest_path or package_dir / "package_manifest.jsonl"
    package_chunks_path = package_chunks_path or package_dir / "package_chunks.jsonl"
    package_manifest = (
        package_manifest
        if package_manifest is not None
        else _read_required_jsonl(package_manifest_path, "package manifest")
    )
    package_chunks = (
        package_chunks
        if package_chunks is not None
        else _read_required_jsonl(package_chunks_path, "package chunks")
    )
    if source_set_id is None:
        source_set_id = _source_set_id_from_package_chunks(package_chunks)
    _validate_safe_segment(source_set_id, "source_set_id")
    created_at = created_at or _utc_now()
    package_manifest_sha256 = package_manifest_sha256 or sha256_file(package_manifest_path)
    package_chunks_sha256 = package_chunks_sha256 or sha256_file(package_chunks_path)

    extraction = extract_selected_action_scope(package_chunks)
    validation = _validate_selected_action(
        package_manifest=package_manifest,
        package_chunks=package_chunks,
        extraction=extraction,
    )
    artifact_without_hash = {
        "schema_version": SELECTED_ACTION_SCHEMA_VERSION,
        "selected_action_id": f"selected-action:{review_id}",
        "review_id": review_id,
        "source_set_id": source_set_id,
        "created_at": created_at,
        "package_manifest_sha256": package_manifest_sha256,
        "package_chunks_sha256": package_chunks_sha256,
        "extraction_method_version": SELECTED_ACTION_EXTRACTION_METHOD_VERSION,
        "source_package": _source_package_metadata(
            package_path=package_path,
            package_manifest=package_manifest,
        ),
        "artifact_paths": {
            "package_manifest_path": str(package_manifest_path),
            "package_chunks_path": str(package_chunks_path),
        },
        "selected_action_scope": extraction["selected_action_scope"],
        "action_statements": extraction["action_statements"],
        "evidence_spans": extraction["evidence_spans"],
        "excluded_context_summary": extraction["excluded_context_summary"],
        "validation": validation,
    }
    selected_action_sha256 = _stable_sha256(artifact_without_hash)
    artifact_payload = {
        **artifact_without_hash,
        "selected_action_sha256": selected_action_sha256,
    }
    validation_payload = {
        "schema_version": SELECTED_ACTION_VALIDATION_SCHEMA_VERSION,
        "selected_action_id": artifact_payload["selected_action_id"],
        "review_id": review_id,
        "source_set_id": source_set_id,
        "created_at": created_at,
        "package_manifest_sha256": package_manifest_sha256,
        "package_chunks_sha256": package_chunks_sha256,
        "selected_action_sha256": selected_action_sha256,
        "validation": validation,
        "summary": {
            **selected_action_summary(artifact_payload),
            "validation_passed": validation["passed"],
        },
    }
    selected_action_path = selected_action_dir / "selected_action.json"
    selected_action_validation_path = selected_action_dir / "selected_action_validation.json"
    _write_json(selected_action_path, artifact_payload)
    _write_json(selected_action_validation_path, validation_payload)
    summary = {
        **selected_action_summary(artifact_payload),
        "extraction_method_version": SELECTED_ACTION_EXTRACTION_METHOD_VERSION,
        "validation_passed": validation["passed"],
        "selected_action_path": str(selected_action_path),
        "selected_action_validation_path": str(selected_action_validation_path),
    }
    return SelectedActionResult(
        review_id=review_id,
        source_set_id=source_set_id,
        selected_action_dir=selected_action_dir,
        selected_action_path=selected_action_path,
        selected_action_validation_path=selected_action_validation_path,
        summary=summary,
    )


def extract_selected_action_scope(package_chunks: list[dict[str, Any]]) -> dict[str, Any]:
    scored: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for chunk in package_chunks:
        if not isinstance(chunk, dict):
            continue
        score = _score_action_chunk(chunk)
        if score["selected"]:
            scored.append(_selected_action_span(chunk, score))
        else:
            excluded.append(
                {
                    "package_chunk_id": str(chunk.get("chunk_id") or ""),
                    "section": chunk.get("section"),
                    "heading": chunk.get("heading"),
                    "exclusion_reason": score["exclusion_reason"],
                    "score": score["score"],
                    "matched_cues": score["matched_cues"],
                }
            )
    scored.sort(key=lambda item: (-float(item["score"]), int(item["chunk_index"]), item["span_id"]))
    ordered = sorted(scored, key=lambda item: (int(item["chunk_index"]), item["span_id"]))
    chunk_ids = [span["package_chunk_id"] for span in ordered]
    role_counts = Counter(str(span["action_role"]) for span in ordered)
    scope_status = _scope_status(role_counts)
    action_text = "\n\n".join(span["text_excerpt"] for span in ordered)
    scope = {
        "scope_status": scope_status,
        "driver": _scope_driver(role_counts),
        "package_chunk_ids": chunk_ids,
        "evidence_span_ids": [span["span_id"] for span in ordered],
        "action_statement_count": len(ordered),
        "action_role_counts": dict(sorted(role_counts.items())),
        "action_text_sha256": (
            hashlib.sha256(action_text.encode("utf-8")).hexdigest() if action_text else None
        ),
        "matched_cues": sorted(
            {
                cue
                for span in ordered
                for cue in span.get("matched_cues", [])
            }
        ),
    }
    return {
        "selected_action_scope": scope,
        "action_statements": [_action_statement(span) for span in ordered],
        "evidence_spans": ordered,
        "excluded_context_summary": _excluded_context_summary(excluded),
    }


def selected_action_summary(selected_action: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(selected_action, dict):
        return {
            "selected_action_sha256": None,
            "selected_action_scope_status": "artifact_missing",
            "selected_action_scope_chunk_count": 0,
            "selected_action_evidence_span_count": 0,
            "selected_action_validation_passed": False,
        }
    scope = selected_action.get("selected_action_scope")
    if not isinstance(scope, dict):
        scope = {}
    validation = selected_action.get("validation")
    if not isinstance(validation, dict):
        validation = {}
    chunk_ids = selected_action_chunk_ids(selected_action)
    return {
        "selected_action_sha256": selected_action.get("selected_action_sha256"),
        "selected_action_scope_status": scope.get("scope_status") or "missing",
        "selected_action_scope_chunk_count": len(chunk_ids or []),
        "selected_action_evidence_span_count": len(
            selected_action.get("evidence_spans")
            if isinstance(selected_action.get("evidence_spans"), list)
            else []
        ),
        "selected_action_validation_passed": bool(validation.get("passed")),
    }


def selected_action_chunk_ids(selected_action: dict[str, Any] | None) -> set[str] | None:
    if selected_action is None:
        return None
    if not isinstance(selected_action, dict):
        return set()
    scope = selected_action.get("selected_action_scope")
    if not isinstance(scope, dict):
        return set()
    return set(_strings(scope.get("package_chunk_ids")))


def load_selected_action_from_artifact_path(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    path = Path(path)
    if not path.exists():
        return {
            "schema_version": SELECTED_ACTION_SCHEMA_VERSION,
            "selected_action_scope": {
                "scope_status": "artifact_missing",
                "package_chunk_ids": [],
                "evidence_span_ids": [],
            },
            "validation": {"passed": False, "checks": []},
            "artifact_paths": {"selected_action_path": str(path)},
        }
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else None


def selected_action_path_from_artifact(payload: dict[str, Any]) -> Path | None:
    artifacts = payload.get("artifact_paths")
    if not isinstance(artifacts, dict):
        return None
    value = artifacts.get("selected_action_path")
    return Path(str(value)) if value else None


def _score_action_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
    section = str(chunk.get("section") or "")
    heading = str(chunk.get("heading") or "")
    text = str(chunk.get("text") or "")
    haystack = f"{section}\n{heading}\n{text}"
    lower = haystack.lower()
    matched: list[str] = []
    score = 0
    action_role = "supporting_action_context"
    for cue in (
        "selected alternative",
        "selected action",
        "i have decided",
        "decision is to implement",
        "selected the",
    ):
        if cue in lower:
            matched.append(cue)
            score += 8
            action_role = "selected_action"
    for cue in (
        "decision notice",
        "finding of no significant impact",
        "decision and fonsi",
    ):
        if cue in lower:
            matched.append(cue)
            score += 3
            if action_role != "selected_action":
                action_role = "decision_action_context"
    for cue in (
        "modified proposed action",
        "forest service proposes",
        "proposes to",
        "proposed project",
        "action alternative",
    ):
        if cue in lower:
            matched.append(cue)
            score += 5
            if action_role not in {"selected_action", "decision_action_context"}:
                action_role = "proposed_action"
    if "proposed action" in lower:
        matched.append("proposed action")
        score += 2
        if action_role == "supporting_action_context":
            action_role = "proposed_action"
    for cue in (
        "proposed action includes",
        "proposed action would include",
        "proposed action consists of",
        "proposed action is to",
        "selected alternative includes",
        "selected alternative authorizes",
        "selected action includes",
        "selected action authorizes",
    ):
        if cue in lower:
            matched.append(cue)
            score += 4
            if "selected" in cue:
                action_role = "selected_action"
            elif action_role != "selected_action":
                action_role = "proposed_action"
    section_family = _section_family(chunk)
    if section_family in {"finding_decision", "alternatives"}:
        score += 2
    if section_family == "purpose_need":
        score += 1
    if "proposed action" in f"{section} {heading}".lower():
        score += 5
        matched.append("proposed action heading")
        if action_role == "supporting_action_context":
            action_role = "proposed_action"
    if "selected alternative" in f"{section} {heading}".lower():
        score += 8
        matched.append("selected alternative heading")
        action_role = "selected_action"
    no_action_context = "no action" in f"{section} {heading}".lower()
    if no_action_context and action_role != "selected_action":
        score -= 6
        matched.append("no action context")
    effects_context = any(
        cue in lower
        for cue in (
            "environmental consequences of the proposed action",
            "direct and indirect effects",
            "effects of the proposed action",
            "cumulative effects",
            "proposed action affects",
        )
    )
    if effects_context and action_role != "selected_action":
        score -= 5
        matched.append("effects context")
    broad_context = section_family in {
        "affected_environment",
        "environmental_consequences",
        "cumulative_effects",
    }
    if broad_context and not matched:
        score -= 2
    selected = score >= 5 and not (no_action_context and action_role != "selected_action")
    return {
        "score": score,
        "selected": selected,
        "action_role": action_role,
        "section_family": section_family,
        "matched_cues": sorted(set(matched)),
        "exclusion_reason": None if selected else _exclusion_reason(score, no_action_context, broad_context),
    }


def _selected_action_span(chunk: dict[str, Any], score: dict[str, Any]) -> dict[str, Any]:
    text = str(chunk.get("text") or "")
    chunk_id = str(chunk.get("chunk_id") or "")
    span_id = _stable_id("selected-action-span", chunk_id, str(chunk.get("content_sha256") or ""))
    return {
        "span_id": span_id,
        "package_chunk_id": chunk_id,
        "source_record_id": chunk.get("source_record_id"),
        "citation_label": chunk.get("citation_label"),
        "artifact_sha256": chunk.get("artifact_sha256"),
        "content_sha256": chunk.get("content_sha256"),
        "page_label": _page_label(chunk),
        "char_start": chunk.get("char_start"),
        "char_end": chunk.get("char_end"),
        "section": chunk.get("section"),
        "heading": chunk.get("heading"),
        "section_family": score["section_family"],
        "action_role": score["action_role"],
        "matched_cues": score["matched_cues"],
        "score": score["score"],
        "chunk_index": int(chunk.get("chunk_index") or 0),
        "text_excerpt": _excerpt(text),
        "text_hash": chunk.get("content_sha256")
        or hashlib.sha256(text.encode("utf-8")).hexdigest(),
    }


def _action_statement(span: dict[str, Any]) -> dict[str, Any]:
    return {
        "statement_id": _stable_id("selected-action-statement", str(span["span_id"])),
        "action_role": span["action_role"],
        "package_chunk_id": span["package_chunk_id"],
        "evidence_span_id": span["span_id"],
        "citation_label": span.get("citation_label"),
        "page_label": span.get("page_label"),
        "section": span.get("section"),
        "heading": span.get("heading"),
        "text_excerpt": span.get("text_excerpt"),
        "text_hash": span.get("text_hash"),
    }


def _validate_selected_action(
    *,
    package_manifest: list[dict[str, Any]],
    package_chunks: list[dict[str, Any]],
    extraction: dict[str, Any],
) -> dict[str, Any]:
    scope = extraction["selected_action_scope"]
    spans = extraction["evidence_spans"]
    chunk_ids = set(_strings(scope.get("package_chunk_ids")))
    available_chunk_ids = {
        str(chunk.get("chunk_id") or "")
        for chunk in package_chunks
        if str(chunk.get("chunk_id") or "")
    }
    checks = [
        {
            "name": "package_cache_present",
            "passed": bool(package_manifest) and bool(package_chunks),
            "details": {
                "package_file_count": len(package_manifest),
                "package_chunk_count": len(package_chunks),
            },
        },
        {
            "name": "selected_or_proposed_action_scope_present",
            "passed": scope["scope_status"]
            in {"selected_action_found", "proposed_action_found", "decision_action_found"},
            "details": {
                "scope_status": scope["scope_status"],
                "action_statement_count": scope["action_statement_count"],
            },
        },
        {
            "name": "selected_action_spans_resolve_to_package_chunks",
            "passed": chunk_ids <= available_chunk_ids,
            "details": {
                "missing_package_chunk_ids": sorted(chunk_ids - available_chunk_ids),
                "package_chunk_ids": sorted(chunk_ids),
            },
        },
        {
            "name": "broad_background_context_excluded_from_action_scope",
            "passed": True,
            "details": extraction["excluded_context_summary"],
        },
    ]
    return {
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "scope_status": scope["scope_status"],
        "action_statement_count": len(spans),
    }


def _scope_status(role_counts: Counter[str]) -> str:
    if role_counts.get("selected_action"):
        return "selected_action_found"
    if role_counts.get("proposed_action"):
        return "proposed_action_found"
    if role_counts.get("decision_action_context"):
        return "decision_action_found"
    return "missing"


def _scope_driver(role_counts: Counter[str]) -> str | None:
    for role in ("selected_action", "proposed_action", "decision_action_context"):
        if role_counts.get(role):
            return role
    return None


def _excluded_context_summary(excluded: list[dict[str, Any]]) -> dict[str, Any]:
    reason_counts = Counter(str(row.get("exclusion_reason") or "unspecified") for row in excluded)
    return {
        "excluded_chunk_count": len(excluded),
        "exclusion_reason_counts": dict(sorted(reason_counts.items())),
        "sample_excluded_chunks": sorted(
            excluded,
            key=lambda item: (
                str(item.get("exclusion_reason") or ""),
                str(item.get("package_chunk_id") or ""),
            ),
        )[:10],
    }


def _exclusion_reason(score: int, no_action_context: bool, broad_context: bool) -> str:
    if no_action_context:
        return "no_action_alternative_context"
    if broad_context:
        return "broad_resource_or_effects_context"
    if score > 0:
        return "insufficient_action_cues"
    return "no_action_scope_cues"


def _section_family(chunk: dict[str, Any]) -> str | None:
    values = " ".join(str(chunk.get(key) or "").lower() for key in ("section", "heading"))
    if "no action" in values:
        return "no_action"
    if "cumulative" in values:
        return "cumulative_effects"
    if "purpose" in values or "need" in values:
        return "purpose_need"
    if "affected" in values or "environment" in values:
        return "affected_environment"
    if "consequence" in values or "effect" in values:
        return "environmental_consequences"
    if "alternative" in values or "proposed action" in values:
        return "alternatives"
    if "decision" in values or "finding" in values or "fonsi" in values:
        return "finding_decision"
    return None


def _source_package_metadata(
    *,
    package_path: Path | None,
    package_manifest: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "package_path": str(package_path) if package_path else None,
        "artifact_paths": sorted(
            str(record.get("artifact_path"))
            for record in package_manifest
            if str(record.get("artifact_path") or "").strip()
        ),
        "source_record_ids": sorted(
            str(record.get("source_record_id"))
            for record in package_manifest
            if str(record.get("source_record_id") or "").strip()
        ),
        "extracted_file_count": sum(
            1 for record in package_manifest if record.get("status") == "extracted"
        ),
        "failed_file_count": sum(
            1 for record in package_manifest if record.get("status") != "extracted"
        ),
    }


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


def _read_required_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"Expected JSON object lines in {path}")
        rows.append(value)
    if not rows:
        raise ValueError(f"Empty {label}: {path}")
    return rows


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _stable_id(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def _stable_sha256(value: dict[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _excerpt(text: str, limit: int = 1200) -> str:
    text = " ".join(str(text or "").split())
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3].rstrip()}..."


def _page_label(chunk: dict[str, Any]) -> str | None:
    value = chunk.get("page_label") or chunk.get("page")
    return str(value) if value is not None else None


def _strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        values: list[str] = []
        for item in value:
            values.extend(_strings(item))
        return values
    text = str(value).strip()
    return [text] if text else []


def _validate_safe_segment(value: str | None, field_name: str) -> None:
    if not value or not SAFE_SEGMENT_RE.fullmatch(str(value)):
        raise ValueError(
            f"{field_name} must contain only letters, numbers, dots, underscores, or hyphens."
        )


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
