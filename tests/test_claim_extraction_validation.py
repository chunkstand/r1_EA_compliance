from __future__ import annotations

from pathlib import Path
import json
import tempfile

from usfs_r1_ea_sources.claim_extraction import build_claim_extraction
from usfs_r1_ea_sources.claim_extraction_validation import validate_claim_outputs

from tests.test_claim_extraction import _chunk
from tests.test_claim_extraction import _prepare_source_library
from tests.test_claim_extraction import _read_jsonl
from tests.test_claim_extraction import _write_jsonl


def test_claim_validation_rejects_tampered_unsupported_claim() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        source_set_id = "source-set-test"
        _prepare_source_library(
            output_dir,
            source_set_id,
            [
                _chunk(
                    source_set_id=source_set_id,
                    source_record_id="R1EA-001",
                    title="Purpose and need",
                    document_role="regulation",
                    authority_level="federal_regulation",
                    citation_label="R1EA-001 | Purpose and need | artifact abc123",
                    text="The agency must identify the purpose and need.",
                )
            ],
        )
        result = build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)
        claims = _read_jsonl(result.claims_path)
        claims[0]["claim_type"] = "model_generated_conclusion"
        claims[0]["pattern_id"] = "unsupported"
        _write_jsonl(result.claims_path, claims)

        validation = validate_claim_outputs(
            output_dir=output_dir,
            source_set_id=source_set_id,
            claims_path=result.claims_path,
            entities_path=result.entities_path,
            nodes_path=result.nodes_path,
            edges_path=result.edges_path,
            chunks_path=output_dir / "derived" / source_set_id / "chunks" / "chunks.jsonl",
        )

        assert not validation["passed"]
        assert not _check(validation, "claim_types_are_supported")["passed"]
        assert not _check(validation, "no_unsupported_claims_emitted")["passed"]


def test_claim_validation_partial_retrieval_preserves_readiness_failure_details() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        source_set_id = "source-set-test"
        _prepare_source_library(
            output_dir,
            source_set_id,
            [
                _chunk(
                    source_set_id=source_set_id,
                    source_record_id="R1EA-014",
                    title="FONSI availability",
                    document_role="regulation",
                    authority_level="federal_regulation",
                    citation_label="R1EA-014 | FONSI availability | artifact def456",
                    text="USDA shall make the FONSI available to the public.",
                )
            ],
        )
        result = build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)
        retrieval_summary_path = output_dir / "derived" / source_set_id / "retrieval" / "summary.json"
        retrieval_summary = json.loads(retrieval_summary_path.read_text(encoding="utf-8"))
        retrieval_summary["reviewer_ready"] = False
        retrieval_summary_path.write_text(
            json.dumps(retrieval_summary, sort_keys=True),
            encoding="utf-8",
        )

        strict_validation = validate_claim_outputs(
            output_dir=output_dir,
            source_set_id=source_set_id,
            claims_path=result.claims_path,
            entities_path=result.entities_path,
            nodes_path=result.nodes_path,
            edges_path=result.edges_path,
            chunks_path=output_dir / "derived" / source_set_id / "chunks" / "chunks.jsonl",
        )
        partial_validation = validate_claim_outputs(
            output_dir=output_dir,
            source_set_id=source_set_id,
            claims_path=result.claims_path,
            entities_path=result.entities_path,
            nodes_path=result.nodes_path,
            edges_path=result.edges_path,
            chunks_path=output_dir / "derived" / source_set_id / "chunks" / "chunks.jsonl",
            allow_partial_retrieval=True,
        )

        assert not strict_validation["passed"]
        assert not _check(strict_validation, "retrieval_is_reviewer_ready")["passed"]
        assert partial_validation["passed"]
        partial_readiness = _check(partial_validation, "retrieval_is_reviewer_ready")
        assert partial_readiness["passed"]
        assert partial_readiness["details"]["allow_partial_retrieval"] is True
        assert partial_readiness["details"]["reviewer_ready"] is False


def _check(validation: dict, name: str) -> dict:
    for check in validation["checks"]:
        if check["name"] == name:
            return check
    raise AssertionError(f"Missing validation check {name}")
