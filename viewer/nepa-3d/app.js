const MANIFEST_PATH = "manifest.json";
const DEFAULT_LENS_SOURCE_SET = "readiness_blockers";
const DEFAULT_LENS_REVIEW = "package_applicability";
const DEFAULT_DEMO_REVIEW_ID = "v1-cg-ecid-compliance-review";
const DEMO_START_SCENE_ID = "applicability";
const CUSTOM_DEMO_SCENE_ID = "custom";
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
const LABEL_TIER_ORDER = ["overview", "focus", "detail"];
const LABEL_TIER_COPY = {
  overview: "Overview labels",
  focus: "Focus labels",
  detail: "Detail labels"
};
const LABEL_NODE_BUDGETS = {
  overview: 7,
  focus: 22,
  detail: 70
};
const LABEL_DISTANCE_THRESHOLDS = {
  focus: 540,
  detail: 330
};
const DEMO_SCENES = [
  {
    id: "source_library",
    label: "Source library",
    reviewId: "",
    lensId: "all",
    filters: { nodeEdgeType: "source_record" },
    neighborDepth: 1,
    degreeThreshold: 90,
    hideHighDegree: false,
    capabilityTitle: "Auditable source library",
    capabilityCopy:
      "Shows workbook source-row identity, source records, and artifact links before the review overlay adds applicability decisions.",
    proofLabels: ["one source record per catalog row", "artifact links remain visible", "source-set boundary is explicit"],
    graphLabel: "Source library",
    graphSubLabel: "Catalog records and source artifacts",
    labelNodeTypes: ["source_set", "source_record", "artifact"]
  },
  {
    id: "authority_universe",
    label: "Authority graph",
    reviewId: DEFAULT_DEMO_REVIEW_ID,
    lensId: "authority_currentness",
    filters: {},
    neighborDepth: 1,
    degreeThreshold: 90,
    hideHighDegree: false,
    capabilityTitle: "Current authority graph",
    capabilityCopy:
      "Shows the authority families and source records used to make currentness and supersession status reviewable.",
    proofLabels: ["authority families are graph nodes", "currentness is data-backed", "superseded material is separated"],
    graphLabel: "Authority graph",
    graphSubLabel: "Authority families, sources, currentness",
    labelNodeTypes: ["authority_family", "source_record", "readiness_blocker"]
  },
  {
    id: "applicability",
    label: "Applicability",
    reviewId: DEFAULT_DEMO_REVIEW_ID,
    lensId: "package_applicability",
    filters: {},
    neighborDepth: 1,
    degreeThreshold: 90,
    hideHighDegree: false,
    capabilityTitle: "Package-specific applicability",
    capabilityCopy:
      "Shows how the V1 review partitions candidate authorities into applicable and not-applicable decisions for the Custer Gallatin package.",
    proofLabels: ["applicability is explicit", "non-applicable authorities stay visible", "decisions are tied to the review id"],
    graphLabel: "Applicability",
    graphSubLabel: "Applicable and non-applicable authority decisions",
    labelNodeTypes: ["review", "authority_family", "rule_template", "applicability_decision"]
  },
  {
    id: "evidence_path",
    label: "Evidence path",
    reviewId: DEFAULT_DEMO_REVIEW_ID,
    lensId: "evidence_path",
    filters: {},
    neighborDepth: 1,
    degreeThreshold: 90,
    hideHighDegree: false,
    spotlight: "evidence_path",
    capabilityTitle: "Evidence-to-finding trace",
    capabilityCopy:
      "Spotlights one graph-derived path from source record to artifact, chunk, evidence span, claim, rule, and compliance finding.",
    proofLabels: ["citation path is clickable", "rule support is traceable", "finding support is evidence-backed"],
    graphLabel: "Evidence path",
    graphSubLabel: "Source record to compliance finding",
    labelNodeTypes: [
      "source_record",
      "artifact",
      "chunk",
      "evidence_span",
      "source_claim",
      "rule_template",
      "applicability_decision",
      "generated_rule",
      "compliance_finding"
    ]
  },
  {
    id: "forest_plan",
    label: "Forest Plan",
    reviewId: DEFAULT_DEMO_REVIEW_ID,
    lensId: "forest_plan",
    filters: { forestUnit: "custer-gallatin-nf" },
    neighborDepth: 1,
    degreeThreshold: 90,
    hideHighDegree: false,
    capabilityTitle: "Forest-plan legibility",
    capabilityCopy:
      "Shows Region 1 forest-plan profiles and Custer Gallatin components as graph-visible review evidence, with other profiles kept distinct.",
    proofLabels: ["forest units are filterable", "plan components stay linked", "scope is visible to reviewers"],
    graphLabel: "Forest Plan",
    graphSubLabel: "Forest units, plans, and components",
    labelNodeTypes: ["forest_unit", "forest_plan", "forest_plan_component"]
  },
  {
    id: "readiness",
    label: "Readiness",
    reviewId: DEFAULT_DEMO_REVIEW_ID,
    lensId: "readiness_blockers",
    filters: {},
    neighborDepth: 1,
    degreeThreshold: 90,
    hideHighDegree: false,
    capabilityTitle: "Promotion-risk view",
    capabilityCopy:
      "Shows readiness blockers and graph-visible reasons why broader Region 1 expansion remains separate from the promoted V1 review.",
    proofLabels: ["readiness is an artifact field", "blockers are not hidden", "layout cannot promote the review"],
    graphLabel: "Readiness",
    graphSubLabel: "Promotion blockers remain visible",
    labelNodeTypes: ["readiness_blocker", "source_record", "forest_unit", "authority_family"]
  },
  {
    id: "full_graph",
    label: "Full graph",
    reviewId: DEFAULT_DEMO_REVIEW_ID,
    lensId: "all",
    filters: {},
    neighborDepth: 1,
    degreeThreshold: 120,
    hideHighDegree: false,
    capabilityTitle: "Full validated graph",
    capabilityCopy:
      "Shows the complete validated review overlay when a client wants to see the breadth behind the curated scenes.",
    proofLabels: ["all node and edge tables are loaded", "validation remains visible", "advanced filters can narrow the view"],
    graphLabel: "Full graph",
    graphSubLabel: "Complete validated review overlay",
    labelNodeTypes: [
      "review",
      "authority_family",
      "applicability_decision",
      "generated_rule",
      "compliance_finding",
      "forest_unit",
      "readiness_blocker"
    ]
  }
];

const state = {
  graphApi: null,
  manifest: null,
  dataset: null,
  graph: null,
  graphControls: null,
  nodes: [],
  edges: [],
  nodeIndex: new Map(),
  adjacency: new Map(),
  degree: new Map(),
  filterValues: {},
  selectedNodeId: null,
  selectedEdgeId: null,
  currentRender: { nodes: [], edges: [] },
  activeDemoSceneId: DEMO_START_SCENE_ID,
  applyingDemoScene: false,
  spotlightNodeIds: new Set(),
  spotlightEdgeIds: new Set(),
  spotlightSteps: [],
  spotlightTitle: "",
  labelNodeLevels: new Map(),
  labelSprites: new Map(),
  labelZoomTier: "overview",
  labelStats: { overview: 0, focus: 0, detail: 0 }
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
    "demo-reset",
    "demo-scenes",
    "lens-select",
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
    "graph-scene-label",
    "graph-root",
    "status-line",
    "legend",
    "capability-panel",
    "detail-panel",
    "validation-panel"
  ];
  for (const id of ids) {
    els[toCamel(id)] = document.getElementById(id);
  }
}

function bindEvents() {
  els.sourceSetSelect.addEventListener("change", () => {
    markCustomScene();
    populateReviewSelector();
    loadSelectedDataset();
  });
  els.reviewSelect.addEventListener("change", () => {
    markCustomScene();
    loadSelectedDataset();
  });
  els.lensSelect.addEventListener("change", () => {
    markCustomScene();
    populateFilterOptions({ preserveSelected: true });
    renderGraph();
  });
  els.graphSearch.addEventListener("input", () => {
    markCustomScene();
    renderGraph();
  });
  els.graphFileInput.addEventListener("change", loadFileDataset);
  els.neighborDepth.addEventListener("input", () => {
    markCustomScene({ keepSpotlight: true });
    els.neighborDepthValue.value = els.neighborDepth.value;
    renderGraph();
  });
  els.degreeThreshold.addEventListener("input", () => {
    markCustomScene({ keepSpotlight: true });
    els.degreeThresholdValue.value = els.degreeThreshold.value;
    renderGraph();
  });
  els.hideHighDegree.addEventListener("change", () => {
    markCustomScene({ keepSpotlight: true });
    renderGraph();
  });
  els.pinSelected.addEventListener("change", updatePinnedSelection);
  els.fitGraph.addEventListener("click", fitGraph);
  els.resetLayout.addEventListener("click", resetLayout);
  els.clearFilters.addEventListener("click", clearFilters);
  els.demoReset.addEventListener("click", () => {
    applyDemoScene(DEMO_START_SCENE_ID);
  });
  els.demoScenes.addEventListener("click", (event) => {
    const button = event.target.closest("[data-demo-scene-id]");
    if (button) {
      applyDemoScene(button.dataset.demoSceneId);
    }
  });
  els.capabilityPanel.addEventListener("click", (event) => {
    const button = event.target.closest("[data-node-id]");
    if (button) {
      selectCapabilityNode(button.dataset.nodeId);
    }
  });
  els.exportShot.addEventListener("click", exportScreenshot);
  els.exportState.addEventListener("click", exportViewerState);
  for (const filter of FILTER_DEFINITIONS) {
    document.getElementById(filter.selector).addEventListener("change", () => {
      markCustomScene();
      renderGraph();
    });
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

async function loadManifest() {
  try {
    const response = await fetch(MANIFEST_PATH, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`manifest HTTP ${response.status}`);
    }
    state.manifest = await response.json();
    populateSourceSetSelector();
    populateReviewSelector(DEFAULT_DEMO_REVIEW_ID);
    renderDemoScenes();
    await applyDemoScene(DEMO_START_SCENE_ID);
  } catch (error) {
    setStatus(`Manifest unavailable: ${error.message}. Use Graph JSON file input.`);
    renderDemoScenes();
    renderCapabilityPanel();
    renderEmptyDetails();
  }
}

function populateSourceSetSelector() {
  const sourceSetIds = uniqueValues(
    state.manifest.datasets.map((dataset) => dataset.source_set_id).filter(Boolean)
  );
  replaceOptions(els.sourceSetSelect, sourceSetIds, state.manifest.default_source_set_id);
}

function populateReviewSelector(selectedReviewId = state.manifest.default_review_id || "") {
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
  replaceOptionsFromPairs(els.reviewSelect, options, selectedReviewId);
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
  markCustomScene();
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

function renderDemoScenes() {
  if (!els.demoScenes) {
    return;
  }
  els.demoScenes.innerHTML = DEMO_SCENES.map(
    (scene) =>
      `<button class="demo-scene-button" type="button" data-demo-scene-id="${escapeHtml(scene.id)}" aria-pressed="false">${escapeHtml(scene.label)}</button>`
  ).join("");
  setActiveDemoButton();
}

async function applyDemoScene(sceneId) {
  const scene = demoSceneById(sceneId) || demoSceneById(DEMO_START_SCENE_ID);
  if (!scene) {
    return;
  }
  state.applyingDemoScene = true;
  state.activeDemoSceneId = scene.id;
  clearSpotlight();
  state.selectedNodeId = null;
  state.selectedEdgeId = null;
  renderEmptyDetails();
  setActiveDemoButton();
  try {
    if (state.manifest) {
      const sourceSetId = scene.sourceSetId || state.manifest.default_source_set_id;
      if (sourceSetId && els.sourceSetSelect.value !== sourceSetId) {
        els.sourceSetSelect.value = sourceSetId;
        populateReviewSelector(scene.reviewId || "");
      }
      const reviewId = scene.reviewId ?? DEFAULT_DEMO_REVIEW_ID;
      if (els.reviewSelect.value !== reviewId) {
        els.reviewSelect.value = reviewId;
      }
      const expectedReviewId = reviewId || null;
      const needsDataset =
        !state.dataset ||
        state.dataset.source_set_id !== sourceSetId ||
        (state.dataset.review_id || null) !== expectedReviewId;
      if (needsDataset) {
        await loadSelectedDataset();
      }
    }
    setLensControl(scene.lensId);
    populateFilterOptions();
    resetFilterControls();
    setLayoutControls(scene);
    setFilterControls(scene.filters || {});
    if (scene.spotlight === "evidence_path") {
      buildEvidencePathSpotlight();
    }
    renderGraph();
  } finally {
    state.applyingDemoScene = false;
    setActiveDemoButton();
  }
}

function demoSceneById(sceneId) {
  return DEMO_SCENES.find((scene) => scene.id === sceneId);
}

function activeDemoScene() {
  return demoSceneById(state.activeDemoSceneId);
}

function markCustomScene({ keepSpotlight = false } = {}) {
  if (state.applyingDemoScene) {
    return;
  }
  state.activeDemoSceneId = CUSTOM_DEMO_SCENE_ID;
  if (!keepSpotlight) {
    clearSpotlight();
  }
  setActiveDemoButton();
}

function setActiveDemoButton() {
  if (!els.demoScenes) {
    return;
  }
  for (const button of els.demoScenes.querySelectorAll("[data-demo-scene-id]")) {
    const active = button.dataset.demoSceneId === state.activeDemoSceneId;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", active ? "true" : "false");
  }
}

function resetFilterControls() {
  els.graphSearch.value = "";
  for (const filter of FILTER_DEFINITIONS) {
    document.getElementById(filter.selector).value = "";
  }
}

function setFilterControls(filterValues) {
  for (const [filterId, value] of Object.entries(filterValues)) {
    const filter = FILTER_DEFINITIONS.find((candidate) => candidate.id === filterId);
    if (!filter) {
      continue;
    }
    const select = document.getElementById(filter.selector);
    if ([...select.options].some((option) => option.value === value)) {
      select.value = value;
    }
  }
}

function setLensControl(lensId) {
  const nextLens = [...els.lensSelect.options].some((option) => option.value === lensId) ? lensId : "all";
  els.lensSelect.value = nextLens;
}

function setLayoutControls(scene) {
  els.neighborDepth.value = String(scene.neighborDepth ?? 1);
  els.neighborDepthValue.value = els.neighborDepth.value;
  els.degreeThreshold.value = String(scene.degreeThreshold ?? 90);
  els.degreeThresholdValue.value = els.degreeThreshold.value;
  els.hideHighDegree.checked = scene.hideHighDegree === true;
}

function clearSpotlight() {
  state.spotlightNodeIds = new Set();
  state.spotlightEdgeIds = new Set();
  state.spotlightSteps = [];
  state.spotlightTitle = "";
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
        const nodeIds = new Set(pathNodes.map((node) => node.node_id));
        const edgeIds = new Set(pathEdges.map((edge) => edge.edge_id));
        state.spotlightNodeIds = nodeIds;
        state.spotlightEdgeIds = edgeIds;
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
  renderLegend(filtered.nodes);
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
  els.graphSceneLabel.innerHTML = [
    `<div class="graph-scene-title">${escapeHtml(title)}</div>`,
    `<div class="graph-scene-subtitle">${escapeHtml(subtitle)}</div>`,
    `<div class="graph-label-mode">${escapeHtml(LABEL_TIER_COPY[state.labelZoomTier] || "Overview labels")}: ${state.labelStats[state.labelZoomTier] || 0} visible of ${filtered.nodes.length} nodes</div>`
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
    spotlight_node_count: state.spotlightNodeIds.size,
    spotlight_edge_count: state.spotlightEdgeIds.size,
    rendered_node_count: filtered.nodes.length,
    rendered_edge_count: filtered.edges.length,
    canvas_count: els.graphRoot.querySelectorAll("canvas").length,
    validation_passed: state.graph?.summary?.validation_passed === true
  };
}

function graphNodeObject(node, sphereGeometry) {
  const group = new window.THREE.Group();
  const material = new window.THREE.MeshLambertMaterial({
    color: nodeColor(node),
    transparent: true,
    opacity: state.spotlightNodeIds.has(node.node_id) || node.node_type === "readiness_blocker" ? 0.95 : 0.82
  });
  const mesh = new window.THREE.Mesh(sphereGeometry, material);
  const scale = state.spotlightNodeIds.has(node.node_id)
    ? 2.7
    : node.node_type === "readiness_blocker" || node.display_status === "applicable"
      ? 2.2
      : 1;
  mesh.scale.setScalar(scale);
  group.add(mesh);

  const descriptor = nodeLabelDescriptor(node);
  if (descriptor) {
    const sprite = makeTextSprite(descriptor.text, descriptor);
    sprite.position.set(0, descriptor.level === 0 ? 24 : 18, 0);
    sprite.userData.labelLevel = descriptor.level;
    sprite.userData.nodeId = node.node_id;
    group.add(sprite);
    state.labelSprites.set(node.node_id, sprite);
  }
  return group;
}

function buildLabelPlan(filtered) {
  const descriptors = new Map();
  const addLabel = (node, level, reason = "") => {
    if (!node) {
      return;
    }
    const current = descriptors.get(node.node_id);
    if (!current || level < current.level) {
      descriptors.set(node.node_id, { level, reason });
    }
  };

  const scene = activeDemoScene();
  const renderedIds = new Set(filtered.nodes.map((node) => node.node_id));
  for (const node of filtered.nodes) {
    if (node.node_type === "source_set" || node.node_type === "review") {
      addLabel(node, 0, "graph root");
    }
    if (state.selectedNodeId === node.node_id || state.spotlightNodeIds.has(node.node_id)) {
      addLabel(node, 0, "selected path");
    }
  }

  for (const node of topLabelCandidates(filtered.nodes, scene, LABEL_NODE_BUDGETS.overview)) {
    addLabel(node, 0, "overview");
  }
  for (const node of topLabelCandidates(filtered.nodes, scene, LABEL_NODE_BUDGETS.focus)) {
    addLabel(node, 1, "focus");
  }
  for (const node of topLabelCandidates(filtered.nodes, scene, LABEL_NODE_BUDGETS.detail)) {
    addLabel(node, 2, "detail");
  }

  state.labelNodeLevels = new Map(
    [...descriptors.entries()].filter(([nodeId]) => renderedIds.has(nodeId))
  );
  state.labelStats = {
    overview: [...state.labelNodeLevels.values()].filter((descriptor) => descriptor.level <= 0).length,
    focus: [...state.labelNodeLevels.values()].filter((descriptor) => descriptor.level <= 1).length,
    detail: [...state.labelNodeLevels.values()].filter((descriptor) => descriptor.level <= 2).length
  };
}

function topLabelCandidates(nodes, scene, limit) {
  return nodes
    .map((node) => ({ node, score: labelScore(node, scene) }))
    .filter(({ score }) => score > 0)
    .sort((left, right) => right.score - left.score || left.node.label.localeCompare(right.node.label))
    .slice(0, limit)
    .map(({ node }) => node);
}

function labelScore(node, scene) {
  const labelTypes = new Set(scene?.labelNodeTypes || []);
  let score = 0;
  if (labelTypes.has(node.node_type)) {
    score += 90;
  }
  if (node.node_type === "source_set" || node.node_type === "review") {
    score += 120;
  }
  if (state.spotlightNodeIds.has(node.node_id) || state.selectedNodeId === node.node_id) {
    score += 160;
  }
  if (node.display_status === "applicable") {
    score += 30;
  }
  if (node.display_status === "readiness_blocked" || node.node_type === "readiness_blocker") {
    score += 55;
  }
  if (node.node_type === "forest_unit" || node.node_type === "compliance_finding") {
    score += 28;
  }
  if (node.node_type === "authority_family" || node.node_type === "generated_rule") {
    score += 18;
  }
  score += Math.min(35, state.degree.get(node.node_id) || 0);
  return score;
}

function nodeLabelDescriptor(node) {
  const labelPlan = state.labelNodeLevels.get(node.node_id);
  if (!labelPlan) {
    return null;
  }
  return {
    level: labelPlan.level,
    text: nodeLabelText(node, labelPlan),
    fill: nodeLabelFill(node, labelPlan.level),
    accent: nodeColor(node),
    scale: labelPlan.level === 0 ? 0.2 : labelPlan.level === 1 ? 0.17 : 0.145,
    maxWidth: labelPlan.level === 0 ? 360 : labelPlan.level === 1 ? 300 : 250,
    fontSize: labelPlan.level === 0 ? 24 : labelPlan.level === 1 ? 21 : 18
  };
}

function nodeLabelText(node, labelPlan) {
  if (state.spotlightNodeIds.has(node.node_id)) {
    const pathIndex = state.spotlightSteps.findIndex((step) => step.node_id === node.node_id);
    const prefix = pathIndex >= 0 ? `${pathIndex + 1}. ` : "";
    return `${prefix}${shortNodeType(node.node_type)}: ${compactLabel(node.label || node.node_id)}`;
  }
  if (state.selectedNodeId === node.node_id) {
    return `Selected: ${compactLabel(node.label || node.node_id)}`;
  }
  if (node.node_type === "review") {
    return activeDemoScene()?.graphLabel || "Review overlay";
  }
  if (node.node_type === "source_set") {
    return "Source set";
  }
  const type = labelPlan.level <= 1 ? `${shortNodeType(node.node_type)}: ` : "";
  return `${type}${compactLabel(node.label || node.node_id)}`;
}

function compactLabel(value) {
  return String(value)
    .replace(/^rule-template:nepa-ea-v0:[^:]+:/, "")
    .replace(/^source-set-/, "source-set ")
    .replace(/^v1-cg-ecid-compliance-review:?/, "")
    .replace(/\s+/g, " ")
    .trim();
}

function shortNodeType(nodeType) {
  const labels = {
    applicability_decision: "decision",
    authority_family: "authority",
    compliance_finding: "finding",
    evidence_span: "evidence",
    forest_plan_component: "component",
    forest_unit: "forest",
    generated_rule: "rule",
    readiness_blocker: "blocker",
    rule_template: "authority rule",
    source_claim: "claim",
    source_record: "source"
  };
  return labels[nodeType] || nodeType.replaceAll("_", " ");
}

function nodeLabelFill(node, level) {
  if (state.spotlightNodeIds.has(node.node_id)) {
    return "rgba(255, 250, 236, 0.96)";
  }
  if (level === 0) {
    return "rgba(255, 255, 255, 0.94)";
  }
  if (level === 1) {
    return "rgba(247, 246, 241, 0.9)";
  }
  return "rgba(255, 255, 255, 0.84)";
}

function makeTextSprite(text, descriptor) {
  const canvas = document.createElement("canvas");
  const context = canvas.getContext("2d");
  const fontSize = descriptor.fontSize;
  context.font = `700 ${fontSize}px Inter, ui-sans-serif, system-ui, sans-serif`;
  const paddingX = 16;
  const paddingY = 10;
  const lineHeight = Math.round(fontSize * 1.18);
  const lines = wrapLabelText(context, text, descriptor.maxWidth - paddingX * 2, descriptor.level === 2 ? 2 : 3);
  const textWidth = Math.min(
    descriptor.maxWidth - paddingX * 2,
    Math.max(...lines.map((line) => context.measureText(line).width), 80)
  );
  canvas.width = Math.ceil(textWidth + paddingX * 2);
  canvas.height = Math.ceil(lines.length * lineHeight + paddingY * 2);
  context.font = `700 ${fontSize}px Inter, ui-sans-serif, system-ui, sans-serif`;
  context.textBaseline = "top";
  context.fillStyle = descriptor.fill;
  roundRect(context, 0, 0, canvas.width, canvas.height, 12);
  context.fill();
  context.strokeStyle = descriptor.accent;
  context.lineWidth = descriptor.level === 0 ? 4 : 3;
  roundRect(context, 1.5, 1.5, canvas.width - 3, canvas.height - 3, 11);
  context.stroke();
  context.fillStyle = "#171713";
  lines.forEach((line, index) => {
    context.fillText(line, paddingX, paddingY + index * lineHeight);
  });

  const texture = new window.THREE.CanvasTexture(canvas);
  texture.minFilter = window.THREE.LinearFilter;
  const material = new window.THREE.SpriteMaterial({
    map: texture,
    transparent: true,
    depthTest: false,
    depthWrite: false
  });
  const sprite = new window.THREE.Sprite(material);
  sprite.scale.set(canvas.width * descriptor.scale, canvas.height * descriptor.scale, 1);
  sprite.renderOrder = 999;
  return sprite;
}

function wrapLabelText(context, text, maxWidth, maxLines) {
  const words = String(text).split(/\s+/).filter(Boolean);
  const lines = [];
  let current = "";
  for (const word of words) {
    const next = current ? `${current} ${word}` : word;
    if (context.measureText(next).width <= maxWidth || !current) {
      current = next;
    } else {
      lines.push(current);
      current = word;
      if (lines.length === maxLines - 1) {
        break;
      }
    }
  }
  if (current && lines.length < maxLines) {
    lines.push(current);
  }
  const consumed = lines.join(" ").split(/\s+/).filter(Boolean).length;
  if (consumed < words.length && lines.length > 0) {
    lines[lines.length - 1] = `${lines[lines.length - 1].replace(/[.,;:]+$/, "")}...`;
  }
  return lines.length > 0 ? lines : [String(text).slice(0, 48)];
}

function roundRect(context, x, y, width, height, radius) {
  context.beginPath();
  context.moveTo(x + radius, y);
  context.arcTo(x + width, y, x + width, y + height, radius);
  context.arcTo(x + width, y + height, x, y + height, radius);
  context.arcTo(x, y + height, x, y, radius);
  context.arcTo(x, y, x + width, y, radius);
  context.closePath();
}

function updateLabelVisibility() {
  const nextTier = labelTierForCamera();
  const changed = nextTier !== state.labelZoomTier;
  state.labelZoomTier = nextTier;
  const visibleLevel = LABEL_TIER_ORDER.indexOf(nextTier);
  for (const sprite of state.labelSprites.values()) {
    const show = sprite.userData.labelLevel <= visibleLevel;
    sprite.visible = show;
    if (sprite.material) {
      sprite.material.opacity = show ? 1 : 0;
    }
  }
  if (changed) {
    renderGraphSceneLabel();
    updateViewerReadyState(state.currentRender);
  }
}

function labelTierForCamera() {
  const distance = cameraDistance();
  if (distance <= LABEL_DISTANCE_THRESHOLDS.detail) {
    return "detail";
  }
  if (distance <= LABEL_DISTANCE_THRESHOLDS.focus) {
    return "focus";
  }
  return "overview";
}

function cameraDistance() {
  const controlsCamera = state.graphControls?.object;
  if (controlsCamera?.position) {
    return Math.hypot(controlsCamera.position.x, controlsCamera.position.y, controlsCamera.position.z);
  }
  const position = state.graphApi?.cameraPosition?.();
  if (position && typeof position.x === "number") {
    return Math.hypot(position.x, position.y, position.z);
  }
  const camera = state.graphApi?.camera?.();
  if (camera?.position) {
    return Math.hypot(camera.position.x, camera.position.y, camera.position.z);
  }
  return 620;
}

function nodeValue(node) {
  const degree = state.degree.get(node.node_id) || 1;
  if (state.spotlightNodeIds.has(node.node_id)) {
    return 2.4;
  }
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
  if (state.spotlightNodeIds.has(node.node_id)) {
    return "#d7932f";
  }
  return STATUS_COLORS[node.display_status] || NODE_TYPE_COLORS[node.node_type] || "#7f7b73";
}

function edgeColor(edge) {
  if (state.spotlightEdgeIds.has(edge.edge_id)) {
    return "rgba(215, 147, 47, 0.92)";
  }
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
  if (state.spotlightEdgeIds.has(edge.edge_id)) {
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
  if (state.spotlightEdgeIds.has(edge.edge_id)) {
    return 3;
  }
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
