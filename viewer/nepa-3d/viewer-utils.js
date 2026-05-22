function statusValues(item) {
  return compactValues([
    item.display_status,
    item.review_readiness_status,
    readinessSemanticClass(item) !== "none" ? readinessSemanticClass(item) : ""
  ]);
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
  if (filterId === "status" && READINESS_SEMANTIC_LABELS[raw]) {
    return `readiness class: ${READINESS_SEMANTIC_LABELS[raw].toLowerCase()}`;
  }
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

function readinessSemanticClass(item) {
  return item?.readiness_semantic_class || inferReadinessSemanticClass(item);
}

function inferReadinessSemanticClass(item) {
  if (!item) {
    return "none";
  }
  if (item.node_type === "readiness_blocker") {
    return "synthetic_blocker_node";
  }
  if (item.edge_type) {
    if (edgeTargetNodeType(item) === "readiness_blocker") {
      return "blocker_relationship_edge";
    }
    if (item.display_status === "readiness_blocked") {
      return "blocked_relationship_edge";
    }
    return "none";
  }
  if (item.display_status === "readiness_blocked") {
    return "blocked_domain_node";
  }
  return "none";
}

function edgeTargetNodeType(edge) {
  const targetNodeId = edge.target_node_id || edge.target?.node_id || edge.target;
  return state.nodeIndex.get(targetNodeId)?.node_type || "";
}

function readinessSemanticLabel(readinessClass) {
  return READINESS_SEMANTIC_LABELS[readinessClass] || String(readinessClass || "none").replaceAll("_", " ");
}

function readinessSemanticExplanation(item) {
  const readinessClass = readinessSemanticClass(item);
  if (readinessClass === "synthetic_blocker_node") {
    return "Explicit blocker record emitted by the exporter.";
  }
  if (readinessClass === "blocked_domain_node") {
    return "Domain surface remains visible, but its readiness state is blocked.";
  }
  if (readinessClass === "blocker_relationship_edge") {
    return "Explicit relationship from a subject to a blocker record.";
  }
  if (readinessClass === "blocked_relationship_edge") {
    return "Normal relationship shown as blocked because its owning surface is blocked.";
  }
  return "";
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
