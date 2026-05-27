from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit
import hashlib
import json
import re


SOURCE_RECORD_RECONCILIATION_SCHEMA_VERSION = "compliance-source-record-reconciliation-v1"
DEFAULT_SOURCE_RECORD_RECONCILIATION_PATH = Path(
    "config/compliance_source_record_reconciliation_v1.json"
)
FOREST_PLAN_IDENTITY_RECONCILIATION_SCHEMA_VERSION = (
    "region1-forest-plan-identity-reconciliation-registry-v1"
)
DEFAULT_FOREST_PLAN_IDENTITY_RECONCILIATION_PATH = Path(
    "config/r1_forest_plan_identity_reconciliation_v1.json"
)
SAFE_SOURCE_RECORD_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
FOREST_PLAN_ALIAS_PREFIXES = ("R1PLAN-", "FOR-", "FPS-", "FINAL-", "R1-")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_url(url: str) -> str:
    parsed = urlsplit(url.strip())
    return urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path,
            parsed.query,
            "",
        )
    )


def slugify(value: str, max_length: int = 80) -> str:
    lowered = value.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return (slug or "source")[:max_length].strip("-")


def reconciled_source_record_ids(
    *,
    source_record_id: str | None = None,
    source_record_ids: list[str] | tuple[str, ...] | None = None,
    reconciliation_path: Path = DEFAULT_SOURCE_RECORD_RECONCILIATION_PATH,
) -> list[str]:
    values = _normalized_source_record_ids(
        source_record_id=source_record_id,
        source_record_ids=source_record_ids,
    )
    if not values:
        return []
    reconciliation = _load_source_record_reconciliation(reconciliation_path)
    resolved: list[str] = []
    for value in values:
        resolved.append(value)
        resolved.extend(reconciliation["current_by_legacy"].get(value, ()))
    return _deduped_strings(resolved)


def aliased_source_record_ids(
    source_record_ids: list[str] | tuple[str, ...],
    *,
    reconciliation_path: Path = DEFAULT_SOURCE_RECORD_RECONCILIATION_PATH,
) -> list[str]:
    values = _normalized_source_record_ids(source_record_ids=source_record_ids)
    if not values:
        return []
    reconciliation = _load_source_record_reconciliation(reconciliation_path)
    aliased: list[str] = []
    for value in values:
        aliased.append(value)
        aliased.extend(reconciliation["current_by_legacy"].get(value, ()))
        for legacy_source_record_id in reconciliation["legacy_by_current"].get(value, ()):
            aliased.append(legacy_source_record_id)
            aliased.extend(reconciliation["current_by_legacy"].get(legacy_source_record_id, ()))
    forest_plan_alias_candidates = [
        value
        for value in _deduped_strings(aliased)
        if _looks_like_forest_plan_source_record_id(value)
    ]
    if forest_plan_alias_candidates:
        aliased.extend(
            _aliased_forest_plan_source_record_ids(
                source_record_ids=forest_plan_alias_candidates,
            )
        )
    return _deduped_strings(aliased)


@dataclass(frozen=True)
class SourceRecordIdentityGateResult:
    catalog_dir: Path
    eval_file: Path | None
    summary: dict[str, Any]


@dataclass(frozen=True)
class WorkbookSource:
    source_record_id: str
    sheet: str
    excel_row: int
    source_id: str | None
    title: str
    original_url: str
    effective_url: str
    normalized_url: str
    metadata: dict[str, str | None]


def planned_artifact_path(output_root: Path, source: WorkbookSource) -> Path:
    parsed = urlsplit(source.normalized_url)
    host = slugify(parsed.netloc or "unknown-host", max_length=64)
    title = slugify(source.title, max_length=72)
    short_id = slugify(source.source_id or source.source_record_id, max_length=32)
    return output_root / "artifacts" / "raw" / host / f"{short_id}_{title}.raw"


def expected_source_record_ids_from_v1_eval_contract(contract: dict[str, Any]) -> list[str]:
    source_record_ids: list[str] = []
    baseline_policy = contract.get("baseline_policy", {})
    if isinstance(baseline_policy, dict):
        source_record_ids.extend(
            str(value)
            for value in baseline_policy.get("expected_source_record_ids", []) or []
        )
    for key in ("rule_review_expectations", "conditional_source_expectations"):
        expectations = contract.get(key, [])
        if not isinstance(expectations, list):
            continue
        for expectation in expectations:
            if not isinstance(expectation, dict):
                continue
            source_record_ids.extend(
                str(value)
                for value in expectation.get("expected_source_record_ids", []) or []
            )
    forest_plan = contract.get("forest_plan", {})
    if isinstance(forest_plan, dict):
        source_record_ids.extend(
            str(value)
            for value in forest_plan.get("required_source_record_ids", []) or []
        )
    return _deduped_strings(source_record_ids)


def evaluate_source_record_identity_gate(
    *,
    expected_source_record_ids: list[str] | tuple[str, ...],
    catalog_source_record_ids: set[str],
    catalog_dir: Path | None = None,
    eval_file: Path | None = None,
    source_set_id: str | None = None,
    source_record_reconciliation_path: Path = DEFAULT_SOURCE_RECORD_RECONCILIATION_PATH,
    forest_plan_identity_reconciliation_path: Path = DEFAULT_FOREST_PLAN_IDENTITY_RECONCILIATION_PATH,
) -> SourceRecordIdentityGateResult:
    expected_ids = _normalized_source_record_ids(source_record_ids=expected_source_record_ids)
    catalog_ids = {str(value).strip() for value in catalog_source_record_ids if str(value).strip()}
    source_record_reconciliation = _load_source_record_reconciliation(
        source_record_reconciliation_path
    )
    forest_plan_reconciliation = _load_forest_plan_identity_reconciliation(
        forest_plan_identity_reconciliation_path
    )
    compliance_map = source_record_reconciliation["current_by_legacy"]
    forest_plan_map = forest_plan_reconciliation["canonical_by_legacy"]

    direct_hits: list[str] = []
    compliance_hits: list[str] = []
    forest_plan_hits: list[str] = []
    unmapped_source_record_ids: list[str] = []
    mapped_targets_absent: dict[str, list[str]] = {}
    ambiguous_mappings: dict[str, list[str]] = {}
    covered_source_record_ids: list[str] = []
    resolved_source_record_ids_by_expected_id: dict[str, list[str]] = {}

    for expected_id in expected_ids:
        if expected_id in catalog_ids:
            direct_hits.append(expected_id)
            covered_source_record_ids.append(expected_id)
            resolved_source_record_ids_by_expected_id[expected_id] = [expected_id]
            continue

        compliance_targets = list(compliance_map.get(expected_id, ()))
        forest_plan_target = forest_plan_map.get(expected_id)
        forest_plan_targets = [forest_plan_target] if forest_plan_target else []
        targets = _deduped_strings([*compliance_targets, *forest_plan_targets])
        present_targets = [target for target in targets if target in catalog_ids]
        absent_targets = [target for target in targets if target not in catalog_ids]

        if compliance_targets and any(target in catalog_ids for target in compliance_targets):
            compliance_hits.append(expected_id)
        if forest_plan_targets and any(target in catalog_ids for target in forest_plan_targets):
            forest_plan_hits.append(expected_id)
        if present_targets:
            covered_source_record_ids.append(expected_id)
        if not targets:
            unmapped_source_record_ids.append(expected_id)
        if absent_targets:
            mapped_targets_absent[expected_id] = sorted(absent_targets)
        if len(present_targets) > 1:
            ambiguous_mappings[expected_id] = sorted(present_targets)
        if len(present_targets) == 1 and not absent_targets:
            resolved_source_record_ids_by_expected_id[expected_id] = present_targets

    checks = [
        {
            "name": "expected_source_record_ids_present",
            "passed": bool(expected_ids),
            "details": {"expected_source_record_count": len(expected_ids)},
        },
        {
            "name": "all_expected_source_record_ids_mapped",
            "passed": not unmapped_source_record_ids,
            "details": {"unmapped_source_record_ids": unmapped_source_record_ids},
        },
        {
            "name": "mapped_source_record_ids_present_in_target_catalog",
            "passed": not mapped_targets_absent,
            "details": {"mapped_targets_absent_from_catalog": mapped_targets_absent},
        },
        {
            "name": "source_record_identity_mappings_unambiguous",
            "passed": not ambiguous_mappings,
            "details": {"ambiguous_mappings": ambiguous_mappings},
        },
    ]
    passed = all(check["passed"] for check in checks)
    summary: dict[str, Any] = {
        "passed": passed,
        "source_record_identity_status": "passed" if passed else "failed",
        "source_set_id": source_set_id,
        "catalog_dir": str(catalog_dir) if catalog_dir is not None else None,
        "eval_file": str(eval_file) if eval_file is not None else None,
        "catalog_source_record_count": len(catalog_ids),
        "expected_source_record_count": len(expected_ids),
        "direct_current_catalog_hit_count": len(direct_hits),
        "compliance_reconciled_source_record_count": len(compliance_hits),
        "forest_plan_reconciled_source_record_count": len(forest_plan_hits),
        "catalog_covered_source_record_count": len(_deduped_strings(covered_source_record_ids)),
        "identity_resolved_source_record_count": len(resolved_source_record_ids_by_expected_id),
        "unmapped_source_record_ids": unmapped_source_record_ids,
        "mapped_targets_absent_from_catalog": mapped_targets_absent,
        "ambiguous_mappings": ambiguous_mappings,
        "resolved_source_record_ids_by_expected_id": resolved_source_record_ids_by_expected_id,
        "checks": checks,
    }
    return SourceRecordIdentityGateResult(
        catalog_dir=catalog_dir or Path(),
        eval_file=eval_file,
        summary=summary,
    )


def run_source_record_identity_gate(
    *,
    output_dir: Path = Path("source_library"),
    source_set_id: str | None = None,
    catalog_dir: Path | None = None,
    eval_file: Path | None = None,
    source_record_ids: list[str] | tuple[str, ...] | None = None,
    source_record_reconciliation_path: Path = DEFAULT_SOURCE_RECORD_RECONCILIATION_PATH,
    forest_plan_identity_reconciliation_path: Path = DEFAULT_FOREST_PLAN_IDENTITY_RECONCILIATION_PATH,
) -> SourceRecordIdentityGateResult:
    from .catalog_surface import catalog_source_record_ids
    from .catalog_surface import catalog_source_set_id
    from .catalog_surface import resolve_catalog_dir_for_source_set

    resolved_catalog_dir = resolve_catalog_dir_for_source_set(
        output_dir=output_dir,
        source_set_id=source_set_id,
        catalog_dir=catalog_dir,
    )
    catalog_ids = catalog_source_record_ids(resolved_catalog_dir)
    expected_ids = _normalized_source_record_ids(source_record_ids=source_record_ids)
    if eval_file is not None:
        contract = json.loads(Path(eval_file).read_text(encoding="utf-8"))
        expected_ids = _deduped_strings(
            [*expected_ids, *expected_source_record_ids_from_v1_eval_contract(contract)]
        )
    resolved_source_set_id = source_set_id or catalog_source_set_id(resolved_catalog_dir)
    if catalog_ids is None:
        checks = [
            {
                "name": "target_catalog_source_record_ids_available",
                "passed": False,
                "details": {
                    "catalog_dir": str(resolved_catalog_dir),
                    "required_file": str(resolved_catalog_dir / "review_sources.sqlite"),
                },
            }
        ]
        return SourceRecordIdentityGateResult(
            catalog_dir=resolved_catalog_dir,
            eval_file=eval_file,
            summary={
                "passed": False,
                "source_record_identity_status": "failed",
                "source_set_id": resolved_source_set_id,
                "catalog_dir": str(resolved_catalog_dir),
                "eval_file": str(eval_file) if eval_file is not None else None,
                "catalog_source_record_count": 0,
                "expected_source_record_count": len(expected_ids),
                "checks": checks,
            },
        )
    return evaluate_source_record_identity_gate(
        expected_source_record_ids=expected_ids,
        catalog_source_record_ids=catalog_ids,
        catalog_dir=resolved_catalog_dir,
        eval_file=eval_file,
        source_set_id=resolved_source_set_id,
        source_record_reconciliation_path=source_record_reconciliation_path,
        forest_plan_identity_reconciliation_path=forest_plan_identity_reconciliation_path,
    )


def _normalized_source_record_ids(
    *,
    source_record_id: str | None = None,
    source_record_ids: list[str] | tuple[str, ...] | None = None,
) -> list[str]:
    values: list[str] = []
    if source_record_id is not None:
        values.append(str(source_record_id))
    values.extend(str(value) for value in (source_record_ids or []))
    return _deduped_strings(values)


def _deduped_strings(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen = set()
    for value in values:
        normalized = str(value or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return deduped


def _looks_like_forest_plan_source_record_id(value: str) -> bool:
    return str(value or "").startswith(FOREST_PLAN_ALIAS_PREFIXES)


def _aliased_forest_plan_source_record_ids(
    *,
    source_record_ids: list[str] | tuple[str, ...],
    reconciliation_path: Path = DEFAULT_FOREST_PLAN_IDENTITY_RECONCILIATION_PATH,
) -> list[str]:
    values = _normalized_source_record_ids(source_record_ids=source_record_ids)
    if not values:
        return []
    reconciliation = _load_forest_plan_identity_reconciliation(reconciliation_path)
    aliased: list[str] = []
    for value in values:
        aliased.append(value)
        canonical_source_record_id = reconciliation["canonical_by_legacy"].get(value)
        if canonical_source_record_id:
            aliased.append(canonical_source_record_id)
        aliased.extend(reconciliation["legacy_by_canonical"].get(value, ()))
    return _deduped_strings(aliased)


@lru_cache(maxsize=8)
def _load_source_record_reconciliation(path: Path) -> dict[str, dict[str, tuple[str, ...]]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Compliance source-record reconciliation must be a JSON object.")
    if payload.get("schema_version") != SOURCE_RECORD_RECONCILIATION_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported compliance source-record reconciliation schema_version: "
            f"{payload.get('schema_version')!r}"
        )
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise ValueError("Compliance source-record reconciliation entries must be a list.")
    current_by_legacy: dict[str, tuple[str, ...]] = {}
    legacy_by_current: dict[str, set[str]] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ValueError(
                "Compliance source-record reconciliation entry "
                f"{index} must be a JSON object."
            )
        legacy_source_record_id = str(entry.get("legacy_source_record_id") or "").strip()
        if not legacy_source_record_id:
            raise ValueError(
                "Compliance source-record reconciliation entry "
                f"{index} is missing legacy_source_record_id."
            )
        if not SAFE_SOURCE_RECORD_ID_RE.fullmatch(legacy_source_record_id):
            raise ValueError(
                "Compliance source-record reconciliation legacy_source_record_id must be safe: "
                f"{legacy_source_record_id!r}"
            )
        replacement_ids = _deduped_strings(
            [str(value) for value in entry.get("current_source_record_ids", []) or []]
        )
        for replacement_id in replacement_ids:
            if not SAFE_SOURCE_RECORD_ID_RE.fullmatch(replacement_id):
                raise ValueError(
                    "Compliance source-record reconciliation current_source_record_id must be "
                    f"safe: {replacement_id!r}"
                )
            legacy_by_current.setdefault(replacement_id, set()).add(legacy_source_record_id)
        current_by_legacy[legacy_source_record_id] = tuple(replacement_ids)
    return {
        "current_by_legacy": current_by_legacy,
        "legacy_by_current": {
            current_source_record_id: tuple(sorted(legacy_source_record_ids))
            for current_source_record_id, legacy_source_record_ids in legacy_by_current.items()
        },
    }


@lru_cache(maxsize=4)
def _load_forest_plan_identity_reconciliation(
    path: Path,
) -> dict[str, dict[str, tuple[str, ...]] | dict[str, str]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Forest-plan identity reconciliation must be a JSON object.")
    if payload.get("schema_version") != FOREST_PLAN_IDENTITY_RECONCILIATION_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported forest-plan identity reconciliation schema_version: "
            f"{payload.get('schema_version')!r}"
        )
    canonical_by_legacy: dict[str, str] = {}
    legacy_by_canonical: dict[str, set[str]] = {}
    for key in (
        "exact_url_matched_source_records",
        "governed_catalog_rebound_source_records",
    ):
        entries = payload.get(key)
        if not isinstance(entries, list):
            raise ValueError(f"Forest-plan identity reconciliation {key} must be a list.")
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise ValueError(
                    "Forest-plan identity reconciliation entry "
                    f"{key}[{index}] must be a JSON object."
                )
            legacy_source_record_id = str(entry.get("legacy_source_record_id") or "").strip()
            canonical_source_record_id = str(entry.get("canonical_source_record_id") or "").strip()
            if not legacy_source_record_id or not canonical_source_record_id:
                raise ValueError(
                    "Forest-plan identity reconciliation entry must include "
                    "legacy_source_record_id and canonical_source_record_id."
                )
            canonical_by_legacy[legacy_source_record_id] = canonical_source_record_id
            legacy_by_canonical.setdefault(canonical_source_record_id, set()).add(
                legacy_source_record_id
            )
    return {
        "canonical_by_legacy": canonical_by_legacy,
        "legacy_by_canonical": {
            canonical_source_record_id: tuple(sorted(legacy_source_record_ids))
            for canonical_source_record_id, legacy_source_record_ids in legacy_by_canonical.items()
        },
    }
