from __future__ import annotations

from pathlib import Path
import json
import tempfile

from usfs_r1_ea_sources.evidence_graph import build_evidence_graph
from usfs_r1_ea_sources.evidence_graph_validation import validate_evidence_graph_outputs
from usfs_r1_ea_sources.retrieval import build_retrieval_index

from tests.support.phase_eval_fixtures import check
from tests.support.phase_eval_fixtures import chunk
from tests.support.phase_eval_fixtures import read_jsonl
from tests.support.phase_eval_fixtures import write_catalog_sqlite
from tests.support.phase_eval_fixtures import write_catalog_validation
from tests.support.phase_eval_fixtures import write_chunks
from tests.support.phase_eval_fixtures import write_extraction_diagnostics
from tests.support.phase_eval_fixtures import write_jsonl


def test_evidence_graph_validation_rejects_dangling_edges_and_missing_chunk_node() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        source_set_id, result = _build_graph_fixture(output_dir)
        nodes = read_jsonl(result.nodes_path)
        chunk_node_id = next(node["id"] for node in nodes if node["type"] == "DocumentChunk")
        nodes = [node for node in nodes if node["id"] != chunk_node_id]
        write_jsonl(result.nodes_path, nodes)

        validation = validate_evidence_graph_outputs(
            output_dir=output_dir,
            source_set_id=source_set_id,
        )

        assert not validation["passed"]
        assert not check(validation, "every_chunk_has_graph_node")["passed"]
        assert not check(validation, "edges_resolve_to_existing_nodes")["passed"]


def test_evidence_graph_validation_rejects_tampered_evidence_span_content() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        source_set_id, result = _build_graph_fixture(output_dir)
        nodes = read_jsonl(result.nodes_path)
        evidence_span = next(node for node in nodes if node["type"] == "EvidenceSpan")
        evidence_span["text"] = "Tampered evidence span text."
        evidence_span["content_sha256"] = "tampered"
        write_jsonl(result.nodes_path, nodes)

        validation = validate_evidence_graph_outputs(
            output_dir=output_dir,
            source_set_id=source_set_id,
        )

        assert not validation["passed"]
        assert not check(validation, "evidence_span_content_matches_chunks")["passed"]


def test_evidence_graph_validation_rejects_missing_review_topic_edge() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output_dir = Path(tmp)
        source_set_id, result = _build_graph_fixture(output_dir)
        edges = read_jsonl(result.edges_path)
        edges = [
            edge
            for edge in edges
            if edge["relationship"] != "CHUNK_SUPPORTS_REVIEW_TOPIC"
        ]
        write_jsonl(result.edges_path, edges)

        validation = validate_evidence_graph_outputs(
            output_dir=output_dir,
            source_set_id=source_set_id,
        )

        assert not validation["passed"]
        assert not check(validation, "every_chunk_has_review_topic_edge")["passed"]


def _build_graph_fixture(output_dir: Path) -> tuple[str, object]:
    source_set_id = "source-set-test"
    write_catalog_validation(output_dir, passed=True)
    write_extraction_diagnostics(
        output_dir,
        source_set_id,
        source_record_ids=["R1EA-001"],
    )
    write_chunks(
        output_dir,
        source_set_id,
        [
            chunk(
                source_set_id=source_set_id,
                source_record_id="R1EA-001",
                title="NEPA regulations",
                document_role="regulation",
                authority_level="federal_regulation",
                citation_label="R1EA-001 | NEPA regulations | artifact abc123",
                text="Agencies shall consider alternatives and environmental effects.",
            )
        ],
    )
    write_catalog_sqlite(output_dir, {"R1EA-001": ["NEPA alternatives"]})
    build_retrieval_index(output_dir=output_dir, source_set_id=source_set_id)
    result = build_evidence_graph(output_dir=output_dir, source_set_id=source_set_id)
    assert result.summary["validation_passed"]
    assert result.summary["reviewer_ready"]
    validation = json.loads(result.validation_path.read_text(encoding="utf-8"))
    assert validation["passed"]
    return source_set_id, result
