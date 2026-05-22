function createGraph() {
  state.graphApi = ForceGraph3D({ controlType: "orbit" })(els.graphRoot)
    .backgroundColor("rgba(247,246,241,0)")
    .warmupTicks(0)
    .cooldownTicks(0)
    .nodeId("node_id")
    .nodeRelSize(0.55)
    .nodeResolution(10)
    .nodeOpacity(0.92)
    .nodeVal(nodeValue)
    .nodeColor(nodeColor)
    .nodeLabel(nodeTooltip)
    .linkColor(edgeColor)
    .linkOpacity(0.34)
    .linkWidth(edgeWidth)
    .linkDirectionalParticles(linkParticles)
    .linkDirectionalParticleWidth(1.4)
    .linkDirectionalParticleSpeed(0.004)
    .onNodeClick(handleNodeClick)
    .onLinkClick(handleEdgeClick)
    .onBackgroundClick(clearSelection);
  if (window.THREE) {
    const sphereGeometry = new window.THREE.SphereGeometry(0.42, 8, 8);
    state.graphApi.nodeThreeObject((node) => graphNodeObject(node, sphereGeometry));
  }
  const chargeForce = state.graphApi.d3Force("charge");
  if (chargeForce?.strength) {
    chargeForce.strength(-950);
  }
  const linkForce = state.graphApi.d3Force("link");
  if (linkForce?.distance) {
    linkForce.distance((edge) => {
      if (edge.edge_type === "PRODUCES_APPLICABILITY_DECISION") {
        return 155;
      }
      if (edge.edge_type === "HAS_READINESS_BLOCKER") {
        return 180;
      }
      return 135;
    });
  }
  state.graphApi.d3VelocityDecay(0.34);
  const controls = state.graphApi.controls?.();
  state.graphControls = controls || null;
  if (controls?.addEventListener) {
    controls.addEventListener("change", updateLabelVisibility);
  }
}

function ingestGraph(graph, dataset) {
  state.dataset = dataset;
  state.graph = graph;
  state.nodes = (graph.nodes || []).map((node) => ({ ...node }));
  state.edges = (graph.edges || []).map((edge) => ({
    ...edge,
    source: edge.source_node_id,
    target: edge.target_node_id
  }));
  state.selectedNodeId = null;
  state.selectedEdgeId = null;
  state.nodeIndex = new Map(state.nodes.map((node) => [node.node_id, node]));
  buildGraphIndexes();
  populateLensSelector();
  populateFilterOptions();
  renderValidation();
  renderEmptyDetails();
  setStatus("Graph loaded from validated export data. Viewer layout does not change readiness.");
  setActiveDemoButton();
  renderGraph();
}

function buildGraphIndexes() {
  state.adjacency = new Map();
  state.degree = new Map();
  for (const node of state.nodes) {
    state.adjacency.set(node.node_id, new Set());
    state.degree.set(node.node_id, 0);
  }
  for (const edge of state.edges) {
    if (!state.nodeIndex.has(edge.source_node_id) || !state.nodeIndex.has(edge.target_node_id)) {
      continue;
    }
    state.adjacency.get(edge.source_node_id).add(edge.target_node_id);
    state.adjacency.get(edge.target_node_id).add(edge.source_node_id);
    state.degree.set(edge.source_node_id, (state.degree.get(edge.source_node_id) || 0) + 1);
    state.degree.set(edge.target_node_id, (state.degree.get(edge.target_node_id) || 0) + 1);
  }
}

function buildEvidencePathSpotlight() {
  clearSpotlight();
  const findings = state.nodes.filter((node) => node.node_type === "compliance_finding");
  for (const finding of findings) {
    const sourceClaimIds = finding.metadata?.source_claim_ids || [];
    const claimIds = compactValues([
      ...(Array.isArray(sourceClaimIds) ? sourceClaimIds : [sourceClaimIds]),
      finding.metadata?.source_claim_id
    ]);
    const findingSupportEdges = incomingEdges(finding.node_id, "SUPPORTS_COMPLIANCE_FINDING");
    for (const claimId of claimIds) {
      const sourceClaim = sourceClaimNode(claimId);
      if (!sourceClaim) {
        continue;
      }
      const evidenceEdge = incomingEdges(sourceClaim.node_id, "SUPPORTS_SOURCE_CLAIM")[0];
      const evidenceSpan = evidenceEdge ? state.nodeIndex.get(evidenceEdge.source_node_id) : null;
      const chunkEdge = evidenceSpan ? incomingEdges(evidenceSpan.node_id, "HAS_EVIDENCE_SPAN")[0] : null;
      const chunk = chunkEdge ? state.nodeIndex.get(chunkEdge.source_node_id) : null;
      const artifactEdge = chunk ? incomingEdges(chunk.node_id, "HAS_CHUNK")[0] : null;
      const artifact = artifactEdge ? state.nodeIndex.get(artifactEdge.source_node_id) : null;
      const sourceRecordEdge = artifact ? incomingEdges(artifact.node_id, "HAS_ARTIFACT")[0] : null;
      const sourceRecord = sourceRecordEdge ? state.nodeIndex.get(sourceRecordEdge.source_node_id) : null;
      if (!sourceRecord || !artifact || !chunk || !evidenceSpan) {
        continue;
      }
      for (const findingEdge of findingSupportEdges) {
        const generatedRule = state.nodeIndex.get(findingEdge.source_node_id);
        const generatedRuleEdge = generatedRule ? incomingEdges(generatedRule.node_id, "GENERATES_RULE")[0] : null;
        const decision = generatedRuleEdge ? state.nodeIndex.get(generatedRuleEdge.source_node_id) : null;
        const decisionEdge = decision ? incomingEdges(decision.node_id, "PRODUCES_APPLICABILITY_DECISION")[0] : null;
        const candidateRule = decisionEdge ? state.nodeIndex.get(decisionEdge.source_node_id) : null;
        const claimRuleEdge = outgoingEdges(sourceClaim.node_id, "SUPPORTS_RULE_TEMPLATE").find(
          (edge) => !candidateRule || edge.target_node_id === candidateRule.node_id
        );
        const ruleTemplate = claimRuleEdge ? state.nodeIndex.get(claimRuleEdge.target_node_id) : candidateRule;
        if (!generatedRule || !decision || !decisionEdge || !ruleTemplate || !claimRuleEdge) {
          continue;
        }
        const pathNodes = [
          sourceRecord,
          artifact,
          chunk,
          evidenceSpan,
          sourceClaim,
          ruleTemplate,
          decision,
          generatedRule,
          finding
        ];
        const pathEdges = [
          sourceRecordEdge,
          artifactEdge,
          chunkEdge,
          evidenceEdge,
          claimRuleEdge,
          decisionEdge,
          generatedRuleEdge,
          findingEdge
        ];
        state.spotlightNodeIds = new Set(pathNodes.map((node) => node.node_id));
        state.spotlightEdgeIds = new Set(pathEdges.map((edge) => edge.edge_id));
        state.spotlightSteps = pathNodes.map((node) => ({
          node_id: node.node_id,
          label: `${formatOptionLabel(node.node_type, "nodeEdgeType")}: ${node.label || node.node_id}`
        }));
        state.spotlightTitle = finding.label || "evidence path";
        return;
      }
    }
  }
  setStatus("No complete evidence-to-finding path was found in this graph export.");
}

function spotlightGraph() {
  const nodes = state.nodes.filter((node) => state.spotlightNodeIds.has(node.node_id));
  const nodeIds = new Set(nodes.map((node) => node.node_id));
  const edges = state.edges.filter(
    (edge) =>
      state.spotlightEdgeIds.has(edge.edge_id) &&
      nodeIds.has(edge.source_node_id) &&
      nodeIds.has(edge.target_node_id)
  );
  return { nodes, edges };
}

function incomingEdges(nodeId, edgeType = "") {
  return state.edges.filter(
    (edge) => edge.target_node_id === nodeId && (!edgeType || edge.edge_type === edgeType)
  );
}

function outgoingEdges(nodeId, edgeType = "") {
  return state.edges.filter(
    (edge) => edge.source_node_id === nodeId && (!edgeType || edge.edge_type === edgeType)
  );
}

function sourceClaimNode(claimId) {
  const normalized = String(claimId).replace(/^claim:/, "");
  return (
    state.nodeIndex.get(`source_claim:${normalized}`) ||
    state.nodes.find(
      (node) =>
        node.node_type === "source_claim" &&
        [node.node_id, node.provenance?.source_claim_id, node.metadata?.source_claim_id]
          .filter(Boolean)
          .some((value) => String(value).endsWith(normalized))
    )
  );
}

function populateLensSelector() {
  const lenses = [{ lens_id: "all", label: "All validated graph data" }]
    .concat(state.graph.lens_metadata || [])
    .concat(state.dataset.review_id ? [DIFFERENCE_LENS] : []);
  const lensIds = new Set(lenses.map((lens) => lens.lens_id));
  const missingRequiredLenses = REQUIRED_EXPORT_LENSES.filter((lensId) => !lensIds.has(lensId));
  if (missingRequiredLenses.length > 0) {
    setStatus(`Graph export is missing required lens metadata: ${missingRequiredLenses.join(", ")}`);
  }
  els.lensSelect.innerHTML = "";
  for (const lens of lenses) {
    const lensCounts = displayLensGraph(lens);
    const grounding =
      lens.lens_id === "all"
        ? "validated graph export node and edge tables"
        : lens.lens_id === DIFFERENCE_LENS.lens_id
          ? "review overlay graph export and viewer difference-lens contract"
          : "graph export lens metadata";
    const option = document.createElement("option");
    option.value = lens.lens_id;
    option.textContent = `${lens.label} (${lensCounts.nodes.length} nodes / ${lensCounts.edges.length} edges)`;
    option.title = `${lens.label}: ${lensCounts.nodes.length} graph nodes and ${lensCounts.edges.length} graph edges shown by this lens`;
    option.dataset.grounding = grounding;
    els.lensSelect.append(option);
  }
  const defaultLens = state.dataset.review_id ? DEFAULT_LENS_REVIEW : DEFAULT_LENS_SOURCE_SET;
  els.lensSelect.value = lenses.some((lens) => lens.lens_id === defaultLens) ? defaultLens : "all";
}

function populateFilterOptions({ preserveSelected = false } = {}) {
  const selectedValues = preserveSelected ? selectedFilterValues() : {};
  const optionGraph = { nodes: state.nodes, edges: state.edges };
  state.filterValues = {};
  for (const filter of FILTER_DEFINITIONS) {
    const valueCounts = filterOptionCounts(filter, optionGraph);
    const values = uniqueValues([...valueCounts.keys()]);
    state.filterValues[filter.id] = values;
    const selectedValue = values.includes(selectedValues[filter.id]) ? selectedValues[filter.id] : "";
    replaceOptionsFromPairs(
      document.getElementById(filter.selector),
      [{ value: "", label: "Any" }].concat(
        values.map((value) => ({
          value,
          label: `${formatOptionLabel(value, filter.id)} (${valueCounts.get(value)})`,
          grounding: `${filter.label}: ${valueCounts.get(value)} graph item(s) in this export`
        }))
      ),
      selectedValue
    );
  }
}

function renderGraph() {
  if (!state.graphApi || !state.graph) {
    return;
  }
  const filtered = filteredGraph();
  state.currentRender = filtered;
  buildLabelPlan(filtered);
  state.labelSprites = new Map();
  const preparedNodes = seededLayoutNodes(filtered.nodes);
  state.graphApi.graphData({
    nodes: preparedNodes,
    links: filtered.edges.map((edge) => ({ ...edge }))
  });
  state.graphApi.width(els.graphRoot.clientWidth).height(els.graphRoot.clientHeight);
  state.graphApi.d3ReheatSimulation();
  window.setTimeout(() => {
    if (state.graphApi && filtered.nodes.length > 0) {
      state.graphApi.cameraPosition({ x: 0, y: 0, z: 620 }, { x: 0, y: 0, z: 0 }, 500);
      window.setTimeout(updateLabelVisibility, 650);
    }
  }, 900);
  renderTitle();
  renderLegend(filtered);
  renderCounts(filtered);
  renderGraphSceneLabel(filtered);
  renderCapabilityPanel(filtered);
  updateViewerReadyState(filtered);
  updateLabelVisibility();
}

function filteredGraph() {
  if (state.spotlightNodeIds.size > 0) {
    return spotlightGraph();
  }
  const lens = selectedLens();
  const baseGraph = baseLensGraph(lens);
  const baseNodeIds = new Set(baseGraph.nodes.map((node) => node.node_id));
  const filterValues = selectedFilterValues();
  const searchSeeds = matchingSearchNodeIds(state.nodes);
  const contextFilterSeedGroups = matchingContextFilterSeedGroups(filterValues);
  const selectedSeeds = state.selectedNodeId ? new Set([state.selectedNodeId]) : new Set();
  const seedGroups = contextFilterSeedGroups.concat(searchSeeds.size > 0 ? [searchSeeds] : []);
  if (selectedSeeds.size > 0) {
    seedGroups.push(selectedSeeds);
  }
  const seedIds = unionSets(seedGroups);
  const expandedIds = expandedSeedIntersection(seedGroups, Number(els.neighborDepth.value));
  const hasSeedFilter = seedGroups.length > 0;
  const degreeThreshold = Number(els.degreeThreshold.value);
  const hideHighDegree = els.hideHighDegree.checked;

  const allowedNodes = new Set();
  for (const node of state.nodes) {
    const isSeed = seedIds.has(node.node_id);
    if (!baseNodeIds.has(node.node_id) && !isSeed) {
      continue;
    }
    if (hasSeedFilter && !expandedIds.has(node.node_id)) {
      continue;
    }
    const isSelected = state.selectedNodeId === node.node_id;
    if (hideHighDegree && !isSeed && !isSelected && (state.degree.get(node.node_id) || 0) > degreeThreshold) {
      continue;
    }
    allowedNodes.add(node.node_id);
  }

  let edges = baseGraph.edges.filter((edge) => {
    if (!allowedNodes.has(edge.source_node_id) || !allowedNodes.has(edge.target_node_id)) {
      return false;
    }
    return true;
  });

  const edgeNodeIds = new Set(edges.flatMap((edge) => [edge.source_node_id, edge.target_node_id]));
  const visibleNodeIds = hasSeedFilter
    ? new Set([...edgeNodeIds, ...seedIds])
    : lens?.lens_id === "all" || edgeNodeIds.size === 0
      ? allowedNodes
      : edgeNodeIds;
  const nodes = state.nodes.filter((node) => allowedNodes.has(node.node_id) && visibleNodeIds.has(node.node_id));
  const nodeIds = new Set(nodes.map((node) => node.node_id));
  edges = edges.filter((edge) => nodeIds.has(edge.source_node_id) && nodeIds.has(edge.target_node_id));

  return { nodes, edges };
}

function baseLensGraph(lens = selectedLens()) {
  return lensGraph(lens);
}

function displayLensGraph(lens) {
  const graph = lensGraph(lens);
  if (lens?.lens_id === "all") {
    return graph;
  }
  const edgeNodeIds = new Set(graph.edges.flatMap((edge) => [edge.source_node_id, edge.target_node_id]));
  if (edgeNodeIds.size === 0) {
    return graph;
  }
  return {
    nodes: graph.nodes.filter((node) => edgeNodeIds.has(node.node_id)),
    edges: graph.edges
  };
}

function lensGraph(lens) {
  if (!lens || lens.lens_id === "all") {
    return { nodes: state.nodes, edges: state.edges };
  }
  const lensNodeTypes = new Set(lens.supported_node_types || []);
  const lensEdgeTypes = new Set(lens.supported_edge_types || []);
  const lensStatuses = new Set(lens.display_status_values || []);
  const lensEndpointNodeIds = new Set();
  const edges = state.edges.filter((edge) => {
    if (!lensEdgeTypes.has(edge.edge_type)) {
      return false;
    }
    lensEndpointNodeIds.add(edge.source_node_id);
    lensEndpointNodeIds.add(edge.target_node_id);
    return true;
  });
  const nodes = state.nodes.filter((node) => {
    const typeAllowed = lensNodeTypes.has(node.node_type);
    const statusAllowed = lensStatuses.size === 0 || lensStatuses.has(node.display_status);
    const endpointAllowed = lensEndpointNodeIds.has(node.node_id);
    return typeAllowed || statusAllowed || endpointAllowed;
  });
  const nodeIds = new Set(nodes.map((node) => node.node_id));
  return {
    nodes,
    edges: edges.filter((edge) => nodeIds.has(edge.source_node_id) && nodeIds.has(edge.target_node_id))
  };
}

function selectedLens() {
  const lensId = els.lensSelect.value;
  if (lensId === "all") {
    return { lens_id: "all", label: "All validated graph data" };
  }
  if (lensId === DIFFERENCE_LENS.lens_id) {
    return DIFFERENCE_LENS;
  }
  return (state.graph.lens_metadata || []).find((lens) => lens.lens_id === lensId);
}

function selectedFilterValues() {
  const selected = {};
  for (const filter of FILTER_DEFINITIONS) {
    selected[filter.id] = document.getElementById(filter.selector).value;
  }
  return selected;
}

function matchingSearchNodeIds(nodes) {
  const query = els.graphSearch.value.trim().toLowerCase();
  if (!query) {
    return new Set();
  }
  return new Set(nodes.filter((node) => nodeSearchText(node).includes(query)).map((node) => node.node_id));
}

function matchingContextFilterSeedGroups(filterValues) {
  const groups = [];
  for (const filter of FILTER_DEFINITIONS) {
    if (!CONTEXT_SEED_FILTER_IDS.has(filter.id) || !filterValues[filter.id]) {
      continue;
    }
    const seeds = new Set();
    for (const node of state.nodes) {
      if (filter.accessor(node).includes(filterValues[filter.id])) {
        seeds.add(node.node_id);
      }
    }
    for (const edge of state.edges) {
      if (filter.accessor(edge).includes(filterValues[filter.id])) {
        seeds.add(edge.source_node_id);
        seeds.add(edge.target_node_id);
      }
    }
    groups.push(seeds);
  }
  return groups;
}

function expandSeeds(seedIds, depth) {
  const expanded = new Set(seedIds);
  let frontier = new Set(seedIds);
  for (let index = 0; index < depth; index += 1) {
    const next = new Set();
    for (const nodeId of frontier) {
      for (const neighbor of state.adjacency.get(nodeId) || []) {
        if (!expanded.has(neighbor)) {
          expanded.add(neighbor);
          next.add(neighbor);
        }
      }
    }
    frontier = next;
    if (frontier.size === 0) {
      break;
    }
  }
  return expanded;
}

function expandedSeedIntersection(seedGroups, depth) {
  if (seedGroups.length === 0) {
    return new Set();
  }
  const expandedGroups = seedGroups.map((seeds) => expandSeeds(seeds, depth));
  return intersectSets(expandedGroups);
}

function unionSets(sets) {
  const union = new Set();
  for (const set of sets) {
    for (const value of set) {
      union.add(value);
    }
  }
  return union;
}

function intersectSets(sets) {
  if (sets.length === 0) {
    return new Set();
  }
  const [first, ...rest] = sets;
  const intersection = new Set(first);
  for (const value of first) {
    if (!rest.every((set) => set.has(value))) {
      intersection.delete(value);
    }
  }
  return intersection;
}

function filterOptionCounts(filter, baseGraph) {
  const counts = new Map();
  for (const item of baseGraph.nodes.concat(baseGraph.edges)) {
    for (const value of filter.accessor(item)) {
      counts.set(value, (counts.get(value) || 0) + 1);
    }
  }
  return counts;
}

function renderTitle() {
  const summary = state.graph.summary || {};
  els.datasetTitle.textContent = state.dataset.label || state.graph.graph_id || "NEPA 3D graph";
  const validationPassed = validationPassedText();
  els.graphCounts.textContent = [summary.source_set_id, summary.review_id, validationPassed].filter(Boolean).join(" | ");
}

function renderCounts(filtered) {
  const summary = state.graph.summary || {};
  const totalNodes = summary.node_count ?? state.nodes.length;
  const totalEdges = summary.edge_count ?? state.edges.length;
  if (state.spotlightNodeIds.size > 0) {
    setStatus(
      `Spotlighting ${state.spotlightTitle || "evidence path"} with ${filtered.nodes.length}/${totalNodes} nodes and ${filtered.edges.length}/${totalEdges} edges from validated graph data.`
    );
    return;
  }
  const activeContext = activeContextLabels();
  let hint = "";
  if (activeContext.length > 0 && filtered.nodes.length === 0) {
    hint = " No matching context in this lens; try All validated graph data or clear filters.";
  } else if (activeContext.length > 0 && filtered.edges.length === 0) {
    hint = " Matching nodes have no edges in this lens; try All validated graph data.";
  }
  setStatus(
    `Showing ${filtered.nodes.length}/${totalNodes} nodes and ${filtered.edges.length}/${totalEdges} edges with ${selectedLens()?.label || "selected lens"}.${hint}`
  );
}

function renderGraphSceneLabel(filtered = state.currentRender) {
  if (!els.graphSceneLabel) {
    return;
  }
  const scene = activeDemoScene();
  const title = scene?.graphLabel || scene?.label || "Custom graph view";
  const subtitle = scene?.graphSubLabel || selectedLens()?.label || "Validated graph export";
  const labelMode = state.labelsEnabled
    ? `${LABEL_TIER_COPY[state.labelZoomTier] || "Overview labels"}: ${state.labelStats[state.labelZoomTier] || 0} visible of ${filtered.nodes.length} nodes`
    : "Node labels: off";
  els.graphSceneLabel.innerHTML = [
    `<div class="graph-scene-title">${escapeHtml(title)}</div>`,
    `<div class="graph-scene-subtitle">${escapeHtml(subtitle)}</div>`,
    `<div class="graph-label-mode">${escapeHtml(labelMode)}</div>`
  ].join("");
}

function activeContextLabels() {
  const labels = [];
  for (const filter of FILTER_DEFINITIONS) {
    const selected = document.getElementById(filter.selector).value;
    if (selected) {
      labels.push(`${filter.label}: ${selected}`);
    }
  }
  if (els.graphSearch.value.trim()) {
    labels.push(`Search: ${els.graphSearch.value.trim()}`);
  }
  return labels;
}

function renderLegend(filtered) {
  const nodes = filtered?.nodes || [];
  const edges = filtered?.edges || [];
  const statuses = uniqueValues(
    nodes
      .map((node) => node.display_status)
      .filter((status) => status && status !== "readiness_blocked")
  ).slice(0, 8);
  const readinessClasses = uniqueValues(
    nodes
      .concat(edges)
      .map((item) => readinessSemanticClass(item))
      .filter((value) => value && value !== "none")
  );
  els.legend.innerHTML = "";
  for (const status of statuses) {
    const item = document.createElement("div");
    item.className = "legend-item";
    const swatch = document.createElement("span");
    swatch.className = "legend-swatch";
    swatch.style.background = STATUS_COLORS[status] || "#7f7b73";
    const label = document.createElement("span");
    label.textContent = status.replaceAll("_", " ");
    item.append(swatch, label);
    els.legend.append(item);
  }
  for (const readinessClass of readinessClasses) {
    const item = document.createElement("div");
    item.className = "legend-item";
    const swatch = document.createElement("span");
    swatch.className = "legend-swatch";
    swatch.style.background = READINESS_SEMANTIC_COLORS[readinessClass] || STATUS_COLORS.readiness_blocked;
    const label = document.createElement("span");
    label.textContent = readinessSemanticLabel(readinessClass);
    item.append(swatch, label);
    els.legend.append(item);
  }
}

function renderValidation() {
  const validation = state.graph.validation || {};
  const summary = state.graph.summary || {};
  const checks = validation.checks || [];
  const failed = checks.filter((check) => check.passed === false);
  const rows = [
    ["validation", validationPassedText()],
    ["checks", summary.validation_check_count ?? checks.length ?? ""],
    ["failed", summary.failed_validation_check_count ?? failed.length ?? ""],
    ["source set", summary.source_set_id || ""],
    ["review", summary.review_id || ""],
    ["graph path", summary.graph_path || state.dataset.graph_path || ""],
    ["created", state.graph.created_at || ""]
  ];
  els.validationPanel.innerHTML = detailMarkup(rows);
}

function updateViewerReadyState(filtered) {
  window.__NEPA_3D_VIEWER_READY__ = {
    loaded: true,
    dataset_id: state.dataset?.dataset_id || null,
    source_set_id: state.graph?.summary?.source_set_id || null,
    review_id: state.graph?.summary?.review_id || null,
    demo_scene_id: state.activeDemoSceneId,
    lens_id: els.lensSelect.value,
    label_zoom_tier: state.labelZoomTier,
    visible_label_count: state.labelStats[state.labelZoomTier] || 0,
    labels_enabled: state.labelsEnabled,
    spotlight_node_count: state.spotlightNodeIds.size,
    spotlight_edge_count: state.spotlightEdgeIds.size,
    rendered_node_count: filtered.nodes.length,
    rendered_edge_count: filtered.edges.length,
    canvas_count: els.graphRoot.querySelectorAll("canvas").length,
    validation_passed: state.graph?.summary?.validation_passed === true
  };
}
