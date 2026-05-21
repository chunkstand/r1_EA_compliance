from __future__ import annotations

from pathlib import Path
import tempfile

from usfs_r1_ea_sources.claim_extraction import build_claim_extraction
from usfs_r1_ea_sources.rule_claim_binding import build_rule_claim_links
from usfs_r1_ea_sources.rule_claim_binding_validation import validate_rule_claim_links

from tests.test_rule_claim_binding import _check
from tests.test_rule_claim_binding import _chunk
from tests.test_rule_claim_binding import _prepare_source_library
from tests.test_rule_claim_binding import _read_jsonl
from tests.test_rule_claim_binding import _write_jsonl
from tests.test_rule_claim_binding import _write_rule_pack


def test_rule_claim_validation_rejects_unknown_rule_links() -> None:
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
                    title="EA requirements",
                    document_role="regulation",
                    authority_level="federal",
                    citation_label="R1EA-001 | EA requirements | artifact abc123",
                    text="An environmental assessment should describe the purpose and need.",
                )
            ],
        )
        claims = build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)
        rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
        result = build_rule_claim_links(
            output_dir=output_dir,
            source_set_id=source_set_id,
            rule_pack_path=rule_pack_path,
        )
        links = _read_jsonl(result.links_path)
        links[0]["rule_id"] = "unknown_rule"
        _write_jsonl(result.links_path, links)

        validation = validate_rule_claim_links(
            output_dir=output_dir,
            source_set_id=source_set_id,
            rule_pack_path=rule_pack_path,
            claims_path=claims.claims_path,
            links_path=result.links_path,
            gaps_path=result.gaps_path,
        )

        assert not validation["passed"]
        assert not _check(validation, "all_rules_have_claim_link_or_explicit_gap")["passed"]
        assert not _check(validation, "rule_claim_links_match_rule_filters")["passed"]


def test_rule_claim_validation_rejects_tampered_link_identity_score_and_rank() -> None:
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
                    title="EA requirements",
                    document_role="regulation",
                    authority_level="federal",
                    citation_label="R1EA-001 | EA requirements | artifact abc123",
                    text="An environmental assessment should describe the purpose and need.",
                ),
                _chunk(
                    source_set_id=source_set_id,
                    source_record_id="R1EA-002",
                    title="EA alternatives",
                    document_role="regulation",
                    authority_level="federal",
                    citation_label="R1EA-002 | EA alternatives | artifact def456",
                    text="An environmental assessment should describe alternatives.",
                ),
            ],
        )
        claims = build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)
        rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
        result = build_rule_claim_links(
            output_dir=output_dir,
            source_set_id=source_set_id,
            rule_pack_path=rule_pack_path,
            top_k=2,
        )
        links = _read_jsonl(result.links_path)
        assert len(links) == 2
        links[0]["link_id"] = "rule_claim_link:tampered"
        links[0]["score"] = 99
        links[1]["rank"] = 1
        _write_jsonl(result.links_path, links)

        validation = validate_rule_claim_links(
            output_dir=output_dir,
            source_set_id=source_set_id,
            rule_pack_path=rule_pack_path,
            claims_path=claims.claims_path,
            links_path=result.links_path,
            gaps_path=result.gaps_path,
        )

        assert not validation["passed"]
        assert not _check(validation, "rule_claim_record_identities_are_deterministic")["passed"]
        assert not _check(validation, "rule_claim_link_scores_are_supported")["passed"]
        assert not _check(validation, "rule_claim_link_ranks_are_contiguous")["passed"]


def test_rule_claim_validation_rejects_tampered_gap_identity_and_reason() -> None:
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
                    title="EA requirements",
                    document_role="regulation",
                    authority_level="federal",
                    citation_label="R1EA-001 | EA requirements | artifact abc123",
                    text="An environmental assessment should describe the purpose and need.",
                )
            ],
        )
        claims = build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)
        rule_pack_path = _write_rule_pack(Path(tmp))
        result = build_rule_claim_links(
            output_dir=output_dir,
            source_set_id=source_set_id,
            rule_pack_path=rule_pack_path,
        )
        gaps = _read_jsonl(result.gaps_path)
        assert len(gaps) == 1
        gaps[0]["gap_id"] = "rule_claim_gap:tampered"
        gaps[0]["reason"] = "manual_override"
        _write_jsonl(result.gaps_path, gaps)

        validation = validate_rule_claim_links(
            output_dir=output_dir,
            source_set_id=source_set_id,
            rule_pack_path=rule_pack_path,
            claims_path=claims.claims_path,
            links_path=result.links_path,
            gaps_path=result.gaps_path,
        )

        assert not validation["passed"]
        assert not _check(validation, "rule_claim_record_identities_are_deterministic")["passed"]
        assert not _check(validation, "rule_claim_gap_records_are_explicit")["passed"]
