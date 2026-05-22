from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import re

from .rule_packs import _baseline_source_record_ids


CLAIM_STATUSES = {"pass", "gap"}
VALID_FINDING_STATUSES = {"pass", "gap", "uncertain", "not_applicable"}


def _authority_readiness_signal(summary: dict) -> str:
    row_count = int(summary.get("row_count") or 0)
    status_counts = summary.get("status_counts", {})
    if row_count and status_counts == {"pass": row_count}:
        finding_signal = (
            f"All {row_count} applicable authority rows pass the deterministic evidence gate."
        )
    else:
        finding_signal = f"{row_count} authority rows are rendered: {_count_phrase(status_counts)}."
    return f"{finding_signal} {_review_gate_phrase(summary)}"


def _forest_plan_readiness_signal(summary: dict) -> str:
    row_count = int(summary.get("row_count") or 0)
    standard_count = int(summary.get("applicable_standard_row_count") or 0)
    status_counts = summary.get("compliance_status_counts", {})
    complies = int(status_counts.get("complies") or 0)
    non_standard_count = max(row_count - standard_count, 0)
    if standard_count and complies == standard_count:
        standard_signal = f"all {standard_count} applicable standards comply"
    elif standard_count:
        standard_signal = (
            f"{standard_count} applicable standards are present; "
            f"status detail: {_count_phrase(status_counts)}"
        )
    else:
        standard_signal = "no applicable standards are counted for pass/fail compliance"
    if non_standard_count:
        return (
            f"{row_count} applicable Forest Plan components are visible; "
            f"{standard_signal}; {non_standard_count} goals, guidelines, desired conditions, "
            "or other non-standard components are carried as plan-consistency support."
        )
    return f"{row_count} applicable Forest Plan components are visible; {standard_signal}."


def _review_gate_phrase(summary: dict) -> str:
    reviewer_ready = bool(summary.get("reviewer_ready"))
    validated = bool(summary.get("validated"))
    if reviewer_ready and validated:
        return "Review gates passed and reviewer-ready support is available."
    if reviewer_ready:
        return "Reviewer-ready support is available, but validation needs review."
    if validated:
        return "Validation passed, but reviewer-ready support is not available."
    return "Review gates need review before relying on this matrix."


def _count_phrase(counts: dict | None) -> str:
    if not counts:
        return "no counts recorded"
    ordered_keys = [
        "pass",
        "gap",
        "uncertain",
        "not_applicable",
        "applicable",
        "complies",
        "does_not_comply",
        "partial",
        "not_evaluated_for_compliance",
    ]
    seen: set[str] = set()
    keys: list[str] = []
    for key in ordered_keys:
        if key in counts:
            keys.append(key)
            seen.add(key)
    keys.extend(sorted(key for key in counts if key not in seen))
    return "; ".join(
        f"{int(counts[key])} {_count_label(key, int(counts[key]))}" for key in keys
    )


def _count_label(key: str, count: int) -> str:
    if key == "complies":
        return "standard complies" if count == 1 else "standards comply"
    if key == "does_not_comply":
        return "standard does not comply" if count == 1 else "standards do not comply"
    return _display_value(key).lower()


def _yes_no_sentence(value: object, label: str) -> str:
    return f"{label}: {'yes' if bool(value) else 'no'}"


def _missing_summary(values: list[object], label: str) -> str:
    cleaned = [str(value) for value in values if value]
    if not cleaned:
        return f"0 {label}"
    preview = ", ".join(cleaned[:5])
    suffix = "" if len(cleaned) <= 5 else f", +{len(cleaned) - 5} more"
    return f"{len(cleaned)} {label}: {preview}{suffix}"


def _section_row_count(section: dict | None) -> int:
    if not section:
        return 0
    return int((section.get("summary") or {}).get("row_count") or 0)


def _section_summary_value(section: dict | None, key: str, default):
    if not section:
        return default
    return (section.get("summary") or {}).get(key, default)


def _optional_path(value: object) -> Path | None:
    if not value:
        return None
    return Path(str(value))


def _strings(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item or "").strip()]
    if str(value or "").strip():
        return [str(value).strip()]
    return []


def _read_json_if_exists(path: Path | None, load_errors: list[str]) -> dict | None:
    if path is None:
        return None
    if not path.exists():
        load_errors.append(f"missing:{path}")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        load_errors.append(f"unreadable:{path}:{exc}")
        return None
    if not isinstance(payload, dict):
        load_errors.append(f"invalid_json_object:{path}")
        return None
    return payload


def _standard_coverage_by_component_id(standard_coverage: dict | None) -> dict[str, dict]:
    if not standard_coverage:
        return {}
    coverage = {}
    for row in standard_coverage.get("standards", []):
        if not isinstance(row, dict):
            continue
        component_id = str(row.get("component_id") or row.get("standard_id") or "").strip()
        if component_id:
            coverage[component_id] = row
    return coverage


def _first_dict(values: object) -> dict:
    if isinstance(values, list):
        for value in values:
            if isinstance(value, dict):
                return value
    if isinstance(values, dict):
        return values
    return {}


def _component_key(finding: dict, coverage: dict) -> str | None:
    basis = finding.get("applicability_basis") or {}
    value = finding.get("component_key") or coverage.get("component_key") or basis.get(
        "component_key"
    )
    return str(value) if value else None


def _standard_applied(finding: dict, coverage: dict) -> bool | None:
    for key in ("standard_applied", "applied"):
        if key in finding:
            return bool(finding.get(key))
        if key in coverage:
            return bool(coverage.get(key))
    return None


def _forest_plan_component_type_sort_key(component_type: str) -> int:
    order = {
        "standard": 0,
        "guideline": 1,
        "desired_condition": 2,
        "objective": 3,
        "suitability": 4,
    }
    return order.get(component_type, 99)


def _compact_evidence(evidence: dict | None) -> dict | None:
    if not evidence:
        return None
    span = evidence.get("evidence_span") or {}
    provenance = evidence.get("provenance") or {}
    return {
        "citation_label": evidence.get("citation_label"),
        "source_record_id": evidence.get("source_record_id"),
        "title": evidence.get("title"),
        "chunk_id": evidence.get("chunk_id"),
        "text": span.get("text"),
        "source_char_start": span.get("source_char_start"),
        "source_char_end": span.get("source_char_end"),
        "chunk_char_start": span.get("chunk_char_start"),
        "chunk_char_end": span.get("chunk_char_end"),
        "page": provenance.get("page"),
        "section": provenance.get("section"),
        "artifact_path": provenance.get("artifact_path"),
        "artifact_sha256": provenance.get("artifact_sha256"),
        "content_sha256": provenance.get("content_sha256"),
    }


def finding_source_record_ids(finding: dict) -> list[str]:
    source_record_ids = set()
    source_evidence = finding.get("source_library_evidence") or {}
    if source_evidence.get("source_record_id"):
        source_record_ids.add(str(source_evidence["source_record_id"]))
    for link in finding.get("source_claim_links", []):
        if link.get("source_record_id"):
            source_record_ids.add(str(link["source_record_id"]))
    return sorted(source_record_ids)


def finding_source_document_roles(finding: dict) -> list[str]:
    roles = set()
    source_evidence = finding.get("source_library_evidence") or {}
    if source_evidence.get("document_role"):
        roles.add(str(source_evidence["document_role"]))
    for link in finding.get("source_claim_links", []):
        if link.get("document_role"):
            roles.add(str(link["document_role"]))
    return sorted(roles)


def _finding_has_required_eval_citations(finding: dict) -> bool:
    status = finding.get("status")
    if status not in CLAIM_STATUSES:
        return True
    if not _finding_has_source_evidence(finding) or not _finding_has_source_claim_links(finding):
        return False
    if status == "pass" and not _finding_has_package_evidence(finding):
        return False
    return True


def _finding_has_package_evidence(finding: dict) -> bool:
    return bool(finding.get("package_evidence_citation") and finding.get("package_evidence"))


def _finding_has_source_evidence(finding: dict) -> bool:
    return bool(finding.get("source_library_evidence_citation") and finding.get("source_library_evidence"))


def _finding_has_source_claim_links(finding: dict) -> bool:
    return bool(finding.get("source_claim_link_count") and finding.get("source_claim_links"))


def _matrix_failure_category(finding: dict) -> str | None:
    status = finding.get("status")
    if status == "pass":
        return None
    if status == "gap":
        return "package_evidence_gap"
    if status == "not_applicable":
        return "not_applicable"
    if finding.get("source_library_evidence_status") != "found":
        return "source_retrieval_miss"
    if finding.get("package_evidence_status") != "found":
        return "package_evidence_search_miss"
    if status not in VALID_FINDING_STATUSES:
        return "unsupported_status"
    return "uncertain_finding"


def _matrix_row_marker(row_class: str, row_id: object) -> str:
    return f"matrix-row:{row_class}:{_safe_marker_id(row_id)}"


def _safe_marker_id(value: object) -> str:
    text = str(value or "unknown")
    return re.sub(r"[^A-Za-z0-9_.:-]+", "-", text).strip("-") or "unknown"


def _render_manifest_row(
    *,
    row_class: str,
    row: dict,
    row_order: int,
    section: str,
    table_id: str,
    json_selector: str,
    markdown_marker: str,
    row_identity: dict,
) -> dict:
    return {
        "row_render_id": f"render:{row_class}:{_safe_marker_id(row.get('row_id') or row_identity)}",
        "row_class": row_class,
        "row_id": row.get("row_id"),
        "row_order": row_order,
        "section": section,
        "table_id": table_id,
        "json_selector": json_selector,
        "markdown_marker": markdown_marker,
        "pdf_render_contract": "pdf_generated_from_manifested_matrix_rows",
        "row_identity": row_identity,
        "source_record_ids": _render_source_record_ids(row),
        "status": row.get("status") or row.get("compliance_status"),
        "applicability_status": row.get("applicability_status"),
        "row_hash": _row_hash(row),
    }


def _render_source_record_ids(row: dict) -> list[str]:
    values = []
    for key in ("authority_source_record_id", "applied_source_record_ids"):
        value = row.get(key)
        if isinstance(value, list):
            values.extend(str(item) for item in value if item)
        elif value:
            values.append(str(value))
    return sorted(set(values))


def _row_hash(row: dict) -> str:
    payload = json.dumps(row, sort_keys=True, ensure_ascii=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _row_set_sha256(rows: list[dict]) -> str:
    identities = [
        {
            "row_class": row.get("row_class"),
            "row_identity": row.get("row_identity"),
            "row_hash": row.get("row_hash"),
        }
        for row in rows
    ]
    payload = json.dumps(identities, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _truncate(value: str, max_chars: int) -> str:
    normalized = " ".join(str(value).split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 3].rstrip() + "..."


def _evidence_excerpt(evidence: dict, max_chars: int) -> str:
    text = _clean_evidence_text(str(evidence.get("text") or ""))
    if not text:
        return ""
    return _truncate(text, max_chars)


def _clean_evidence_text(value: str) -> str:
    text = value.replace("|", " ")
    text = text.replace("#", " ")
    text = text.replace("*", " ")
    text = text.replace("\u2022", " ")
    text = " ".join(text.split())
    while "---" in text:
        text = text.replace("---", "--")
    text = text.strip(" -")
    if text and text[0].islower():
        match = re.search(r"\b[A-Z][A-Za-z0-9]", text)
        if match and match.start() < 120:
            text = text[match.start() :]
    return text


def _display_value(value: object) -> str:
    text = str(value or "unknown").replace("_", " ").strip()
    if not text:
        return "Unknown"
    return text[:1].upper() + text[1:]


def _md_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def _rule_pack_summary(rule_pack: dict) -> dict:
    return {
        "schema_version": rule_pack["schema_version"],
        "rule_pack_id": rule_pack["rule_pack_id"],
        "version": rule_pack["version"],
        "title": rule_pack["title"],
        "description": rule_pack.get("description"),
        "domain": rule_pack.get("domain"),
        "jurisdiction": rule_pack.get("jurisdiction"),
        "baseline_source_record_ids": _baseline_source_record_ids(rule_pack),
        "rule_count": len(rule_pack["rules"]),
    }


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
