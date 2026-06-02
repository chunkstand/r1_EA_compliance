from __future__ import annotations

from pathlib import Path
import hashlib
import json

from usfs_r1_ea_sources.forest_plan_inventory_build_manifest import (
    load_region1_forest_plan_inventory_build_manifest,
)


def _write_download_run(
    output_dir: Path,
    run_id: str,
    *,
    source_record_id: str = "R1EA-001",
    artifact_body: bytes | None = None,
    content_type: str = "text/html",
    suffix: str = ".html",
) -> Path:
    run_dir = output_dir / "runs" / run_id
    manifest_dir = output_dir / "manifests"
    run_dir.mkdir(parents=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"download_{run_id}.jsonl"
    body = artifact_body or _artifact_body()
    artifact = output_dir / "artifacts" / "raw" / f"{run_id}-{source_record_id}{suffix}"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_bytes(body)
    record = {
        "run_id": run_id,
        "source_record_id": source_record_id,
        "status": "downloaded",
        "artifact_path": str(artifact),
        "artifact_sha256": _artifact_sha256(body),
        "artifact_byte_size": len(body),
        "content_type": content_type,
        "fetch_timestamp": "2026-04-30T00:00:00Z",
        "final_url": "https://example.test/final",
    }
    manifest_path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
    summary = {
        "run_id": run_id,
        "mode": "download",
        "manifest_path": str(manifest_path),
        "filtered_rows": 1,
        "status_counts": {"downloaded": 1},
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, sort_keys=True), encoding="utf-8")
    return manifest_path


def _write_download_run_records(
    output_dir: Path,
    run_id: str,
    *,
    source_record_ids: list[str],
    content_type: str,
) -> Path:
    run_dir = output_dir / "runs" / run_id
    manifest_dir = output_dir / "manifests"
    artifact_dir = output_dir / "artifacts" / "raw"
    run_dir.mkdir(parents=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_dir / f"download_{run_id}.jsonl"
    extension = "pdf" if content_type == "application/pdf" else "html"
    records = []
    for source_record_id in source_record_ids:
        if extension == "pdf":
            body = f"%PDF-1.4 catalog artifact {source_record_id}".encode("utf-8") + b" " * 128
        else:
            body = (
                f"<html><body>catalog artifact {source_record_id}</body></html>".encode("utf-8")
                + b" " * 128
            )
        artifact = artifact_dir / f"{run_id}-{source_record_id}.{extension}"
        artifact.write_bytes(body)
        records.append(
            {
                "run_id": run_id,
                "source_record_id": source_record_id,
                "status": "downloaded",
                "artifact_path": str(artifact),
                "artifact_sha256": _artifact_sha256(body),
                "artifact_byte_size": len(body),
                "content_type": content_type,
                "fetch_timestamp": "2026-04-30T00:00:00Z",
                "final_url": f"https://example.test/{source_record_id}",
            }
        )
    manifest_path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )
    summary = {
        "run_id": run_id,
        "mode": "download",
        "manifest_path": str(manifest_path),
        "filtered_rows": len(source_record_ids),
        "status_counts": {"downloaded": len(source_record_ids)},
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, sort_keys=True), encoding="utf-8")
    return manifest_path


def _write_batch_run(output_dir: Path, batch_run_id: str, batches: list[tuple[str, Path]]) -> None:
    run_dir = output_dir / "runs" / batch_run_id
    run_dir.mkdir(parents=True)
    ledger_path = run_dir / "batch_ledger.json"
    ledger_batches = [
        {
            "batch_id": batch_id,
            "status": "passed",
            "gate_passed": True,
            "manifest_path": str(manifest_path),
            "source_record_ids": [
                record["source_record_id"] for record in _read_jsonl(manifest_path)
            ],
        }
        for batch_id, manifest_path in batches
    ]
    ledger_path.write_text(
        json.dumps({"run_id": batch_run_id, "batches": ledger_batches}, sort_keys=True),
        encoding="utf-8",
    )
    summary = {
        "run_id": batch_run_id,
        "all_passed": True,
        "batch_count": len(batches),
        "failed_batch_count": 0,
        "needs_repair_batch_count": 0,
        "ledger_path": str(ledger_path),
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, sort_keys=True), encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _artifact_body() -> bytes:
    return b"<html><body>catalog artifact</body></html>" + b" " * 128


def _artifact_sha256(body: bytes | None = None) -> str:
    return hashlib.sha256(body or _artifact_body()).hexdigest()


def _source_delta_primary_plan_source_record_ids(register) -> list[str]:
    manifest = load_region1_forest_plan_inventory_build_manifest()
    source_delta_ids = {source.source_record_id for source in register.source_delta_sources}
    return sorted(
        row.primary_plan_source_record_id
        for row in manifest.profile_rows
        if row.primary_plan_source_record_id in source_delta_ids
    )


def _source_delta_catalog_role_counts(register) -> dict[str, int]:
    primary_count = len(_source_delta_primary_plan_source_record_ids(register))
    source_delta_count = len(register.source_delta_sources)
    counts = {
        "forest_plan": primary_count,
        "forest_plan_support": source_delta_count - primary_count,
    }
    return {role: count for role, count in counts.items() if count}


def _merged_catalog_role_counts(register) -> dict[str, int]:
    source_delta_counts = _source_delta_catalog_role_counts(register)
    counts = {
        "forest_plan": 28 + source_delta_counts.get("forest_plan", 0),
        "forest_plan_support": source_delta_counts.get("forest_plan_support", 0),
    }
    return {role: count for role, count in counts.items() if count}


def _check(validation: dict, name: str) -> dict:
    for check in validation["checks"]:
        if check["name"] == name:
            return check
    raise AssertionError(f"Missing validation check {name}")
