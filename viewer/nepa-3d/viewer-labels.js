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
  if (!state.labelsEnabled) {
    state.labelNodeLevels = new Map();
    state.labelStats = { overview: 0, focus: 0, detail: 0 };
    return;
  }
  const descriptors = new Map();
  const addLabel = (node, level) => {
    if (!node) {
      return;
    }
    const current = descriptors.get(node.node_id);
    if (!current || level < current.level) {
      descriptors.set(node.node_id, { level });
    }
  };

  const scene = activeDemoScene();
  const renderedIds = new Set(filtered.nodes.map((node) => node.node_id));
  for (const node of filtered.nodes) {
    if (node.node_type === "source_set" || node.node_type === "review") {
      addLabel(node, 0);
    }
    if (state.selectedNodeId === node.node_id || state.spotlightNodeIds.has(node.node_id)) {
      addLabel(node, 0);
    }
  }

  for (const node of topLabelCandidates(filtered.nodes, scene, LABEL_NODE_BUDGETS.overview)) {
    addLabel(node, 0);
  }
  for (const node of topLabelCandidates(filtered.nodes, scene, LABEL_NODE_BUDGETS.focus)) {
    addLabel(node, 1);
  }
  for (const node of topLabelCandidates(filtered.nodes, scene, LABEL_NODE_BUDGETS.detail)) {
    addLabel(node, 2);
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
  const readinessClass = readinessSemanticClass(node);
  if (state.spotlightNodeIds.has(node.node_id)) {
    return "#d7932f";
  }
  if (readinessClass !== "none") {
    return READINESS_SEMANTIC_COLORS[readinessClass] || STATUS_COLORS.readiness_blocked;
  }
  return STATUS_COLORS[node.display_status] || NODE_TYPE_COLORS[node.node_type] || "#7f7b73";
}

function edgeColor(edge) {
  const readinessClass = readinessSemanticClass(edge);
  if (state.spotlightEdgeIds.has(edge.edge_id)) {
    return "rgba(215, 147, 47, 0.92)";
  }
  if (readinessClass === "blocker_relationship_edge" || readinessClass === "blocked_relationship_edge") {
    return READINESS_SEMANTIC_COLORS[readinessClass];
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
  const readinessClass = readinessSemanticClass(edge);
  if (state.selectedEdgeId && state.selectedEdgeId === edge.edge_id) {
    return 3;
  }
  if (state.spotlightEdgeIds.has(edge.edge_id)) {
    return 3;
  }
  if (readinessClass === "blocker_relationship_edge") {
    return 2;
  }
  if (readinessClass === "blocked_relationship_edge") {
    return 1.4;
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
  const readinessClass = readinessSemanticClass(node);
  return [node.label, node.node_type, node.display_status, readinessClass !== "none" ? readinessSemanticLabel(readinessClass) : "", citation]
    .filter(Boolean)
    .join(" | ");
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
