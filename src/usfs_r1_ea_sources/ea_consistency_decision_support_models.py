from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import hashlib
import json
import textwrap

from .pdf_object_writer import write_paginated_line_pdf


REPORT_SCHEMA_VERSION = "ea-consistency-decision-support-report-v1"
MANIFEST_SCHEMA_VERSION = "ea-consistency-decision-support-manifest-v1"
GENERATOR_VERSION = "ea-consistency-decision-support-generator-v1"
DEFAULT_CONFIG_PATH = Path("config/ea_consistency_decision_support_v1.json")
DEFAULT_EXPECTED_SUMMARY_PATH = Path(
    "config/fixtures/decision_support/v1_ecid_decision_support_expected_summary.json"
)
REVIEW_PACKET_ARTIFACT_KEYS = {
    "review_packet_row_inventory",
    "compliance_matrix_render_manifest",
    "review_packet_index",
    "review_packet_index_validation",
    "review_packet_index_pdf",
}


@dataclass(frozen=True)
class EAConsistencyDecisionSupportResult:
    output_dir: Path
    report_path: Path
    markdown_path: Path
    pdf_path: Path
    manifest_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class EAConsistencyDecisionSupportValidationResult:
    output_dir: Path
    report_path: Path
    markdown_path: Path
    pdf_path: Path
    manifest_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class _LoadedArtifact:
    key: str
    path: Path
    artifact_type: str
    required: bool
    payload: Any
    exists: bool
    parse_ok: bool
    sha256: str | None
    failure_category: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class _DecisionSupportContext:
    output_dir: Path
    review_dir: Path
    review_id: str
    source_set_id: str
    config_path: Path
    expected_summary_path: Path
    config: dict[str, Any]
    expected: dict[str, Any]
    artifacts: dict[str, _LoadedArtifact]

    def payload(self, key: str) -> Any:
        return self.artifacts[key].payload


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _dict_list(value: Any) -> list[dict[str, Any]]:
    return [item for item in _list(value) if isinstance(item, dict)]


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _strings(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item or "").strip()]
    if str(value or "").strip():
        return [str(value)]
    return []


def _int(*values: Any) -> int:
    for value in values:
        if isinstance(value, bool):
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return 0


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _truncate(value: str, max_chars: int) -> str:
    normalized = " ".join(str(value).split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 3].rstrip() + "..."


def _md_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def _wrap_pdf_line(line: str, width: int = 145) -> list[str]:
    if len(line) <= width:
        return [line]
    return textwrap.wrap(
        line,
        width=width,
        subsequent_indent="    ",
        break_long_words=False,
        break_on_hyphens=False,
    )


def _paginate_pdf_lines(lines: list[str], *, max_lines: int) -> list[list[str]]:
    pages: list[list[str]] = []
    page: list[str] = []
    for line in lines:
        if len(page) >= max_lines:
            pages.append(page)
            page = []
        page.append(line)
    if page:
        pages.append(page)
    return pages or [["EA Consistency Decision Support"]]


def _write_simple_pdf(path: Path, pages: list[list[str]], *, title: str) -> None:
    write_paginated_line_pdf(
        path,
        pages,
        title=title,
        text_transform=_pdf_text,
    )


def _pdf_text(value: str) -> str:
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00a7": "Sec.",
    }
    text = str(value)
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def _validation_result(
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    *,
    counts: dict[str, Any],
) -> dict[str, Any]:
    return {
        "passed": not failures,
        "checks": checks,
        "failures": failures,
        "failure_categories": sorted(
            {failure["failure_category"] for failure in failures}
        ),
        "counts": counts,
    }


def _record_check(
    checks: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    *,
    name: str,
    passed: bool,
    failure_category: str,
    source_selector: str,
    expected: Any,
    actual: Any,
    message: str | None = None,
) -> None:
    check = {
        "name": name,
        "passed": bool(passed),
        "failure_category": failure_category,
        "source_selector": source_selector,
        "expected": expected,
        "actual": actual,
    }
    if message:
        check["message"] = message
    checks.append(check)
    if not passed:
        failures.append(check)
