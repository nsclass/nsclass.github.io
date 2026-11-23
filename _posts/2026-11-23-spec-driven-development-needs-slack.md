---
layout: single
title: "Thoughts on Spec-Driven Development in the Age of AI"
date: 2026-11-23 18:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - ai
  - api-design
permalink: "2026/11/23/spec-driven-development-needs-slack"
---

Spec-driven development is having a moment. Write a precise spec, hand it to an AI agent, and the implementation takes care of itself. I care a lot about specs, formal verification and LLM code-generation pipelines, so I want this to work. But the more I watch the trend, the more it looks like a mistake our industry already made once.

The missing piece has a name: **slack**.

## We have seen this movie before

Waterfall made a simple promise. Define every requirement up front, capture the design in UML, and implementation becomes a translation step. Nobody needs to worry much about the code, because the thinking is already done.

It didn't work. Requirements moved while the project was still in design. The design turned out to be wrong in ways that only showed up once someone tried to build it. And every late change was expensive, because the whole process assumed changes wouldn't happen.

Spec-driven development with AI makes the same pitch in new clothes. The spec is the new UML. The coding agent is the new implementation team that "just builds what the document says." Get the spec right, and the rest is mechanical.

There is one real difference: generating code is now nearly free. That sounds like it fixes waterfall's cost problem. It doesn't. It means we can produce a large amount of code against a wrong spec very quickly, and be wrong faster than ever.

## What extreme programming learned

Extreme programming grew out of waterfall's failures. Its core insight was humble: requirements will change, and the first implementation is how you find out what the design should have been.

So XP made design a continuous activity instead of a phase. Short iterations, tests that pin down behavior, and constant refactoring let the design absorb what each round of building taught. The point was never "no design." The point was a design that could keep changing without falling apart.

That lesson didn't expire when AI arrived. If anything, it matters more now, because the loop between "write the spec" and "see the code" has shrunk from months to minutes.

## The missing ingredient: slack

The main thing spec-driven development leaves out is slack. I took the word from Lisa Lippincott's C++Now 2026 talk, [Cutting Some Slack for our Programs](https://www.youtube.com/watch?v=xwnRPyRK5h4).

Slack is the room we deliberately leave in a program so that it can change. It is preparation for facts we already know: what we build today will be redesigned, reused in ways we didn't plan, or removed. Without that preparation, software can't follow changing requirements, and it can't keep evolving for as long as it stays useful.

A spec that describes exactly what the software must do today, completely and precisely, is a spec with zero slack. It can be perfectly correct and still brittle. Think of a bridge built to the exact length of the gap on the day it was measured, with no expansion joints. It fits beautifully until the first hot afternoon.

## Three plans: redesign, reuse, remove

Slack comes down to three plans you make before you need them.

| Plan | What you assume | What it asks of the spec |
|---|---|---|
| Plan to redesign | This design is a first draft | Separate the contract callers rely on from details that are free to change |
| Plan to reuse | Someone will use this in a context you didn't foresee | State preconditions explicitly; keep pieces small and avoid hidden assumptions about the caller |
| Plan to remove | This code will be deleted one day | Keep the feature behind a clear seam so every dependency on it can be found and cut |

**Plan to redesign.** The first version teaches you what the second should be. If the spec pins down every internal detail, the agent will faithfully build them, and the redesign becomes a rewrite.

**Plan to reuse.** Code that only works under the exact conditions of its first caller is not really reusable. A spec that says what a component requires, rather than silently assuming it, leaves room for the next caller.

**Plan to remove.** Code that is hard to delete becomes permanent by accident. Planning for removal means keeping a feature's assumptions from leaking into everything around it.

## Kent Beck: the genie and the options

Kent Beck, who created extreme programming, approaches the same problem from the AI side in his Prodacity 2026 talk, [Software Engineering in the Age of AI](https://www.youtube.com/watch?v=F8fBgDCf2Y4). He describes AI as a genie: it grants your wish, along with side effects you never asked for. It produces plausible code fast, but plausible is not the same as working.

His prescription sounds a lot like slack. After each feature, stop and restore the options for changing the code before you build the next one. And measure progress by how close you are to the goal of the software, not by how many lines got written.

This connects to an idea from his book *Tidy First?*: software is worth its features plus its options, the cheap ability to change it later. Spec-driven generation is very good at producing features. Left alone, it quietly spends the options. **A spec with no slack is a plan to use up the options as fast as the agent can type.**

## Specs with slack built in

None of this is an argument against specs. It is an argument for specs that expect to change. A few practices I'd suggest:

1. **Layer the spec.** Mark which parts are the stable contract and which are provisional. The agent should treat the second group as free to change.
2. **Treat the first implementation as a probe.** Expect the generated code to teach you something, and plan to revise the spec from it. Spec and code evolve together; the loop goes both ways.
3. **Add a change budget to every spec.** Three short answers: what is likely to be redesigned, who else might reuse this, and how it would be removed.
4. **Tidy between features.** Before the agent starts the next feature, spend a pass restoring options: simplify, cut dead paths, clean up the seams.
5. **Verify the contract, not the incidentals.** Put tests and formal verification on what callers truly rely on. Everything else stays free to move.

## Closing thought

Waterfall didn't fail because planning is bad. It failed because it planned for a world that would hold still. Spec-driven development with AI risks the same failure, only faster.

The fix is not fewer specs. It is specs that admit they will change: plan to redesign, plan to reuse, plan to remove. That is the slack that lets software last.

## References

- Lisa Lippincott, [Cutting Some Slack for our Programs](https://www.youtube.com/watch?v=xwnRPyRK5h4), C++Now 2026
- Kent Beck, [Software Engineering in the Age of AI](https://www.youtube.com/watch?v=F8fBgDCf2Y4), Prodacity 2026 ([notes on this blog](/2026/11/23/software-engineering-age-of-ai-kent-beck))
