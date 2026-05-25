from __future__ import annotations

from .records import aliased_source_record_ids


def authority_document_role(rule_or_template: dict, catalog_record: dict | None) -> str | None:
    source_filters = (
        rule_or_template.get("source_filters")
        if isinstance(rule_or_template.get("source_filters"), dict)
        else {}
    )
    value = (
        rule_or_template.get("authority_document_role")
        or source_filters.get("document_role")
        or (catalog_record or {}).get("document_role")
    )
    return str(value).strip() if str(value or "").strip() else None


def rule_source_record_id(rule: dict) -> str | None:
    source_filters = rule.get("source_filters") if isinstance(rule.get("source_filters"), dict) else {}
    value = rule.get("authority_source_record_id") or source_filters.get("source_record_id")
    return str(value).strip() if str(value or "").strip() else None


def baseline_source_record_ids(rule_pack: dict) -> list[str]:
    raw = rule_pack.get("baseline_source_record_ids")
    if not isinstance(raw, list):
        return []
    return [str(value).strip() for value in raw if str(value or "").strip()]


def strings(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (list, tuple)):
        values = []
        for item in value:
            if isinstance(item, (list, tuple)):
                values.extend(strings(item))
                continue
            text = str(item or "").strip()
            if text:
                values.append(text)
        return values
    text = str(value or "").strip()
    return [text] if text else []


def dedupe_strings(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in strings(values):
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def dedupe_groups(groups: list[list[str]]) -> list[list[str]]:
    seen = set()
    result = []
    for group in groups:
        normalized = tuple(strings(group))
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(list(normalized))
    return result


def string_groups(value: object) -> list[list[str]]:
    if not isinstance(value, list):
        return []
    groups = []
    for item in value:
        if isinstance(item, list):
            group = strings(item)
            if group:
                groups.append(group)
            continue
        text = str(item or "").strip()
        if text:
            groups.append([text])
    return groups


def source_record_summary(record: dict | None) -> dict:
    if not record:
        return {}
    return {
        "source_record_id": record.get("source_record_id"),
        "title": record.get("title"),
        "citation_label": record.get("citation_label"),
        "document_role": record.get("document_role"),
        "authority_level": record.get("authority_level"),
        "issuer": record.get("issuer"),
        "scope": record.get("scope"),
        "layer": record.get("layer"),
        "document_type": record.get("document_type"),
        "unit_or_overlay": record.get("unit_or_overlay"),
        "applies_to": record.get("applies_to"),
        "trigger": record.get("trigger"),
        "review_topics": record.get("review_topics", []),
        "currentness_notes": record.get("currentness_notes"),
        "source_status": record.get("source_status"),
        "artifact_sha256": record.get("artifact_sha256"),
        "artifact_path": record.get("artifact_path"),
        "artifact_byte_size": record.get("artifact_byte_size"),
        "content_type": record.get("content_type"),
        "retrieved_at": record.get("retrieved_at"),
    }


def catalog_resolved_source_record_ids(
    source_record_ids: list[str] | tuple[str, ...],
    *,
    catalog_by_source_id: dict[str, dict],
) -> list[str]:
    resolved: list[str] = []
    for source_record_id in strings(source_record_ids):
        catalog_matches = [
            candidate_id
            for candidate_id in aliased_source_record_ids([source_record_id])
            if candidate_id in catalog_by_source_id
        ]
        if catalog_matches:
            resolved.extend(catalog_matches)
            continue
        resolved.append(source_record_id)
    return dedupe_strings(resolved)
