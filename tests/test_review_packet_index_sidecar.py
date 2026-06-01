from pathlib import Path
import tempfile

from usfs_r1_ea_sources.review_packet_index import run_review_packet_index
from tests.test_review_packet_index import _read_json
from tests.test_review_packet_index import _validation_check
from tests.test_review_packet_index import _write_json
from tests.test_review_packet_index import _write_minimal_review


def test_review_packet_index_records_sidecar_rule_claim_lineage() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "source_library"
        review_id = "review-sidecar"
        review_dir = output_dir / "reviews" / review_id
        _write_minimal_review(review_dir, review_id=review_id)
        sidecar_links_path = _write_sidecar_artifacts(output_dir)
        sidecar_eval_path = sidecar_links_path.parent / "rule_claim_link_eval_results.json"
        _write_sidecar_compliance_summary(review_dir, sidecar_links_path)
        _write_sidecar_phase_eval(review_dir, sidecar_links_path, sidecar_eval_path)

        result = run_review_packet_index(output_dir=output_dir, review_id=review_id)

        assert result.summary["passed"] is True
        assert result.summary["sidecar_rule_claim_links_used"] is True
        inventory = _read_json(result.row_inventory_path)
        packet = _read_json(result.packet_index_path)
        validation = _read_json(result.validation_path)
        lineage = inventory["sidecar_rule_claim_lineage"]
        assert lineage == packet["sidecar_rule_claim_lineage"]
        assert lineage["sidecar_rule_claim_links_used"] is True
        assert lineage["compliance_review_rule_claim_links_path"] == str(sidecar_links_path)
        assert lineage["phase_eval_selected_rule_claim_links_path"] == str(sidecar_links_path)
        assert lineage["phase_eval_direct_eval_summary_path"] == str(sidecar_eval_path)
        assert lineage["failed_checks"] == []
        assert _validation_check(
            validation,
            "sidecar_rule_claim_lineage_phase_eval_rule_claim_links_match_compliance",
        )["passed"]


def test_review_packet_index_rejects_sidecar_lineage_mismatch() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "source_library"
        review_id = "review-sidecar-mismatch"
        review_dir = output_dir / "reviews" / review_id
        _write_minimal_review(review_dir, review_id=review_id)
        compliance_links_path = _write_sidecar_artifacts(output_dir)
        phase_links_path = _write_sidecar_artifacts(output_dir, suffix="other")
        sidecar_eval_path = phase_links_path.parent / "rule_claim_link_eval_results.json"
        _write_sidecar_compliance_summary(review_dir, compliance_links_path)
        _write_sidecar_phase_eval(review_dir, phase_links_path, sidecar_eval_path)

        result = run_review_packet_index(output_dir=output_dir, review_id=review_id)

        assert result.summary["passed"] is False
        assert result.summary["sidecar_rule_claim_lineage_failed_check_count"] == 1
        validation = _read_json(result.validation_path)
        check = _validation_check(
            validation,
            "sidecar_rule_claim_lineage_phase_eval_rule_claim_links_match_compliance",
        )
        assert check["passed"] is False
        assert validation["summary"]["failure_category_counts"] == {
            "sidecar_rule_claim_lineage_mismatch": 1
        }


def _write_sidecar_artifacts(output_dir: Path, *, suffix: str = "main") -> Path:
    sidecar_dir = (
        output_dir
        / "derived"
        / "source-set-test"
        / "rule_claim_links_sidecar"
        / "generated-unit-nepa-ea"
        / f"applicability-v0-{suffix}"
    )
    sidecar_dir.mkdir(parents=True)
    links_path = sidecar_dir / "rule_claim_links.jsonl"
    links_path.write_text("", encoding="utf-8")
    (sidecar_dir / "summary.json").write_text("{}", encoding="utf-8")
    (sidecar_dir / "rule_claim_link_validation.json").write_text("{}", encoding="utf-8")
    (sidecar_dir / "rule_claim_link_eval_results.json").write_text("{}", encoding="utf-8")
    return links_path


def _write_sidecar_compliance_summary(review_dir: Path, links_path: Path) -> None:
    compliance = _read_json(review_dir / "compliance_review.json")
    compliance["summary"] = {
        "rule_claim_links_path": str(links_path),
        "rule_claim_links_dir": str(links_path.parent),
        "rule_claim_canonical_links_dir": str(links_path.parents[2] / "rule_claim_links"),
        "rule_claim_links_are_canonical": False,
    }
    _write_json(review_dir / "compliance_review.json", compliance)


def _write_sidecar_phase_eval(
    review_dir: Path,
    links_path: Path,
    sidecar_eval_path: Path,
) -> None:
    _write_json(
        review_dir / "phase_eval_results.json",
        {
            "review_id": review_dir.name,
            "source_set_id": "source-set-test",
            "phases": [
                {
                    "name": "rule_claim_binding",
                    "passed": True,
                    "reviewer_ready": True,
                    "details": {
                        "selected_rule_claim_links_path": str(links_path),
                        "selected_rule_claim_eval_path": str(sidecar_eval_path),
                        "direct_eval_summary_path": str(sidecar_eval_path),
                        "direct_eval_status": "direct_eval_present",
                        "uses_sidecar_rule_claim_links": True,
                        "failed_path_checks": [],
                    },
                }
            ],
        },
    )
