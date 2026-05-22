from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import json

def _render_markdown(report: dict[str, Any]) -> str:
    summary_lines = [
        "# Region 1 Forest-Plan Source-Delta Readiness",
        "",
        f"- Schema: `{report['schema_version']}`",
        f"- Created: `{report['created_at']}`",
        f"- Gate passed: `{str(report['passed']).lower()}`",
        f"- Source-delta rows: `{report['register']['source_delta_count']}`",
        f"- Catalog-confirmed rows: `{report['register']['catalog_confirmed_count']}`",
        f"- Official-source gaps: `{report['register']['gap_count']}`",
        "- Gap source IDs: "
        + ", ".join(f"`{source_id}`" for source_id in report["register"]["skipped_gap_source_record_ids"]),
        f"- Official-source gap evidence: `{report['official_source_gap_evidence']['path']}`",
        f"- Scoped source-delta source set: `{report['scoped_source_delta_catalog']['source_set_id']}`",
        (
            f"- Merged source-delta source set: "
            f"`{report['merged_source_delta_catalog']['source_set_id']}`"
        )
        if report.get("merged_source_delta_catalog")
        else "- Merged source-delta source set: `not_evaluated`",
        f"- Active canonical source set: `{report['active_canonical_catalog']['source_set_id']}`",
        f"- Extraction source set: `{report['extraction_readiness']['source_set_id']}`",
        f"- Extraction readiness: `{report['extraction_readiness']['status']}`",
        f"- Retrieval readiness: `{report['retrieval_readiness']['status']}`",
        f"- Retrieval eval passed: `{str(report['retrieval_readiness']['retrieval_eval_passed']).lower()}`",
        "",
        "## Checks",
        "",
    ]
    for check in report["checks"]:
        marker = "pass" if check["passed"] else "fail"
        summary_lines.append(f"- `{marker}` `{check['name']}`")
    summary_lines.extend(
        [
            "",
            "## Forest-Profile Readiness",
            "",
        ]
    )
    for unit in report["forest_profile_readiness"]["profile_rows"]:
        blockers = ", ".join(
            f"`{item}`" for item in unit["blocker_source_record_ids"]
        ) or "`none`"
        summary_lines.append(
            "- "
            + f"`{unit['forest_unit_id']}`: "
            + f"status=`{unit['profile_readiness_status']}`, "
            + f"retrieval_ready=`{unit['retrieval_ready_source_record_count']}/{unit['source_requirement_count']}`, "
            + f"blockers={blockers}"
        )
    summary_lines.append("")
    return "\n".join(summary_lines)

def _read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))

def _read_jsonl_if_exists(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
