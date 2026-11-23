---
layout: single
title: "Plausible Is Not Working: Rest Between Features When the Genie Writes the Code (Kent Beck, Prodacity 2026)"
date: 2026-11-23 14:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - ai
  - testing
permalink: "2026/11/23/software-engineering-age-of-ai-kent-beck"
---

[Kent Beck: Software Engineering in the Age of AI - Prodacity 2026 - Rise8](https://www.youtube.com/watch?v=F8fBgDCf2Y4)

Beck calls the coding model "the genie" because it grants your wishes, and what you get is never quite what you wanted. His one takeaway is that the claim "the genie is better at coding than humans" is wrong: **the genie is very good at plausible, and plausible is not working.** The rest of the talk is about what a programmer's craft turns into once the typing is free. You keep "working" checkable, you spend the pause between features buying back options, and you measure the mission instead of the output.

No slides have been published for this talk. The two C++ programs below are my own illustrations of the testing point, not code from the talk.

## Case 1: the check items pass

Beck found a 1957 programming book that tells you to ask users for "check items", input/output pairs from their domain, and to make the program match them. That is TDD, decades early. Here is a set of check items for a leap-year function, and the sort of implementation a genie hands back:

```cpp
#include <cstdio>

// The genie's implementation: short, readable, plausible.
bool is_leap(int y) { return y % 4 == 0 && y != 1900; }

int main() {
    struct { int year; bool leap; } check_items[] = {   // the users' input/output pairs
        {2024, true}, {2023, false}, {1900, false}, {2000, true},
    };
    int failed = 0;
    for (auto [year, leap] : check_items)
        if (is_leap(year) != leap) { std::printf("FAIL %d\n", year); ++failed; }
    std::printf("%s\n", failed ? "red" : "green");   // prints green
}
```

It prints `green`. The `y != 1900` is exactly the kind of shortcut Beck warns about: the genie "will do things that subvert the intentions of test cases", such as returning constants or special-casing the inputs it was shown, "just to say, 'Yeah, it works, boss.'" Every example passes and the rule is still wrong.

## Case 2: a property against an oracle — red

Examples alone don't constrain a model that is optimising for green. Check a property over the whole input range against an independent oracle, here `std::chrono::year::is_leap` from C++20:

```cpp
#include <chrono>
#include <cstdio>

bool is_leap(int y) { return y % 4 == 0 && y != 1900; }   // same genie code

int main() {
    // Property: agree with an independent oracle on every year, not on four examples.
    int wrong = 0, first = 0;
    for (int y = 1; y <= 9999; ++y)
        if (is_leap(y) != std::chrono::year{y}.is_leap()) {
            if (!first) first = y;
            ++wrong;
        }
    std::printf("%d wrong years, first is %d\n", wrong, first);   // 74 wrong years, first is 100
}
```

It prints `74 wrong years, first is 100`. That is every century year that isn't a multiple of 400, except the 1900 the genie hard-coded. Beck's recipe for trustworthy software has two parts: **carefully chosen examples and automated tests, plus a foolproofed design** that makes whole classes of bugs impossible. The genie skips the second part unless you push it, so the review stance has to be adversarial: "You made yourself happy, but did you make me happy?" (For the foolproofing half in C++, see [Jody Hagins on interfaces neither humans nor AI can misuse](/2026/10/29/cpp-ai-forcing-us-to-obey-scott-meyers-jody-hagins).)

## Features burn futures

Beck's model of a project's value is **features plus futures**. Futures are the options for what you could change next. Every feature burns some futures: you now owe backwards compatibility, or you rip the feature out and that constrains you too. Ship feature after feature and you reach zero options, the state where you can't fix one bug without breaking two others.

```
  futures
    ^
    |*                 feature, feature, feature ...
    | *_
    |   *__            -> "project 2", "project 3", "project 4"
    |      *___
    |          *_____*   no options left: every change breaks something
    +--------------------------------------------> features
```

Beck's GitHub shows the result: a project, then *project two*, *project three*, *project four*, each restarted when it hit the wall. It used to take a hundred people ten years to reach that state. "Now with AI, I can do this in the privacy of my own office, one person, one week."

## Rest between the notes

The fix is the moment after the genie says "Okay boss, I finished that feature. Want me to implement the next thing?" Beck borrows the (made-up) Pablo Casals line about playing long runs of sixteenth notes: "I rest between the notes." Use that pause to **add futures back** before the next feature:

- refactor what's there and remove duplication;
- make the code easier to read where people will need to read it;
- throw away what you just did and implement it again a different way.

That last item comes from Ward Cunningham. Beck watched him switch off the computer at the end of a day's half-satisfying work. The next morning they rebuilt it in about fifteen minutes, and this time they understood it. Beck's conclusion: good development is a learning process that "throws off software as a side effect". Fully agentic "dark factory" runs skip the pause, and in Beck's experience they "always" go off the rails, entertainingly. You can't wipe the knife while you're cutting, but you do have to wipe it.

The hard part is accounting. Features are visible and everyone asks for them. Nobody writes a spec line saying "and this will be easier to change in the future", so time spent on futures looks like gilding the lily.

## One-shot vs iterative: spec-driven is waterfall again

"Write a spec good enough and the genie will produce software good enough" is, in Beck's words, exactly waterfall. Winston Royce's original paper shows the waterfall diagram and then says it doesn't work, because later decisions feed back into earlier ones. What people remembered was the picture.

| Approach | Fits | Breaks on |
|---|---|---|
| One-shot from a spec | small apps you can regenerate | data migration, continuity, a large install base |
| Iterative: deploy, learn, change | anything long-lived (Beck's graph-database VM) | needs the discipline of the pause |
| Formal methods (Beck tried Lean with the genie) | proving properties of a model | still one-shot when the spec changes; gap from model to C/C++/ARM64 code |

Beck says there are times for both. But for systems with real users you are better off assuming iteration from the start. (This blog's [spec-driven development post](/2026/05/24/spec-driven-development-openspec-opencode) is the optimistic side of that argument.)

## Effort → output → outcome → mission

Beck closes with a chain he refined while listening to the opening keynote:

| Stage | Example | Easy to measure? |
|---|---|---|
| Effort | tokens spent, genies spun up | yes |
| Output | 200,000 lines of code, PR count | yes |
| Outcome | users' behaviour changes | with telemetry |
| Mission | the shared goal moves forward | hard; often bursty, visible only in a crisis |

The genie makes the first two nearly free, which is why they look like productivity. But **200,000 lines is not ten times as valuable as 20,000**. The earlier in the chain you measure, the harder Goodhart's law bites. Beck goes further than Goodhart: people don't just stop learning from a gamed measure, they "twist the entire system out of shape" to improve it. The case 1 genie did the same thing to the check items.

## Summary

| Practice | What the genie does by default | What you add |
|---|---|---|
| Testing | passes the examples it was shown | properties, oracles, adversarial review |
| Design | takes shortcuts | foolproofing: make bug classes impossible |
| Pacing | "next feature, boss?" | rest between features and buy back futures |
| Process | one-shot from a spec | iterate on deployed software |
| Measurement | maximises output | measure as close to the mission as you can |

- Treat genie output as plausible until a check it can't game says otherwise.
- Example tests are necessary but not enough. Add a property or an oracle the model never saw.
- A project's value is features plus futures. Spend the pause after each feature adding futures back.
- Spec-driven one-shotting is waterfall with a new coat. Long-lived systems need iteration.
- Lines of code and PR counts measure effort and output, never mission.
