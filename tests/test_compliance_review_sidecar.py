from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch

from usfs_r1_ea_sources.claim_extraction import build_claim_extraction
from usfs_r1_ea_sources.compliance_review import run_compliance_review
from usfs_r1_ea_sources.rule_claim_binding import build_rule_claim_links
from tests.support.compliance_review_fixtures import (
    _build_source_library,
    _check,
    _write_generated_review_gate,
    _write_package,
    _write_rule_pack,
)


class ComplianceReviewSidecarTests(unittest.TestCase):
    def test_compliance_review_consumes_sidecar_rule_claim_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "source_library"
            source_set_id = "source-set-test"
            review_id = "generated-sidecar-review"
            _build_source_library(output_dir, source_set_id)
            package_path = _write_package(Path(tmp), "Purpose and Need")
            base_rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
            generated_rule_pack_path = _write_generated_review_gate(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=source_set_id,
                package_path=package_path,
                base_rule_pack_path=base_rule_pack_path,
            )
            sidecar_claims = build_claim_extraction(
                output_dir=output_dir,
                source_set_id=source_set_id,
                claims_dir=output_dir / "derived" / source_set_id / "claims_sidecar",
            )
            sidecar_links_dir = (
                output_dir
                / "derived"
                / source_set_id
                / "rule_claim_links_sidecar"
                / "generated-unit-nepa-ea"
                / "applicability-v0"
            )
            sidecar_links = build_rule_claim_links(
                output_dir=output_dir,
                source_set_id=source_set_id,
                claims_path=sidecar_claims.claims_path,
                links_dir=sidecar_links_dir,
                rule_pack_path=generated_rule_pack_path,
            )
            canonical_links_dir = (
                output_dir
                / "derived"
                / source_set_id
                / "rule_claim_links"
                / "generated-unit-nepa-ea"
                / "applicability-v0"
            )

            with patch(
                "usfs_r1_ea_sources.rule_claim_binding.build_rule_claim_links",
                side_effect=AssertionError("canonical rule-claim links should not be rebuilt"),
            ):
                result = run_compliance_review(
                    package_path=package_path,
                    output_dir=output_dir,
                    source_set_id=source_set_id,
                    rule_pack_path=generated_rule_pack_path,
                    review_id=review_id,
                    reuse_package_cache=True,
                    rule_claim_links_path=sidecar_links.links_path,
                )

            self.assertTrue(result.summary["reviewer_ready"])
            self.assertEqual(result.rule_claim_links_path, sidecar_links.links_path)
            self.assertFalse(canonical_links_dir.exists())
            self.assertEqual(result.summary["rule_claim_links_dir"], str(sidecar_links_dir))
            self.assertFalse(result.summary["rule_claim_links_are_canonical"])
            validation = json.loads(
                result.compliance_validation_path.read_text(encoding="utf-8")
            )
            rule_claim_check = _check(validation, "rule_claim_binding_reviewer_ready")
            self.assertTrue(rule_claim_check["passed"])
            self.assertFalse(rule_claim_check["details"]["links_dir_is_canonical"])
