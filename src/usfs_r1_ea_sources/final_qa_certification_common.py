from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path("config/east_crazies_final_qa_certification_v1.json")
DEFAULT_EXPECTED_SUMMARY_PATH = Path(
    "config/fixtures/final_qa/v1_ecid_final_qa_expected_summary.json"
)

REPORT_FILENAME = "east_crazies_final_qa_certification.json"
MARKDOWN_FILENAME = "east_crazies_final_qa_certification.md"
PDF_FILENAME = "east_crazies_final_qa_certification.pdf"
MANIFEST_FILENAME = "east_crazies_final_qa_certification_manifest.json"
VALIDATION_FILENAME = "east_crazies_final_qa_certification_validation.json"
VALIDATION_SCHEMA_VERSION = "east-crazies-final-qa-certification-validation-v1"
GENERATOR_VERSION = "final-qa-certification-sequence-3"
HUMAN_JUDGMENT_CAVEAT = (
    "This packet supports review but does not replace responsible official, "
    "line officer, counsel, or specialist judgment."
)


@dataclass(frozen=True)
class FinalQACertificationResult:
    summary: dict[str, Any]
    report_path: Path
    markdown_path: Path
    pdf_path: Path
    manifest_path: Path
    validation_path: Path


@dataclass(frozen=True)
class OutputPaths:
    results_dir: Path
    report_path: Path
    markdown_path: Path
    pdf_path: Path
    manifest_path: Path
    validation_path: Path


def _output_paths(
    output_dir: Path,
    review_id: str,
    results_dir: Path | None,
) -> OutputPaths:
    resolved_results_dir = results_dir or output_dir / "reviews" / review_id / "final_qa"
    return OutputPaths(
        results_dir=resolved_results_dir,
        report_path=resolved_results_dir / REPORT_FILENAME,
        markdown_path=resolved_results_dir / MARKDOWN_FILENAME,
        pdf_path=resolved_results_dir / PDF_FILENAME,
        manifest_path=resolved_results_dir / MANIFEST_FILENAME,
        validation_path=resolved_results_dir / VALIDATION_FILENAME,
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _resolve_artifact_path(path: str, output_dir: Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    parts = candidate.parts
    if parts and parts[0] == "source_library":
        return output_dir.joinpath(*parts[1:])
    return candidate


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _selector_value(data: Any, selector: str) -> Any:
    current = data
    for part in selector.split("."):
        if isinstance(current, Mapping):
            current = current.get(part)
        else:
            return None
    return current


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _summary_or_self(data: Any) -> Any:
    if isinstance(data, Mapping) and isinstance(data.get("summary"), Mapping):
        return data["summary"]
    return data


def _checks_passed(checks: list[Mapping[str, Any]]) -> bool:
    return all(check.get("passed") for check in checks)


def _add_check(
    checks: list[dict[str, Any]],
    *,
    name: str,
    passed: bool,
    category: str,
    details: Mapping[str, Any],
) -> None:
    checks.append(
        {
            "name": name,
            "passed": bool(passed),
            "failure_category": None if passed else category,
            "details": dict(details),
        }
    )


def _summarize_checks(
    *,
    checks: list[dict[str, Any]],
    review_id: str,
    source_set_id: str,
    paths: OutputPaths,
    output_written: bool,
) -> dict[str, Any]:
    failed = [check for check in checks if not check.get("passed")]
    failure_categories = Counter(
        check["failure_category"] for check in failed if check.get("failure_category")
    )
    return {
        "passed": not failed,
        "machine_replay_status": "passed" if not failed else "failed",
        "review_id": review_id,
        "source_set_id": source_set_id,
        "check_count": len(checks),
        "passed_check_count": len(checks) - len(failed),
        "failed_check_count": len(failed),
        "failure_category_counts": dict(sorted(failure_categories.items())),
        "report_path": str(paths.report_path),
        "markdown_path": str(paths.markdown_path),
        "pdf_path": str(paths.pdf_path),
        "manifest_path": str(paths.manifest_path),
        "validation_path": str(paths.validation_path),
        "output_written": output_written,
    }


def _validation_result_payload(summary: Mapping[str, Any], paths: OutputPaths) -> dict[str, Any]:
    return {
        "schema_version": VALIDATION_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "generator_version": GENERATOR_VERSION,
        "review_id": summary.get("review_id"),
        "source_set_id": summary.get("source_set_id"),
        "passed": bool(summary.get("passed")),
        "machine_replay_status": summary.get("machine_replay_status"),
        "check_count": summary.get("check_count"),
        "passed_check_count": summary.get("passed_check_count"),
        "failed_check_count": summary.get("failed_check_count"),
        "failure_category_counts": summary.get("failure_category_counts", {}),
        "output_written": bool(summary.get("output_written")),
        "output_files": {
            "json": str(paths.report_path),
            "markdown": str(paths.markdown_path),
            "pdf": str(paths.pdf_path),
            "manifest": str(paths.manifest_path),
            "validation": str(paths.validation_path),
        },
        "output_hashes": _validation_output_hashes(paths),
    }


def _validation_output_hashes(paths: OutputPaths) -> dict[str, str]:
    hash_paths = {
        "json_sha256": paths.report_path,
        "markdown_sha256": paths.markdown_path,
        "pdf_sha256": paths.pdf_path,
        "manifest_sha256": paths.manifest_path,
    }
    return {
        key: _sha256_file(path)
        for key, path in hash_paths.items()
        if path.exists()
    }


def _utc_now() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
