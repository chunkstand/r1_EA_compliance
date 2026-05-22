from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from .artifact_utils import _dict
from .artifact_utils import _dict_list
from .artifact_utils import _utc_now
from .artifact_utils import _write_json
from .draft_generation_common import _check
from .draft_generation_common import _safe_len
from .draft_generation_common import _sha256_file
from .draft_generation_common import DEFAULT_CONFIG_PATH
from .draft_generation_common import DEFENSIBILITY_FILENAME
from .draft_generation_common import DEFENSIBILITY_SCHEMA_VERSION
from .draft_generation_common import DraftGenerationBundle
from .draft_generation_common import DraftGenerationContext
from .draft_generation_common import DraftGenerationResult
from .draft_generation_common import GENERATOR_VERSION
from .draft_generation_common import MANIFEST_FILENAME
from .draft_generation_common import MANIFEST_SCHEMA_VERSION
from .draft_generation_common import MARKDOWN_FILENAME
from .draft_generation_common import PACKAGE_FILENAME
from .draft_generation_common import PACKAGE_SCHEMA_VERSION
from .draft_generation_common import REFUSAL_FILENAME
from .draft_generation_common import REFUSAL_SCHEMA_VERSION
from .draft_generation_common import TRACEABILITY_FILENAME
from .draft_generation_common import TRACEABILITY_SCHEMA_VERSION
from .draft_generation_common import VALIDATION_FILENAME
from .draft_generation_common import VALIDATION_SCHEMA_VERSION
from .draft_generation_inputs import _build_finding_index
from .draft_generation_inputs import _input_checks
from .draft_generation_inputs import load_draft_generation_context
from .draft_generation_sections import _generate_sections


def run_draft_generate(
    *,
    output_dir: Path = Path("source_library"),
    review_id: str | None = None,
    config_path: Path = DEFAULT_CONFIG_PATH,
    results_dir: Path | None = None,
) -> DraftGenerationResult:
    context = load_draft_generation_context(
        output_dir=output_dir,
        review_id=review_id,
        config_path=config_path,
    )
    bundle = build_draft_generation_bundle(
        context=context,
        results_dir=results_dir,
    )
    target_dir = results_dir or context.review_dir / "draft_generation"
    return _write_bundle(bundle=bundle, results_dir=target_dir)


def build_draft_generation_bundle(
    *,
    context: DraftGenerationContext,
    results_dir: Path | None = None,
    requested_output_ids: list[str] | None = None,
    config_override: dict[str, Any] | None = None,
) -> DraftGenerationBundle:
    config = deepcopy(config_override if config_override is not None else context.config)
    resolved_results_dir = Path(results_dir) if results_dir is not None else context.review_dir / "draft_generation"
    checks = _input_checks(context=context, config=config)
    bundle_index = _build_finding_index(context)
    checks.extend(bundle_index["checks"])
    generation = _generate_sections(
        context=context,
        config=config,
        bundle_index=bundle_index,
        requested_output_ids=requested_output_ids,
    )
    checks.extend(generation["checks"])

    package = _build_package(
        context=context,
        config=config,
        sections=generation["sections"],
        refusals=generation["refusals"],
        results_dir=resolved_results_dir,
    )
    traceability = _build_traceability(
        context=context,
        sections=generation["sections"],
        paragraph_traces=generation["paragraph_traces"],
    )
    refusals = _build_refusals(
        context=context,
        refusal_entries=generation["refusals"],
    )
    defensibility_packet = _build_defensibility_packet(
        context=context,
        sections=generation["sections"],
        paragraph_traces=generation["paragraph_traces"],
        refusals=generation["refusals"],
    )
    checks.extend(
        _output_checks(
            context=context,
            config=config,
            package=package,
            traceability=traceability,
            refusals=refusals,
            paragraph_traces=generation["paragraph_traces"],
            bundle_index=bundle_index,
        )
    )
    validation = _build_validation(
        context=context,
        checks=checks,
        sections=generation["sections"],
        refusal_entries=generation["refusals"],
        results_dir=resolved_results_dir,
    )
    manifest = _build_manifest(
        context=context,
        config=config,
        sections=generation["sections"],
        validation=validation,
        results_dir=resolved_results_dir,
    )
    markdown = _render_markdown(
        context=context,
        package=package,
        sections=generation["sections"],
        refusals=refusals,
    )
    return DraftGenerationBundle(
        package=package,
        markdown=markdown,
        manifest=manifest,
        traceability=traceability,
        refusals=refusals,
        defensibility_packet=defensibility_packet,
        validation=validation,
    )


def _write_bundle(*, bundle: DraftGenerationBundle, results_dir: Path) -> DraftGenerationResult:
    results_dir = Path(results_dir)
    package_path = results_dir / PACKAGE_FILENAME
    markdown_path = results_dir / MARKDOWN_FILENAME
    manifest_path = results_dir / MANIFEST_FILENAME
    traceability_path = results_dir / TRACEABILITY_FILENAME
    refusal_path = results_dir / REFUSAL_FILENAME
    defensibility_path = results_dir / DEFENSIBILITY_FILENAME
    validation_path = results_dir / VALIDATION_FILENAME
    results_dir.mkdir(parents=True, exist_ok=True)
    _write_json(package_path, bundle.package)
    markdown_path.write_text(bundle.markdown, encoding="utf-8")
    _write_json(manifest_path, bundle.manifest)
    _write_json(traceability_path, bundle.traceability)
    _write_json(refusal_path, bundle.refusals)
    _write_json(defensibility_path, bundle.defensibility_packet)
    _write_json(validation_path, bundle.validation)

    output_files = {
        "package": package_path,
        "markdown": markdown_path,
        "manifest": manifest_path,
        "traceability": traceability_path,
        "refusals": refusal_path,
        "defensibility_packet": defensibility_path,
        "validation": validation_path,
    }
    output_hashes = {
        f"{name}_sha256": _sha256_file(path)
        for name, path in output_files.items()
    }
    bundle.package["artifact_paths"] = {key: str(path) for key, path in output_files.items()}
    bundle.package["output_hashes"] = output_hashes
    bundle.manifest["output_files"] = {key: str(path) for key, path in output_files.items()}
    bundle.manifest["output_hashes"] = output_hashes
    bundle.validation["output_files"] = {key: str(path) for key, path in output_files.items()}
    bundle.validation["output_hashes"] = output_hashes
    bundle.defensibility_packet["output_hashes"] = output_hashes

    _write_json(package_path, bundle.package)
    _write_json(manifest_path, bundle.manifest)
    _write_json(validation_path, bundle.validation)
    _write_json(defensibility_path, bundle.defensibility_packet)
    return DraftGenerationResult(
        output_dir=results_dir,
        package_path=package_path,
        markdown_path=markdown_path,
        manifest_path=manifest_path,
        traceability_path=traceability_path,
        refusal_path=refusal_path,
        defensibility_path=defensibility_path,
        validation_path=validation_path,
        summary=_dict(bundle.validation.get("summary")),
    )


def _build_package(
    *,
    context: DraftGenerationContext,
    config: dict[str, Any],
    sections: list[dict[str, Any]],
    refusals: list[dict[str, Any]],
    results_dir: Path,
) -> dict[str, Any]:
    ready_sections = [
        section
        for section in sections
        if section.get("readiness_status") in {"ready", "ready_with_reviewer_warnings"}
    ]
    warning_sections = [section for section in ready_sections if section.get("warnings")]
    return {
        "schema_version": PACKAGE_SCHEMA_VERSION,
        "review_id": context.review_id,
        "source_set_id": context.source_set_id,
        "created_at": _utc_now(),
        "generator_version": str(config.get("generator_version") or GENERATOR_VERSION),
        "review_boundary": {
            "decision_use_caveat": str(config.get("human_review_caveat") or ""),
            "human_review_required": True,
            "legal_conclusion": False,
            "review_id": context.review_id,
            "source_set_id": context.source_set_id,
        },
        "section_order": [section["section_id"] for section in sections],
        "sections": sections,
        "refusal_path": str(results_dir / REFUSAL_FILENAME),
        "traceability_path": str(results_dir / TRACEABILITY_FILENAME),
        "defensibility_packet_path": str(results_dir / DEFENSIBILITY_FILENAME),
        "summary": {
            "ready_section_count": len(ready_sections),
            "warning_section_count": len(warning_sections),
            "refused_section_count": sum(section.get("readiness_status") == "refused" for section in sections),
            "refusal_count": len(refusals),
            "paragraph_count": sum(len(_dict_list(section.get("paragraphs"))) for section in ready_sections),
        },
    }


def _build_traceability(
    *,
    context: DraftGenerationContext,
    sections: list[dict[str, Any]],
    paragraph_traces: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": TRACEABILITY_SCHEMA_VERSION,
        "review_id": context.review_id,
        "source_set_id": context.source_set_id,
        "created_at": _utc_now(),
        "section_count": len(sections),
        "paragraph_traces": paragraph_traces,
        "summary": {
            "paragraph_trace_count": len(paragraph_traces),
            "warning_paragraph_count": sum(bool(row.get("warning_inserted")) for row in paragraph_traces),
            "paragraphs_missing_authority_family_ids": sum(
                not row.get("authority_family_ids") for row in paragraph_traces
            ),
        },
    }


def _build_refusals(
    *,
    context: DraftGenerationContext,
    refusal_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": REFUSAL_SCHEMA_VERSION,
        "review_id": context.review_id,
        "source_set_id": context.source_set_id,
        "created_at": _utc_now(),
        "refusals": refusal_entries,
        "summary": {
            "refusal_count": len(refusal_entries),
            "refusal_category_counts": dict(
                Counter(str(entry.get("category") or "") for entry in refusal_entries)
            ),
        },
    }


def _build_defensibility_packet(
    *,
    context: DraftGenerationContext,
    sections: list[dict[str, Any]],
    paragraph_traces: list[dict[str, Any]],
    refusals: list[dict[str, Any]],
) -> dict[str, Any]:
    traces_by_section: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for trace in paragraph_traces:
        traces_by_section[str(trace.get("section_id") or "")].append(trace)
    return {
        "schema_version": DEFENSIBILITY_SCHEMA_VERSION,
        "review_id": context.review_id,
        "source_set_id": context.source_set_id,
        "created_at": _utc_now(),
        "section_packets": [
            {
                "section_id": section["section_id"],
                "section_type": section["section_type"],
                "title": section["title"],
                "readiness_status": section["readiness_status"],
                "paragraph_count": len(_dict_list(section.get("paragraphs"))),
                "authority_family_ids": sorted(
                    {
                        family_id
                        for trace in traces_by_section.get(section["section_id"], [])
                        for family_id in trace.get("authority_family_ids", [])
                    }
                ),
                "rule_ids": sorted(
                    {
                        rule_id
                        for trace in traces_by_section.get(section["section_id"], [])
                        for rule_id in trace.get("rule_ids", [])
                    }
                ),
                "residual_risk_refs": sorted(
                    {
                        risk_id
                        for trace in traces_by_section.get(section["section_id"], [])
                        for risk_id in trace.get("residual_risk_refs", [])
                    }
                ),
                "unresolved_issue_refs": sorted(
                    {
                        ref
                        for trace in traces_by_section.get(section["section_id"], [])
                        for ref in trace.get("unresolved_issue_refs", [])
                    }
                ),
            }
            for section in sections
        ],
        "summary": {
            "passed": not refusals and all(
                section.get("readiness_status") in {"ready", "ready_with_reviewer_warnings"}
                for section in sections
            ),
            "refusal_count": len(refusals),
            "warning_section_count": sum(bool(section.get("warnings")) for section in sections),
        },
    }


def _build_manifest(
    *,
    context: DraftGenerationContext,
    config: dict[str, Any],
    sections: list[dict[str, Any]],
    validation: dict[str, Any],
    results_dir: Path,
) -> dict[str, Any]:
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "review_id": context.review_id,
        "source_set_id": context.source_set_id,
        "created_at": _utc_now(),
        "generator_version": str(config.get("generator_version") or GENERATOR_VERSION),
        "validation_passed": bool(_dict(validation.get("summary")).get("passed")),
        "config_path": str(context.config_path),
        "results_dir": str(results_dir),
        "input_artifacts": [
            {
                "artifact_key": artifact.key,
                "artifact_path": str(artifact.path),
                "required": artifact.required,
                "exists": artifact.exists,
                "parse_ok": artifact.parse_ok,
                "sha256": artifact.sha256,
                "semantic_sha256": _semantic_sha256_for_artifact(
                    artifact_key=artifact.key,
                    payload=artifact.payload,
                ),
            }
            for artifact in context.artifacts.values()
        ],
        "section_dependencies": [
            {
                "section_id": section["section_id"],
                "section_type": section["section_type"],
                "traceability_path": str(results_dir / TRACEABILITY_FILENAME),
                "refusal_path": str(results_dir / REFUSAL_FILENAME),
                "warning_count": len(section.get("warnings") or []),
            }
            for section in sections
        ],
    }


def _semantic_sha256_for_artifact(
    *,
    artifact_key: str,
    payload: dict[str, Any] | None,
) -> str | None:
    if artifact_key != "final_qa" or not isinstance(payload, dict):
        return None
    semantic_projection = {
        "decision_support_qa": {
            "legal_conclusion": _dict(payload.get("decision_support_qa")).get("legal_conclusion")
        },
        "accepted_v1_risk_ledger": {
            "policy_mode": _dict(payload.get("accepted_v1_risk_ledger")).get("policy_mode"),
            "accepted_pending_count": _dict(payload.get("accepted_v1_risk_ledger")).get("accepted_pending_count"),
            "actual_pending_count": _dict(payload.get("accepted_v1_risk_ledger")).get("actual_pending_count"),
            "actual_pending_applicable_count": _dict(payload.get("accepted_v1_risk_ledger")).get(
                "actual_pending_applicable_count"
            ),
            "risks": _dict(payload.get("accepted_v1_risk_ledger")).get("risks") or [],
        },
    }
    return hashlib.sha256(
        json.dumps(semantic_projection, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _build_validation(
    *,
    context: DraftGenerationContext,
    checks: list[dict[str, Any]],
    sections: list[dict[str, Any]],
    refusal_entries: list[dict[str, Any]],
    results_dir: Path,
) -> dict[str, Any]:
    passed = all(check["passed"] for check in checks) and not refusal_entries and all(
        section.get("readiness_status") in {"ready", "ready_with_reviewer_warnings"}
        for section in sections
    )
    failed_checks = [check for check in checks if not check["passed"]]
    failure_category_counts = Counter(str(check.get("failure_category") or "") for check in failed_checks)
    failure_category_counts.update(str(entry.get("category") or "") for entry in refusal_entries)
    return {
        "schema_version": VALIDATION_SCHEMA_VERSION,
        "review_id": context.review_id,
        "source_set_id": context.source_set_id,
        "created_at": _utc_now(),
        "checks": checks,
        "summary": {
            "passed": passed,
            "check_count": len(checks),
            "failed_check_count": len(failed_checks),
            "failure_category_counts": dict(sorted(failure_category_counts.items())),
            "ready_section_count": sum(
                section.get("readiness_status") in {"ready", "ready_with_reviewer_warnings"}
                for section in sections
            ),
            "refusal_count": len(refusal_entries),
            "results_dir": str(results_dir),
        },
    }


def _output_checks(
    *,
    context: DraftGenerationContext,
    config: dict[str, Any],
    package: dict[str, Any],
    traceability: dict[str, Any],
    refusals: dict[str, Any],
    paragraph_traces: list[dict[str, Any]],
    bundle_index: dict[str, Any],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    prohibited_phrases = [str(value).lower() for value in config.get("prohibited_phrases", [])]
    package_text = "\n".join(
        paragraph["text"]
        for section in _dict_list(package.get("sections"))
        for paragraph in _dict_list(section.get("paragraphs"))
    ).lower()
    for phrase in prohibited_phrases:
        checks.append(
            _check(
                f"prohibited_phrase_absent:{phrase}",
                phrase not in package_text,
                "unsupported_legal_conclusion",
                {"phrase": phrase},
            )
        )
    checks.append(
        _check(
            "traceability_paragraph_count_matches_package",
            len(paragraph_traces)
            == sum(
                len(_dict_list(section.get("paragraphs"))) for section in _dict_list(package.get("sections"))
            ),
            "contradictory_evidence",
            {
                "trace_count": len(paragraph_traces),
                "paragraph_count": sum(
                    len(_dict_list(section.get("paragraphs")))
                    for section in _dict_list(package.get("sections"))
                ),
            },
        )
    )
    unresolved_inputs = (
        _safe_len(_dict_list(bundle_index.get("implementation_confirmations")))
        + _safe_len(_dict_list(bundle_index.get("accepted_risks")))
        + _safe_len(_dict_list(bundle_index.get("pending_resolution_paths")))
        + _safe_len(_dict_list(bundle_index.get("reviewer_resolution_items")))
    )
    warning_count = sum(bool(trace.get("warning_inserted")) for trace in paragraph_traces)
    checks.append(
        _check(
            "reviewer_warning_inserted_for_unresolved_inputs",
            unresolved_inputs == 0 or warning_count > 0,
            "reviewer_warning_missing",
            {"unresolved_inputs": unresolved_inputs, "warning_count": warning_count},
        )
    )
    checks.append(
        _check(
            "all_ready_paragraphs_have_complete_citations",
            not any(trace.get("missing_evidence_refs") for trace in paragraph_traces),
            "missing_citation",
            {
                "paragraphs_missing_citations": [
                    trace["paragraph_id"]
                    for trace in paragraph_traces
                    if trace.get("missing_evidence_refs")
                ]
            },
        )
    )
    checks.append(
        _check(
            "all_refusals_have_messages",
            all(str(entry.get("message") or "").strip() for entry in _dict_list(refusals.get("refusals"))),
            "insufficient_evidence",
            {"refusal_count": _safe_len(_dict_list(refusals.get("refusals")))},
        )
    )
    checks.append(
        _check(
            "human_review_boundary_explicit",
            _dict(package.get("review_boundary")).get("human_review_required") is True
            and _dict(package.get("review_boundary")).get("legal_conclusion") is False,
            "human_boundary_missing",
            {"review_boundary": package.get("review_boundary")},
        )
    )
    checks.append(
        _check(
            "traceability_schema_version",
            traceability.get("schema_version") == TRACEABILITY_SCHEMA_VERSION,
            "contradictory_evidence",
            {"schema_version": traceability.get("schema_version")},
        )
    )
    return checks


def _render_markdown(
    *,
    context: DraftGenerationContext,
    package: dict[str, Any],
    sections: list[dict[str, Any]],
    refusals: dict[str, Any],
) -> str:
    lines = [
        "# Evidence-Backed Draft Support",
        "",
        _dict(package.get("review_boundary")).get("decision_use_caveat")
        or "This generated draft supports human review. It does not replace responsible-official, line-officer, counsel, or specialist judgment.",
        "",
        f"Review ID: `{context.review_id}`",
        f"Source Set ID: `{context.source_set_id}`",
        "",
    ]
    for section in sections:
        lines.append(f"## {section['title']}")
        lines.append("")
        lines.append(f"Status: `{section['readiness_status']}`")
        if section.get("warnings"):
            lines.append(f"Warnings: `{', '.join(section['warnings'])}`")
        lines.append("")
        if section.get("readiness_status") == "refused":
            lines.append(
                f"Generation refused: `{section.get('refusal_category')}` via `{section.get('refusal_id')}`."
            )
            lines.append("")
            continue
        for paragraph in _dict_list(section.get("paragraphs")):
            lines.append(paragraph["text"])
            if paragraph.get("citations"):
                lines.append(f"Citations: `{'; '.join(paragraph['citations'])}`")
            if paragraph.get("authority_family_ids"):
                lines.append(
                    f"Authority Families: `{'; '.join(paragraph['authority_family_ids'])}`"
                )
            lines.append("")
    refusal_rows = _dict_list(refusals.get("refusals"))
    if refusal_rows:
        lines.append("## Refusals")
        lines.append("")
        for row in refusal_rows:
            lines.append(
                f"- `{row['output_id']}`: `{row['category']}`. {row['message']}"
            )
    return "\n".join(lines).strip() + "\n"
