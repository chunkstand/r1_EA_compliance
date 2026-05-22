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
  initializeLayoutState();
  initializeLabelState();
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
    "show-node-labels",
    "fit-graph",
    "reset-layout",
    "clear-filters",
    "export-shot",
    "export-state",
    "dataset-title",
    "graph-counts",
    "graph-scene-label",
    "graph-root",
    "viewer-shell",
    "detail-rail",
    "detail-rail-toggle",
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
  els.detailRailToggle.addEventListener("click", toggleDetailRail);
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
  els.showNodeLabels.addEventListener("change", updateNodeLabelPreference);
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
    resizeGraphViewport();
  });
}

function initializeLayoutState() {
  let collapsed = true;
  try {
    const storedValue = window.localStorage.getItem(DETAIL_RAIL_STORAGE_KEY);
    collapsed = storedValue === null ? true : storedValue === "true";
  } catch {
    collapsed = true;
  }
  applyDetailRailState(collapsed, { persist: false });
}

function toggleDetailRail() {
  const collapsed = !els.viewerShell.classList.contains("is-detail-collapsed");
  applyDetailRailState(collapsed);
}

function applyDetailRailState(collapsed, { persist = true } = {}) {
  els.viewerShell.classList.toggle("is-detail-collapsed", collapsed);
  els.detailRail.setAttribute("aria-hidden", collapsed ? "true" : "false");
  els.detailRail.hidden = collapsed;
  els.detailRailToggle.classList.toggle("is-collapsed", collapsed);
  els.detailRailToggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
  els.detailRailToggle.setAttribute(
    "aria-label",
    collapsed ? "Show right sidebar details" : "Hide right sidebar details"
  );
  if (persist) {
    try {
      window.localStorage.setItem(DETAIL_RAIL_STORAGE_KEY, String(collapsed));
    } catch {
      // Ignore storage failures; the viewer can still function without persistence.
    }
  }
  window.requestAnimationFrame(() => {
    resizeGraphViewport();
    window.setTimeout(() => {
      resizeGraphViewport();
    }, 220);
  });
}

function initializeLabelState() {
  let enabled = false;
  try {
    enabled = window.localStorage.getItem(NODE_LABELS_STORAGE_KEY) === "true";
  } catch {
    enabled = false;
  }
  state.labelsEnabled = enabled;
  els.showNodeLabels.checked = enabled;
}

function updateNodeLabelPreference() {
  state.labelsEnabled = els.showNodeLabels.checked;
  try {
    window.localStorage.setItem(NODE_LABELS_STORAGE_KEY, String(state.labelsEnabled));
  } catch {
    // Ignore storage failures; label visibility can still work for this session.
  }
  renderGraph();
}

function resizeGraphViewport() {
  if (state.graphApi) {
    state.graphApi.width(els.graphRoot.clientWidth).height(els.graphRoot.clientHeight);
  }
}
