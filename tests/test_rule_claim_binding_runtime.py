from __future__ import annotations

from usfs_r1_ea_sources.rule_claim_binding_runtime import _build_links
from usfs_r1_ea_sources.rule_claim_binding_runtime import _claim_matches_rule_filters
from usfs_r1_ea_sources.rule_claim_binding_runtime import _score_rule_claim
from usfs_r1_ea_sources.rule_claim_binding_runtime import _tokenize


def test_claim_matches_rule_filters_allows_topic_slug_when_source_record_is_fixed() -> None:
    claim = _claim(
        claim_id="claim:R1EA-082:1",
        source_record_id="R1EA-082",
        review_topics=["Topic unrelated to the slug filter"],
    )

    assert _claim_matches_rule_filters(
        claim,
        {
            "source_record_id": "R1EA-082",
            "document_role": "regulation",
            "authority_level": "federal",
            "topic": "clean_water_act_wotus_permits",
        },
    )


def test_claim_matches_rule_filters_allows_reconciled_source_record_ids() -> None:
    claim = _claim(
        claim_id="claim:FED-001:1",
        source_record_id="FED-001",
        review_topics=["Topic unrelated to the slug filter"],
    )

    assert _claim_matches_rule_filters(
        claim,
        {
            "source_record_id": "R1EA-001",
            "document_role": "regulation",
            "authority_level": "federal",
            "topic": "nepa_core_statute",
        },
        source_record_ids=["R1EA-001", "FED-001"],
    )


def test_score_rule_claim_returns_expected_terms_and_topic_bonus() -> None:
    rule = {
        "id": "purpose_need",
        "title": "Purpose and need rule",
        "requirement": "Document purpose and need.",
        "source_query": "purpose and need",
        "package_terms": ["purpose", "need"],
        "source_filters": {"review_topic": "purpose_need"},
    }
    claim = _claim(
        claim_id="claim:R1EA-001:1",
        source_record_id="R1EA-001",
        claim_text="The environmental assessment should describe the purpose and need.",
        review_topics=["Purpose and need"],
    )

    score, matched_terms = _score_rule_claim(
        rule,
        claim,
        terms=_tokenize(" ".join([rule["source_query"], rule["requirement"], rule["title"]])),
        query=rule["source_query"],
    )

    assert matched_terms == ["purpose", "need"]
    assert round(score, 6) == 1.16


def test_build_links_orders_matches_and_emits_explicit_gap() -> None:
    rule_pack = {
        "rule_pack_id": "unit-nepa-ea",
        "version": "0.1.0",
        "rules": [
            {
                "id": "purpose_need",
                "title": "Purpose and need rule",
                "requirement": "Document purpose and need.",
                "source_query": "purpose and need",
                "package_terms": ["purpose", "need"],
                "source_filters": {
                    "document_role": "regulation",
                    "authority_level": "federal",
                },
            },
            {
                "id": "mitigation",
                "title": "Mitigation rule",
                "requirement": "Document mitigation measures.",
                "source_query": "mitigation monitoring",
                "package_terms": ["mitigation"],
                "source_filters": {
                    "document_role": "regulation",
                    "authority_level": "federal",
                },
            },
        ],
    }
    claims = [
        _claim(
            claim_id="claim:R1EA-001:1",
            source_record_id="R1EA-001",
            claim_text="The environmental assessment should describe the purpose and need.",
            review_topics=["Purpose and need"],
        ),
        _claim(
            claim_id="claim:R1EA-002:1",
            source_record_id="R1EA-002",
            claim_text="The need for federal action must be explained.",
            review_topics=["Need statement"],
            source_char_start=40,
            source_char_end=88,
            chunk_char_start=40,
            chunk_char_end=88,
        ),
    ]

    links, gaps = _build_links(
        source_set_id="source-set-test",
        rule_pack=rule_pack,
        claims=claims,
        top_k=2,
        created_at="2026-05-20T00:00:00Z",
    )

    assert [link["rule_id"] for link in links] == ["purpose_need", "purpose_need"]
    assert [link["claim_id"] for link in links] == ["claim:R1EA-001:1", "claim:R1EA-002:1"]
    assert [link["rank"] for link in links] == [1, 2]
    assert gaps == [
        {
            "created_at": "2026-05-20T00:00:00Z",
            "gap_id": gaps[0]["gap_id"],
            "reason": "no_validated_source_claim_match",
            "rule_id": "mitigation",
            "rule_pack_id": "unit-nepa-ea",
            "rule_pack_version": "0.1.0",
            "rule_query": "mitigation monitoring Document mitigation measures. Mitigation rule mitigation",
            "rule_requirement": "Document mitigation measures.",
            "rule_source_filters": {
                "authority_level": "federal",
                "document_role": "regulation",
            },
            "rule_title": "Mitigation rule",
            "schema_version": "rule-claim-link-gaps-v0",
            "source_set_id": "source-set-test",
            "validation_status": "explicit_no_claim_gap",
        }
    ]


def _claim(
    *,
    claim_id: str,
    source_record_id: str,
    claim_text: str = "The environmental assessment should describe the purpose and need.",
    review_topics: list[str] | None = None,
    source_char_start: int = 0,
    source_char_end: int = 64,
    chunk_char_start: int = 0,
    chunk_char_end: int = 64,
) -> dict:
    return {
        "claim_id": claim_id,
        "claim_type": "guidance",
        "claim_text": claim_text,
        "source_record_id": source_record_id,
        "chunk_id": f"chunk:{source_record_id}:0",
        "citation_label": f"{source_record_id} | Test citation | artifact abc123",
        "authority_level": "federal",
        "document_role": "regulation",
        "review_topics": review_topics or [],
        "title": "EA requirements",
        "artifact_sha256": "artifact123",
        "artifact_path": f"artifacts/raw/{source_record_id}.html",
        "original_url": f"https://example.test/{source_record_id}/original",
        "effective_url": f"https://example.test/{source_record_id}",
        "final_url": f"https://example.test/{source_record_id}",
        "parser_name": "unit_parser",
        "parser_version": "1.0",
        "source_text_path": f"derived/source-set-test/extracted_text/{source_record_id}.txt",
        "source_char_start": source_char_start,
        "source_char_end": source_char_end,
        "chunk_char_start": chunk_char_start,
        "chunk_char_end": chunk_char_end,
        "content_sha256": f"content:{source_record_id}",
        "chunk_content_sha256": f"chunk:{source_record_id}",
        "validation_status": "valid",
    }
