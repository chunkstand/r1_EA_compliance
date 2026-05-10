from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VIEWER_ROOT = REPO_ROOT / "viewer" / "nepa-3d"


def test_nepa_3d_viewer_manifest_lists_graph_capable_fallback_exports() -> None:
    manifest = json.loads((VIEWER_ROOT / "manifest.json").read_text())

    assert manifest["schema_version"] == "nepa-3d-viewer-manifest-v1"
    assert manifest["runtime"]["graph_runtime"] == "3d-force-graph"
    assert manifest["default_source_set_id"] == "source-set-8a4005c8a083af1a"
    assert manifest["default_review_id"] is None

    datasets = {dataset["dataset_id"]: dataset for dataset in manifest["datasets"]}
    current_fallback = datasets["source-set-8a4005c8a083af1a"]
    source_delta = datasets["source-set-7e2652d23e764068"]
    promoted_v1 = datasets["source-set-ba8d0feae79501b8"]
    review = datasets["v1-cg-ecid-compliance-review"]

    assert manifest["runtime"]["three_runtime_url"].endswith("three@0.149.0/build/three.min.js")
    assert manifest["runtime"]["graph_runtime_url"].endswith(
        "3d-force-graph@1.76.0/dist/3d-force-graph.min.js"
    )
    for source_set_id, dataset in [
        ("source-set-8a4005c8a083af1a", current_fallback),
        ("source-set-7e2652d23e764068", source_delta),
        ("source-set-ba8d0feae79501b8", promoted_v1),
    ]:
        assert dataset["scope"] == "source_set"
        assert dataset["source_set_id"] == source_set_id
        assert dataset["review_id"] is None
        assert dataset["graph_path"].startswith("../../source_library/")
        assert dataset["graph_path"].endswith(
            f"source_library/derived/{source_set_id}/knowledge_graph/nepa_3d_graph.json"
        )
        assert dataset["summary_path"].endswith(
            f"source_library/derived/{source_set_id}/knowledge_graph/nepa_3d_graph_summary.json"
        )
        assert dataset["validation_path"].endswith(
            f"source_library/derived/{source_set_id}/knowledge_graph/nepa_3d_graph_validation.json"
        )

    assert review["scope"] == "review_overlay"
    assert review["source_set_id"] == promoted_v1["source_set_id"]
    assert review["review_id"] == "v1-cg-ecid-compliance-review"
    assert review["graph_path"].startswith("../../source_library/")
    assert review["graph_path"].endswith(
        "source_library/reviews/v1-cg-ecid-compliance-review/knowledge_graph/nepa_3d_graph.json"
    )


def test_nepa_3d_viewer_has_required_controls_and_runtime_hook() -> None:
    parser = _IdParser()
    parser.feed((VIEWER_ROOT / "index.html").read_text())

    required_ids = {
        "source-set-select",
        "review-select",
        "graph-file-input",
        "demo-reset",
        "demo-scenes",
        "lens-select",
        "show-node-labels",
        "advanced-filters",
        "graph-search",
        "status-filter",
        "authority-category-filter",
        "authority-family-filter",
        "document-role-filter",
        "currentness-filter",
        "blocker-filter",
        "node-edge-type-filter",
        "evidence-kind-filter",
        "forest-unit-filter",
        "review-phase-filter",
        "neighbor-depth",
        "degree-threshold",
        "hide-high-degree",
        "pin-selected",
        "fit-graph",
        "reset-layout",
        "clear-filters",
        "export-shot",
        "export-state",
        "graph-root",
        "graph-scene-label",
        "capability-panel",
        "viewer-shell",
        "detail-rail",
        "detail-rail-toggle",
        "detail-panel",
        "validation-panel",
        "legend",
    }

    assert required_ids <= parser.ids
    assert any("three@" in src for src in parser.script_srcs)
    assert any("3d-force-graph" in src for src in parser.script_srcs)
    assert any(src.startswith("app.js") for src in parser.script_srcs)


def test_nepa_3d_viewer_app_preserves_milestone_controls_and_readiness_boundary() -> None:
    script = (VIEWER_ROOT / "app.js").read_text()

    for required in [
        "ForceGraph3D",
        "DEFAULT_DEMO_REVIEW_ID",
        "DEMO_START_SCENE_ID",
        "DEMO_SCENES",
        "v1-cg-ecid-compliance-review",
        "authority_currentness",
        "forest_plan",
        "package_applicability",
        "evidence_path",
        "readiness_blockers",
        "difference_view",
        "authorityCategory",
        "authorityFamily",
        "documentRole",
        "currentness",
        "readinessBlocker",
        "nodeEdgeType",
        "evidenceKind",
        "forestUnit",
        "reviewPhase",
        "applyDemoScene",
        "buildEvidencePathSpotlight",
        "spotlightNodeIds",
        "renderCapabilityPanel",
        "buildLabelPlan",
        "graphNodeObject",
        "makeTextSprite",
        "updateLabelVisibility",
        "CATALOG_SOURCE_SET_MANIFEST_PATH",
        "DERIVED_SOURCE_SETS_ROOT_PATH",
        "REVIEWS_ROOT_PATH",
        "resolveCurrentViewerManifest",
        "discoverGraphSourceSetDatasets",
        "discoverReviewDatasets",
        "listDirectoryNames",
        "fetchJsonOrNull",
        "LABEL_NODE_BUDGETS",
        "label_zoom_tier",
        "clearFilters",
        "exportScreenshot",
        "exportViewerState",
        "__NEPA_3D_VIEWER_READY__",
    ]:
        assert required in script

    assert '.nodeId("node_id")' in script
    assert "source: edge.source_node_id" in script
    assert "target: edge.target_node_id" in script
    assert "CONTEXT_SEED_FILTER_IDS = new Set(FILTER_DEFINITIONS.map((filter) => filter.id))" in script
    assert "matchingContextFilterSeedGroups" in script
    assert "baseLensGraph" in script
    assert "displayLensGraph" in script
    assert "filterOptionCounts" in script
    assert "new DOMParser()" in script
    assert 'lens?.lens_id === "all" || edgeNodeIds.size === 0' in script
    assert '"artifact hash"' in script
    assert '"artifact path"' in script
    assert "validation_passed" in script
    assert "Viewer layout does not change readiness" in script


def test_nepa_3d_viewer_filter_categories_are_not_overloaded() -> None:
    script = (VIEWER_ROOT / "app.js").read_text()
    html = (VIEWER_ROOT / "index.html").read_text()

    authority_category = _function_body(script, "authorityCategoryValues")
    authority_family = _function_body(script, "authorityFamilyValues")
    forest_unit = _function_body(script, "forestUnitValues")
    node_edge_type = _function_body(script, "nodeEdgeTypeValues")
    evidence_kind = _function_body(script, "evidenceKindValues")

    assert "authority_family_id" not in authority_category
    assert "authority_family_id" in authority_family
    assert "forest_code" in forest_unit
    assert "item.node_type || item.edge_type" in node_edge_type
    assert "item.node_type || item.edge_type" not in evidence_kind
    assert "currentness_metadata?.basis_type" in evidence_kind
    assert "Node / edge type" in html
    assert "Evidence / basis" in html
    assert "Capability shown" in html
    assert "graph-scene-label" in html
    assert "Advanced filters" in html
    assert "Status / readiness" in html
    assert "Currentness / partition" in html
    assert "Clear filters" in html
    assert "dataset.grounding" in script
    assert "lensGraph(lens)" in script


def test_nepa_3d_viewer_styles_define_desktop_and_mobile_graph_surfaces() -> None:
    styles = (VIEWER_ROOT / "styles.css").read_text()

    assert ".viewer-shell" in styles
    assert ".graph-root" in styles
    assert ".detail-rail" in styles
    assert ".graph-scene-label" in styles
    assert ".demo-scenes" in styles
    assert ".advanced-filters" in styles
    assert ".capability-panel" in styles
    assert ".path-step" in styles
    assert ".filter-actions" in styles
    assert "@media (max-width: 1020px)" in styles
    assert "@media (max-width: 620px)" in styles


def _function_body(script: str, function_name: str) -> str:
    marker = f"function {function_name}"
    start = script.index(marker)
    next_function = script.find("\nfunction ", start + len(marker))
    if next_function == -1:
        return script[start:]
    return script[start:next_function]


class _IdParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.script_srcs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if "id" in attrs_dict and attrs_dict["id"]:
            self.ids.add(attrs_dict["id"])
        if tag == "script" and attrs_dict.get("src"):
            self.script_srcs.append(attrs_dict["src"])
