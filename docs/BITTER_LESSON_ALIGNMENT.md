# Bitter Lesson Alignment

Source: Rich Sutton, "The Bitter Lesson", March 13, 2019.
https://www.incompleteideas.net/IncIdeas/BitterLesson.html

## Core Reading

Sutton's practical warning is that AI systems built around hand-authored domain knowledge can look
good early, then plateau as soon as broader data, search, learning, and compute become available.
For this project, the lesson is not to remove expert knowledge. It is to keep expert knowledge in
auditable data, prompts, rulesets, and evaluations while the runtime stays as general as possible.

The NEPA EA reviewer should therefore optimize for:

- scalable corpus capture
- robust extraction
- broad evidence retrieval
- eval loops that expose misses
- model-facing evidence graphs
- learning-ready telemetry

It should avoid making compliance quality depend on hidden handcrafted heuristics.

## Architecture Commitments

1. Search and learning are first-class.

The system should improve primarily by ingesting more source material, running more retrieval and
review evals, capturing more failure cases, and applying stronger general search or learning
methods. Narrow keyword tricks are acceptable only as transparent baselines or filters, not as the
core reviewer intelligence.

2. Domain knowledge is data.

NEPA concepts, Forest Service policies, source roles, review topics, and compliance expectations
belong in the workbook, catalog tables, knowledge-base records, eval fixtures, or versioned rule
packs. They should not be scattered through extraction, retrieval, graph, or answer-generation code
as hidden conditionals.

3. The runtime builds meta-methods.

The stable code should parse, chunk, index, retrieve, trace, evaluate, and report. It should not
pretend that a fixed set of developer-authored categories captures the complexity of EA compliance.
The system should make it easy for models and evaluators to discover patterns from evidence.

4. Evidence beats intuition.

Reviewer conclusions must be backed by cited chunks, artifact hashes, parser versions, source
offsets, and graph traces. A plausible compliance statement with weak provenance is a failure, not a
shortcut.

5. Scale before cleverness.

When review quality is weak, the default next step is to improve corpus coverage, extraction
quality, retrieval recall, evaluation cases, and error telemetry before adding special-case review
logic.

## Current Alignment

The current v1 foundation is aligned in the important places:

- raw source artifacts are immutable and hash-checked
- extraction is rebuildable from the reviewer catalog
- retrieval is a general local index over chunks and metadata
- retrieval evals measure evidence recall and provenance coverage
- the evidence graph is built from source/chunk/evidence primitives
- the source claim graph is built from exact source-text spans, not generated conclusions
- graph validation rejects stale or forged evidence payloads
- compliance rule packs and coverage expectations are versioned data, not hidden runtime branches
- compliance review findings require package evidence, source evidence, source-claim links, and
  finding graph coverage
- gold adjudication fixtures are versioned data and run through the same compliance-review eval path
- phase eval separates capture, extraction, retrieval, graph, claim, rule binding, coverage, gold
  eval, and review readiness

The current full-library state is correctly treated as a gated v1 foundation. The system can inspect
and evaluate the captured corpus and deterministic seed packages, but it does not claim broad EA
review quality until adjudicated real-package eval coverage exists.

## Guardrails

General reviewer runtime modules must not encode NEPA-specific review terms as logic. The allowed
place for those terms is data:

- workbook rows
- catalog metadata
- review topics
- eval fixtures
- versioned compliance rule packs
- user-visible reports and docs

This keeps the core engine reusable and lets better corpus coverage, retrieval, graph reasoning,
and model evaluation improve the reviewer over time.

## Current Claim and Rule-Pack Milestones

The current claim and compliance milestones favor a computation-scalable reviewer loop:

- run full-corpus extraction rather than optimizing a one-source slice
- build broader retrieval evals from real EA review questions
- extract source claims with generic legal/action patterns and strict offset validation
- bind rule-pack requirements to validated source claims with deterministic scoring and explicit
  no-claim gaps
- evaluate final compliance-review findings against deterministic package fixtures
- validate rule-pack coverage against matrix rows, current source-claim links, source-claim terms,
  and compliance-review eval cases
- run adjudicated positive, mixed, and negative package profiles through a deterministic promotion
  gate
- add failure telemetry for missed evidence and unsupported answers
- keep compliance rule packs as data, with citations required for every claim-bearing finding
- keep generated conclusions downstream of retrieval, graph evidence, source-claim links, and eval
  gates

## Next Alignment Milestone

The next aligned step is expanding the gold eval set and triaging failures from more realistic EA
packages. This keeps the system on the Bitter Lesson path: improve quality through broader data,
stronger evaluation, and transparent failure telemetry before adding bespoke review logic or
model-generated synthesis.
