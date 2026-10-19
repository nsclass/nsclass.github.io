---
layout: single
title: "C++ - An Algorithm Library Built From Four Stage Shapes (John Bandela, C++Now 2026)"
date: 2026-10-18 14:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - api-design
  - metaprogramming
permalink: "2026/10/18/cpp-spl-four-stage-shapes-john-bandela"
---

[SPL - Open Source, Constexpr Library for Composing Algorithms - John Bandela - C++Now 2026](https://www.youtube.com/watch?v=96AGjm3uwko) ([slides](https://github.com/boostcon/cppnow_presentations_2026/blob/main/Presentations/SPL.pdf))

Give up the one thing a pipeline stage seems to need — the ability to *return* its result — and have it call the next stage instead. [SPL](https://github.com/jbandela/cpp-from-the-sky-down/tree/main/spl) shows what you get back: an algorithm library that falls out of four stage shapes, composable, variadic, allocation-free, and usable in a constant expression. Every listing below was compiled and run against `spl.h` from the repo with Apple clang 21 at `-std=c++23`.

## `apply` type-checks the pipeline before it runs

Each stage declares how it consumes input and how it produces output: `incremental` (one element at a time) or `complete` (the value as a whole), and a stage's input style must match the previous stage's output style. Given `std::vector<int> v{1, 2, 3}` and `triple = [](int n) { return n * 3; }`, which of these `spl::apply(v, …)` calls compile?

| Stages passed to `apply` | Compiles? | Why |
|---|---|---|
| `max()` | yes | `complete` input converts implicitly to `incremental`; `max` ends `complete` |
| `transform(triple)` | **no** | last stage is `incremental` — `apply` has no single value to return |
| `transform(triple), to_vector()` | yes | `to_vector` is the `incremental → complete` cap |
| `transform(triple), sort()` | **no** | `transform` outputs `incremental`, `sort` demands `complete` |
| `… to_vector(), sort()` | yes | `to_vector` re-wholes the stream, so `sort` can take it |
| `… sort(), filter_duplicates(), accumulate(…)` | yes | you may cross back and forth as often as you like |

Two rules do all the work: **`complete` converts implicitly to `incremental`, never the other way, and the last stage must be `complete`.** Note the cost of enforcing this with types rather than concepts: a mismatch produces library-internal errors like `no member named 'process_incremental' in 'spl::detail::end_stage'`, not a `static_assert` telling you which stage is wrong.

## Four shapes cover every stage

Those two styles give four input→output combinations, and each has one helper that spares you writing a stage class by hand:

| Input → output | Examples | Write your own with |
|---|---|---|
| incremental → incremental | `transform`, `filter`, `take` | `flat_map` |
| incremental → complete | `sum`, `count`, `to_vector`, `any_of` | `accumulate_in_place[_with_init]` |
| complete → complete | `sort`, `stable_sort`, `unique`, `nth_element` | `transform_complete` |
| complete → incremental | iterating a range (implicit) | `generator` + ADL hooks |

(Table adapted from the slides.) The two easy ones are one-liners — `spl::transform_complete([](std::string s) { std::reverse(s.begin(), s.end()); return s; })` reverses a whole value, and `spl::accumulate_in_place(1, [](int& acc, int v) { acc *= v; })` is `product`. The interesting two are these:

```cpp
#include <cstddef>
#include <iostream>
#include <vector>
#include "spl.h"

// incremental -> incremental: call out() zero or more times per input element.
constexpr auto repeat_each(size_t n) {
  return spl::flat_map([n]<typename Out>(Out&& out, auto&& x) {
    if constexpr (spl::impl::calculate_type_v<Out>) {
      return out(x);                       // decltype-only: names the output type
    } else {
      for (size_t i = 0; i < n; ++i) out(x);
      return true;                         // false stops the pipeline
    }
  });
}

// complete -> incremental: a generator pushes one element per call until it stops.
constexpr auto fib(size_t count) {
  return spl::generator([count, a = 0, b = 1, i = size_t{0}](auto&& out) mutable {
    if constexpr (spl::impl::calculate_type_v<decltype(out)>) {
      return out(a);
    } else {
      if (i++ == count) return false;
      out(a);
      auto next = a + b;
      a = b;
      b = next;
      return true;
    }
  });
}

int main() {
  for (int x : spl::apply(std::vector{1, 2, 3}, repeat_each(3), spl::to_vector()))
    std::cout << x << ' ';
  std::cout << "\n";                       // 1 1 1 2 2 2 3 3 3

  for (int x : spl::apply(fib(10), spl::to_vector())) std::cout << x << ' ';
  std::cout << "\n";                       // 0 1 1 2 3 5 8 13 21 34
}
```

`repeat_each` is `filter`, `transform`, and `flatten` in one shape: **zero-or-more outputs per input is the general case, and the familiar stages are special cases of it.** A `generator` is just a lambda tagged with a type so SPL recognizes it; `fib` keeps its state in the capture, which works precisely because each element is pushed exactly once.

## Pushing costs you the return type — `calculate_type_v` buys it back

That `if constexpr` branch is the price of the whole design. A stage that returns a value tells the compiler its output type for free — `decltype(f(x))`. A stage that *pushes* returns nothing, so the type must come from somewhere else.

So SPL invokes your callable twice. Once in an unevaluated `decltype` context with a sentinel outputter for which `calculate_type_v` is `true`, and whatever you pass to `out` there becomes the stage's `output_types`; then at run time with the real outputter and `calculate_type_v` `false`. **The probe branch never executes, so it may contain code that would be undefined behaviour if it did** — only the types it mentions matter. That is why `fib`'s probe returns `out(a)` without touching the recurrence, and why the library's own range hook can write `auto&& v = *r.begin();` on a possibly empty range.

Because nothing in the chain allocates or escapes, a whole pipeline is a constant expression:

```cpp
static_assert(spl::apply(std::array{1, 2, 3, 4, 5},
                         spl::filter([](int n) { return n % 2; }),
                         spl::transform([](int n) { return n * n; }),
                         spl::sum()) == 35);
```

Bandela turns this into a debugging technique: run a suspect pipeline in a `constexpr` context and the compiler refuses to compile a dangling reference.

## `compose` makes one stage out of many

`compose` bottles a run of stages into a single stage, which `apply` then treats exactly as if you had written them out. A composed stage is a first-class value you can name, return from a function, and reuse — `spl::compose(spl::iota(size_t{1}), spl::transform([](size_t i) { return i * i; }))` is an infinite stream of perfect squares. Nesting them gets interesting:

```cpp
#include <cstddef>
#include <iostream>
#include <tuple>
#include <vector>
#include "spl.h"

// zip_result + flatten is a nested loop; compose names the pattern once.
constexpr auto pythagorean_triples() {
  auto zip_flat = [](auto f) {
    return spl::compose(spl::zip_result(f), spl::flatten());
  };
  return spl::compose(
      spl::iota(size_t{1}),                                             // c = 1, 2, 3, ...
      zip_flat([](size_t c) { return spl::iota(size_t{1}, c + 1); }),    // a = 1..c
      zip_flat([](size_t c, size_t a) { return spl::iota(a, c + 1); }),  // b = a..c
      spl::filter([](size_t c, size_t a, size_t b) { return a * a + b * b == c * c; }),
      spl::swizzle<1, 2, 0>());                                         // (c,a,b) -> (a,b,c)
}

int main() {
  spl::apply(pythagorean_triples(), spl::take(4),
             spl::for_each([](size_t a, size_t b, size_t c) {
               std::cout << a << "," << b << "," << c << "  ";
             }));
  std::cout << "\n";                      // 3,4,5  6,8,10  5,12,13  9,12,15

  std::vector<std::tuple<size_t, size_t, size_t>> v = spl::apply(
      pythagorean_triples(), spl::take(4), spl::make_tuple(), spl::to_vector());
  std::cout << v.size() << " collected\n";
}
```

`pythagorean_triples()` is an infinite, lazily evaluated triple loop with no iterators, no coroutines, and no allocation — and the same composed value feeds both a `for_each` and a `to_vector`.

One correction: slide 49 composes over a member container with `spl::compose(std::cref(amounts), …)`, which **does not compile** — `std::reference_wrapper` is not a range, so the output hook finds no overload. `std::span(amounts)` keeps the slide's intent of borrowing explicitly. A plain lvalue container works too but silently *copies* it: editing the container in place afterwards, the `span` version sees the change and the by-value version does not.

## The McIlroy challenge, end to end

The talk opens with Bentley's *Programming Pearls* column: print the `k` most common words in a file, in decreasing frequency. Knuth answered with a literate-programming tour de force; Doug McIlroy answered with six shell commands. Here is the pipeline version, assembled from four named stages:

```cpp
#include <cctype>
#include <cstddef>
#include <functional>
#include <iostream>
#include <string>
#include <string_view>
#include "spl.h"

auto read_lines() {
  return spl::transform_complete([](std::istream& is) {
    return spl::generator([&is, line = std::string()](auto&& output) mutable {
      auto emit = [&] { return output(std::string_view(line)); };
      if constexpr (spl::impl::calculate_type_v<decltype(output)>) {
        return emit();
      } else {
        if (std::getline(is, line)) { emit(); return true; }
        return false;                      // one reused buffer, no allocation per line
      }
    });
  });
}

auto split_words() {
  return spl::compose(
      spl::transform([](std::string_view line) {         // chunk WITHIN each line
        return spl::apply(line,
            spl::chunk_by(
                [](unsigned char prev, unsigned char c) {
                  return std::isalpha(prev) == std::isalpha(c);
                },
                spl::tee(spl::first_or_null(), spl::count()),  // (char*, length)
                spl::construct_complete<std::string_view>()),  // string_view's ctor exactly
            spl::filter([](std::string_view s) {
              return !s.empty() && std::isalpha((unsigned char)s.front());
            }),
            spl::to_vector());
      }),
      spl::flatten());                                   // then merge the per-line results
}

auto lower_case() {
  return spl::transform([](std::string_view s) {
    return spl::apply(s,
        spl::transform([](char c) { return (char)std::tolower((unsigned char)c); }),
        spl::to_string_reserve(s.size()));
  });
}

auto unique_counts() {
  return spl::compose(spl::group_by(std::identity{}, spl::count()),
                      spl::swizzle<1, 0>(),              // (word, n) -> (n, word)
                      spl::make_pair());
}

int main(int argc, char** argv) {
  size_t k = argc > 1 ? std::stoul(argv[1]) : 5;
  spl::apply(std::cin, read_lines(), split_words(), lower_case(), unique_counts(),
      spl::to_vector(),
      spl::partial_sort(k, std::greater<>()),            // safe even if k > size
      spl::take(k),
      spl::expand_tuple(),
      spl::for_each([](size_t n, const auto& s) { std::cout << n << " " << s << "\n"; }));
}
```

Run on its own source alongside McIlroy's shell pipeline, the two agree line for line:

```
$ ./wordcount 7 < wordcount.cpp
30 spl / 17 std / 14 return / 10 string / 9 s / 8 line / 8 char

$ tr -cs A-Za-z '\n' < wordcount.cpp | tr A-Z a-z | grep -v '^$' |
    sort | uniq -c | sort -rn | sed 7q
30 spl / 17 std / 14 return / 10 string / 9 s / 8 line / 8 char
```

The two agree on every word, not just the leaders: diffing the complete maps over all 106 distinct words in that file shows no difference at all.

**That required fixing the deck.** Slide 58 puts `spl::flatten()` *first* and chunks the resulting character stream:

```cpp
spl::compose(spl::flatten(), spl::chunk_by(/* same args */), spl::filter(/* … */))
```

Flattening erases the line boundaries, so a word ending one line and a word starting the next have the same alpha-ness and `chunk_by` merges them into one chunk: `first_or_null` points into line N while `count` runs into line N+1, and `construct_complete<std::string_view>` builds a view that reads past the end of the buffer. On the two-line input `{"auto", "bar"}` the deck's splitter yields a single 7-character `[auto ba]` instead of `[auto] [bar]`. With `read_lines`' reused buffer the overread turns into visible garbage — a `std::map`-backed `group_by` ends up holding two distinct keys that both print as `auto`. Chunking inside each line and flattening afterwards costs one small vector per line and makes the output exact.

Three details carry the corrected pipeline. **`tee`, `group_by`, and `chunk_by` widen the pipeline into parallel argument streams instead of packing values into tuples** — which is why `construct_complete<std::string_view>()` receives `(char*, size_t)` as two arguments matching a `string_view` constructor exactly, and why `swizzle<1, 0>()` reorders `(word, count)` into `(count, word)` without a `std::get`. Second, `read_lines` reuses one buffer and emits `string_view`s into it, so nothing allocates per line. Third, `partial_sort(k, …)` is well defined when `k` exceeds the element count, unlike `std::partial_sort` — which matters when an upstream `filter` decides how many elements there are. `max`, `first`, and `last` return `std::optional<T>` for the same reason.

## Summary

| Shape | Helper | What it can do |
|---|---|---|
| incremental → incremental | `flat_map` | 0..n outputs per input; subsumes transform, filter, flatten |
| incremental → complete | `accumulate_in_place` | fold a stream into one value |
| complete → complete | `transform_complete` | rewrite a whole value |
| complete → incremental | `generator` | turn a source into a stream, statefully |

- The library's whole surface is those four shapes plus `compose`; `sum`, `to_vector`, `take`, and `group_by` are each one of them with an argument filled in.
- Pushing instead of returning costs you the return type, and `calculate_type_v` buys it back: the stage is probed once for types in an unevaluated context, then called for real.
- Argument streams instead of tuples is the quiet win: `tee`, `zip`, and `group_by` widen the pipeline and downstream lambdas just grow a parameter.
- The composition rules are statically enforced, but a mismatch yields raw template errors rather than a `static_assert` naming the bad stage.
- Two deck bugs to know: slide 49's `std::cref` spelling does not compile (use `std::span`), and slide 58's `flatten()`-then-`chunk_by` word splitter reads past the end of the line buffer. Chunk per line, then flatten.
