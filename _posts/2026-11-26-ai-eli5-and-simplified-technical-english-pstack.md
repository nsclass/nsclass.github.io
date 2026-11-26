---
layout: single
title: "AI - ELI5 and Simplified Technical English: Two Ways to Make an Agent's Answer Readable (with pstack)"
date: 2026-11-26 09:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - ai
  - llm
  - writing
permalink: "2026/11/26/ai-eli5-and-simplified-technical-english-pstack"
---

When you run several coding agents at once, your own reading speed becomes the limit. An agent can fix a bug in ten minutes and then explain the fix in one 74-word sentence that takes you three reads. Two techniques help, and they work on different things:

- **ELI5** ("explain like I'm five") changes the **words and ideas**. Remove jargon, and say what happens in everyday terms.
- **STE** ([ASD-STE100 Simplified Technical English](https://www.asd-ste100.org/)) changes the **sentence structure**. Give each sentence one fact, keep it short, and give each word one meaning.

[pstack](https://github.com/cursor/plugins/tree/main/pstack) is the Cursor skill pack that [poteto](https://x.com/poteto) (React core team, Cursor) uses every day. It ships both techniques as skills. [`/bro`](https://github.com/cursor/plugins/blob/main/pstack/skills/bro/SKILL.md) is its ELI5, and [`/technical-writing`](https://github.com/cursor/plugins/blob/main/pstack/skills/technical-writing/SKILL.md) contains its STE layer. This post runs both skills on one agent reply, then puts the results side by side in an interactive checker.

## The case: a scroll-drift bug report

The prompt comes from the pstack README:

```
/poteto-mode this pr has a subtle bug where the scroll drifts every 750ms even when idle.
repro first, then fix and verify.
```

Below is the kind of reply an agent often writes when it finishes. The component names (`useStickyScroll`, `measureRow()`, `ChatPanel`) are made up for this post.

> I've thoroughly investigated the scroll drift issue and identified the root cause — it's a crucial interplay between the ResizeObserver callback and the virtualized list's scroll anchoring logic, which leverages a 750ms polling interval in useStickyScroll to re-measure row heights, and since the measured heights are being rounded differently than the estimated heights, this causes a small delta to accumulate on each tick, ultimately resulting in the visible drift even when the user is idle. I've implemented a fix that ensures measurements are compared with a tolerance, and additionally removed the redundant polling since the ResizeObserver already handles it. It should be noted that this may potentially also affect the chat panel. Let me know if you'd like me to make any further changes!

All the facts are in that reply. Its first sentence holds six of them, and it uses three names for one quantity ("row heights", "measured heights", "measurements"). The one risk is buried in a hedge ("may potentially").

## Try it: one reply, four ways to write it

Click the four tabs to compare the versions. Each bar is one sentence, and the ticks mark STE's 20-word and 25-word limits. Each highlight marks a rule from pstack's `unslop` or `technical-writing` skill, and you can hover over it to see which one. Open **Edit the text or paste your own** to check your own text.

<iframe class="anim-frame" src="/assets/html/ai-eli5-ste-pstack.html" title="ELI5 vs STE sentence checker" style="width:100%;height:900px;border:1px solid #e8e8e8;border-radius:8px"></iframe>

| Version | Sentences | Longest | Words per sentence | Flags | Grade (approx.) |
|---|---|---|---|---|---|
| Agent's first reply | 4 | 74 | 30.8 | 16 | 16.5 |
| Classic ELI5 (analogy) | 5 | 18 | 11.8 | 0 | 5.4 |
| `/bro` (plain ELI5) | 7 | 15 | 12.7 | 0 | 4.6 |
| `/technical-writing` (STE) | 13 | 10 | 7.8 | 0 | 4.4 |

The second row is why you can't judge these versions by the numbers alone. The analogy version has no flags and reads at grade 5. It is also the worst answer, because it drops every fact a reviewer needs.

## ELI5: change the words, keep the mechanism

ELI5 comes from Reddit's r/explainlikeimfive. In practice it means "explain it to a smart person outside the field", not literally to a child. The usual way to do that is an analogy:

> Imagine two kids building a tower of blocks. One kid counts the blocks and the other kid guesses. Every so often they argue about how tall the tower is, and the tower wobbles a tiny bit. After a while, all the wobbles add up and the tower leans.

The analogy loses four facts: which code changed, the 750 ms timer, that the timer was deleted, and that `ChatPanel` is untested. "Argue" is not a mechanism, so you can't check the analogy against the code.

pstack avoids this. `/bro` is one instruction:

```
Restate your last message. Stop using jargon and speak coherently. State it more simply
and concisely, like one human talking to another.
```

Its sibling skill [`teach`](https://github.com/cursor/plugins/blob/main/pstack/skills/teach/SKILL.md) states the rule that rules out the analogy: *"State the concrete mechanism, not a metaphor, a framing, or a preview of what is coming."* The result keeps every fact and uses words you would say out loud:

> The list moves by itself because two parts of the code disagree about row height. Every 750 ms, one part measures each row and rounds the height to whole pixels. The other part uses an unrounded guess. The list shifts by the gap between the two numbers, and the shifts add up. I made the code ignore gaps smaller than 1 pixel. I also deleted the 750 ms timer, because `ResizeObserver` already reports size changes. The chat panel uses the same list, and I have not tested it yet.

So in pstack, ELI5 means plain words with the real mechanism, not a simpler story.

## STE: one fact per sentence

ASD-STE100 started in the early 1980s at AECMA, the European aerospace industry association, for aircraft maintenance manuals. Many mechanics who read those manuals were not native English speakers, and a misread step could ground an aircraft or worse. Today ASD maintains the specification. It has two parts:

1. **Writing rules.** At most 20 words in a procedural sentence and 25 in a descriptive one. One instruction per sentence. Active voice in procedures. Warnings and cautions come before the step they apply to. Keep the articles ("the", "a").
2. **A controlled dictionary.** Each approved word has one meaning and one part of speech, and each unapproved word lists an approved replacement.

pstack's `technical-writing` skill takes the rules and compresses the dictionary into one line: *"Give each word one meaning, and pick one word per action."* It also places STE as the third of five layers. Each layer fixes a different kind of problem in the example reply:

<iframe class="anim-frame" src="/assets/html/ai-eli5-ste-pstack.html?view=layers" title="The five layers of pstack technical-writing" style="width:100%;height:560px;border:1px solid #e8e8e8;border-radius:8px"></iframe>

| Layer | Fixes | Example change |
|---|---|---|
| [Diátaxis](https://diataxis.fr/) | a document doing several jobs | work report + explanation + offer becomes one PR body |
| [Google developer style](https://developers.google.com/style) | unclear actor, missing names | "heights are being rounded" becomes "`measureRow()` rounds the measured height" |
| **STE** | sentences that hold several facts | a 74-word sentence becomes four sentences of 7 to 11 words |
| Global English | text with two possible readings | "this causes a small delta" becomes "The differences add up on each tick." |
| [`unslop`](https://github.com/cursor/plugins/blob/main/pstack/skills/unslop/SKILL.md) | words that mark AI-written text | "crucial", "leverages", "Let me know if..." are deleted |

The final PR body:

```markdown
## Fix scroll drift in an idle list
The list scrolls by itself when the user does nothing. The cause is a rounding mismatch
between two row heights.
- Every 750 ms, `useStickyScroll` calls `measureRow()` for each visible row.
- `measureRow()` rounds the measured height to whole pixels.
- `estimateRow()` returns the estimated height without rounding.
- `useStickyScroll` moves the scroll anchor by the difference. The differences add up on each tick.

This PR makes two changes:
1. `useStickyScroll` ignores a difference smaller than 1 px.
2. This PR removes the 750 ms timer. `ResizeObserver` already reports each size change.

Caution: `ChatPanel` uses the same list. Test scrolling in `ChatPanel` before you merge this PR.
```

The warning moved from the last hedged sentence to a labeled caution that comes before the merge step it guards. That move comes straight from STE.

## Which one, when

| | ELI5 (`/bro`) | STE (`/technical-writing`) |
|---|---|---|
| Changes | words and ideas | sentence structure |
| Reader | you, now, in the chat | reviewers, future maintainers, non-native readers, other agents |
| Shape | one short paragraph | heading, lists, labeled caution |
| How it fails | an analogy drops facts | reads flat, and is too much for a quick chat reply |
| When to use it | after a dense reply you need to understand now | docs, RFCs, READMEs, PR descriptions, commit messages |

The two techniques combine well. Use `/bro` to understand the change, then `/technical-writing` for the text that lands in the repo.

## The same rules make prompts clearer

An agent reads a skill file the same way a mechanic reads a manual. A pronoun that can point at two things gives the model two ways to read the instruction. I ran the checker on three pstack skill files (measured, frontmatter removed):

| Skill file | Sentences | Longest | Words per sentence | Over 25 words |
|---|---|---|---|---|
| `technical-writing` | 81 | 20 | 7.7 | 0 |
| `unslop` | 49 | 17 | 7.2 | 0 |
| `teach` | 67 | 44 | 13.6 | 7 |

`technical-writing` follows its own rule: no sentence is longer than 20 words. `unslop` has 19 flags only because it lists the words it bans. `teach` is written as explanation, so it has longer sentences.

If you don't use pstack, you can get most of the effect from a few lines in `CLAUDE.md` or `AGENTS.md`:

```markdown
## Writing replies
- Lead with the result. Do not report what you did.
- One fact per sentence. Keep sentences under 25 words, and instructions under 20.
- Name the real function, file, or flag. Call each thing by one name.
- Put a warning before the step it applies to.
- Explain the real mechanism in plain words. Do not use analogies.
- No em dashes, no semicolons, and at most one hedge.
```

The checker above is a page of regular expressions, so it misses some problems and flags some sentences that are fine. The analogy row shows its biggest limit: it measures how sentences are built, not whether the facts survived. That part still needs a human, or a second agent that has the code.

<script>
document.querySelectorAll('iframe.anim-frame').forEach(function (f) {
  function fit() { try { f.style.height = (f.contentDocument.body.offsetHeight + 4) + 'px'; } catch (e) {} }
  f.addEventListener('load', function () {
    fit();
    try { new ResizeObserver(fit).observe(f.contentDocument.body); } catch (e) {}
  });
});
</script>
