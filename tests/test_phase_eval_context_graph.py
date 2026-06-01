from __future__ import annotations

from pathlib import Path
import hashlib
import json
import tempfile

from usfs_r1_ea_sources.evidence_graph import build_evidence_graph
from usfs_r1_ea_sources.phase_eval import run_phase_aligned_eval
from usfs_r1_ea_sources.phase_eval_direct_eval import load_phase_eval_direct_eval_contract
from usfs_r1_ea_sources.phase_eval_direct_eval import resolve_phase_eval_direct_eval_coverage
from usfs_r1_ea_sources.retrieval import build_retrieval_index

from tests.support.phase_eval_fixtures import chunk
from tests.support.phase_eval_fixtures import phase
from tests.support.phase_eval_fixtures import write_catalog_sqlite
from tests.support.phase_eval_fixtures import write_catalog_validation
from tests.support.phase_eval_fixtures import write_chunks
from tests.support.phase_eval_fixtures import write_extraction_diagnostics


REPO_ROOT = Path(__file__).resolve().parents[1]
FULL_CANONICAL_SOURCE_SET_ID = "source-set-f70ea11e04ae3d53"


def test_committed_phase_eval_contract_tracks_context_graph_phase() -> None:
    contract = load_phase_eval_direct_eval_contract()
    source_set_phases = {
        entry["phase_name"]: entry for entry in contract["source_set_phases"]
    }

    context_graph = source_set_phases["observability_eval_context_graph"]
    assert context_graph["lane_id"] == "observability_eval_context_graph"
    assert context_graph["producer"] == "eval_context_graph_evaluation"
    assert context_graph["contract_path"] == "context_graph_contract_v1.json"
    assert context_graph["results_path"] == (
        "evaluations/eval_context_graph/eval_context_graph_eval_summary.json"
    )
    assert context_graph["required_source_set_ids"] == [FULL_CANONICAL_SOURCE_SET_ID]


def test_phase_eval_direct_eval_marks_context_graph_summary_missing() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=Path(tmp),
            source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
        )

    context_graph = summary["source_set_phase_statuses"][
        "observability_eval_context_graph"
    ]
    assert context_graph["status"] == "direct_eval_missing"
    assert context_graph["failure_reasons"] == ["missing_required_direct_eval"]


def test_phase_eval_direct_eval_skips_context_graph_for_other_source_sets() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=Path(tmp),
            source_set_id="source-set-non-full-canonical",
        )

    assert "observability_eval_context_graph" not in summary["source_set_phase_statuses"]


def test_phase_eval_direct_eval_accepts_eval_context_graph_eval() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        _write_eval_context_graph_eval(
            output_dir,
            _eval_context_graph_eval_payload(source_set_id=FULL_CANONICAL_SOURCE_SET_ID),
        )

        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=output_dir,
            source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
        )

    context_graph = summary["source_set_phase_statuses"][
        "observability_eval_context_graph"
    ]
    assert context_graph["status"] == "direct_eval_present"
    assert context_graph["case_count"] == 3
    assert context_graph["hard_negative_case_count"] == 0
    assert context_graph["details"]["event_node_count"] == 4
    assert context_graph["details"]["source_set_ids"] == [FULL_CANONICAL_SOURCE_SET_ID]


def test_phase_eval_direct_eval_rejects_eval_context_graph_source_set_mismatch() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        _write_eval_context_graph_eval(
            output_dir,
            _eval_context_graph_eval_payload(source_set_id="source-set-other"),
        )

        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=output_dir,
            source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
        )

    context_graph = summary["source_set_phase_statuses"][
        "observability_eval_context_graph"
    ]
    assert context_graph["status"] == "direct_eval_identity_mismatch"
    assert context_graph["failure_reasons"] == ["direct_eval_identity_mismatch"]


def test_phase_eval_direct_eval_rejects_eval_context_graph_threshold_failures() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        _write_eval_context_graph_eval(
            output_dir,
            _eval_context_graph_eval_payload(
                source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
                failed_check_names=["event_nodes_have_emitted_edges"],
                event_node_count=0,
            ),
        )

        summary = resolve_phase_eval_direct_eval_coverage(
            output_dir=output_dir,
            source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
        )

    context_graph = summary["source_set_phase_statuses"][
        "observability_eval_context_graph"
    ]
    assert context_graph["status"] == "direct_eval_failed"
    assert context_graph["failure_reasons"] == ["direct_eval_threshold_failed"]
    assert context_graph["threshold_failures"] == [
        {
            "metric": "graph_eval_checks",
            "reason": "graph_eval_checks_failed",
            "failed_checks": ["event_nodes_have_emitted_edges"],
        },
        {
            "metric": "command_succeeded",
            "reason": "producer_command_failed",
            "actual": False,
        },
        {
            "metric": "event_node_count",
            "reason": "event_nodes_missing",
            "actual": 0,
            "expected_minimum": 1,
        },
    ]


def test_phase_eval_requires_context_graph_eval_for_full_canonical_source_set() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        write_catalog_validation(output_dir, passed=True)
        write_extraction_diagnostics(
            output_dir,
            FULL_CANONICAL_SOURCE_SET_ID,
            source_record_ids=["R1EA-034"],
        )
        write_chunks(
            output_dir,
            FULL_CANONICAL_SOURCE_SET_ID,
            [
                chunk(
                    source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
                    source_record_id="R1EA-034",
                    title="Context graph eval phase source",
                    document_role="agency_policy",
                    authority_level="federal_guidance",
                    citation_label=(
                        "R1EA-034 | Context graph eval phase source | artifact abc123"
                    ),
                    text=(
                        "The full-canonical source set should require context graph "
                        "eval coverage."
                    ),
                )
            ],
        )
        write_catalog_sqlite(output_dir, {"R1EA-034": ["Context graph eval"]})
        build_retrieval_index(
            output_dir=output_dir,
            source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
        )
        build_evidence_graph(
            output_dir=output_dir,
            source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
        )

        missing_result = run_phase_aligned_eval(
            output_dir=output_dir,
            source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
        )
        context_graph_phase = phase(
            missing_result.summary,
            "observability_eval_context_graph",
        )
        assert not context_graph_phase["passed"]
        assert not context_graph_phase["reviewer_ready"]
        assert context_graph_phase["details"]["direct_eval_status"] == (
            "direct_eval_missing"
        )
        assert "missing_required_direct_eval" in context_graph_phase["failure_reasons"]

        _write_eval_context_graph_eval(
            output_dir,
            _eval_context_graph_eval_payload(source_set_id=FULL_CANONICAL_SOURCE_SET_ID),
        )
        ready_result = run_phase_aligned_eval(
            output_dir=output_dir,
            source_set_id=FULL_CANONICAL_SOURCE_SET_ID,
        )
        context_graph_phase = phase(
            ready_result.summary,
            "observability_eval_context_graph",
        )
        assert context_graph_phase["passed"]
        assert context_graph_phase["reviewer_ready"]
        assert context_graph_phase["details"]["direct_eval_status"] == (
            "direct_eval_present"
        )
        assert (
            context_graph_phase["details"]["direct_eval_details"]["event_node_count"]
            == 4
        )


def _write_eval_context_graph_eval(output_dir: Path, payload: dict) -> Path:
    path = (
        output_dir
        / "evaluations"
        / "eval_context_graph"
        / "eval_context_graph_eval_summary.json"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return path


def _eval_context_graph_eval_payload(
    *,
    source_set_id: str,
    failed_check_names: list[str] | None = None,
    event_node_count: int = 4,
) -> dict:
    failed_check_names = failed_check_names or []
    check_names = [
        "required_node_kinds_present",
        "event_nodes_have_emitted_edges",
        "trace_result_score_paths_present",
    ]
    passed = not failed_check_names and event_node_count > 0
    return {
        "schema_version": "eval-context-graph-eval-summary-v1",
        "graph_schema_version": "eval-context-graph-v1",
        "contract_id": "first-class-generated-observability-eval-context-graph",
        "contract_version": "0.4.0",
        "contract": {
            "sha256": hashlib.sha256(
                (REPO_ROOT / "config" / "context_graph_contract_v1.json").read_bytes()
            ).hexdigest()
        },
        "graph_json_path": "evaluations/eval_context_graph/eval_context_graph.json",
        "passed": passed,
        "command_succeeded": passed,
        "node_counts": {
            "eval_result": 18,
            "log_event": max(0, event_node_count - 2),
            "source_set": 1,
            "span": 18,
            "span_event": min(event_node_count, 2),
            "trace": 18,
        },
        "edge_counts": {
            "CONTAINS": 18,
            "EMITTED": event_node_count,
            "EVALUATED_BY": 18,
            "SCORED_AS": 18,
            "TARGETS": 18,
        },
        "event_source_count": 3 if event_node_count else 0,
        "event_node_count": event_node_count,
        "node_count": 96 + event_node_count,
        "edge_count": 128 + event_node_count,
        "source_set_ids": [source_set_id],
        "review_ids": ["review-a"],
        "validation_checks": [
            {"name": name, "passed": name not in failed_check_names}
            for name in check_names
        ],
    }
