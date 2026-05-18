from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from .artifact_utils import _dict
from .artifact_utils import _dict_list
from .artifact_utils import _read_json
from .artifact_utils import _utc_now
from .artifact_utils import _write_json


DEFAULT_CONFIG_PATH = Path("config/draft_generation_v1.json")

PACKAGE_SCHEMA_VERSION = "draft-generation-package-v1"
MANIFEST_SCHEMA_VERSION = "draft-generation-manifest-v1"
TRACEABILITY_SCHEMA_VERSION = "draft-generation-traceability-v1"
REFUSAL_SCHEMA_VERSION = "draft-generation-refusals-v1"
DEFENSIBILITY_SCHEMA_VERSION = "draft-defensibility-packet-v1"
VALIDATION_SCHEMA_VERSION = "draft-generation-validation-v1"
GENERATOR_VERSION = "draft-generation-v1"

PACKAGE_FILENAME = "draft_generation_package.json"
MARKDOWN_FILENAME = "draft_generation.md"
MANIFEST_FILENAME = "draft_generation_manifest.json"
TRACEABILITY_FILENAME = "draft_generation_traceability.json"
REFUSAL_FILENAME = "draft_generation_refusals.json"
DEFENSIBILITY_FILENAME = "draft_defensibility_packet.json"
VALIDATION_FILENAME = "draft_generation_validation.json"

SUPPORTED_SECTION_TYPES = {
    "citation_bearing_issue_summary",
    "compliance_narrative",
    "authority_coverage_appendix",
    "environmental_consequences",
    "unresolved_issue_statement",
}
PROHIBITED_LEGAL_OUTPUT_TYPES = {
    "legal_sufficiency_determination",
    "record_of_decision",
    "line_officer_approval",
    "responsible_official_certification",
}


@dataclass(frozen=True)
class DraftGenerationResult:
    output_dir: Path
    package_path: Path
    markdown_path: Path
    manifest_path: Path
    traceability_path: Path
    refusal_path: Path
    defensibility_path: Path
    validation_path: Path
    summary: dict[str, Any]


@dataclass(frozen=True)
class DraftGenerationBundle:
    package: dict[str, Any]
    markdown: str
    manifest: dict[str, Any]
    traceability: dict[str, Any]
    refusals: dict[str, Any]
    defensibility_packet: dict[str, Any]
    validation: dict[str, Any]


@dataclass(frozen=True)
class _Artifact:
    key: str
    path: Path
    required: bool
    exists: bool
    parse_ok: bool
    payload: dict[str, Any] | None
    sha256: str | None
    error: str | None = None


@dataclass(frozen=True)
class DraftGenerationContext:
    output_dir: Path
    review_dir: Path
    review_id: str
    source_set_id: str
    config_path: Path
    config: dict[str, Any]
    artifacts: dict[str, _Artifact]

    def payload(self, key: str) -> dict[str, Any]:
        artifact = self.artifacts[key]
        return artifact.payload if isinstance(artifact.payload, dict) else {}


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
    return _write_bundle(bundle=bundle, results_dir=results_dir or context.review_dir / "draft_generation")


def load_draft_generation_context(
    *,
    output_dir: Path = Path("source_library"),
    review_id: str | None = None,
    config_path: Path = DEFAULT_CONFIG_PATH,
) -> DraftGenerationContext:
    output_dir = Path(output_dir)
    config_path = Path(config_path)
    config = _read_json(config_path)
    resolved_review_id = str(review_id or config.get("review_id") or "")
    if not resolved_review_id:
        raise ValueError("draft-generation config must declare review_id when --review-id is omitted")
    review_dir = output_dir / "reviews" / resolved_review_id
    artifacts = _load_artifacts(review_dir=review_dir)
    source_set_id = _resolve_source_set_id(config=config, artifacts=artifacts)
    return DraftGenerationContext(
        output_dir=output_dir,
        review_dir=review_dir,
        review_id=resolved_review_id,
        source_set_id=source_set_id,
        config_path=config_path,
        config=config,
        artifacts=artifacts,
    )


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


def _load_artifacts(*, review_dir: Path) -> dict[str, _Artifact]:
    specs = {
        "compliance_review": (review_dir / "compliance_review.json", True),
        "compliance_validation": (review_dir / "compliance_validation.json", True),
        "authority_explanation_paths": (review_dir / "authority_explanation_paths.json", True),
        "decision_support": (
            review_dir / "decision_support" / "ea_consistency_decision_support.json",
            True,
        ),
        "review_packet_index": (
            review_dir / "review_packet_index" / "review_packet_index.json",
            True,
        ),
        "non_applicable_authority_appendix": (
            review_dir / "non_applicable_authority_appendix.json",
            True,
        ),
        "litigation_risk_summary": (review_dir / "litigation_risk_summary.json", True),
        "authority_reviewer_resolution_report": (
            review_dir / "authority_reviewer_resolution_report.json",
            False,
        ),
        "final_qa": (
            review_dir / "final_qa" / "east_crazies_final_qa_certification.json",
            False,
        ),
    }
    return {
        key: _load_json_artifact(key=key, path=path, required=required)
        for key, (path, required) in specs.items()
    }


def _load_json_artifact(*, key: str, path: Path, required: bool) -> _Artifact:
    if not path.exists():
        return _Artifact(
            key=key,
            path=path,
            required=required,
            exists=False,
            parse_ok=False,
            payload=None,
            sha256=None,
            error=f"Missing artifact: {path}",
        )
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return _Artifact(
            key=key,
            path=path,
            required=required,
            exists=True,
            parse_ok=False,
            payload=None,
            sha256=digest,
            error=str(exc),
        )
    return _Artifact(
        key=key,
        path=path,
        required=required,
        exists=True,
        parse_ok=isinstance(payload, dict),
        payload=payload if isinstance(payload, dict) else None,
        sha256=digest,
        error=None if isinstance(payload, dict) else f"Artifact did not parse as JSON object: {path}",
    )


def _resolve_source_set_id(*, config: dict[str, Any], artifacts: dict[str, _Artifact]) -> str:
    if config.get("source_set_id"):
        return str(config["source_set_id"])
    for key in (
        "authority_explanation_paths",
        "decision_support",
        "final_qa",
        "review_packet_index",
    ):
        payload = artifacts[key].payload if artifacts[key].parse_ok else {}
        if isinstance(payload, dict) and payload.get("source_set_id"):
            return str(payload["source_set_id"])
    return ""


def _input_checks(*, context: DraftGenerationContext, config: dict[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    checks.append(
        _check(
            "draft_generation_config_schema",
            config.get("schema_version") == "draft-generation-config-v1",
            "stale_authority",
            {"actual": config.get("schema_version"), "expected": "draft-generation-config-v1"},
        )
    )
    checks.append(
        _check(
            "draft_generation_review_id_matches_config",
            context.review_id == str(config.get("review_id") or context.review_id),
            "review_source_set_mismatch",
            {"review_id": context.review_id, "config_review_id": config.get("review_id")},
        )
    )
    checks.append(
        _check(
            "draft_generation_source_set_matches_config",
            not config.get("source_set_id") or context.source_set_id == str(config.get("source_set_id")),
            "review_source_set_mismatch",
            {"source_set_id": context.source_set_id, "config_source_set_id": config.get("source_set_id")},
        )
    )
    for artifact in context.artifacts.values():
        checks.append(
            _check(
                f"{artifact.key}_exists",
                artifact.exists or not artifact.required,
                "missing_required_artifact",
                {"path": str(artifact.path), "required": artifact.required},
            )
        )
        if artifact.exists:
            checks.append(
                _check(
                    f"{artifact.key}_parses",
                    artifact.parse_ok,
                    "missing_required_artifact",
                    {"path": str(artifact.path), "error": artifact.error},
                )
            )
    for key in (
        "compliance_review",
        "authority_explanation_paths",
        "decision_support",
        "review_packet_index",
    ):
        payload = context.payload(key)
        if not payload:
            continue
        review_id = payload.get("review_id")
        if review_id is not None:
            checks.append(
                _check(
                    f"{key}_review_id_matches",
                    str(review_id) == context.review_id,
                    "review_source_set_mismatch",
                    {"artifact_review_id": review_id, "review_id": context.review_id},
                )
            )
        source_set_id = payload.get("source_set_id")
        if source_set_id is not None and context.source_set_id:
            checks.append(
                _check(
                    f"{key}_source_set_matches",
                    str(source_set_id) == context.source_set_id,
                    "review_source_set_mismatch",
                    {
                        "artifact_source_set_id": source_set_id,
                        "source_set_id": context.source_set_id,
                    },
                )
            )

    compliance_validation = context.payload("compliance_validation")
    checks.append(
        _check(
            "compliance_validation_passed",
            bool(compliance_validation.get("passed")),
            "stale_authority",
            {"path": str(context.artifacts["compliance_validation"].path), "passed": compliance_validation.get("passed")},
        )
    )
    authority_paths = context.payload("authority_explanation_paths")
    authority_summary = _dict(authority_paths.get("summary"))
    checks.append(
        _check(
            "authority_explanation_paths_validation_passed",
            bool(authority_summary.get("validation_passed")),
            "stale_authority",
            {
                "path": str(context.artifacts["authority_explanation_paths"].path),
                "validation_passed": authority_summary.get("validation_passed"),
            },
        )
    )
    decision_support = context.payload("decision_support")
    decision_validation = _dict(decision_support.get("validation_and_replay"))
    checks.append(
        _check(
            "decision_support_validation_passed",
            bool(decision_validation.get("passed")),
            "stale_authority",
            {
                "path": str(context.artifacts["decision_support"].path),
                "validation_passed": decision_validation.get("passed"),
            },
        )
    )
    executive = _dict(decision_support.get("executive_determination"))
    checks.append(
        _check(
            "decision_support_legal_conclusion_false",
            executive.get("legal_conclusion") is False,
            "unsupported_legal_conclusion",
            {"legal_conclusion": executive.get("legal_conclusion")},
        )
    )
    final_qa = context.payload("final_qa")
    if final_qa:
        checks.append(
            _check(
                "final_qa_legal_conclusion_false",
                _dict(final_qa.get("decision_support_qa")).get("legal_conclusion") is False,
                "unsupported_legal_conclusion",
                {"legal_conclusion": _dict(final_qa.get("decision_support_qa")).get("legal_conclusion")},
            )
        )
    return checks


def _build_finding_index(context: DraftGenerationContext) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    compliance_findings = {
        str(row.get("rule_id") or row.get("id") or ""): row
        for row in _dict_list(context.payload("compliance_review").get("findings"))
        if str(row.get("rule_id") or row.get("id") or "").strip()
    }
    explanation_rows = {
        str(row.get("finding_id") or row.get("rule_id") or ""): row
        for row in _dict_list(context.payload("authority_explanation_paths").get("finding_explanation_paths"))
        if str(row.get("finding_id") or row.get("rule_id") or "").strip()
    }
    packet_rows = {
        str(row.get("rule_id") or ""): row
        for row in _dict_list(context.payload("review_packet_index").get("applicable_authority_rows"))
        if str(row.get("rule_id") or "").strip()
    }
    decision_rows = {
        str(row.get("rule_id") or ""): row
        for row in _dict_list(context.payload("decision_support").get("authority_findings"))
        if str(row.get("rule_id") or "").strip()
    }
    bundles: dict[str, dict[str, Any]] = {}
    for rule_id, decision_row in decision_rows.items():
        compliance_row = compliance_findings.get(rule_id)
        explanation_row = explanation_rows.get(rule_id)
        packet_row = packet_rows.get(rule_id)
        checks.append(
            _check(
                f"{rule_id}_has_compliance_review_row",
                compliance_row is not None,
                "contradictory_evidence",
                {"rule_id": rule_id},
            )
        )
        checks.append(
            _check(
                f"{rule_id}_has_authority_explanation_row",
                explanation_row is not None,
                "contradictory_evidence",
                {"rule_id": rule_id},
            )
        )
        checks.append(
            _check(
                f"{rule_id}_has_review_packet_row",
                packet_row is not None,
                "contradictory_evidence",
                {"rule_id": rule_id},
            )
        )
        if compliance_row is None or explanation_row is None or packet_row is None:
            continue
        checks.extend(_bundle_consistency_checks(rule_id, compliance_row, explanation_row, decision_row, packet_row))
        bundles[rule_id] = {
            "rule_id": rule_id,
            "compliance": compliance_row,
            "explanation": explanation_row,
            "decision_support": decision_row,
            "packet": packet_row,
        }

    return {
        "checks": checks,
        "bundles": bundles,
        "land_exchange_rows": _dict_list(context.payload("review_packet_index").get("land_exchange_rows")),
        "non_applicable_boundary": _dict(
            context.payload("review_packet_index").get("non_applicable_authority_boundary")
        ),
        "implementation_confirmations": _dict_list(
            context.payload("decision_support").get("implementation_confirmation_checklist")
        ),
        "residual_risks": _dict_list(context.payload("decision_support").get("residual_risk_register")),
        "accepted_risks": _dict_list(
            _dict(context.payload("final_qa").get("accepted_v1_risk_ledger")).get("risks")
        ),
        "pending_resolution_paths": _dict_list(
            context.payload("authority_explanation_paths").get("pending_resolution_paths")
        ),
        "reviewer_resolution_items": _dict_list(
            context.payload("authority_reviewer_resolution_report").get("pending_resolution_items")
        ),
        "non_applicable_rows": _dict_list(
            context.payload("non_applicable_authority_appendix").get("authorities")
        ),
    }


def _bundle_consistency_checks(
    rule_id: str,
    compliance_row: dict[str, Any],
    explanation_row: dict[str, Any],
    decision_row: dict[str, Any],
    packet_row: dict[str, Any],
) -> list[dict[str, Any]]:
    checks = []
    checks.append(
        _check(
            f"{rule_id}_compliance_status_consistent",
            str(compliance_row.get("status") or "") == str(decision_row.get("compliance_status") or "")
            == str(packet_row.get("compliance_status") or ""),
            "contradictory_evidence",
            {
                "compliance_review": compliance_row.get("status"),
                "decision_support": decision_row.get("compliance_status"),
                "review_packet": packet_row.get("compliance_status"),
            },
        )
    )
    checks.append(
        _check(
            f"{rule_id}_applicability_status_consistent",
            str(compliance_row.get("applicability_status") or "") == str(decision_row.get("applicability_status") or "")
            == str(packet_row.get("applicability_status") or "")
            == str(explanation_row.get("applicability_status") or ""),
            "contradictory_evidence",
            {
                "compliance_review": compliance_row.get("applicability_status"),
                "decision_support": decision_row.get("applicability_status"),
                "review_packet": packet_row.get("applicability_status"),
                "authority_explanation": explanation_row.get("applicability_status"),
            },
        )
    )
    checks.append(
        _check(
            f"{rule_id}_authority_source_consistent",
            str(compliance_row.get("authority_source_record_id") or "")
            == str(decision_row.get("authority_source_record_id") or "")
            == str(packet_row.get("authority_source_record_id") or "")
            == str(explanation_row.get("authority_source_record_id") or ""),
            "contradictory_evidence",
            {
                "compliance_review": compliance_row.get("authority_source_record_id"),
                "decision_support": decision_row.get("authority_source_record_id"),
                "review_packet": packet_row.get("authority_source_record_id"),
                "authority_explanation": explanation_row.get("authority_source_record_id"),
            },
        )
    )
    return checks


def _generate_sections(
    *,
    context: DraftGenerationContext,
    config: dict[str, Any],
    bundle_index: dict[str, Any],
    requested_output_ids: list[str] | None,
) -> dict[str, Any]:
    profiles = {
        str(profile.get("output_id") or ""): profile
        for profile in _dict_list(config.get("section_profiles"))
        if str(profile.get("output_id") or "").strip()
    }
    configured_ids = [str(item) for item in config.get("section_order", []) if str(item).strip()]
    requested = requested_output_ids or configured_ids
    sections: list[dict[str, Any]] = []
    paragraph_traces: list[dict[str, Any]] = []
    refusals: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []

    for output_id in requested:
        profile = _dict(profiles.get(output_id))
        if not profile:
            refusals.append(
                _refusal(
                    context=context,
                    output_id=output_id,
                    category="unsupported_legal_conclusion"
                    if output_id in PROHIBITED_LEGAL_OUTPUT_TYPES
                    else "insufficient_evidence",
                    message=f"Requested output '{output_id}' is not a governed draft-generation surface.",
                )
            )
            continue
        section_type = str(profile.get("section_type") or "")
        if section_type not in SUPPORTED_SECTION_TYPES or output_id in PROHIBITED_LEGAL_OUTPUT_TYPES:
            refusals.append(
                _refusal(
                    context=context,
                    output_id=output_id,
                    category="unsupported_legal_conclusion",
                    message=f"Requested section '{output_id}' is outside the governed draft boundary.",
                )
            )
            continue
        generator = {
            "citation_bearing_issue_summary": _issue_summary_section,
            "compliance_narrative": _compliance_narrative_section,
            "authority_coverage_appendix": _authority_coverage_appendix_section,
            "environmental_consequences": _environmental_consequences_section,
            "unresolved_issue_statement": _unresolved_issue_statements_section,
        }[section_type]
        generated = generator(
            context=context,
            profile=profile,
            bundle_index=bundle_index,
        )
        checks.extend(generated["checks"])
        sections.append(generated["section"])
        paragraph_traces.extend(generated["paragraph_traces"])
        refusals.extend(generated["refusals"])

    return {
        "sections": sections,
        "paragraph_traces": paragraph_traces,
        "refusals": refusals,
        "checks": checks,
    }


def _issue_summary_section(
    *,
    context: DraftGenerationContext,
    profile: dict[str, Any],
    bundle_index: dict[str, Any],
) -> dict[str, Any]:
    bundles = _dict(bundle_index.get("bundles"))
    confirmations = _dict_list(bundle_index.get("implementation_confirmations"))
    accepted_risks = _dict_list(bundle_index.get("accepted_risks"))
    refusals: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []

    paragraphs = []

    summary_bundles = [
        bundle
        for rule_id, bundle in bundles.items()
        if rule_id.startswith("land_exchange_") or rule_id.startswith("flpma_")
    ]
    if not summary_bundles:
        summary_bundles = list(bundles.values())[:3]
    counts = {
        "applicable": len(bundles),
        "non_applicable": _safe_len(_dict_list(_dict(bundle_index.get("non_applicable_boundary")).get("rows"))),
        "confirmations": len(confirmations),
        "accepted_risks": len(accepted_risks),
    }
    paragraphs.append(
        _paragraph(
            section_id=str(profile["output_id"]),
            ordinal=1,
            text=(
                "This draft is limited to reviewed, citation-bearing evidence. "
                f"The current record carries {counts['applicable']} applicable authority findings, "
                f"{counts['non_applicable']} documented non-applicable authority rows, "
                f"{counts['confirmations']} implementation confirmations, and "
                f"{counts['accepted_risks']} accepted pending authority questions that must stay visible to reviewers."
            ),
            trace_seed=_trace_seed_from_bundles(
                context=context,
                bundles=summary_bundles,
            ),
            warning=True,
        )
    )
    if confirmations:
        confirmation = confirmations[0]
        related = _bundles_for_confirmation(confirmations=[confirmation], bundles=bundles)
        paragraphs.append(
            _paragraph(
                section_id=str(profile["output_id"]),
                ordinal=2,
                text=(
                    "Reviewer warning: implementation-dependent language must remain conditional. "
                    f"{confirmation.get('label') or 'Tracked implementation confirmation'} is still recorded as "
                    f"{confirmation.get('status') or 'requires_confirmation'}, so the draft can describe the planned control "
                    "but must not imply that the underlying instrument is already final."
                ),
                trace_seed=_trace_seed_from_confirmation(
                    context=context,
                    confirmation=confirmation,
                    bundles=related,
                ),
                warning=True,
            )
        )
    if accepted_risks:
        sample = accepted_risks[0]
        matched_bundle = bundles.get(str(sample.get("rule_id") or ""))
        paragraphs.append(
            _paragraph(
                section_id=str(profile["output_id"]),
                ordinal=3,
                text=(
                    "Reviewer warning: accepted pending authority items remain part of the defensibility boundary. "
                    f"The current packet still tracks {len(accepted_risks)} accepted pending items, including "
                    f"{sample.get('rule_id') or 'a pending authority question'}, and their rationale must stay visible "
                    "where the draft references that authority family."
                ),
                trace_seed=_trace_seed_from_accepted_risk(
                    context=context,
                    risk=sample,
                    bundle=matched_bundle,
                ),
                warning=True,
            )
        )
    section, section_checks = _section_payload(
        context=context,
        profile=profile,
        paragraphs=paragraphs,
        warnings=["reviewer_attention_required"] if paragraphs else [],
    )
    checks.extend(section_checks)
    return {
        "section": section,
        "paragraph_traces": [paragraph["_trace"] for paragraph in paragraphs],
        "refusals": refusals,
        "checks": checks,
    }


def _compliance_narrative_section(
    *,
    context: DraftGenerationContext,
    profile: dict[str, Any],
    bundle_index: dict[str, Any],
) -> dict[str, Any]:
    bundles = list(_dict(bundle_index.get("bundles")).values())
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for bundle in bundles:
        category = str(bundle["decision_support"].get("authority_category") or "authority")
        by_category[category].append(bundle)
    ordered_categories = sorted(by_category, key=lambda item: (-len(by_category[item]), item))
    paragraphs = [
        _paragraph(
            section_id=str(profile["output_id"]),
            ordinal=1,
            text=(
                "The compliance narrative below is limited to audited authority findings that carry both package evidence "
                "and supporting source-library authority. It supports reviewer drafting but does not state legal sufficiency "
                "or final agency approval."
            ),
            trace_seed=_trace_seed_from_bundles(context=context, bundles=bundles[:3]),
        )
    ]
    for ordinal, category in enumerate(ordered_categories, start=2):
        group = by_category[category]
        titles = [str(bundle["decision_support"].get("rule_title") or bundle["rule_id"]) for bundle in group[:3]]
        paragraphs.append(
            _paragraph(
                section_id=str(profile["output_id"]),
                ordinal=ordinal,
                text=(
                    f"The reviewed record contains {len(group)} applicable {category.replace('_', ' ')} findings. "
                    f"Representative governed authorities include {', '.join(titles)}. "
                    "Those findings remain anchored to paired package and source-library evidence and should be drafted as "
                    "review-supported narrative rather than as independent legal conclusions."
                ),
                trace_seed=_trace_seed_from_bundles(context=context, bundles=group),
            )
        )
    section, checks = _section_payload(
        context=context,
        profile=profile,
        paragraphs=paragraphs,
        warnings=[],
    )
    return {
        "section": section,
        "paragraph_traces": [paragraph["_trace"] for paragraph in paragraphs],
        "refusals": [],
        "checks": checks,
    }


def _authority_coverage_appendix_section(
    *,
    context: DraftGenerationContext,
    profile: dict[str, Any],
    bundle_index: dict[str, Any],
) -> dict[str, Any]:
    bundles = list(_dict(bundle_index.get("bundles")).values())
    by_category = Counter(
        str(bundle["decision_support"].get("authority_category") or "authority")
        for bundle in bundles
    )
    non_applicable_boundary = _dict(bundle_index.get("non_applicable_boundary"))
    review_packet = context.payload("review_packet_index")
    summary = _dict(review_packet.get("row_inventory_summary"))
    paragraphs = []
    representative = bundles[:4]
    paragraphs.append(
        _paragraph(
            section_id=str(profile["output_id"]),
            ordinal=1,
            text=(
                "Applicable authority coverage remains explicitly partitioned by category and traceable back to reviewed findings. "
                f"The current draft package covers {len(bundles)} applicable authorities across "
                + ", ".join(
                    f"{count} {category.replace('_', ' ')}"
                    for category, count in sorted(by_category.items())
                )
                + "."
            ),
            trace_seed=_trace_seed_from_bundles(context=context, bundles=representative),
        )
    )
    paragraphs.append(
        _paragraph(
            section_id=str(profile["output_id"]),
            ordinal=2,
            text=(
                "The non-applicable authority boundary remains first class rather than implied by omission. "
                f"The appendix still carries {non_applicable_boundary.get('non_applicable_authority_count') or 0} non-applicable rows "
                f"with {non_applicable_boundary.get('coverage_certificate_count') or 0} search-coverage certificates, and those rows "
                "must stay outside ready compliance narrative unless reviewer adjudication changes the boundary."
            ),
            trace_seed=_trace_seed_from_non_applicable_boundary(
                context=context,
                boundary=non_applicable_boundary,
                representative_rows=_dict_list(non_applicable_boundary.get("rows"))[:3],
            ),
            warning=True,
        )
    )
    paragraphs.append(
        _paragraph(
            section_id=str(profile["output_id"]),
            ordinal=3,
            text=(
                "Forest-plan context remains visible in the appendix boundary. "
                f"The packet currently tracks {summary.get('forest_plan_component_row_count') or 0} applicable forest-plan component rows "
                f"and {summary.get('applicable_standard_count') or 0} applicable standards alongside the authority coverage ledger."
            ),
            trace_seed=_trace_seed_from_bundles(context=context, bundles=representative),
        )
    )
    section, checks = _section_payload(
        context=context,
        profile=profile,
        paragraphs=paragraphs,
        warnings=["non_applicable_boundary_visible"],
    )
    return {
        "section": section,
        "paragraph_traces": [paragraph["_trace"] for paragraph in paragraphs],
        "refusals": [],
        "checks": checks,
    }


def _environmental_consequences_section(
    *,
    context: DraftGenerationContext,
    profile: dict[str, Any],
    bundle_index: dict[str, Any],
) -> dict[str, Any]:
    bundle_map = _dict(bundle_index.get("bundles"))
    rule_ids = [str(value) for value in profile.get("rule_ids", []) if str(value).strip()]
    selected = [bundle_map[rule_id] for rule_id in rule_ids if rule_id in bundle_map]
    minimum_findings = int(profile.get("minimum_findings") or 1)
    if len(selected) < minimum_findings:
        refusal = _refusal(
            context=context,
            output_id=str(profile["output_id"]),
            category="insufficient_evidence",
            message=(
                f"Section '{profile.get('title')}' requires at least {minimum_findings} traced findings "
                f"but only found {len(selected)}."
            ),
        )
        section = _refused_section(profile=profile, refusal=refusal)
        return {"section": section, "paragraph_traces": [], "refusals": [refusal], "checks": []}
    paragraphs = []
    for ordinal, bundle in enumerate(selected, start=1):
        rule_title = str(bundle["decision_support"].get("rule_title") or bundle["rule_id"])
        rationale = str(bundle["decision_support"].get("rationale") or "The reviewed finding remains evidence-backed.")
        warning_text = ""
        accepted_risk = _accepted_risk_for_rule(bundle_index=bundle_index, rule_id=bundle["rule_id"])
        if accepted_risk is not None:
            warning_text = (
                " Reviewer warning: this topic remains in the accepted-pending ledger and should be drafted as a governed "
                "review question rather than as a closed legal conclusion."
            )
        paragraphs.append(
            _paragraph(
                section_id=str(profile["output_id"]),
                ordinal=ordinal,
                text=(
                    f"{rule_title} remains part of the reviewed environmental-consequences record. {rationale}"
                    f"{warning_text}"
                ),
                trace_seed=_trace_seed_from_bundles(context=context, bundles=[bundle]),
                warning=bool(warning_text),
            )
        )
    section, checks = _section_payload(
        context=context,
        profile=profile,
        paragraphs=paragraphs,
        warnings=["accepted_pending_environmental_issue"] if any(
            _accepted_risk_for_rule(bundle_index=bundle_index, rule_id=bundle["rule_id"]) is not None
            for bundle in selected
        ) else [],
    )
    return {
        "section": section,
        "paragraph_traces": [paragraph["_trace"] for paragraph in paragraphs],
        "refusals": [],
        "checks": checks,
    }


def _unresolved_issue_statements_section(
    *,
    context: DraftGenerationContext,
    profile: dict[str, Any],
    bundle_index: dict[str, Any],
) -> dict[str, Any]:
    bundle_map = _dict(bundle_index.get("bundles"))
    confirmations = _dict_list(bundle_index.get("implementation_confirmations"))
    accepted_risks = _dict_list(bundle_index.get("accepted_risks"))
    pending_paths = _dict_list(bundle_index.get("pending_resolution_paths"))
    reviewer_resolution_items = _dict_list(bundle_index.get("reviewer_resolution_items"))

    paragraphs = []
    ordinal = 1
    for confirmation in confirmations:
        if str(confirmation.get("status") or "") == "confirmed":
            continue
        related_bundles = _bundles_for_confirmation(confirmations=[confirmation], bundles=bundle_map)
        paragraphs.append(
            _paragraph(
                section_id=str(profile["output_id"]),
                ordinal=ordinal,
                text=(
                    "Reviewer warning: "
                    f"{confirmation.get('label') or 'Implementation confirmation'} is still "
                    f"{confirmation.get('status') or 'requires_confirmation'}. "
                    "Draft language may describe the planned control, but it must keep the confirmation boundary explicit."
                ),
                trace_seed=_trace_seed_from_confirmation(
                    context=context,
                    confirmation=confirmation,
                    bundles=related_bundles,
                ),
                warning=True,
            )
        )
        ordinal += 1
    for risk in accepted_risks:
        paragraphs.append(
            _paragraph(
                section_id=str(profile["output_id"]),
                ordinal=ordinal,
                text=(
                    "Reviewer warning: "
                    f"{risk.get('rule_id') or 'accepted pending authority item'} remains in the accepted V1 risk ledger. "
                    f"{risk.get('classification_rationale') or 'Reviewer adjudication is still required before the issue can be closed.'}"
                ),
                trace_seed=_trace_seed_from_accepted_risk(
                    context=context,
                    risk=risk,
                    bundle=bundle_map.get(str(risk.get("rule_id") or "")),
                ),
                warning=True,
            )
        )
        ordinal += 1
    for row in pending_paths + reviewer_resolution_items:
        paragraphs.append(
            _paragraph(
                section_id=str(profile["output_id"]),
                ordinal=ordinal,
                text=(
                    "Reviewer warning: unresolved authority review remains open. "
                    f"{row.get('explanation_summary') or row.get('rationale') or 'Pending resolution evidence must be adjudicated before the issue can be treated as closed.'}"
                ),
                trace_seed=_trace_seed_from_pending_resolution(context=context, row=row),
                warning=True,
            )
        )
        ordinal += 1
    if not paragraphs:
        paragraphs.append(
            _paragraph(
                section_id=str(profile["output_id"]),
                ordinal=1,
                text=(
                    "No unresolved reviewer warnings are currently tracked in the reviewed authority packet. "
                    "This absence does not remove the human-review boundary for the generated draft."
                ),
                trace_seed=_trace_seed_from_bundles(
                    context=context,
                    bundles=list(bundle_map.values())[:1],
                ),
            )
        )
    section, checks = _section_payload(
        context=context,
        profile=profile,
        paragraphs=paragraphs,
        warnings=["reviewer_warning_inserted"],
    )
    return {
        "section": section,
        "paragraph_traces": [paragraph["_trace"] for paragraph in paragraphs],
        "refusals": [],
        "checks": checks,
    }


def _section_payload(
    *,
    context: DraftGenerationContext,
    profile: dict[str, Any],
    paragraphs: list[dict[str, Any]],
    warnings: list[str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    section_checks = []
    readiness_status = "ready_with_reviewer_warnings" if warnings else "ready"
    section = {
        "section_id": str(profile.get("output_id") or ""),
        "section_type": str(profile.get("section_type") or ""),
        "title": str(profile.get("title") or ""),
        "readiness_status": readiness_status,
        "human_review_required": True,
        "legal_conclusion": False,
        "warnings": sorted(set(warnings)),
        "paragraphs": [_public_paragraph(paragraph) for paragraph in paragraphs],
        "supporting_authority_family_ids": sorted(
            {
                family_id
                for paragraph in paragraphs
                for family_id in paragraph["_trace"].get("authority_family_ids", [])
            }
        ),
        "supporting_rule_ids": sorted(
            {
                rule_id
                for paragraph in paragraphs
                for rule_id in paragraph["_trace"].get("rule_ids", [])
            }
        ),
        "traceability_path": str(context.review_dir / "draft_generation" / TRACEABILITY_FILENAME),
    }
    for paragraph in paragraphs:
        section_checks.append(
            _check(
                f"{section['section_id']}:{paragraph['paragraph_id']}:has_citations",
                bool(paragraph["citations"]),
                "missing_citation",
                {"paragraph_id": paragraph["paragraph_id"], "citations": paragraph["citations"]},
            )
        )
        section_checks.append(
            _check(
                f"{section['section_id']}:{paragraph['paragraph_id']}:human_boundary",
                "This generated draft" not in paragraph["text"],
                "human_boundary_missing",
                {"paragraph_id": paragraph["paragraph_id"]},
            )
        )
    return section, section_checks


def _refused_section(*, profile: dict[str, Any], refusal: dict[str, Any]) -> dict[str, Any]:
    return {
        "section_id": str(profile.get("output_id") or ""),
        "section_type": str(profile.get("section_type") or ""),
        "title": str(profile.get("title") or ""),
        "readiness_status": "refused",
        "human_review_required": True,
        "legal_conclusion": False,
        "warnings": ["generation_refused"],
        "paragraphs": [],
        "refusal_id": refusal["refusal_id"],
        "refusal_category": refusal["category"],
    }


def _paragraph(
    *,
    section_id: str,
    ordinal: int,
    text: str,
    trace_seed: dict[str, Any],
    warning: bool = False,
) -> dict[str, Any]:
    citations = _citation_labels(trace_seed)
    paragraph_id = f"{section_id}:paragraph:{ordinal}"
    trace = {
        "paragraph_id": paragraph_id,
        "section_id": section_id,
        "source_passages": _dedupe_dict_rows(trace_seed.get("source_passages", [])),
        "authority_family_ids": sorted(set(trace_seed.get("authority_family_ids", []))),
        "graph_path_ids": sorted(set(trace_seed.get("graph_path_ids", []))),
        "retrieval_trace_ids": sorted(set(trace_seed.get("retrieval_trace_ids", []))),
        "review_decision_refs": _dedupe_dict_rows(trace_seed.get("review_decision_refs", [])),
        "unresolved_issue_refs": sorted(set(trace_seed.get("unresolved_issue_refs", []))),
        "missing_evidence_refs": sorted(set(trace_seed.get("missing_evidence_refs", []))),
        "residual_risk_refs": sorted(set(trace_seed.get("residual_risk_refs", []))),
        "rule_ids": sorted(set(trace_seed.get("rule_ids", []))),
        "warning_inserted": warning,
    }
    return {
        "paragraph_id": paragraph_id,
        "text": text,
        "citations": citations,
        "source_record_ids": sorted(
            {
                str(row.get("source_record_id") or "")
                for row in trace["source_passages"]
                if str(row.get("source_record_id") or "").strip()
            }
        ),
        "authority_family_ids": trace["authority_family_ids"],
        "warning_inserted": warning,
        "_trace": trace,
    }


def _public_paragraph(paragraph: dict[str, Any]) -> dict[str, Any]:
    return {
        "paragraph_id": paragraph["paragraph_id"],
        "text": paragraph["text"],
        "citations": paragraph["citations"],
        "source_record_ids": paragraph["source_record_ids"],
        "authority_family_ids": paragraph["authority_family_ids"],
        "warning_inserted": paragraph["warning_inserted"],
    }


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
            "legal_conclusion": _dict(payload.get("decision_support_qa")).get(
                "legal_conclusion"
            )
        },
        "accepted_v1_risk_ledger": {
            "policy_mode": _dict(payload.get("accepted_v1_risk_ledger")).get("policy_mode"),
            "accepted_pending_count": _dict(payload.get("accepted_v1_risk_ledger")).get(
                "accepted_pending_count"
            ),
            "actual_pending_count": _dict(payload.get("accepted_v1_risk_ledger")).get(
                "actual_pending_count"
            ),
            "actual_pending_applicable_count": _dict(
                payload.get("accepted_v1_risk_ledger")
            ).get("actual_pending_applicable_count"),
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
        section.get("readiness_status") in {"ready", "ready_with_reviewer_warnings"} for section in sections
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


def _trace_seed_from_bundles(
    *,
    context: DraftGenerationContext,
    bundles: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    source_passages = []
    authority_family_ids: list[str] = []
    graph_path_ids: list[str] = []
    retrieval_trace_ids: list[str] = []
    review_decision_refs: list[dict[str, Any]] = []
    unresolved_issue_refs: list[str] = []
    missing_evidence_refs: list[str] = []
    residual_risk_refs: list[str] = []
    rule_ids: list[str] = []
    for bundle in bundles:
        decision_row = _dict(bundle.get("decision_support"))
        explanation = _dict(bundle.get("explanation"))
        packet = _dict(bundle.get("packet"))
        rule_id = str(bundle.get("rule_id") or "")
        if rule_id:
            rule_ids.append(rule_id)
        package_evidence = _dict_list(decision_row.get("ea_package_evidence"))
        source_evidence = _dict_list(decision_row.get("source_library_evidence"))
        source_passages.extend(package_evidence)
        source_passages.extend(source_evidence)
        authority_family_ids.extend(_string_list(decision_row.get("authority_family_ids")))
        authority_family_ids.extend(_string_list(explanation.get("authority_family_ids")))
        graph_path_ids.extend(_string_list(explanation.get("graph_path_ids")))
        retrieval_trace_ids.extend(_string_list(explanation.get("retrieval_trace_ids")))
        unresolved_issue_refs.extend(_string_list(explanation.get("unresolved_issue_refs")))
        residual_risk_refs.extend(_string_list(explanation.get("residual_risk_categories")))
        missing_evidence_refs.extend(
            _missing_citation_refs(
                evidence_rows=package_evidence,
                rule_id=rule_id,
                evidence_kind="package",
            )
        )
        missing_evidence_refs.extend(
            _missing_citation_refs(
                evidence_rows=source_evidence,
                rule_id=rule_id,
                evidence_kind="source_library",
            )
        )
        review_decision_refs.extend(
            [
                {
                    "artifact_path": str(context.review_dir / "compliance_review.json"),
                    "selector": f"findings[rule_id={rule_id}]",
                },
                {
                    "artifact_path": str(context.review_dir / "authority_explanation_paths.json"),
                    "selector": f"finding_explanation_paths[finding_id={rule_id}]",
                },
                {
                    "artifact_path": str(context.review_dir / "decision_support" / "ea_consistency_decision_support.json"),
                    "selector": f"authority_findings[rule_id={rule_id}]",
                },
            ]
        )
        review_decision_refs.extend(_dict_list(packet.get("canonical_selectors")))
    return {
        "source_passages": source_passages,
        "authority_family_ids": authority_family_ids,
        "graph_path_ids": graph_path_ids,
        "retrieval_trace_ids": retrieval_trace_ids,
        "review_decision_refs": review_decision_refs,
        "unresolved_issue_refs": unresolved_issue_refs,
        "missing_evidence_refs": missing_evidence_refs,
        "residual_risk_refs": residual_risk_refs,
        "rule_ids": rule_ids,
    }


def _trace_seed_from_confirmation(
    *,
    context: DraftGenerationContext,
    confirmation: dict[str, Any],
    bundles: list[dict[str, Any]],
) -> dict[str, Any]:
    seed = _trace_seed_from_bundles(context=context, bundles=bundles)
    evidence_rows = _dict_list(confirmation.get("evidence"))
    seed["source_passages"].extend(evidence_rows)
    seed["review_decision_refs"].extend(_dict_list(confirmation.get("source_selectors")))
    seed["review_decision_refs"].extend(
        {
            "artifact_path": str(context.review_dir / "decision_support" / "ea_consistency_decision_support.json"),
            "selector": f"implementation_confirmation_checklist[confirmation_id={confirmation.get('confirmation_id')}]",
        }
        for _ in [0]
    )
    seed["unresolved_issue_refs"].append(str(confirmation.get("confirmation_id") or ""))
    seed["missing_evidence_refs"].extend(
        _missing_citation_refs(
            evidence_rows=evidence_rows,
            rule_id=str(confirmation.get("confirmation_id") or "confirmation"),
            evidence_kind="implementation_confirmation",
        )
    )
    return seed


def _trace_seed_from_accepted_risk(
    *,
    context: DraftGenerationContext,
    risk: dict[str, Any],
    bundle: dict[str, Any] | None,
) -> dict[str, Any]:
    seed = _trace_seed_from_bundles(context=context, bundles=[bundle] if bundle else [])
    if not bundle:
        for source_record_id in _string_list(risk.get("source_record_ids")):
            seed["source_passages"].append(
                {
                    "source_record_id": source_record_id,
                    "citation_label": source_record_id,
                }
            )
    seed["review_decision_refs"].append(
        {
            "artifact_path": str(context.review_dir / "final_qa" / "east_crazies_final_qa_certification.json"),
            "selector": f"accepted_v1_risk_ledger.risks[rule_id={risk.get('rule_id')}]",
        }
    )
    seed["residual_risk_refs"].append(f"accepted-risk:{risk.get('rule_id')}")
    seed["unresolved_issue_refs"].append(str(risk.get("rule_id") or ""))
    return seed


def _trace_seed_from_pending_resolution(
    *,
    context: DraftGenerationContext,
    row: dict[str, Any],
) -> dict[str, Any]:
    return {
        "source_passages": [
            {
                "source_record_id": source_record_id,
                "citation_label": source_record_id,
            }
            for source_record_id in _string_list(row.get("source_record_ids"))
        ],
        "authority_family_ids": _string_list(row.get("authority_family_ids")),
        "graph_path_ids": _string_list(row.get("graph_path_ids")),
        "retrieval_trace_ids": _string_list(row.get("retrieval_trace_ids")),
        "review_decision_refs": [
            {
                "artifact_path": str(context.review_dir / "authority_explanation_paths.json"),
                "selector": "pending_resolution_paths",
            }
        ],
        "unresolved_issue_refs": [str(row.get("decision_id") or row.get("authority_explanation_id") or "pending-resolution")],
        "missing_evidence_refs": [],
        "residual_risk_refs": _string_list(row.get("residual_risk_categories")),
        "rule_ids": [str(row.get("rule_id") or "")] if row.get("rule_id") else [],
    }


def _trace_seed_from_non_applicable_boundary(
    *,
    context: DraftGenerationContext,
    boundary: dict[str, Any],
    representative_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    refs = [
        {
            "artifact_path": str(context.review_dir / "review_packet_index" / "review_packet_index.json"),
            "selector": "non_applicable_authority_boundary",
        },
        {
            "artifact_path": str(context.review_dir / "non_applicable_authority_appendix.json"),
            "selector": "authorities",
        },
    ]
    source_passages = [
        {
            "source_record_id": source_record_id,
            "citation_label": source_record_id,
        }
        for row in representative_rows
        for source_record_id in _string_list(row.get("source_record_ids"))
    ]
    return {
        "source_passages": source_passages,
        "authority_family_ids": [
            family_id
            for row in representative_rows
            for family_id in _string_list(row.get("authority_family_ids"))
        ],
        "graph_path_ids": [],
        "retrieval_trace_ids": [],
        "review_decision_refs": refs,
        "unresolved_issue_refs": [],
        "missing_evidence_refs": [],
        "residual_risk_refs": ["non_applicable_authority_boundary"]
        if boundary.get("non_applicable_authority_count")
        else [],
        "rule_ids": [],
    }


def _bundles_for_confirmation(
    *,
    confirmations: list[dict[str, Any]],
    bundles: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    confirmation_ids = {
        str(row.get("confirmation_id") or "")
        for row in confirmations
        if str(row.get("confirmation_id") or "").strip()
    }
    return [
        bundle
        for bundle in bundles.values()
        if confirmation_ids.intersection(
            _string_list(_dict(bundle.get("decision_support")).get("implementation_confirmation_ids"))
        )
    ]


def _accepted_risk_for_rule(*, bundle_index: dict[str, Any], rule_id: str) -> dict[str, Any] | None:
    for row in _dict_list(bundle_index.get("accepted_risks")):
        if str(row.get("rule_id") or "") == rule_id:
            return row
    return None


def _citation_labels(trace_seed: dict[str, Any]) -> list[str]:
    labels = []
    for row in _dict_list(trace_seed.get("source_passages")):
        label = ""
        if row.get("citation_label"):
            label = str(row.get("citation_label") or "").strip()
        elif "artifact_sha256" not in row and row.get("source_record_id"):
            label = str(row.get("source_record_id") or "").strip()
        if label:
            labels.append(label)
    return sorted(dict.fromkeys(labels))


def _refusal(
    *,
    context: DraftGenerationContext,
    output_id: str,
    category: str,
    message: str,
) -> dict[str, Any]:
    return {
        "refusal_id": f"refusal:{output_id}:{category}",
        "output_id": output_id,
        "category": category,
        "message": message,
        "review_id": context.review_id,
        "source_set_id": context.source_set_id,
    }


def _check(name: str, passed: bool, failure_category: str, details: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": name,
        "passed": passed,
        "failure_category": failure_category,
        "details": details,
    }


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _safe_len(value: Any) -> int:
    return len(value) if isinstance(value, list) else 0


def _dedupe_dict_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    deduped = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = json.dumps(row, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped


def _missing_citation_refs(
    *,
    evidence_rows: list[dict[str, Any]],
    rule_id: str,
    evidence_kind: str,
) -> list[str]:
    missing = []
    for row in evidence_rows:
        if row.get("citation_label"):
            continue
        if row.get("artifact_sha256") or row.get("text_span") or row.get("chunk_id"):
            missing.append(
                f"{rule_id}:{evidence_kind}:{row.get('chunk_id') or row.get('source_record_id') or 'missing-citation'}"
            )
    return missing
