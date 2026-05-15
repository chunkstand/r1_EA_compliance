from __future__ import annotations

from contextlib import closing
from pathlib import Path
import hashlib
import json
import sqlite3
import unittest

from usfs_r1_ea_sources.claim_extraction import build_claim_extraction
from usfs_r1_ea_sources.compliance_review import run_compliance_review
from usfs_r1_ea_sources.ea_review import run_ea_review
from usfs_r1_ea_sources.records import sha256_file
from usfs_r1_ea_sources.retrieval import build_retrieval_index
from usfs_r1_ea_sources.rule_claim_binding import default_rule_claim_links_dir


def _build_source_library(output_dir: Path, source_set_id: str) -> None:
    _write_extraction_diagnostics(
        output_dir,
        source_set_id,
        source_record_ids=["R1EA-001", "R1EA-002"],
    )
    _write_chunks(
        output_dir,
        source_set_id,
        [
            _chunk(
                source_set_id=source_set_id,
                source_record_id="R1EA-001",
                title="EA requirements",
                document_role="regulation",
                authority_level="federal",
                citation_label="R1EA-001 | EA requirements | artifact abc123",
                text="An environmental assessment should describe the purpose and need.",
            ),
            _chunk(
                source_set_id=source_set_id,
                source_record_id="R1EA-002",
                title="FONSI mitigation",
                document_role="regulation",
                authority_level="federal",
                citation_label="R1EA-002 | FONSI mitigation | artifact def456",
                text="A finding of no significant impact should address mitigation measures.",
            ),
        ],
    )
    _write_catalog_sqlite(
        output_dir,
        {
            "R1EA-001": ["Purpose and need"],
            "R1EA-002": ["Mitigation"],
        },
    )
    build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
    build_claim_extraction(output_dir=output_dir, source_set_id=source_set_id)


def _write_extraction_diagnostics(
    output_dir: Path,
    source_set_id: str,
    *,
    source_record_ids: list[str],
) -> None:
    diagnostics_dir = output_dir / "derived" / source_set_id / "diagnostics"
    diagnostics_dir.mkdir(parents=True, exist_ok=True)
    (diagnostics_dir / "extraction_validation.json").write_text(
        json.dumps({"passed": True}, sort_keys=True),
        encoding="utf-8",
    )
    manifest_records = [
        {
            "source_set_id": source_set_id,
            "source_record_id": source_record_id,
            "status": "extracted",
        }
        for source_record_id in source_record_ids
    ]
    (diagnostics_dir / "extraction_manifest.jsonl").write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in manifest_records),
        encoding="utf-8",
    )
    summary = {
        "source_set_id": source_set_id,
        "catalog_source_count": len(source_record_ids),
        "selected_source_count": len(source_record_ids),
        "extracted_count": len(source_record_ids),
        "filters": {"id": None, "parser": None, "limit": None},
    }
    (diagnostics_dir / "summary.json").write_text(
        json.dumps(summary, sort_keys=True),
        encoding="utf-8",
    )
    catalog_dir = output_dir / "catalog"
    catalog_dir.mkdir(parents=True, exist_ok=True)
    (catalog_dir / "source_set_manifest.json").write_text(
        json.dumps({"source_set_id": source_set_id}, sort_keys=True),
        encoding="utf-8",
    )
    (catalog_dir / "catalog_validation.json").write_text(
        json.dumps({"passed": True}, sort_keys=True),
        encoding="utf-8",
    )


def _write_extraction_accuracy_audit(
    output_dir: Path,
    source_set_id: str,
    *,
    admitted_source_record_ids: list[str],
) -> Path:
    path = output_dir / "derived" / source_set_id / "diagnostics" / "extraction_accuracy_audit.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source_set_id": source_set_id,
        "passed": True,
        "knowledge_base_admitted_source_record_ids": admitted_source_record_ids,
        "knowledge_base_blocked_source_record_ids": [],
    }
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return path


def _write_chunks(output_dir: Path, source_set_id: str, chunks: list[dict]) -> Path:
    path = output_dir / "derived" / source_set_id / "chunks" / "chunks.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    for chunk in chunks:
        artifact_path = output_dir / chunk["artifact_path"]
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(f"artifact for {chunk['source_record_id']}", encoding="utf-8")
        text_path = output_dir / chunk["source_text_path"]
        text_path.parent.mkdir(parents=True, exist_ok=True)
        text_path.write_text(chunk["text"], encoding="utf-8")
    path.write_text(
        "".join(json.dumps(chunk, sort_keys=True) + "\n" for chunk in chunks),
        encoding="utf-8",
    )
    return path


def _write_catalog_sqlite(output_dir: Path, topics_by_source: dict[str, list[str]]) -> None:
    path = output_dir / "catalog" / "review_sources.sqlite"
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as connection:
        connection.executescript(
            """
            CREATE TABLE review_topics (
              topic_id TEXT PRIMARY KEY,
              label TEXT NOT NULL
            );
            CREATE TABLE source_review_topics (
              source_record_id TEXT NOT NULL,
              topic_id TEXT NOT NULL,
              PRIMARY KEY (source_record_id, topic_id)
            );
            """
        )
        for source_record_id, topics in topics_by_source.items():
            for index, topic in enumerate(topics):
                topic_id = f"topic:{source_record_id}:{index}"
                connection.execute("INSERT INTO review_topics VALUES (?, ?)", (topic_id, topic))
                connection.execute(
                    "INSERT INTO source_review_topics VALUES (?, ?)",
                    (source_record_id, topic_id),
                )
        connection.commit()


def _write_downstream_direct_eval_phase_outputs(output_dir: Path, source_set_id: str) -> None:
    contracts = {
        output_dir / "derived" / source_set_id / "retrieval" / "retrieval_eval_results.json": (
            Path("config/retrieval_eval_seed.json"),
            "retrieval-direct-eval-v1",
        ),
        output_dir / "derived" / source_set_id / "claims" / "claim_eval_results.json": (
            Path("config/claim_eval_seed.json"),
            "claim-direct-eval-v1",
        ),
        output_dir / "reviews" / "compliance_review_eval" / "compliance_review_eval_results.json": (
            Path("config/compliance_review_eval_seed.json"),
            "compliance-review-direct-eval-v1",
        ),
    }
    rule_claim_root = output_dir / "derived" / source_set_id / "rule_claim_links"
    candidates = sorted(rule_claim_root.glob("*/*/summary.json"))
    rule_claim_result_paths = {
        candidate.parent / "rule_claim_link_eval_results.json" for candidate in candidates
    }
    if not rule_claim_result_paths:
        rule_claim_result_paths.add(
            default_rule_claim_links_dir(
                output_dir,
                source_set_id=source_set_id,
            )
            / "rule_claim_link_eval_results.json"
        )
    for rule_claim_result_path in rule_claim_result_paths:
        contracts[rule_claim_result_path] = (
            Path("config/rule_claim_link_eval_seed.json"),
            "rule-claim-direct-eval-v1",
        )
    for result_path, (contract_path, eval_id) in contracts.items():
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(
            json.dumps(
                _direct_eval_result_payload(
                    contract_path=contract_path,
                    eval_id=eval_id,
                    source_set_id=source_set_id,
                ),
                sort_keys=True,
            ),
            encoding="utf-8",
        )


def _chunk(
    *,
    source_set_id: str,
    source_record_id: str,
    title: str,
    document_role: str,
    authority_level: str,
    citation_label: str,
    text: str,
) -> dict:
    content_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    artifact_sha256 = hashlib.sha256(source_record_id.encode("utf-8")).hexdigest()
    return {
        "chunk_id": f"chunk:{source_record_id}",
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "chunk_index": 0,
        "title": title,
        "document_role": document_role,
        "support_document_role": document_role,
        "authority_level": authority_level,
        "host": "example.test",
        "expected_parser": "html",
        "artifact_sha256": artifact_sha256,
        "artifact_path": f"artifacts/raw/{source_record_id}.html",
        "citation_label": citation_label,
        "original_url": f"https://example.test/{source_record_id}/original",
        "effective_url": f"https://example.test/{source_record_id}",
        "final_url": f"https://example.test/{source_record_id}",
        "parser_name": "unit_parser",
        "parser_version": "1.0",
        "extracted_at": "2026-04-30T00:00:00Z",
        "source_text_path": f"derived/{source_set_id}/extracted_text/{source_record_id}.txt",
        "char_start": 0,
        "char_end": len(text),
        "page": None,
        "section": None,
        "heading": title,
        "content_sha256": content_sha256,
        "text": text,
    }


def _direct_eval_result_payload(
    *,
    contract_path: Path,
    eval_id: str,
    source_set_id: str,
) -> dict:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    coverage_requirements = contract.get("coverage_requirements", {})
    case_count = int(
        coverage_requirements.get("case_count")
        or ((contract.get("metric_thresholds") or {}).get("case_count") or {}).get("min")
        or 1
    )
    metrics = {}
    for metric_name, threshold in (contract.get("metric_thresholds") or {}).items():
        if not isinstance(threshold, dict):
            continue
        if "min" in threshold:
            metrics[metric_name] = threshold["min"]
        elif "max" in threshold:
            metrics[metric_name] = threshold["max"]
    payload = {
        "schema_version": "unit-direct-eval-result",
        "eval_id": eval_id,
        "source_set_id": source_set_id,
        "passed": True,
        "checks": [
            {
                "name": "eval_cases_pass",
                "passed": True,
                "details": {"case_count": case_count, "failed_case_ids": []},
            },
            {
                "name": "metric_thresholds_met",
                "passed": True,
                "details": {"failures": []},
            },
        ],
        "contract": {"sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest()},
        "metrics": metrics,
    }
    for key, value in coverage_requirements.items():
        payload[key] = value
    payload.setdefault("case_count", case_count)
    payload.setdefault(
        "hard_negative_case_count",
        coverage_requirements.get("hard_negative_case_count", 0),
    )
    if eval_id == "retrieval-direct-eval-v1":
        payload["query_count"] = case_count
    return payload


def _write_package(directory: Path, text: str) -> Path:
    path = directory / "ea-package.txt"
    path.write_text(text, encoding="utf-8")
    return path


def _write_rule_pack(directory: Path, rule_ids: list[str] | None = None) -> Path:
    rule_pack = _rule_pack()
    if rule_ids is not None:
        wanted = set(rule_ids)
        rule_pack["rules"] = [rule for rule in rule_pack["rules"] if rule["id"] in wanted]
        kept_source_record_ids = {
            source_record_id
            for rule in rule_pack["rules"]
            if (source_record_id := rule.get("authority_source_record_id"))
        }
        rule_pack["baseline_source_record_ids"] = [
            source_record_id
            for source_record_id in rule_pack.get("baseline_source_record_ids", [])
            if source_record_id in kept_source_record_ids
        ]
    path = directory / "rule-pack.json"
    path.write_text(json.dumps(rule_pack, sort_keys=True), encoding="utf-8")
    return path


def _write_generated_review_gate(
    *,
    output_dir: Path,
    review_id: str,
    source_set_id: str,
    package_path: Path,
    base_rule_pack_path: Path,
    include_non_applicable: bool = False,
) -> Path:
    review_dir = output_dir / "reviews" / review_id
    run_ea_review(
        package_path=package_path,
        output_dir=output_dir,
        source_set_id=source_set_id,
        checklist_path=base_rule_pack_path,
        review_id=review_id,
        results_dir=review_dir,
    )
    applicability_dir = review_dir / "applicability"
    applicability_dir.mkdir(parents=True, exist_ok=True)
    base_rule_pack = json.loads(base_rule_pack_path.read_text(encoding="utf-8"))
    package_manifest_path = review_dir / "package" / "package_manifest.jsonl"
    package_chunks_path = review_dir / "package" / "package_chunks.jsonl"
    authority_universe_path = applicability_dir / "authority_universe_snapshot.json"
    package_fact_graph_path = applicability_dir / "package_fact_graph.json"
    package_fact_graph_validation_path = applicability_dir / "package_fact_graph_validation.json"
    retrieval_trace_path = applicability_dir / "applicability_retrieval_trace.jsonl"
    graph_trace_path = applicability_dir / "applicability_graph_trace.jsonl"
    trace_diagnostics_path = applicability_dir / "applicability_retrieval_graph_diagnostics.json"
    decisions_path = applicability_dir / "applicability_decisions.jsonl"
    applicable_path = applicability_dir / "applicable_authorities.json"
    non_applicable_path = applicability_dir / "non_applicable_authorities.json"
    coverage_path = applicability_dir / "search_coverage_certificates.json"
    provenance_path = applicability_dir / "applicability_provenance.json"
    validation_path = applicability_dir / "applicability_validation.json"
    generated_path = applicability_dir / "generated_rule_pack.json"
    generated_validation_path = applicability_dir / "generated_rule_pack_validation.json"
    applicability_run_id = f"applicability-{review_id}"
    applicable_authorities = []
    decisions = []
    candidate_authorities = []
    for rule in base_rule_pack["rules"]:
        candidate_id = f"candidate:{rule['id']}"
        decision_id = f"decision:{rule['id']}"
        authority_family_id = rule.get("authority_family_id")
        authority = {
            "candidate_authority_id": candidate_id,
            "candidate_authority_type": "rule_template",
            "decision_id": decision_id,
            "authority_family_id": authority_family_id,
            "authority_family_ids": [authority_family_id] if authority_family_id else [],
            "status": "applicable",
            "basis_type": "mandatory_baseline",
            "applicability_basis": {
                "rationale": "Unit generated gate marks baseline rule applicable.",
            },
            "rule_template": {
                "rule_id": rule["id"],
                "authority_family_id": authority_family_id,
            },
            "source_record_ids": [rule.get("authority_source_record_id")],
            "document_roles": [rule.get("authority_document_role") or "regulation"],
        }
        candidate_authorities.append(authority)
        applicable_authorities.append(authority)
        decisions.append(authority)
    non_applicable_authorities = (
        [
            {
                "candidate_authority_id": "candidate:not-applicable",
                "candidate_authority_type": "rule_template",
                "decision_id": "decision:not-applicable",
                "authority_family_id": "unit_not_applicable",
                "authority_family_ids": ["unit_not_applicable"],
                "status": "not_applicable",
                "basis_type": "absent_trigger_evidence",
                "applicability_basis": {
                    "rationale": "Unit package did not include the conditional trigger.",
                },
                "non_applicability_basis": {
                    "rationale": "Unit package did not include the conditional trigger.",
                },
                "search_coverage_certificate_ids": ["coverage:not-applicable"],
            }
        ]
        if include_non_applicable
        else []
    )
    if include_non_applicable:
        candidate_authorities.extend(non_applicable_authorities)
        decisions.extend(non_applicable_authorities)
    _write_json(
        authority_universe_path,
        {
            "schema_version": "authority-universe-snapshot-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "validation": {"passed": True},
            "candidate_authorities": candidate_authorities,
        },
    )
    package_fact_graph_sha256 = hashlib.sha256(
        f"{review_id}:{source_set_id}:package-facts".encode("utf-8")
    ).hexdigest()
    _write_json(
        package_fact_graph_path,
        {
            "schema_version": "package-fact-graph-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "package_fact_graph_sha256": package_fact_graph_sha256,
            "nodes": [{"node_id": "package-fact:purpose-need", "node_type": "package_section"}],
            "edges": [],
        },
    )
    _write_json(
        package_fact_graph_validation_path,
        {
            "schema_version": "package-fact-graph-validation-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "package_fact_graph_sha256": package_fact_graph_sha256,
            "validation": {"passed": True, "checks": []},
        },
    )
    _write_jsonl(
        retrieval_trace_path,
        [
            {
                "candidate_authority_id": authority["candidate_authority_id"],
                "trace_id": f"retrieval:{authority['candidate_authority_id']}",
            }
            for authority in candidate_authorities
        ],
    )
    _write_jsonl(
        graph_trace_path,
        [
            {
                "candidate_authority_id": authority["candidate_authority_id"],
                "trace_id": f"graph:{authority['candidate_authority_id']}",
            }
            for authority in candidate_authorities
        ],
    )
    _write_json(
        trace_diagnostics_path,
        {
            "schema_version": "applicability-retrieval-graph-diagnostics-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "retrieval_trace_sha256": sha256_file(retrieval_trace_path),
            "graph_trace_sha256": sha256_file(graph_trace_path),
            "validation": {"passed": True, "checks": []},
        },
    )
    _write_jsonl(decisions_path, decisions)
    _write_json(
        applicable_path,
        {
            "schema_version": "applicable-authorities-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "authority_count": len(applicable_authorities),
            "authorities": applicable_authorities,
        },
    )
    _write_json(
        non_applicable_path,
        {
            "schema_version": "non-applicable-authorities-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "authority_count": len(non_applicable_authorities),
            "authorities": non_applicable_authorities,
        },
    )
    coverage_certificates = (
        [
            {
                "coverage_certificate_id": "coverage:not-applicable",
                "candidate_authority_id": "candidate:not-applicable",
                "covered_candidate_authority_ids": ["candidate:not-applicable"],
                "covered_decision_ids": ["decision:not-applicable"],
                "coverage_class": "non_applicable_authority",
                "coverage_result": "sufficient",
                "rationale": "Unit coverage certificate for not-applicable authority.",
            }
        ]
        if include_non_applicable
        else []
    )
    _write_json(
        coverage_path,
        {
            "schema_version": "search-coverage-certificates-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "certificates": coverage_certificates,
        },
    )
    _write_json(
        provenance_path,
        {
            "schema_version": "applicability-provenance-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "applicability_run_id": applicability_run_id,
            "entities": [],
        },
    )
    hashes = {
        "applicable_authorities_sha256": sha256_file(applicable_path),
        "authority_universe_sha256": sha256_file(authority_universe_path),
        "decisions_sha256": sha256_file(decisions_path),
        "non_applicable_authorities_sha256": sha256_file(non_applicable_path),
        "applicability_provenance_sha256": sha256_file(provenance_path),
        "package_manifest_sha256": sha256_file(package_manifest_path),
        "package_chunks_sha256": sha256_file(package_chunks_path),
        "search_coverage_certificates_sha256": sha256_file(coverage_path),
    }
    _write_json(
        validation_path,
        {
            "schema_version": "applicability-validation-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "applicability_run_id": applicability_run_id,
            "passed": True,
            "reviewer_ready": True,
            "generated_rule_pack_ready": True,
            "artifact_paths": {
                "applicable_authorities": str(applicable_path),
                "authority_universe": str(authority_universe_path),
                "decisions": str(decisions_path),
                "non_applicable_authorities": str(non_applicable_path),
                "search_coverage_certificates": str(coverage_path),
                "provenance": str(provenance_path),
            },
            "hashes": hashes,
        },
    )
    generated_rules = []
    for rule in base_rule_pack["rules"]:
        generated_rule = dict(rule)
        generated_rule["base_rule_id"] = rule["id"]
        generated_rule["generated_rule_id"] = rule["id"]
        generated_rule["base_rule_pack_id"] = base_rule_pack["rule_pack_id"]
        generated_rule["base_rule_pack_version"] = base_rule_pack["version"]
        generated_rule["generated_from_applicability"] = True
        generated_rule["applicability_decision_id"] = f"decision:{rule['id']}"
        generated_rule["candidate_authority_id"] = f"candidate:{rule['id']}"
        generated_rule["authority_family_id"] = rule.get("authority_family_id")
        generated_rule["authority_family_ids"] = [rule.get("authority_family_id")]
        generated_rule["applicability"] = {
            "decision_id": generated_rule["applicability_decision_id"],
            "candidate_authority_id": generated_rule["candidate_authority_id"],
            "candidate_authority_type": "rule_template",
            "authority_family_id": rule.get("authority_family_id"),
            "authority_family_ids": [rule.get("authority_family_id")],
            "status": "applicable",
            "basis_type": "mandatory_baseline",
            "applicability_basis": {
                "rationale": "Unit generated gate marks baseline rule applicable.",
            },
            "source_record_ids": [rule.get("authority_source_record_id")],
            "document_roles": [rule.get("authority_document_role") or "regulation"],
        }
        generated_rules.append(generated_rule)
    generated_rule_pack = {
        **base_rule_pack,
        "schema_version": "generated-compliance-rule-pack-v0",
        "rule_pack_id": f"generated-{base_rule_pack['rule_pack_id']}",
        "version": "applicability-v0",
        "base_rule_pack_id": base_rule_pack["rule_pack_id"],
        "base_rule_pack_version": base_rule_pack["version"],
        "base_rule_pack_sha256": sha256_file(base_rule_pack_path),
        "generated_rule_pack_id": f"generated-{base_rule_pack['rule_pack_id']}",
        "generated_rule_pack_version": "applicability-v0",
        "applicability_run_id": applicability_run_id,
        "applicability_validation_sha256": sha256_file(validation_path),
        "source_set_id": source_set_id,
        "review_id": review_id,
        "non_applicable_authorities_sha256": sha256_file(non_applicable_path),
        **hashes,
        "rules": generated_rules,
    }
    _write_json(generated_path, generated_rule_pack)
    generated_sha = sha256_file(generated_path)
    _write_json(
        generated_validation_path,
        {
            "schema_version": "generated-rule-pack-validation-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "passed": True,
            "summary": {
                "generated_rule_pack_ready": True,
                "generated_rule_pack_sha256": generated_sha,
                "expected_generated_rule_pack_sha256": generated_sha,
                "applicability_run_id": applicability_run_id,
                "source_set_id": source_set_id,
            },
        },
    )
    return generated_path


def _run_generated_compliance_review(
    *,
    output_dir: Path,
    review_id: str,
    source_set_id: str,
    package_path: Path,
    base_rule_pack_path: Path,
    include_non_applicable: bool = False,
    forest_unit_id: str = "custer-gallatin-nf",
):
    generated_rule_pack_path = _write_generated_review_gate(
        output_dir=output_dir,
        review_id=review_id,
        source_set_id=source_set_id,
        package_path=package_path,
        base_rule_pack_path=base_rule_pack_path,
        include_non_applicable=include_non_applicable,
    )
    result = run_compliance_review(
        package_path=package_path,
        output_dir=output_dir,
        source_set_id=source_set_id,
        rule_pack_path=generated_rule_pack_path,
        forest_unit_id=forest_unit_id,
        review_id=review_id,
        reuse_package_cache=True,
    )
    _write_downstream_direct_eval_phase_outputs(output_dir, source_set_id)
    return result


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _write_grouped_conditional_rule_pack(directory: Path) -> Path:
    rule_pack = {
        "schema_version": "compliance-rule-pack-v0",
        "rule_pack_id": "unit-grouped-conditional",
        "version": "0.1.0",
        "title": "Unit Grouped Conditional Rule Pack",
        "description": "Unit test rule pack for grouped conditional applicability.",
        "rules": [
            {
                "id": "ce_adoption",
                "title": "CE adoption is reviewed",
                "authority_category": "regulation",
                "authority_source_record_id": "R1EA-002",
                "applicability_mode": "conditional",
                "question": "Does the EA package document a CE adoption path?",
                "requirement": "A CE adoption path should be documented when actually used.",
                "package_query": "adopted CE categorical exclusion path",
                "package_terms": ["adopted CE", "categorical exclusion path"],
                "source_query": "mitigation measures finding of no significant impact",
                "source_filters": {
                    "document_role": "regulation",
                    "source_record_id": "R1EA-002",
                },
                "applies_if_package_terms": [
                    "categorical exclusion",
                    "adopted CE",
                    "categorical exclusion path",
                ],
                "applies_if_package_term_groups": [
                    ["categorical exclusion", "CE"],
                    ["adopted CE", "categorical exclusion path"],
                ],
                "does_not_apply_if_package_terms": [
                    "not subject to a categorical exclusion",
                    "categorical exclusion path is not used",
                ],
                "severity": "high",
            }
        ],
    }
    path = directory / "grouped-conditional-rule-pack.json"
    path.write_text(json.dumps(rule_pack, sort_keys=True), encoding="utf-8")
    return path


def _write_compliance_eval_file(
    directory: Path,
    cases: list[dict],
    *,
    path: Path | None = None,
) -> Path:
    eval_path = path or directory / "compliance-eval.json"
    eval_path.write_text(json.dumps(cases, sort_keys=True), encoding="utf-8")
    return eval_path


def _write_coverage_matrix(directory: Path, rule_ids: list[str] | None = None) -> Path:
    items = [
        {
            "rule_id": "purpose_need",
            "obligation_area": "Purpose and need",
            "expected_package_evidence": "Purpose and need or proposed action text.",
            "source_record_ids": ["R1EA-001"],
            "source_claim_terms": ["purpose", "need"],
            "eval_case_ids": ["coverage-case"],
        },
        {
            "rule_id": "mitigation",
            "obligation_area": "Mitigation",
            "expected_package_evidence": "Mitigation or FONSI support text.",
            "source_record_ids": ["R1EA-002"],
            "source_claim_terms": ["mitigation"],
            "eval_case_ids": ["coverage-case"],
        },
    ]
    if rule_ids is not None:
        wanted = set(rule_ids)
        items = [item for item in items if item["rule_id"] in wanted]
    path = directory / "coverage-matrix.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "compliance-rule-pack-coverage-v0",
                "rule_pack_id": "unit-nepa-ea",
                "rule_pack_version": "0.1.0",
                "title": "Unit coverage matrix",
                "coverage_items": items,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def _write_gold_eval_file(directory: Path, profiles: list[str] | None = None) -> Path:
    profiles = profiles or ["positive", "mixed", "negative"]
    cases = [
        {
            "id": "gold-positive",
            "profile": profiles[0],
            "package_text": (
                "Purpose and Need. The proposed action improves trail access. "
                "Alternatives include no action. Mitigation measures support a FONSI."
            ),
            "expected_statuses": {
                "purpose_need": "pass",
                "mitigation": "pass",
            },
            "expected_finding_status_counts": {"pass": 2},
            "min_findings": 2,
        },
        {
            "id": "gold-mixed",
            "profile": profiles[1],
            "package_text": "Purpose and Need. The proposed action improves trail access.",
            "expected_statuses": {
                "purpose_need": "pass",
                "mitigation": "gap",
            },
            "expected_finding_status_counts": {"gap": 1, "pass": 1},
            "min_findings": 2,
        },
        {
            "id": "gold-negative",
            "profile": profiles[2],
            "package_text": "Routing slip. Staff contacts and a meeting date.",
            "expected_statuses": {
                "purpose_need": "gap",
                "mitigation": "gap",
            },
            "expected_finding_status_counts": {"gap": 2},
            "min_findings": 2,
        },
    ]
    for case in cases:
        case["adjudication"] = {
            "status": "adjudicated_seed",
            "source_type": "realistic_synthetic",
            "adjudicated_by": ["unit-test"],
            "adjudicated_at": "2026-04-30",
            "rationale": f"Unit adjudication for {case['id']}.",
        }
        case["expected_unsupported_finding_ids"] = []
        case["expected_source_record_ids"] = {
            "purpose_need": ["R1EA-001"],
            "mitigation": ["R1EA-002"],
        }
        case["expected_source_document_roles"] = {
            "purpose_need": ["regulation"],
            "mitigation": ["regulation"],
        }
    path = directory / "gold-eval.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "compliance-gold-eval-v0",
                "id": "unit-gold-v0.1",
                "version": "0.1.0",
                "title": "Unit Gold Eval",
                "rule_pack_id": "unit-nepa-ea",
                "rule_pack_version": "0.1.0",
                "adjudication": {
                    "status": "seed_gold",
                    "method": "Unit test adjudication.",
                    "adjudicated_by": ["unit-test"],
                    "adjudicated_at": "2026-04-30",
                    "promotion_gate": True,
                },
                "cases": cases,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def _rule_pack() -> dict:
    return {
        "schema_version": "compliance-rule-pack-v0",
        "rule_pack_id": "unit-nepa-ea",
        "version": "0.1.0",
        "title": "Unit NEPA EA Rule Pack",
        "description": "Unit test rule pack.",
        "baseline_source_record_ids": ["R1EA-001", "R1EA-002"],
        "rules": [
            {
                "id": "purpose_need",
                "title": "Purpose and need are stated",
                "authority_category": "regulation",
                "authority_family_id": "unit_purpose_need",
                "authority_source_record_id": "R1EA-001",
                "applicability_mode": "baseline",
                "question": "Does the EA package identify the purpose and need?",
                "requirement": "Purpose and need should be identified.",
                "package_query": "purpose need proposed action",
                "package_terms": ["purpose and need", "proposed action"],
                "source_query": "environmental assessment purpose need",
                "source_filters": {"document_role": "regulation", "source_record_id": "R1EA-001"},
                "severity": "high",
            },
            {
                "id": "mitigation",
                "title": "Mitigation is addressed",
                "authority_category": "regulation",
                "authority_family_id": "unit_mitigation",
                "authority_source_record_id": "R1EA-002",
                "applicability_mode": "baseline",
                "question": "Does the EA package address mitigation?",
                "requirement": "Mitigation should be addressed when used to support a finding.",
                "package_query": "mitigation measures",
                "package_terms": ["mitigation"],
                "source_query": "mitigation measures finding of no significant impact",
                "source_filters": {"document_role": "regulation", "source_record_id": "R1EA-002"},
                "severity": "high",
            },
        ],
    }


def _rule_by_id(rule_pack: dict, rule_id: str) -> dict:
    return next(rule for rule in rule_pack["rules"] if rule["id"] == rule_id)


def _coverage_item_by_rule_id(coverage: dict, rule_id: str) -> dict:
    return next(item for item in coverage["coverage_items"] if item["rule_id"] == rule_id)


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _finding(report: dict, finding_id: str) -> dict:
    return next(finding for finding in report["findings"] if finding["id"] == finding_id)


def _check(validation: dict, name: str) -> dict:
    return next(check for check in validation["checks"] if check["name"] == name)


def _phase(summary: dict, name: str) -> dict:
    return next(phase for phase in summary["phases"] if phase["name"] == name)


def _assert_v1_land_exchange_contract(testcase: unittest.TestCase) -> None:
    rule_pack = json.loads(
        Path("config/compliance_rule_pack_nepa_ea_v0.json").read_text(encoding="utf-8")
    )
    coverage = json.loads(
        Path("config/compliance_rule_pack_coverage_nepa_ea_v0.json").read_text(
            encoding="utf-8"
        )
    )
    eval_contract = json.loads(
        Path("config/compliance_review_eval_seed.json").read_text(encoding="utf-8")
    )
    eval_cases = {case["id"]: case for case in eval_contract["cases"]}
    v1_contract = json.loads(Path("config/v1_ecid_real_ea_eval.json").read_text(encoding="utf-8"))

    rule = _rule_by_id(rule_pack, "flpma_section_206_land_exchange")
    testcase.assertEqual(rule["authority_source_record_id"], "R1EA-146")
    testcase.assertEqual(rule["applicability_mode"], "conditional")
    testcase.assertEqual(
        rule["source_filters"],
        {"document_role": "law", "source_record_id": "R1EA-146"},
    )
    testcase.assertIn("FLPMA", rule["applies_if_package_terms"])
    testcase.assertIn("cash equalization", rule["package_terms"])

    coverage_item = _coverage_item_by_rule_id(
        coverage,
        "flpma_section_206_land_exchange",
    )
    testcase.assertEqual(coverage_item["source_record_ids"], ["R1EA-146"])
    testcase.assertEqual(
        set(coverage_item["eval_case_ids"]),
        {
            "all-authorities-pass",
            "baseline-nepa-only",
            "unrelated-package-produces-baseline-gaps",
        },
    )

    testcase.assertEqual(
        eval_cases["all-authorities-pass"]["expected_statuses"][
            "flpma_section_206_land_exchange"
        ],
        "pass",
    )
    testcase.assertEqual(
        eval_cases["all-authorities-pass"]["expected_source_record_ids"][
            "flpma_section_206_land_exchange"
        ],
        ["R1EA-146"],
    )
    testcase.assertEqual(
        eval_cases["baseline-nepa-only"]["expected_statuses"][
            "flpma_section_206_land_exchange"
        ],
        "not_applicable",
    )
    testcase.assertEqual(
        eval_cases["unrelated-package-produces-baseline-gaps"]["expected_statuses"][
            "flpma_section_206_land_exchange"
        ],
        "not_applicable",
    )

    conditional_expectations = {
        expectation["rule_id"]: expectation
        for expectation in v1_contract["conditional_source_expectations"]
    }
    land_exchange_contracts = {
        "flpma_section_206_land_exchange": {
            "source_record_ids": ["R1EA-146"],
            "document_roles": ["law"],
            "family_id": "land_exchange_statutory_authorities",
            "mode": "conditional",
        },
        "land_exchange_statutory_authorities": {
            "source_record_ids": ["R1EA-137"],
            "document_roles": ["law"],
            "family_id": "land_exchange_statutory_authorities",
            "mode": "conditional",
        },
        "land_exchange_regulatory_requirements": {
            "source_record_ids": ["R1EA-124"],
            "document_roles": ["regulation"],
            "family_id": "land_exchange_regulatory_requirements",
            "mode": "conditional",
        },
        "land_exchange_fs_policy_and_project_references": {
            "source_record_ids": ["R1EA-150"],
            "document_roles": ["agency_policy"],
            "family_id": "land_exchange_fs_policy_and_project_references",
            "mode": "conditional",
        },
    }
    generic_exchange_terms = {
        "acquisition",
        "appraisal",
        "cash equalization",
        "closing",
        "disposal",
        "easement",
        "equal value",
        "feasibility analysis",
        "mineral reservation",
        "outstanding rights",
        "public interest determination",
        "reservation",
        "reservations",
        "segregation",
        "title evidence",
    }
    for rule_id, expected in land_exchange_contracts.items():
        rule = _rule_by_id(rule_pack, rule_id)
        testcase.assertEqual(rule["authority_source_record_id"], expected["source_record_ids"][0])
        testcase.assertEqual(rule["applicability_mode"], expected["mode"])
        testcase.assertEqual(rule["authority_family_id"], expected["family_id"])
        testcase.assertIn("land exchange", [term.lower() for term in rule["package_terms"]])
        singleton_trigger_groups = {
            tuple(term.lower() for term in group)
            for group in rule.get("applies_if_package_term_groups", [])
            if len(group) == 1
        }
        testcase.assertFalse(
            {(term,) for term in generic_exchange_terms} & singleton_trigger_groups
        )

        coverage_item = _coverage_item_by_rule_id(coverage, rule_id)
        testcase.assertEqual(coverage_item["source_record_ids"], expected["source_record_ids"])
        testcase.assertEqual(
            set(coverage_item["eval_case_ids"]),
            {
                "all-authorities-pass",
                "baseline-nepa-only",
                "unrelated-package-produces-baseline-gaps",
            },
        )

        testcase.assertEqual(eval_cases["all-authorities-pass"]["expected_statuses"][rule_id], "pass")
        testcase.assertEqual(
            eval_cases["baseline-nepa-only"]["expected_statuses"][rule_id],
            "not_applicable",
        )
        testcase.assertEqual(
            eval_cases["unrelated-package-produces-baseline-gaps"]["expected_statuses"][rule_id],
            "not_applicable",
        )

        v1_expectation = conditional_expectations[rule_id]
        testcase.assertEqual(v1_expectation["expected_applicability"], "applicable")
        testcase.assertEqual(
            v1_expectation["expected_source_record_ids"],
            expected["source_record_ids"],
        )
        testcase.assertEqual(
            v1_expectation["expected_source_document_roles"],
            expected["document_roles"],
        )
