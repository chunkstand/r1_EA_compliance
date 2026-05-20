from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from usfs_r1_ea_sources.source_set_support import (
    resolve_support_document_role,
    source_derived_dir,
)


class SourceSetSupportTests(unittest.TestCase):
    def test_resolve_support_document_role_prefers_r1_register_override(self) -> None:
        role = resolve_support_document_role(
            {
                "source_record_id": "R1PLAN-custer-gallatin-nf-06",
                "document_role": "forest_plan",
                "metadata": {},
            },
            support_document_role_overrides={
                "R1PLAN-custer-gallatin-nf-06": "biological_assessment",
            },
        )

        self.assertEqual(role, "biological_assessment")

    def test_source_derived_dir_rejects_unsafe_source_set_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                source_derived_dir(Path(tmp), "../outside")
