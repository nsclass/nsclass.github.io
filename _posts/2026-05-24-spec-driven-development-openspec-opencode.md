---
layout: single
title: "Spec-Driven Development with OpenCode and OpenSpec"
date: 2026-05-24 10:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - ai
permalink: "2026/05/24/spec-driven-development-openspec-opencode"
---
[Spec-Driven Development with OpenCode and OpenSpec](https://www.youtube.com/watch?v=M3dp9u1wZes)

"Vibe coding" — letting an AI agent invent its way from a one-line prompt to a feature — works just often enough to be dangerous. The agent compiles, the tests pass, and the PR lands. Then a week later someone asks *why* a decision was made, what edge cases were considered, or how this change relates to the next one, and the answer is gone: it never lived anywhere except in a chat transcript.

This video walks through an alternative: a **Spec-Driven Development (SDD)** loop built from two open-source tools — **OpenSpec** for the spec layer and **OpenCode** for the agent runtime — wired together with a handful of skills that enforce git discipline, generate diagrams, capture decisions, and run multiple changes in parallel.

## The Core Idea: Agree Before You Code

Spec-Driven Development inverts the usual AI-coding loop. Instead of:

> *prompt → code → review → maybe-write-something-down*

…you write down what you're building **first**, get explicit alignment between human and agent on that document, and only then turn it into code. The spec becomes the source of truth, and the implementation is its shadow.

OpenSpec ships a default schema (`spec-driven`) that produces four artifacts for every change, each in its own folder:

| Artifact | Purpose |
|---|---|
| `proposal.md` | What we want to change and why |
| `specs.md` | The new/modified capability described as deltas: `ADDED`, `MODIFIED`, `REMOVED` |
| `design.md` | Technical approach, alternatives, trade-offs |
| `tasks.md` | The actionable checklist the agent will work through |

When a change is **archived**, only `specs.md` is folded back into the unified, living source-of-truth specification. Proposal, design, and task lists were scaffolding — they served their purpose at the proposal stage. The spec itself is what future you (and future agents) need.

## The Two Halves: OpenSpec + OpenCode

- **OpenSpec** is the spec framework — it generates the folders, structures the artifacts, and exposes slash commands (`/opsx:propose`, `/opsx:apply`, `/opsx:archive`) that work across 25+ AI assistants.
- **OpenCode** is an open-source agent runtime that hosts the LLM session, executes the slash commands, and applies *skills* — small, scoped instruction modules that shape how the agent behaves in a particular phase.

Skills are the lever. Each one is a tightly written rulebook that activates in a specific phase of the lifecycle.

## The Skills That Make It Work

The talk highlights five skills that turn a vanilla OpenSpec install into a disciplined SDD workflow.

### 1. `openspec-git-discipline` — gates around every phase

The rule is one sentence: **every OpenSpec state change must cross `main` before the next lifecycle phase depends on it.** That means the proposal, the application, and the archive each correspond to a real commit on `main`, not to in-flight branch state the agent silently forgets about.

This sounds boring until you've watched an agent "apply" a change that was never committed, then "archive" it, leaving you with a spec that claims a feature exists and a working tree that has never seen it.

### 2. `grill-me` — interrogate the proposal

Borrowed from Matt Pocock, this skill makes the agent ask the user sharp, sequential questions during the proposal phase rather than guessing. The point is to surface ambiguity *while the spec is still cheap to change* — before any code, diagrams, or tasks are written against the wrong shape.

### 3. `c4-diagrams` — visualize the design

Activated in the design phase, this generates [C4-model](https://c4model.com) diagrams (system context, container, component, dynamic, deployment) in ASCII or Mermaid. The skill picks the abstraction level based on what's actually changing — you don't get a component diagram for a one-line config tweak.

### 4. `architectural-decision-records` — capture the *why*

ADRs are the canonical place to write down "we picked X over Y because Z." This skill produces them in your format of choice (MADR, Nygard, Y-Statement, custom). Using the `spec-driven-with-adr` schema, ADRs live **alongside** the source-of-truth spec — not inside a single change folder — so they outlive any one feature.

### 5. `openspec-bulk-apply-change` — parallel changes in worktrees

This is the showcase capability. Once multiple proposals are approved on `main`, the skill spins up a Git worktree per change and dispatches a SubAgent into each. Every SubAgent runs **Verify** before merging back, which checks the proposed change against the source-of-truth spec — catching cross-change conflicts before they collide in `main`.

The flow becomes:

```
propose on main → fan out: worktree-per-change → SubAgent apply
                ↓
              verify ↔ source-of-truth spec
                ↓
           merge in order → archive
```

This is what makes parallel feature work *actually* parallel instead of "three branches that will conflict next week."

## The Schema Glues It Together

A schema in OpenSpec is the recipe that orders the artifacts. The `intent-driven` schema used in the talk sequences them as:

```
proposal → specs → design → adr → tasks
```

This ordering matters: you don't write tasks before you've decided the design, and you don't decide the design before the spec deltas are clear. Custom schemas are configured via `config.yaml`, so a team can codify their own flow rather than picking among defaults.

## The Lifecycle in Practice

A typical change runs like this:

```bash
# 1. Bootstrap
npm install -g @fission-ai/openspec@latest
cd your-project
openspec init        # pick profiles: git-discipline, c4, adr, ...

# 2. Propose (interactive — grill-me kicks in)
/opsx:propose add-rate-limiting-to-public-api

# 3. Commit the proposal to main — git-discipline gate

# 4. Apply (in a worktree if running with others)
/opsx:apply add-rate-limiting-to-public-api

# 5. Verify against source-of-truth spec, merge to main

# 6. Archive — specs.md folds into the unified spec
/opsx:archive add-rate-limiting-to-public-api
```

What you get on disk afterward isn't a vague chat log — it's a structured trail: the proposal that explained *why*, the spec deltas that define *what*, the design and ADRs that defend *how*, and the task list that proves *what was actually done*.

## Why This Matters

Three things change once SDD is in place:

1. **Reviewable intent.** A PR isn't "the agent did some stuff" — it's "here's the proposal, here's the spec delta, here's the ADR, here's the code that satisfies it." Reviewers argue about intent on the spec, not about syntax on the diff.
2. **Parallelism without merge hell.** Worktrees plus a single source-of-truth spec mean two agents can build different features without stepping on each other, because each verifies its delta against the same spec before merging.
3. **Memory that survives the session.** When the next change lands six months later, the spec, ADRs, and archived proposals are still there. The agent (and the human) start with context instead of with a blank chat.

Vibe coding optimizes for the first iteration. Spec-Driven Development optimizes for the **tenth** — the one where you've forgotten what you built and the codebase has to explain itself.

## Resources

- [OpenSpec on GitHub](https://github.com/Fission-AI/OpenSpec) — the spec framework
- [intent-driven.dev](https://intent-driven.dev/) — workflow guides, schemas, and the template referenced in the talk
- [Spec-Driven Development with OpenSpec and OpenCode](https://intent-driven.dev/blog/2026/05/10/spec-driven-development-openspec-opencode/) — companion write-up
- [C4 model](https://c4model.com) — the diagramming notation the design phase uses
