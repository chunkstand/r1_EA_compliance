# System Design Thought-Leader Review

Date: 2026-05-06

## Purpose

This brief reviews the current USFS Region 1 EA reviewer system through applicable system-design,
AI-evaluation, RAG, legal-technology, observability, and provenance lenses. It is intended to guide
the next build work without replacing the repo's current milestone plans, generated artifacts, or
verification gates.

The review is grounded in the current repo architecture:

- workbook-as-contract source capture;
- artifact-first local source library under `source_library/`;
- deterministic applicability before compliance review;
- generated applicability rule packs;
- citation-bearing compliance and Forest Plan outputs;
- NEPA 3D graph exports over audited artifacts;
- architecture fitness gates backed by `docs/architecture_contract.toml`;
- current next lane: EA consistency decision-support synthesis for
  `v1-cg-ecid-compliance-review`.

## Current System Assessment

The system is directionally strong. Its best design choices are the ones that keep authority,
evidence, and reviewer readiness separate:

- Applicability is now a pre-review artifact family, not an implicit compliance-review side effect.
- Non-applicable authorities are first-class outputs with search coverage, not omitted rows.
- Compliance review consumes generated applicable rules instead of deciding applicability itself.
- Source capture, extraction, retrieval, graph, claim, applicability, compliance, and eval outputs
  are durable and replayable.
- Architecture drift has a cheap deterministic gate.
- The current East Crazies proving review has a well-bounded next product: a generated
  decision-support document over existing audited artifacts.

The main build risk has shifted. The problem is no longer "can this repo produce evidence-backed
review artifacts?" The problem is now "can the synthesis layer stay as disciplined as the evidence
layer?" The next report generator can easily become a hand-authored narrative that quietly collapses
the distinction between applicable authorities, non-applicable authorities, Forest Plan components,
implementation confirmations, and residual risk. That would weaken the system even if the prose is
more readable.

## Expert Lenses

### Rich Sutton: scale search, learning, and evals instead of hidden heuristics

Sutton's "Bitter Lesson" lens says this system should continue improving through better corpus
coverage, retrieval, graph search, eval fixtures, adjudication data, and telemetry rather than
through buried NEPA-specific branches. The repo already encodes this in
`docs/BITTER_LESSON_ALIGNMENT.md`. The next step is to preserve that stance in the
decision-support layer: the generated report should be a renderer over audited data and validation
results, not a new hidden reasoning engine.

Build guidance:

- Keep legal and NEPA knowledge in workbook rows, authority-family configs, rule packs, Forest Plan
  profiles, eval fixtures, and generated artifacts.
- Add report-quality eval cases instead of adding narrative heuristics.
- When the generated synthesis is weak, first inspect missing evidence, retrieval misses,
  component summarization gaps, and residual-risk taxonomy gaps.

### Fowler, Ford, Parsons, Kua: evolutionary architecture needs fitness functions

The repo's architecture contract is a practical fitness function: module ownership, import
direction, command grouping, and artifact ownership are checked continuously. This matches the
evolutionary architecture lens: guide incremental change with automated feedback rather than a
static architecture diagram.

Build guidance:

- Add the decision-support report family to the architecture contract when the generator is built.
- Keep every synthesis sequence under the same closeout pattern: focused tests,
  `tests/test_architecture_contract.py`, and `git diff --check`.
- Prefer new deterministic gates over reviewer instructions that only live in prose.

### John Ousterhout: deep modules, simple interfaces, hidden complexity

Ousterhout's lens is the strongest warning for the next implementation. The codebase already has
large, important modules. The decision-support generator should not add another shallow module that
passes many raw JSON shapes around and forces every caller to understand all upstream artifacts.

Build guidance:

- Give the report generator a small public interface:
  `review_id`, `output_dir`, optional `source_set_id`, and explicit validation flags.
- Hide artifact-loading complexity behind typed internal records.
- Make the canonical JSON schema stable and let Markdown/PDF be renderers from that JSON.
- Do not create pass-through layers where each function merely relays upstream dicts.

### Adam Tornhill: refactor where churn, size, and risk intersect

The current live size signal still points to risk concentration:

- `compliance_review.py`: 3,575 lines;
- `nepa_knowledge_graph_export.py`: 3,391 lines;
- `forest_plan_components.py`: 3,302 lines;
- `evidence_graph.py`: 2,693 lines;
- applicability validation/eval/decision modules: 2,300-2,500 lines each.

Tornhill's hotspot lens says not all complexity is equally important. The next refactors should be
driven by files that are both large and frequently modified in milestone work.

Build guidance:

- Do not refactor large modules during the decision-support schema sequence unless required.
- After the report generator exists, target the next split at the new report-rendering boundary or
  at the largest active module touched by that milestone.
- Keep hotspot reports as recurring milestone inputs, not one-time cleanup artifacts.

### Hamel Husain, Shreya Shankar, and Eugene Yan: evals should target observed failure modes

The current system has strong eval culture. The next quality jump is to make report synthesis evals
as explicit as applicability and phase evals. Hamel's lens favors binary decisions with detailed
critiques; Yan's lens favors task-specific metrics such as precision, recall, false positives, and
false negatives for classification/extraction-like work.

Build guidance:

- Add report evals that answer binary questions with critiques:
  - Does every applicable authority row appear exactly once?
  - Does every row cite package evidence and source evidence?
  - Are all non-applicable authorities summarized without becoming compliance findings?
  - Are residual risks separated from compliance findings?
  - Does the PDF derive from the canonical JSON?
- Track false-positive synthesis claims and false-negative omissions separately.
- Treat "all green" evals skeptically unless they include hard negatives and malformed artifact
  fixtures.

### Charity Majors: inspect individual high-cardinality events, not only aggregate health

The system already writes many artifacts, but the next debugging burden will be explaining why a
specific authority, Forest Plan standard, implementation confirmation, or residual risk appears in
the supervisor-facing report. Observability for this system should mean a traceable chain from each
report section back to candidate authority, package fact, retrieval result, graph path, source
claim, compliance finding, and source artifact hash.

Build guidance:

- Add a report manifest that records input artifact hashes and per-section source dependencies.
- Add per-row `trace_ids` or equivalent IDs for authority rows, standard rows, non-applicable
  summaries, and risk items.
- Prefer wide, high-cardinality diagnostic rows over aggregate-only summaries.
- Make outlier inspection easy: a reviewer should be able to ask "why is this one authority here?"
  and find the exact supporting chain.

### Microsoft GraphRAG and DRIFT: graph search is for sensemaking, not final authority

GraphRAG/DRIFT-style work supports this repo's graph direction: combine broad corpus context with
local refinement and preserve navigation back to source chunks. The key boundary is that graph
search should discover and organize evidence, while deterministic applicability and validation
artifacts remain the source of reviewer-ready decisions.

Build guidance:

- Keep NEPA 3D and graph exports as inspection, traversal, readiness, and explanation surfaces.
- Do not let graph layout or graph centrality become a compliance decision rule.
- For the decision-support report, use graph traces to explain relationships, not to invent
  authority applicability.

### LegalBench-RAG and Legal RAG Bench: retrieval sets the ceiling in legal RAG

The legal-RAG benchmark literature is directly applicable. LegalBench-RAG emphasizes precise
legal-passage retrieval and expert annotation. Legal RAG Bench goes further by decomposing legal
RAG errors into retrieval and reasoning contributions and reports retrieval as the primary driver
of end-to-end legal RAG performance.

Build guidance:

- Keep applicability evals separate from compliance evals.
- Add report evals that distinguish retrieval/source-evidence omission from synthesis omission.
- Prioritize hard-negative authority and Forest Plan cases over broad generic legal Q&A.
- Do not claim "legal reasoning quality" from fluent report text; claim only artifact-backed
  coverage, traceability, and validation status.

### Simon Willison: untrusted content plus tools is the danger zone

This repo already treats downloaded and package content as untrusted evidence. That boundary must
survive any later model-assisted synthesis. The risky pattern is an LLM that reads untrusted source
content while also having access to private data, filesystem writes, browser/network actions, or
external communication.

Build guidance:

- Sequence 1 and Sequence 2 of the decision-support milestone should be deterministic and
  model-free unless a later milestone explicitly adds a gated model layer.
- If model-assisted synthesis is added later, make it a constrained renderer over canonical JSON,
  with no write/tool authority beyond producing candidate prose for validation.
- Add adversarial package/source fixtures before any privileged model/tool path is introduced.

### W3C PROV and NIST AI RMF: trust comes from provenance, evaluation, and oversight

The repo's hash lineage and generated manifests already align with provenance-first design. The
decision-support report should make this visible to a reviewer, not just to developers. NIST AI RMF
also supports keeping risk management, evaluation, and human oversight in the design rather than
bolted on afterward.

Build guidance:

- Model the report manifest around entities, activities, agents/tools, derivations, hashes, and
  validation status.
- Keep the decision-use caveat explicit: this is decision support, not legal advice or final line
  officer judgment.
- Make residual risks and required implementation confirmations explicit, evidence-linked, and
  reviewable.

## Recommended Build Direction

The next build should continue with the existing EA consistency decision-support milestone, but with
these research-informed constraints:

1. Finish the Sequence 0 preflight boundary before report implementation.
   Do not start the generator if artifact freshness, authority partition coverage, residual-risk
   mapping, or implementation-confirmation mapping is unresolved.
2. Implement Sequence 1 as a schema and fixture milestone.
   The schema should define canonical JSON, Markdown/PDF renderings, manifest lineage, row-level
   trace IDs, fail-closed validation states, and report eval expectations.
3. Implement Sequence 2 as a deterministic generator.
   It should read audited review artifacts only. It should not read manual root-level drafts or scan
   raw artifact filenames.
4. Implement Sequence 3 as a real East Crazies generated report.
   Treat generated files under `source_library/` as ignored local outputs unless repo policy
   changes.
5. Add report-quality evals before broadening scope.
   The report should be evaluated for omission, overclaiming, source traceability, non-applicable
   boundary preservation, Forest Plan standard coverage, PDF validity, and manifest freshness.
6. After the report lane is stable, run a hotspot-driven split.
   Use live size/churn data to choose the next refactor, and keep it separate from report behavior.

## Concrete Acceptance Gates For The Decision-Support Lane

The generated decision-support report should fail closed unless all of these hold:

- The review ID, source set ID, package manifest hash, applicability validation hash, generated
  rule-pack validation hash, compliance matrix hash, Forest Plan component hash, standard coverage
  hash, non-applicable authority hash, and residual-risk source hash match current inputs.
- Every applicable authority appears exactly once in the report and maps to a compliance finding.
- Every applicable authority row has package evidence, source evidence, source-record identity,
  authority-family identity, applicability basis, compliance status, and limitation fields.
- Every non-applicable authority remains outside the compliance findings and remains traceable to
  search coverage.
- Forest Plan component counts and applicable-standard counts match current generated artifacts.
- Residual risks are separate from compliance findings and point to evidence or implementation
  confirmations.
- Markdown and PDF are rendered from canonical JSON.
- The PDF exists and begins with `%PDF-`.
- The report manifest contains enough lineage for an independent reviewer to replay the generation.

## Post-Implementation Alignment Check

The EA consistency decision-support lane now aligns with the panel guidance through the completed
Sequence 0 through Sequence 5 work and the post-sequence rendering-gate closeout:

- The report generator is deterministic and reads audited review artifacts, not manual root-level
  East Crazies draft exports.
- The canonical JSON remains the machine contract; Markdown and PDF are renderings from that JSON.
- The architecture contract owns the `decision_support` layer, command group, and generated report
  family.
- The manifest records input hashes, per-section dependencies, validation status, and replayable
  lineage.
- Row-level trace IDs, source selectors, citation labels, artifact hashes, and evidence spans are
  present for reviewer-facing report rows.
- Validation and phase eval fail closed on stale hashes, missing sections, missing evidence,
  non-applicable boundary omissions, missing applicable standards, unresolved implementation
  confirmations, residual-risk legal conclusions, missing/invalid PDF, and manual-draft
  dependencies.
- The post-sequence gap-close pass adds live Markdown/PDF supervisor rendering checks for front
  matter, review snapshot, table summaries, key counts, section ordering, and source-pointer
  content. Missing rendering content fails as `false_negative_synthesis_omission`.

Residual scope:
The panel's "after the report lane is stable, run a hotspot-driven split" recommendation remains a
separate future milestone. It should not be folded into the completed decision-support sequence
because it targets broader module design, not report readiness.

## Stop Conditions

Stop the build and write a follow-up milestone if any of these occur:

- The report needs hand-authored conclusions not present in audited artifacts.
- The generator would need to promote root-level manual draft exports as canonical evidence.
- The current review is no longer reviewer-ready.
- Authority counts drift without an explained upstream rerun.
- Non-applicable authority coverage is missing, stale, or not disjoint from applicable authorities.
- Forest Plan consistency requires a different profile or uncited manual interpretation.
- A model-assisted path is proposed without adversarial untrusted-content fixtures and a human gate.

## Sources

- Rich Sutton, "The Bitter Lesson": https://bitterlesson.ai/
- Martin Fowler, foreword to "Building Evolutionary Architectures":
  https://martinfowler.com/articles/evo-arch-forward.html
- Thoughtworks, "Fitness function-driven development":
  https://www.thoughtworks.com/en-us/insights/articles/fitness-function-driven-development
- John Ousterhout, Stanford CS 190 "Managing Complexity":
  https://web.stanford.edu/~ouster/cgi-bin/cs190-spring15/lecture.php?topic=complexity
- Adam Tornhill, "Software (r)Evolution - Part 2":
  https://www.adamtornhill.com/articles/software-revolution/part2/index.html
- Hamel Husain, "A Field Guide to Rapidly Improving AI Products":
  https://hamel.dev/blog/posts/field-guide/
- Eugene Yan, "Task-Specific LLM Evals that Do & Don't Work":
  https://eugeneyan.com/writing/evals/
- Charity Majors and Phillip Carter, "Observability in the Age of AI":
  https://www.honeycomb.io/blog/observability-age-of-ai
- Microsoft Research, "Introducing DRIFT Search":
  https://www.microsoft.com/en-us/research/blog/introducing-drift-search-combining-global-and-local-search-methods-to-improve-quality-and-efficiency/
- LegalBench-RAG:
  https://arxiv.org/abs/2408.10343
- Legal RAG Bench:
  https://arxiv.org/abs/2603.01710
- Simon Willison, "The lethal trifecta for AI agents":
  https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/
- W3C PROV Overview:
  https://www.w3.org/TR/prov-overview/
- NIST AI Risk Management Framework:
  https://www.nist.gov/itl/ai-risk-management-framework
