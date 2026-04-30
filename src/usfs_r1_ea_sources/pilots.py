from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit
import json

from .config import DownloaderConfig
from .download import run_download
from .records import slugify
from .report import build_run_report
from .validate_run import validate_run
from .workbook import load_canonical_sources


@dataclass(frozen=True)
class HostPilotResult:
    run_id: str
    summary_path: Path
    report_path: Path
    summary: dict


def discover_canonical_hosts(*, workbook_path: Path, config: DownloaderConfig) -> list[str]:
    sources = load_canonical_sources(workbook_path, config.workbook)
    hosts = {urlsplit(source.normalized_url).netloc.lower() for source in sources}
    return sorted(hosts)


def run_host_pilots(
    *,
    workbook_path: Path,
    output_dir: Path,
    config: DownloaderConfig,
    run_id_prefix: str = "host-pilot",
    hosts: list[str] | None = None,
    limit_per_host: int | None = None,
    force: bool = False,
    downloader=run_download,
    reporter=build_run_report,
    validator=validate_run,
) -> HostPilotResult:
    selected_hosts = hosts or discover_canonical_hosts(workbook_path=workbook_path, config=config)
    parent_run_id = f"{run_id_prefix}-host-pilots"
    parent_run_dir = output_dir / config.outputs.run_dir / parent_run_id
    parent_run_dir.mkdir(parents=True, exist_ok=True)

    host_results = []
    for host in selected_hosts:
        host_run_id = f"{run_id_prefix}-{slugify(host, max_length=64)}"
        download_result = downloader(
            workbook_path=workbook_path,
            output_dir=output_dir,
            config=config,
            run_id=host_run_id,
            host_filter=host,
            limit=limit_per_host,
            force=force,
        )
        report_result = reporter(output_dir=output_dir, run_id=host_run_id)
        validation_result = validator(output_dir=output_dir, run_id=host_run_id)
        failed_count = int(download_result.summary.get("failed_count") or 0)
        ready = validation_result.passed and failed_count == 0
        host_results.append(
            {
                "host": host,
                "run_id": host_run_id,
                "filtered_rows": download_result.summary.get("filtered_rows"),
                "filtered_override_count": download_result.summary.get("filtered_override_count"),
                "checked_url_count": download_result.summary.get("checked_url_count"),
                "downloaded_count": download_result.summary.get("downloaded_count"),
                "downloaded_existing_count": download_result.summary.get("downloaded_existing_count"),
                "duplicate_content_count": download_result.summary.get("duplicate_content_count"),
                "duplicate_url_count": download_result.summary.get("duplicate_url_count"),
                "failed_count": failed_count,
                "needs_review_count": download_result.summary.get("needs_review_count"),
                "status_counts": download_result.summary.get("status_counts", {}),
                "gate_passed": validation_result.passed,
                "ready_for_full_download": ready,
                "manifest_path": str(download_result.manifest_path),
                "report_path": str(report_result.report_path),
                "acceptance_gate_path": str(validation_result.validation_path),
            }
        )

    summary = {
        "run_id": parent_run_id,
        "run_id_prefix": run_id_prefix,
        "hosts_requested": selected_hosts,
        "host_count": len(host_results),
        "ready_host_count": sum(1 for result in host_results if result["ready_for_full_download"]),
        "blocked_host_count": sum(1 for result in host_results if not result["ready_for_full_download"]),
        "all_ready": all(result["ready_for_full_download"] for result in host_results),
        "host_results": host_results,
    }
    summary_path = parent_run_dir / "summary.json"
    report_path = parent_run_dir / "operator_report.md"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(render_host_pilot_report(summary), encoding="utf-8")
    return HostPilotResult(
        run_id=parent_run_id,
        summary_path=summary_path,
        report_path=report_path,
        summary=summary,
    )


def render_host_pilot_report(summary: dict) -> str:
    lines = [
        f"# Host Pilot Summary: {summary['run_id']}",
        "",
        f"- Hosts: `{summary['host_count']}`",
        f"- Ready: `{summary['ready_host_count']}`",
        f"- Blocked: `{summary['blocked_host_count']}`",
        f"- All ready: `{summary['all_ready']}`",
        "",
        "## Hosts",
        "",
    ]
    for result in summary["host_results"]:
        state = "ready" if result["ready_for_full_download"] else "blocked"
        lines.append(
            f"- `{result['host']}`: `{state}`, rows `{result['filtered_rows']}`, "
            f"failed `{result['failed_count']}`, gate `{result['gate_passed']}`"
        )
        lines.append(f"  Run: `{result['run_id']}`")
    lines.append("")
    return "\n".join(lines)
