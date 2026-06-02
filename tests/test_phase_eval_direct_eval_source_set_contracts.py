from __future__ import annotations

from pathlib import Path
import hashlib
import json
import tempfile

from usfs_r1_ea_sources.phase_eval_direct_eval import resolve_phase_eval_direct_eval_coverage


FULL_CANONICAL_SOURCE_SET_ID = "source-set-f70ea11e04ae3d53"
NON_FULL_CANONICAL_SOURCE_SET_ID = "source-set-non-full-canonical"
REPO_ROOT = Path(__file__).resolve().parents[1]


def test_phase_eval_direct_eval_accepts_extraction_fidelity_eval() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        result_path = (
            output_dir
            / "evaluations"
            / "extraction_fidelity"
            / "extraction_fidelity_eval_results.json"
        )
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(
            json.dumps(
                _extraction_fidelity_eval_payload(),
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=output_dir,
            source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
        )

    extraction = summary["source_set_phase_statuses"]["extraction"]
    assert extraction["status"] == "direct_eval_present"
    assert extraction["failure_reasons"] == []
    assert extraction["details"]["matched_case_count"] == 24


def test_phase_eval_direct_eval_rejects_extraction_fidelity_threshold_failures() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        result_path = (
            output_dir
            / "evaluations"
            / "extraction_fidelity"
            / "extraction_fidelity_eval_results.json"
        )
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(
            json.dumps(
                _extraction_fidelity_eval_payload(
                    passed=False,
                    failed_case_ids=["case-1"],
                    failed_contract_check_names=["contract_check_failed"],
                ),
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=output_dir,
            source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
        )

    extraction = summary["source_set_phase_statuses"]["extraction"]
    assert extraction["status"] == "direct_eval_failed"
    assert extraction["failure_reasons"] == ["direct_eval_threshold_failed"]
    assert extraction["threshold_failures"]


def test_phase_eval_direct_eval_skips_full_canonical_only_source_set_gates() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=Path(tmp),
            source_set_id=NON_FULL_CANONICAL_SOURCE_SET_ID,
        )

    assert "nepa_3d_source_set_graph" not in summary["source_set_phase_statuses"]
    assert "canonical_semantic_graph" not in summary["source_set_phase_statuses"]
    assert "forest_plan_component_retrieval" not in summary["source_set_phase_statuses"]


def test_phase_eval_direct_eval_accepts_semantic_graph_eval() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        result_path = (
            output_dir
            / "derived"
            / FULL_CANONICAL_SOURCE_SET_ID
            / "knowledge_graph"
            / "semantic_graph_eval_results.json"
        )
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(
            json.dumps(
                _semantic_graph_eval_payload(source_set_id=FULL_CANONICAL_SOURCE_SET_ID),
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=output_dir,
            source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
        )

    semantic_graph = summary["source_set_phase_statuses"]["canonical_semantic_graph"]
    assert semantic_graph["status"] == "direct_eval_present"
    assert semantic_graph["case_count"] == 12
    assert semantic_graph["hard_negative_case_count"] == 7


def test_phase_eval_direct_eval_rejects_semantic_graph_eval_threshold_failures() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        result_path = (
            output_dir
            / "derived"
            / FULL_CANONICAL_SOURCE_SET_ID
            / "knowledge_graph"
            / "semantic_graph_eval_results.json"
        )
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(
            json.dumps(
                _semantic_graph_eval_payload(
                    source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
                    passed=False,
                    failed_negative_case_ids=["justification_edge_removed"],
                ),
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=output_dir,
            source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
        )

    semantic_graph = summary["source_set_phase_statuses"]["canonical_semantic_graph"]
    assert semantic_graph["status"] == "direct_eval_failed"
    assert semantic_graph["failure_reasons"] == ["direct_eval_threshold_failed"]
    assert semantic_graph["threshold_failures"]


def test_phase_eval_direct_eval_accepts_knowledge_graph_query_eval() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        result_path = (
            output_dir
            / "derived"
            / FULL_CANONICAL_SOURCE_SET_ID
            / "knowledge_graph"
            / "knowledge_graph_query_eval_results.json"
        )
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(
            json.dumps(
                _knowledge_graph_query_eval_payload(
                    source_set_id=FULL_CANONICAL_SOURCE_SET_ID
                ),
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=output_dir,
            source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
        )

    query_surface = summary["source_set_phase_statuses"]["knowledge_graph_query_surface"]
    assert query_surface["status"] == "direct_eval_present"
    assert query_surface["case_count"] == 9
    assert query_surface["hard_negative_case_count"] == 2
    assert query_surface["details"]["query_type_count"] == 7
    assert query_surface["details"]["freshness_warning_case_count"] == 0


def test_phase_eval_direct_eval_rejects_knowledge_graph_query_freshness_warnings() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        result_path = (
            output_dir
            / "derived"
            / FULL_CANONICAL_SOURCE_SET_ID
            / "knowledge_graph"
            / "knowledge_graph_query_eval_results.json"
        )
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(
            json.dumps(
                _knowledge_graph_query_eval_payload(
                    source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
                    freshness_warning_case_count=1,
                ),
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=output_dir,
            source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
        )

    query_surface = summary["source_set_phase_statuses"]["knowledge_graph_query_surface"]
    assert query_surface["status"] == "direct_eval_failed"
    assert query_surface["failure_reasons"] == ["direct_eval_threshold_failed"]
    assert query_surface["threshold_failures"] == [
        {
            "metric": "freshness_warning_case_count",
            "reason": "freshness_warnings_present",
            "actual": 1,
            "expected_maximum": 0,
        }
    ]


def _extraction_fidelity_eval_payload(
    *,
    passed: bool = True,
    failed_case_ids: list[str] | None = None,
    failed_contract_check_names: list[str] | None = None,
) -> dict:
    failed_case_ids = failed_case_ids or []
    failed_contract_check_names = failed_contract_check_names or []
    return {
        "schema_version": "extraction-fidelity-eval-results-v0",
        "passed": passed,
        "required_category_count": 12,
        "case_count": 24,
        "matched_case_count": 24 - len(failed_case_ids),
        "failed_case_ids": failed_case_ids,
        "contract_checks": [
            {
                "name": name,
                "passed": False,
            }
            for name in failed_contract_check_names
        ],
    }


def _semantic_graph_eval_payload(
    *,
    source_set_id: str,
    passed: bool = True,
    failed_positive_case_ids: list[str] | None = None,
    failed_negative_case_ids: list[str] | None = None,
) -> dict:
    failed_positive_case_ids = failed_positive_case_ids or []
    failed_negative_case_ids = failed_negative_case_ids or []
    return {
        "schema_version": "semantic-graph-eval-results-v1",
        "eval_id": "semantic-graph-direct-eval-v1",
        "contract_id": "semantic-graph-direct-eval-v1",
        "contract_version": "1.0.0",
        "source_set_id": source_set_id,
        "passed": passed,
        "case_count": 12,
        "positive_case_count": 5,
        "hard_negative_case_count": 7,
        "coverage_categories": [
            "ontology_typing",
            "relationship_correctness",
            "relationship_provenance",
            "alias_identity_resolution",
            "currentness_metadata_carriage",
            "semantic_lens_integrity",
            "justification_path_accuracy",
            "controlled_negative",
        ],
        "contract": {
            "sha256": hashlib.sha256(
                (REPO_ROOT / "config" / "semantic_graph_direct_eval_v1.json").read_bytes()
            ).hexdigest()
        },
        "threshold_failures": (
            [
                {
                    "metric": "controlled_negative_cases",
                    "failed_case_ids": failed_negative_case_ids,
                }
            ]
            if failed_negative_case_ids
            else []
        ),
        "contract_checks": [
            {
                "name": "semantic_graph_eval_thresholds_met",
                "passed": passed,
            }
        ],
        "summary": {
            "passed": passed,
            "source_set_id": source_set_id,
            "case_count": 12,
            "positive_case_count": 5,
            "hard_negative_case_count": 7,
            "failed_positive_case_ids": failed_positive_case_ids,
            "failed_negative_case_ids": failed_negative_case_ids,
        },
    }


def _knowledge_graph_query_eval_payload(
    *,
    source_set_id: str,
    passed: bool = True,
    freshness_warning_case_count: int = 0,
    failed_case_ids: list[str] | None = None,
) -> dict:
    failed_case_ids = failed_case_ids or []
    return {
        "schema_version": "knowledge-graph-query-eval-results-v1",
        "eval_id": "knowledge-graph-query-eval-v1",
        "contract_id": "knowledge-graph-query-eval-v1",
        "contract_version": "1.0.0",
        "source_set_id": source_set_id,
        "passed": passed,
        "case_count": 9,
        "hard_negative_case_count": 2,
        "query_type_count": 7,
        "query_types": [
            "citation",
            "edge_type",
            "forest_unit",
            "node_id",
            "node_type",
            "readiness_blocker",
            "source_record",
        ],
        "freshness_warning_case_count": freshness_warning_case_count,
        "contract": {
            "sha256": hashlib.sha256(
                (REPO_ROOT / "config" / "knowledge_graph_query_eval_v1.json").read_bytes()
            ).hexdigest()
        },
        "contract_checks": [
            {
                "name": "knowledge_graph_query_eval_cases_pass",
                "passed": passed,
            }
        ],
        "summary": {
            "passed": passed,
            "source_set_id": source_set_id,
            "case_count": 9,
            "hard_negative_case_count": 2,
            "query_type_count": 7,
            "failed_case_ids": failed_case_ids,
            "failed_contract_check_names": []
            if passed
            else ["knowledge_graph_query_eval_cases_pass"],
            "freshness_warning_case_count": freshness_warning_case_count,
        },
    }
