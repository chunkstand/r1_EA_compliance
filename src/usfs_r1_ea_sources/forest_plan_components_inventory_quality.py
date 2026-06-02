from __future__ import annotations

import re
from collections import Counter
from difflib import SequenceMatcher
from .forest_plan_profiles import load_forest_plan_profile
from pathlib import Path

from .forest_plan_components_common import _compact, _component_id, _dedupe_preserve_order, _duplicate_values, _normalized_component_text, _safe_identifier, _utc_now
from .forest_plan_components_inventory_common import _section_heading_for_match, _suppress_tabular_component_label
from .forest_plan_components_inventory_detection import _components_from_chunk, _detected_component_labels
from .forest_plan_components_models import COMPONENT_LABEL_CANDIDATE_RE, COMPONENT_LABEL_RE, COMPONENT_NUMBER_RE, FOREST_PLAN_COMPONENT_INVENTORY_BUILD_COVERAGE_SCHEMA_VERSION, TOKEN_RE, _ForestPlanInventoryProfileBuild


def _component_inventory_build_coverage(
    *,
    source_set_id: str,
    source_record_ids: tuple[str, ...],
    chunks_path: Path,
    chunks: list[dict],
    components: list[dict],
    validation_errors: list[dict],
    profile_builds: list[_ForestPlanInventoryProfileBuild] | None = None,
) -> dict:
    detected_labels = _merge_overlapping_detected_labels(_detected_component_labels(chunks))
    inventory_quality_issues = _component_inventory_quality_issues(chunks)
    blocking_inventory_quality_issues = [
        issue for issue in inventory_quality_issues if issue.get("severity") == "error"
    ]
    component_source_accuracy = _component_inventory_source_accuracy(
        chunks=chunks,
        components=components,
    )
    detected_standards = [
        label for label in detected_labels if label["component_type"] == "standard"
    ]
    detected_component_ids = [label["component_id"] for label in detected_labels]
    detected_standard_ids = [label["component_id"] for label in detected_standards]
    built_component_ids = [str(component.get("component_id") or "") for component in components]
    built_standard_ids = [
        str(component.get("component_id") or "")
        for component in components
        if component.get("component_type") == "standard"
    ]
    missing_component_ids = sorted(set(detected_component_ids) - set(built_component_ids))
    missing_standard_ids = sorted(set(detected_standard_ids) - set(built_standard_ids))
    duplicate_component_ids = _duplicate_values(built_component_ids)
    duplicate_standard_ids = _duplicate_values(detected_standard_ids)
    checks = [
        {
            "name": "selected_forest_plan_chunks_present",
            "passed": bool(chunks),
            "details": {"chunk_count": len(chunks), "chunks_path": str(chunks_path)},
        },
        {
            "name": "labeled_components_detected",
            "passed": bool(detected_labels),
            "details": {"detected_component_count": len(detected_labels)},
        },
        {
            "name": "standard_components_detected",
            "passed": bool(detected_standards),
            "details": {"detected_standard_count": len(detected_standards)},
        },
        {
            "name": "all_detected_components_built",
            "passed": not missing_component_ids,
            "details": {"component_ids": missing_component_ids},
        },
        {
            "name": "all_detected_standards_built",
            "passed": not missing_standard_ids,
            "details": {"component_ids": missing_standard_ids},
        },
        {
            "name": "built_component_ids_are_unique",
            "passed": not duplicate_component_ids,
            "details": {"component_ids": duplicate_component_ids},
        },
        {
            "name": "detected_standard_labels_are_unique",
            "passed": not duplicate_standard_ids,
            "details": {"component_ids": duplicate_standard_ids},
        },
        {
            "name": "built_component_records_validate",
            "passed": not validation_errors,
            "details": {"errors": validation_errors},
        },
        {
            "name": "blocking_inventory_quality_issues_absent",
            "passed": not blocking_inventory_quality_issues,
            "details": {
                "issue_count": len(blocking_inventory_quality_issues),
                "issues": blocking_inventory_quality_issues,
            },
        },
        *component_source_accuracy["checks"],
    ]
    profile_results = []
    if profile_builds:
        failed_profile_builds = []
        missing_profile_chunks = []
        for profile_build in profile_builds:
            profile_coverage = profile_build.coverage
            failed_checks = [
                check["name"]
                for check in profile_coverage["checks"]
                if not check["passed"]
            ]
            blocker_types = _component_inventory_profile_blocker_types(
                failed_checks=failed_checks,
                selected_chunk_count=profile_coverage["selected_chunk_count"],
                built_component_count=profile_coverage["built_component_count"],
                built_standard_count=profile_coverage["built_standard_count"],
                duplicate_component_ids=profile_coverage["duplicate_component_ids"],
                duplicate_standard_ids=profile_coverage["duplicate_standard_ids"],
            )
            profile_results.append(
                {
                    "forest_unit_id": profile_build.forest_unit_id,
                    "plan_version": profile_build.plan_version,
                    "primary_plan_source_record_id": (
                        profile_build.primary_plan_source_record_id
                    ),
                    "source_record_ids": list(profile_build.source_record_ids),
                    "selected_chunk_count": profile_coverage["selected_chunk_count"],
                    "detected_component_count": profile_coverage["detected_component_count"],
                    "detected_standard_count": profile_coverage["detected_standard_count"],
                    "built_component_count": profile_coverage["built_component_count"],
                    "built_standard_count": profile_coverage["built_standard_count"],
                    "missing_component_ids": profile_coverage["missing_component_ids"],
                    "missing_standard_ids": profile_coverage["missing_standard_ids"],
                    "duplicate_component_ids": profile_coverage["duplicate_component_ids"],
                    "duplicate_standard_ids": profile_coverage["duplicate_standard_ids"],
                    "inventory_quality_issue_count": profile_coverage[
                        "inventory_quality_issue_count"
                    ],
                    "blocking_inventory_quality_issue_count": profile_coverage[
                        "blocking_inventory_quality_issue_count"
                    ],
                    "validation_error_count": len(profile_coverage["validation_errors"]),
                    "failed_checks": failed_checks,
                    "blocker_types": blocker_types,
                    "passed": profile_coverage["passed"],
                }
            )
            if not profile_coverage["passed"]:
                failed_profile_builds.append(profile_build.forest_unit_id)
            if profile_coverage["selected_chunk_count"] == 0:
                missing_profile_chunks.append(profile_build.forest_unit_id)
        checks.extend(
            [
                {
                    "name": "all_profile_builds_pass",
                    "passed": not failed_profile_builds,
                    "details": {"forest_unit_ids": failed_profile_builds},
                },
                {
                    "name": "all_profile_builds_have_selected_chunks",
                    "passed": not missing_profile_chunks,
                    "details": {"forest_unit_ids": missing_profile_chunks},
                },
            ]
        )
    return {
        "schema_version": FOREST_PLAN_COMPONENT_INVENTORY_BUILD_COVERAGE_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "source_set_id": source_set_id,
        "source_record_id": source_record_ids[0] if len(source_record_ids) == 1 else None,
        "source_record_ids": list(source_record_ids),
        "build_scope": "manifest_batch" if profile_builds else "single_forest",
        "chunks_path": str(chunks_path),
        "selected_chunk_count": len(chunks),
        "detected_component_count": len(detected_labels),
        "detected_standard_count": len(detected_standards),
        "built_component_count": len(components),
        "built_standard_count": len(built_standard_ids),
        "inventory_quality_issue_count": len(inventory_quality_issues),
        "blocking_inventory_quality_issue_count": len(blocking_inventory_quality_issues),
        "missing_component_ids": missing_component_ids,
        "missing_standard_ids": missing_standard_ids,
        "duplicate_component_ids": duplicate_component_ids,
        "duplicate_standard_ids": duplicate_standard_ids,
        "validation_errors": validation_errors,
        "inventory_quality_issues": inventory_quality_issues,
        "component_source_accuracy_passed": component_source_accuracy["passed"],
        "component_source_accuracy_failure_count": component_source_accuracy[
            "failure_count"
        ],
        "component_source_accuracy_failures": component_source_accuracy["failures"],
        "detected_component_labels": detected_labels,
        "detected_standard_labels": detected_standards,
        "profile_results": profile_results,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def _component_inventory_profile_blocker_types(
    *,
    failed_checks: list[str],
    selected_chunk_count: int,
    built_component_count: int,
    built_standard_count: int,
    duplicate_component_ids: list[str],
    duplicate_standard_ids: list[str],
) -> list[str]:
    blockers = []
    failed = set(failed_checks)
    if selected_chunk_count == 0:
        blockers.append("no_selected_forest_plan_chunks")
    if (
        "labeled_components_detected" in failed
        and built_component_count == 0
    ):
        blockers.append("plan_component_labels_not_detected")
    if (
        "standard_components_detected" in failed
        and built_standard_count == 0
    ):
        blockers.append("plan_standard_labels_not_detected")
    if "built_component_ids_are_unique" in failed and duplicate_component_ids:
        blockers.append("duplicate_component_ids_detected")
    if "detected_standard_labels_are_unique" in failed and duplicate_standard_ids:
        blockers.append("duplicate_standard_ids_detected")
    if not blockers and failed_checks:
        blockers.extend(sorted(failed))
    return blockers


def _component_inventory_source_accuracy(*, chunks: list[dict], components: list[dict]) -> dict:
    chunk_by_id = {
        str(chunk.get("chunk_id") or ""): chunk
        for chunk in chunks
        if str(chunk.get("chunk_id") or "").strip()
    }
    reparsed_by_key: dict[tuple[str, str, str, str], list[dict]] = {}
    failures = []
    for component in components:
        component_id = str(component.get("component_id") or "")
        source_chunk_ids = [
            str(chunk_id).strip()
            for chunk_id in component.get("source_chunk_ids", [])
            if str(chunk_id).strip()
        ]
        failure = {
            "component_id": component_id,
            "source_record_id": str(component.get("source_record_id") or ""),
            "primary_source_chunk_id": _primary_source_chunk_id(component),
            "source_chunk_ids": source_chunk_ids,
            "reasons": [],
        }
        missing_source_chunk_ids = [
            chunk_id for chunk_id in source_chunk_ids if chunk_id not in chunk_by_id
        ]
        if missing_source_chunk_ids:
            failure["reasons"].append("missing_source_chunks")
            failure["missing_source_chunk_ids"] = missing_source_chunk_ids
        source_record_mismatches = [
            {
                "chunk_id": chunk_id,
                "chunk_source_record_id": str(
                    (chunk_by_id.get(chunk_id) or {}).get("source_record_id") or ""
                ),
            }
            for chunk_id in source_chunk_ids
            if chunk_id in chunk_by_id
            and str(chunk_by_id[chunk_id].get("source_record_id") or "")
            != str(component.get("source_record_id") or "")
        ]
        if source_record_mismatches:
            failure["reasons"].append("source_record_mismatch")
            failure["source_record_mismatches"] = source_record_mismatches
        artifact_sha256_mismatches = [
            {
                "chunk_id": chunk_id,
                "chunk_artifact_sha256": str(
                    (chunk_by_id.get(chunk_id) or {}).get("artifact_sha256") or ""
                ),
            }
            for chunk_id in source_chunk_ids
            if chunk_id in chunk_by_id
            and str(chunk_by_id[chunk_id].get("artifact_sha256") or "")
            != str(component.get("artifact_sha256") or "")
        ]
        if artifact_sha256_mismatches:
            failure["reasons"].append("artifact_sha256_mismatch")
            failure["artifact_sha256_mismatches"] = artifact_sha256_mismatches
        primary_chunk_id = failure["primary_source_chunk_id"]
        primary_chunk = chunk_by_id.get(primary_chunk_id)
        if primary_chunk is None:
            failure["reasons"].append("missing_primary_source_chunk")
        else:
            if str(primary_chunk.get("content_sha256") or "") != str(
                component.get("content_sha256") or ""
            ):
                failure["reasons"].append("primary_content_sha256_mismatch")
                failure["primary_chunk_content_sha256"] = str(
                    primary_chunk.get("content_sha256") or ""
                )
                failure["component_content_sha256"] = str(
                    component.get("content_sha256") or ""
                )
            legacy_context = (
                component.get("legacy_parse_context")
                if isinstance(component.get("legacy_parse_context"), dict)
                else None
            )
            reparse_key = (
                primary_chunk_id,
                str(component.get("forest_unit_id") or ""),
                str(component.get("plan_version") or ""),
                str(component.get("source_set_id") or ""),
                tuple(sorted((str(key), str(value)) for key, value in legacy_context.items()))
                if legacy_context
                else (),
            )
            reparsed_components = reparsed_by_key.get(reparse_key)
            if reparsed_components is None:
                reparsed_components = _components_from_chunk(
                    chunk=primary_chunk,
                    forest_unit_id=str(component.get("forest_unit_id") or ""),
                    plan_version=str(component.get("plan_version") or ""),
                    source_set_id=str(component.get("source_set_id") or ""),
                    geographic_area_ids=[],
                    management_area_ids=[],
                    overlay_ids=[],
                    profile_context=_profile_context_terms(
                        str(component.get("forest_unit_id") or "")
                    ),
                    legacy_context=legacy_context,
                )
                reparsed_by_key[reparse_key] = reparsed_components
            if not any(
                candidate.get("component_id") == component_id
                and candidate.get("component_text") == component.get("component_text")
                and candidate.get("content_sha256") == component.get("content_sha256")
                and candidate.get("artifact_sha256") == component.get("artifact_sha256")
                for candidate in reparsed_components
            ):
                failure["reasons"].append(
                    "component_not_redetected_from_primary_source_chunk"
                )
        if failure["reasons"]:
            failures.append(failure)
    checks = [
        {
            "name": "component_source_chunks_exist",
            "passed": not _component_accuracy_failure_ids(failures, "missing_source_chunks"),
            "details": {
                "component_ids": _component_accuracy_failure_ids(
                    failures,
                    "missing_source_chunks",
                )
            },
        },
        {
            "name": "component_source_chunks_match_source_record",
            "passed": not _component_accuracy_failure_ids(failures, "source_record_mismatch"),
            "details": {
                "component_ids": _component_accuracy_failure_ids(
                    failures,
                    "source_record_mismatch",
                )
            },
        },
        {
            "name": "component_source_chunks_match_artifact_sha256",
            "passed": not _component_accuracy_failure_ids(
                failures,
                "artifact_sha256_mismatch",
            ),
            "details": {
                "component_ids": _component_accuracy_failure_ids(
                    failures,
                    "artifact_sha256_mismatch",
                )
            },
        },
        {
            "name": "component_primary_source_chunk_matches_content_sha256",
            "passed": not _component_accuracy_failure_ids(
                failures,
                "primary_content_sha256_mismatch",
            ),
            "details": {
                "component_ids": _component_accuracy_failure_ids(
                    failures,
                    "primary_content_sha256_mismatch",
                )
            },
        },
        {
            "name": "component_redetects_from_primary_source_chunk",
            "passed": not _component_accuracy_failure_ids(
                failures,
                "component_not_redetected_from_primary_source_chunk",
            ),
            "details": {
                "component_ids": _component_accuracy_failure_ids(
                    failures,
                    "component_not_redetected_from_primary_source_chunk",
                )
            },
        },
    ]
    return {
        "passed": all(check["passed"] for check in checks),
        "failure_count": len(failures),
        "failures": failures,
        "checks": checks,
    }


def _component_accuracy_failure_ids(failures: list[dict], reason: str) -> list[str]:
    return sorted(
        failure["component_id"]
        for failure in failures
        if reason in failure.get("reasons", [])
    )


def _component_inventory_quality_issues(chunks: list[dict]) -> list[dict]:
    issues = []
    seen = set()
    for chunk in chunks:
        text = str(chunk.get("text") or "")
        for match in COMPONENT_LABEL_RE.finditer(text):
            label = match.group("label")
            code = match.group("code")
            number = match.group("number")
            component_text = match.group("text")
            if not _suppress_tabular_component_label(
                label=label,
                code=code,
                number=number,
                text=component_text,
            ):
                continue
            source_record_id = str(chunk.get("source_record_id") or "")
            candidate_component_id = _component_id(
                source_record_id=source_record_id,
                code=code,
                number=number,
            )
            chunk_id = str(chunk.get("chunk_id") or "")
            dedupe_key = ("tabular_component_label", candidate_component_id, chunk_id)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            section_heading = _section_heading_for_match(
                text=text,
                start=match.start(),
                fallback=str(chunk.get("heading") or chunk.get("title") or "Forest Plan Components"),
            )
            issues.append(
                {
                    "issue_id": _safe_identifier(
                        f"{candidate_component_id}-tabular-component-label-{chunk_id or 'chunk'}"
                    ),
                    "issue_type": "tabular_component_label",
                    "severity": "warning",
                    "candidate_component_id": candidate_component_id,
                    "suggested_component_id": None,
                    "label": label,
                    "code": code,
                    "number_token": number,
                    "source_record_id": source_record_id,
                    "chunk_id": chunk_id,
                    "section_heading": section_heading,
                    "candidate_text": _compact(
                        f"{label} ({code}) {number} {component_text}",
                        limit=1200,
                    ),
                    "message": (
                        "Component-like label was suppressed because it matches a tabular "
                        "max/min statistic heading rather than a plan component."
                    ),
                }
            )
        for match in COMPONENT_LABEL_CANDIDATE_RE.finditer(text):
            number = match.group("number")
            if COMPONENT_NUMBER_RE.match(number):
                continue
            label = match.group("label")
            code = match.group("code")
            source_record_id = str(chunk.get("source_record_id") or "")
            candidate_component_id = _component_id(
                source_record_id=source_record_id,
                code=code,
                number=number,
            )
            suggested_number = _suggested_component_number(
                number_token=number,
                text=match.group("text"),
            )
            suggested_component_id = (
                _component_id(
                    source_record_id=source_record_id,
                    code=code,
                    number=suggested_number,
                )
                if suggested_number
                else None
            )
            issue_type = _component_inventory_quality_issue_type(
                number=number,
                text=match.group("text"),
            )
            chunk_id = str(chunk.get("chunk_id") or "")
            dedupe_key = (
                issue_type,
                candidate_component_id,
                suggested_component_id,
                chunk_id,
            )
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            section_heading = _section_heading_for_match(
                text=text,
                start=match.start(),
                fallback=str(chunk.get("heading") or chunk.get("title") or "Forest Plan Components"),
            )
            issues.append(
                {
                    "issue_id": _safe_identifier(
                        f"{candidate_component_id}-{issue_type}-{chunk_id or 'chunk'}"
                    ),
                    "issue_type": issue_type,
                    "severity": "warning",
                    "candidate_component_id": candidate_component_id,
                    "suggested_component_id": suggested_component_id,
                    "label": label,
                    "code": code,
                    "number_token": number,
                    "source_record_id": source_record_id,
                    "chunk_id": chunk_id,
                    "section_heading": section_heading,
                    "candidate_text": _compact(
                        f"{label} ({code}) {number} {match.group('text')}",
                        limit=1200,
                    ),
                    "message": (
                        "Component-like label was not built because the token after the "
                        "component code is not numeric; inspect whether this is a "
                        "cross-reference/table heading or should be normalized."
                    ),
                }
            )
    return issues


def _component_inventory_quality_issue_type(*, number: str, text: str) -> str:
    normalized_number = number.strip().lower()
    normalized_text = _normalized_component_text(text)
    if normalized_number in {"see", "table"} or normalized_text.startswith("see "):
        return "cross_reference_component_label"
    return "non_numeric_component_label"


def _suggested_component_number(*, number_token: str, text: str) -> str | None:
    if number_token.strip().lower() in {"table", "figure", "appendix"}:
        return None
    match = re.search(r"(?:\A|[.!?]\s+)(?P<number>[0-9][A-Za-z0-9.]*)\s+\S", text)
    if not match:
        return None
    number = match.group("number").strip().rstrip(".")
    return number if COMPONENT_NUMBER_RE.match(number) else None


def _profile_context_terms(forest_unit_id: str) -> dict[str, tuple[object, ...]]:
    try:
        profile = load_forest_plan_profile(forest_unit_id)
    except (FileNotFoundError, KeyError, ValueError):
        return {}
    return {
        "geographic_area_terms": profile.geographic_area_terms,
        "management_area_terms": profile.management_area_terms,
        "overlay_terms": profile.overlay_terms,
    }


def _merge_overlapping_component_records(components: list[dict]) -> list[dict]:
    merged = []
    for _, group in _group_by_component_id(components):
        if len(group) == 1 or not _overlapping_duplicate_group(group):
            merged.extend(group)
            continue
        base = max(group, key=lambda component: len(str(component.get("component_text") or "")))
        combined = dict(base)
        source_chunk_ids = _dedupe_preserve_order(
            [
                chunk_id
                for chunk_id in base.get("source_chunk_ids", [])
                if str(chunk_id).strip()
            ]
            + [
                chunk_id
                for component in group
                for chunk_id in component.get("source_chunk_ids", [])
                if str(chunk_id).strip()
            ]
        )
        combined["source_chunk_ids"] = source_chunk_ids
        provenance = dict(combined.get("provenance") or {})
        entity = dict(provenance.get("entity") or {})
        entity["source_chunk_ids"] = source_chunk_ids
        provenance["entity"] = entity
        combined["provenance"] = provenance
        merged.append(combined)
    return merged


def _merge_overlapping_detected_labels(labels: list[dict]) -> list[dict]:
    merged = []
    for _, group in _group_by_component_id(labels):
        if len(group) == 1 or not _overlapping_duplicate_group(group):
            merged.extend(group)
            continue
        merged.append(max(group, key=lambda label: len(str(label.get("component_text") or ""))))
    return merged


def _group_by_component_id(items: list[dict]) -> list[tuple[str, list[dict]]]:
    grouped: dict[str, list[dict]] = {}
    order = []
    for item in items:
        component_id = str(item.get("component_id") or "")
        if component_id not in grouped:
            grouped[component_id] = []
            order.append(component_id)
        grouped[component_id].append(item)
    return [(component_id, grouped[component_id]) for component_id in order]


def _overlapping_duplicate_group(group: list[dict]) -> bool:
    chunk_ids = [_primary_source_chunk_id(item) for item in group]
    chunk_ids = [chunk_id for chunk_id in chunk_ids if chunk_id]
    if len(set(chunk_ids)) <= 1:
        return False
    if len({str(item.get("component_type") or "") for item in group}) > 1:
        return False
    texts = [_normalized_component_text(str(item.get("component_text") or "")) for item in group]
    if any(not text for text in texts):
        return False
    longest = max(texts, key=len)
    for text in texts:
        if text == longest or text in longest:
            continue
        matcher = SequenceMatcher(None, text, longest)
        longest_match_size = matcher.find_longest_match(0, len(text), 0, len(longest)).size
        if (
            matcher.ratio() >= 0.9
            or (text and (longest_match_size / len(text)) >= 0.9)
            or _token_overlap_ratio(text, longest) >= 0.9
        ):
            continue
        return False
    return True


def _token_overlap_ratio(text: str, longest: str) -> float:
    text_tokens = TOKEN_RE.findall(text)
    if not text_tokens:
        return 0.0
    longest_counter = Counter(TOKEN_RE.findall(longest))
    matched_token_count = 0
    for token, count in Counter(text_tokens).items():
        matched_token_count += min(count, longest_counter[token])
    return matched_token_count / len(text_tokens)


def _primary_source_chunk_id(item: dict) -> str:
    if item.get("chunk_id"):
        return str(item["chunk_id"])
    source_chunk_ids = item.get("source_chunk_ids")
    if isinstance(source_chunk_ids, list) and source_chunk_ids:
        return str(source_chunk_ids[0])
    return ""
