---
layout: single
title: "C++ - A Tour of C++ Executors, Part 1 (Eric Niebler, CppCon 2021)"
date: 2026-06-30 10:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - asynchrony
permalink: "2026/06/30/cpp-tour-of-executors-niebler-part1"
---

[Eric Niebler - Working with Asynchrony Generically: A Tour of C++ Executors (part 1/2) - CppCon 2021](https://www.youtube.com/watch?v=xLboNIf7BTg)

This is the talk where [`std::execution`](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html) (P2300) was introduced to a wide audience. Watching it in 2026 — now that the proposal has landed in C++26 — is interesting precisely because Niebler lays out the *intent* before the design hardened. If you've used the algorithms (`then`, `let_value`, `when_all`) without quite grasping why senders are built the way they are, this is the talk that explains the machine underneath. This post covers part 1: the goals, the four core concepts, and the mechanics of how a concurrent operation actually executes.

> **A note on names.** This talk is from 2021, and a few names changed on the way into the standard. The cancellation completion was `set_done` and is now **`set_stopped`**; `done_as_optional`/`done_as_error` are now **`stopped_as_optional`**/**`stopped_as_error`**; the C++23 target slipped to **C++26**. I'll use the talk's original terms where Niebler does and flag the modern spelling.

## The goal: an STL for asynchrony

Niebler frames the whole effort with one analogy. The STL gave us containers, iterators, and **generic algorithms over sequences** — Stepanov's great achievement. But sequences are one narrow domain. The executors work aims to do "what Stepanov did for the STL, but for asynchronous algorithms": a full suite of standard async algorithms derived from real-world requirements (`then` to chain work, `when_all` to launch work concurrently, `sync_wait` to block, plus `repeat`, `stop_when`, `timeout`, …), and a set of **concepts derived from the algorithms themselves**.

Alongside the algorithms, the vision includes: efficient interop with C++20 coroutines (Niebler firmly believes the `sync_await` style is how people will *want* to write async code), an open and extensible way to say *where, how, and when* work runs, standard schedulers out of the box (an event loop; portable access to the system execution context — a Windows thread pool, or Grand Central Dispatch on macOS), and a "nursery" for spawned work.

## P2300 = `std::execution`: four concepts

The proposal is built on a tiny vocabulary:

- **scheduler** — a handle to a compute resource. One operation: `schedule()`.
- **sender** — a unit of *lazy* async work. (You will, Niebler jokes, get tired of hearing "unit of lazy work.")
- **receiver** — a completion handler / callback.
- **operation state** — the live state of an in-flight operation.

The name "sender/receiver" describes what flows: a sender sends, to a receiver, the **result** of an async computation — which is one of three things: a bundle of **values** (success), an **error**, or a **cancellation** signal.

## First example: launch, fan out, join, wait

```cpp
scheduler auto sch = thread_pool.get_scheduler();

sender auto work =
    schedule(sch)
  | then([]{ return do_task_1(); })
  | ... ;

auto [a, b, c] = sync_wait(when_all(t1, t2, t3)).value();
```

Niebler highlights two things about this. First, **everything in the example happens with zero allocations** — scheduling work, running it concurrently, and blocking for it, all allocation-free. Second, executing those lines **does nothing**: you are building a *tree* of work. But not a runtime tree like a red-black tree — the nodes are stored statically in member variables. Think **expression template**.

The design is **self-similar**: `schedule` returns a sender; `then` takes a sender and returns a sender; `when_all` takes senders and returns a sender. Because every algorithm is sender-in/sender-out, you compose complex async expressions out of simple ones, exactly like ranges (and yes, pipe syntax works).

## Second example: moving between execution contexts

```cpp
// accept on a low-latency pool, process on a worker pool, repeat
on(low_latency_sched, accept_request())     // accept_request() returns a sender
  | transfer(worker_sched)
  | then(process_request)
  | repeat();                                // repeat: from libunifex, not P2300
```

`on` (which Niebler clarifies means **start-on** — start execution *on* this context; today's `starts_on`) specifies *where* work begins; `transfer` (today's `continues_on`) moves the completion to another context. He's candid that this serial version only fetches the next request after the previous finishes — you'd launch many concurrent instances, or write it as a coroutine returning a `task` (a libunifex type; there was no standard `task` yet) and `co_await` the senders.

## Under the hood: the control flow

Here's the machine, and it's small:

1. A **scheduler** has one function, `schedule()`, returning a sender that starts in that scheduler's context. *If you only use the algorithms, this is all you need to know.*
2. **`connect(sender, receiver)`** returns an **operation state** — all the state that must stay alive for the operation's duration.
3. The operation state has one function, **`start()`**, which enqueues the work. Nothing is enqueued until `start` is called. (You can connect a sender to a receiver, get an op state, and *drop it on the floor* — no work happened. It's fine.)
4. A **receiver** has three functions — `set_value` (success), `set_error` (failure), `set_done` (cancellation; now `set_stopped`). When the operation completes it calls **exactly one of these, exactly once**.

That's the heart and soul of the model: two simple concepts you'll use (scheduler, sender), and two more for algorithm authors (receiver, operation state). These four can express *any* async computation.

## How a composite operation executes: nesting dolls

Take the `when_all` tree and `connect` it to a receiver. Each sender **wraps the receiver in its own receiver** (adding its algorithm's logic) and passes it down to its children. `when_all` builds three wrapped receivers, hands them to its three child senders, each of which wraps again and passes down to the innermost sender — which, having no children, builds an **operation state** and returns it back up, each parent wrapping it in its own op state.

So: **senders nest, receivers nest, operation states nest** — Russian nesting dolls. Then `start()` recurses into the children: operations **execute outside-in** and **complete inside-out**. The innermost `schedule` operation enqueues onto the thread pool; a thread picks it up and calls `set_value`, which propagates back out through each wrapping receiver.

Two things Niebler stresses:

- Every adapter (`when_all`, `then`, …) gets to **run code when the operation starts and when it finishes** — it bookends each async operation, which is how it implements its logic.
- These are **layers of behavior, not necessarily layers of data**. An op state with many nested layers can still be tiny — don't fear a giant struct.

## Implementing `then` in ~20 lines

The whole point of the four concepts is that *you* can write algorithms. A minimal `then`:

```cpp
// the algorithm: curry the sender and function into a then_sender
template <sender S, class F>
sender auto then(S s, F f) { return then_sender<S, F>{std::move(s), std::move(f)}; }

// the sender: store the input sender; connect wraps the receiver
template <sender S, class F>
struct then_sender {
    S s_; F f_;
    template <receiver R>
    auto connect(R r) {
        return execution::connect(std::move(s_),
                                  then_receiver<R, F>{std::move(r), std::move(f_)});
        // no work happens at start, so just return the inner op state
    }
};

// the receiver: this is where then's logic lives
template <receiver R, class F>
struct then_receiver {
    R r_; F f_;
    template <class... Vs>
    void set_value(Vs... vs) {
        execution::set_value(std::move(r_), f_(std::move(vs)...));  // chain f
    }
    void set_error(auto e)  { execution::set_error(std::move(r_), e); }   // pass through
    void set_done()         { execution::set_done(std::move(r_)); }       // pass through
};
```

`set_value` is where the magic is: instead of forwarding the values, it runs them through the user's `f` and forwards *that*. Error and cancellation just pass through. (Caveat Niebler flags: if `f` returns `void`, this won't compile — you need an extra overload.) The standard's `then` handles more corner cases, but this is genuinely the shape of it.

## Senders and coroutines

The interop goes both ways, with **no extra allocation or synchronization** for the adaptation:

- **Awaitables as senders.** A `task` (a coroutine type) can be passed straight to `sync_wait`, which expects a sender. The `task` doesn't need to know anything about sender/receiver — it just implements the awaitable interface, and the sender/receiver customization points recognize awaitables and adapt them as receivers.
- **Senders as awaitables.** You can `co_await` a sender inside a coroutine, provided the coroutine's promise type opts in. Authoring such a `task` is easy: inherit the promise from **`with_awaitable_senders`** and you get sender-awaiting for free.

So the guidance becomes: leave the choice to your caller. **If you provide an async API, return a sender** — then the user decides whether to use coroutines or not. That choice belongs to them.

## Cancellation across the coroutine boundary

Coroutines have no cancellation channel — only return and throw. So what happens when an awaited sender completes via `set_done`? Niebler's answer: it behaves like an **uncatchable "exception"** (his scare quotes). The entire async call stack of awaiting coroutine frames is unwound exactly as if an exception were propagating — destructors run in the same order — and even `catch(...)` won't stop it. Mechanically, `with_awaitable_senders` builds a linked list of coroutine frames; cancellation walks that list, deleting each frame.

If you *don't* want to unwind the whole stack, map cancellation into something a coroutine understands natively: `done_as_optional` (→ `nullopt`) or `done_as_error` (→ an exception of your choice) — today's `stopped_as_optional` / `stopped_as_error`. And when that cancellation "exception" reaches a sender boundary (you're awaiting a sender, not a coroutine — no frame to delete), it's translated back into a `set_done` call. Senders and coroutines intermix seamlessly, and that's why the earlier "infinite loop" isn't infinite: awaiting a sender can exit via cancellation, which immediately stops the coroutine.

## Q&A worth keeping

- **GPUs / heterogeneous.** A vendor (e.g. NVIDIA) supplies the scheduler and the compiler; the generic algorithms have default implementations but are **customizable**, so passing a GPU scheduler to `sort` picks a GPU-specific implementation. Unified-memory CPUs (M1) fit *nicely* — generic code compiles for device with no host/device annotations, reaching ~90–95% of hand-tuned performance, lowering the bar to acceleration.
- **Debugging.** Sender/receiver doesn't directly help, but it's **structured**: coroutines give you a real async call stack, and debuggers are gaining the ability to walk coroutine chains — so you'll see not just *what* is executing but *who's waiting on it and how you got there*.
- **Does this replace `future`/`promise`?** No — it's a **lower-level substrate**. You don't have to build one giant tree and `sync_wait` it in `main`; you could write an `as_future` that launches a sender and hands back a handle. They didn't propose it because `std::future` is "fairly broken." Expect most people to live in coroutines and higher-level abstractions (channels, message passing, reactive streams) built *on* sender/receiver — just as ranges sit on iterators.
- **vs. ASIO/folly executors.** Those are a **fire-and-forget** `execute(function)` model, which has composability problems (the subject of part 2). Sender/receiver is designed to supersede them.

## Takeaways

- The mission is an **STL for asynchrony**: standard generic async algorithms over a small concept vocabulary.
- Four concepts — **scheduler, sender, receiver, operation state** — express any async computation. Senders are lazy; nothing runs until `start()`.
- The design is **self-similar** (sender-in/sender-out) and builds a **static tree** with zero allocations; senders, receivers, and operation states **nest** like dolls, executing outside-in and completing inside-out.
- Writing an algorithm means writing a **receiver** (and maybe an op state); `then` is ~20 lines, with `set_value` carrying the logic.
- Senders and coroutines convert both ways for free; **cancellation** unwinds the async coroutine stack like an uncatchable exception, and translates back to `set_stopped` at sender boundaries.
- If you write async APIs, **return senders** and let the caller choose coroutines or not.

Part 2 covers structured concurrency, how cancellation is actually implemented, and an extended worked example — worth watching right after this one.

---

**Sources**

- [Eric Niebler — A Tour of C++ Executors, part 1/2 (CppCon 2021, YouTube)](https://www.youtube.com/watch?v=xLboNIf7BTg)
- [P2300R10: `std::execution`](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html)
- [NVIDIA/stdexec — reference implementation](https://github.com/NVIDIA/stdexec)
- [libunifex — the experimental library this talk demos](https://github.com/facebookexperimental/libunifex)
