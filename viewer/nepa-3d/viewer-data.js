async function loadManifest() {
  try {
    const response = await fetch(MANIFEST_PATH, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`manifest HTTP ${response.status}`);
    }
    const fallbackManifest = await response.json();
    state.manifest = await resolveCurrentViewerManifest(fallbackManifest);
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

async function resolveCurrentViewerManifest(fallbackManifest) {
  const manifest = JSON.parse(JSON.stringify(fallbackManifest));
  const discoveredSourceSets = await discoverGraphSourceSetDatasets();
  if (discoveredSourceSets.length === 0) {
    return manifest;
  }
  const catalogSourceSetId = await loadCatalogSourceSetId();
  const preferredSourceSet =
    discoveredSourceSets.find((dataset) => dataset.source_set_id === catalogSourceSetId) ||
    discoveredSourceSets[0];
  const reviewDatasets = await discoverReviewDatasets(preferredSourceSet.source_set_id);
  manifest.datasets = discoveredSourceSets.concat(reviewDatasets);
  manifest.default_source_set_id = preferredSourceSet.source_set_id;
  manifest.default_review_id = reviewDatasets[0]?.review_id || "";
  return manifest;
}

async function loadCatalogSourceSetId() {
  const payload = await fetchJsonOrNull(CATALOG_SOURCE_SET_MANIFEST_PATH);
  return payload?.data?.source_set_id || "";
}

async function discoverGraphSourceSetDatasets() {
  const directories = await listDirectoryNames(DERIVED_SOURCE_SETS_ROOT_PATH);
  const candidates = [];
  for (const directoryName of directories) {
    if (!directoryName.startsWith("source-set-")) {
      continue;
    }
    const summaryPath = `${DERIVED_SOURCE_SETS_ROOT_PATH}${directoryName}/knowledge_graph/nepa_3d_graph_summary.json`;
    const summaryPayload = await fetchJsonOrNull(summaryPath);
    const sourceSetId = summaryPayload?.data?.source_set_id;
    if (!sourceSetId) {
      continue;
    }
    candidates.push({
      dataset_id: sourceSetId,
      label: `Source Set: ${sourceSetId}`,
      scope: "source_set",
      source_set_id: sourceSetId,
      review_id: null,
      graph_path: `${DERIVED_SOURCE_SETS_ROOT_PATH}${sourceSetId}/knowledge_graph/nepa_3d_graph.json`,
      summary_path: summaryPath,
      validation_path: `${DERIVED_SOURCE_SETS_ROOT_PATH}${sourceSetId}/knowledge_graph/nepa_3d_graph_validation.json`,
      last_modified: summaryPayload.lastModified
    });
  }
  return candidates.sort(compareLastModifiedDesc);
}

async function discoverReviewDatasets(sourceSetId) {
  if (!sourceSetId) {
    return [];
  }
  const directories = await listDirectoryNames(REVIEWS_ROOT_PATH);
  const candidates = [];
  for (const directoryName of directories) {
    const summaryPath = `${REVIEWS_ROOT_PATH}${directoryName}/knowledge_graph/nepa_3d_graph_summary.json`;
    const summaryPayload = await fetchJsonOrNull(summaryPath);
    const summary = summaryPayload?.data;
    if (!summary || summary.source_set_id !== sourceSetId || !summary.review_id) {
      continue;
    }
    const reviewId = summary.review_id;
    candidates.push({
      dataset_id: reviewId,
      label: `Review Overlay: ${reviewId}`,
      scope: "review_overlay",
      source_set_id: sourceSetId,
      review_id: reviewId,
      graph_path: `${REVIEWS_ROOT_PATH}${directoryName}/knowledge_graph/nepa_3d_graph.json`,
      summary_path: summaryPath,
      validation_path: `${REVIEWS_ROOT_PATH}${directoryName}/knowledge_graph/nepa_3d_graph_validation.json`,
      last_modified: summaryPayload.lastModified
    });
  }
  return candidates.sort(compareLastModifiedDesc);
}

async function listDirectoryNames(directoryPath) {
  try {
    const response = await fetch(directoryPath, { cache: "no-store" });
    if (!response.ok) {
      return [];
    }
    const html = await response.text();
    const parser = new DOMParser();
    const documentRoot = parser.parseFromString(html, "text/html");
    const names = [];
    for (const link of documentRoot.querySelectorAll("a[href]")) {
      const href = link.getAttribute("href") || "";
      if (!href || href === "../" || !href.endsWith("/")) {
        continue;
      }
      names.push(decodeURIComponent(href.replace(/\/$/, "")));
    }
    return uniqueValues(names);
  } catch {
    return [];
  }
}

async function fetchJsonOrNull(path) {
  try {
    const response = await fetch(path, { cache: "no-store" });
    if (!response.ok) {
      return null;
    }
    return {
      data: await response.json(),
      lastModified: Date.parse(response.headers.get("last-modified") || "") || 0
    };
  } catch {
    return null;
  }
}

function compareLastModifiedDesc(left, right) {
  return (right.last_modified || 0) - (left.last_modified || 0);
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
