# Architecture Governance Rebaseline Milestone Plan

Date: 2026-05-26

Status: resolved locally 2026-05-26; architecture governance now matches live repo truth again,
`docs/CURRENT_ROUTING.md` is back under its short-route cap, and the remaining `9` oversized files
are explicitly inventoried as follow-on debt

Owner context: This is a narrow child packet opened after a read-only architecture audit found
that the repo's live architecture-governance surfaces no longer match current code size, current
route size, or the repo's own quality gates. The active implementation lane remains
`docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`. This packet only repairs the
architecture control plane and re-routes remaining oversized-file debt truthfully; it must not
rewrite the 2026-05-21 under-`800` closeout as if it were false at the time.

## Purpose

Restore truthful, green architecture governance on the current repo state.

The exact weakness is not merely that large files exist again. The weakness is that the repo's
machine-readable oversized-file inventory, architecture-quality gate, route-document size contract,
and current-state docs now disagree about whether those files exist. Until those surfaces are
rebaselined, future sessions cannot trust architecture status claims, and the historical
under-`800` closeout is being used as live truth after the repo moved on.

## Current Evidence

### Live architecture evidence on 2026-05-26

- Fresh architecture probe:
  `python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20`
  reported `472` code files, `9` code files above `800` lines, no Python or JS/TS import cycles,
  and top hotspot `tests/test_compliance_review.py` with score `35420`.
- Current oversized code files from that probe:
  - `1144` `src/usfs_r1_ea_sources/extraction_fidelity_eval.py`
  - `852` `src/usfs_r1_ea_sources/extract_runtime.py`
  - `839` `src/usfs_r1_ea_sources/phase_eval_direct_eval_source_set.py`
  - `814` `src/usfs_r1_ea_sources/applicability_candidate_assembly.py`
  - `1407` `tests/test_applicability_authority_family_templates.py`
  - `913` `tests/test_promotion_suite_full_canonical.py`
  - `847` `tests/test_extraction_accuracy.py`
  - `829` `tests/test_forest_plan_resolver_scope.py`
  - `820` `tests/test_catalog.py`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py tests/test_architecture_quality.py -q`
  currently fails four checks:
  - live oversized-file count is `9`, not `0`
  - `config/architecture_large_file_inventory_v1.json` is empty instead of listing the live set
  - `docs/CURRENT_ROUTING.md` is `277` lines instead of `<= 40`
  - the current cross-doc alignment assertion still expects volatile gold-state text in
    `README.md`
- `config/architecture_large_file_inventory_v1.json` still records
  `plan_status="resolved_historical_closeout"` and `families=[]`.
- `README.md`, `docs/CURRENT_ROUTING.md`, and the architecture readback in `docs/ARCHITECTURE.md`
  still describe the under-`800` packet as live current truth rather than historical closeout.

### Historical context that must remain truthful

- `docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md` is a historical closeout record for the
  2026-05-21 zero-oversized baseline and its then-current readback sweep.
- `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md` is a historical umbrella closeout and
  must not be rewritten to pretend its earlier milestone counts never existed.
- The current weakness is later governance drift plus later code growth, not proof that the
  historical closeout packet was fabricated.

## Goal

Rebaseline the architecture control plane so current repo truth comes from:

- the live architecture probe;
- an exact machine-readable oversized-file inventory for the current repo state;
- a green `tests/test_architecture_quality.py` suite scoped to the intended doc/gate ownership;
- a short `docs/CURRENT_ROUTING.md` that stays within its enforced line cap; and
- current-state docs that distinguish historical closeout facts from current reopened debt.

## Non-Goals

- Do not reduce the current `9` oversized files below `800` in this packet.
- Do not reopen the active reviewer-facing replay-repair packet or absorb its runtime work.
- Do not falsify historical 2026-05-21 architecture closeout facts just to make current docs look
  simple.
- Do not weaken tests, delete assertions, add skips, or broaden tolerances to get the gate green.
- Do not rerun broad network/download/review workflows; this is a docs/test/control-plane packet.
- Do not expand `docs/CURRENT_ROUTING.md` with more deep state while trying to fix its line-count
  contract.

## Scope

In scope:

- `tests/test_architecture_quality.py` and any narrowly-related helper extraction required to make
  the architecture-quality gate truthful and reviewable;
- `config/architecture_large_file_inventory_v1.json` as the current oversized-file source of
  truth;
- `docs/CURRENT_ROUTING.md` as the short first-stop routing surface;
- `README.md`, `docs/ARCHITECTURE.md`, `docs/CURRENT_SYSTEM_STATE.md`, and
  `docs/SESSION_HANDOFF.md` architecture status claims;
- historical/current distinction for the under-`800` closeout;
- truthful routing of the remaining `9` oversized-file backlog after governance closes.

Out of scope:

- owner-family source splits for the `9` oversized files themselves;
- replay-contract, forest-plan, applicability, compliance, or promotion-suite semantic changes;
- new architecture model tooling beyond what is required to keep current truth machine-checked.

## Owner Surfaces

| Surface | Owner role in this packet | Required verification |
| --- | --- | --- |
| `tests/test_architecture_quality.py` | Governs live oversized-file, route-doc, and doc-ownership architecture checks | focused pytest, ruff, compileall |
| `tests/test_architecture_contract.py` | Guards import-boundary truth while the architecture-quality gate is being changed | focused pytest |
| `config/architecture_large_file_inventory_v1.json` | Machine-readable live oversized-file inventory and queue metadata | focused pytest readback plus targeted JSON inspection |
| `docs/CURRENT_ROUTING.md` | Short first-stop route only; must not carry deep live state | `wc -l`, focused pytest, targeted doc readback |
| `README.md` | Stable public entrypoint; should point to live route and current-state docs without duplicating volatile architecture counts | targeted doc readback |
| `docs/ARCHITECTURE.md` | Current architecture map and current architecture gate readback | targeted doc readback |
| `docs/CURRENT_SYSTEM_STATE.md` | Canonical current-state owner for live architecture status when the count changes | targeted doc readback |
| `docs/SESSION_HANDOFF.md` | Canonical fresh-session owner for the current architecture follow-on route and baseline evidence | targeted doc readback |
| `docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md` | Historical closeout reference only; update only if an explicit historical/follow-on note is required | targeted grep for historical wording |

## Placement Rules

- Keep `docs/ARCHITECTURE.md` as the canonical tracked path; do not introduce a second tracked
  lowercase architecture doc.
- Keep `docs/CURRENT_ROUTING.md` at `<= 40` lines after closeout. It may link to deeper docs, but
  it must not become the deep current-state log again.
- Keep volatile architecture counts, reopened debt notes, and next architecture routing in
  `docs/CURRENT_SYSTEM_STATE.md` and the top of `docs/SESSION_HANDOFF.md`, not duplicated across
  every entrypoint doc.
- Treat `docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md` and
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md` as historical evidence. If live repo
  state has drifted, record that drift in current-state surfaces instead of rewriting the old
  milestone outcomes.
- If `tests/test_architecture_quality.py` is split for legibility, keep the public test ownership
  obvious and avoid generic helper modules with no named architecture purpose.

## Weak-Point Prevention Contract

| Milestone | Weak point forecast | Owner surface | Prevention gate | Fail threshold | Controlled violation | Future-Codex misuse prevented |
| --- | --- | --- | --- | --- | --- | --- |
| `0` | Rebaseline starts from the wrong live state or erases historical closeout truth | this plan, `docs/SESSION_HANDOFF.md`, historical architecture plans | fresh architecture probe, failing focused pytest baseline, targeted stale-token grep | the 2026-05-26 baseline does not reproduce the `9` oversized files, `277`-line route doc, and `4` failing assertions; or the only way to proceed is to falsify historical closeout text | the current repo must reproduce the known failing architecture-quality checks before edits begin | a future session trusts the 2026-05-21 zero-oversized claim as live current truth and edits the wrong packet |
| `1` | Inventory is refreshed, but the gate still allows substitution drift or stale empty-closeout claims | `config/architecture_large_file_inventory_v1.json`, `tests/test_architecture_quality.py` | focused pytest, exact inventory/path/line-count readback, synthetic mismatch/unit helper if test helpers are extracted | a live oversized path can disappear from the inventory without test failure; a stale `families=[]` closeout can still pass | add or preserve a focused negative-path assertion that fails on missing or stale inventory entries | a future session updates one line count, forgets one path, and still calls the architecture inventory current |
| `2` | Route-doc repair weakens the doc gate by silently dropping volatile truth instead of assigning it to the right owner docs | `docs/CURRENT_ROUTING.md`, `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`, `tests/test_architecture_quality.py` | `wc -l docs/CURRENT_ROUTING.md`, focused pytest, targeted doc readback | `docs/CURRENT_ROUTING.md` remains above `40` lines, or README/current-routing still need deep live-state tokens to satisfy the gate | preserve a failing-overlength baseline and add doc-ownership assertions that require the deeper docs to hold live counts | a future session shoves another packet summary into `docs/CURRENT_ROUTING.md` because it is convenient |
| `3` | Closeout greens the architecture gate but leaves stale zero-oversized claims or no truthful next routing for the `9` live hotspots | `README.md`, `docs/ARCHITECTURE.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`, inventory artifact | focused pytest, targeted `rg`, `git diff --check` | any live-state surface still claims `0` oversized files or an empty oversized inventory without explicit historical context; or the remaining hotspot backlog has no next routing | the pre-closeout stale-token grep must show the old false claims before the docs are updated | a future session sees a green test suite but still lands changes against stale README/current-state architecture claims |

## Milestone Sequence

| Milestone | Scope | Outcome label |
| --- | --- | --- |
| `0` | Baseline lock and historical/current distinction | `resolved` |
| `1` | Exact oversized-file inventory and architecture-quality gate rebaseline | `resolved` |
| `2` | Short-route contract and doc-ownership contract restoration | `resolved` |
| `3` | Current-state readback, handoff routing, and closeout alignment | `resolved` |

### Milestone `0`: Baseline lock and historical/current distinction

Outcome label: `resolved`

Work:

- Re-run `git status -sb`, the architecture probe, `wc -l docs/CURRENT_ROUTING.md`, and the focused
  architecture pytest slice before any edits.
- Record the exact failing signals and the exact live oversized-file set in this plan and the top
  of `docs/SESSION_HANDOFF.md`.
- Mark the 2026-05-21 under-`800` packet and architecture umbrella as historical closeout records,
  not current live truth.

Required verification:

```bash
git status -sb
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py tests/test_architecture_quality.py -q
wc -l docs/CURRENT_ROUTING.md
rg -n "0 code files above `800` lines|empty oversized-file inventory|under-`800` follow-on" README.md docs/CURRENT_ROUTING.md docs/ARCHITECTURE.md docs/CURRENT_SYSTEM_STATE.md docs/SESSION_HANDOFF.md
```

### Milestone `1`: Exact oversized-file inventory and architecture-quality gate rebaseline

Outcome label: `resolved`

Work:

- Replace the stale empty-closeout payload in `config/architecture_large_file_inventory_v1.json`
  with the live reopened inventory:
  - exact current oversized file paths and line counts
  - owner-family grouping for the `4` source owners and `5` test owners
  - `as_of`, probe command, and required focused verification surfaces
  - explicit note that the 2026-05-21 empty inventory is historical, not current
- Update `tests/test_architecture_quality.py` so the live oversized-file gate enforces current repo
  truth rather than stale closeout prose.
- Keep the gate exact:
  - fail if a listed file's line count drifts without inventory refresh
  - fail if a new `>800` file appears
  - fail if the inventory claims `families=[]` while live oversized files exist
- If helper extraction is needed for test legibility, keep the negative-path coverage at least as
  strong as the current live mismatch checks.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py tests/test_architecture_quality.py -q
PYTHONPATH=src uv run --extra dev ruff check tests/test_architecture_contract.py tests/test_architecture_quality.py
PYTHONPATH=src python -m compileall tests/test_architecture_quality.py tests/test_architecture_contract.py
git diff --check
```

### Milestone `2`: Short-route contract and doc-ownership contract restoration

Outcome label: `resolved`

Work:

- Reduce `docs/CURRENT_ROUTING.md` back to a true short route of `<= 40` lines.
- Keep `docs/CURRENT_ROUTING.md` limited to:
  - start order
  - active implementation packet
  - named architecture follow-on packet
  - links to deeper current-state docs
- Move live architecture counts and reopened oversized-file status out of `README.md` and
  `docs/CURRENT_ROUTING.md` into `docs/CURRENT_SYSTEM_STATE.md` and the top section of
  `docs/SESSION_HANDOFF.md`.
- Update `tests/test_architecture_quality.py` so the doc gate enforces the intended ownership:
  README and current-routing are indexes, while current-state and handoff hold volatile detail.

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_quality.py -q
wc -l docs/CURRENT_ROUTING.md
rg -n "docs/CURRENT_SYSTEM_STATE.md|docs/SESSION_HANDOFF.md" docs/CURRENT_ROUTING.md README.md docs/AGENT_START_HERE.md
git diff --check
```

### Milestone `3`: Current-state readback, handoff routing, and closeout alignment

Outcome label: `resolved`

Work:

- Update `README.md`, `docs/ARCHITECTURE.md`, `docs/CURRENT_SYSTEM_STATE.md`, and the fresh-session
  section at the top of `docs/SESSION_HANDOFF.md` so they:
  - distinguish the historical 2026-05-21 zero-oversized closeout from the reopened 2026-05-26
    live oversized-file backlog
  - report the fresh architecture probe date and current oversized-file count truthfully
  - route the remaining `9` oversized files as live follow-on architecture debt instead of
    pretending the repo is still at zero
- Keep the historical milestone plans historical. If they need a note, add a historical/follow-on
  pointer rather than rewriting milestone outcomes.
- Record the next architecture follow-on explicitly from the live inventory after governance closes.

Required verification:

```bash
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py tests/test_architecture_quality.py -q
rg -n "0 code files above `800` lines|empty oversized-file inventory" README.md docs/CURRENT_ROUTING.md docs/ARCHITECTURE.md docs/CURRENT_SYSTEM_STATE.md docs/SESSION_HANDOFF.md
git diff --check
```

## Required Implementation Artifacts

- updated `config/architecture_large_file_inventory_v1.json`
- updated `tests/test_architecture_quality.py`
- updated `README.md`
- updated `docs/CURRENT_ROUTING.md`
- updated `docs/ARCHITECTURE.md`
- updated `docs/CURRENT_SYSTEM_STATE.md`
- updated `docs/SESSION_HANDOFF.md`
- this plan file

## Required Documentation And Handoff Updates

- keep this plan current with milestone progress and exact closeout status
- update the top section of `docs/SESSION_HANDOFF.md` with:
  - exact architecture probe command
  - final oversized-file count
  - final route-doc line count
  - closed governance issue
  - next routed architecture follow-on
- update `docs/CURRENT_SYSTEM_STATE.md` with the new current architecture-governance state
- update `README.md` and `docs/ARCHITECTURE.md` only to the level needed to keep public/current
  architecture truth aligned without duplicating volatile deep state

## Required Verification Gates

```bash
git status -sb
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py tests/test_architecture_quality.py -q
PYTHONPATH=src uv run --extra dev ruff check tests/test_architecture_contract.py tests/test_architecture_quality.py
PYTHONPATH=src python -m compileall tests/test_architecture_quality.py tests/test_architecture_contract.py
wc -l docs/CURRENT_ROUTING.md
rg -n "0 code files above `800` lines|empty oversized-file inventory|five still-unmapped live authorities|zero-link structural surface|generated diagnostic" README.md docs/CURRENT_ROUTING.md docs/ARCHITECTURE.md docs/CURRENT_SYSTEM_STATE.md docs/SESSION_HANDOFF.md
git diff --check
```

## Acceptance Criteria

- The baseline reproduced the 2026-05-26 architecture-governance drift before edits:
  `9` oversized code files, `277`-line `docs/CURRENT_ROUTING.md`, and the known failing
  architecture-quality assertions.
- `config/architecture_large_file_inventory_v1.json` lists the exact live oversized-file set and
  no longer claims a current empty inventory.
- `PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py tests/test_architecture_quality.py -q`
  passes on the live repo state without removing or weakening the architecture controls that caught
  the drift.
- `docs/CURRENT_ROUTING.md` is back at `<= 40` lines and acts only as a short route.
- `README.md` and `docs/CURRENT_ROUTING.md` no longer own volatile architecture counts that belong
  in `docs/CURRENT_SYSTEM_STATE.md` and `docs/SESSION_HANDOFF.md`.
- `README.md`, `docs/ARCHITECTURE.md`, `docs/CURRENT_SYSTEM_STATE.md`, and the top of
  `docs/SESSION_HANDOFF.md` truthfully distinguish:
  - the historical 2026-05-21 under-`800` closeout
  - the reopened 2026-05-26 oversized-file backlog
- No live-state surface claims `0` oversized code files or an empty oversized-file inventory
  unless it is explicitly labeled as historical context.
- The closeout commit stages only the governance slice:
  docs, tests, and machine-readable inventory updates for this packet.

## Stop Conditions

- Stop if the fresh architecture probe no longer reproduces the `9`-file oversized baseline before
  implementation begins; rebaseline the packet first instead of patching against stale audit data.
- Stop if resolving the doc-ownership gate would require broad replay-lane semantics or unrelated
  runtime changes.
- Stop if a future edit would need to falsify historical milestone closeout facts instead of
  recording later drift truthfully.
- Stop before commit if `tests/test_architecture_contract.py` or
  `tests/test_architecture_quality.py` still fail after the intended governance updates.

## Local Commit Closeout Policy

- Stage only the verified governance-rebaseline slice.
- Leave unrelated runtime, corpus, and generated-output surfaces untouched.
- Include the machine-readable inventory update, focused architecture tests, route/current-state
  docs, this plan, and handoff updates in the same local atomic commit.
- Record the closeout commit hash in `docs/SESSION_HANDOFF.md`.
- Treat the packet as incomplete until that local commit exists.

## Residual Risks And Next Milestone Routing

If this packet closes correctly, the remaining architecture issue is no longer stale governance. The
remaining issue is the actual oversized-file backlog now enumerated truthfully in the live
inventory.

Expected next routed architecture follow-on after this packet:

- source-owner backlog first:
  `src/usfs_r1_ea_sources/extraction_fidelity_eval.py`,
  `src/usfs_r1_ea_sources/extract_runtime.py`,
  `src/usfs_r1_ea_sources/phase_eval_direct_eval_source_set.py`, and
  `src/usfs_r1_ea_sources/applicability_candidate_assembly.py`
- then the test-owner backlog:
  `tests/test_applicability_authority_family_templates.py`,
  `tests/test_promotion_suite_full_canonical.py`,
  `tests/test_extraction_accuracy.py`,
  `tests/test_forest_plan_resolver_scope.py`, and
  `tests/test_catalog.py`

That follow-on should be written as a separate owner-reduction packet after this governance packet
is green, so future sessions start from truthful current architecture state instead of from stale
zero-oversized claims.
