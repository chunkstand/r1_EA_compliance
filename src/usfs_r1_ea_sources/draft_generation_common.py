from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path("config/draft_generation_v1.json")

PACKAGE_SCHEMA_VERSION = "draft-generation-package-v1"
MANIFEST_SCHEMA_VERSION = "draft-generation-manifest-v1"
TRACEABILITY_SCHEMA_VERSION = "draft-generation-traceability-v1"
REFUSAL_SCHEMA_VERSION = "draft-generation-refusals-v1"
DEFENSIBILITY_SCHEMA_VERSION = "draft-defensibility-packet-v1"
VALIDATION_SCHEMA_VERSION = "draft-generation-validation-v1"
GENERATOR_VERSION = "draft-generation-v1"

PACKAGE_FILENAME = "draft_generation_package.json"
MARKDOWN_FILENAME = "draft_generation.md"
MANIFEST_FILENAME = "draft_generation_manifest.json"
TRACEABILITY_FILENAME = "draft_generation_traceability.json"
REFUSAL_FILENAME = "draft_generation_refusals.json"
DEFENSIBILITY_FILENAME = "draft_defensibility_packet.json"
VALIDATION_FILENAME = "draft_generation_validation.json"

SUPPORTED_SECTION_TYPES = {
    "citation_bearing_issue_summary",
    "compliance_narrative",
    "authority_coverage_appendix",
    "environmental_consequences",
    "unresolved_issue_statement",
}
PROHIBITED_LEGAL_OUTPUT_TYPES = {
    "legal_sufficiency_determination",
    "record_of_decision",
    "line_officer_approval",
    "responsible_official_certification",
}


@dataclass(frozen=True)
class DraftGenerationResult:
    output_dir: Path
    package_path: Path
    markdown_path: Path
    manifest_path: Path
    traceability_path: Path
    refusal_path: Path
    defensibility_path: Path
    validation_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class DraftGenerationBundle:
    package: dict[str, Any]
    markdown: str
    manifest: dict[str, Any]
    traceability: dict[str, Any]
    refusals: dict[str, Any]
    defensibility_packet: dict[str, Any]
    validation: dict[str, Any]


@dataclass(frozen=True)
class _Artifact:
    key: str
    path: Path
    required: bool
    exists: bool
    parse_ok: bool
    payload: dict[str, Any] | None
    sha256: str | None
    error: str | None = None


@dataclass(frozen=True)
class DraftGenerationContext:
    output_dir: Path
    review_dir: Path
    review_id: str
    source_set_id: str
    config_path: Path
    config: dict[str, Any]
    artifacts: dict[str, _Artifact]

    def payload(self, key: str) -> dict[str, Any]:
        artifact = self.artifacts[key]
        return artifact.payload if isinstance(artifact.payload, dict) else {}


def _refusal(
    *,
    context: DraftGenerationContext,
    output_id: str,
    category: str,
    message: str,
) -> dict[str, Any]:
    return {
        "refusal_id": f"refusal:{output_id}:{category}",
        "output_id": output_id,
        "category": category,
        "message": message,
        "review_id": context.review_id,
        "source_set_id": context.source_set_id,
    }


def _check(name: str, passed: bool, failure_category: str, details: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": name,
        "passed": passed,
        "failure_category": failure_category,
        "details": details,
    }


def _paragraph(
    *,
    section_id: str,
    ordinal: int,
    text: str,
    trace_seed: dict[str, Any],
    warning: bool = False,
) -> dict[str, Any]:
    citations = _citation_labels(trace_seed)
    paragraph_id = f"{section_id}:paragraph:{ordinal}"
    trace = {
        "paragraph_id": paragraph_id,
        "section_id": section_id,
        "source_passages": _dedupe_dict_rows(trace_seed.get("source_passages", [])),
        "authority_family_ids": sorted(set(trace_seed.get("authority_family_ids", []))),
        "graph_path_ids": sorted(set(trace_seed.get("graph_path_ids", []))),
        "retrieval_trace_ids": sorted(set(trace_seed.get("retrieval_trace_ids", []))),
        "review_decision_refs": _dedupe_dict_rows(trace_seed.get("review_decision_refs", [])),
        "unresolved_issue_refs": sorted(set(trace_seed.get("unresolved_issue_refs", []))),
        "missing_evidence_refs": sorted(set(trace_seed.get("missing_evidence_refs", []))),
        "residual_risk_refs": sorted(set(trace_seed.get("residual_risk_refs", []))),
        "rule_ids": sorted(set(trace_seed.get("rule_ids", []))),
        "warning_inserted": warning,
    }
    return {
        "paragraph_id": paragraph_id,
        "text": text,
        "citations": citations,
        "source_record_ids": sorted(
            {
                str(row.get("source_record_id") or "")
                for row in trace["source_passages"]
                if isinstance(row, dict) and str(row.get("source_record_id") or "").strip()
            }
        ),
        "authority_family_ids": trace["authority_family_ids"],
        "warning_inserted": warning,
        "_trace": trace,
    }


def _public_paragraph(paragraph: dict[str, Any]) -> dict[str, Any]:
    return {
        "paragraph_id": paragraph["paragraph_id"],
        "text": paragraph["text"],
        "citations": paragraph["citations"],
        "source_record_ids": paragraph["source_record_ids"],
        "authority_family_ids": paragraph["authority_family_ids"],
        "warning_inserted": paragraph["warning_inserted"],
    }


def _citation_labels(trace_seed: dict[str, Any]) -> list[str]:
    labels = []
    value = trace_seed.get("source_passages")
    rows = value if isinstance(value, list) else []
    for row in rows:
        if not isinstance(row, dict):
            continue
        label = ""
        if row.get("citation_label"):
            label = str(row.get("citation_label") or "").strip()
        elif "artifact_sha256" not in row and row.get("source_record_id"):
            label = str(row.get("source_record_id") or "").strip()
        if label:
            labels.append(label)
    return sorted(dict.fromkeys(labels))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _safe_len(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def _dedupe_dict_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    deduped = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = json.dumps(row, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def _missing_citation_refs(
    *,
    evidence_rows: list[dict[str, Any]],
    rule_id: str,
    evidence_kind: str,
) -> list[str]:
    missing = []
    for row in evidence_rows:
        if row.get("citation_label"):
            continue
        if row.get("artifact_sha256") or row.get("text_span") or row.get("chunk_id"):
            missing.append(
                f"{rule_id}:{evidence_kind}:{row.get('chunk_id') or row.get('source_record_id') or 'missing-citation'}"
            )
    return missing
