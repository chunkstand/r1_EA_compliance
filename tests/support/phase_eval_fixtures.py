from __future__ import annotations

from contextlib import closing
from pathlib import Path
import hashlib
import json
import sqlite3


def write_catalog_validation(output_dir: Path, *, passed: bool) -> None:
    write_catalog_validation_for_dir(output_dir / "catalog", passed=passed)


def write_catalog_validation_for_dir(catalog_dir: Path, *, passed: bool) -> None:
    path = catalog_dir / "catalog_validation.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"passed": passed}, sort_keys=True), encoding="utf-8")


def write_extraction_diagnostics(
    output_dir: Path,
    source_set_id: str,
    *,
    source_record_ids: list[str],
    skipped_source_record_ids: list[str] | None = None,
    catalog_source_count: int | None = None,
    filters: dict | None = None,
) -> None:
    diagnostics_dir = output_dir / "derived" / source_set_id / "diagnostics"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    (diagnostics_dir / "extraction_validation.json").write_text(
        json.dumps({"passed": True}, sort_keys=True),
        encoding="utf-8",
    )
    skipped_source_record_ids = skipped_source_record_ids or []
    manifest_records = [
        {
            "source_set_id": source_set_id,
            "source_record_id": source_record_id,
            "status": "extracted",
        }
        for source_record_id in source_record_ids
    ]
    manifest_records.extend(
        {
            "source_set_id": source_set_id,
            "source_record_id": source_record_id,
            "status": "skipped_excluded",
        }
        for source_record_id in skipped_source_record_ids
    )
    (diagnostics_dir / "extraction_manifest.jsonl").write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in manifest_records),
        encoding="utf-8",
    )
    selected_count = len(source_record_ids) + len(skipped_source_record_ids)
    catalog_count = catalog_source_count if catalog_source_count is not None else selected_count
    required_count = catalog_count - len(skipped_source_record_ids)
    summary = {
        "source_set_id": source_set_id,
        "catalog_source_count": catalog_count,
        "artifact_bearing_source_count": required_count,
        "required_extraction_source_count": required_count,
        "selected_source_count": selected_count,
        "selected_required_extraction_source_count": len(source_record_ids),
        "extracted_count": len(source_record_ids),
        "failed_count": 0,
        "skipped_excluded_count": len(skipped_source_record_ids),
        "filters": filters or {"id": None, "parser": None, "limit": None},
    }
    (diagnostics_dir / "summary.json").write_text(
        json.dumps(summary, sort_keys=True),
        encoding="utf-8",
    )


def write_chunks(output_dir: Path, source_set_id: str, chunks: list[dict]) -> Path:
    path = output_dir / "derived" / source_set_id / "chunks" / "chunks.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    for chunk in chunks:
        artifact_path = output_dir / chunk["artifact_path"]
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(f"artifact for {chunk['source_record_id']}", encoding="utf-8")
        text_path = output_dir / chunk["source_text_path"]
        text_path.parent.mkdir(parents=True, exist_ok=True)
        text_path.write_text(chunk["text"], encoding="utf-8")
    path.write_text(
        "".join(json.dumps(chunk, sort_keys=True) + "\n" for chunk in chunks),
        encoding="utf-8",
    )
    return path


def direct_eval_result_payload(
    *,
    contract_path: Path,
    eval_id: str,
    source_set_id: str,
) -> dict:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    coverage_requirements = contract.get("coverage_requirements", {})
    case_count = int(
        coverage_requirements.get("case_count")
        or ((contract.get("metric_thresholds") or {}).get("case_count") or {}).get("min")
        or 1
    )
    metrics = {}
    for metric_name, threshold in (contract.get("metric_thresholds") or {}).items():
        if not isinstance(threshold, dict):
            continue
        if "min" in threshold:
            metrics[metric_name] = threshold["min"]
        elif "max" in threshold:
            metrics[metric_name] = threshold["max"]
    payload = {
        "schema_version": "unit-direct-eval-result",
        "eval_id": eval_id,
        "source_set_id": source_set_id,
        "passed": True,
        "checks": [
            {
                "name": "eval_cases_pass",
                "passed": True,
                "details": {"case_count": case_count, "failed_case_ids": []},
            },
            {
                "name": "metric_thresholds_met",
                "passed": True,
                "details": {"failures": []},
            },
        ],
        "contract": {"sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest()},
        "metrics": metrics,
    }
    for key, value in coverage_requirements.items():
        payload[key] = value
    payload.setdefault("case_count", case_count)
    payload.setdefault(
        "hard_negative_case_count",
        coverage_requirements.get("hard_negative_case_count", 0),
    )
    if eval_id == "retrieval-direct-eval-v1":
        payload["query_count"] = case_count
    return payload


def write_forest_plan_profile_eval_results(
    *,
    output_dir: Path,
    source_set_id: str,
    passed: bool = True,
    profile_failure_count: int = 0,
    profiles_below_floor_ids: list[str] | None = None,
) -> None:
    path = (
        output_dir
        / "evaluations"
        / "forest_plan_profile"
        / "forest_plan_profile_eval_results.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "region1-forest-plan-profile-eval-results-v1",
                "contract_id": "region1-forest-plan-profile-eval-coverage",
                "contract_version": "1.0.0",
                "passed": passed,
                "active_source_set_ids": [source_set_id],
                "expected_active_source_set_ids": [source_set_id],
                "required_profile_count": 10,
                "covered_profile_count": 10,
                "fixture_contract_defined_profile_count": 0,
                "not_started_profile_count": 0,
                "profile_failure_count": profile_failure_count,
                "profiles_below_floor_ids": profiles_below_floor_ids or [],
                "threshold_failures": [],
                "contract_checks": [
                    {
                        "name": "active_source_set_binding_matches_manifest",
                        "passed": True,
                    }
                ],
                "profiles": [
                    {
                        "forest_unit_id": "custer-gallatin-nf",
                        "hard_negative_case_count": 2,
                    }
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def write_forest_plan_component_retrieval_eval_results(
    *,
    output_dir: Path,
    source_set_id: str,
    passed: bool = True,
    failed_case_ids: list[str] | None = None,
) -> None:
    path = (
        output_dir
        / "evaluations"
        / "forest_plan_component_retrieval"
        / "forest_plan_component_retrieval_eval_results.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "forest-plan-component-retrieval-eval-results-v1",
                "contract_id": "region1-forest-plan-component-retrieval-eval",
                "contract_version": "1",
                "source_set_id": source_set_id,
                "expected_active_source_set_ids": [source_set_id],
                "passed": passed,
                "case_count": 6,
                "expected_pass_case_count": 4,
                "hard_negative_case_count": 2,
                "covered_forest_unit_ids": [
                    "beaverhead-deerlodge-nf",
                    "custer-gallatin-nf",
                    "flathead-nf",
                ],
                "required_forest_unit_ids": [
                    "beaverhead-deerlodge-nf",
                    "custer-gallatin-nf",
                    "flathead-nf",
                ],
                "failed_case_ids": failed_case_ids or [],
                "metrics": {
                    "component_retrieval_precision": 1.0,
                    "component_retrieval_recall": 1.0,
                    "wrong_forest_component_rate": 0.0,
                },
                "contract_checks": [
                    {
                        "name": "metric_thresholds_met",
                        "passed": passed,
                    }
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def write_catalog_sqlite(output_dir: Path, topics_by_source: dict[str, list[str]]) -> Path:
    return write_catalog_sqlite_for_dir(output_dir / "catalog", topics_by_source)


def write_catalog_sqlite_for_dir(
    catalog_dir: Path,
    topics_by_source: dict[str, list[str]],
) -> Path:
    path = catalog_dir / "review_sources.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as connection:
        connection.executescript(
            """
            CREATE TABLE sources (
              source_record_id TEXT PRIMARY KEY,
              issuer TEXT,
              scope TEXT,
              applies_to TEXT,
              trigger TEXT,
              currentness_notes TEXT
            );
            CREATE TABLE review_topics (
              topic_id TEXT PRIMARY KEY,
              label TEXT NOT NULL
            );
            CREATE TABLE source_review_topics (
              source_record_id TEXT NOT NULL,
              topic_id TEXT NOT NULL,
              PRIMARY KEY (source_record_id, topic_id)
            );
            """
        )
        for source_record_id, topics in topics_by_source.items():
            connection.execute(
                "INSERT INTO sources VALUES (?, ?, ?, ?, ?, ?)",
                (
                    source_record_id,
                    "Test issuer",
                    "test scope",
                    "test applicability",
                    None,
                    None,
                ),
            )
            for index, topic in enumerate(topics):
                topic_id = f"topic:{source_record_id}:{index}"
                connection.execute("INSERT INTO review_topics VALUES (?, ?)", (topic_id, topic))
                connection.execute(
                    "INSERT INTO source_review_topics VALUES (?, ?)",
                    (source_record_id, topic_id),
                )
        connection.commit()
    return path


def write_catalog_source_set_manifest(output_dir: Path, source_set_id: str) -> None:
    write_catalog_source_set_manifest_for_dir(output_dir / "catalog", source_set_id)


def write_catalog_source_set_manifest_for_dir(catalog_dir: Path, source_set_id: str) -> None:
    path = catalog_dir / "source_set_manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"source_set_id": source_set_id}, sort_keys=True),
        encoding="utf-8",
    )


def write_replay_context(
    repo_root: Path,
    *,
    review_id: str,
    source_set_id: str,
    catalog_dir: Path,
) -> Path:
    path = repo_root / "config" / "replay_contexts" / f"{review_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "review_id": review_id,
                "source_set_id": source_set_id,
                "catalog_dir": str(catalog_dir),
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def chunk(
    *,
    source_set_id: str,
    source_record_id: str,
    title: str,
    document_role: str,
    authority_level: str,
    citation_label: str,
    text: str,
) -> dict:
    content_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    artifact_sha256 = hashlib.sha256(source_record_id.encode("utf-8")).hexdigest()
    return {
        "chunk_id": f"chunk:{source_record_id}",
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "chunk_index": 0,
        "title": title,
        "document_role": document_role,
        "support_document_role": document_role,
        "authority_level": authority_level,
        "host": "example.test",
        "expected_parser": "html",
        "artifact_sha256": artifact_sha256,
        "artifact_path": f"artifacts/raw/{source_record_id}.html",
        "citation_label": citation_label,
        "original_url": f"https://example.test/{source_record_id}/original",
        "effective_url": f"https://example.test/{source_record_id}",
        "final_url": f"https://example.test/{source_record_id}",
        "parser_name": "unit_parser",
        "parser_version": "1.0",
        "extracted_at": "2026-04-30T00:00:00Z",
        "source_text_path": f"derived/{source_set_id}/extracted_text/{source_record_id}.txt",
        "char_start": 0,
        "char_end": len(text),
        "page": None,
        "section": None,
        "heading": title,
        "content_sha256": content_sha256,
        "text": text,
    }


def read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def check(validation: dict, name: str) -> dict:
    for item in validation["checks"]:
        if item["name"] == name:
            return item
    raise AssertionError(f"Missing validation check {name}")


def phase(summary: dict, name: str) -> dict:
    for item in summary["phases"]:
        if item["name"] == name:
            return item
    raise AssertionError(f"Missing phase {name}")
