from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit
import json

from .preflight import _is_failure_status


@dataclass(frozen=True)
class ReportResult:
    run_id: str
    report_path: Path
    summary: dict
    text: str


def build_run_report(*, output_dir: Path, run_id: str) -> ReportResult:
    run_dir = output_dir / "runs" / run_id
    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing run summary: {summary_path}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    manifest_path = Path(summary["manifest_path"])
    if not manifest_path.is_absolute():
        manifest_path = output_dir.parent / manifest_path
    if not manifest_path.exists():
        fallback = output_dir / "manifests" / f"{summary['mode']}_{run_id}.jsonl"
        if fallback.exists():
            manifest_path = fallback
        else:
            raise FileNotFoundError(f"Missing manifest: {manifest_path}")

    records = _read_jsonl(manifest_path)
    report_summary = summarize_records(summary, records)
    text = render_markdown_report(report_summary)
    report_path = run_dir / "operator_report.md"
    report_path.write_text(text, encoding="utf-8")
    return ReportResult(run_id=run_id, report_path=report_path, summary=report_summary, text=text)


def summarize_records(summary: dict, records: list[dict]) -> dict:
    status_counts = Counter(record["status"] for record in records)
    host_counts = Counter(urlsplit(record["normalized_url"]).netloc.lower() for record in records)
    failure_counts = Counter(
        (urlsplit(record["normalized_url"]).netloc.lower(), record["status"])
        for record in records
        if _is_failure_status(record["status"])
    )
    adapter_counts = Counter(
        record.get("validation", {}).get("adapter")
        for record in records
        if record.get("validation", {}).get("adapter")
    )
    repair_rows = [
        {
            "source_record_id": record["source_record_id"],
            "sheet": record["sheet"],
            "excel_row": record["excel_row"],
            "title": record["title"],
            "url": record["original_url"],
            "status": record["status"],
            "host": urlsplit(record["normalized_url"]).netloc.lower(),
            "error": (record.get("failure") or {}).get("error_message"),
            "suggested_action": suggested_action(record),
        }
        for record in records
        if _is_failure_status(record["status"])
    ]
    return {
        "run_id": summary["run_id"],
        "mode": summary["mode"],
        "workbook_sha256": summary.get("workbook_sha256"),
        "filtered_rows": len(records),
        "status_counts": dict(status_counts),
        "host_counts": dict(host_counts),
        "failure_counts": {
            f"{host}|{status}": count for (host, status), count in failure_counts.most_common()
        },
        "adapter_counts": dict(adapter_counts),
        "repair_rows": repair_rows,
        "summary": summary,
    }


def suggested_action(record: dict) -> str:
    host = urlsplit(record["normalized_url"]).netloc.lower()
    status = record["status"]
    if status == "challenge_page" and host in {"www.ecfr.gov", "www.federalregister.gov"}:
        return "Use official API/export adapter or verify adapter coverage."
    if status == "not_found" and host == "uscode.house.gov":
        return "Check for bad U.S. Code path or section query."
    if status == "not_found" and host == "www.fs.usda.gov":
        return "Repair stale Forest Service page URL or replace with current media/document URL."
    if status == "ssl_error":
        return "Review certificate chain; do not disable TLS globally."
    if status == "rate_limited":
        return "Retry later with lower host rate and preserve Retry-After if present."
    return "Manual source review required."


def render_markdown_report(report: dict) -> str:
    lines = [
        f"# Run Report: {report['run_id']}",
        "",
        f"- Mode: `{report['mode']}`",
        f"- Rows: `{report['filtered_rows']}`",
        f"- Workbook SHA256: `{report['workbook_sha256']}`",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in sorted(report["status_counts"].items()):
        lines.append(f"- `{status}`: {count}")
    lines.extend(["", "## Host Counts", ""])
    for host, count in sorted(report["host_counts"].items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{host}`: {count}")
    if report["adapter_counts"]:
        lines.extend(["", "## Adapter Counts", ""])
        for adapter, count in sorted(report["adapter_counts"].items()):
            lines.append(f"- `{adapter}`: {count}")
    lines.extend(["", "## Repair Queue", ""])
    if not report["repair_rows"]:
        lines.append("No failed rows require manual repair.")
    else:
        for row in report["repair_rows"]:
            lines.append(
                f"- `{row['source_record_id']}` row `{row['excel_row']}` "
                f"`{row['status']}` `{row['host']}`: {row['suggested_action']}"
            )
            lines.append(f"  URL: {row['url']}")
    lines.append("")
    return "\n".join(lines)


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
