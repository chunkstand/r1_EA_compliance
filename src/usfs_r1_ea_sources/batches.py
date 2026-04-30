from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit
import csv
import json
import traceback

from .config import DownloaderConfig
from .download import run_download
from .records import WorkbookSource, slugify
from .report import build_run_report
from .validate_run import validate_run
from .workbook import load_canonical_sources


@dataclass(frozen=True)
class BatchDownloadResult:
    run_id: str
    plan_path: Path
    ledger_path: Path
    summary_path: Path
    report_path: Path
    repair_queue_path: Path
    summary: dict


def build_batch_plan(
    *,
    workbook_path: Path,
    config: DownloaderConfig,
    run_id_prefix: str,
    hosts: list[str] | None = None,
    batch_size: int = 5,
    limit_per_host: int | None = None,
) -> list[dict]:
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")
    sources = load_canonical_sources(workbook_path, config.workbook)
    available_hosts = {source_host(source) for source in sources}
    if hosts:
        unknown_hosts = sorted(set(hosts) - available_hosts)
        if unknown_hosts:
            raise ValueError(f"Batch plan requested hosts with no workbook sources: {unknown_hosts}")
    selected_hosts = hosts or sorted(available_hosts)
    batches: list[dict] = []
    for host in selected_hosts:
        host_sources = [source for source in sources if source_host(source) == host]
        if limit_per_host is not None:
            host_sources = host_sources[:limit_per_host]
        for index, chunk in enumerate(_chunks(host_sources, batch_size), start=1):
            batch_id = f"{run_id_prefix}-{slugify(host, max_length=64)}-{index:03d}"
            batches.append(
                {
                    "batch_id": batch_id,
                    "host": host,
                    "sequence": len(batches) + 1,
                    "host_sequence": index,
                    "row_count": len(chunk),
                    "source_record_ids": [source.source_record_id for source in chunk],
                    "workbook_rows": [
                        {
                            "source_record_id": source.source_record_id,
                            "sheet": source.sheet,
                            "excel_row": source.excel_row,
                            "title": source.title,
                            "effective_url": source.effective_url,
                        }
                        for source in chunk
                    ],
                }
            )
    return batches


def run_batch_downloads(
    *,
    workbook_path: Path,
    output_dir: Path,
    config: DownloaderConfig,
    run_id_prefix: str = "batch",
    hosts: list[str] | None = None,
    batch_size: int = 5,
    limit_per_host: int | None = None,
    force: bool = False,
    plan_only: bool = False,
    resume: bool = False,
    continue_on_failure: bool = False,
    downloader=run_download,
    reporter=build_run_report,
    validator=validate_run,
) -> BatchDownloadResult:
    parent_run_id = f"{run_id_prefix}-batches"
    parent_run_dir = output_dir / config.outputs.run_dir / parent_run_id
    parent_run_dir.mkdir(parents=True, exist_ok=True)

    plan_path = parent_run_dir / "batch_plan.json"
    ledger_path = parent_run_dir / "batch_ledger.json"
    summary_path = parent_run_dir / "summary.json"
    report_path = parent_run_dir / "operator_report.md"
    repair_queue_path = parent_run_dir / "repair_queue.csv"

    planned_batches = build_batch_plan(
        workbook_path=workbook_path,
        config=config,
        run_id_prefix=run_id_prefix,
        hosts=hosts,
        batch_size=batch_size,
        limit_per_host=limit_per_host,
    )
    _write_json(
        plan_path,
        {
            "run_id": parent_run_id,
            "run_id_prefix": run_id_prefix,
            "batch_size": batch_size,
            "limit_per_host": limit_per_host,
            "hosts_requested": hosts,
            "batch_count": len(planned_batches),
            "planned_row_count": sum(batch["row_count"] for batch in planned_batches),
            "batches": planned_batches,
        },
    )

    ledger_entries = _initial_ledger(planned_batches)
    if resume and ledger_path.exists():
        existing_entries = _read_json(ledger_path).get("batches", [])
        ledger_entries = _merge_resume_ledger(ledger_entries, existing_entries)

    repair_rows: list[dict] = []
    stopped_after_batch_id = None
    if not plan_only:
        for entry in ledger_entries:
            if resume and entry.get("status") == "passed" and not force:
                continue
            entry.update({"status": "running", "error": None})
            _write_ledger(ledger_path, parent_run_id, ledger_entries)
            try:
                download_result = downloader(
                    workbook_path=workbook_path,
                    output_dir=output_dir,
                    config=config,
                    run_id=entry["batch_id"],
                    host_filter=entry["host"],
                    source_record_ids=set(entry["source_record_ids"]),
                    force=force,
                )
                report_result = reporter(output_dir=output_dir, run_id=entry["batch_id"])
                validation_result = validator(output_dir=output_dir, run_id=entry["batch_id"])
                manifest_metrics = _batch_manifest_metrics(download_result.manifest_path)
                batch_repair_rows = [
                    {**row, "batch_id": entry["batch_id"], "run_id": entry["batch_id"]}
                    for row in report_result.summary.get("repair_rows", [])
                ]
                repair_rows.extend(batch_repair_rows)
                failed_count = int(download_result.summary.get("failed_count") or 0)
                needs_review_count = int(download_result.summary.get("needs_review_count") or 0)
                entry.update(
                    {
                        "status": _batch_status(
                            validation_result.passed,
                            failed_count,
                            needs_review_count,
                        ),
                        "filtered_rows": download_result.summary.get("filtered_rows"),
                        "checked_url_count": download_result.summary.get("checked_url_count"),
                        "downloaded_count": download_result.summary.get("downloaded_count"),
                        "downloaded_existing_count": download_result.summary.get(
                            "downloaded_existing_count"
                        ),
                        "duplicate_content_count": download_result.summary.get(
                            "duplicate_content_count"
                        ),
                        "duplicate_url_count": download_result.summary.get("duplicate_url_count"),
                        "failed_count": failed_count,
                        "needs_review_count": needs_review_count,
                        "status_counts": download_result.summary.get("status_counts", {}),
                        "artifact_count": manifest_metrics["artifact_count"],
                        "browser_compatible_user_agent_count": manifest_metrics[
                            "browser_compatible_user_agent_count"
                        ],
                        "gate_passed": validation_result.passed,
                        "manifest_path": str(download_result.manifest_path),
                        "report_path": str(report_result.report_path),
                        "acceptance_gate_path": str(validation_result.validation_path),
                    }
                )
            except Exception as error:  # pragma: no cover - defensive ledger preservation
                entry.update(
                    {
                        "status": "failed",
                        "error": {
                            "class": type(error).__name__,
                            "message": str(error),
                            "traceback": traceback.format_exc(),
                        },
                    }
                )
            _write_ledger(ledger_path, parent_run_id, ledger_entries)
            if entry["status"] != "passed" and not continue_on_failure:
                stopped_after_batch_id = entry["batch_id"]
                break

    _write_ledger(ledger_path, parent_run_id, ledger_entries)
    _write_repair_queue(repair_queue_path, repair_rows)
    summary = _batch_summary(
        parent_run_id=parent_run_id,
        run_id_prefix=run_id_prefix,
        batch_size=batch_size,
        limit_per_host=limit_per_host,
        plan_only=plan_only,
        stopped_after_batch_id=stopped_after_batch_id,
        ledger_entries=ledger_entries,
        repair_queue_path=repair_queue_path,
        plan_path=plan_path,
        ledger_path=ledger_path,
    )
    _write_json(summary_path, summary)
    report_path.write_text(render_batch_report(summary, ledger_entries), encoding="utf-8")
    return BatchDownloadResult(
        run_id=parent_run_id,
        plan_path=plan_path,
        ledger_path=ledger_path,
        summary_path=summary_path,
        report_path=report_path,
        repair_queue_path=repair_queue_path,
        summary=summary,
    )


def render_batch_report(summary: dict, ledger_entries: list[dict]) -> str:
    lines = [
        f"# Batch Download Summary: {summary['run_id']}",
        "",
        f"- Batches: `{summary['batch_count']}`",
        f"- Planned rows: `{summary['planned_row_count']}`",
        f"- Passed: `{summary['passed_batch_count']}`",
        f"- Failed: `{summary['failed_batch_count']}`",
        f"- Needs repair: `{summary['needs_repair_batch_count']}`",
        f"- Artifacts: `{summary['artifact_count']}`",
        f"- Browser-compatible UA rows: `{summary['browser_compatible_user_agent_count']}`",
        f"- All passed: `{summary['all_passed']}`",
        "",
        "## Batches",
        "",
    ]
    for entry in ledger_entries:
        lines.append(
            f"- `{entry['batch_id']}` `{entry['status']}` host `{entry['host']}` "
            f"rows `{entry['row_count']}` failed `{entry.get('failed_count', 0)}` "
            f"gate `{entry.get('gate_passed')}`"
        )
    lines.append("")
    return "\n".join(lines)


def source_host(source: WorkbookSource) -> str:
    return urlsplit(source.normalized_url).netloc.lower()


def _chunks(sources: list[WorkbookSource], size: int) -> list[list[WorkbookSource]]:
    return [sources[index : index + size] for index in range(0, len(sources), size)]


def _initial_ledger(planned_batches: list[dict]) -> list[dict]:
    return [
        {
            "batch_id": batch["batch_id"],
            "host": batch["host"],
            "sequence": batch["sequence"],
            "host_sequence": batch["host_sequence"],
            "row_count": batch["row_count"],
            "source_record_ids": batch["source_record_ids"],
            "status": "planned",
            "gate_passed": None,
            "failed_count": None,
            "needs_review_count": None,
            "error": None,
        }
        for batch in planned_batches
    ]


def _merge_resume_ledger(planned_entries: list[dict], existing_entries: list[dict]) -> list[dict]:
    existing_by_id = {entry["batch_id"]: entry for entry in existing_entries}
    merged = []
    for planned in planned_entries:
        existing = existing_by_id.get(planned["batch_id"])
        if existing and existing.get("source_record_ids") == planned["source_record_ids"]:
            merged.append({**planned, **existing})
        else:
            merged.append(planned)
    return merged


def _batch_status(gate_passed: bool, failed_count: int, needs_review_count: int) -> str:
    if not gate_passed:
        return "failed"
    if failed_count or needs_review_count:
        return "needs_repair"
    return "passed"


def _batch_summary(
    *,
    parent_run_id: str,
    run_id_prefix: str,
    batch_size: int,
    limit_per_host: int | None,
    plan_only: bool,
    stopped_after_batch_id: str | None,
    ledger_entries: list[dict],
    repair_queue_path: Path,
    plan_path: Path,
    ledger_path: Path,
) -> dict:
    status_counts: dict[str, int] = {}
    for entry in ledger_entries:
        status_counts[entry["status"]] = status_counts.get(entry["status"], 0) + 1
    artifact_count = sum(int(entry.get("artifact_count") or 0) for entry in ledger_entries)
    browser_compatible_count = sum(
        int(entry.get("browser_compatible_user_agent_count") or 0) for entry in ledger_entries
    )
    return {
        "run_id": parent_run_id,
        "run_id_prefix": run_id_prefix,
        "batch_size": batch_size,
        "limit_per_host": limit_per_host,
        "plan_only": plan_only,
        "batch_count": len(ledger_entries),
        "planned_row_count": sum(entry["row_count"] for entry in ledger_entries),
        "passed_batch_count": status_counts.get("passed", 0),
        "failed_batch_count": status_counts.get("failed", 0),
        "needs_repair_batch_count": status_counts.get("needs_repair", 0),
        "planned_batch_count": status_counts.get("planned", 0),
        "running_batch_count": status_counts.get("running", 0),
        "artifact_count": artifact_count,
        "browser_compatible_user_agent_count": browser_compatible_count,
        "all_passed": bool(ledger_entries)
        and all(entry["status"] == "passed" for entry in ledger_entries),
        "stopped_after_batch_id": stopped_after_batch_id,
        "status_counts": status_counts,
        "plan_path": str(plan_path),
        "ledger_path": str(ledger_path),
        "repair_queue_path": str(repair_queue_path),
    }


def _write_ledger(path: Path, run_id: str, entries: list[dict]) -> None:
    _write_json(path, {"run_id": run_id, "batches": entries})


def _batch_manifest_metrics(manifest_path: Path) -> dict:
    if not manifest_path.exists():
        return {"artifact_count": 0, "browser_compatible_user_agent_count": 0}
    artifact_sha256s = set()
    browser_compatible_count = 0
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("artifact_sha256"):
            artifact_sha256s.add(record["artifact_sha256"])
        if record.get("validation", {}).get("browser_compatible_user_agent"):
            browser_compatible_count += 1
    return {
        "artifact_count": len(artifact_sha256s),
        "browser_compatible_user_agent_count": browser_compatible_count,
    }


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_repair_queue(path: Path, rows: list[dict]) -> None:
    headers = [
        "batch_id",
        "run_id",
        "source_record_id",
        "sheet",
        "excel_row",
        "title",
        "url",
        "status",
        "host",
        "error",
        "suggested_action",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header) for header in headers})
