from __future__ import annotations

from pathlib import Path
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
GENERAL_REVIEW_RUNTIME_MODULES = [
    PROJECT_ROOT / "src" / "usfs_r1_ea_sources" / "extract.py",
    PROJECT_ROOT / "src" / "usfs_r1_ea_sources" / "retrieval.py",
    PROJECT_ROOT / "src" / "usfs_r1_ea_sources" / "evidence_graph.py",
]
DOMAIN_REVIEW_TERMS = (
    "nepa",
    "environmental assessment",
    "purpose and need",
    "connected actions",
    "cumulative impacts",
    "alternatives analysis",
    "forest plan consistency",
    "decision notice",
    "mitigation measures",
    "scoping public comment",
)


class BitterLessonAlignmentTests(unittest.TestCase):
    def test_general_runtime_layers_do_not_encode_nepa_review_terms(self) -> None:
        failures = []
        for module_path in GENERAL_REVIEW_RUNTIME_MODULES:
            text = module_path.read_text(encoding="utf-8").lower()
            for term in DOMAIN_REVIEW_TERMS:
                if term in text:
                    failures.append(f"{module_path.relative_to(PROJECT_ROOT)} contains {term!r}")
        self.assertEqual(failures, [])

    def test_alignment_doc_records_operational_commitments(self) -> None:
        doc_path = PROJECT_ROOT / "docs" / "BITTER_LESSON_ALIGNMENT.md"
        text = doc_path.read_text(encoding="utf-8")
        required_phrases = [
            "Search and learning are first-class.",
            "Domain knowledge is data.",
            "The runtime builds meta-methods.",
            "Evidence beats intuition.",
            "Scale before cleverness.",
        ]
        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
