from __future__ import annotations

import hashlib
import unittest

from usfs_r1_ea_sources.selected_action import extract_selected_action_scope


class SelectedActionTests(unittest.TestCase):
    def test_extracts_selected_action_without_broad_resource_background(self) -> None:
        artifact_sha256 = hashlib.sha256(b"unit").hexdigest()
        chunks = [
            _chunk(
                index=0,
                artifact_sha256=artifact_sha256,
                section="Decision Notice",
                heading="Selected Alternative",
                text=(
                    "The Selected Alternative authorizes vegetation treatment and road "
                    "decommissioning. No mining is planned."
                ),
            ),
            _chunk(
                index=1,
                artifact_sha256=artifact_sha256,
                section="Appendix A",
                heading="Minerals and Energy Resources",
                text=(
                    "Minerals and Energy Resources. Mineral activity will continue "
                    "under the 1872 mining law, and oil and gas leasing may occur."
                ),
            ),
        ]

        extraction = extract_selected_action_scope(chunks)

        scope = extraction["selected_action_scope"]
        self.assertEqual(scope["scope_status"], "selected_action_found")
        self.assertEqual(scope["package_chunk_ids"], ["chunk-0"])
        self.assertIn("No mining is planned", extraction["action_statements"][0]["text_excerpt"])
        excluded = extraction["excluded_context_summary"]
        self.assertEqual(excluded["excluded_chunk_count"], 1)
        self.assertEqual(
            excluded["sample_excluded_chunks"][0]["package_chunk_id"],
            "chunk-1",
        )


def _chunk(
    *,
    index: int,
    artifact_sha256: str,
    section: str,
    heading: str,
    text: str,
) -> dict:
    return {
        "chunk_id": f"chunk-{index}",
        "source_set_id": "source-set-unit",
        "source_record_id": "EA-PACKAGE-001",
        "chunk_index": index,
        "artifact_sha256": artifact_sha256,
        "citation_label": "EA-PACKAGE-001",
        "page": index + 1,
        "section": section,
        "heading": heading,
        "char_start": index * 1000,
        "char_end": index * 1000 + len(text),
        "content_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "text": text,
    }
