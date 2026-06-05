from __future__ import annotations

from pathlib import Path
import tempfile

from usfs_r1_ea_sources.review_packet_index import run_review_packet_direct_eval
from usfs_r1_ea_sources.review_packet_index import run_review_packet_index
from usfs_r1_ea_sources.review_packet_direct_eval import (
    REVIEW_PACKET_DIRECT_EVAL_CONTRACT_ID,
)
from usfs_r1_ea_sources.review_packet_direct_eval import (
    REVIEW_PACKET_DIRECT_EVAL_SCHEMA_VERSION,
)
from usfs_r1_ea_sources.review_packet_direct_eval import (
    REVIEW_PACKET_FAILURE_INTAKE_SCHEMA_VERSION,
)

from tests.test_review_packet_index import _read_json
from tests.test_review_packet_index import _write_minimal_review


def test_review_packet_direct_eval_writes_green_summary_and_empty_intake() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "source_library"
        review_id = "review-1"
        review_dir = output_dir / "reviews" / review_id
        _write_minimal_review(review_dir, review_id=review_id)
        generated = run_review_packet_index(output_dir=output_dir, review_id=review_id)
        assert generated.summary["passed"] is True

        result = run_review_packet_direct_eval(output_dir=output_dir, review_id=review_id)

        assert result.summary["schema_version"] == REVIEW_PACKET_DIRECT_EVAL_SCHEMA_VERSION
        assert result.summary["contract_id"] == REVIEW_PACKET_DIRECT_EVAL_CONTRACT_ID
        assert result.summary["direct_eval_present"] is True
        assert result.summary["passed"] is True
        assert result.summary["metric_group_count"] == 6
        assert result.summary["blocking_gap_group_ids"] == []
        assert result.summary["required_metric_group_ids_present"] == []
        assert result.summary["failure_intake_case_count"] == 0
        assert result.output_path.exists()
        intake = _read_json(result.failure_intake_path)
        assert intake["schema_version"] == REVIEW_PACKET_FAILURE_INTAKE_SCHEMA_VERSION
        assert intake["case_count"] == 0
        assert intake["cases"] == []


def test_review_packet_direct_eval_fails_closed_for_stale_packet_artifact() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "source_library"
        review_id = "review-1"
        review_dir = output_dir / "reviews" / review_id
        _write_minimal_review(review_dir, review_id=review_id)
        generated = run_review_packet_index(output_dir=output_dir, review_id=review_id)
        assert generated.summary["passed"] is True
        generated.packet_index_markdown_path.write_text(
            generated.packet_index_markdown_path.read_text(encoding="utf-8") + "\n",
            encoding="utf-8",
        )

        result = run_review_packet_direct_eval(output_dir=output_dir, review_id=review_id)

        assert result.summary["passed"] is False
        assert "artifact_hash_alignment" in result.summary["blocking_gap_group_ids"]
        assert result.summary["failure_intake_case_count"] >= 1
        intake = _read_json(result.failure_intake_path)
        case = next(
            case
            for case in intake["cases"]
            if case["metric_group_id"] == "artifact_hash_alignment"
        )
        assert case["owner"] == "review_packet_index"
        assert case["risk_level"] == "blocking"
        assert case["source_set_id"] == "source-set-test"
        assert {artifact["artifact_id"] for artifact in case["source_artifacts"]} >= {
            "row_inventory",
            "packet_index",
            "packet_index_markdown",
            "validation",
        }
