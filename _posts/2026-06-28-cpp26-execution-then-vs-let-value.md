---
layout: single
title: "C++26 std::execution: then vs let_value, and the Full Algorithm Catalog"
date: 2026-06-28 10:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - asynchrony
permalink: "2026/06/28/cpp26-execution-then-vs-let-value"
---

C++26 finally ships [`std::execution`](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html) (P2300) — the sender/receiver framework for asynchronous and parallel programming. Two of its algorithms get confused constantly: `then` and `let_value`. They look almost identical at the call site, but one is `transform` (a.k.a. `map`) and the other is monadic `bind` (a.k.a. `flatMap`). Getting the distinction wrong is the single most common mistake when people start composing senders.

This post catalogs **every** algorithm in the library, drills into `then` vs `let_value`, and gives a fresh (mid-2026) read on implementation status across the major standard libraries and stdexec. The code uses the `stdexec::` namespace from NVIDIA's reference implementation, which mirrors the standard `std::execution::` names one-to-one.

## The complete algorithm catalog

The library splits cleanly into **factories** (make a sender from non-senders), **adaptors** (take a sender, return a sender — these pipe), and **consumers** (take a sender, run it / return a result).

### Sender factories

| Function | Purpose |
|----------|---------|
| `stdexec::schedule(sch)` | The root sender of a scheduler; completes on that scheduler's execution resource |
| `stdexec::just(vs...)` | Completes synchronously on the value channel with `vs...` |
| `stdexec::just_error(e)` | Completes on the error channel with `e` |
| `stdexec::just_stopped()` | Completes on the stopped (cancellation) channel |
| `stdexec::read_env(q)` | Reads a value (e.g. the stop token or current scheduler) out of the receiver's environment |

### Sender adaptors, grouped by channel

The adaptors fall into a clean grid. Three of the groups each handle exactly one of the completion channels — **value**, **error**, **cancellation (stopped)** — and within each group there's a transform form (`return a value`) and a bind form (`return a sender`). The rest are channel-agnostic: they're about *where* work runs or how senders are *combined*.

**Value channel** — operate on a successful result:

| Function | Purpose |
|----------|---------|
| `stdexec::then(s, f)` | Call `f` with the values; the **value** it returns becomes the new result (transform) |
| `stdexec::let_value(s, f)` | Call `f` with the values; `f` returns a **sender** that is then run (bind) |

**Error channel** — operate on a failure:

| Function | Purpose |
|----------|---------|
| `stdexec::upon_error(s, f)` | Call `f` with the error; its **value** becomes a value-channel result (transform/recover) |
| `stdexec::let_error(s, f)` | Call `f` with the error; `f` returns a **sender** (bind — async recovery/retry) |

**Cancellation (stopped) channel** — operate on cancellation:

| Function | Purpose |
|----------|---------|
| `stdexec::upon_stopped(s, f)` | Call `f` when stopped; its **value** becomes a value-channel result (transform) |
| `stdexec::let_stopped(s, f)` | Call `f` when stopped; `f` returns a **sender** (bind) |
| `stdexec::stopped_as_optional(s)` | Translate stopped into a value: `T`/stopped → `optional<T>` |
| `stdexec::stopped_as_error(s, e)` | Translate the stopped channel into an error completion |

**Scheduling / execution transitions** — channel-agnostic, control *where* work runs:

| Function | Purpose |
|----------|---------|
| `stdexec::starts_on(sch, s)` | Start `s` on `sch`'s resource (transition *in*) |
| `stdexec::continues_on(s, sch)` | Move the completion of `s` onto `sch` (transition *out*) — the renamed `transfer` |
| `stdexec::on(sch, s)` | Composite: start on `sch`, run `s`, then return to wherever you came from |
| `stdexec::schedule_from(sch, s)` | Low-level primitive behind `continues_on`; rarely called directly |

**Combining / structural** — channel-agnostic, shape multiple senders or completions:

| Function | Purpose |
|----------|---------|
| `stdexec::when_all(ss...)` | Complete when **all** input senders complete; concatenates their values |
| `stdexec::when_all_with_variant(ss...)` | Like `when_all`, but each input's result is wrapped in a variant |
| `stdexec::into_variant(s)` | Collapse a sender's multiple possible value completions into one `variant<tuple<...>>` |
| `stdexec::bulk(s, shape, f)` | Invoke `f(i, vs...)` for each index `i` in `[0, shape)` |
| `stdexec::split(s)` | Turn a single-shot sender into a multi-shot one that many consumers can observe |

The channel grid at a glance:

| Channel | Transform (`-> value`) | Bind (`-> sender`) | Translate |
|---------|------------------------|--------------------|-----------|
| **value** | `then` | `let_value` | — |
| **error** | `upon_error` | `let_error` | — |
| **stopped** | `upon_stopped` | `let_stopped` | `stopped_as_optional`, `stopped_as_error` |

### Sender consumers

| Function | Purpose |
|----------|---------|
| `stdexec::sync_wait(s)` | Block the calling thread until `s` completes; return `optional<tuple<...>>` (empty on stopped, throws on error) |
| `stdexec::sync_wait_with_variant(s)` | `sync_wait` for senders with multiple value completion signatures |

> **A moving target:** the eager consumers `start_detached` and `ensure_started` were **removed** from P2300 before C++26 over lifetime-safety concerns, and replaced by the structured **async scope** facilities (`spawn`, `spawn_future` against a `counting_scope`). stdexec still ships `start_detached`/`ensure_started` for convenience, but treat them as legacy. This is exactly the kind of thing that shifts paper-to-paper — verify against the latest draft.

## `then` vs `let_value`: transform vs bind

Here is the whole distinction in one line:

- **`then`**: your function returns a **value**. → `T -> U`
- **`let_value`**: your function returns a **sender**. → `T -> sender<U>`

`then` is `transform`/`map`. `let_value` is monadic `bind`/`flatMap`. If your callback needs to launch *more* async work whose shape depends on the incoming value, you need `let_value`; `then` can only compute a plain value synchronously inside the callback.

```cpp
// then: the lambda returns an int — a value.
auto a = stdexec::just(2)
       | stdexec::then([](int x) { return x * 21; });   // completes with 42

// let_value: the lambda returns a *sender*.
auto b = stdexec::just(2)
       | stdexec::let_value([](int x) {                 // x is kept alive...
             return stdexec::just(x * 21);              // ...and we hand back a sender
         });                                            // completes with 42
```

Both produce `42`, so why bother? Because of what each *enables*.

### 1. Dynamic, value-dependent async continuations

This is the headline use case. You don't know which async operation to run until you've seen the previous result.

```cpp
stdexec::sender auto fetch_user(int id);            // returns sender<User>
stdexec::sender auto fetch_orders(User const&);     // returns sender<Orders>

auto pipeline =
      fetch_user(7)
    | stdexec::let_value([](User const& u) {        // pick the next async op
          return fetch_orders(u);                   // based on the value we got
      });
// pipeline is a sender<Orders>
```

You *cannot* express this with `then`. `then`'s callback would have to return a `sender<Orders>` as a plain value, and the framework would hand you back a `sender<sender<Orders>>` — a nested sender that never actually runs the inner work. `let_value` is precisely the "unwrap one level / flatten" operation.

### 2. Lifetime of the argument

`let_value` stores the value it received inside the **operation state** and keeps it alive for the entire duration of the sender the callback returns. The callback receives it by **reference**, so you can safely capture a reference to it in the returned sender.

```cpp
auto p = stdexec::just(std::string("payload"))
       | stdexec::let_value([](std::string& data) {     // note: by reference
             // `data` lives until the inner sender completes
             return write_async(data)
                  | stdexec::then([&] { return data.size(); });
         });
```

With `then`, the argument is gone the moment the callback returns — there is no inner sender whose lifetime it could be tied to.

### 3. Error/stopped propagation is identical in spirit

`then` / `let_value` operate on the **value** channel and pass error/stopped through untouched. The variants line up one-to-one:

| Channel | "return a value" | "return a sender" |
|---------|------------------|-------------------|
| value | `then` | `let_value` |
| error | `upon_error` | `let_error` |
| stopped | `upon_stopped` | `let_stopped` |

A classic use of `let_error` is async recovery — retry, fall back to a cache, etc. — which inherently needs to launch a new operation, so the sender-returning form is required:

```cpp
auto robust =
      fetch_from_network()
    | stdexec::let_error([](std::error_code) {
          return fetch_from_cache();        // recover with another async op
      });
```

### When to reach for which

- Use **`then`** when the callback is a pure, synchronous transformation of the value. It's lighter — no nested operation state, no extra connect.
- Use **`let_value`** when the next step is itself asynchronous, or when its shape depends on the incoming value, or when you need the argument to stay alive across a subsequent async step.

A quick smell test: *if your `then` lambda is about to return a sender, you wanted `let_value`.*

## Implementation status (fresh, mid-2026)

This genuinely changes month to month, so check the trackers rather than trusting any blog (including this one). The shape of things as of **June 2026**:

**P2300 / the standard.** `std::execution` was accepted into C++26; the standard hit feature freeze in 2025 with ISO publication expected late 2026. The wording reference is [P2300R10](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html). Note that the async-scope facilities and a few algorithm renames/removals (like `transfer`→`continues_on`, and the removal of `start_detached`/`ensure_started`) landed via follow-on papers, so the algorithm set is slightly different from older R5-era tutorials.

**NVIDIA stdexec — the reference implementation.** This is what you should actually build against today. It's [header-only, dependency-free, and works across GCC, Clang, and MSVC](https://github.com/NVIDIA/stdexec), tracks the paper closely, and is the de-facto way to use senders in production right now. Standard-library shipping vehicles are still catching up to it.

**libstdc++ (GCC).** Senders are arriving as a C++26 (`-std=c++2c`) preview in the GCC 16 timeframe, but it is incomplete and experimental — not the full algorithm set, and not something to depend on yet. Authoritative source: the [libstdc++ status page](https://gcc.gnu.org/onlinedocs/libstdc++/manual/status.html).

**libc++ (Clang).** Also experimental/partial under `-std=c++2c`; the implementation is being grown in the open and is not complete. A big part of that work lives in the **[Beman.Execution](https://github.com/bemanproject/execution)** project — an independent P2300R10 implementation (GCC 14+, Clang 19+, MSVC, C++23 minimum) explicitly described as *"under development and not yet ready for production use,"* and a natural feeder for libc++. Track the [libc++ status pages](https://libcxx.llvm.org/Status/Cxx26.html) for the canonical state.

**MSVC.** Microsoft has been actively implementing `std::execution` in their STL; recent Visual Studio 2026 toolsets expose it under C++ latest, though as with the others, coverage is partial and evolving.

**The honest summary:** if you want to *use* senders today, use **stdexec**. The standard-library implementations (libstdc++, libc++, MSVC STL) are all real but incomplete in mid-2026, converging on the same API. Pin a stdexec version, alias `namespace ex = stdexec;` if you like the brevity, and you'll be able to swap to `std::execution` with minimal churn once your toolchain ships it.

## Takeaways

- `then` = transform (returns a value); `let_value` = bind (returns a sender). The same triple exists on the error (`upon_error`/`let_error`) and stopped (`upon_stopped`/`let_stopped`) channels.
- Reach for `let_value` whenever the next step is asynchronous or value-dependent, or you need the argument to outlive the callback.
- The `stdexec::` names mirror the standard `std::execution::` names one-to-one, so code written today ports cleanly.
- For real code today, build on **stdexec**; standard-library support is partial and moving — check the libstdc++, libc++, and cppreference trackers rather than relying on a snapshot.

---

**Sources**

- [P2300R10: `std::execution`](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html)
- [NVIDIA/stdexec — reference implementation](https://github.com/NVIDIA/stdexec)
- [stdexec User's Guide](https://nvidia.github.io/stdexec/user/index.html)
- [Beman.Execution — P2300 implementation](https://github.com/bemanproject/execution)
- [libstdc++ implementation status](https://gcc.gnu.org/onlinedocs/libstdc++/manual/status.html)
- [libc++ C++26 status](https://libcxx.llvm.org/Status/Cxx26.html)
- [Compiler support for C++26 — cppreference](https://en.cppreference.com/w/cpp/compiler_support/26)
- [Senders/Receivers: An Introduction — ACCU Overload](https://accu.org/journals/overload/32/184/teodorescu/)
