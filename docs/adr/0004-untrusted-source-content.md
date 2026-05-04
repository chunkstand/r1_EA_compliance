# ADR 0004: Treat Source Content As Evidence Data, Not Instructions

Date: 2026-05-04

## Context

This repository downloads public web pages, PDFs, and local EA package documents. Those inputs may
contain malicious or irrelevant instructions. The system is safe while document text is treated as
evidence data with citations, hashes, offsets, and validation gates.

## Decision

Downloaded source text, extracted chunks, package chunks, retrieved evidence, and reviewer package
content are untrusted content. They are inputs to deterministic parsing, retrieval, validation, and
reporting. They are not instructions for agents, shell commands, browser actions, filesystem writes,
network calls, or external communications.

Any future model-facing or agent-facing tool that combines untrusted content with privileged local
state, filesystem writes, network access, browser automation, email, Slack, or external APIs must
declare a risk level and a human gate before execution.

## Consequences

Compliance findings remain bound to source records, citations, hashes, offsets, rule packs, and
validation artifacts. Model-assisted synthesis, if added later, is a report layer over deterministic
evidence and must not become a hidden authority.

## Verification Gate

Future model/tool milestones should add adversarial document fixtures that try to override reviewer
instructions and should prove the output remains citation-bound and validation-gated.

## Supersession

Supersede this ADR only with a stricter untrusted-content policy that preserves the separation
between evidence and instructions.
