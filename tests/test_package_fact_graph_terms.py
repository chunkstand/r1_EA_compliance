from __future__ import annotations

from usfs_r1_ea_sources.package_fact_graph_terms import _base_term_specs


def test_base_term_specs_keep_flpma_authority_metadata_and_deduped_terms() -> None:
    spec = next(
        item
        for item in _base_term_specs()
        if item["normalized_value"] == "flpma_section_206_land_exchange"
    )

    assert spec["source_metadata"] == {
        "authority_family_id": "land_exchange_statutory_authorities",
        "rule_id": "flpma_section_206_land_exchange",
        "source_record_id": "R1EA-146",
        "statutory_citation": "43 U.S.C. 1716",
    }
    assert "FLPMA" in spec["terms"]
    assert "43 U.S.C. 1716" in spec["terms"]
    assert len(spec["terms"]) == len({term.casefold() for term in spec["terms"]})
