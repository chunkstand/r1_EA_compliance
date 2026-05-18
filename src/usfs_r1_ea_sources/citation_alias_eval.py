from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from .source_register_proving import default_proving_output_path
from .source_register_proving import load_proving_report


CITATION_ALIAS_EVAL_SCHEMA_VERSION = "citation-alias-eval-report-v1"


@dataclass(frozen=True)
class CitationAliasEvalResult:
    output_path: Path
    summary: dict


def run_citation_alias_eval(
    *,
    output_dir: Path,
    report_path: Path | None = None,
    output_path: Path | None = None,
) -> CitationAliasEvalResult:
    output_dir = Path(output_dir)
    report = load_proving_report(output_dir, report_path)
    alias_report = report["alias_report"]
    expected_rows = alias_report["expected_rows"]
    blocked_rows = [
        row for row in alias_report["rows"] if row["blocked_alias_terms"]
    ]
    unresolved_expected_rows = [
        row["source_record_id"] for row in expected_rows if not row["resolved_with_context"]
    ]
    checks = [
        _check(
            "blocked_alias_rows_present",
            bool(blocked_rows),
            True,
            bool(blocked_rows),
        ),
        _check(
            "expected_alias_stress_rows_resolve_with_context",
            not unresolved_expected_rows,
            [],
            unresolved_expected_rows,
        ),
        _check(
            "identity_collision_count_zero",
            alias_report["identity_collision_count"] == 0,
            0,
            alias_report["identity_collision_count"],
        ),
        _check(
            "all_alias_rows_have_authority_document_ids",
            all(row["authority_document_id"] for row in alias_report["rows"]),
            True,
            all(row["authority_document_id"] for row in alias_report["rows"]),
        ),
    ]
    passed = all(check["passed"] for check in checks)
    output_path = output_path or default_proving_output_path(
        output_dir, "citation_alias_eval_report.json"
    )
    payload = {
        "schema_version": CITATION_ALIAS_EVAL_SCHEMA_VERSION,
        "source_set_id": report["source_set_id"],
        "checks": checks,
        "summary": {
            "passed": passed,
            "alias_row_count": alias_report["row_count"],
            "blocked_alias_row_count": alias_report["blocked_alias_row_count"],
            "output_path": str(output_path),
        },
    }
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return CitationAliasEvalResult(output_path=output_path, summary=payload["summary"])


def _check(name: str, passed: bool, expected, actual) -> dict:
    return {
        "name": name,
        "passed": passed,
        "expected": expected,
        "actual": actual,
    }
