const MANIFEST_PATH = "manifest.json";
const DEFAULT_LENS_SOURCE_SET = "readiness_blockers";
const DEFAULT_LENS_REVIEW = "package_applicability";
const REQUIRED_EXPORT_LENSES = [
  "authority_currentness",
  "forest_plan",
  "package_applicability",
  "evidence_path",
  "readiness_blockers"
];
const STATUS_COLORS = {
  active: "#26786f",
  applicable: "#2f8f45",
  not_applicable: "#7d7a72",
  readiness_blocked: "#b13d38",
  candidate: "#a75a22",
  superseded: "#6f5e9d",
  reserved: "#356a9b",
  out_of_scope: "#5e6572",
  unresolved: "#a75a22",
  adjudicated: "#3f7667"
};
const NODE_TYPE_COLORS = {
  authority_family: "#26786f",
  source_record: "#356a9b",
  artifact: "#7f7b73",
  chunk: "#8b8a51",
  evidence_span: "#a75a22",
  source_claim: "#6f5e9d",
  rule_template: "#364f7a",
  applicability_decision: "#2f8f45",
  generated_rule: "#485f28",
  compliance_finding: "#7c493c",
  forest_unit: "#216a60",
  forest_plan: "#417d46",
  forest_plan_component: "#6c8d38",
  readiness_blocker: "#b13d38",
  review: "#2d5976",
  source_set: "#171713",
  graph_lens: "#8b6b3e"
};
const NODE_TYPE_ORDER = [
  "source_set",
  "review",
  "authority_family",
  "source_record",
  "artifact",
  "chunk",
  "evidence_span",
  "source_claim",
  "rule_template",
  "applicability_decision",
  "generated_rule",
  "compliance_finding",
  "forest_unit",
  "forest_plan",
  "forest_plan_component",
  "readiness_blocker",
  "graph_lens"
];
const DIFFERENCE_LENS = {
  lens_id: "difference_view",
  label: "Difference View",
  description: "Review-only applicability, generated-rule, finding, and blocker overlay.",
  supported_node_types: [
    "review",
    "authority_family",
    "rule_template",
    "applicability_decision",
    "generated_rule",
    "compliance_finding",
    "readiness_blocker"
  ],
  supported_edge_types: [
    "PRODUCES_APPLICABILITY_DECISION",
    "APPLIES_TO_REVIEW",
    "NOT_APPLICABLE_TO_REVIEW",
    "NEEDS_ADJUDICATION",
    "GENERATES_RULE",
    "SUPPORTS_COMPLIANCE_FINDING",
    "HAS_READINESS_BLOCKER"
  ],
  display_status_values: [
    "applicable",
    "not_applicable",
    "unresolved",
    "adjudicated",
    "readiness_blocked"
  ]
};
const FILTER_DEFINITIONS = [
  { id: "status", selector: "status-filter", label: "Status / readiness", accessor: statusValues },
  {
    id: "authorityCategory",
    selector: "authority-category-filter",
    label: "Authority category",
    accessor: authorityCategoryValues
  },
  {
    id: "authorityFamily",
    selector: "authority-family-filter",
    label: "Authority family",
    accessor: authorityFamilyValues
  },
  {
    id: "documentRole",
    selector: "document-role-filter",
    label: "Document role",
    accessor: documentRoleValues
  },
  {
    id: "currentness",
    selector: "currentness-filter",
    label: "Currentness / partition",
    accessor: currentnessValues
  },
  {
    id: "readinessBlocker",
    selector: "blocker-filter",
    label: "Readiness blocker",
    accessor: readinessBlockerValues
  },
  {
    id: "nodeEdgeType",
    selector: "node-edge-type-filter",
    label: "Node / edge type",
    accessor: nodeEdgeTypeValues
  },
  {
    id: "evidenceKind",
    selector: "evidence-kind-filter",
    label: "Evidence / basis",
    accessor: evidenceKindValues
  },
  {
    id: "forestUnit",
    selector: "forest-unit-filter",
    label: "Forest unit",
    accessor: forestUnitValues
  },
  {
    id: "reviewPhase",
    selector: "review-phase-filter",
    label: "Review phase",
    accessor: reviewPhaseValues
  }
];
const CONTEXT_SEED_FILTER_IDS = new Set(FILTER_DEFINITIONS.map((filter) => filter.id));

const state = {
  graphApi: null,
  manifest: null,
  dataset: null,
  graph: null,
  nodes: [],
  edges: [],
  nodeIndex: new Map(),
  adjacency: new Map(),
  degree: new Map(),
  filterValues: {},
  selectedNodeId: null,
  selectedEdgeId: null,
  currentRender: { nodes: [], edges: [] }
};

const els = {};

document.addEventListener("DOMContentLoaded", () => {
  bindElements();
  bindEvents();
  waitForRuntime();
});

function waitForRuntime() {
  if (window.ForceGraph3D) {
    initialize();
    return;
  }
  const startedAt = Date.now();
  const interval = window.setInterval(() => {
    if (window.ForceGraph3D) {
      window.clearInterval(interval);
      initialize();
    } else if (Date.now() - startedAt > 12000) {
      window.clearInterval(interval);
      setStatus("3D graph runtime did not load. Check network access or CDN availability.");
    }
  }, 120);
}

async function initialize() {
  createGraph();
  await loadManifest();
}

function bindElements() {
  const ids = [
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
    "neighbor-depth-value",
    "degree-threshold",
    "degree-threshold-value",
    "hide-high-degree",
    "pin-selected",
    "fit-graph",
    "reset-layout",
    "clear-filters",
    "export-shot",
    "export-state",
    "dataset-title",
    "graph-counts",
    "graph-root",
    "status-line",
    "legend",
    "detail-panel",
    "validation-panel"
  ];
  for (const id of ids) {
    els[toCamel(id)] = document.getElementById(id);
  }
}

function bindEvents() {
  els.sourceSetSelect.addEventListener("change", () => {
    populateReviewSelector();
    loadSelectedDataset();
  });
  els.reviewSelect.addEventListener("change", loadSelectedDataset);
  els.lensSelect.addEventListener("change", () => {
    populateFilterOptions({ preserveSelected: true });
    renderGraph();
  });
  els.graphSearch.addEventListener("input", renderGraph);
  els.graphFileInput.addEventListener("change", loadFileDataset);
  els.neighborDepth.addEventListener("input", () => {
    els.neighborDepthValue.value = els.neighborDepth.value;
    renderGraph();
  });
  els.degreeThreshold.addEventListener("input", () => {
    els.degreeThresholdValue.value = els.degreeThreshold.value;
    renderGraph();
  });
  els.hideHighDegree.addEventListener("change", renderGraph);
  els.pinSelected.addEventListener("change", updatePinnedSelection);
  els.fitGraph.addEventListener("click", fitGraph);
  els.resetLayout.addEventListener("click", resetLayout);
  els.clearFilters.addEventListener("click", clearFilters);
  els.exportShot.addEventListener("click", exportScreenshot);
  els.exportState.addEventListener("click", exportViewerState);
  for (const filter of FILTER_DEFINITIONS) {
    document.getElementById(filter.selector).addEventListener("change", renderGraph);
  }
  window.addEventListener("resize", () => {
    if (state.graphApi) {
      state.graphApi.width(els.graphRoot.clientWidth).height(els.graphRoot.clientHeight);
    }
  });
}

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
    state.graphApi.nodeThreeObject((node) => {
      const material = new window.THREE.MeshLambertMaterial({
        color: nodeColor(node),
        transparent: true,
        opacity: node.node_type === "readiness_blocker" ? 0.95 : 0.82
      });
      const mesh = new window.THREE.Mesh(sphereGeometry, material);
      const scale = node.node_type === "readiness_blocker" || node.display_status === "applicable" ? 2.2 : 1;
      mesh.scale.setScalar(scale);
      return mesh;
    });
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
}

async function loadManifest() {
  try {
    const response = await fetch(MANIFEST_PATH, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`manifest HTTP ${response.status}`);
    }
    state.manifest = await response.json();
    populateSourceSetSelector();
    populateReviewSelector();
    await loadSelectedDataset();
  } catch (error) {
    setStatus(`Manifest unavailable: ${error.message}. Use Graph JSON file input.`);
    renderEmptyDetails();
  }
}

function populateSourceSetSelector() {
  const sourceSetIds = uniqueValues(
    state.manifest.datasets.map((dataset) => dataset.source_set_id).filter(Boolean)
  );
  replaceOptions(els.sourceSetSelect, sourceSetIds, state.manifest.default_source_set_id);
}

function populateReviewSelector() {
  const sourceSetId = els.sourceSetSelect.value;
  const reviewDatasets = state.manifest.datasets.filter(
    (dataset) => dataset.scope === "review_overlay" && dataset.source_set_id === sourceSetId
  );
  const options = [{ value: "", label: "Source set only" }].concat(
    reviewDatasets.map((dataset) => ({
      value: dataset.review_id,
      label: dataset.review_id
    }))
  );
  replaceOptionsFromPairs(els.reviewSelect, options, state.manifest.default_review_id || "");
}

async function loadSelectedDataset() {
  if (!state.manifest) {
    return;
  }
  const sourceSetId = els.sourceSetSelect.value || state.manifest.default_source_set_id;
  const reviewId = els.reviewSelect.value;
  const dataset = state.manifest.datasets.find((candidate) => {
    if (reviewId) {
      return candidate.source_set_id === sourceSetId && candidate.review_id === reviewId;
    }
    return candidate.source_set_id === sourceSetId && candidate.scope === "source_set";
  });
  if (!dataset) {
    setStatus("No graph dataset matches the selected source set and review.");
    return;
  }
  await loadDataset(dataset);
}

async function loadDataset(dataset) {
  setStatus(`Loading ${dataset.label}`);
  const response = await fetch(dataset.graph_path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Graph export fetch failed for ${dataset.graph_path}: HTTP ${response.status}`);
  }
  const graph = await response.json();
  ingestGraph(graph, dataset);
}

async function loadFileDataset() {
  const file = els.graphFileInput.files && els.graphFileInput.files[0];
  if (!file) {
    return;
  }
  const text = await file.text();
  const graph = JSON.parse(text);
  const dataset = {
    dataset_id: `file:${file.name}`,
    label: file.name,
    scope: graph.export_scope || "file",
    source_set_id: graph.summary?.source_set_id || graph.inputs?.source_set_id || "",
    review_id: graph.summary?.review_id || null,
    graph_path: file.name
  };
  ingestGraph(graph, dataset);
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
    }
  }, 900);
  renderTitle();
  renderLegend(filtered.nodes);
  renderCounts(filtered);
  updateViewerReadyState(filtered);
}

function filteredGraph() {
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
  els.graphCounts.textContent = [
    summary.source_set_id,
    summary.review_id,
    validationPassed
  ].filter(Boolean).join(" | ");
}

function renderCounts(filtered) {
  const summary = state.graph.summary || {};
  const totalNodes = summary.node_count ?? state.nodes.length;
  const totalEdges = summary.edge_count ?? state.edges.length;
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

function renderLegend(nodes) {
  const statuses = uniqueValues(nodes.map((node) => node.display_status).filter(Boolean)).slice(0, 8);
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

function renderEmptyDetails() {
  els.detailPanel.innerHTML = '<div class="detail-empty">Select a node or edge.</div>';
}

function renderNodeDetails(node) {
  const rows = [
    ["label", node.label],
    ["node id", node.node_id],
    ["type", node.node_type],
    ["status", node.display_status],
    ["review readiness", node.review_readiness_status],
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
    badgeRow([node.node_type, node.display_status, node.review_readiness_status]),
    detailMarkup(rows),
    jsonBlock("provenance", node.provenance),
    jsonBlock("currentness", node.currentness_metadata),
    jsonBlock("metadata", node.metadata),
    jsonBlock("readiness blockers", node.readiness_blockers)
  ].join("");
}

function renderEdgeDetails(edge) {
  const rows = [
    ["edge id", edge.edge_id],
    ["type", edge.edge_type],
    ["source", edge.source_node_id || edge.source?.node_id || edge.source],
    ["target", edge.target_node_id || edge.target?.node_id || edge.target],
    ["status", edge.display_status],
    ["review readiness", edge.review_readiness_status],
    ["source record", edge.provenance?.source_record_id],
    ["citation", edge.provenance?.citation_label],
    ["artifact hash", edge.provenance?.artifact_sha256],
    ["review", edge.provenance?.review_id]
  ];
  els.detailPanel.innerHTML = [
    `<div class="detail-title">${escapeHtml(edge.edge_type || edge.edge_id)}</div>`,
    badgeRow([edge.edge_type, edge.display_status, edge.review_readiness_status]),
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
  els.graphSearch.value = "";
  for (const filter of FILTER_DEFINITIONS) {
    document.getElementById(filter.selector).value = "";
  }
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
    lens_id: els.lensSelect.value,
    filters: selectedFilterValues(),
    search: els.graphSearch.value,
    neighbor_depth: Number(els.neighborDepth.value),
    hide_high_degree_nodes: els.hideHighDegree.checked,
    degree_threshold: Number(els.degreeThreshold.value),
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

function updateViewerReadyState(filtered) {
  window.__NEPA_3D_VIEWER_READY__ = {
    loaded: true,
    dataset_id: state.dataset?.dataset_id || null,
    source_set_id: state.graph?.summary?.source_set_id || null,
    review_id: state.graph?.summary?.review_id || null,
    lens_id: els.lensSelect.value,
    rendered_node_count: filtered.nodes.length,
    rendered_edge_count: filtered.edges.length,
    canvas_count: els.graphRoot.querySelectorAll("canvas").length,
    validation_passed: state.graph?.summary?.validation_passed === true
  };
}

function nodeValue(node) {
  const degree = state.degree.get(node.node_id) || 1;
  if (node.node_type === "readiness_blocker") {
    return 1.6;
  }
  if (node.display_status === "applicable") {
    return 1.5;
  }
  return Math.min(1.8, 0.85 + Math.sqrt(degree) / 16);
}

function seededLayoutNodes(nodes) {
  const typeKeys = uniqueValues(nodes.map((node) => node.node_type));
  const orderedKeys = NODE_TYPE_ORDER.filter((key) => typeKeys.includes(key)).concat(
    typeKeys.filter((key) => !NODE_TYPE_ORDER.includes(key))
  );
  const clusterCount = Math.max(1, orderedKeys.length);
  const clusterRadius = Math.max(110, Math.min(310, 34 * clusterCount));
  const clusterByType = new Map();
  orderedKeys.forEach((type, index) => {
    const angle = (Math.PI * 2 * index) / clusterCount;
    const verticalBand = ((index % 5) - 2) * 44;
    clusterByType.set(type, {
      x: Math.cos(angle) * clusterRadius,
      y: Math.sin(angle) * clusterRadius,
      z: verticalBand
    });
  });
  return nodes.map((node) => {
    const center = clusterByType.get(node.node_type) || { x: 0, y: 0, z: 0 };
    const hash = stableHash(node.node_id);
    const angle = ((hash % 3600) / 3600) * Math.PI * 2;
    const ring = 22 + (hash % 90);
    const zJitter = ((Math.floor(hash / 17) % 90) - 45) * 0.9;
    const x = center.x + Math.cos(angle) * ring;
    const y = center.y + Math.sin(angle) * ring;
    const z = center.z + zJitter;
    return {
      ...node,
      x,
      y,
      z,
      fx: x,
      fy: y,
      fz: z
    };
  });
}

function stableHash(value) {
  let hash = 2166136261;
  const text = String(value);
  for (let index = 0; index < text.length; index += 1) {
    hash ^= text.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function nodeColor(node) {
  return STATUS_COLORS[node.display_status] || NODE_TYPE_COLORS[node.node_type] || "#7f7b73";
}

function edgeColor(edge) {
  if (edge.edge_type === "HAS_READINESS_BLOCKER" || edge.display_status === "readiness_blocked") {
    return "rgba(177, 61, 56, 0.72)";
  }
  if (edge.edge_type === "APPLIES_TO_REVIEW" || edge.edge_type === "GENERATES_RULE") {
    return "rgba(47, 143, 69, 0.66)";
  }
  if (edge.edge_type === "NOT_APPLICABLE_TO_REVIEW") {
    return "rgba(125, 122, 114, 0.58)";
  }
  return "rgba(53, 106, 155, 0.42)";
}

function edgeWidth(edge) {
  if (state.selectedEdgeId && state.selectedEdgeId === edge.edge_id) {
    return 3;
  }
  if (edge.edge_type === "HAS_READINESS_BLOCKER") {
    return 2;
  }
  if (edge.edge_type === "APPLIES_TO_REVIEW" || edge.edge_type === "GENERATES_RULE") {
    return 1.4;
  }
  return 0.65;
}

function linkParticles(edge) {
  if (state.selectedEdgeId === edge.edge_id) {
    return 3;
  }
  if (
    state.selectedNodeId &&
    (edge.source_node_id === state.selectedNodeId || edge.target_node_id === state.selectedNodeId)
  ) {
    return 1;
  }
  return 0;
}

function nodeTooltip(node) {
  const citation = node.provenance?.citation_label || node.provenance?.source_record_id || "";
  return [node.label, node.node_type, node.display_status, citation].filter(Boolean).join(" | ");
}

function nodeSearchText(node) {
  return [
    node.node_id,
    node.node_type,
    node.label,
    node.display_status,
    node.review_readiness_status,
    flattenObject(node.provenance),
    flattenObject(node.currentness_metadata),
    flattenObject(node.metadata),
    ...(node.readiness_blockers || [])
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

function statusValues(item) {
  return compactValues([item.display_status, item.review_readiness_status]);
}

function authorityCategoryValues(item) {
  return compactValues([
    item.provenance?.authority_category,
    item.metadata?.authority_category
  ]);
}

function authorityFamilyValues(item) {
  return compactValues([
    item.provenance?.authority_family_id,
    item.metadata?.authority_family_id
  ]);
}

function documentRoleValues(item) {
  return compactValues([
    item.provenance?.document_role,
    item.metadata?.document_role,
    item.currentness_metadata?.document_role
  ]);
}

function currentnessValues(item) {
  return compactValues([
    item.currentness_metadata?.currentness_status,
    item.currentness_metadata?.supersession_status,
    item.currentness_metadata?.source_partition,
    item.provenance?.source_partition
  ]);
}

function readinessBlockerValues(item) {
  return compactValues([
    ...(item.readiness_blockers || []),
    item.provenance?.blocker_type,
    item.metadata?.blocker_type,
    item.currentness_metadata?.blocker_type
  ]);
}

function nodeEdgeTypeValues(item) {
  return compactValues([item.node_type || item.edge_type]);
}

function evidenceKindValues(item) {
  return compactValues([
    item.provenance?.evidence_type,
    item.metadata?.evidence_type,
    item.metadata?.claim_type,
    item.metadata?.basis_type,
    item.currentness_metadata?.basis_type
  ]);
}

function forestUnitValues(item) {
  return compactValues([
    item.provenance?.forest_unit_id,
    item.provenance?.forest_code,
    item.metadata?.forest_unit_id,
    item.metadata?.forest_code,
    item.currentness_metadata?.forest_unit_id,
    item.currentness_metadata?.forest_code
  ]);
}

function reviewPhaseValues(item) {
  return compactValues([
    item.provenance?.review_phase,
    item.metadata?.review_phase,
    item.metadata?.phase,
    item.node_type === "applicability_decision" ? "applicability" : "",
    item.node_type === "generated_rule" ? "generated_rule_pack" : "",
    item.node_type === "compliance_finding" ? "compliance_review" : "",
    item.edge_type === "PRODUCES_APPLICABILITY_DECISION" ? "applicability" : "",
    item.edge_type === "GENERATES_RULE" ? "generated_rule_pack" : "",
    item.edge_type === "SUPPORTS_COMPLIANCE_FINDING" ? "compliance_review" : ""
  ]);
}

function compactValues(values) {
  return values
    .flatMap((value) => (Array.isArray(value) ? value : [value]))
    .filter((value) => value !== null && value !== undefined && String(value).trim() !== "")
    .map((value) => String(value));
}

function replaceOptions(select, values, selectedValue) {
  replaceOptionsFromPairs(
    select,
    values.map((value) => ({ value, label: value })),
    selectedValue
  );
}

function formatOptionLabel(value, filterId = "") {
  const raw = String(value);
  const label = raw.replaceAll("_", " ");
  if (filterId === "nodeEdgeType") {
    return raw === raw.toUpperCase() ? `edge: ${label.toLowerCase()}` : `node: ${label}`;
  }
  if (filterId === "evidenceKind") {
    return `evidence/basis: ${label}`;
  }
  return label;
}

function replaceOptionsFromPairs(select, options, selectedValue) {
  select.innerHTML = "";
  for (const optionInfo of options) {
    const option = document.createElement("option");
    option.value = optionInfo.value;
    option.textContent = optionInfo.label;
    if (optionInfo.grounding) {
      option.title = optionInfo.grounding;
      option.dataset.grounding = optionInfo.grounding;
    }
    select.append(option);
  }
  if (options.some((option) => option.value === selectedValue)) {
    select.value = selectedValue;
  }
}

function uniqueValues(values) {
  return [...new Set(values.filter((value) => value !== null && value !== undefined && value !== ""))]
    .map((value) => String(value))
    .sort((a, b) => a.localeCompare(b));
}

function detailMarkup(rows) {
  const visibleRows = rows.filter(([, value]) => value !== null && value !== undefined && value !== "");
  if (visibleRows.length === 0) {
    return "";
  }
  const inner = visibleRows
    .map(([key, value]) => `<dt>${escapeHtml(key)}</dt><dd>${escapeHtml(String(value))}</dd>`)
    .join("");
  return `<dl class="detail-meta">${inner}</dl>`;
}

function badgeRow(values) {
  const badges = compactValues(values)
    .map((value) => `<span class="badge">${escapeHtml(value.replaceAll("_", " "))}</span>`)
    .join("");
  return badges ? `<div class="badge-row">${badges}</div>` : "";
}

function jsonBlock(label, value) {
  if (!value || (Array.isArray(value) && value.length === 0)) {
    return "";
  }
  return `<div><div class="badge-row"><span class="badge">${escapeHtml(label)}</span></div><pre class="json-block">${escapeHtml(JSON.stringify(value, null, 2))}</pre></div>`;
}

function flattenObject(value) {
  if (!value) {
    return "";
  }
  if (typeof value !== "object") {
    return String(value);
  }
  return Object.values(value).map(flattenObject).join(" ");
}

function validationPassedText() {
  const summary = state.graph?.summary || {};
  const validation = state.graph?.validation || {};
  const passed = summary.validation_passed ?? validation.passed;
  if (passed === true) {
    return "validation passed";
  }
  if (passed === false) {
    return "validation failed";
  }
  return "validation unknown";
}

function setStatus(message) {
  els.statusLine.textContent = message;
}

function toCamel(id) {
  return id.replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
