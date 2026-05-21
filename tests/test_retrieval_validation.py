from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest

from usfs_r1_ea_sources.retrieval import build_retrieval_index
from usfs_r1_ea_sources.retrieval import query_retrieval_index

from tests.support.retrieval_fixtures import _check
from tests.support.retrieval_fixtures import _chunk
from tests.support.retrieval_fixtures import _write_catalog_source_set_manifest
from tests.support.retrieval_fixtures import _write_catalog_source_set_manifest_for_dir
from tests.support.retrieval_fixtures import _write_catalog_sqlite
from tests.support.retrieval_fixtures import _write_catalog_sqlite_for_dir
from tests.support.retrieval_fixtures import _write_chunks
from tests.support.retrieval_fixtures import _write_extraction_accuracy_audit
from tests.support.retrieval_fixtures import _write_extraction_diagnostics


class RetrievalValidationTests(unittest.TestCase):
    def test_retrieval_build_fails_validation_on_bad_chunk_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-004"],
            )
            chunk = _chunk(
                source_set_id=source_set_id,
                source_record_id="R1EA-004",
                title="Bad hash source",
                document_role="regulation",
                authority_level="federal_regulation",
                citation_label="R1EA-004 | Bad hash source | artifact abc123",
                text="This chunk hash has been corrupted.",
            )
            chunk["content_sha256"] = "0" * 64
            _write_chunks(output_dir, source_set_id, [chunk])
            _write_catalog_sqlite(output_dir, {"R1EA-004": ["Integrity"]})

            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            self.assertFalse(result.summary["validation_passed"])
            self.assertFalse(result.sqlite_path.exists())
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            hash_check = _check(validation, "chunk_content_hashes_match_text")
            self.assertFalse(hash_check["passed"])
            self.assertEqual(hash_check["details"]["failure_count"], 1)

    def test_retrieval_build_rejects_partial_extraction_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-005"],
                catalog_source_count=2,
                filters={"id": "R1EA-005", "parser": None, "limit": None},
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-005",
                        title="Partial source",
                        document_role="case_law",
                        authority_level="federal",
                        citation_label="R1EA-005 | Partial source | artifact abc123",
                        text="NEPA requires environmental review.",
                    )
                ],
            )
            _write_catalog_sqlite(output_dir, {"R1EA-005": ["NEPA"]})

            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            self.assertFalse(result.summary["validation_passed"])
            self.assertFalse(result.summary["reviewer_ready"])
            self.assertFalse(result.sqlite_path.exists())
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            scope_check = _check(validation, "extraction_scope_is_complete")
            self.assertFalse(scope_check["passed"])
            self.assertEqual(scope_check["details"]["catalog_source_count"], 2)

            diagnostic = build_retrieval_index(
                output_dir=output_dir,
                source_set_id=source_set_id,
                allow_partial_extraction=True,
            )
            self.assertTrue(diagnostic.summary["validation_passed"])
            self.assertFalse(diagnostic.summary["reviewer_ready"])
            self.assertTrue(diagnostic.sqlite_path.exists())

    def test_retrieval_build_backfills_missing_support_document_role_from_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-009"],
            )
            chunk = _chunk(
                source_set_id=source_set_id,
                source_record_id="R1EA-009",
                title="Decision notice",
                document_role="project_record",
                authority_level="project_record",
                citation_label="R1EA-009 | Decision notice | artifact abc123",
                text="The decision notice contains enforceable mitigation measures.",
            )
            chunk["support_document_role"] = None
            _write_chunks(output_dir, source_set_id, [chunk])
            _write_catalog_sqlite(
                output_dir,
                {"R1EA-009": ["Mitigation"]},
                source_rows_by_source={
                    "R1EA-009": {
                        "document_role": "project_record",
                        "metadata_json": {"document_role": "record_of_decision"},
                        "title": "Decision notice",
                    }
                },
            )

            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["support_document_role_counts"], {"record_of_decision": 1})
            query = query_retrieval_index(
                index_path=result.sqlite_path,
                query="",
                source_record_id="R1EA-009",
            )
            self.assertEqual(query["results"][0]["support_document_role"], "record_of_decision")

    def test_retrieval_build_rejects_catalog_with_incompatible_source_record_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-009"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-009",
                        title="Decision notice",
                        document_role="project_record",
                        authority_level="project_record",
                        citation_label="R1EA-009 | Decision notice | artifact abc123",
                        text="The decision notice contains enforceable mitigation measures.",
                    )
                ],
            )
            _write_catalog_sqlite(
                output_dir,
                {
                    "R1EA-009": ["Mitigation"],
                    "R1EA-010": ["Extra row"],
                },
            )
            _write_catalog_source_set_manifest(output_dir, "source-set-other")

            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            self.assertFalse(result.summary["validation_passed"])
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            catalog_check = _check(
                validation,
                "catalog_source_set_matches_requested_source_set",
            )
            self.assertFalse(catalog_check["passed"])
            self.assertEqual(
                catalog_check["details"]["requested_source_set_id"],
                source_set_id,
            )
            self.assertEqual(
                catalog_check["details"]["catalog_source_set_id"],
                "source-set-other",
            )
            self.assertEqual(
                catalog_check["details"]["match_mode"],
                "mismatch",
            )
            self.assertEqual(
                catalog_check["details"]["unexpected_source_record_ids"],
                ["R1EA-010"],
            )

    def test_retrieval_build_auto_resolves_compatible_archived_catalog_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            archived_catalog_dir = output_dir / "runs" / "2026-05-14-replay" / "catalog_gate"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-009"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-009",
                        title="Decision notice",
                        document_role="project_record",
                        authority_level="project_record",
                        citation_label="R1EA-009 | Decision notice | artifact abc123",
                        text="The decision notice contains enforceable mitigation measures.",
                    )
                ],
            )
            _write_catalog_sqlite(
                output_dir,
                {
                    "R1EA-009": ["Mitigation"],
                    "R1EA-010": ["Extra row"],
                },
            )
            _write_catalog_source_set_manifest(output_dir, "source-set-other")
            archived_catalog_dir.mkdir(parents=True, exist_ok=True)
            _write_catalog_source_set_manifest_for_dir(
                archived_catalog_dir,
                "source-set-compatible-archived",
            )
            _write_catalog_sqlite_for_dir(
                archived_catalog_dir,
                {"R1EA-009": ["Mitigation"]},
            )

            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(
                result.summary["catalog_source_set_id"],
                "source-set-compatible-archived",
            )
            self.assertEqual(result.summary["catalog_dir"], str(archived_catalog_dir))
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            catalog_check = _check(
                validation,
                "catalog_source_set_matches_requested_source_set",
            )
            self.assertEqual(
                catalog_check["details"]["match_mode"],
                "selected_source_record_set",
            )

    def test_retrieval_build_prefers_exact_archived_catalog_gate_over_compatible_active_catalog(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            archived_catalog_dir = output_dir / "runs" / "2026-05-14-replay" / "catalog_gate"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-009"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-009",
                        title="Decision notice",
                        document_role="project_record",
                        authority_level="project_record",
                        citation_label="R1EA-009 | Decision notice | artifact abc123",
                        text="The decision notice contains enforceable mitigation measures.",
                    )
                ],
            )
            _write_catalog_sqlite(
                output_dir,
                {
                    "R1EA-009": ["Active topic"],
                },
            )
            _write_catalog_source_set_manifest(output_dir, "source-set-other")
            archived_catalog_dir.mkdir(parents=True, exist_ok=True)
            _write_catalog_source_set_manifest_for_dir(archived_catalog_dir, source_set_id)
            _write_catalog_sqlite_for_dir(
                archived_catalog_dir,
                {"R1EA-009": ["Archived exact topic"]},
            )

            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            self.assertTrue(result.summary["validation_passed"])
            self.assertEqual(result.summary["catalog_source_set_id"], source_set_id)
            self.assertEqual(result.summary["catalog_dir"], str(archived_catalog_dir))

    def test_retrieval_build_requires_verified_flathead_extraction_audit_only_for_full_contract_match(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)

            partial_source_set_id = "source-set-flathead-partial"
            _write_extraction_diagnostics(
                output_dir,
                partial_source_set_id,
                source_record_ids=["R1PLAN-flathead-nf-02"],
            )
            _write_chunks(
                output_dir,
                partial_source_set_id,
                [
                    _chunk(
                        source_set_id=partial_source_set_id,
                        source_record_id="R1PLAN-flathead-nf-02",
                        title="2018 Revised Land Management Plan",
                        document_role="forest_plan",
                        support_document_role="primary_land_management_plan",
                        authority_level="forest",
                        citation_label="R1PLAN-flathead-nf-02 | 2018 Revised Land Management Plan | artifact abc123",
                        text="Flathead forest plan direction applies.",
                    )
                ],
            )
            _write_catalog_sqlite(
                output_dir,
                {"R1PLAN-flathead-nf-02": ["Flathead direction"]},
            )

            partial = build_retrieval_index(
                output_dir=output_dir,
                source_set_id=partial_source_set_id,
            )

            self.assertTrue(partial.summary["validation_passed"])
            self.assertEqual(partial.summary["verified_extraction_required_source_count"], 0)
            self.assertEqual(partial.summary["verified_extraction_contract_ids"], [])

            full_source_set_id = "source-set-flathead-full"
            full_source_record_ids = [f"R1PLAN-flathead-nf-{index:02d}" for index in range(1, 18)]
            _write_extraction_diagnostics(
                output_dir,
                full_source_set_id,
                source_record_ids=full_source_record_ids,
            )
            _write_chunks(
                output_dir,
                full_source_set_id,
                [
                    _chunk(
                        source_set_id=full_source_set_id,
                        source_record_id=source_record_id,
                        title=f"Flathead source {source_record_id}",
                        document_role="forest_plan",
                        support_document_role="forest_plan",
                        authority_level="forest",
                        citation_label=f"{source_record_id} | Flathead source | artifact abc123",
                        text=f"Flathead source text for {source_record_id}.",
                    )
                    for source_record_id in full_source_record_ids
                ],
            )
            _write_catalog_sqlite(
                output_dir,
                {
                    source_record_id: ["Flathead direction"]
                    for source_record_id in full_source_record_ids
                },
            )

            failed = build_retrieval_index(output_dir=output_dir, source_set_id=full_source_set_id)

            self.assertFalse(failed.summary["validation_passed"])
            self.assertEqual(failed.summary["verified_extraction_required_source_count"], 17)
            missing_audit = json.loads(failed.validation_path.read_text(encoding="utf-8"))
            self.assertFalse(
                _check(missing_audit, "verified_extraction_accuracy_audit_exists")["passed"]
            )

            _write_extraction_accuracy_audit(
                output_dir,
                full_source_set_id,
                admitted_source_record_ids=full_source_record_ids,
            )

            passed = build_retrieval_index(output_dir=output_dir, source_set_id=full_source_set_id)

            self.assertTrue(passed.summary["validation_passed"])
            self.assertTrue(passed.summary["reviewer_ready"])
            self.assertTrue(passed.sqlite_path.exists())

    def test_retrieval_build_allows_scope_excluded_rows_in_complete_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-005"],
                skipped_source_record_ids=["R1EA-160"],
                catalog_source_count=2,
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-005",
                        title="Extracted source",
                        document_role="case_law",
                        authority_level="federal",
                        citation_label="R1EA-005 | Extracted source | artifact abc123",
                        text="NEPA requires environmental review.",
                    )
                ],
            )
            _write_catalog_sqlite(output_dir, {"R1EA-005": ["NEPA"]})

            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            self.assertTrue(result.summary["validation_passed"])
            self.assertTrue(result.summary["reviewer_ready"])
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            scope_check = _check(validation, "extraction_scope_is_complete")
            self.assertTrue(scope_check["passed"])
            self.assertEqual(scope_check["details"]["required_extraction_source_count"], 1)

    def test_retrieval_build_fails_when_extracted_source_has_no_chunk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            source_set_id = "source-set-test"
            _write_extraction_diagnostics(
                output_dir,
                source_set_id,
                source_record_ids=["R1EA-006", "R1EA-007"],
            )
            _write_chunks(
                output_dir,
                source_set_id,
                [
                    _chunk(
                        source_set_id=source_set_id,
                        source_record_id="R1EA-006",
                        title="One source",
                        document_role="regulation",
                        authority_level="federal_regulation",
                        citation_label="R1EA-006 | One source | artifact abc123",
                        text="Alternatives must be considered.",
                    )
                ],
            )
            _write_catalog_sqlite(
                output_dir,
                {
                    "R1EA-006": ["Alternatives"],
                    "R1EA-007": ["Scoping"],
                },
            )

            result = build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)

            self.assertFalse(result.summary["validation_passed"])
            validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
            manifest_check = _check(validation, "indexed_sources_match_extraction_manifest")
            self.assertFalse(manifest_check["passed"])
            self.assertEqual(manifest_check["details"]["missing_from_chunks"], ["R1EA-007"])
