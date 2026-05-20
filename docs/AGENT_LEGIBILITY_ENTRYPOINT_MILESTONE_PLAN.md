# Agent Legibility Entrypoint Milestone Plan

Date: 2026-05-20

Status: complete

Owner context: This is a fresh standalone follow-on milestone plan. It does not append to
`docs/AGENTIC_CODING_ARCHITECTURE_MILESTONE_PLAN.md`, which closed the earlier repo-wide
architecture-hardening lane. This packet is narrower: make the repo legible enough that a future
agent can receive a document request, route it to the correct existing document lane, refuse
unsupported requests, and prove why the chosen lane is the correct auditable path.

## Purpose

Close the cold-start routing gap between a user prompt and the correct document-producing lane.

The repo already contains strong document-producing systems:

- `project-sow-package` for proposed-action resource SOW requirements packages before a complete EA
  package exists;
- `ea-consistency-document` for responsible-official-facing decision support over audited review
  artifacts; and
- `draft-generate` for governed reviewed-draft packet generation over traced review artifacts.

The missing surface is the first step an agent should use. Today a future agent can eventually
assemble the right path from `README.md`, `docs/ARCHITECTURE.md`, `docs/OUTPUT_SCHEMAS.md`,
`docs/CURRENT_SYSTEM_STATE.md`, CLI help, and lane-specific configs, but there is no single
repo-local entrypoint that answers:

- which document lane fits this prompt;
- what input contract that lane requires;
- what the lane must refuse;
- which commands and artifacts prove the result is auditable and defensible; and
- what current-state or freshness facts must be rechecked before generation.

This milestone adds that entrypoint without changing the underlying document generators.

## Current Evidence

- `docs/ARCHITECTURE.md` correctly states that the system is artifact-first and already has
  decision-support and project-planning document lanes, but it does not provide a single
  prompt-to-lane operator path.
- `src/usfs_r1_ea_sources/cli.py` currently exposes a broad public CLI surface, and
  `python -m usfs_r1_ea_sources --help` enumerates the document lanes beside many non-document
  workflow commands.
- `config/draft_generation_v1.json` and
  `config/ea_consistency_decision_support_v1.json` are proving-review-specific and currently pin
  `review_id="v1-cg-ecid-compliance-review"` and
  `source_set_id="source-set-ba8d0feae79501b8"`.
- `docs/PROJECT_SOW_PACKAGE_RUNBOOK.md` is a concise reusable runbook, but there is no equivalent
  short first-stop doc for the decision-support and reviewed-draft lanes.
- `docs/schemas/` currently exposes the project SOW intake schema, but there is no generic
  normalized document-request schema for future agents.
- Current durable docs are high-signal but large: `README.md`, `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`, and `docs/OUTPUT_SCHEMAS.md` together require broad scanning before
  an agent can answer a narrow document-generation request.

## Goal

Add a small, explicit, repo-local agent entrypoint for document work:

- a concise `docs/AGENT_START_HERE.md` first-stop guide;
- a machine-readable lane registry that maps request classes to existing document lanes;
- a normalized document-request schema for agent-written request packets; and
- one dry-run routing command that chooses the correct lane or refuses the request without
  generating canonical document outputs.

## Non-Goals

- Do not change the workbook contract, downloader, catalog, extraction, retrieval, graph, claim,
  applicability, compliance-review, or evaluation semantics.
- Do not rewrite `project_sow_package.py`, `ea_consistency_decision_support.py`, or
  `draft_generation.py` as part of this packet.
- Do not generalize the proving-review data contracts beyond what is required to separate generic
  lane routing from review-specific bindings.
- Do not create new canonical reviewer-facing documents from raw prompts or raw workbook rows.
- Do not make legal sufficiency, responsible-official approval, final agency decision, or counsel
  signoff requests appear supported.
- Do not rerun corpus-building, network download, or broad `source_library/` regeneration workflows
  unless a freshness check explicitly requires a small bounded replay.

## Scope

In scope:

- agent-facing document-routing docs and schemas;
- a dry-run document-planning CLI entrypoint;
- lane registry/config ownership for document routing;
- refusal rules for unsupported legal-conclusion requests;
- focused tests and fixtures for prompt-to-lane routing;
- architecture-contract updates for the new command and owner module; and
- durable docs and handoff updates that tell future agents where to start.

Out of scope:

- new document-generation content logic inside the existing lane implementations;
- new real-package review content, new rule-pack logic, or new compliance reasoning;
- promotion of generic lane routing into a full autonomous generation loop; and
- full audit-packet unification across all document lanes.

## Owner Surfaces

- `docs/AGENT_START_HERE.md`
- `docs/ARCHITECTURE.md`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/SESSION_HANDOFF.md`
- `docs/architecture_contract.toml`
- `docs/schemas/document_request_v1.schema.json`
- `config/document_lanes_v1.json`
- `src/usfs_r1_ea_sources/document_plan.py`
- `src/usfs_r1_ea_sources/cli.py`
- `src/usfs_r1_ea_sources/cli_decision_support.py`
- `tests/test_document_plan.py`
- `tests/test_cli.py`
- `tests/fixtures/document_plan/`

## Placement Rules

- The new routing command is a planning facade, not a new document generator. It may read tracked
  configs, lane registry data, and required durable docs, but it must not re-implement downstream
  review or synthesis logic.
- Keep generic lane-routing metadata in `config/document_lanes_v1.json`. Review-specific proving
  bindings must remain in their lane-owned configs rather than being copied into the generic
  routing registry.
- Place the routing implementation in a small dedicated module such as
  `src/usfs_r1_ea_sources/document_plan.py`. Do not keep expanding `cli.py` or the large lane
  modules with mixed routing logic.
- The command should emit routing artifacts under a generated local directory such as
  `source_library/document_plans/<request_id>/`. Those artifacts are planning outputs only, not
  canonical review documents.
- `docs/AGENT_START_HERE.md` must stay concise and link outward to deeper docs. It should not
  duplicate large parts of `README.md` or `docs/OUTPUT_SCHEMAS.md`.
- Unsupported requests must fail closed with explicit refusal categories rather than falling
  through to a nearby lane.
- No new public command may claim to create legal sufficiency determinations, final agency
  decisions, or responsible-official approvals.

## Weak-Point Prevention Contract

- Weak point forecast: a new agent-facing entrypoint could bypass the existing audited review lanes
  and route prompts directly to raw source or workbook-driven generation.
  Owner surface: `config/document_lanes_v1.json`, `src/usfs_r1_ea_sources/document_plan.py`,
  `tests/test_document_plan.py`
  Prevention gate: the routing command must require explicit lane prerequisites and return
  `refuse` when the prompt asks for outputs that the repo does not support or when required lane
  inputs are absent.
  Fail threshold: the routing command selects `draft-generate` or
  `ea-consistency-document` without a review-backed request context, or selects
  `project-sow-package` for a review-artifact request.
  Controlled violation: submit a fixture that asks for a legal sufficiency determination or a
  final agency decision with no eligible lane; the command and tests must refuse it.
  Future-Codex misuse scenario: a later session treats the planner as a raw-text generator; the
  request-schema and refusal tests must block that misuse.

- Weak point forecast: the generic routing contract drifts into East-Crazies-only proving logic and
  stops being a reusable agent-facing surface.
  Owner surface: `config/document_lanes_v1.json`,
  `docs/schemas/document_request_v1.schema.json`,
  `tests/test_document_plan.py`
  Prevention gate: the generic lane registry and request schema must remain review-agnostic except
  for lane prerequisites. Review-specific IDs belong in lane-owned configs and fixtures only.
  Fail threshold: the generic routing registry hardcodes
  `v1-cg-ecid-compliance-review`, `source-set-ba8d0feae79501b8`, or another proving-review binding
  as the only valid generic route.
  Controlled violation: mutate the generic lane registry to pin a proving-review ID and require the
  focused routing tests to fail.
  Future-Codex misuse scenario: a later session adds another proving-review lane by copying ECID
  values into the generic registry instead of using lane-owned bindings; the drift test must fail.

- Weak point forecast: the new routing facade becomes another large hotspot or broadens `cli.py`
  instead of reducing cold-start cost.
  Owner surface: `src/usfs_r1_ea_sources/document_plan.py`,
  `src/usfs_r1_ea_sources/cli.py`,
  `src/usfs_r1_ea_sources/cli_decision_support.py`
  Prevention gate: the new routing implementation must live in a small dedicated module, the public
  command registration remains grouped by lane, and the architecture probe/hotspot readback must
  show no new >800-line file and no material hotspot growth caused by the planner.
  Fail threshold: this milestone primarily grows `cli.py` or another existing >800-line hotspot
  instead of adding a narrow owner module.
  Controlled violation: force the planner logic into `cli.py` in a controlled branch and require
  the architecture review/readback gate to fail the milestone.
  Future-Codex misuse scenario: a later session adds more document-routing branches into `cli.py`;
  the placement rules and line-count readback must flag that as wrong-surface work.

- Weak point forecast: the entrypoint docs become stale or too large, so future agents still have to
  scan the large canonical docs to know where to start.
  Owner surface: `docs/AGENT_START_HERE.md`, `README.md`, `docs/OUTPUT_SCHEMAS.md`,
  `docs/SESSION_HANDOFF.md`
  Prevention gate: the start-here doc must stay concise, must point to the active workbook and
  current canonical lanes, and must list exact starting commands plus refusal boundaries.
  Fail threshold: the start-here doc duplicates large schema prose, omits a current active lane, or
  lacks an explicit refusal path.
  Controlled violation: remove the refusal guidance or the lane-command mapping from the start-here
  doc and require focused doc/readback review to fail the milestone.
  Future-Codex misuse scenario: a later session updates one lane command or path but not the first
  stop doc; the closeout docs gate must catch that drift.

## Milestone Sequence

### Milestone 0 - Rebaseline The Active Document Lanes

Outcome label: reduced
Status: complete

Purpose: refresh the live routing facts before creating a new generic entrypoint.

Implementation tasks:

1. Recheck the active document-producing lanes and their current proofs from live docs and command
   surfaces:
   - `project-sow-package`
   - `ea-consistency-document`
   - `draft-generate`
   - `review-packet-index`
   - `final-qa-certification`
2. Recheck which commands are generation commands, which are validation-only commands, and which
   are proving-review-specific.
3. Refresh this plan before implementation if the active workbook, active source set, or proving
   review bindings changed since the plan was drafted.

Acceptance criteria:

- This plan records the exact current lane roster and the bounded scope of the first packet.
- The first milestone does not attempt to solve full audit-packet unification, lane-generic
  content generation, or corpus-state abstraction in the same closeout.

Rebaseline checkpoint on 2026-05-20:

- `python -m usfs_r1_ea_sources --help` still exposes the active lane roster:
  `project-sow-package`, `ea-consistency-document`, `draft-generate`,
  `review-packet-index`, and `final-qa-certification`.
- The first generic routing packet remains intentionally narrower than that
  full roster: it routes only `project_sow_requirements_package`,
  `decision_support_report`, and `reviewed_draft_packet`.
- `review-packet-index` and `final-qa-certification` were rechecked during
  rebaseline and are now explicitly marked as scoped-out adjacent review-sidecar
  lanes in `config/document_lanes_v1.json` rather than being silently omitted.

Verification:

```bash
git status -sb
PYTHONPATH=src python -m usfs_r1_ea_sources --help
rg -n "draft-generate|ea-consistency-document|project-sow-package|review-packet-index|final-qa-certification" src/usfs_r1_ea_sources/cli*.py docs/ARCHITECTURE.md docs/OUTPUT_SCHEMAS.md
```

Stop conditions:

- The live lane roster has materially changed and the plan has not been refreshed.
- The active generic route would require reopening current corpus-state claims rather than routing
  through existing lane contracts.

### Milestone 1 - Add The Generic Document-Lane Contract

Outcome label: resolved
Status: complete

Purpose: create one small machine-readable source of truth for prompt-to-lane routing.

Implementation tasks:

1. Add `config/document_lanes_v1.json` with one row per supported route:
   - `project_sow_requirements_package`
   - `decision_support_report`
   - `reviewed_draft_packet`
   - optional explicit non-generation helper lanes such as `review_packet_index` only if they are
     intentionally part of the agent-facing entrypoint.
2. For each lane, record:
   - supported request class;
   - required identifiers such as `review_id` or intake path;
   - allowed input mode;
   - refusal categories;
   - canonical generator command;
   - validation command;
   - canonical output directory family;
   - authoritative config files and runbook/doc links.
3. Add `docs/schemas/document_request_v1.schema.json` for the normalized agent-written request
   packet.
4. Add focused fixtures under `tests/fixtures/document_plan/` that prove routing to each supported
   lane plus unsupported request refusal.

Implemented work:

- added `config/document_lanes_v1.json` as the first machine-readable routing
  registry for the three primary generator lanes and the two explicitly
  scoped-out adjacent review-sidecar lanes;
- added `docs/schemas/document_request_v1.schema.json` for normalized agent
  request packets;
- added `src/usfs_r1_ea_sources/document_plan.py` with schema validation,
  registry validation, preview-command rendering, lane selection, and fail-closed
  refusal routing for unsupported legal-conclusion/final-decision requests; and
- added `tests/fixtures/document_plan/` plus `tests/test_document_plan.py` to
  lock the routed classes, generic-registry boundary, refusal categories, and
  missing-identifier behavior.

Acceptance criteria:

- The repo has one generic routing registry and one normalized request schema that future agents can
  inspect without opening lane internals first.
- The generic lane registry does not hardcode a proving-review ID or active source-set ID as part of
  the generic route definition.
- A request fixture exists for:
  `project_sow_requirements_package`,
  `decision_support_report`,
  `reviewed_draft_packet`,
  and at least one unsupported legal-conclusion request.

Required implementation artifacts:

- `config/document_lanes_v1.json`
- `docs/schemas/document_request_v1.schema.json`
- `tests/fixtures/document_plan/`
- `tests/test_document_plan.py`

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_document_plan.py -q
git diff --check
```

Stop conditions:

- The only way to define the generic lane registry is to copy proving-review-specific IDs into it.
- The request schema cannot distinguish supported planning support from unsupported legal-conclusion
  requests.

### Milestone 2 - Add The Dry-Run `document-plan` Command

Outcome label: resolved
Status: complete

Purpose: make one narrow public CLI entrypoint that chooses the right lane or refuses the request.

Implementation tasks:

1. Add a dedicated small owner module such as `src/usfs_r1_ea_sources/document_plan.py`.
2. Add the public command `document-plan` and register it through the CLI lane structure without
   broadening `cli.py` into another hotspot.
3. The command must:
   - accept a request file that validates against `document_request_v1.schema.json`;
   - load `config/document_lanes_v1.json`;
   - select exactly one supported lane or emit a refusal;
   - write a dry-run plan artifact family under `source_library/document_plans/<request_id>/`;
   - list the next commands, prerequisite artifacts, validation command, expected outputs, and
     refusal reasons.
4. The command must not generate canonical document outputs for the selected lane.
5. Add a focused CLI smoke test that proves the new public command is registered and that the
   architecture contract records the new command group or command placement correctly.

Acceptance criteria:

- `document-plan` can classify a supported project-SOW request, a supported decision-support
  request, a supported reviewed-draft request, and an unsupported legal-conclusion request.
- The dry-run plan artifacts list the exact downstream lane command, validation command, required
  identifiers, and canonical output family.
- The planner never writes lane-owned canonical outputs such as
  `project_sow_package.json`,
  `ea_consistency_decision_support.json`,
  or `draft_generation_package.json`.
- The planner module stays small and isolated; it does not turn `cli.py` or an existing large lane
  file into the new routing hotspot.

Required implementation artifacts:

- `src/usfs_r1_ea_sources/document_plan.py`
- CLI registration updates in `src/usfs_r1_ea_sources/cli.py` and/or
  `src/usfs_r1_ea_sources/cli_decision_support.py`
- `tests/test_document_plan.py`
- `tests/test_cli.py`
- `docs/architecture_contract.toml`

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_document_plan.py tests/test_cli.py tests/test_architecture_contract.py -q
PYTHONPATH=src uv run --extra dev ruff check src tests
python -m compileall src
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20
git diff --check
```

Stop conditions:

- The planner needs to inspect raw workbook rows or raw review artifacts to emulate downstream
  reasoning instead of routing to lane-owned commands.
- The planner requires a broad new architecture exception or materially broadens an existing
  hotspot to land.

Closeout on 2026-05-20:

- `document-plan` is now registered through `src/usfs_r1_ea_sources/cli.py` via the dedicated
  owner module `src/usfs_r1_ea_sources/cli_document_planning.py`.
- The planner writes `document_request.json`, `document_plan.json`, and `document_plan.md` under
  `source_library/document_plans/<request_id>/` and does not write canonical lane outputs.
- The routing registry now declares each supported lane's expected canonical output filenames so
  the dry-run plan artifacts can remain registry-driven rather than lane-hardcoded.

### Milestone 3 - Publish The First-Stop Agent Docs

Outcome label: resolved
Status: complete

Purpose: make the routing contract discoverable in one short read.

Implementation tasks:

1. Add `docs/AGENT_START_HERE.md` with:
   - current active workbook;
   - current live document lanes;
   - when to use `document-plan`;
   - one-line distinctions between project SOW, decision support, and reviewed draft generation;
   - refusal boundaries for unsupported legal-conclusion/final-decision requests; and
   - links to deeper lane docs.
2. Update `README.md`, `docs/ARCHITECTURE.md`, and `docs/OUTPUT_SCHEMAS.md` so the new planner and
   entrypoint docs are the documented first stop for agent-driven document work.
3. Update `docs/SESSION_HANDOFF.md` with the closeout hash, exact verification commands, and the
   next milestone routing.
4. Confirm whether `docs/TECH_DEBT_REGISTER.md` remains unchanged. Only add an entry if this packet
   deliberately introduces a temporary debt exception; otherwise explicitly leave the register
   untouched.

Acceptance criteria:

- A future agent can locate the right entrypoint from one short doc before reading the large
  canonical docs.
- The start-here doc explicitly states that this repo supports auditable planning support and
  reviewed-draft generation, not legal sufficiency determinations or final agency decisions.
- The durable docs agree on the new first-stop routing surface.

Required implementation artifacts:

- `docs/AGENT_START_HERE.md`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/SESSION_HANDOFF.md`

Verification:

```bash
git diff --check
rg -n "document-plan|AGENT_START_HERE|legal sufficiency|final agency decision" README.md docs/AGENT_START_HERE.md docs/ARCHITECTURE.md docs/OUTPUT_SCHEMAS.md docs/SESSION_HANDOFF.md
```

Stop conditions:

- The start-here doc duplicates large sections of existing docs instead of staying concise.
- The closeout docs imply broader legal or operational readiness than the existing lanes prove.

Closeout on 2026-05-20:

- `docs/AGENT_START_HERE.md` is now the first-stop agent guide for document work.
- `README.md`, `docs/ARCHITECTURE.md`, and `docs/OUTPUT_SCHEMAS.md` now route agent-driven
  document work to the planner and keep the refusal boundary explicit.
- `docs/TECH_DEBT_REGISTER.md` remains unchanged because this packet did not introduce a temporary
  debt exception.

## Required Documentation And Handoff Updates

- `docs/AGENT_START_HERE.md`
- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/architecture_contract.toml`
- `docs/SESSION_HANDOFF.md`
- `docs/TECH_DEBT_REGISTER.md` only if a temporary debt exception is intentionally introduced

## Required Verification Gates

At milestone closeout, the packet must run:

```bash
git status -sb
PYTHONPATH=src uv run --extra dev pytest tests/test_document_plan.py tests/test_cli.py tests/test_architecture_contract.py -q
PYTHONPATH=src uv run --extra dev pytest tests/test_draft_generation.py tests/test_ea_consistency_decision_support.py tests/test_project_sow_package.py -q
PYTHONPATH=src uv run --extra dev ruff check src tests
python -m compileall src
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20
git diff --check
```

If a future implementation changes any lane-owned generator semantics instead of only the routing
surface, add the corresponding lane tests and evals in the same milestone rather than claiming this
packet stayed routing-only.

## Acceptance Criteria

- The repo has one explicit first-stop doc for agent-driven document work.
- The repo has one normalized document-request schema and one machine-readable lane registry.
- The repo has one narrow public dry-run command that routes to existing document lanes or refuses
  the request.
- The planner cannot silently route unsupported legal-conclusion or final-decision requests into a
  nearby supported lane.
- The planner does not write canonical lane outputs.
- The planner does not materially increase hotspot risk in `cli.py` or the existing document-lane
  modules.
- The durable docs, architecture contract, and CLI help all agree on the new entrypoint.

## Local Commit Closeout Policy

- Stage only the verified milestone slice for this packet.
- Leave unrelated dirty or untracked files untouched.
- Commit the planner code, focused tests, docs, architecture-contract updates, and session handoff
  in one atomic local commit after verification passes.
- Record the commit hash in `docs/SESSION_HANDOFF.md`.
- Treat the milestone as incomplete until that local commit exists.
- Do not push unless the user explicitly asks for push or publish.

## Residual Risks And Next Milestone Routing

If this packet closes green, the main remaining legibility work should route into a second
standalone follow-on packet rather than broadening this milestone in place. The likely next packet
is:

- lane-specific concise runbooks for decision support and reviewed draft generation to match the
  quality of `docs/PROJECT_SOW_PACKAGE_RUNBOOK.md`;
- unified document audit-packet terminology across project SOW, decision support, reviewed draft,
  review packet index, and final QA surfaces; and
- optional future multi-lane orchestration only after the dry-run routing layer proves stable.

This first packet should therefore resolve the missing entrypoint, not the entire agent-legibility
program.
