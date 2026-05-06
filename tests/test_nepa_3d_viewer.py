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

    assert source_set["scope"] == "source_set"
    assert source_set["review_id"] is None
    assert source_set["graph_path"].endswith(
        "source_library/derived/source-set-ba8d0feae79501b8/knowledge_graph/nepa_3d_graph.json"
    )
    assert review["scope"] == "review_overlay"
    assert review["source_set_id"] == source_set["source_set_id"]
    assert review["review_id"] == "v1-cg-ecid-compliance-review"
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
        "document-role-filter",
        "currentness-filter",
        "blocker-filter",
        "evidence-type-filter",
        "forest-unit-filter",
        "review-phase-filter",
        "neighbor-depth",
        "degree-threshold",
        "hide-high-degree",
        "pin-selected",
        "fit-graph",
        "reset-layout",
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
        "documentRole",
        "currentness",
        "readinessBlocker",
        "evidenceType",
        "forestUnit",
        "reviewPhase",
        "exportScreenshot",
        "exportViewerState",
        "__NEPA_3D_VIEWER_READY__",
    ]:
        assert required in script

    assert "Viewer layout does not change readiness" in script


def test_nepa_3d_viewer_styles_define_desktop_and_mobile_graph_surfaces() -> None:
    styles = (VIEWER_ROOT / "styles.css").read_text()

    assert ".viewer-shell" in styles
    assert ".graph-root" in styles
    assert ".detail-rail" in styles
    assert "@media (max-width: 1020px)" in styles
    assert "@media (max-width: 620px)" in styles


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
