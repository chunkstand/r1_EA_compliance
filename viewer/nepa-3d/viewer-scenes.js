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
