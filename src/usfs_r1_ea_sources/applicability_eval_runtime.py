from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from .applicability_eval_authority_universe import _selected_authority_family_templates
from .applicability_eval_authority_universe import _selected_rules
from .applicability_eval_authority_universe import _write_authority_universe
from .applicability_eval_fixture_runtime import _case_package_path
from .applicability_eval_fixture_runtime import _case_source_chunks
from .applicability_eval_fixture_runtime import _write_package_cache
from .applicability_eval_fixture_runtime import _write_source_index
from .applicability_eval_scoring import _read_case_artifacts
from .applicability_eval_scoring import _score_case
from .applicability_eval_summary import _aggregate_arbitration_summary
from .applicability_eval_summary import _authority_family_template_coverage
from .applicability_eval_summary import _failure_category_counts
from .applicability_eval_support import DEFAULT_APPLICABILITY_EVAL_PATH
from .applicability_eval_support import APPLICABILITY_EVAL_RESULT_SCHEMA_VERSION
from .applicability_eval_support import APPLICABILITY_EVAL_SCHEMA_VERSION
from .applicability_eval_support import ApplicabilityEvalResult
from .applicability_eval_support import _case_list
from .applicability_eval_support import _case_rate
from .applicability_eval_support import _load_authority_family_template_set
from .applicability_eval_support import _load_eval_payload
from .applicability_eval_support import _source_chunk_specs
from .applicability_eval_support import _strings
from .applicability_eval_support import _utc_now
from .applicability_eval_support import _validate_safe_segment
from .applicability_eval_support import _write_json
from .applicability import DEFAULT_AUTHORITY_FAMILY_TEMPLATES_PATH
from .applicability_decisions import build_applicability_decisions
from .applicability_retrieval import build_applicability_retrieval_traces
from .applicability_rule_pack import generate_applicability_rule_pack
from .applicability_validation import apply_applicability_adjudication
from .applicability_validation import validate_applicability_run
from .applicability_validation import write_applicability_adjudication_template
from .package_fact_graph import build_package_fact_graph
from .rule_packs import DEFAULT_RULE_PACK_PATH
from .rule_packs import load_rule_pack


def run_applicability_eval(
    *,
    output_dir: Path,
    eval_file: Path = DEFAULT_APPLICABILITY_EVAL_PATH,
    base_rule_pack_path: Path = DEFAULT_RULE_PACK_PATH,
    authority_family_templates_path: Path | None = DEFAULT_AUTHORITY_FAMILY_TEMPLATES_PATH,
    source_set_id: str | None = None,
    results_dir: Path | None = None,
    top_k: int = 5,
) -> ApplicabilityEvalResult:
    """Run deterministic applicability decision-quality eval cases."""

    output_dir = Path(output_dir)
    eval_file = Path(eval_file)
    base_rule_pack_path = Path(base_rule_pack_path)
    authority_family_templates_path = (
        Path(authority_family_templates_path) if authority_family_templates_path else None
    )
    eval_payload = _load_eval_payload(eval_file, APPLICABILITY_EVAL_SCHEMA_VERSION)
    base_rule_pack = load_rule_pack(base_rule_pack_path)
    authority_family_template_set = _load_authority_family_template_set(
        authority_family_templates_path
    )
    cases = _case_list(eval_payload)
    eval_output_dir = (
        Path(results_dir) if results_dir else output_dir / "reviews" / "applicability_eval"
    )
    eval_output_dir.mkdir(parents=True, exist_ok=True)
    output_path = eval_output_dir / "applicability_eval_results.json"
    inherited_source_chunks = _source_chunk_specs(eval_payload.get("source_chunks"))
    case_results = []
    for index, case in enumerate(cases, start=1):
        case_results.append(
            _run_eval_case(
                output_dir=output_dir,
                eval_output_dir=eval_output_dir,
                eval_file=eval_file,
                eval_payload=eval_payload,
                base_rule_pack_path=base_rule_pack_path,
                base_rule_pack=base_rule_pack,
                authority_family_template_set=authority_family_template_set,
                source_set_id=source_set_id,
                case=case,
                case_index=index,
                inherited_source_chunks=inherited_source_chunks,
                top_k=top_k,
            )
        )

    passed_count = sum(1 for case in case_results if case["passed"])
    case_count = len(case_results)
    source_set_ids = sorted(
        {str(case["source_set_id"]) for case in case_results if case.get("source_set_id")}
    )
    summary = {
        "schema_version": APPLICABILITY_EVAL_RESULT_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "eval_file": str(eval_file),
        "eval_id": eval_payload.get("id"),
        "eval_version": eval_payload.get("version"),
        "output_dir": str(eval_output_dir),
        "output_path": str(output_path),
        "base_rule_pack_path": str(base_rule_pack_path),
        "base_rule_pack_id": base_rule_pack.get("rule_pack_id"),
        "base_rule_pack_version": base_rule_pack.get("version"),
        "authority_family_templates_path": (
            str(authority_family_templates_path)
            if authority_family_templates_path
            else None
        ),
        "source_set_id": source_set_id or (source_set_ids[0] if len(source_set_ids) == 1 else None),
        "source_set_ids": source_set_ids,
        "case_count": case_count,
        "passed_count": passed_count,
        "failed_count": case_count - passed_count,
        "passed": case_count > 0 and passed_count == case_count,
        "generated_rule_pack_ready_case_count": sum(
            1 for case in case_results if case.get("generated_rule_pack_ready")
        ),
        "metrics": {
            "pass_rate": passed_count / case_count if case_count else 0.0,
            "status_match_rate": _case_rate(case_results, "expected_statuses_match"),
            "arbitration_status_match_rate": _case_rate(
                case_results,
                "arbitration_status_alignment_matches",
            ),
            "arbitration_decision_effect_match_rate": _case_rate(
                case_results,
                "arbitration_decision_effect_alignment_matches",
            ),
            "applicable_partition_match_rate": _case_rate(
                case_results,
                "expected_applicable_authorities_match",
            ),
            "non_applicable_partition_match_rate": _case_rate(
                case_results,
                "expected_non_applicable_authorities_match",
            ),
            "coverage_certificate_rate": _case_rate(
                case_results,
                "non_applicable_coverage_supported",
            ),
            "generated_rule_pack_match_rate": _case_rate(
                case_results,
                "generated_rule_pack_matches_applicability",
            ),
        },
        "authority_family_template_coverage": _authority_family_template_coverage(
            eval_payload=eval_payload,
            template_set=authority_family_template_set,
            case_results=case_results,
        ),
        "arbitration_summary": _aggregate_arbitration_summary(case_results),
        "failure_category_counts": _failure_category_counts(case_results),
        "cases": case_results,
    }
    _write_json(output_path, summary)
    return ApplicabilityEvalResult(
        eval_file=eval_file,
        output_dir=eval_output_dir,
        output_path=output_path,
        summary=summary,
    )


def _run_eval_case(
    *,
    output_dir: Path,
    eval_output_dir: Path,
    eval_file: Path,
    eval_payload: dict[str, Any],
    base_rule_pack_path: Path,
    base_rule_pack: dict[str, Any],
    authority_family_template_set: dict[str, Any] | None,
    source_set_id: str | None,
    case: dict[str, Any],
    case_index: int,
    inherited_source_chunks: list[dict[str, Any]],
    top_k: int,
) -> dict[str, Any]:
    case_id = str(case.get("id") or f"case-{case_index}").strip()
    _validate_safe_segment(case_id, "case id")
    case_source_set_id = str(
        source_set_id
        or case.get("source_set_id")
        or eval_payload.get("source_set_id")
        or f"source-set-{case_id}"
    )
    _validate_safe_segment(case_source_set_id, "source_set_id")
    review_id = str(case.get("review_id") or f"applicability-eval-{case_id}")
    _validate_safe_segment(review_id, "review_id")
    review_dir = output_dir / "reviews" / review_id
    applicability_dir = review_dir / "applicability"

    selected_rules = _selected_rules(base_rule_pack, case)
    selected_authority_family_templates = _selected_authority_family_templates(
        authority_family_template_set,
        case,
    )
    source_chunks = _case_source_chunks(
        case=case,
        inherited_source_chunks=inherited_source_chunks,
        rules=selected_rules,
        authority_family_templates=selected_authority_family_templates,
        source_set_id=case_source_set_id,
    )
    _write_package_cache(
        review_dir=review_dir,
        review_id=review_id,
        source_set_id=case_source_set_id,
        case=case,
        eval_file=eval_file,
    )
    retrieval_index_path = _write_source_index(
        output_dir=output_dir,
        eval_output_dir=eval_output_dir,
        case_id=case_id,
        source_set_id=case_source_set_id,
        chunks=source_chunks,
    )
    _write_authority_universe(
        applicability_dir=applicability_dir,
        review_id=review_id,
        source_set_id=case_source_set_id,
        base_rule_pack_path=base_rule_pack_path,
        base_rule_pack=base_rule_pack,
        rules=selected_rules,
        authority_family_template_set=authority_family_template_set,
        authority_family_templates=selected_authority_family_templates,
    )
    build_package_fact_graph(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=case_source_set_id,
        package_path=_case_package_path(case, eval_file),
    )
    build_applicability_retrieval_traces(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=case_source_set_id,
        retrieval_index_path=retrieval_index_path,
        top_k=top_k,
    )
    build_applicability_decisions(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=case_source_set_id,
    )
    adjudication_summary = _apply_case_adjudication_if_requested(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=case_source_set_id,
        case=case,
    )
    validation_result = validate_applicability_run(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=case_source_set_id,
    )
    generated_summary = None
    generated_error = None
    if validation_result.summary.get("passed"):
        try:
            generated_result = generate_applicability_rule_pack(
                output_dir=output_dir,
                review_id=review_id,
                source_set_id=case_source_set_id,
                base_rule_pack_path=base_rule_pack_path,
            )
            generated_summary = generated_result.summary
        except (FileNotFoundError, ValueError) as error:
            generated_error = str(error)

    artifacts = _read_case_artifacts(applicability_dir)
    if generated_summary is None:
        # Reused review directories can retain old generated-pack artifacts from an earlier
        # successful run. Ignore them unless generation completed in this invocation.
        artifacts["generated_rule_pack"] = {}
        artifacts["generated_validation"] = {}
    return _score_case(
        case=case,
        case_id=case_id,
        review_id=review_id,
        source_set_id=case_source_set_id,
        review_dir=review_dir,
        retrieval_index_path=retrieval_index_path,
        adjudication_summary=adjudication_summary,
        validation_summary=validation_result.summary,
        generated_summary=generated_summary,
        generated_error=generated_error,
        artifacts=artifacts,
    )


def _apply_case_adjudication_if_requested(
    *,
    output_dir: Path,
    review_id: str,
    source_set_id: str,
    case: dict[str, Any],
) -> dict[str, Any] | None:
    adjudication = case.get("applicability_adjudication")
    if not isinstance(adjudication, dict):
        return None
    template_result = write_applicability_adjudication_template(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=source_set_id,
    )
    template = json.loads(template_result.output_path.read_text(encoding="utf-8"))
    item_specs = adjudication.get("items_by_rule_id")
    if not isinstance(item_specs, dict):
        item_specs = {}
    for item in template.get("items") or []:
        if not isinstance(item, dict):
            continue
        rule_id = _rule_id_from_candidate_id(str(item.get("candidate_authority_id") or ""))
        spec = (
            item_specs.get(rule_id)
            or item_specs.get(str(item.get("candidate_authority_id") or ""))
            or item_specs.get(str(item.get("decision_id") or ""))
        )
        if not isinstance(spec, dict):
            continue
        item["final_status"] = spec.get("final_status", item.get("final_status"))
        item["disposition"] = spec.get("disposition", item.get("disposition"))
        item["adjudicated_at"] = spec.get("adjudicated_at") or adjudication.get(
            "adjudicated_at",
        )
        item["adjudicated_by"] = spec.get("adjudicated_by") or adjudication.get(
            "adjudicated_by",
        )
        item["source_type"] = spec.get("source_type") or adjudication.get(
            "source_type",
            "applicability-gold-eval",
        )
        item["rationale"] = spec.get("rationale") or adjudication.get(
            "rationale",
            "Applicability eval fixture adjudication.",
        )
        refs = sorted(
            set(
                _strings(item.get("supporting_citation_refs"))
                + _strings(spec.get("supporting_citation_refs"))
            )
        )
        item["supporting_citation_refs"] = refs or ["EA-PACKAGE-001"]
    _write_json(template_result.output_path, template)
    apply_result = apply_applicability_adjudication(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=source_set_id,
        adjudication_file=template_result.output_path,
    )
    return {
        "requested": True,
        "template_path": str(template_result.output_path),
        "markdown_path": str(template_result.markdown_path),
        "apply_path": str(apply_result.output_path),
        "passed": apply_result.summary.get("passed"),
        "applied": apply_result.summary.get("applied"),
        "applied_item_count": apply_result.summary.get("applied_item_count", 0),
        "remaining_unresolved_authority_count": apply_result.summary.get(
            "remaining_unresolved_authority_count",
        ),
    }


def _rule_id_from_candidate_id(candidate_id: str) -> str:
    return candidate_id.rsplit(":", 1)[-1] if candidate_id else ""
