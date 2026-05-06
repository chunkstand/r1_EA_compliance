from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VIEWER_ROOT = REPO_ROOT / "viewer" / "nepa-3d"


def test_nepa_3d_viewer_manifest_points_to_source_set_and_review_exports() -> None:
    manifest = json.loads((VIEWER_ROOT / "manifest.json").read_text())

    assert manifest["schema_version"] == "nepa-3d-viewer-manifest-v1"
    assert manifest["runtime"]["graph_runtime"] == "3d-force-graph"
    assert manifest["default_source_set_id"] == "source-set-ba8d0feae79501b8"
    assert manifest["default_review_id"] is None

    datasets = {dataset["dataset_id"]: dataset for dataset in manifest["datasets"]}
    source_set = datasets["source-set-ba8d0feae79501b8"]
    review = datasets["v1-cg-ecid-compliance-review"]

    assert manifest["runtime"]["three_runtime_url"].endswith("three@0.149.0/build/three.min.js")
    assert manifest["runtime"]["graph_runtime_url"].endswith(
        "3d-force-graph@1.76.0/dist/3d-force-graph.min.js"
    )
    assert source_set["scope"] == "source_set"
    assert source_set["review_id"] is None
    assert source_set["graph_path"].startswith("../../source_library/")
    assert source_set["graph_path"].endswith(
        "source_library/derived/source-set-ba8d0feae79501b8/knowledge_graph/nepa_3d_graph.json"
    )
    assert review["scope"] == "review_overlay"
    assert review["source_set_id"] == source_set["source_set_id"]
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
        "lens-select",
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
        "detail-panel",
        "validation-panel",
        "legend",
    }

    assert required_ids <= parser.ids
    assert any("three@" in src for src in parser.script_srcs)
    assert any("3d-force-graph" in src for src in parser.script_srcs)
    assert "app.js" in parser.script_srcs


def test_nepa_3d_viewer_app_preserves_milestone_controls_and_readiness_boundary() -> None:
    script = (VIEWER_ROOT / "app.js").read_text()

    for required in [
        "ForceGraph3D",
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
