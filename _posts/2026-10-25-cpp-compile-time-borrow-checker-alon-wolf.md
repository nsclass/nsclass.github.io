---
layout: single
title: "C++ - A Borrow Checker in Constexpr: Stateful Metaprogramming Records the IR (Alon Wolf, C++Now 2026)"
date: 2026-10-25 14:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - metaprogramming
  - memory
  - static-analysis
permalink: "2026/10/25/cpp-compile-time-borrow-checker-alon-wolf"
---

[Compile-Time Borrow Checker with Stateful Metaprogramming - Alon Wolf - C++Now 2026](https://www.youtube.com/watch?v=3hL8mh0K8-I) ([slides](https://github.com/boostcon/cppnow_presentations_2026/blob/main/Presentations/Compile-Time_Borrow_Checker_with_Stateful_Metaprogramming.pdf))

Rust's NLL borrow checker is just a few dataflow passes over an IR. Writing those passes in C++ is easy: they are ordinary `constexpr` functions. The hard part is getting an IR of your own code at compile time. **Friend injection gives the compiler memory you can write to**, and with that you can record every expression as it is compiled and borrow-check the result in a `static_assert`.

## The friend database: write once, read anywhere

```cpp
// db.hpp — the "friend database"
#pragma once

template <auto Key>
struct detector {
    friend constexpr auto injected(detector<Key>);            // declaration only: no body, no return type
};

template <auto Key, auto Value>
struct injector {
    friend constexpr auto injected(detector<Key>) { return Value; }  // instantiating this defines it
};
```

```cpp
#include "db.hpp"
#include <print>

template <auto Key>                                          // must be a template: a non-dependent
constexpr bool has_definition =                              // requires-expression is a hard error
    requires(detector<Key> d) { injected(d); };

static_assert(!has_definition<0>);                           // CHECK(0): declared, not defined
template struct injector<0, 42>;                             // INSERT(0, 42)
static_assert(injected(detector<0>{}) == 42);                // GET(0)
// template struct injector<0, 43>;                          // error: redefinition of 'injected'

int main() {
    std::println("GET(0) = {}", injected(detector<0>{}));    // prints GET(0) = 42
}
```

`detector<0>` declares a free function `injected(detector<0>)` with a deduced return type. Nothing defines it until `injector<0, 42>` is instantiated, and then the definition shows up in the enclosing namespace. That gives three operations: CHECK (is it defined yet?), INSERT (instantiate an injector), and GET (call it). Inserting a second value for the same key is a redefinition, so each key can be written only once.

## Templates cache; a fresh lambda breaks the cache

Once a template has been instantiated, the compiler reuses that instantiation, so a CHECK that ran before an INSERT keeps returning the old answer:

```cpp
#include "db.hpp"
#include <print>

template <auto Key, auto... eval>                             // CHECK(Key); eval only makes it unique
constexpr bool has_definition = requires(detector<Key> d) { injected(d); };

template <auto Key, bool V = has_definition<Key>>             // has_definition<0> every time
constexpr bool has_key_cached() { return V; }

template <auto Key, auto eval = [] {}, bool V = has_definition<Key, eval>>
constexpr bool has_key() { return V; }                        // fresh lambda, threaded through

int main() {
    constexpr bool cached_before = has_key_cached<0>();
    constexpr bool fresh_before = has_key<0>();
    (void)injector<0, 42>{};                                  // INSERT(0, 42)
    constexpr bool cached_after = has_key_cached<0>();        // reuses has_definition<0>: stale
    constexpr bool fresh_after = has_key<0>();

    std::println("cached: {} -> {}", cached_before, cached_after);  // prints cached: false -> false
    std::println("eval:   {} -> {}", fresh_before, fresh_after);    // prints eval:   false -> true
}
```

Each `[]{}` is a new closure type, so a default `eval = []{}` makes every call a new instantiation. **The lambda has to reach the template that actually caches.** If you add `eval` to `has_key` but still read `has_definition<Key>`, it prints `false -> false` too. All three compilers agree: Apple Clang 21, GCC 15.1 and MSVC 19.latest print the output above.

## Versions turn write-once into an append-only list

Add a version number to the key. To read, probe versions 0, 1, 2, … until one has no definition. To write, define the first free version. The talk wraps this in a `meta_state` whose default key is itself a lambda:

```cpp
// meta_state.hpp — a versioned friend DB: each key holds an append-only list
#pragma once
#include <array>
#include <utility>

template <auto Key, int Version>
struct slot {
    friend constexpr auto value_of(slot);                     // declared, defined later by append
};

template <auto Key, int Version, auto Value>
struct append_at {
    friend constexpr auto value_of(slot<Key, Version>) { return Value; }
};

template <auto Key, auto eval, int V = 0>
consteval int size() {                                        // first version with no definition
    if constexpr (requires { value_of(slot<Key, V>{}); })
        return size<Key, eval, V + 1>();
    else
        return V;
}

template <auto Key = [] {}>
struct meta_state {
    template <auto Value, auto eval = [] {}>
    static consteval int push() {                             // UPDATE: write at version size()
        constexpr int n = size<Key, eval>();                  // read once: a second size<Key, eval>() is cached
        (void)append_at<Key, n, Value>{};
        return n;
    }

    template <auto eval = [] {}>
    static consteval auto all() {                             // ALL: every value, in order
        return []<int... I>(std::integer_sequence<int, I...>) {
            return std::array{value_of(slot<Key, I>{})...};
        }(std::make_integer_sequence<int, size<Key, eval>()>{});
    }
};
```

```cpp
#include "meta_state.hpp"
#include <print>

using M = meta_state<>;

int main() {
    constexpr int i0 = M::push<10>();
    constexpr int i1 = M::push<20>();
    constexpr int i2 = M::push<30>();
    constexpr auto values = M::all();

    static_assert(values == std::array{10, 20, 30});          // the compiler remembered
    std::println("{} {} {} -> {}", i0, i1, i2, values);       // prints 0 1 2 -> [10, 20, 30]
}
```

The comment on `push` marks a bug I hit while writing this. My first version returned `size<Key, eval>() - 1` after the append. That is the same instantiation as the line above it, so it returned the stale size minus one, and the indices came out `-1 0 1`. Keeping state in the compiler means you are always thinking about the template cache.

## Record the IR, then borrow-check it in `constexpr`

Now each "statement" pushes an instruction onto a recorder, and the checker is plain `consteval` code. It runs three NLL passes, the same ones as slides 99–105:

```cpp
// borrowck.hpp — a constexpr NLL checker for a straight-line IR
#pragma once
#include <array>
#include <cstddef>

enum class kind { make, ref, mut, copy, use };

struct inst {                       // instruction i defines variable i (like MIR's _1, _2, ...)
    kind k;
    int arg = -1;                   // ref/mut: borrowed var; copy: source ref; use: used var
};

template <std::size_t N>
consteval int borrow_check(const std::array<inst, N>& ir) {
    // 1. liveness: a variable is live from after its creation up to its last use
    std::array<std::array<bool, N>, N> live{};                // live[point][var]
    for (std::size_t p = 0; p < N; ++p)
        if (ir[p].k == kind::use)
            for (int q = p; q > ir[p].arg; --q) live[q][ir[p].arg] = true;

    // 2. region inference: `dst = copy(src)` means `dst ⊂ `src, applied to a fixed point
    for (bool changed = true; changed;) {
        changed = false;
        for (auto& point : live)
            for (std::size_t v = 0; v < N; ++v)
                if (ir[v].k == kind::copy && point[v] && !point[ir[v].arg]) {
                    point[ir[v].arg] = true;
                    changed = true;
                }
    }

    // 3. loans: two live loans of the same variable conflict if either is mutable
    for (std::size_t p = 0; p < N; ++p)
        for (std::size_t a = 0; a < N; ++a)
            for (std::size_t b = a + 1; b < N; ++b)
                if ((ir[a].k == kind::ref || ir[a].k == kind::mut) &&
                    (ir[b].k == kind::ref || ir[b].k == kind::mut) &&
                    ir[a].arg == ir[b].arg && live[p][a] && live[p][b] &&
                    (ir[a].k == kind::mut || ir[b].k == kind::mut))
                    return p;                                 // error at this point
    return -1;                                                // borrow check passed
}
```

```cpp
#include "meta_state.hpp"
#include "borrowck.hpp"
#include <print>

using Ok = meta_state<1>;                                     // one recorder per "function"
using Bad = meta_state<2>;

int main() {
    {   // int* r = &vec[0]; print(*r); vec.push_back(4);
        constexpr int vec = Ok::push<inst{kind::make}>();
        constexpr int r   = Ok::push<inst{kind::ref, vec}>();
        static_assert(Ok::push<inst{kind::use, r}>() > 0);    // last use of r
        constexpr int t   = Ok::push<inst{kind::mut, vec}>(); // push_back borrows vec mutably
        static_assert(Ok::push<inst{kind::use, t}>() > 0);
    }
    {   // int* r = &vec[0]; int* r2 = r; vec.push_back(4); print(*r2);
        constexpr int vec = Bad::push<inst{kind::make}>();
        constexpr int r   = Bad::push<inst{kind::ref, vec}>();
        constexpr int r2  = Bad::push<inst{kind::copy, r}>(); // `r2 ⊂ `r keeps r's loan alive
        constexpr int t   = Bad::push<inst{kind::mut, vec}>();
        static_assert(Bad::push<inst{kind::use, t}>() > 0);
        static_assert(Bad::push<inst{kind::use, r2}>() > 0);  // r2 used after the mutation
    }

    constexpr int ok = borrow_check(Ok::all());
    constexpr int bad = borrow_check(Bad::all());
    static_assert(ok == -1, "borrow checker failed");
    // static_assert(bad == -1, "borrow checker failed");     // error: static assertion failed
    std::println("ok: {}, bad: conflict at instruction {}", ok, bad);  // prints ok: -1, bad: conflict at instruction 4
}
```

In the first block `r` dies at its last use, before `push_back`. That is **non-lexical lifetimes**: the scope doesn't matter, only the last use does. In the second block `r` is never used directly. Region inference keeps it alive because its copy `r2` is, and that is how the checker finds the conflict at the `push_back` (instruction 4). Disable pass 2 and `bad` silently comes back `-1`. Uncomment the last `static_assert` and Clang reports `static assertion failed due to requirement 'bad == -1': borrow checker failed`. Two portability traps came up here. First, a plain `(void)Bad::push<...>();` worked on Clang, but on GCC 15.1 and MSVC the last two instructions were missing from `all()`. Wrapping every push in a constant-evaluated context (`constexpr int` or `static_assert`, as the talk's recorder does) fixed it on all three. Second, I give each recorder an explicit key.

The real library goes much further: an `exp<T>` proxy records each operator call, `var` records constructors and `.ref()`/`.mut()` borrows, `if_ … scope_ … end_` macros record control flow, and the liveness pass runs over a real CFG with live-in/live-out sets. The [demo](https://godbolt.org/z/hGrnY1jef) shows the generated assembly is identical to the unchecked function.

## C++26 reflection makes the database official

C++26 makes "is this type complete yet?" a sanctioned question. Declare `template <int Key> struct db;`; then CHECK is `is_complete_type(substitute(^^db, {reflect_constant(key)}))` and INSERT is `define_aggregate(...)` on that same specialization. CHECK is now a plain `consteval` function rather than a template, so there's no cache to dodge and no `eval` lambda.

**Slide 113 leaves out one rule:** in final C++26, `define_aggregate` may only run inside a `consteval { ... }` block. GCC 16.2 rejects a direct call with "`define_aggregate` not evaluated from `consteval` block", and so does the P2996 Clang branch. A counter written as three `consteval { push(); }` blocks compiles on both and counts `0 -> 3`. Reflection still can't see function bodies, though, so the recording step stays until some future standard lets you write `get_ir(^^foo)`.

## Summary

| | Rust | C++ (this approach) |
|---|---|---|
| Features & optimizations | More (field paths, graph-based region inference) | Fewer, but can catch up |
| Checker performance | Native code in the compiler | `constexpr`/templates, about as fast as a scripting language |
| Ergonomics | Built into the syntax | Wrappers and macros |
| Enable/disable | Opt out with `unsafe` | Opt in with `push()`/`pop()` |
| Customization | None | Every rule is your code |

(Scorecard adapted from the slides.)

- A lifetime is a **set of points**, and the borrow checker is two rules: the borrowed value must outlive the reference (`'r ⊂ 'vec`), and no `mut` loan may overlap any other loan. That model helps when reviewing C++ even without a tool.
- Friend injection gives you write-once compile-time storage, and versioned keys turn it into a list. Every bug you hit comes from instantiation caching, and `eval = []{}` is the fix, but only if it reaches the template that caches.
- NLL itself is about 40 lines of `consteval` loops: liveness, region inference to a fixed point, and a loan-conflict scan.
- "Technically yes, practically no": compile times and the recording syntax are what stop it today. The same code → IR → `constexpr` analysis pipeline also works for custom validation, design by introspection, or autodiff. The library is [Mitzi](https://github.com/a10nw01f/Mitzi).
- In C++26, use `is_complete_type` + `define_aggregate` inside `consteval { }` blocks instead of friend injection.
