from __future__ import annotations

from pathlib import Path
import json
import tempfile

from usfs_r1_ea_sources.nepa_knowledge_graph_export import build_nepa_knowledge_graph_export


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_nepa_knowledge_graph_export_builds_source_set_graph_from_audited_surfaces() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp) / "source_library"
        source_set_id = "source-set-test"
        paths = _write_minimal_source_set(output_dir, source_set_id=source_set_id)

        result = build_nepa_knowledge_graph_export(
            output_dir=output_dir,
            source_set_id=source_set_id,
            graph_contract_path=REPO_ROOT / "config" / "nepa_3d_graph_contract_v1.json",
            authority_inventory_path=paths["authority_inventory"],
            authority_family_rule_templates_path=paths["templates"],
            forest_plan_profiles_path=paths["forest_profiles"],
            rule_pack_path=paths["rule_pack"],
        )

        assert result.summary["validation_passed"]
        assert result.summary["authority_family_count"] == 3
        assert result.summary["base_rule_count"] == 2
        assert result.summary["authority_family_rule_template_count"] == 1
        assert result.summary["forest_plan_component_count"] == 1
        assert result.summary["catalog_graph_node_count"] == 1
        assert result.summary["catalog_graph_edge_count"] == 1

        graph = _read_json(result.graph_path)
        nodes = _read_jsonl(result.nodes_path)
        edges = _read_jsonl(result.edges_path)
        node_ids = {node["node_id"] for node in nodes}
        checks = {check["name"]: check for check in graph["validation"]["checks"]}

        assert len(nodes) == graph["summary"]["node_count"]
        assert len(edges) == graph["summary"]["edge_count"]
        assert all(edge["source_node_id"] in node_ids for edge in edges)
        assert all(edge["target_node_id"] in node_ids for edge in edges)
        assert checks["nepa_3d_graph_exports_all_authority_families"]["passed"]
        assert checks["nepa_3d_graph_exports_all_catalog_source_records"]["passed"]
        assert checks["nepa_3d_graph_exports_candidate_families"]["passed"]
        assert checks["nepa_3d_graph_exports_superseded_families"]["passed"]
        assert checks["nepa_3d_graph_reads_catalog_graph_seeds"]["passed"]
        assert checks["nepa_3d_graph_nodes_have_required_provenance"]["passed"]
        assert checks["nepa_3d_graph_edges_match_declared_endpoint_types"]["passed"]
        assert checks["nepa_3d_graph_lens_metadata_shape"]["passed"]
        assert checks["nepa_3d_graph_lens_metadata_required_lenses_present"]["passed"]
        assert "forest_plan_component" in graph["summary"]["node_type_counts"]
        assert "source_claim" in graph["summary"]["node_type_counts"]

        first_bytes = result.graph_path.read_bytes()
        second = build_nepa_knowledge_graph_export(
            output_dir=output_dir,
            source_set_id=source_set_id,
            graph_contract_path=REPO_ROOT / "config" / "nepa_3d_graph_contract_v1.json",
            authority_inventory_path=paths["authority_inventory"],
            authority_family_rule_templates_path=paths["templates"],
            forest_plan_profiles_path=paths["forest_profiles"],
            rule_pack_path=paths["rule_pack"],
        )
        assert second.graph_path.read_bytes() == first_bytes


def _write_minimal_source_set(output_dir: Path, *, source_set_id: str) -> dict[str, Path]:
    catalog_dir = output_dir / "catalog"
    derived_dir = output_dir / "derived" / source_set_id
    catalog_dir.mkdir(parents=True, exist_ok=True)
    _write_json(
        catalog_dir / "source_set_manifest.json",
        {
            "source_set_id": source_set_id,
            "created_at": "2026-05-06T00:00:00Z",
            "source_count": 5,
            "artifact_count": 5,
        },
    )
    catalog_rows = [
        _catalog_row(source_set_id, "R1EA-001", "Active NEPA source", "downloaded"),
        _catalog_row(source_set_id, "R1EA-002", "Active supporting source", "downloaded"),
        _catalog_row(source_set_id, "R1EA-003", "Candidate blocked source", "skipped_excluded"),
        _catalog_row(source_set_id, "R1EA-004", "Superseded source", "downloaded"),
        _catalog_row(source_set_id, "R1PLAN-001", "Forest Plan", "downloaded", document_role="forest_plan"),
    ]
    _write_jsonl(catalog_dir / "source_catalog.jsonl", catalog_rows)
    _write_jsonl(
        catalog_dir / "source_graph_nodes.jsonl",
        [{"id": "source:R1EA-001", "type": "Source", "source_record_id": "R1EA-001"}],
    )
    _write_jsonl(
        catalog_dir / "source_graph_edges.jsonl",
        [
            {
                "id": "source:R1EA-001|SUPPORTS_REVIEW_TOPIC|topic:nepa",
                "source": "source:R1EA-001",
                "target": "topic:nepa",
                "relationship": "SUPPORTS_REVIEW_TOPIC",
            }
        ],
    )
    _write_json(
        derived_dir / "authority_currentness" / "authority_currentness_report.json",
        _currentness_report(source_set_id),
    )
    _write_jsonl(
        derived_dir / "evidence_graph" / "document_graph_nodes.jsonl",
        [{"id": "source:R1EA-001", "type": "SourceDocument"}],
    )
    _write_jsonl(
        derived_dir / "evidence_graph" / "document_graph_edges.jsonl",
        [{"id": "edge:1", "source": "source:R1EA-001", "target": "artifact:sha001"}],
    )
    _write_jsonl(
        derived_dir / "claims" / "claims.jsonl",
        [
            {
                "schema_version": "source-claims-v0",
                "claim_id": "claim:001",
                "claim_text": "The agency must consider environmental effects.",
                "claim_type": "obligation",
                "source_set_id": source_set_id,
                "source_record_id": "R1EA-001",
                "artifact_sha256": "sha-R1EA-001",
                "chunk_id": "chunk:001",
                "chunk_index": 0,
                "chunk_content_sha256": "chunksha001",
                "content_sha256": "claimsha001",
                "source_char_start": 0,
                "source_char_end": 64,
                "citation_label": "R1EA-001 citation",
                "validation_status": "valid",
            }
        ],
    )
    _write_jsonl(
        derived_dir / "rule_claim_links" / "nepa-ea-v0" / "0.1.0" / "rule_claim_links.jsonl",
        [
            {
                "schema_version": "rule-claim-links-v0",
                "link_id": "rule_claim_link:001",
                "rule_id": "nepa_rule",
                "rule_pack_id": "nepa-ea-v0",
                "rule_pack_version": "0.1.0",
                "claim_id": "claim:001",
                "source_set_id": source_set_id,
                "source_record_id": "R1EA-001",
                "artifact_sha256": "sha-R1EA-001",
                "chunk_id": "chunk:001",
                "chunk_index": 0,
                "chunk_content_sha256": "chunksha001",
                "source_char_start": 0,
                "source_char_end": 64,
                "citation_label": "R1EA-001 citation",
                "score": 0.9,
            }
        ],
    )
    _write_json(
        derived_dir / "forest_plan_components" / "component_inventory.json",
        {
            "schema_version": "forest-plan-component-inventory-v0",
            "source_set_id": source_set_id,
            "components": [
                {
                    "component_id": "R1PLAN-001-FW-STD-01",
                    "component_type": "standard",
                    "forest_unit_id": "test-forest",
                    "source_record_id": "R1PLAN-001",
                    "artifact_sha256": "sha-plan",
                    "content_sha256": "component-sha",
                    "component_text": "Standard 01",
                    "source_chunk_ids": ["chunk:plan"],
                }
            ],
        },
    )

    authority_inventory = output_dir / "authority_inventory.json"
    rule_pack = output_dir / "rule_pack.json"
    templates = output_dir / "templates.json"
    forest_profiles = output_dir / "forest_profiles.json"
    _write_json(
        authority_inventory,
        {
            "schema_version": "authority-universe-families-v1",
            "authority_families": [
                {
                    "family_id": "active_family",
                    "name": "Active family",
                    "status": "active",
                    "source_record_ids": ["R1EA-001", "R1EA-002"],
                    "rule_ids": ["nepa_rule", "supporting_rule"],
                    "open_inventory_gaps": [],
                },
                {
                    "family_id": "candidate_family",
                    "name": "Candidate family",
                    "status": "candidate",
                    "source_record_ids": ["R1EA-003"],
                    "rule_ids": [],
                    "open_inventory_gaps": ["official source needed"],
                },
                {
                    "family_id": "superseded_family",
                    "name": "Superseded family",
                    "status": "superseded",
                    "source_record_ids": ["R1EA-004"],
                    "rule_ids": [],
                    "open_inventory_gaps": [],
                },
            ],
        },
    )
    _write_json(
        rule_pack,
        {
            "schema_version": "compliance-rule-pack-v0",
            "rule_pack_id": "nepa-ea-v0",
            "version": "0.1.0",
            "title": "Test rule pack",
            "rules": [
                {
                    "id": "nepa_rule",
                    "title": "NEPA applies",
                    "authority_source_record_id": "R1EA-001",
                    "applicability_mode": "baseline",
                    "authority_category": "law",
                    "severity": "high",
                    "requirement": "Consider environmental effects.",
                },
                {
                    "id": "supporting_rule",
                    "title": "Supporting source applies",
                    "authority_source_record_id": "R1EA-002",
                    "applicability_mode": "baseline",
                    "authority_category": "regulation",
                    "severity": "medium",
                    "requirement": "Use supporting source.",
                },
            ],
        },
    )
    _write_json(
        templates,
        {
            "schema_version": "authority-family-rule-templates-v1",
            "base_rule_pack_id": "nepa-ea-v0",
            "base_rule_pack_version": "0.1.0",
            "templates": [
                {
                    "template_id": "active_family_template",
                    "rule_id": "active_family_template_rule",
                    "authority_family_id": "active_family",
                    "title": "Active family template",
                    "applicability_mode": "conditional",
                    "source_record_ids": ["R1EA-002"],
                    "supporting_source_record_ids": [],
                    "package_fact_types": ["action"],
                    "requirement": "Template requirement.",
                }
            ],
        },
    )
    _write_json(
        forest_profiles,
        {
            "schema_version": "forest-plan-profiles-v0",
            "profiles": [
                {
                    "forest_unit_id": "test-forest",
                    "forest_unit_names": ["Test Forest"],
                    "active_plan_source_record_id": "R1PLAN-001",
                    "required_readiness_source_roles": ["primary_land_management_plan"],
                    "supporting_source_record_ids_by_role": {
                        "primary_land_management_plan": {"source_record_id": "R1PLAN-001"}
                    },
                }
            ],
        },
    )
    return {
        "authority_inventory": authority_inventory,
        "rule_pack": rule_pack,
        "templates": templates,
        "forest_profiles": forest_profiles,
    }


def _catalog_row(
    source_set_id: str,
    source_record_id: str,
    title: str,
    source_status: str,
    *,
    document_role: str = "law",
) -> dict:
    return {
        "source_set_id": source_set_id,
        "source_record_id": source_record_id,
        "title": title,
        "source_status": source_status,
        "citation_label": f"{source_record_id} citation",
        "artifact_sha256": f"sha-{source_record_id}",
        "artifact_path": f"source_library/artifacts/raw/{source_record_id}.txt",
        "effective_url": f"https://example.test/{source_record_id}",
        "document_role": document_role,
        "authority_level": "federal",
        "scope": "Baseline",
        "issuer": "Test issuer",
        "review_topics": ["test topic"],
    }


def _currentness_report(source_set_id: str) -> dict:
    return {
        "schema_version": "authority-currentness-report-v0",
        "source_set_id": source_set_id,
        "created_at": "2026-05-06T00:00:00Z",
        "source_partition_contract": {
            "workbook_source_delta_plan": {
                "fsh_1909_15": "Add chapter records before claiming completeness."
            }
        },
        "summary": {"validation_passed": True},
        "validation": {"passed": True, "checks": []},
        "family_currentness": [
            _family_currentness("active_family", "active", "source_currentness_confirmed"),
            _family_currentness("candidate_family", "candidate", "documented_source_non_addition"),
            _family_currentness(
                "superseded_family",
                "superseded",
                "superseded_replacement_sources_confirmed",
            ),
        ],
        "catalog_source_partitions": [
            _catalog_partition("R1EA-001", "active_review_corpus"),
            _catalog_partition("R1EA-002", "active_review_corpus"),
            _catalog_partition("R1EA-003", "candidate_blocked_source"),
            _catalog_partition("R1EA-004", "currentness_supersession_archive"),
            _catalog_partition("R1PLAN-001", "active_review_corpus"),
        ],
        "source_currentness_records": [
            _source_currentness(source_set_id, "active_family", "active", "R1EA-001"),
            _source_currentness(source_set_id, "active_family", "active", "R1EA-002"),
            _source_currentness(
                source_set_id,
                "candidate_family",
                "candidate",
                "R1EA-003",
                source_partition="candidate_blocked_source",
                source_status="skipped_excluded",
                currentness_status="excluded_no_artifact",
                counts=False,
            ),
            _source_currentness(
                source_set_id,
                "superseded_family",
                "superseded",
                "R1EA-004",
                source_partition="currentness_supersession_archive",
                supersession_status="superseded_replacement_source",
                counts=False,
            ),
            _source_currentness(source_set_id, "active_family", "active", "R1PLAN-001"),
        ],
    }


def _family_currentness(family_id: str, family_status: str, currentness_status: str) -> dict:
    return {
        "schema_version": "authority-currentness-report-v0",
        "authority_family_id": family_id,
        "family_status": family_status,
        "currentness_status": currentness_status,
        "current_source_record_count": 1 if family_status == "active" else 0,
        "replacement_source_record_count": 1 if family_status == "superseded" else 0,
        "failed_source_record_count": 0,
    }


def _catalog_partition(source_record_id: str, source_partition: str) -> dict:
    return {
        "source_record_id": source_record_id,
        "source_partition": source_partition,
        "source_partition_basis": "test",
    }


def _source_currentness(
    source_set_id: str,
    family_id: str,
    family_status: str,
    source_record_id: str,
    *,
    source_partition: str = "active_review_corpus",
    source_status: str = "downloaded",
    currentness_status: str = "confirmed_from_catalog",
    supersession_status: str = "current_authoritative_source",
    counts: bool = True,
) -> dict:
    return {
        "schema_version": "authority-currentness-report-v0",
        "authority_family_id": family_id,
        "family_status": family_status,
        "source_record_id": source_record_id,
        "source_title": source_record_id,
        "citation_label": f"{source_record_id} citation",
        "url": f"https://example.test/{source_record_id}",
        "source_status": source_status,
        "source_partition": source_partition,
        "source_partition_basis": "test",
        "currentness_status": currentness_status,
        "supersession_status": supersession_status,
        "counts_as_current_authority": counts,
        "artifact_path": f"source_library/artifacts/raw/{source_record_id}.txt",
        "artifact_sha256": f"sha-{source_record_id}",
        "capture_date": "2026-05-06T00:00:00Z",
        "source_set_id": source_set_id,
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
