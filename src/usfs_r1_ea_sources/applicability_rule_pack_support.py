from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import hashlib
import json
import re

from .records import sha256_file
from .rule_packs import DEFAULT_RULE_PACK_PATH


SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


def _artifact_paths(
    *,
    output_dir: Path,
    review_id: str,
    authority_universe_path: Path | None,
    decisions_path: Path | None,
    applicable_authorities_path: Path | None,
    non_applicable_authorities_path: Path | None,
    applicability_validation_path: Path | None,
    generated_rule_pack_path: Path | None,
    validation_output_path: Path | None,
) -> dict[str, Path]:
    applicability_dir = output_dir / "reviews" / review_id / "applicability"
    return {
        "applicability_dir": applicability_dir,
        "authority_universe": Path(authority_universe_path)
        if authority_universe_path
        else applicability_dir / "authority_universe_snapshot.json",
        "decisions": Path(decisions_path)
        if decisions_path
        else applicability_dir / "applicability_decisions.jsonl",
        "applicable_authorities": Path(applicable_authorities_path)
        if applicable_authorities_path
        else applicability_dir / "applicable_authorities.json",
        "non_applicable_authorities": Path(non_applicable_authorities_path)
        if non_applicable_authorities_path
        else applicability_dir / "non_applicable_authorities.json",
        "applicability_validation": Path(applicability_validation_path)
        if applicability_validation_path
        else applicability_dir / "applicability_validation.json",
        "generated_rule_pack": Path(generated_rule_pack_path)
        if generated_rule_pack_path
        else applicability_dir / "generated_rule_pack.json",
        "generated_rule_pack_validation": Path(validation_output_path)
        if validation_output_path
        else applicability_dir / "generated_rule_pack_validation.json",
    }


def _resolve_base_rule_pack_path(
    *,
    base_rule_pack_path: Path | None,
    authority_universe: dict[str, Any],
) -> Path:
    if base_rule_pack_path:
        return Path(base_rule_pack_path)
    artifact_paths = (
        authority_universe.get("artifact_paths")
        if isinstance(authority_universe.get("artifact_paths"), dict)
        else {}
    )
    inferred = str(artifact_paths.get("base_rule_pack_path") or "").strip()
    return Path(inferred) if inferred else DEFAULT_RULE_PACK_PATH


def _authority_ids(payload: dict[str, Any]) -> set[str]:
    return {
        str(row.get("candidate_authority_id") or "")
        for row in payload.get("authorities") or []
        if isinstance(row, dict) and row.get("candidate_authority_id")
    }


def _evidence_refs(spans: Any) -> list[dict[str, Any]]:
    refs = []
    for span in spans or []:
        if not isinstance(span, dict):
            continue
        refs.append(
            {
                "evidence_id": span.get("evidence_id"),
                "citation_label": span.get("citation_label"),
                "node_id": span.get("node_id"),
                "chunk_id": span.get("chunk_id"),
                "retrieval_result_id": span.get("retrieval_result_id"),
            }
        )
    return refs


def _check(
    name: str,
    passed: bool,
    failures: list[dict[str, Any]],
    details: dict[str, Any],
) -> dict[str, Any]:
    return {
        "name": name,
        "passed": passed,
        "failure_categories": sorted(
            {
                str(failure.get("failure_category") or "")
                for failure in failures
                if failure.get("failure_category")
            }
        ),
        "failures": failures,
        "details": details,
    }


def _failure(
    failure_category: str,
    *,
    artifact: str | None = None,
    path: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "failure_category": failure_category,
        "artifact": artifact,
        "path": path,
        "details": details or {},
    }


def _read_json_if_exists(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return value


def _read_required_json(path: Path, label: str) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    return _read_json_if_exists(path)


def _read_required_jsonl(path: Path, label: str) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing {label}: {path}")
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _optional_file_sha256(path: Path | None) -> str | None:
    return sha256_file(path) if path is not None and path.exists() else None


def _validation_artifact_path(
    validation_paths: dict[str, Any],
    artifact_name: str,
) -> Path | None:
    value = str(validation_paths.get(artifact_name) or "").strip()
    return Path(value) if value else None


def _json_field_from_path(path: Path | None, field: str) -> Any:
    if path is None or not path.exists():
        return None
    payload = _read_json_if_exists(path)
    return payload.get(field)


def _hash_from_validation(validation: dict[str, Any], field: str) -> Any:
    hashes = validation.get("hashes") if isinstance(validation.get("hashes"), dict) else {}
    return hashes.get(field)


def _safe_id(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._-")
    if not normalized:
        normalized = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return normalized[:160]


def _strings(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item or "").strip()]
    if value is None:
        return []
    text = str(value).strip()
    return [text] if text else []


def _first_present(*values: Any) -> Any:
    for value in values:
        if isinstance(value, list):
            if value:
                return value[0]
        elif value:
            return value
    return None


def _validate_safe_segment(value: str | None, label: str) -> None:
    if not value or not SAFE_SEGMENT_RE.fullmatch(value):
        raise ValueError(f"{label} must contain only letters, numbers, dot, underscore, or hyphen.")


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
