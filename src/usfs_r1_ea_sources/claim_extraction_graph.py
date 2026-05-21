from __future__ import annotations

from collections import Counter, defaultdict
from contextlib import closing
from datetime import UTC, datetime
import hashlib
import json
import re
import sqlite3
from pathlib import Path


CLAIM_GRAPH_SCHEMA_VERSION = "source-claim-graph-v0"


def build_entity_records(
    claims: list[dict],
    *,
    extractor_name: str,
    extractor_version: str,
) -> list[dict]:
    entities: dict[str, dict] = {}
    mention_claims: defaultdict[str, set[str]] = defaultdict(set)
    mention_sources: defaultdict[str, set[str]] = defaultdict(set)
    mention_citations: defaultdict[str, set[str]] = defaultdict(set)
    mention_counts: Counter[str] = Counter()
    for claim in claims:
        for entity_type, label in _extract_entities(str(claim["claim_text"])):
            entity_id = _entity_id(entity_type, label)
            entities.setdefault(
                entity_id,
                {
                    "entity_id": entity_id,
                    "entity_type": entity_type,
                    "label": label,
                    "normalized_label": _normalize_entity_label(label),
                },
            )
            mention_claims[entity_id].add(str(claim["claim_id"]))
            mention_sources[entity_id].add(str(claim["source_record_id"]))
            if claim.get("citation_label"):
                mention_citations[entity_id].add(str(claim["citation_label"]))
            mention_counts[entity_id] += 1
    records = []
    for entity_id, entity in entities.items():
        records.append(
            {
                **entity,
                "source_set_id": claims[0]["source_set_id"] if claims else None,
                "claim_ids": sorted(mention_claims[entity_id]),
                "source_record_ids": sorted(mention_sources[entity_id]),
                "citation_labels": sorted(mention_citations[entity_id]),
                "mention_count": mention_counts[entity_id],
                "extractor_name": extractor_name,
                "extractor_version": extractor_version,
            }
        )
    return sorted(records, key=lambda entity: (entity["entity_type"], entity["label"]))


def build_claim_graph_records(
    *,
    source_set_id: str,
    claims: list[dict],
    entities: list[dict],
) -> tuple[list[dict], list[dict]]:
    nodes_by_id: dict[str, dict] = {}
    edges_by_id: dict[str, dict] = {}
    source_set_node_id = f"source_set:{source_set_id}"
    nodes_by_id[source_set_node_id] = _node(
        source_set_node_id,
        "SourceSet",
        source_set_id=source_set_id,
    )
    entities_by_id = {entity["entity_id"]: entity for entity in entities}
    entity_ids_by_claim: defaultdict[str, list[str]] = defaultdict(list)
    for entity in entities:
        for claim_id in entity.get("claim_ids", []):
            entity_ids_by_claim[str(claim_id)].append(str(entity["entity_id"]))
            nodes_by_id.setdefault(
                str(entity["entity_id"]),
                _node(
                    str(entity["entity_id"]),
                    "Entity",
                    entity_type=entity["entity_type"],
                    label=entity["label"],
                    normalized_label=entity["normalized_label"],
                    mention_count=entity["mention_count"],
                ),
            )

    for claim in claims:
        source_node_id = f"source:{claim['source_record_id']}"
        chunk_node_id = str(claim["chunk_id"])
        claim_node_id = str(claim["claim_id"])
        authority_node_id = _authority_node_id(str(claim["authority_level"]))
        evidence_node_id = _claim_evidence_span_node_id(claim)
        nodes_by_id.setdefault(
            source_node_id,
            _node(
                source_node_id,
                "SourceDocument",
                source_set_id=source_set_id,
                source_record_id=claim["source_record_id"],
                title=claim.get("title"),
                document_role=claim.get("document_role"),
                authority_level=claim.get("authority_level"),
                citation_label=claim.get("citation_label"),
            ),
        )
        nodes_by_id.setdefault(
            chunk_node_id,
            _node(
                chunk_node_id,
                "DocumentChunk",
                chunk_id=chunk_node_id,
                source_record_id=claim["source_record_id"],
                chunk_index=claim.get("chunk_index"),
                chunk_content_sha256=claim.get("chunk_content_sha256"),
            ),
        )
        nodes_by_id.setdefault(
            authority_node_id,
            _node(
                authority_node_id,
                "Authority",
                authority_level=claim["authority_level"],
            ),
        )
        nodes_by_id[claim_node_id] = _node(
            claim_node_id,
            "Claim",
            claim_id=claim_node_id,
            source_record_id=claim["source_record_id"],
            chunk_id=chunk_node_id,
            claim_type=claim["claim_type"],
            claim_text=claim["claim_text"],
            citation_label=claim["citation_label"],
            source_char_start=claim["source_char_start"],
            source_char_end=claim["source_char_end"],
            content_sha256=claim["content_sha256"],
            extractor_version=claim["extractor_version"],
            validation_status=claim["validation_status"],
        )
        nodes_by_id[evidence_node_id] = _node(
            evidence_node_id,
            "ClaimEvidenceSpan",
            claim_id=claim_node_id,
            chunk_id=chunk_node_id,
            source_record_id=claim["source_record_id"],
            citation_label=claim["citation_label"],
            text=claim["claim_text"],
            chunk_char_start=claim["chunk_char_start"],
            chunk_char_end=claim["chunk_char_end"],
            source_char_start=claim["source_char_start"],
            source_char_end=claim["source_char_end"],
            content_sha256=claim["content_sha256"],
        )
        _put_edge(edges_by_id, source_set_node_id, source_node_id, "SOURCE_SET_HAS_SOURCE")
        _put_edge(edges_by_id, source_node_id, chunk_node_id, "SOURCE_HAS_CHUNK")
        _put_edge(edges_by_id, chunk_node_id, claim_node_id, "CHUNK_HAS_CLAIM")
        _put_edge(edges_by_id, claim_node_id, evidence_node_id, "CLAIM_HAS_EVIDENCE_SPAN")
        _put_edge(edges_by_id, evidence_node_id, chunk_node_id, "CLAIM_EVIDENCE_FROM_CHUNK")
        _put_edge(edges_by_id, claim_node_id, authority_node_id, "CLAIM_HAS_AUTHORITY")
        _put_edge(edges_by_id, source_node_id, authority_node_id, "SOURCE_HAS_AUTHORITY")
        for topic in claim.get("review_topics", []):
            topic_node_id = _topic_node_id(str(topic))
            nodes_by_id.setdefault(
                topic_node_id,
                _node(topic_node_id, "ReviewTopic", label=str(topic)),
            )
            _put_edge(edges_by_id, claim_node_id, topic_node_id, "CLAIM_SUPPORTS_REVIEW_TOPIC")
        for entity_id in entity_ids_by_claim.get(claim_node_id, []):
            if entity_id in entities_by_id:
                _put_edge(edges_by_id, claim_node_id, entity_id, "CLAIM_MENTIONS_ENTITY")
    return list(nodes_by_id.values()), list(edges_by_id.values())


def write_sqlite_graph(
    path: Path,
    *,
    source_set_id: str,
    claims: list[dict],
    entities: list[dict],
    nodes: list[dict],
    edges: list[dict],
    metrics: dict,
) -> None:
    if path.exists():
        path.unlink()
    with closing(sqlite3.connect(path)) as connection:
        connection.executescript(
            """
            CREATE TABLE metadata (
              key TEXT PRIMARY KEY,
              value_json TEXT NOT NULL
            );

            CREATE TABLE claims (
              claim_id TEXT PRIMARY KEY,
              source_set_id TEXT NOT NULL,
              source_record_id TEXT NOT NULL,
              chunk_id TEXT NOT NULL,
              claim_type TEXT NOT NULL,
              citation_label TEXT NOT NULL,
              source_char_start INTEGER NOT NULL,
              source_char_end INTEGER NOT NULL,
              content_sha256 TEXT NOT NULL,
              payload_json TEXT NOT NULL
            );

            CREATE TABLE entities (
              entity_id TEXT PRIMARY KEY,
              entity_type TEXT NOT NULL,
              label TEXT NOT NULL,
              payload_json TEXT NOT NULL
            );

            CREATE TABLE graph_nodes (
              id TEXT PRIMARY KEY,
              type TEXT NOT NULL,
              payload_json TEXT NOT NULL
            );

            CREATE TABLE graph_edges (
              id TEXT PRIMARY KEY,
              source TEXT NOT NULL,
              target TEXT NOT NULL,
              relationship TEXT NOT NULL,
              payload_json TEXT NOT NULL
            );

            CREATE INDEX idx_claims_source_record_id ON claims(source_record_id);
            CREATE INDEX idx_claims_chunk_id ON claims(chunk_id);
            CREATE INDEX idx_claims_claim_type ON claims(claim_type);
            CREATE INDEX idx_entities_entity_type ON entities(entity_type);
            CREATE INDEX idx_claim_graph_edges_source ON graph_edges(source);
            CREATE INDEX idx_claim_graph_edges_target ON graph_edges(target);
            CREATE INDEX idx_claim_graph_edges_relationship ON graph_edges(relationship);
            """
        )
        metadata = {
            "schema_version": CLAIM_GRAPH_SCHEMA_VERSION,
            "source_set_id": source_set_id,
            "created_at": _utc_now(),
            "claim_count": len(claims),
            "entity_count": len(entities),
            "node_count": len(nodes),
            "edge_count": len(edges),
            "metrics": metrics,
        }
        for key, value in metadata.items():
            connection.execute(
                "INSERT INTO metadata VALUES (?, ?)",
                (key, json.dumps(value, sort_keys=True)),
            )
        for claim in claims:
            connection.execute(
                """
                INSERT INTO claims VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    claim["claim_id"],
                    claim["source_set_id"],
                    claim["source_record_id"],
                    claim["chunk_id"],
                    claim["claim_type"],
                    claim["citation_label"],
                    int(claim["source_char_start"]),
                    int(claim["source_char_end"]),
                    claim["content_sha256"],
                    json.dumps(claim, sort_keys=True),
                ),
            )
        for entity in entities:
            connection.execute(
                "INSERT INTO entities VALUES (?, ?, ?, ?)",
                (
                    entity["entity_id"],
                    entity["entity_type"],
                    entity["label"],
                    json.dumps(entity, sort_keys=True),
                ),
            )
        for node in nodes:
            connection.execute(
                "INSERT INTO graph_nodes VALUES (?, ?, ?)",
                (node["id"], node["type"], json.dumps(node, sort_keys=True)),
            )
        for edge in edges:
            connection.execute(
                "INSERT INTO graph_edges VALUES (?, ?, ?, ?, ?)",
                (
                    edge["id"],
                    edge["source"],
                    edge["target"],
                    edge["relationship"],
                    json.dumps(edge, sort_keys=True),
                ),
            )
        connection.commit()


def sqlite_graph_checks(
    path: Path,
    *,
    expected_claim_count: int,
    expected_entity_count: int,
    expected_node_count: int,
    expected_edge_count: int,
) -> list[dict]:
    if not path.exists():
        return [
            {
                "name": "claim_sqlite_graph_exists",
                "passed": False,
                "details": {"path": str(path)},
            }
        ]
    try:
        with closing(sqlite3.connect(path)) as connection:
            claim_count = connection.execute("SELECT COUNT(*) FROM claims").fetchone()[0]
            entity_count = connection.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
            node_count = connection.execute("SELECT COUNT(*) FROM graph_nodes").fetchone()[0]
            edge_count = connection.execute("SELECT COUNT(*) FROM graph_edges").fetchone()[0]
    except sqlite3.Error as error:
        return [
            {
                "name": "claim_sqlite_graph_readable",
                "passed": False,
                "details": {"path": str(path), "error": str(error)},
            }
        ]
    return [
        {
            "name": "claim_sqlite_graph_exists",
            "passed": True,
            "details": {"path": str(path)},
        },
        {
            "name": "claim_sqlite_claim_count_matches_jsonl",
            "passed": claim_count == expected_claim_count,
            "details": {"expected": expected_claim_count, "actual": claim_count},
        },
        {
            "name": "claim_sqlite_entity_count_matches_jsonl",
            "passed": entity_count == expected_entity_count,
            "details": {"expected": expected_entity_count, "actual": entity_count},
        },
        {
            "name": "claim_sqlite_node_count_matches_jsonl",
            "passed": node_count == expected_node_count,
            "details": {"expected": expected_node_count, "actual": node_count},
        },
        {
            "name": "claim_sqlite_edge_count_matches_jsonl",
            "passed": edge_count == expected_edge_count,
            "details": {"expected": expected_edge_count, "actual": edge_count},
        },
    ]


def _extract_entities(text: str) -> list[tuple[str, str]]:
    entities: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for entity_type, regex in (
        ("legal_citation", LEGAL_CITATION_RE),
        ("section_reference", SECTION_RE),
        ("acronym", ACRONYM_RE),
        ("named_actor", CAPITALIZED_PHRASE_RE),
    ):
        for match in regex.finditer(text):
            label = match.group(0).strip(" ,.;:()[]{}\"'")
            if len(label) < 2:
                continue
            key = (entity_type, _normalize_entity_label(label))
            if key in seen:
                continue
            seen.add(key)
            entities.append((entity_type, label))
    return entities


def _entity_id(entity_type: str, label: str) -> str:
    material = f"{entity_type}|{_normalize_entity_label(label)}"
    return f"entity:{hashlib.sha256(material.encode('utf-8')).hexdigest()[:24]}"


def _claim_evidence_span_node_id(claim: dict) -> str:
    material = "|".join(
        [
            str(claim["claim_id"]),
            str(claim["chunk_id"]),
            str(claim["source_char_start"]),
            str(claim["source_char_end"]),
            str(claim["content_sha256"]),
        ]
    )
    return f"claim_evidence_span:{hashlib.sha256(material.encode('utf-8')).hexdigest()[:24]}"


def _authority_node_id(authority_level: str) -> str:
    return f"authority:{_slug(authority_level)}"


def _topic_node_id(topic: str) -> str:
    return f"review_topic:{_slug(topic)}"


def _node(node_id: str, node_type: str, **properties: object) -> dict:
    return {"id": node_id, "type": node_type, **properties}


def _edge(source: str, target: str, relationship: str) -> dict:
    return {
        "id": _edge_id(source, target, relationship),
        "source": source,
        "target": target,
        "relationship": relationship,
    }


def _put_edge(edges_by_id: dict[str, dict], source: str, target: str, relationship: str) -> None:
    edge = _edge(source, target, relationship)
    edges_by_id[edge["id"]] = edge


def _edge_id(source: str, target: str, relationship: str) -> str:
    material = f"{source}|{relationship}|{target}"
    return f"edge:{hashlib.sha256(material.encode('utf-8')).hexdigest()[:32]}"


def _slug(value: str, *, max_length: int = 80) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        slug = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    return slug[:max_length]


def _normalize_entity_label(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().lower()


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


LEGAL_CITATION_RE = re.compile(
    r"\b\d+\s+(?:CFR|U\.S\.C\.|USC)\s*(?:part|section|sec\.)?\s*[\w.:-]*",
    re.I,
)
SECTION_RE = re.compile(r"(?:\u00a7|section|sec\.)\s*[\w.:-]+", re.I)
ACRONYM_RE = re.compile(r"\b[A-Z][A-Z0-9&]{2,}\b")
CAPITALIZED_PHRASE_RE = re.compile(
    r"\b[A-Z][a-z][A-Za-z&'-]*(?:\s+[A-Z][a-z][A-Za-z&'-]*){1,5}\b"
)

