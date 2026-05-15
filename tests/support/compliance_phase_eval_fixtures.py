from __future__ import annotations

from pathlib import Path
import json

from tests.support.compliance_review_fixtures import (
    _write_downstream_direct_eval_phase_outputs,
    _write_json,
)


def _write_graph_phase_outputs(output_dir: Path, source_set_id: str) -> None:
    graph_dir = output_dir / "derived" / source_set_id / "evidence_graph"
    graph_dir.mkdir(parents=True, exist_ok=True)
    (graph_dir / "evidence_graph_validation.json").write_text(
        json.dumps({"passed": True, "checks": []}, sort_keys=True),
        encoding="utf-8",
    )
    (graph_dir / "summary.json").write_text(
        json.dumps(
            {
                "reviewer_ready": True,
                "validation_passed": True,
                "retrieval_index_path": "index.sqlite",
                "retrieval_index_chunk_count": 2,
                "retrieval_binding_mismatch_count": 0,
                "metrics": {},
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    _write_upstream_evaluation_phase_outputs(output_dir)
    _write_downstream_direct_eval_phase_outputs(output_dir, source_set_id)


def _write_upstream_evaluation_phase_outputs(output_dir: Path) -> None:
    path = output_dir / "evaluations" / "upstream" / "upstream_evaluation_results.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "upstream-evaluation-results-v0",
                "passed": True,
                "lane_summaries": [
                    {"lane_id": "capture", "status": "direct_eval_present"},
                    {"lane_id": "catalog", "status": "direct_eval_present"},
                    {"lane_id": "extraction", "status": "direct_eval_present"},
                ],
                "failed_case_ids": [],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def _write_final_qa_phase_outputs(
    review_dir: Path,
    *,
    review_id: str,
    source_set_id: str,
) -> None:
    final_qa_dir = review_dir / "final_qa"
    final_qa_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        final_qa_dir / "east_crazies_final_qa_certification.json",
        {
            "schema_version": "east-crazies-final-qa-certification-report-v1",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "gate_replay_summary": {"machine_replay_status": "passed"},
            "finding_qa": {"authority_finding_count": 33},
            "accepted_v1_risk_ledger": {"accepted_pending_count": 14},
            "certification_statement": {"legal_conclusion": False},
        },
    )
    _write_json(
        final_qa_dir / "east_crazies_final_qa_certification_manifest.json",
        {
            "schema_version": "east-crazies-final-qa-certification-manifest-v1",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "validation_status": "passed",
        },
    )
    _write_json(
        final_qa_dir / "east_crazies_final_qa_certification_validation.json",
        {
            "schema_version": "east-crazies-final-qa-certification-validation-v1",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "passed": True,
            "machine_replay_status": "passed",
            "check_count": 157,
            "failed_check_count": 0,
            "failure_category_counts": {},
        },
    )
    (final_qa_dir / "east_crazies_final_qa_certification.pdf").write_bytes(b"%PDF-1.4\n")
