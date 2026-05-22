function renderEmptyDetails() {
  els.detailPanel.innerHTML = '<div class="detail-empty">Select a node or edge.</div>';
}

function renderCapabilityPanel(filtered = state.currentRender) {
  if (!els.capabilityPanel) {
    return;
  }
  const scene = activeDemoScene();
  const title = scene?.capabilityTitle || "Custom graph view";
  const copy =
    scene?.capabilityCopy ||
    "Shows a reviewer-defined combination of graph lens, search, filters, and layout controls over the validated export.";
  const rows = sceneMetricRows(scene, filtered);
  const metrics = rows
    .map(
      ([label, value]) =>
        `<div class="capability-metric"><span>${escapeHtml(label)}</span><strong>${escapeHtml(String(value))}</strong></div>`
    )
    .join("");
  const proofLabels = scene?.proofLabels || activeContextLabels();
  const proof = proofLabels.length
    ? `<div class="capability-proof">${proofLabels.map((label) => `<span>${escapeHtml(label)}</span>`).join("")}</div>`
    : "";
  const pathMarkup =
    state.spotlightSteps.length > 0
      ? `<div class="path-steps">${state.spotlightSteps
          .map(
            (step, index) =>
              `<button class="path-step" type="button" data-node-id="${escapeHtml(step.node_id)}"><span>${index + 1}</span>${escapeHtml(step.label)}</button>`
          )
          .join("")}</div>`
      : "";
  els.capabilityPanel.innerHTML = [
    `<div class="capability-title">${escapeHtml(title)}</div>`,
    `<p class="capability-copy">${escapeHtml(copy)}</p>`,
    metrics ? `<div class="capability-metrics">${metrics}</div>` : "",
    proof,
    pathMarkup
  ].join("");
}

function sceneMetricRows(scene, filtered) {
  const rows = [
    ["rendered nodes", filtered.nodes.length],
    ["rendered edges", filtered.edges.length]
  ];
  if (!state.graph) {
    return rows;
  }
  if (scene?.id === "source_library") {
    rows.push(["source records", countNodes("source_record")]);
    rows.push(["artifacts", countNodes("artifact")]);
  } else if (scene?.id === "authority_universe") {
    rows.push(["authority families", countNodes("authority_family")]);
    rows.push(["source records", countNodes("source_record")]);
  } else if (scene?.id === "applicability") {
    rows.push(["applicable decisions", countNodes("applicability_decision", (node) => node.display_status === "applicable")]);
    rows.push([
      "non-applicable decisions",
      countNodes("applicability_decision", (node) => node.display_status === "not_applicable")
    ]);
  } else if (scene?.id === "evidence_path") {
    rows.push(["path steps", state.spotlightSteps.length]);
    rows.push(["path edges", state.spotlightEdgeIds.size]);
  } else if (scene?.id === "forest_plan") {
    rows.push(["forest units", countNodes("forest_unit")]);
    rows.push(["plan components", countNodes("forest_plan_component")]);
  } else if (scene?.id === "readiness") {
    rows.push(["readiness blockers", countNodes("readiness_blocker")]);
    rows.push(["blocker edges", countEdges("HAS_READINESS_BLOCKER")]);
  } else if (scene?.id === "full_graph") {
    rows.push(["total graph nodes", state.nodes.length]);
    rows.push(["total graph edges", state.edges.length]);
  }
  return rows;
}

function countNodes(nodeType, predicate = () => true) {
  return state.nodes.filter((node) => node.node_type === nodeType && predicate(node)).length;
}

function countEdges(edgeType, predicate = () => true) {
  return state.edges.filter((edge) => edge.edge_type === edgeType && predicate(edge)).length;
}

function selectCapabilityNode(nodeId) {
  const node = state.nodeIndex.get(nodeId);
  if (!node) {
    return;
  }
  state.selectedNodeId = node.node_id;
  state.selectedEdgeId = null;
  updatePinnedSelection(node);
  renderNodeDetails(node);
  renderGraph();
}

function renderNodeDetails(node) {
  const readinessClass = readinessSemanticClass(node);
  const rows = [
    ["label", node.label],
    ["node id", node.node_id],
    ["type", node.node_type],
    ["status", node.display_status],
    ["review readiness", node.review_readiness_status],
    ["readiness class", readinessClass !== "none" ? readinessSemanticLabel(readinessClass) : ""],
    ["readiness meaning", readinessSemanticExplanation(node)],
    ["source record", node.provenance?.source_record_id],
    ["citation", node.provenance?.citation_label],
    ["artifact hash", node.provenance?.artifact_sha256],
    ["artifact path", node.provenance?.artifact_path],
    ["authority family", node.provenance?.authority_family_id],
    ["rule id", node.provenance?.rule_id],
    ["component id", node.provenance?.component_id],
    ["forest unit", node.provenance?.forest_unit_id || node.provenance?.forest_code],
    ["review", node.provenance?.review_id]
  ];
  els.detailPanel.innerHTML = [
    `<div class="detail-title">${escapeHtml(node.label || node.node_id)}</div>`,
    badgeRow([
      node.node_type,
      node.display_status,
      node.review_readiness_status,
      readinessClass !== "none" ? readinessSemanticLabel(readinessClass) : ""
    ]),
    detailMarkup(rows),
    jsonBlock("provenance", node.provenance),
    jsonBlock("currentness", node.currentness_metadata),
    jsonBlock("metadata", node.metadata),
    jsonBlock("readiness blockers", node.readiness_blockers)
  ].join("");
}

function renderEdgeDetails(edge) {
  const readinessClass = readinessSemanticClass(edge);
  const rows = [
    ["edge id", edge.edge_id],
    ["type", edge.edge_type],
    ["source", edge.source_node_id || edge.source?.node_id || edge.source],
    ["target", edge.target_node_id || edge.target?.node_id || edge.target],
    ["status", edge.display_status],
    ["review readiness", edge.review_readiness_status],
    ["readiness class", readinessClass !== "none" ? readinessSemanticLabel(readinessClass) : ""],
    ["readiness meaning", readinessSemanticExplanation(edge)],
    ["source record", edge.provenance?.source_record_id],
    ["citation", edge.provenance?.citation_label],
    ["artifact hash", edge.provenance?.artifact_sha256],
    ["review", edge.provenance?.review_id]
  ];
  els.detailPanel.innerHTML = [
    `<div class="detail-title">${escapeHtml(edge.edge_type || edge.edge_id)}</div>`,
    badgeRow([
      edge.edge_type,
      edge.display_status,
      edge.review_readiness_status,
      readinessClass !== "none" ? readinessSemanticLabel(readinessClass) : ""
    ]),
    detailMarkup(rows),
    jsonBlock("provenance", edge.provenance),
    jsonBlock("readiness blockers", edge.readiness_blockers)
  ].join("");
}

function handleNodeClick(node) {
  state.selectedNodeId = node.node_id;
  state.selectedEdgeId = null;
  updatePinnedSelection(node);
  renderNodeDetails(node);
  renderGraph();
}

function handleEdgeClick(edge) {
  state.selectedEdgeId = edge.edge_id;
  state.selectedNodeId = null;
  renderEdgeDetails(edge);
  renderGraph();
}

function clearSelection() {
  state.selectedNodeId = null;
  state.selectedEdgeId = null;
  renderEmptyDetails();
  renderGraph();
}

function updatePinnedSelection(node = null) {
  if (!node && !state.selectedNodeId) {
    return;
  }
  const graphNode = node || state.currentRender.nodes.find((candidate) => candidate.node_id === state.selectedNodeId);
  if (!graphNode) {
    return;
  }
  if (els.pinSelected.checked) {
    graphNode.fx = graphNode.x;
    graphNode.fy = graphNode.y;
    graphNode.fz = graphNode.z;
  } else {
    delete graphNode.fx;
    delete graphNode.fy;
    delete graphNode.fz;
  }
}

function fitGraph() {
  if (state.graphApi) {
    state.graphApi.zoomToFit(550, 70);
  }
}

function resetLayout() {
  state.selectedNodeId = null;
  state.selectedEdgeId = null;
  renderEmptyDetails();
  state.graphApi.d3ReheatSimulation();
  renderGraph();
}

function clearFilters() {
  resetFilterControls();
  markCustomScene();
  state.selectedNodeId = null;
  state.selectedEdgeId = null;
  renderEmptyDetails();
  renderGraph();
}

function exportScreenshot() {
  const canvas = els.graphRoot.querySelector("canvas");
  if (!canvas) {
    setStatus("No canvas is available for PNG export.");
    return;
  }
  const link = document.createElement("a");
  link.download = `${state.dataset?.dataset_id || "nepa-3d"}-${Date.now()}.png`;
  link.href = canvas.toDataURL("image/png");
  link.click();
}

function exportViewerState() {
  const payload = {
    exported_at: new Date().toISOString(),
    dataset: state.dataset,
    demo_scene_id: state.activeDemoSceneId,
    lens_id: els.lensSelect.value,
    filters: selectedFilterValues(),
    search: els.graphSearch.value,
    neighbor_depth: Number(els.neighborDepth.value),
    hide_high_degree_nodes: els.hideHighDegree.checked,
    labels_enabled: state.labelsEnabled,
    detail_rail_collapsed: els.viewerShell.classList.contains("is-detail-collapsed"),
    degree_threshold: Number(els.degreeThreshold.value),
    spotlight_title: state.spotlightTitle || null,
    spotlight_node_ids: [...state.spotlightNodeIds],
    spotlight_edge_ids: [...state.spotlightEdgeIds],
    rendered_node_count: state.currentRender.nodes.length,
    rendered_edge_count: state.currentRender.edges.length,
    graph_summary: state.graph?.summary || null
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const link = document.createElement("a");
  link.download = `${state.dataset?.dataset_id || "nepa-3d"}-viewer-state.json`;
  link.href = URL.createObjectURL(blob);
  link.click();
  URL.revokeObjectURL(link.href);
}
