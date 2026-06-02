from __future__ import annotations

from typing import Any
import hashlib
import re

from .retrieval import query_retrieval_index


APPLICABILITY_RETRIEVAL_TRACE_SCHEMA_VERSION = "applicability-retrieval-trace-v0"
QUERY_TYPES_WITH_SOURCE_INDEX = {
    "exact_keyword",
    "bm25",
    "citation",
    "metadata_filter",
    "source_role",
    "authority_category",
}
PACKAGE_QUERY_TYPES = {"package_section", "graph_seed"}
RRF_K = 60


def _query_specs_for_candidate(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    contract = candidate.get("retrieval_contract")
    if not isinstance(contract, dict):
        contract = {}
    source_filters = _source_filters(candidate)
    package_filters = _package_filters(candidate)
    source_queries = _strings(contract.get("source_queries"))
    package_queries = _strings(contract.get("package_queries"))
    trigger_queries = _flatten_groups(candidate.get("positive_trigger_groups")) + _flatten_groups(
        candidate.get("negative_trigger_groups")
    )
    fallback_query = _candidate_fallback_query(candidate)
    source_query = _first(source_queries) or fallback_query
    package_query = _first(package_queries) or _first(trigger_queries) or fallback_query
    specs: list[dict[str, Any]] = [
        {
            "query_type": "exact_keyword",
            "query_text": source_query,
            "query_source": "retrieval_contract.source_queries",
            "source_filters": source_filters,
            "package_section_filters": package_filters,
        },
        {
            "query_type": "bm25",
            "query_text": source_query,
            "query_source": "retrieval_contract.source_queries",
            "source_filters": source_filters,
            "package_section_filters": package_filters,
        },
        {
            "query_type": "metadata_filter",
            "query_text": "",
            "query_source": "candidate.source_role_filters",
            "source_filters": source_filters,
            "package_section_filters": package_filters,
        },
        {
            "query_type": "source_role",
            "query_text": "",
            "query_source": "candidate.source_role_filters",
            "source_filters": source_filters,
            "package_section_filters": package_filters,
        },
        {
            "query_type": "authority_category",
            "query_text": str(candidate.get("authority_category") or ""),
            "query_source": "candidate.authority_category",
            "source_filters": source_filters,
            "package_section_filters": package_filters,
        },
        {
            "query_type": "citation",
            "query_text": _citation_query(candidate),
            "query_source": "candidate.source_records",
            "source_filters": source_filters,
            "package_section_filters": package_filters,
        },
        {
            "query_type": "package_section",
            "query_text": package_query,
            "query_source": "retrieval_contract.package_queries",
            "source_filters": source_filters,
            "package_section_filters": package_filters,
        },
        {
            "query_type": "graph_seed",
            "query_text": package_query,
            "query_source": "package_fact_graph",
            "source_filters": source_filters,
            "package_section_filters": package_filters,
        },
    ]
    allowed = set(_strings(contract.get("required_query_types"))) | {
        "citation",
        "authority_category",
        "graph_seed",
    }
    filtered = [spec for spec in specs if spec["query_type"] in allowed]
    return filtered or specs


def _execute_query_spec(
    *,
    applicability_run_id: str,
    review_id: str,
    source_set_id: str,
    candidate: dict[str, Any],
    query_spec: dict[str, Any],
    query_index: int,
    retrieval_index_path,
    searched_index_identity: dict[str, Any],
    source_results_cache: dict[tuple, list[dict[str, Any]]],
    package_fact_graph: dict[str, Any],
    package_graph_identity: dict[str, Any],
    package_results_cache: dict[tuple, list[tuple[float, dict[str, Any]]]],
    top_k: int,
    created_at: str,
    query_diagnostics: Any,
) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_authority_id") or "")
    query_plan_id = str(
        (candidate.get("retrieval_contract") or {}).get("query_plan_id")
        or f"retrieval-plan:{candidate_id}"
    )
    query_type = str(query_spec["query_type"])
    query_text = str(query_spec.get("query_text") or "")
    trace_id = _stable_id(
        "retrieval-trace",
        applicability_run_id,
        candidate_id,
        query_type,
        str(query_index),
        query_text,
    )
    if query_type in PACKAGE_QUERY_TYPES:
        results = _package_results(
            trace_id=trace_id,
            query_text=query_text,
            query_type=query_type,
            candidate=candidate,
            package_fact_graph=package_fact_graph,
            package_results_cache=package_results_cache,
            top_k=top_k,
        )
        searched_identity = package_graph_identity
    else:
        results = _source_results(
            trace_id=trace_id,
            query_text=query_text,
            query_type=query_type,
            query_spec=query_spec,
            retrieval_index_path=retrieval_index_path,
            source_results_cache=source_results_cache,
            top_k=top_k,
        )
        searched_identity = searched_index_identity
    return {
        "schema_version": APPLICABILITY_RETRIEVAL_TRACE_SCHEMA_VERSION,
        "trace_kind": "query_execution",
        "applicability_run_id": applicability_run_id,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "candidate_authority_id": candidate_id,
        "candidate_authority_type": candidate.get("candidate_authority_type"),
        "retrieval_trace_id": trace_id,
        "query_plan_id": query_plan_id,
        "query_text": query_text,
        "query_type": query_type,
        "query_terms": _tokenize(query_text),
        "query_timestamp": created_at,
        "query_source": query_spec.get("query_source"),
        "source_filters": query_spec.get("source_filters") or {},
        "package_section_filters": query_spec.get("package_section_filters") or {},
        "source_record_filters": (query_spec.get("source_filters") or {}).get(
            "source_record_ids",
            [],
        ),
        "authority_category_filters": (query_spec.get("source_filters") or {}).get(
            "authority_categories",
            [],
        ),
        "forest_plan_component_filters": _forest_plan_component_filters(candidate),
        "currentness_filters": _currentness_filters(candidate),
        "searched_index": searched_identity,
        "ranked_results": results,
        "fusion_metadata": None,
        "diagnostics": query_diagnostics(
            query_type=query_type,
            retrieval_index_path=retrieval_index_path,
            result_count=len(results),
        ),
    }


def _source_results(
    *,
    trace_id: str,
    query_text: str,
    query_type: str,
    query_spec: dict[str, Any],
    retrieval_index_path,
    source_results_cache: dict[tuple, list[dict[str, Any]]],
    top_k: int,
) -> list[dict[str, Any]]:
    if not retrieval_index_path.exists():
        return []
    source_filters = query_spec.get("source_filters") or {}
    source_record_ids = _strings(source_filters.get("source_record_ids"))
    document_roles = _strings(source_filters.get("document_roles"))
    authority_categories = _strings(source_filters.get("authority_categories"))
    source_record_id = _first(source_record_ids)
    document_role = _first(document_roles)
    authority_level = _first(authority_categories)
    citation = source_record_id if query_type == "citation" else None
    query_for_index = query_text
    if query_type in {"metadata_filter", "source_role", "citation"}:
        query_for_index = ""
    limit = max(top_k * 2, top_k)
    cache_key = (
        str(retrieval_index_path),
        query_for_index,
        limit,
        document_role,
        authority_level,
        source_record_id,
        citation,
    )
    hits = source_results_cache.get(cache_key)
    if hits is None:
        result = query_retrieval_index(
            index_path=retrieval_index_path,
            query=query_for_index,
            limit=limit,
            document_role=document_role,
            authority_level=authority_level,
            source_record_id=source_record_id,
            citation=citation,
        )
        hits = list(result["results"])
        source_results_cache[cache_key] = hits
    query_terms = _tokenize(query_text)
    return [
        _source_result_row(
            trace_id=trace_id,
            hit=hit,
            result_index=index,
            query_type=query_type,
            query_terms=query_terms,
            top_k=top_k,
        )
        for index, hit in enumerate(hits, start=1)
    ]


def _source_result_row(
    *,
    trace_id: str,
    hit: dict[str, Any],
    result_index: int,
    query_type: str,
    query_terms: list[str],
    top_k: int,
) -> dict[str, Any]:
    provenance = hit.get("provenance") or {}
    span = hit.get("evidence_span") or {}
    selected = result_index <= top_k
    result_id = _stable_id(
        "retrieval-result",
        trace_id,
        str(hit.get("chunk_id") or ""),
        str(result_index),
    )
    return {
        "result_id": result_id,
        "result_kind": "source_chunk",
        "rank": result_index,
        "score": hit.get("score"),
        "fused_score": None,
        "selected_status": "selected" if selected else "rejected",
        "rejection_reason": None if selected else "outside_top_k",
        "query_type": query_type,
        "source_record_id": hit.get("source_record_id"),
        "package_chunk_id": None,
        "source_chunk_id": hit.get("chunk_id"),
        "claim_id": None,
        "section_family": _section_family_from_hit(hit),
        "citation_label": hit.get("citation_label"),
        "page_label": _page_label(provenance.get("page")),
        "char_start": span.get("source_char_start"),
        "char_end": span.get("source_char_end"),
        "chunk_char_start": span.get("chunk_char_start"),
        "chunk_char_end": span.get("chunk_char_end"),
        "matched_terms": _matched_terms(query_terms, span.get("text") or ""),
        "text_hash": provenance.get("content_sha256"),
        "content_sha256": provenance.get("content_sha256"),
        "artifact_sha256": provenance.get("artifact_sha256"),
        "text_excerpt": span.get("text"),
        "provenance": provenance,
    }


def _package_results(
    *,
    trace_id: str,
    query_text: str,
    query_type: str,
    candidate: dict[str, Any],
    package_fact_graph: dict[str, Any],
    package_results_cache: dict[tuple, list[tuple[float, dict[str, Any]]]],
    top_k: int,
) -> list[dict[str, Any]]:
    score_context = _package_score_context(query_text=query_text, candidate=candidate)
    query_terms = list(score_context["query_terms"])
    cache_key = _package_results_cache_key(score_context)
    scored = package_results_cache.get(cache_key)
    if scored is None:
        scored = []
        for node in package_fact_graph.get("nodes") or []:
            if not isinstance(node, dict):
                continue
            node_type = str(node.get("node_type") or "")
            if node_type == "evidence_span":
                continue
            score = _score_package_node(node=node, score_context=score_context)
            if score <= 0:
                continue
            scored.append((score, node))
        scored.sort(
            key=lambda item: (
                -item[0],
                str(item[1].get("node_type") or ""),
                str(item[1].get("node_id") or ""),
            )
        )
        package_results_cache[cache_key] = scored
    results = []
    for index, (score, node) in enumerate(scored[: max(top_k * 2, top_k)], start=1):
        selected = index <= top_k
        results.append(
            {
                "result_id": _stable_id(
                    "retrieval-result",
                    trace_id,
                    str(node.get("node_id") or ""),
                    str(index),
                ),
                "result_kind": (
                    "package_section"
                    if node.get("node_type") == "package_section"
                    else "package_fact"
                ),
                "rank": index,
                "score": round(score, 6),
                "fused_score": None,
                "selected_status": "selected" if selected else "rejected",
                "rejection_reason": None if selected else "outside_top_k",
                "query_type": query_type,
                "source_record_id": None,
                "package_chunk_id": _first(_strings(node.get("package_chunk_ids"))),
                "source_chunk_id": None,
                "claim_id": None,
                "package_fact_node_id": node.get("node_id"),
                "section_family": node.get("section_family"),
                "citation_label": node.get("citation_label"),
                "page_label": node.get("page_label"),
                "char_start": node.get("char_start"),
                "char_end": node.get("char_end"),
                "chunk_char_start": node.get("chunk_char_start"),
                "chunk_char_end": node.get("chunk_char_end"),
                "matched_terms": _matched_terms(query_terms, _package_node_text(node)),
                "text_hash": node.get("text_hash") or node.get("content_sha256"),
                "content_sha256": node.get("content_sha256"),
                "artifact_sha256": node.get("artifact_sha256"),
                "text_excerpt": node.get("context_excerpt") or node.get("raw_value"),
                "provenance": {
                    "package_span_ids": node.get("package_span_ids")
                    or node.get("evidence_span_ids")
                    or [],
                    "evidence_span_ids": node.get("evidence_span_ids") or [],
                    "parser_provenance": node.get("parser_provenance") or {},
                    "section_ids": node.get("section_ids") or [],
                    "node_type": node.get("node_type"),
                    "fact_subtype": node.get("fact_subtype"),
                    "normalized_value": node.get("normalized_value"),
                    "confidence_class": node.get("confidence_class"),
                    "evidence_strength": node.get("evidence_strength"),
                },
            }
        )
    return results


def _fused_trace_row(
    *,
    applicability_run_id: str,
    review_id: str,
    source_set_id: str,
    candidate: dict[str, Any],
    trace_rows: list[dict[str, Any]],
    searched_index_identity: dict[str, Any],
    retrieval_index_path,
    top_k: int,
    created_at: str,
    query_diagnostics: Any,
) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_authority_id") or "")
    trace_id = _stable_id("retrieval-trace", applicability_run_id, candidate_id, "fused")
    fused: dict[str, dict[str, Any]] = {}
    input_sets = []
    for row in trace_rows:
        row_id = str(row["retrieval_trace_id"])
        result_ids = []
        for result in row.get("ranked_results") or []:
            result_key = _fusion_result_key(result)
            if result_key not in fused:
                fused[result_key] = {
                    **result,
                    "score": 0.0,
                    "fused_score": 0.0,
                    "input_result_ids": [],
                    "input_trace_ids": [],
                    "source_query_types": [],
                }
            fused[result_key]["fused_score"] += 1.0 / (RRF_K + int(result.get("rank") or 0))
            fused[result_key]["score"] = fused[result_key]["fused_score"]
            fused[result_key]["input_result_ids"].append(result["result_id"])
            fused[result_key]["input_trace_ids"].append(row_id)
            fused[result_key]["source_query_types"].append(row.get("query_type"))
            result_ids.append(result["result_id"])
        input_sets.append(
            {
                "retrieval_trace_id": row_id,
                "query_type": row.get("query_type"),
                "result_ids": result_ids,
            }
        )
    ranked = sorted(
        fused.values(),
        key=lambda item: (
            -float(item.get("fused_score") or 0),
            str(item.get("result_kind") or ""),
            str(item.get("source_record_id") or item.get("package_fact_node_id") or ""),
        ),
    )
    final_results = []
    for index, result in enumerate(ranked, start=1):
        selected = index <= top_k
        final_results.append(
            {
                **result,
                "result_id": _stable_id("retrieval-result", trace_id, _fusion_result_key(result)),
                "rank": index,
                "fused_score": round(float(result.get("fused_score") or 0), 6),
                "score": round(float(result.get("score") or 0), 6),
                "selected_status": "selected" if selected else "rejected",
                "rejection_reason": None if selected else "outside_top_k",
                "query_type": "fused",
                "input_result_ids": sorted(set(result.get("input_result_ids") or [])),
                "input_trace_ids": sorted(set(result.get("input_trace_ids") or [])),
                "source_query_types": sorted(
                    {str(value) for value in result.get("source_query_types") or []}
                ),
            }
        )
    return {
        "schema_version": APPLICABILITY_RETRIEVAL_TRACE_SCHEMA_VERSION,
        "trace_kind": "fused_result_set",
        "applicability_run_id": applicability_run_id,
        "review_id": review_id,
        "source_set_id": source_set_id,
        "candidate_authority_id": candidate_id,
        "candidate_authority_type": candidate.get("candidate_authority_type"),
        "retrieval_trace_id": trace_id,
        "query_plan_id": str(
            (candidate.get("retrieval_contract") or {}).get("query_plan_id")
            or f"retrieval-plan:{candidate_id}"
        ),
        "query_text": "",
        "query_type": "fused",
        "query_terms": [],
        "query_timestamp": created_at,
        "query_source": "reciprocal_rank_fusion",
        "source_filters": _source_filters(candidate),
        "package_section_filters": _package_filters(candidate),
        "source_record_filters": _strings(_source_filters(candidate).get("source_record_ids")),
        "authority_category_filters": _strings(
            _source_filters(candidate).get("authority_categories")
        ),
        "forest_plan_component_filters": _forest_plan_component_filters(candidate),
        "currentness_filters": _currentness_filters(candidate),
        "searched_index": searched_index_identity,
        "ranked_results": final_results,
        "fusion_metadata": {
            "fusion_strategy": "reciprocal_rank_fusion",
            "rrf_k": RRF_K,
            "input_result_sets": input_sets,
            "final_rank_order": [result["result_id"] for result in final_results],
        },
        "diagnostics": query_diagnostics(
            query_type="fused",
            retrieval_index_path=retrieval_index_path,
            result_count=len(final_results),
        ),
    }


def _score_package_node(
    *,
    node: dict[str, Any],
    score_context: dict[str, Any],
) -> float:
    text = str(node.get("_applicability_search_text") or _package_node_text(node).casefold())
    score = 0.0
    if node.get("node_type") in score_context["required_types"]:
        score += 2.0
    for term in score_context["query_terms"]:
        if term in text:
            score += 1.0
    if (
        score_context["section_families"]
        and node.get("section_family") in score_context["section_families"]
    ):
        score += 1.5
    for term in score_context["filter_terms"]:
        if term in text:
            score += 1.0
    if (
        node.get("node_type") == "package_section"
        and not score_context["query_terms"]
        and not score_context["filter_terms"]
    ):
        score += 0.1
    return score


def _prepare_package_fact_graph_search(package_fact_graph: dict[str, Any]) -> None:
    for node in package_fact_graph.get("nodes") or []:
        if isinstance(node, dict) and node.get("node_type") != "evidence_span":
            node["_applicability_search_text"] = _package_node_text(node).casefold()


def _package_score_context(*, query_text: str, candidate: dict[str, Any]) -> dict[str, Any]:
    package_filters = _package_filters(candidate)
    return {
        "query_terms": tuple(term.casefold() for term in _tokenize(query_text)),
        "required_types": frozenset(_strings(candidate.get("required_package_fact_types"))),
        "section_families": frozenset(
            _strings(package_filters.get("preferred_section_families"))
        ),
        "filter_terms": tuple(
            term.casefold()
            for term in (
                _strings(package_filters.get("package_section_terms"))
                + _strings(package_filters.get("package_terms"))
                + _strings(package_filters.get("package_evidence_terms"))
                + _strings(package_filters.get("resource_topics"))
                + _strings(package_filters.get("activity_tags"))
                + _strings(package_filters.get("geographic_area_ids"))
                + _strings(package_filters.get("management_area_ids"))
                + _strings(package_filters.get("overlay_ids"))
            )
        ),
    }


def _package_results_cache_key(score_context: dict[str, Any]) -> tuple:
    return (
        tuple(score_context["query_terms"]),
        tuple(sorted(score_context["required_types"])),
        tuple(sorted(score_context["section_families"])),
        tuple(score_context["filter_terms"]),
    )


def _package_node_matches_candidate(node: dict[str, Any], candidate: dict[str, Any]) -> bool:
    if node.get("node_type") in set(_strings(candidate.get("required_package_fact_types"))):
        return True
    text = str(node.get("_applicability_search_text") or _package_node_text(node).casefold())
    terms = (
        _strings(_package_filters(candidate).get("package_terms"))
        + _strings(_package_filters(candidate).get("package_section_terms"))
        + _strings(_package_filters(candidate).get("package_evidence_terms"))
        + _flatten_groups(candidate.get("positive_trigger_groups"))
        + _flatten_groups(candidate.get("negative_trigger_groups"))
    )
    return any(term.casefold() in text for term in terms)


def _package_node_text(node: dict[str, Any]) -> str:
    values = [
        node.get("label"),
        node.get("raw_value"),
        node.get("normalized_value"),
        node.get("fact_subtype"),
        node.get("section_family"),
        node.get("context_excerpt"),
        node.get("matched_text"),
    ]
    return " ".join(str(value or "") for value in values)


def _source_filters(candidate: dict[str, Any]) -> dict[str, Any]:
    filters = candidate.get("source_role_filters")
    if isinstance(filters, dict):
        return filters
    return {
        "source_record_ids": _strings(candidate.get("source_record_ids")),
        "document_roles": _strings([candidate.get("authority_document_role")]),
        "authority_categories": _strings([candidate.get("authority_category")]),
    }


def _package_filters(candidate: dict[str, Any]) -> dict[str, Any]:
    filters = candidate.get("package_section_filters")
    return filters if isinstance(filters, dict) else {}


def _forest_plan_component_filters(candidate: dict[str, Any]) -> dict[str, Any]:
    forest_plan = candidate.get("forest_plan")
    if not isinstance(forest_plan, dict):
        return {}
    return {
        "forest_unit_id": forest_plan.get("forest_unit_id"),
        "component_inventory_id": forest_plan.get("component_inventory_id"),
        "component_id": forest_plan.get("component_id"),
        "geographic_area_ids": forest_plan.get("geographic_area_ids") or [],
        "management_area_ids": forest_plan.get("management_area_ids") or [],
        "overlay_ids": forest_plan.get("overlay_ids") or [],
    }


def _currentness_filters(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "requires_current_source": bool(
            (candidate.get("required_source_evidence") or {}).get("requires_source_record")
        ),
        "source_evidence_availability": candidate.get("source_evidence_availability") or {},
    }


def _candidate_fallback_query(candidate: dict[str, Any]) -> str:
    rule_template = candidate.get("rule_template")
    if isinstance(rule_template, dict):
        return " ".join(
            _strings(
                [
                    rule_template.get("title"),
                    rule_template.get("question"),
                    rule_template.get("requirement"),
                    rule_template.get("rule_id"),
                ]
            )
        )
    forest_plan = candidate.get("forest_plan")
    if isinstance(forest_plan, dict):
        return " ".join(
            _strings([forest_plan.get("section_heading"), forest_plan.get("component_id")])
        )
    return str(candidate.get("candidate_authority_id") or "")


def _citation_query(candidate: dict[str, Any]) -> str:
    for record in candidate.get("source_records") or []:
        if isinstance(record, dict):
            value = str(
                record.get("citation_label")
                or record.get("source_record_id")
                or record.get("title")
                or ""
            ).strip()
            if value:
                return value
    return _first(_strings(candidate.get("source_record_ids"))) or _candidate_fallback_query(
        candidate
    )


def _fusion_result_key(result: dict[str, Any]) -> str:
    return "|".join(
        [
            str(result.get("result_kind") or ""),
            str(result.get("source_chunk_id") or ""),
            str(result.get("package_fact_node_id") or ""),
            str(result.get("package_chunk_id") or ""),
            str(result.get("claim_id") or ""),
        ]
    )


def _section_family_from_hit(hit: dict[str, Any]) -> str | None:
    provenance = hit.get("provenance") or {}
    heading = str(provenance.get("heading") or "").lower()
    section = str(provenance.get("section") or "").lower()
    text = f"{section} {heading}"
    if "purpose" in text and "need" in text:
        return "purpose_need"
    if "alternative" in text:
        return "alternatives"
    if "consult" in text:
        return "consultation"
    if "decision" in text or "finding" in text:
        return "finding_decision"
    return section or heading or None


def _page_label(value: object) -> str | None:
    if value is None or str(value).strip() == "":
        return None
    return str(value)


def _matched_terms(terms: list[str], text: str) -> list[str]:
    lower = str(text or "").lower()
    return sorted({term for term in terms if term.lower() in lower})


def _tokenize(text: str) -> list[str]:
    return [
        value.lower()
        for value in re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]{1,}", text)
        if len(value) > 1
    ]


def _strings(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, dict):
        return []
    if isinstance(value, (list, tuple, set)):
        values: list[str] = []
        for item in value:
            values.extend(_strings(item))
        return values
    text = str(value).strip()
    return [text] if text else []


def _flatten_groups(value: object) -> list[str]:
    return _strings(value)


def _first(values: list[str]) -> str | None:
    return values[0] if values else None


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    readable = re.sub(r"[^A-Za-z0-9_.-]+", "-", "-".join(parts[:2])).strip("-")
    readable = readable[:80].strip("-") or prefix
    return f"{prefix}:{readable}:{digest}"
