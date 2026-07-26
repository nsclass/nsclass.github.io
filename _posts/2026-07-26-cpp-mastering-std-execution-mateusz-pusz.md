---
layout: single
title: "C++ - Mastering std::execution / Senders & Receivers (Mateusz Pusz, C++Online 2026)"
date: 2026-07-26 14:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - asynchrony
permalink: "2026/07/26/cpp-mastering-std-execution-mateusz-pusz"
---

[Mateusz Pusz - Mastering std::execution (Senders/Receivers) - C++Online 2026 Workshop Preview](https://www.youtube.com/watch?v=bsyqh_bjyE4)

This is a 45-minute teaser for Mateusz Pusz's full-day workshop on `std::execution`, the framework that most of us still call **senders/receivers** because that's where it came from. It officially landed in **C++26**, but — and this is the headline — you don't have to wait for it. It works on **C++20** today via NVIDIA's reference implementation (`stdexec`), it's header-only, and companies are already running it in production.

Where the [Niebler *Tour of Executors*](/2026/06/30/cpp-tour-of-executors-niebler-part1) talks build the model concept-by-concept, Pusz's teaser is a workshop trailer: it's aimed at getting you *oriented* fast — why the framework exists, what the pieces are called, and what a real pipeline looks like — before you go write code yourself. His training motto sums up the philosophy: **"master C++ with your fingertips, not just your eyes."** Reading slides doesn't teach you to write code; muscle memory does. So this post follows the same arc: motivation, vocabulary, then a concrete pipeline.

> **About the speaker.** Mateusz Pusz is a modern-C++ trainer with 20+ years in the language (13 at Intel, 10 at EPAM), the author of **mp-units**, and a voting member of the ISO C++ committee. His interests: performance, low latency, safety, maintainability.

## Why any of this matters: the free lunch is over

The starting point is Herb Sutter's old observation — CPU clock speeds stopped climbing for free. To make software faster you now have to spread work across cores, which means concurrency, parallelism, and asynchrony are no longer a specialist's concern. They touch essentially every non-trivial program and every C++ engineer. So we need this to be *learnable* and *correct*, not just possible.

## Structured concurrency, via the `goto` analogy

Pusz reaches for the same analogy Niebler uses (and it's worth seeing twice, because it's the load-bearing idea). In the 1960s and 70s, programs were written with `goto`. It "worked," but it produced **spaghetti code** — the term comes from literally drawing a line on paper from each `goto` to its target until the page looked like a plate of noodles. No scopes, trivial to write infinite loops, lifetime problems, control flow you can't follow, nothing reusable.

- **Dijkstra, 1968** — *"Go To Statement Considered Harmful."*
- **Kernighan & Ritchie, 1978** — even the fathers of C called `goto` "infinitely abusable."

The fix was **structured programming**: branches, loops, scopes, functions. New language mechanisms replaced the `goto`+`if` patterns with constructs you can reason about locally.

His thesis:

> Computations are to concurrency what functions are to structured programming.

And today's concurrency toolbox is still living in the `goto` era. Mutexes, semaphores, condition variables, raw threads — these low-level primitives impose **no structure**. Everything in RAM is shared with every thread by default; everything is therefore potentially a data race or a deadlock. It would be far better if nothing were shared unless you explicitly declared a channel of communication — but that's not the world we're in, so without structure you synchronize by hand, and that's what crashes in production.

### Fire-and-forget is unstructured

```cpp
void compute_async() {
    SomeData data;
    execute_somewhere(&async_fn, data);   // spawn work referencing `data`, then...
}   // `data` goes out of scope. The detached work may still be running.
```

Detached work never rejoins. It can outlive the data it references, there's no RAII (you can't hand it a `unique_ptr`), and you're back to manual lifetime and manual synchronization. Single entry, but no single exit.

## Why the tools we already had aren't enough

- **`std::future` / `std::promise`** — inefficient and hard to compose. Allocation/deallocation, atomic ref-count churn, synchronization between setting and getting the result, plus scheduling overhead if you use the non-standard `.then` extensions. Worse, a future is **eager**: it's a handle to work *already scheduled*, possibly already running — so you can't even reason cleanly about races. Not usable for efficient composition of async operations.
- **Callbacks** — actually the simplest, most powerful, most efficient way to chain work. But there's **no standard shape**: every vendor invents its own callback signature, so they're inherently uncomposable, and there's no nesting of scopes or lifetimes (RAII doesn't apply).
- **Coroutines** — these genuinely *are* structured concurrency. A co_awaiting coroutine has a single entry and single exit, composes cleanly, and RAII/scopes/lifetimes all just work. Pusz is emphatic that coroutines are excellent and you should learn them. **But** they have two gaps: they **don't support cancellation**, and they may require a **heap allocation** for the coroutine frame (often fine for async I/O, where one allocation is negligible; see the *HALO* paper for when that allocation is elided).

Senders/receivers are designed to fill exactly those gaps — while interoperating with coroutines rather than replacing them.

## The goals of the framework

The proposal set out to give C++ a **standard vocabulary for asynchrony** that feels like the algorithms library — except instead of data algorithms (`find`, `sort`, …), we get **asynchronous algorithms** (`then`, `when_all`, `sync_wait`, `upon_error`, timeouts, retries, …). The design targets:

- An open way to specify **where, how, and when** work runs.
- Composable, generic algorithms; **correct by construction**.
- Efficient coroutine interop.
- Errors that **must** propagate but must **not** be a burden on the user.
- **Cancellation** — which coroutines lack. Note: cancellation is **not an error**; it's just work that's no longer needed.

## The reference implementation

For both the workshop and production you can use **`stdexec` from NVIDIA** — the reference implementation of the accepted C++26 paper, written in C++20, header-only. It's split by namespace/directory:

| Namespace | What it is |
|-----------|-----------|
| `stdexec` | Standardized — proposed and accepted for C++26 |
| `exec` | Useful extensions, not in the standard |
| `nvexec` | NVIDIA GPU hardware schedulers |
| `asioexec` | Interop with Boost.ASIO |

## The four core abstractions

This is the vocabulary the rest of the framework is built on:

- **Scheduler** — a *lightweight* handle to a compute resource, and a strategy for scheduling work onto it. Think of it like `std::allocator`: a cheap handle to something heavier. Its `schedule()` function returns a sender — usually the *start* of a pipeline.
- **Execution context** — the actual resource, the *place* where execution happens (a thread pool, a GPU, an I/O pool). It may be heavy; the scheduler that points at it is cheap.
- **Sender** — a unit of **lazy** async work. It *describes* an asynchronous operation, chains with other senders into pipelines, and acts as a **factory** for receivers and operation states.
- **Receiver** — a completion handler (a callback) with **three channels**: `set_value` (success), `set_error` (failure), and `set_stopped` (cancellation).
- **Operation state** — **non-movable**, persistent storage that lives for the entire duration of the async operation. It's the direct analogue of a **coroutine frame**: the place data is stashed so it survives the whole operation.

### How they fit together

```
scheduler.schedule()            -> sender
sender.connect(receiver)        -> operation_state
operation_state.start()          // work begins here
// completion calls one of: set_value / set_error / set_stopped on the receiver
```

The crucial ergonomic point: **as a user you only ever touch the blue boxes — schedulers and senders.** Receivers and operation states are machinery under the hood. You don't create them, and you often don't even know they're there. (If you're *implementing* an algorithm, then you do need to understand them.)

## Separating *what* from *where*

The whole payoff is that a sender describes the **logic you care about** independently of **where and how** it executes:

```cpp
auto work = read_text(filename)      // a sender producing text
          | std::execution::then(process);   // then run `process` on the result
```

You write the program logic **once**, then decide separately whether it runs on a single thread, a thread pool, a GPU, or anything else — without changing the logic. Note that nothing above says *where* it runs.

`then` takes the previous stage's result as the input to the next functor — exactly like ranges views. And, like views, you can spell it two equivalent ways:

```cpp
// pipe syntax (Pusz's preferred form on slides)
auto s = schedule(sch) | then([]{ return 42; }) | then([](int v){ return v + 42; });

// function-call syntax (identical meaning)
auto s = then(then(schedule(sch), []{ return 42; }), [](int v){ return v + 42; });
```

You'll want `auto` here, because the real type is a nested "onion" that grows with every stage and is as unspellable as a ranges view. Naming the **concept** on the left of `auto` (rather than the type) is how you keep the code readable.

## Three kinds of senders

Every pipeline is built from three roles, mirroring begin / middle / end:

- **Sender factories** — take *no* sender, return a sender (e.g. `schedule`, `just`). The start of the pipeline.
- **Sender adapters** — take a sender, return a sender (e.g. `then`, `continues_on`, `upon_error`). The middle.
- **Sender consumers** — take a sender, return something that is *not* a sender (e.g. `sync_wait`). The end.

The lazy guarantee: factories and adapters **never submit work** before the returned operation state is started, and they never start the inputs passed into them. Nothing runs until a consumer starts it.

```cpp
auto [value] = std::execution::sync_wait(pipeline).value();
```

`sync_wait` starts the operation state and **blocks** the current thread until it completes — because eventually you *do* have to wait for an async result. It returns an **`optional<tuple<...>>`** of whatever the last sender sent:

- The `optional` is **empty** if the operation was **cancelled**.
- It **throws** if the pipeline completed with an **error** (much like `future::get`).
- Otherwise it's a **tuple** — even a single value comes back as a one-element tuple — which is why you'll use **structured bindings** constantly with this framework.

## Channel propagation: the onion at work

Because operation states nest, starting the outermost one cascades `start` inward, and completions cascade back outward through the receivers — the "onion architecture." What each adapter does depends on its logic:

- **`then`** passes `set_error` and `set_stopped` through **unchanged** (it doesn't deal with them), and turns `set_value` into either a new value *or* an error if the lambda throws.
- **`upon_error`** takes an incoming **error** and moves it onto the **value** channel.

Any channel can map to any channel — it's entirely up to the algorithm. And every adapter gets a chance to run code both **when the operation starts** and **when it completes** (that's the adapter's operation state and receiver, respectively).

## Transferring work between execution contexts

One rule that surprises people: **the framework never migrates work from one execution resource to another on its own.** You must be explicit. That's what `starts_on`, `continues_on`, and `schedule` are for:

```cpp
auto pipeline =
      std::execution::schedule(cpu_sched)
    | std::execution::then(work_on_cpu)          // runs on the CPU pool
    | std::execution::continues_on(gpu_sched)    // hop to the GPU
    | std::execution::then(work_on_gpu);         // runs on the GPU
```

The pipeline *knows* where each stage runs because that was encoded into it. You can query it with `get_completion_scheduler` on a sender's environment for a given channel — ask sender-2 above and you get back something equivalent to `cpu_sched`; ask sender-3 and you get `gpu_sched`. The contexts don't have to be different hardware — a classic pattern is an **I/O pool** and a **work pool** on the same CPU, and the framework handles all the cross-context synchronization for you. No manual IPC, no hand-rolled hand-off.

### The teaser's exercise

The hands-on task: read from a socket on the I/O pool, then get *off* the I/O pool quickly (so it's free to wait for the next packet) and do the heavy processing on the work pool.

```cpp
auto work =
      std::execution::schedule(io_sched)
    | std::execution::then([&] {
          return legacy_read_from_socket(socket, buffer.data(), buffer.size());
      })
    | std::execution::continues_on(work_sched)   // note: continues_on, not "continue_on"
    | std::execution::then([&](std::size_t read_len) {
          legacy_process_data(buffer.data(), read_len);
      });

std::execution::sync_wait(std::move(work));
```

A few honest caveats Pusz calls out live:

- **`std::` is stronger than you.** Muscle memory keeps making you type `std::execution` where the framework wants `stdexec` / the correct name — you'll fight your own fingers.
- **`continues_on`, not `continue_on`.** Small name, easy to miss.
- **Compile times are heavy** — this is deeply template-based machinery.
- **Error messages are rough.** Coroutines produce beautiful diagnostics because they're a *language* feature; senders are a pure *library* feature, so the compiler doesn't understand them and the errors are much worse. Getting comfortable reading them is part of the workshop.
- **Lifetime.** In the snippet above `buffer` is captured by reference from the enclosing scope — fine only if you `sync_wait` in the same function. The better pattern is to thread the data *through the pipeline itself* so the whole thing can be returned from a function without dangling. (Covered in the full workshop.)

## Takeaways

The teaser doesn't try to make you fluent — it tries to make the map legible:

- Async is now everyone's problem, and **structured concurrency** is the discipline that makes it tractable: single entry, single exit, local reasoning, correct by construction.
- The existing tools each miss something — futures are eager and inefficient, callbacks have no standard shape, coroutines lack cancellation. `std::execution` unifies them with a standard vocabulary that also **interoperates** with coroutines.
- Learn five words — **scheduler, execution context, sender, receiver, operation state** — and the rest is composition: factories, adapters, consumers piped together, with `continues_on`/`starts_on` to say *where*.
- And Pusz's real message, the one aimed past this particular framework: **you learn to write code by writing it.** Reading slides — or blog posts — gets you oriented. The fingertips do the rest.

For the deeper conceptual build-up of the same model, see the two-part [*A Tour of C++ Executors* (Eric Niebler)](/2026/07/03/cpp-tour-of-executors-niebler-part2) and [Steve Downey on sender/receiver control flow](/2026/06/29/cpp-sender-receiver-control-flow-steve-downey).
