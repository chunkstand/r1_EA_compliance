# Agentic Repo Best Practices Guide

Date: 2026-05-21

This guide turns current primary-source guidance on software architecture, code health, and
agentic engineering into repo practices for `usfs-r1-EA-sources`.

“Top experts” is subjective, so this guide uses a practical set of authoritative lenses that are
widely cited, primary-source, and directly applicable to a local auditable CLI repository operated
by humans and coding agents.

## Selected Expert Lenses

| Lens | Primary source | Core idea | Repo implication |
| --- | --- | --- | --- |
| Simon Brown | [C4 model](https://c4model.com/) and [Structurizr as code](https://docs.structurizr.com/as-code) | Architecture should be legible at multiple levels and kept as text in version control. | Keep architecture, ADRs, and agent entrypoints explicit, small, and linked to code. |
| Rebecca Parsons, Neal Ford, Patrick Kua, Pramod Sadalage | [Building Evolutionary Architectures](https://www.thoughtworks.com/insights/books/building-evolutionaryarchitectures-second-edition) | Use automated governance and fitness functions to protect change over time. | Keep dependency rules, artifact ownership, and milestone closeout checks executable. |
| Titus Winters, Tom Manshreck, Hyrum Wright | [Software Engineering at Google](https://abseil.io/resources/swe-book) | Sustainable code is code you can still change safely over time. Review exists to preserve understandability, not only correctness. | Prefer small reviewed milestones, presubmit-style automation, and boundaries that stay readable. |
| Adam Tornhill | [Code as a Crime Scene](https://adamtornhill.com/articles/crimescene/codeascrimescene.htm) | Refactor where complexity and change frequency overlap, not where style looks ugly. | Use hotspots, churn, and logical coupling to choose the next split. |
| Anthropic | [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) | Start simple, add complexity only when it measurably helps, and design the agent-computer interface carefully. | Treat CLI commands, schemas, configs, and tool docs as first-class agent interfaces. |
| OpenAI | [A practical guide to building agents](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/) and [How OpenAI uses Codex](https://openai.com/business/guides-and-resources/how-openai-uses-codex/) | Good agents need well-documented reusable tools, clear guardrails, and strong context. Coding agents work best on code understanding, refactors, migrations, and tests. | Land new agent surfaces with dependencies, docs, tests, and guardrails together. |
| Simon Willison | [Agentic Engineering Patterns](https://simonwillison.net/guides/agentic-engineering-patterns/) | Git, tests, and review become more important, not less, when using coding agents. | Keep work Git-native, start from current diffs/history, and make agent sessions easy to rehydrate. |
| Chip Huyen | [Agents](https://huyenchip.com/2025/01/07/agents.html) | Agents need explicit tool selection, reflection, and evaluation against failure modes. | Add checkpoints, refusal paths, and evaluation loops to agent-facing workflows. |

## Best Practices For This Repo

### 1. Keep One Canonical Source Of Truth Per Concern

- Workbook and workbook-driven tables remain the source of truth for corpus scope.
- `docs/ARCHITECTURE.md` and `docs/architecture_contract.toml` remain the source of truth for
  module ownership and allowed dependency direction.
- `docs/CURRENT_SYSTEM_STATE.md` remains the source of truth for current live corpus/runtime state.
- `docs/SESSION_HANDOFF.md` remains the source of truth for current routed work and recent closeout
  facts.
- New docs should reduce ambiguity, not create a second competing truth surface.

### 2. Keep Architecture As Plain Text And Executable

- Architecture must stay readable to humans and agents without requiring a UI tool.
- Every source module should appear in `docs/architecture_contract.toml`.
- Dependency direction, temporary exceptions, generated artifact ownership, and command-group
  ownership should stay machine-checked.
- A new boundary is not complete until the contract, tests, and docs agree.

### 3. Treat The CLI, Schemas, And Configs As The Agent-Computer Interface

- Public commands are not just human operator surfaces; they are the main structured interface for
  future agents.
- Each new agent-facing command should land with:
  - a dedicated small owner module;
  - a public CLI registration;
  - documented refusal boundaries;
  - schema/config validation;
  - focused tests; and
  - all required Python dependencies declared in `pyproject.toml`.
- Partial landings are high-risk because agents will discover files before they discover missing
  wiring.

### 4. Keep New Agent Surfaces Atomic

- If a feature introduces a new agent entrypoint, land runtime code, dependency declarations,
  schemas, docs, and tests in the same milestone.
- Do not leave agent-facing modules in a “code exists, interface missing, docs pending” state.
- A partially landed tool teaches future agents the wrong workflow.

### 5. Optimize For Small, Owned Change Surfaces

- Large files are especially dangerous in agentic workflows because local edits can miss distant
  invariants.
- Prefer small owner modules with narrow public interfaces over one more branch in a large
  orchestrator.
- Keep command routing and document routing out of broad monolithic files when a small facade will
  do.

### 6. Pick Refactors By Hotspot Evidence

- Use file size alone only as a weak heuristic.
- Prioritize modules that are both large and frequently changed.
- When two files change together often, treat that as a hidden dependency worth documenting,
  testing, or splitting.

### 7. Make Verification Layered And Cheap To Reuse

- Run architecture checks for structure.
- Run focused tests for behavior.
- Run evals where outputs are reviewer-facing or readiness-facing.
- Prefer deterministic readback commands and generated artifacts over ad hoc inspection.
- A guide or handoff should name the exact commands that prove its claims.

### 8. Keep Work Git-Native

- Start sessions from `git status -sb`, recent commits, current handoff, and the relevant docs.
- Keep milestones small enough to review and revert cleanly.
- Preserve unrelated dirty worktree changes.
- Use history and diffs as context-rehydration tools for future agents.

### 9. Keep Untrusted Content Separate From Privileged Actions

- Downloaded pages, extracted text, package text, retrieved evidence, and review inputs remain
  evidence data, not instructions.
- Any future model-facing or agent-facing workflow that combines untrusted text with privileged
  local actions needs explicit risk classification and a human gate.
- Security policy for this repo should continue to live in durable ADRs and tests, not only prompts.

### 10. Keep Durable Docs Short At The Point Of Entry

- Large canonical docs are acceptable as deep references.
- Agents need one short first-stop entrypoint before the large docs.
- A small `AGENT_START_HERE`-style document is more valuable than adding more prose to
  `README.md` or `docs/SESSION_HANDOFF.md`.
- Append-only history should not be the only onboarding surface.

### 11. Use Reflection And Refusal As First-Class Patterns

- Planning commands should be allowed to refuse unsupported requests cleanly.
- Reflection should exist at milestones, in eval loops, and after tool steps where drift is likely.
- Unsupported legal conclusions, approvals, or final agency decisions should fail closed.

## Current Repo Evaluation

Evaluation date: 2026-05-21

### Strong

#### Artifact-first, auditable architecture

- The repo is strongly aligned with Brown and the Thoughtworks evolutionary-architecture lens on
  explicit boundaries and durable artifacts.
- Evidence:
  - `README.md` and `docs/ARCHITECTURE.md` describe a workbook-driven, artifact-first pipeline.
  - `docs/architecture_contract.toml` exists and covers the current workflow layers.
  - `tests/test_architecture_contract.py` exists and currently passes.

#### Verification culture

- The repo is stronger than average on executable governance.
- Evidence:
  - focused tests, architecture tests, lint, compile, evals, and `git diff --check` are part of
    the repo’s normal closeout vocabulary;
  - ADR `0005` explicitly requires architecture gates in milestone closeout.

#### Security boundary for untrusted source content

- The repo is ahead of many AI-adjacent codebases here.
- Evidence:
  - `docs/adr/0004-untrusted-source-content.md` explicitly says downloaded and extracted content is
    evidence data, not agent instructions;
  - the architecture and AGENTS rules preserve deterministic, citation-bearing outputs.

#### Stable operator-facing workflow model

- The CLI remains broad but coherent.
- Evidence:
  - the main command surface still cleanly separates capture, catalog, extraction, review,
    compliance, decision support, project planning, and eval families.

### Mixed

#### Agent legibility for document work is materially better

- The repo now has a real cold-start surface for prompt-to-document routing.
- Evidence:
  - `docs/AGENT_START_HERE.md` exists and stays short;
  - `python -m usfs_r1_ea_sources --help` exposes `document-plan`;
  - the routed packet `docs/AGENT_LEGIBILITY_ENTRYPOINT_MILESTONE_PLAN.md` is complete; and
  - focused planner, CLI, and architecture tests now pass together.
- Assessment:
  - document-work cold-start is now good;
  - broader repo-wide architecture routing still depends on the larger milestone docs and handoff.

#### Durable context is strong but too expensive to scan

- The repo already stores the right kind of context, but not yet in the right entrypoint shape for
  fast agent startup.
- Evidence:
  - `AGENTS.md`, `README.md`, `docs/ARCHITECTURE.md`, `docs/CURRENT_SYSTEM_STATE.md`, and
    `docs/SESSION_HANDOFF.md` are high-signal;
  - `docs/SESSION_HANDOFF.md` is append-only and very large;
  - `docs/CURRENT_SYSTEM_STATE.md` is authoritative but also large.
- Assessment:
  - high information quality;
  - medium cold-start cost.

#### Reviewability of large modules

- The repo has good boundaries on paper, but large owned modules still dominate the risk surface.
- Evidence from `architecture_probe.py`:
  - `24` code files exceed `800` lines;
  - top hotspots include `project_sow_package.py`, `nepa_knowledge_graph_export.py`,
    `forest_plan_components.py`, `extract.py`, and `final_qa_certification.py`.
- Assessment:
  - good architecture direction;
  - too many large active edit surfaces for easy agentic maintenance.

### Weak

#### Cheap governance only just reached the hotspot layer

- The repo has dependency and debt gates, but large-file and fan-out protection is still young.
- Evidence:
  - `tests/test_architecture_quality.py` now guards the current `24`-file `>800` line baseline,
    blocks new `>20` fan-out source modules with no current exceptions, and pins
    `docs/ARCHITECTURE.md` as the canonical tracked architecture path;
  - Milestone 8 in the umbrella architecture packet is now resolved, so no `tests/` or
    `tests/support/` owner remains above the `800`-line reviewability gate;
  - the gate is intentionally conservative and prevents growth, but it does not yet reduce the
    existing hotspot inventory by itself.
- Assessment:
  - governance is now meaningfully better;
  - the active follow-on is now mechanical routing and hermeticity cleanup before the remaining
    runtime/viewer hotspot families.

#### Hermeticity and long-form routing are still open debt

- Some repo truth is still explicit but too expensive to rehydrate or not fully portable.
- Evidence:
  - `docs/CURRENT_SYSTEM_STATE.md` still declares the preserved West Reservoir replay-context path
    under `/Users/chunkstand/Downloads/West Reservoir (67436)`;
  - `docs/SESSION_HANDOFF.md` and `docs/CURRENT_SYSTEM_STATE.md` remain large canonical surfaces
    even after the new first-stop agent docs landed.
- Assessment:
  - the repo is honest about the dependency;
  - the remaining work is to remove or quarantine it and keep routing summaries small.

## Live Command Evidence

The following commands were run during this assessment:

```bash
git status -sb
python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py tests/test_architecture_quality.py tests/test_debt_contract.py -q
PYTHONPATH=src python -m usfs_r1_ea_sources --help
```

Observed results:

- `git status -sb`: clean worktree on `main`.
- `architecture_probe.py`: no Python or JS cycles; `24` code files over `800` lines; top hotspot
  `project_sow_package.py`; no source module above fan-out `20`; and no `tests/` or
  `tests/support/` owner above the `800`-line reviewability gate.
- `tests/test_architecture_contract.py`, `tests/test_architecture_quality.py`, and
  `tests/test_debt_contract.py`: all pass together after the Milestone 8 docs-alignment closeout.
- CLI help: `document-plan` is exposed on the public command surface.

## Priority Queue

### 1. Remove Mechanical Routing And Hermeticity Drift

- Replace or quarantine the West Reservoir user-home dependency.
- Keep `docs/SESSION_HANDOFF.md`, `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/AGENT_START_HERE.md`, and the umbrella architecture packet aligned on one explicit
  next-step truth.
- Finish the Milestone 9 routing cleanup before reopening broader hotspot-owner refactors.

### 2. Keep The Cheap Architecture Gates Green

- Do not let the size, fan-out, debt, or path-drift checks go stale while Milestones 9 and 10
  close.

### 3. Resume Remaining Runtime And Viewer Hotspots After The Routing Closeout

- After the routing packet closes, the largest remaining active owner families are
  `project_sow_package.py`, `nepa_knowledge_graph_export.py`, `forest_plan_components.py`,
  `ea_consistency_decision_support.py`, `extract.py`, and the NEPA 3D viewer surface.
- Do not refactor by aesthetic preference alone; keep using hotspot and ownership evidence.

## Bottom Line

This repo is already stronger than average on architecture legibility, artifact auditability,
security boundaries, and milestone discipline. The current main gap is no longer agent-entrypoint
completeness or oversized test-owner sprawl. The current main gap is the remaining mechanical
routing and hermeticity debt, with larger runtime/viewer hotspot families queued behind that
cleanup. The next quality step is to close Milestone 9 cleanly while keeping the architecture gates
green.
