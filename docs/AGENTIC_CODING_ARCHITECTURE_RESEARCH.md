# Agentic Coding Architecture Research

Date: 2026-05-04

This brief captures current agentic-coding and software-architecture research that should shape
future work in this repository. It is intentionally implementation-facing: the goal is to make the
codebase easier for humans and coding agents to understand, change, verify, and govern.

## Research Basis

- Anthropic's production guidance argues for simple, composable agentic patterns, clear
  success criteria, feedback loops, and human review. Coding agents work especially well because
  code has objective verification through tests, but broader system fit still needs human review:
  <https://www.anthropic.com/engineering/building-effective-agents>.
- Anthropic's Claude Code best practices emphasize a workflow of explore, plan, implement, and
  commit; precise context; and strong verification commands:
  <https://code.claude.com/docs/en/best-practices>.
- OpenAI's Codex usage guidance frames code understanding, refactoring, migrations, performance,
  and test coverage as high-value agent tasks, especially when the agent can trace data flow and
  locate module relationships:
  <https://openai.com/business/guides-and-resources/how-openai-uses-codex/>.
- OpenAI's agent-building guide treats guardrails as layered engineering controls, with risk-rated
  tools, deterministic protections, and output validation:
  <https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/>.
- Anthropic's tool-design guidance says tools for agents are contracts between deterministic and
  non-deterministic systems. Effective tools are namespaced, high-signal, context-efficient,
  evaluation-backed, and clear about inputs, outputs, and boundaries:
  <https://www.anthropic.com/engineering/writing-tools-for-agents>.
- Anthropic's multi-agent research writeup shows that multi-agent systems help most when work is
  broad, parallel, and information-heavy; coding tasks are often less parallel because files and
  design choices are tightly coupled:
  <https://www.anthropic.com/engineering/multi-agent-research-system>.
- Dex Horthy's 12-factor agents guidance is useful for production agent systems: own prompts,
  own the context window, keep tools as structured outputs, own control flow, use small focused
  agents, and make long-running work resumable:
  <https://github.com/humanlayer/12-factor-agents>.
- Simon Willison's prompt-injection work is directly relevant because this repo processes
  untrusted public web pages, PDFs, and package documents. The high-risk pattern is combining
  private data access, untrusted content, and external communication:
  <https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/>.
- Simon Brown's C4 model and Structurizr architecture-as-code guidance are a strong fit for making
  architecture explicit and agent-legible. Structurizr specifically calls out plain-text models,
  ADRs, and drift detection as useful for agentic workflows:
  <https://c4model.info/> and <https://docs.structurizr.com/as-code>.
- Evolutionary architecture, especially architecture fitness functions from Ford, Parsons, Kua,
  and Sadalage, maps well to this repo's gate culture:
  <https://www.thoughtworks.com/en-us/insights/books/building-evolutionaryarchitectures-second-edition>.
- Current empirical work reinforces the need for explicit agent instructions and architecture
  governance. Recent studies identify repository-level context files as emerging standards, show
  that coding agents tend toward localized refactors, and warn that prompt wording can create
  implicit architecture decisions:
  <https://arxiv.org/abs/2602.14690>,
  <https://arxiv.org/abs/2511.04824>, and
  <https://arxiv.org/abs/2604.04990>.
- Andrej Karpathy's "Software Is Changing (Again)" talk is useful framing: LLMs are a new
  programming interface, but current systems need human oversight, partial autonomy, and
  agent-readable infrastructure:
  <https://rosetta.to/u/ycombinator/andrej-karpathy-software-is-changing-again>.

## What This Repo Already Gets Right

- The workbook is the contract. That gives agents a durable source of truth instead of forcing
  them to infer source-library scope from code or chat history.
- The system is artifact-first. Raw artifacts, manifests, catalog rows, extraction outputs,
  retrieval indexes, graph outputs, claims, rule links, applicability artifacts, review outputs,
  and eval results are persistent and replayable.
- The current applicability-first lane is strongly aligned with agentic architecture: it stages
  authority universe, package facts, retrieval traces, graph traces, deterministic decisions,
  validation/adjudication, generated rule packs, and compliance review.
- The repo already uses agent-friendly context files: `AGENTS.md`, `docs/SESSION_HANDOFF.md`,
  `docs/CURRENT_SYSTEM_STATE.md`, and milestone plans.
- Tests and eval gates are a real strength. The current handoff records full-suite, focused-suite,
  ruff, compileall, and `git diff --check` verification.
- The Bitter Lesson alignment doc keeps domain knowledge in data and eval fixtures rather than
  hidden runtime branches.

## Architecture Risks

1. Oversized modules are becoming architecture surfaces.

   `compliance_review.py`, `forest_plan_components.py`, `applicability_validation.py`, `extract.py`,
   `claim_extraction.py`, and `evidence_graph.py` are large enough that future agents may make
   local edits without seeing the whole invariant. This is exactly where agentic refactoring tends
   to stay low-level unless the desired boundary is made explicit.

2. The CLI is an agent interface, but it is also becoming a monolith.

   `cli.py` owns every subcommand definition and dispatch branch. This is convenient for humans,
   but it gives agents a single 1,400+ line edit target for unrelated workflow changes. The CLI
   should remain stable, but command registration should be grouped by workflow lane.

3. There is at least one source dependency cycle.

   `rule_claim_binding.py` imports rule-pack utilities from `compliance_review.py`, while
   `compliance_review.py` imports rule-claim binding at runtime. The current import works, but the
   architecture says rule packs and rule-claim binding are upstream of compliance review. Shared
   rule-pack loading and validation should move to a neutral module.

4. Architecture intent is documented but not yet enforced as a fitness function.

   The repo has strong functional gates, but no machine-readable dependency policy that says, for
   example, capture cannot import review, retrieval cannot import compliance review, and review
   cannot decide applicability after the generated-rule-pack gate.

5. Untrusted-content boundaries need to remain explicit.

   The repo's inputs are exactly the kind of content that can contain malicious instructions. This
   is safe while the system treats documents as evidence data and uses deterministic tools, but
   future model-facing synthesis or agent tools must keep untrusted source text away from external
   communication and privileged local data.

## Recommended Architecture Direction

The codebase should become explicitly agent-legible:

- Make architecture a versioned artifact, not only prose.
- Keep workflow stages small, named, and artifact-backed.
- Keep domain knowledge in workbook rows, profiles, rule packs, eval fixtures, and generated
  ledgers.
- Add architecture fitness functions beside the existing test/eval gates.
- Treat CLI commands and generated JSON schemas as the agent-computer interface.
- Prefer single-agent implementation sequences for tightly coupled code changes; use parallel
  agents only for independent research, audits, fixture expansion, or disjoint module work.

## Concrete Application To This Codebase

### Sequence 1: Architecture Contract And Fitness Gate

Goal: add a lightweight architecture contract that agents and tests can enforce.

Suggested artifacts:

- `docs/ARCHITECTURE.md`: C4-style system/container/component map for the current local CLI
  pipeline.
- `docs/architecture_contract.yaml` or JSON equivalent: workflow layers, allowed import
  directions, key artifacts, and ownership boundaries.
- `tests/test_architecture_contract.py`: import-cycle and forbidden-dependency checks.

Initial layer model:

```text
workbook/config/records
  -> capture/preflight/download/batches/report/validate
  -> catalog
  -> extraction
  -> retrieval
  -> evidence_graph
  -> claim_extraction
  -> rule_pack/rule_claim_binding
  -> package_fact_graph/applicability
  -> ea_review/forest_plan
  -> compliance_review
  -> eval/promotion
  -> cli
```

The first fitness gate should reject source-level cycles and any direct downstream-to-upstream
dependency that violates the contract.

### Sequence 2: Break The Rule-Pack Cycle

Goal: move shared compliance rule-pack concerns out of `compliance_review.py`.

Suggested change:

- Add `src/usfs_r1_ea_sources/rule_packs.py`.
- Move `DEFAULT_RULE_PACK_PATH`, schema constants, `load_rule_pack`, `validate_rule_pack`, and
  rule-pack helper validation there.
- Update `compliance_review.py`, `rule_claim_binding.py`, `applicability.py`,
  `applicability_rule_pack.py`, eval modules, and tests to import from `rule_packs.py`.

This is small, high-value architecture work because it removes the current cycle and makes the
pipeline direction match the domain model.

### Sequence 3: Group CLI Registration By Workflow Lane

Goal: preserve the current command surface while reducing agent edit collisions.

Suggested shape:

- Keep `src/usfs_r1_ea_sources/cli.py` as the public entrypoint.
- Move command registration and command execution helpers into grouped modules, for example:
  `cli_capture.py`, `cli_derived.py`, `cli_applicability.py`, `cli_review.py`, and `cli_eval.py`.
- Use a small command table or registration function per lane.
- Keep every existing command name and option stable unless a separate migration explicitly changes
  the public interface.

This makes the CLI a cleaner agent-computer interface and limits unrelated changes to smaller
files.

### Sequence 4: Add Architecture Decision Records For Major Review-Lane Changes

Goal: stop agents from making implicit architecture decisions through local edits.

Suggested artifacts:

- `docs/adr/0001-applicability-before-compliance.md`
- `docs/adr/0002-rule-pack-validation-owner.md`
- `docs/adr/0003-agent-safe-untrusted-document-boundary.md`

The ADR format can stay short: context, decision, consequences, verification gate, and supersession
policy.

### Sequence 5: Agent-Safe Security Boundary

Goal: make prompt-injection resistance part of architecture, not a prompt reminder.

Suggested contract:

- Mark downloaded source text, extracted chunks, package chunks, and retrieved evidence as
  `untrusted_content` in schemas that feed model-facing or agent-facing tools.
- Require any future tool that combines untrusted content with filesystem writes, network access,
  email, Slack, browser actions, or external API calls to declare a risk level and a human gate.
- Add eval fixtures with adversarial document text that tries to override reviewer instructions.
- Keep review conclusions bound to citations, hashes, offsets, and validation artifacts, not free
  model authority.

### Sequence 6: Applicability Eval Milestone As Architecture Stress Test

Goal: make Milestone 9 the first consumer of the architecture contract.

The next applicability-quality eval should verify not only decision accuracy, but also architecture
invariants:

- applicability decisions are made before compliance review;
- generated rule packs derive only from validated applicable authorities;
- non-applicable authorities stay outside the compliance matrix but remain cited in their own
  artifact;
- unresolved or needs-adjudication decisions cannot promote;
- stale package fact, retrieval, graph, partition, or generated-pack hashes fail closed.

## Suggested Next Milestone Packet

Goal:
Add an architecture contract, import-cycle check, and first dependency fitness gate.

Non-goals:
Do not refactor the whole system, regenerate `source_library/`, or change public CLI behavior.

Relevant files or surfaces:
`docs/ARCHITECTURE.md`, `docs/architecture_contract.yaml`, `tests/test_architecture_contract.py`,
`src/usfs_r1_ea_sources/*.py`.

Required eval signal:
Architecture test fails on the current `compliance_review`/`rule_claim_binding` cycle, then passes
after the cycle is removed in the next sequence.

Required tests:
`PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py`,
focused tests for any moved rule-pack helpers, `PYTHONPATH=src uv run --extra dev ruff check src tests`,
`PYTHONPATH=src python -m compileall src`, and `git diff --check`.

Commit/push policy:
Commit the verified architecture-contract sequence. Push only when explicitly requested.

Stop conditions:
Stop if the contract exposes additional dependency cycles that require broader design decisions, or
if moving rule-pack helpers changes generated rule-pack or compliance-review behavior.
