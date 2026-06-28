---
layout: single
title: "C++ - Implementing Control Flow with Sender/Receiver (Steve Downey)"
date: 2026-06-29 10:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - asynchrony
permalink: "2026/06/29/cpp-sender-receiver-control-flow-steve-downey"
---

[Steve Downey - Using the C++ Sender/Receiver Framework: Implement Control Flow for Async Processing](https://www.youtube.com/watch?v=xXncLUD-4bA)

Most introductions to C++26 [`std::execution`](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html) (P2300) stop at "here are the algorithms: `then`, `let_value`, `when_all`." Steve Downey's talk goes one level deeper and asks a more interesting question: **if senders are the new way to express asynchronous work, can you build *all* of structured programming out of them?** Sequence, selection, iteration, recursion — the Böhm–Jacopini building blocks. The answer is yes, and watching how the pieces map onto each other is the best way to actually understand what `let_value` is *for*.

The talk was first given at C++Now 2023; the [slides are on Downey's site](https://sdowney.org/posts/index.php/2024/05/18/slides-from-cnow-2023-async-control-flow/). The code below uses the `stdexec::` namespace from NVIDIA's reference implementation, which mirrors the standard `std::execution::` names.

## The core idea: senders are continuation-passing style

Downey grounds the whole framework in 1970s **continuation-passing style** (Sussman & Steele). Instead of a function *returning* a value, it passes that value forward to a *continuation* — a callback that consumes it. A receiver is exactly that continuation, with three channels:

- **value** — success
- **error** — failure
- **stopped** — cancellation

A sender, then, is a *description* of work that will eventually call one of those channels. The punchline he keeps coming back to: senders are **"three monads in a trench-coat"** — one monad stacked over each channel. And the three monadic operations have names you already know:

| Monad operation | Sender algorithm | What it does |
|-----------------|------------------|--------------|
| `pure` / `return` | `just` | Lift a plain value into a sender |
| `fmap` (functor map) | `then` | Transform the value with a function returning a **value** |
| `bind` (`>>=`) | `let_value` | Feed the value to a function returning a **sender** |

The other property that makes everything work: **senders are lazy**. Composing them builds a description; nothing runs until a consumer like `sync_wait` connects a receiver and starts it. That laziness is what lets you treat control flow as data you assemble before executing.

Downey (a Bloomberg C++ infrastructure engineer) is careful to stress this isn't a strange new invention: CPS dates to a 1975 AI memo, the model is a **delimited continuation**, and his favorite intuition for it is the operating system. When a process makes a `read()` syscall it suspends; when the disk delivers data it resumes. *That suspension is the process's continuation* — delimited not by the whole OS but by the process boundary. A receiver plays the same role for a chain of senders. He also notes the corollary that pays off later in C++26: **coroutines are senders** — the thing a coroutine returns to hand you its eventual value *is* a sender, which is exactly why `std::execution` is the framework a future `std::task` plugs into.

## Sequence: `then`

The simplest control structure — do this, then do that — is just a chain of `then`:

```cpp
stdexec::schedule(sch)
  | stdexec::then([] { return 13; })
  | stdexec::then([](int arg) { return arg + 42; });
// completes with 55
```

Each `then` is a functor map: it takes the value off the value channel, transforms it, and puts the result back. Sequencing is function composition.

## Selection: `let_value` as `if`/`else`

Here's the first place `then` is not enough. To choose *which* branch to run **based on a runtime value**, you need to select among senders — and that's `bind`, i.e. `let_value`:

```cpp
| stdexec::let_value([=](auto tpl) {
      return tst((i > j), seven_sender, eleven_sender);
  });
```

The helper `tst` returns a `variant_sender` holding *either* the left or the right branch. The key insight: the branch is **not** baked statically into the sender graph. `let_value` runs its function at execution time, looks at the value, and only then produces the sender to continue with. A conditional is a runtime choice of continuation — which is the literal definition of monadic bind.

This is the single most important takeaway of the talk: **`then` transforms values; `let_value` chooses futures.** Any time control flow depends on a computed value, you reach for `let_value`.

## Recursion: factorial

Once you have sequence and selection, recursion follows. Factorial is `let_value` recursing on a smaller input, then `then` to fold the result back in:

```cpp
auto fac(int n) -> any_int_sender {
    if (n == 0)
        return stdexec::just(1);
    return stdexec::just(n - 1)
         | stdexec::let_value([](int k) { return fac(k); })   // recurse
         | stdexec::then([n](int k) { return k * n; });       // combine
}
// fac(10) == 3628800
```

Note `any_int_sender` — a type-erased sender. Recursion needs a single concrete return type, and the recursive sender type would otherwise be infinite, so you erase it. (Type erasure has a cost; it's the price of unbounded recursion.)

## Iteration: fold as tail recursion

A loop is tail recursion that threads loop state through `let_value`:

```cpp
// sum 1..9999 by advancing (i, acc) until done, yielding 49995000
```

Each iteration uses `let_value` to inspect the current state, decide whether to continue, and produce either the next iteration's sender or a `just` with the final accumulator. This is the async analogue of a fold — and because each step is a sender, the "loop" can suspend, resume on another scheduler, or be cancelled between iterations.

## Fork/join: `when_all`

Independent work runs concurrently with `when_all`, which completes only when all of its input senders complete and concatenates their values:

```cpp
stdexec::when_all(
    stdexec::on(sched, stdexec::just(0) | stdexec::then(square)),
    stdexec::on(sched, stdexec::just(1) | stdexec::then(square)),
    stdexec::on(sched, stdexec::just(2) | stdexec::then(square))
);
// completes with (0, 1, 4)
```

Downey uses this to turn *tree recursion* into *parallelism* — a naive Fibonacci that forks its two recursive calls with `when_all` and joins them with `then`. The execution order is nondeterministic, but the **result** order is fixed by the structure. `on` reschedules each branch onto the thread pool, so the fork actually runs in parallel. He's gleefully honest that this is a terrible Fibonacci: it's exponential, and spreading it across threads *ruins locality* and runs slower — computing `fib(37)` ate **4.8 GB** on his machine. The point isn't efficiency; it's that the control structure composes and stays correct (valgrind and ASan were happy).

## Backtracking: search with a failure continuation

The most sophisticated example is depth-first search with backtracking. A `search_tree` walks a tree via nested `let_value` calls, threading a **`fail` continuation** through the recursion. If the current node matches, it returns immediately; otherwise it chains "search the left subtree" to "search the right subtree," and the `fail` continuation is what gets invoked when a branch dead-ends — backtracking expressed purely as continuations. This is the moment the CPS framing pays off: backtracking is just *which continuation you call next*.

## The three channels: errors and cancellation

Downey keeps the talk on the value channel on purpose — "from a control point of view there's nothing particularly interesting" about the other two, because they work the same way. But the design lets you **cross channels** like a patch bay:

- An error needn't be an exception — you can just *send* one onto the error channel directly, or throw and have it caught and placed there for you. The error channel lets you abort early and do common error handling at the end of the graph rather than threading it through every step.
- His running example of recovery is reconnection: if you can't reach the server you were told to use, the error can be moved back onto the value channel and the work proceeds — "I'll try the other one." Adapters wire the channels together in both directions.
- **stopped** is strictly cancellation — "I was asked to cancel, and now I'm letting you know I'm done." It's not a pause and shouldn't be repurposed as a value channel. `stopped_as_optional` / `stopped_as_error` translate it when you need to.

Because each channel is its own monad, the same `bind` pattern generalizes: "on error, do X" and "on cancellation, do Y" are `let_error` / `let_stopped` — bind applied to a different channel.

## "Can is not Should"

Downey's closing caveat is worth repeating. Just because you *can* express every control structure as senders doesn't mean you *should*. The framework earns its complexity when you genuinely need **throughput** (overlapping I/O, parallelism) or **interruptibility** (structured cancellation). For straight-line synchronous logic, ordinary code is clearer. Senders are a tool for asynchronous composition, not a replacement for `if` and `for`.

## Takeaways

- Senders are continuation-passing style made composable: a receiver is a continuation with value/error/stopped channels.
- `just` = `pure`, `then` = `fmap`, `let_value` = `bind`. That trio is enough to build sequence, selection, iteration, and recursion.
- **`then` transforms a value; `let_value` chooses the next sender.** Any runtime-dependent control flow needs `let_value`.
- `when_all` gives you fork/join; CPS continuations give you backtracking; type erasure (`any_*_sender`) makes recursion compile.
- The same `bind` pattern works on the error and stopped channels, so error handling and cancellation are just control flow on other channels.
- "Can is not Should" — reach for senders when you need throughput or interruptibility, not for ordinary straight-line code.

---

**Sources**

- [Steve Downey — Using the C++ Sender/Receiver Framework (YouTube)](https://www.youtube.com/watch?v=xXncLUD-4bA)
- [Slides: C++Now 2023 Async Control Flow — Steve Downey](https://sdowney.org/posts/index.php/2024/05/18/slides-from-cnow-2023-async-control-flow/)
- [std::execution, Sender/Receiver, and the Continuation Monad — Steve Downey](https://sdowney.org/posts/index.php/2021/10/03/stdexecution-sender-receiver-and-the-continuation-monad/)
- [P2300R10: `std::execution`](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html)
- [NVIDIA/stdexec — reference implementation](https://github.com/NVIDIA/stdexec)
