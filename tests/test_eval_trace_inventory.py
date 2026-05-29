from __future__ import annotations

from pathlib import Path
import json

from usfs_r1_ea_sources.eval_trace_inventory import INVENTORY_RESULT_SCHEMA_VERSION
from usfs_r1_ea_sources.eval_trace_inventory import run_eval_trace_inventory
from usfs_r1_ea_sources.records import sha256_file


def test_review_scoped_inventory_links_fixture_artifacts(tmp_path: Path) -> None:
    fixture = _write_review_fixture(tmp_path)

    result = run_eval_trace_inventory(
        output_dir=fixture["output_dir"],
        source_set_id=fixture["source_set_id"],
        review_id=fixture["review_id"],
        repo_root=tmp_path,
    )
    summary = result.summary

    assert summary["schema_version"] == INVENTORY_RESULT_SCHEMA_VERSION
    assert summary["passed"] is True
    assert summary["coverage_status"] == "passed"
    assert summary["missing_cross_links"] == []
    assert summary["stale_artifacts"] == []
    assert summary["source_set_mismatches"] == []
    assert summary["review_id_mismatches"] == []
    assert summary["trace_hash_mismatches"] == []
    assert summary["required_link_status"]["passed"] is True
    assert summary["export_readiness"] == {
        "canonical_json_ready": False,
        "openinference_ready": False,
        "reason": "sqlite_store_not_built",
        "inventory_rows_exportable": True,
        "local_source_of_record": True,
    }


def test_source_set_inventory_does_not_require_review_artifacts(tmp_path: Path) -> None:
    source_set_id = "source-set-a"
    output_dir = tmp_path / "source_library"
    _write_json(output_dir / "catalog" / "source_set_manifest.json", {"source_set_id": source_set_id})
    _write_jsonl(
        output_dir / "catalog" / "source_catalog.jsonl",
        [
            {
                "source_set_id": source_set_id,
                "source_record_id": "SRC-001",
                "artifact_sha256": "a" * 64,
            }
        ],
    )
    _write_json(
        output_dir / "derived" / source_set_id / "evidence_graph" / "phase_eval_results.json",
        {
            "source_set_id": source_set_id,
            "direct_eval_status": "direct_eval_present",
            "reviewer_ready": True,
        },
    )

    summary = run_eval_trace_inventory(
        output_dir=output_dir,
        source_set_id=source_set_id,
        repo_root=tmp_path,
    ).summary

    assert summary["passed"] is True
    assert summary["scope"]["scope_kind"] == "source_set"
    assert summary["required_artifact_count"] == 3
    assert {artifact["family_id"] for artifact in summary["artifact_families"]} == {
        "phase_eval",
        "source_catalog",
        "source_set_manifest",
    }


def test_inventory_reports_missing_replay_context_without_mutating_artifacts(
    tmp_path: Path,
) -> None:
    fixture = _write_review_fixture(tmp_path)
    fixture["replay_context_path"].unlink()

    summary = run_eval_trace_inventory(
        output_dir=fixture["output_dir"],
        source_set_id=fixture["source_set_id"],
        review_id=fixture["review_id"],
        repo_root=tmp_path,
    ).summary

    assert summary["passed"] is False
    assert any(
        gap["family_id"] == "replay_context"
        and gap["failure_reason"] == "missing_required_artifact"
        for gap in summary["missing_cross_links"]
    )
    assert _link(summary, "replay_context_catalog_match")["passed"] is False


def test_inventory_fails_typed_source_set_mismatch(tmp_path: Path) -> None:
    fixture = _write_review_fixture(tmp_path)
    _write_json(
        fixture["review_dir"] / "v1_ea_eval_results.json",
        {
            "summary": {
                "schema_version": "v1-ea-real-review-eval-results-v0",
                "review_id": fixture["review_id"],
                "source_set_id": "source-set-stale",
                "passed": True,
            }
        },
    )

    summary = run_eval_trace_inventory(
        output_dir=fixture["output_dir"],
        source_set_id=fixture["source_set_id"],
        review_id=fixture["review_id"],
        repo_root=tmp_path,
    ).summary

    assert summary["passed"] is False
    assert {
        "family_id": "v1_ea_eval",
        "path": f"source_library/reviews/{fixture['review_id']}/v1_ea_eval_results.json",
        "expected": fixture["source_set_id"],
        "actual": "source-set-stale",
    } in summary["source_set_mismatches"]
    assert _link(summary, "source_set_identity_match")["failure_reason"] == "source_set_mismatch"


def test_inventory_fails_typed_review_id_mismatch(tmp_path: Path) -> None:
    fixture = _write_review_fixture(tmp_path)
    _write_json(
        fixture["review_dir"] / "forest_plan_component_eval_results.json",
        {
            "schema_version": "forest-plan-component-eval-results-v0",
            "review_id": "other-review",
            "source_set_id": fixture["source_set_id"],
            "passed": True,
        },
    )

    summary = run_eval_trace_inventory(
        output_dir=fixture["output_dir"],
        source_set_id=fixture["source_set_id"],
        review_id=fixture["review_id"],
        repo_root=tmp_path,
    ).summary

    assert summary["passed"] is False
    assert {
        "family_id": "forest_plan_component_eval",
        "path": (
            f"source_library/reviews/{fixture['review_id']}/"
            "forest_plan_component_eval_results.json"
        ),
        "expected": fixture["review_id"],
        "actual": "other-review",
    } in summary["review_id_mismatches"]


def test_inventory_fails_trace_hash_mismatch(tmp_path: Path) -> None:
    fixture = _write_review_fixture(tmp_path)
    fixture["retrieval_trace_path"].write_text('{"trace_id":"changed"}\n', encoding="utf-8")

    summary = run_eval_trace_inventory(
        output_dir=fixture["output_dir"],
        source_set_id=fixture["source_set_id"],
        review_id=fixture["review_id"],
        repo_root=tmp_path,
    ).summary

    assert summary["passed"] is False
    assert summary["trace_hash_mismatches"] == [
        {
            "family_id": "applicability_trace",
            "path": (
                f"source_library/reviews/{fixture['review_id']}/applicability/"
                "applicability_retrieval_trace.jsonl"
            ),
            "expected": fixture["retrieval_trace_sha256"],
            "actual": sha256_file(fixture["retrieval_trace_path"]),
        }
    ]
    assert _link(summary, "applicability_trace_hash_match")["passed"] is False


def test_inventory_reports_missing_eval_result(tmp_path: Path) -> None:
    fixture = _write_review_fixture(tmp_path)
    (fixture["review_dir"] / "forest_plan_component_eval_results.json").unlink()

    summary = run_eval_trace_inventory(
        output_dir=fixture["output_dir"],
        source_set_id=fixture["source_set_id"],
        review_id=fixture["review_id"],
        repo_root=tmp_path,
    ).summary

    assert summary["passed"] is False
    assert any(
        gap["family_id"] == "forest_plan_component_eval"
        and gap["failure_reason"] == "missing_required_artifact"
        for gap in summary["missing_cross_links"]
    )


def test_inventory_reports_malformed_result_schema(tmp_path: Path) -> None:
    fixture = _write_review_fixture(tmp_path)
    (fixture["review_dir"] / "v1_ea_eval_results.json").write_text("{broken", encoding="utf-8")

    summary = run_eval_trace_inventory(
        output_dir=fixture["output_dir"],
        source_set_id=fixture["source_set_id"],
        review_id=fixture["review_id"],
        repo_root=tmp_path,
    ).summary

    assert summary["passed"] is False
    assert summary["malformed_artifact_count"] == 1
    assert any(
        artifact["family_id"] == "v1_ea_eval" and artifact["status"] == "malformed"
        for artifact in summary["artifact_families"]
    )


def test_inventory_writes_explicit_json_or_markdown_results_path(tmp_path: Path) -> None:
    fixture = _write_review_fixture(tmp_path)
    json_path = tmp_path / "inventory.json"
    md_path = tmp_path / "inventory.md"

    run_eval_trace_inventory(
        output_dir=fixture["output_dir"],
        source_set_id=fixture["source_set_id"],
        review_id=fixture["review_id"],
        results_path=json_path,
        format="json",
        repo_root=tmp_path,
    )
    run_eval_trace_inventory(
        output_dir=fixture["output_dir"],
        source_set_id=fixture["source_set_id"],
        review_id=fixture["review_id"],
        results_path=md_path,
        format="markdown",
        repo_root=tmp_path,
    )

    assert json.loads(json_path.read_text(encoding="utf-8"))["passed"] is True
    assert md_path.read_text(encoding="utf-8").startswith("# Eval Trace Inventory Report\n")


def _write_review_fixture(tmp_path: Path) -> dict[str, object]:
    review_id = "review-a"
    source_set_id = "source-set-a"
    output_dir = tmp_path / "source_library"
    review_dir = output_dir / "reviews" / review_id
    catalog_dir = output_dir / "runs" / "fixture-catalog" / "catalog_gate"
    replay_context_path = tmp_path / "config" / "replay_contexts" / f"{review_id}.json"
    _write_json(
        replay_context_path,
        {
            "review_id": review_id,
            "source_set_id": source_set_id,
            "catalog_dir": "source_library/runs/fixture-catalog/catalog_gate",
        },
    )
    _write_json(
        catalog_dir / "source_set_manifest.json",
        {"schema_version": "source-set-manifest-v1", "source_set_id": source_set_id},
    )
    _write_jsonl(
        catalog_dir / "source_catalog.jsonl",
        [
            {
                "source_set_id": source_set_id,
                "source_record_id": "SRC-001",
                "artifact_sha256": "a" * 64,
            }
        ],
    )
    _write_json(
        review_dir / "phase_eval_results.json",
        {
            "review_id": review_id,
            "source_set_id": source_set_id,
            "review_direct_eval_status": "direct_eval_present",
            "reviewer_ready": True,
        },
    )
    retrieval_trace_path = (
        review_dir / "applicability" / "applicability_retrieval_trace.jsonl"
    )
    graph_trace_path = review_dir / "applicability" / "applicability_graph_trace.jsonl"
    _write_jsonl(
        retrieval_trace_path,
        [{"review_id": review_id, "source_set_id": source_set_id, "trace_id": "rt-1"}],
    )
    _write_jsonl(
        graph_trace_path,
        [{"review_id": review_id, "source_set_id": source_set_id, "trace_id": "gt-1"}],
    )
    retrieval_trace_sha256 = sha256_file(retrieval_trace_path)
    graph_trace_sha256 = sha256_file(graph_trace_path)
    _write_json(
        review_dir / "applicability" / "applicability_retrieval_graph_diagnostics.json",
        {
            "schema_version": "applicability-retrieval-graph-diagnostics-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "retrieval_trace_sha256": retrieval_trace_sha256,
            "graph_trace_sha256": graph_trace_sha256,
            "summary": {"validation_passed": True},
        },
    )
    _write_json(
        review_dir / "forest_plan_component_eval_results.json",
        {
            "schema_version": "forest-plan-component-eval-results-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "passed": True,
        },
    )
    _write_json(
        output_dir
        / "evaluations"
        / "forest_plan_component_eval_coverage"
        / "forest_plan_component_eval_coverage_results.json",
        {
            "schema_version": "forest-plan-component-eval-coverage-results-v1",
            "passed": True,
            "slots": [
                {
                    "slot_id": "slot-a",
                    "review_id": review_id,
                    "result_source_set_id": source_set_id,
                    "passed": True,
                }
            ],
        },
    )
    _write_json(
        review_dir / "v1_ea_eval_results.json",
        {
            "summary": {
                "schema_version": "v1-ea-real-review-eval-results-v0",
                "review_id": review_id,
                "source_set_id": source_set_id,
                "passed": True,
            }
        },
    )
    _write_json(
        output_dir
        / "reviews"
        / "real_package_review_coverage_eval"
        / "real_package_review_coverage_eval_results.json",
        {
            "schema_version": "real-package-review-coverage-results-v1",
            "passed": True,
            "slots": [
                {
                    "slot_id": "slot-a",
                    "review_id": review_id,
                    "source_set_id": source_set_id,
                    "passed": True,
                }
            ],
        },
    )
    _write_json(
        review_dir / "decision_support" / "ea_consistency_decision_support.json",
        {
            "schema_version": "ea-consistency-decision-support-report-v1",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "validation_status": "passed",
        },
    )
    _write_json(
        review_dir / "decision_support" / "ea_consistency_decision_support_manifest.json",
        {
            "schema_version": "ea-consistency-decision-support-manifest-v1",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "validation_status": "passed",
        },
    )
    _write_json(
        review_dir / "final_qa" / "east_crazies_final_qa_certification.json",
        {
            "schema_version": "east-crazies-final-qa-certification-v1",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "passed": True,
        },
    )
    _write_json(
        review_dir / "final_qa" / "east_crazies_final_qa_certification_validation.json",
        {
            "schema_version": "east-crazies-final-qa-certification-validation-v1",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "passed": True,
        },
    )
    _write_json(
        review_dir / "review_packet_index" / "review_packet_index.json",
        {
            "schema_version": "review-packet-index-v1",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "reviewer_ready": True,
        },
    )
    _write_json(
        review_dir / "review_packet_index" / "review_packet_index_validation.json",
        {
            "schema_version": "review-packet-index-validation-v1",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "passed": True,
        },
    )
    _write_json(
        output_dir
        / "reviews"
        / "promotion_suite"
        / "post-v1-region1-ea-promotion-suite"
        / "promotion_suite_results.json",
        {
            "schema_version": "promotion-suite-results-v1",
            "suite_id": "post-v1-region1-ea-promotion-suite",
            "source_set_id": source_set_id,
            "promotion_ready": True,
        },
    )
    return {
        "output_dir": output_dir,
        "review_dir": review_dir,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "replay_context_path": replay_context_path,
        "retrieval_trace_path": retrieval_trace_path,
        "retrieval_trace_sha256": retrieval_trace_sha256,
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _link(summary: dict, check_id: str) -> dict:
    return next(
        check
        for check in summary["required_link_status"]["checks"]
        if check["check_id"] == check_id
    )
