from __future__ import annotations

from pathlib import Path
import json
import tempfile

from usfs_r1_ea_sources.phase_eval import run_phase_aligned_eval
from usfs_r1_ea_sources.retrieval import build_retrieval_index

from tests.test_eval_trace_gate import _write_default_inventory_and_store
from tests.test_eval_trace_inventory import _write_review_fixture
from tests.support.phase_eval_fixtures import chunk
from tests.support.phase_eval_fixtures import phase
from tests.support.phase_eval_fixtures import write_catalog_sqlite
from tests.support.phase_eval_fixtures import write_catalog_validation
from tests.support.phase_eval_fixtures import write_chunks
from tests.support.phase_eval_fixtures import write_extraction_diagnostics


def test_phase_eval_reports_optional_matching_eval_trace_gate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        fixture = _write_review_fixture(tmp_path)
        _write_default_inventory_and_store(tmp_path, fixture)

        result = run_phase_aligned_eval(
            output_dir=fixture["output_dir"],
            review_id=str(fixture["review_id"]),
        )

        eval_trace_phase = phase(result.summary, "first_class_eval_trace")
        assert eval_trace_phase["passed"]
        assert eval_trace_phase["reviewer_ready"]
        assert result.summary["eval_trace_gate"]["mode"] == "optional"
        assert result.summary["eval_trace_gate"]["evidence_status"] == "passed"
        assert result.summary["eval_trace_gate"]["failure_reasons"] == []


def test_source_set_phase_eval_ignores_unrelated_gold_eval() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        source_set_id = "source-set-test"
        write_catalog_validation(output_dir, passed=True)
        write_extraction_diagnostics(
            output_dir,
            source_set_id,
            source_record_ids=["R1EA-021"],
        )
        write_chunks(
            output_dir,
            source_set_id,
            [
                chunk(
                    source_set_id=source_set_id,
                    source_record_id="R1EA-021",
                    title="Scoped replay source",
                    document_role="regulation",
                    authority_level="federal_regulation",
                    citation_label="R1EA-021 | Scoped replay source | artifact abc123",
                    text="Source-set phase replay should ignore unrelated global gold evals.",
                )
            ],
        )
        write_catalog_sqlite(output_dir, {"R1EA-021": ["Replay"]})
        build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
        gold_eval_dir = output_dir / "reviews" / "compliance_gold_eval"
        gold_eval_dir.mkdir(parents=True, exist_ok=True)
        (gold_eval_dir / "compliance_gold_eval_results.json").write_text(
            json.dumps(
                {
                    "source_set_id": "source-set-other",
                    "passed": True,
                    "promotion_ready": True,
                    "rule_pack_id": "unit-nepa-ea",
                    "rule_pack_version": "0.4.0",
                },
                sort_keys=True,
            ),
            encoding="utf-8",
        )

        result = run_phase_aligned_eval(output_dir=output_dir, source_set_id=source_set_id)

        phase_names = {item["name"] for item in result.summary["phases"]}
        assert "compliance_gold_eval" not in phase_names
