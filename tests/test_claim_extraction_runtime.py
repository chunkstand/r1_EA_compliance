from __future__ import annotations

from usfs_r1_ea_sources.claim_extraction_runtime import _extract_claims
from usfs_r1_ea_sources.claim_extraction_runtime import _sentence_spans
from usfs_r1_ea_sources.claim_extraction_runtime import _window_claim_span

from tests.test_claim_extraction import _chunk


def test_sentence_spans_skip_abbreviations_and_decimals() -> None:
    spans = _sentence_spans(
        "Sec. 5.2 requires the agency shall act when effects are unknown. "
        "The official must document the decision."
    )

    assert [sentence for _, _, sentence in spans] == [
        "Sec. 5.2 requires the agency shall act when effects are unknown.",
        "The official must document the decision.",
    ]


def test_extract_claims_captures_structural_definition_pattern() -> None:
    claims = _extract_claims(
        chunks=[
            _chunk(
                source_set_id="source-set-test",
                source_record_id="R1EA-028",
                title="Forest Service Directives",
                document_role="agency_policy",
                authority_level="federal",
                citation_label="R1EA-028 | Forest Service Directives | artifact abc123",
                text=(
                    "The Forest Service Directive System consists of the Forest Service "
                    "Manual and Handbooks, which codify the agency's policy, practice, "
                    "and procedure."
                ),
            )
        ],
        source_set_id="source-set-test",
    )

    assert len(claims) == 1
    assert claims[0]["source_record_id"] == "R1EA-028"
    assert claims[0]["claim_type"] == "definition"
    assert claims[0]["pattern_id"] == "structural_definition"


def test_extract_claims_deduplicates_overlapping_source_offsets() -> None:
    text = "The responsible official must document the decision."
    claims = _extract_claims(
        chunks=[
            _chunk(
                source_set_id="source-set-test",
                source_record_id="R1EA-020",
                title="Decision documentation",
                document_role="handbook",
                authority_level="agency_guidance",
                citation_label="R1EA-020 | Decision documentation | artifact abc123",
                text=text,
                chunk_id="chunk:R1EA-020:a",
            ),
            _chunk(
                source_set_id="source-set-test",
                source_record_id="R1EA-020",
                title="Decision documentation",
                document_role="handbook",
                authority_level="agency_guidance",
                citation_label="R1EA-020 | Decision documentation | artifact abc123",
                text=text,
                chunk_id="chunk:R1EA-020:b",
            ),
        ],
        source_set_id="source-set-test",
    )

    assert len(claims) == 1
    assert claims[0]["claim_type"] == "obligation"


def test_window_claim_span_trims_long_sentence_around_match() -> None:
    prefix = "whereas " * 90
    match_segment = "the responsible official shall document the decision"
    suffix = " after review" * 120
    text = f"{prefix}{match_segment}{suffix}."
    pattern_start = text.index("shall")

    start, end, claim_text = _window_claim_span(
        text,
        0,
        len(text),
        pattern_start,
        max_chars=800,
    )

    assert 0 <= start < end <= len(text)
    assert len(claim_text) <= 800
    assert "shall document the decision" in claim_text
