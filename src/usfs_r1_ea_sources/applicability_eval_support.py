from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import hashlib
import json
import re


APPLICABILITY_EVAL_SCHEMA_VERSION = "applicability-eval-v0"
APPLICABILITY_EVAL_RESULT_SCHEMA_VERSION = "applicability-eval-results-v0"
APPLICABILITY_EVAL_CONTRACT_ID = "applicability-direct-eval-summary-v1"
APPLICABILITY_EVAL_SCORER_VERSION = "applicability-direct-eval-scorer-v1"
APPLICABILITY_GOLD_EVAL_SCHEMA_VERSION = "applicability-gold-eval-v0"
APPLICABILITY_GOLD_EVAL_RESULT_SCHEMA_VERSION = "applicability-gold-eval-results-v0"
DEFAULT_APPLICABILITY_EVAL_PATH = Path("config/applicability_eval_seed.json")
DEFAULT_APPLICABILITY_GOLD_EVAL_PATH = Path("config/applicability_gold_eval_v1.json")
REQUIRED_GOLD_PROFILES = {"positive", "mixed", "negative", "unresolved", "adjudicated"}
SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


@dataclass(frozen=True)
class ApplicabilityEvalResult:
    eval_file: Path
    output_dir: Path
    output_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class ApplicabilityGoldEvalResult:
    gold_file: Path
    output_dir: Path
    output_path: Path
    summary: dict[str, Any]


def _load_eval_payload(path: Path, schema_version: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing eval file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, list):
        value = {"schema_version": schema_version, "cases": value}
    if not isinstance(value, dict):
        raise ValueError("Applicability eval file must be a JSON object or case list.")
    if value.get("schema_version") != schema_version:
        raise ValueError(
            f"Expected {schema_version} eval file, got {value.get('schema_version')}"
        )
    return value


def _case_list(payload: dict[str, Any]) -> list[dict[str, Any]]:
    cases = payload.get("cases")
    return cases if isinstance(cases, list) else []


def _source_chunk_specs(value: Any) -> list[dict[str, Any]]:
    return [item for item in value or [] if isinstance(item, dict)]


def _rule_ids(rules: list[dict[str, Any]]) -> list[str]:
    return sorted(str(rule.get("id") or "") for rule in rules if rule.get("id"))


def _template_rule_ids(templates: list[dict[str, Any]]) -> list[str]:
    return sorted(
        str(template.get("rule_id") or "") for template in templates if template.get("rule_id")
    )


def _strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item or "").strip()]
    return [str(value)] if str(value or "").strip() else []


def _string_list_mapping(value: Any) -> dict[str, list[str]]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key): sorted(_strings(item))
        for key, item in value.items()
        if str(key or "").strip() and _strings(item)
    }


def _string_mapping(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {
        str(key): str(item)
        for key, item in value.items()
        if str(key or "").strip() and str(item or "").strip()
    }


def _string_groups(value: Any) -> list[list[str]]:
    if not isinstance(value, list):
        return []
    return [
        _strings(group)
        for group in value
        if isinstance(group, list) and _strings(group)
    ]


def _dedupe(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _dedupe_groups(groups: list[list[str]]) -> list[list[str]]:
    seen = set()
    result = []
    for group in groups:
        clean = tuple(_strings(group))
        if not clean or clean in seen:
            continue
        seen.add(clean)
        result.append(list(clean))
    return result


def _load_authority_family_template_set(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    if not path.exists():
        raise FileNotFoundError(f"Missing authority-family template file: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Authority-family template file must be a JSON object.")
    payload["_path"] = str(path)
    return payload


def _rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _case_rate(case_results: list[dict[str, Any]], field: str) -> float:
    return _rate(sum(1 for case in case_results if case.get(field)), len(case_results))


def _validate_safe_segment(value: str, label: str) -> None:
    if not SAFE_SEGMENT_RE.match(value):
        raise ValueError(f"Unsafe {label}: {value!r}")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _stable_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def _read_jsonl_if_exists(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
