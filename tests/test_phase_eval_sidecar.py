from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import json
import tempfile

from usfs_r1_ea_sources import cli_eval
from usfs_r1_ea_sources.claim_extraction import build_claim_extraction
from usfs_r1_ea_sources.cli import build_parser
from usfs_r1_ea_sources.compliance_review import run_compliance_review
from usfs_r1_ea_sources.phase_eval import run_phase_aligned_eval
from usfs_r1_ea_sources.rule_claim_binding import build_rule_claim_links
from tests.support.compliance_phase_eval_fixtures import _write_graph_phase_outputs
from tests.support.compliance_review_fixtures import (
    _build_source_library,
    _run_generated_compliance_review,
    _write_generated_review_gate,
    _write_package,
    _write_rule_pack,
)
from tests.support.compliance_review_eval_fixtures import (
    _direct_eval_result_payload,
    _phase,
    _write_downstream_direct_eval_phase_outputs,
)


def test_review_phase_eval_uses_sidecar_rule_claim_eval_from_compliance_review() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "source_library"
        source_set_id = "source-set-test"
        review_id = "phase-sidecar-review"
        _build_source_library(output_dir, source_set_id)
        _write_graph_phase_outputs(output_dir, source_set_id)
        _write_downstream_direct_eval_phase_outputs(output_dir, source_set_id)
        package_path = _write_package(Path(tmp), "Purpose and Need")
        base_rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
        generated_rule_pack_path = _write_generated_review_gate(
            output_dir=output_dir,
            review_id=review_id,
            source_set_id=source_set_id,
            package_path=package_path,
            base_rule_pack_path=base_rule_pack_path,
        )
        sidecar_links = _build_sidecar_rule_claim_links(
            output_dir=output_dir,
            source_set_id=source_set_id,
            rule_pack_path=generated_rule_pack_path,
        )
        sidecar_eval_path = _write_sidecar_rule_claim_eval(
            sidecar_links.links_path.parent,
            source_set_id=source_set_id,
        )
        run_compliance_review(
            package_path=package_path,
            output_dir=output_dir,
            source_set_id=source_set_id,
            rule_pack_path=generated_rule_pack_path,
            review_id=review_id,
            reuse_package_cache=True,
            rule_claim_links_path=sidecar_links.links_path,
        )

        phase_result = run_phase_aligned_eval(
            output_dir=output_dir,
            source_set_id=source_set_id,
            review_id=review_id,
        )

        rule_claim_phase = _phase(phase_result.summary, "rule_claim_binding")
        assert rule_claim_phase["passed"]
        assert rule_claim_phase["reviewer_ready"]
        assert rule_claim_phase["details"]["uses_sidecar_rule_claim_links"] is True
        assert rule_claim_phase["details"]["failed_path_checks"] == []
        assert rule_claim_phase["details"]["selected_rule_claim_links_path"] == str(
            sidecar_links.links_path
        )
        assert Path(rule_claim_phase["details"]["direct_eval_summary_path"]) == sidecar_eval_path
        assert rule_claim_phase["details"]["direct_eval_status"] == "direct_eval_present"


def test_phase_eval_rejects_explicit_sidecar_links_that_mismatch_review() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "source_library"
        source_set_id = "source-set-test"
        review_id = "phase-canonical-review"
        _build_source_library(output_dir, source_set_id)
        _write_graph_phase_outputs(output_dir, source_set_id)
        package_path = _write_package(Path(tmp), "Purpose and Need")
        base_rule_pack_path = _write_rule_pack(Path(tmp), rule_ids=["purpose_need"])
        _run_generated_compliance_review(
            output_dir=output_dir,
            review_id=review_id,
            source_set_id=source_set_id,
            package_path=package_path,
            base_rule_pack_path=base_rule_pack_path,
        )
        sidecar_links = _build_sidecar_rule_claim_links(
            output_dir=output_dir,
            source_set_id=source_set_id,
            rule_pack_path=(
                output_dir / "reviews" / review_id / "applicability" / "generated_rule_pack.json"
            ),
        )

        phase_result = run_phase_aligned_eval(
            output_dir=output_dir,
            source_set_id=source_set_id,
            review_id=review_id,
            rule_claim_links_path=sidecar_links.links_path,
        )

        rule_claim_phase = _phase(phase_result.summary, "rule_claim_binding")
        assert not rule_claim_phase["passed"]
        assert "explicit_rule_claim_links_path_matches_compliance_review" in (
            rule_claim_phase["details"]["failed_path_checks"]
        )


def test_phase_eval_cli_propagates_rule_claim_links_path(monkeypatch) -> None:
    captured = {}

    def fake_run_phase_aligned_eval(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(summary={"reviewer_ready": True})

    monkeypatch.setattr(cli_eval, "run_phase_aligned_eval", fake_run_phase_aligned_eval)
    parser = build_parser()
    args = parser.parse_args(
        [
            "phase-eval",
            "--output-dir",
            "source_library",
            "--source-set-id",
            "source-set-1",
            "--rule-claim-links-path",
            "source_library/derived/source-set-1/rule_claim_links_sidecar/unit/0.1.0/rule_claim_links.jsonl",
        ]
    )

    assert cli_eval.handle_eval_command(args, parser) == 0
    assert captured["rule_claim_links_path"] == Path(
        "source_library/derived/source-set-1/rule_claim_links_sidecar/unit/0.1.0/rule_claim_links.jsonl"
    )


def _build_sidecar_rule_claim_links(*, output_dir: Path, source_set_id: str, rule_pack_path: Path):
    sidecar_claims = build_claim_extraction(
        output_dir=output_dir,
        source_set_id=source_set_id,
        claims_dir=output_dir / "derived" / source_set_id / "claims_sidecar",
    )
    return build_rule_claim_links(
        output_dir=output_dir,
        source_set_id=source_set_id,
        claims_path=sidecar_claims.claims_path,
        links_dir=(
            output_dir
            / "derived"
            / source_set_id
            / "rule_claim_links_sidecar"
            / "generated-unit-nepa-ea"
            / "applicability-v0"
        ),
        rule_pack_path=rule_pack_path,
    )


def _write_sidecar_rule_claim_eval(links_dir: Path, *, source_set_id: str) -> Path:
    path = links_dir / "rule_claim_link_eval_results.json"
    path.write_text(
        json.dumps(
            _direct_eval_result_payload(
                contract_path=Path("config/rule_claim_link_eval_seed.json"),
                eval_id="rule-claim-direct-eval-v1",
                source_set_id=source_set_id,
            ),
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path
