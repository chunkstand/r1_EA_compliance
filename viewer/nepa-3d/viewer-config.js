const MANIFEST_PATH = "manifest.json";
const DEFAULT_LENS_SOURCE_SET = "readiness_blockers";
const DEFAULT_LENS_REVIEW = "package_applicability";
const DEFAULT_DEMO_REVIEW_ID = "v1-cg-ecid-compliance-review";
const DEMO_START_SCENE_ID = "full_graph";
const CUSTOM_DEMO_SCENE_ID = "custom";
const DETAIL_RAIL_STORAGE_KEY = "nepa-3d-detail-rail-collapsed-v2";
const NODE_LABELS_STORAGE_KEY = "nepa-3d-show-node-labels";
const CATALOG_SOURCE_SET_MANIFEST_PATH = "../../source_library/catalog/source_set_manifest.json";
const DERIVED_SOURCE_SETS_ROOT_PATH = "../../source_library/derived/";
const REVIEWS_ROOT_PATH = "../../source_library/reviews/";
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
const READINESS_SEMANTIC_LABELS = {
  synthetic_blocker_node: "Synthetic blocker node",
  blocked_domain_node: "Blocked domain node",
  blocker_relationship_edge: "Explicit blocker edge",
  blocked_relationship_edge: "Blocked relationship edge",
  none: "No readiness class"
};
const READINESS_SEMANTIC_COLORS = {
  synthetic_blocker_node: "#b13d38",
  blocked_domain_node: "#cf6c45",
  blocker_relationship_edge: "rgba(177, 61, 56, 0.82)",
  blocked_relationship_edge: "rgba(207, 108, 69, 0.64)"
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
    reviewId: "",
    lensId: "all",
    filters: {},
    neighborDepth: 1,
    degreeThreshold: 120,
    hideHighDegree: false,
    capabilityTitle: "Full validated corpus graph",
    capabilityCopy:
      "Shows the complete validated source-set corpus graph before demo scenes narrow to specific reviewer questions.",
    proofLabels: ["all node and edge tables are loaded", "validation remains visible", "advanced filters can narrow the view"],
    graphLabel: "Full graph",
    graphSubLabel: "Complete validated source-set corpus",
    labelNodeTypes: [
      "source_set",
      "review",
      "authority_family",
      "source_record",
      "artifact",
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
  labelStats: { overview: 0, focus: 0, detail: 0 },
  labelsEnabled: false
};

const els = {};
