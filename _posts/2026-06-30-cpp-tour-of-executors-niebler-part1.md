---
layout: single
title: "C++ - Working with Asynchrony Generically: A Tour of C++ Executors, Part 1 (Eric Niebler)"
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

The talk where [`std::execution`](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html) (P2300) was introduced to a wide audience. Part 1 is the machine: four concepts, how a composite operation actually executes, and how to write an algorithm yourself.

> **Names changed on the way into the standard.** `set_done` → **`set_stopped`**; `done_as_optional`/`done_as_error` → **`stopped_as_optional`**/**`stopped_as_error`**; `on` → **`starts_on`**; `transfer` → **`continues_on`**. Code below uses the talk's spelling with the modern name noted.

## The goal

The STL gave us generic algorithms over sequences. The executors work aims to do "what Stepanov did for the STL, but for asynchronous algorithms" — a suite of standard async algorithms (`then`, `when_all`, `sync_wait`, `repeat`, `stop_when`, `timeout`, …) plus **concepts derived from the algorithms themselves**.

## Four concepts, and that is the whole model

```cpp
// scheduler — a handle to a compute resource. One function.
sender auto s = schedule(sched);

// sender — a unit of LAZY async work. One function.
operation_state auto op = connect(sender, receiver);

// operation_state — the live state of an in-flight operation. One function.
start(op);          // NOW the work is enqueued

// receiver — a completion handler. Three functions; exactly one is
// called, exactly once.
set_value(rcvr, values...);   // success
set_error(rcvr, e);           // failure
set_done(rcvr);               // cancellation  (now set_stopped)
```

Niebler calls this slide "the heart and soul of the sender/receiver model." Two concepts you use (scheduler, sender), two more for algorithm authors (receiver, operation state). Together they express any asynchronous computation.

The laziness is worth dwelling on. Once you have connected a sender to a receiver and hold an operation state, **you can drop it on the floor and no work has happened.** Nothing is enqueued until `start`.

## Launch, fan out, join, wait

```cpp
scheduler auto sch = thread_pool.get_scheduler();

sender auto t1 = schedule(sch) | then([]{ return do_task_1(); });
sender auto t2 = schedule(sch) | then([]{ return do_task_2(); });
sender auto t3 = schedule(sch) | then([]{ return do_task_3(); });

auto [a, b, c] = sync_wait(when_all(t1, t2, t3)).value();
```

Two remarkable properties. **Everything here happens with zero allocations** — scheduling, running concurrently, blocking for completion. And **executing those lines does nothing**: you are building a tree, whose nodes live in member variables rather than heap nodes. Think expression template.

The design is **self-similar** — every algorithm is sender-in/sender-out:

```cpp
sender auto schedule(scheduler auto);              // -> sender
sender auto then(sender auto, invocable auto);     // sender -> sender
sender auto when_all(sender auto...);              // senders -> sender
```

which is what lets complex async expressions compose out of simple ones.

## Moving between execution contexts

```cpp
// accept on a low-latency pool, process on a worker pool, repeat
sender auto accept_and_process() {
    return on(low_latency_sched, accept_request())   // accept_request() -> sender
         | transfer(worker_sched)                    // now: continues_on
         | then(process_request)
         | repeat();                                 // from libunifex, not P2300
}
```

`on` means **start-on** — begin execution on this context. `transfer` moves the *completion* to another context.

Niebler is candid that this serial version only fetches the next request after the previous finishes. The coroutine spelling reads better:

```cpp
task<void> accept_and_process() {
    for (;;) {                       // not actually infinite -- see cancellation
        auto request = co_await on(low_latency_sched, accept_request());
        co_await on(worker_sched, process_request(request));
    }
}
```

## How a composite operation executes

`connect` the `when_all` tree to a receiver, and each sender **wraps the receiver in its own receiver**, adding its algorithm's logic, then passes it down to its children. The innermost sender has no children, so it builds an **operation state** and returns it back up — each parent wrapping it in its own op state.

Senders nest, receivers nest, operation states nest. Russian dolls. Then:

```cpp
start(op);   // recurses into children: operations execute OUTSIDE-IN
             // completions propagate back:  operations complete INSIDE-OUT
```

The innermost `schedule` operation enqueues onto the thread pool; a thread picks it up and calls `set_value`, which propagates back out through each wrapping receiver.

Two points Niebler stresses:

- Every adapter gets to **run code when the operation starts and when it finishes** — it bookends each async operation, which is exactly how it implements its logic.
- These are **layers of behavior, not layers of data.** An op state with many nested layers can still be tiny.

## Implementing `then`

The payoff of the four concepts is that you can write algorithms. A working `then`:

```cpp
// The algorithm: curry the arguments into a sender object.
template <sender S, class F>
sender auto then(S s, F f) {
    return then_sender<S, F>{std::move(s), std::move(f)};
}

// The sender: store the input; connect() wraps the receiver.
template <sender S, class F>
struct then_sender {
    S s_;
    F f_;

    template <receiver R>
    auto connect(R r) {
        // No work needs to happen at start, so just return the inner
        // operation state directly -- no op state of our own.
        return execution::connect(
            std::move(s_),
            then_receiver<R, F>{std::move(r), std::move(f_)});
    }
};

// The receiver: this is where then's logic actually lives.
template <receiver R, class F>
struct then_receiver {
    R r_;
    F f_;

    template <class... Vs>
    void set_value(Vs... vs) {
        // Instead of forwarding the values, run them through f
        // and forward THAT.
        execution::set_value(std::move(r_), f_(std::move(vs)...));
    }

    void set_error(auto e) { execution::set_error(std::move(r_), e); }  // pass through
    void set_done()        { execution::set_done(std::move(r_)); }      // pass through
};
```

`set_value` is the whole algorithm. Error and cancellation pass straight through. Niebler flags the obvious gap: if `f` returns `void` this will not compile, so you need an extra overload. The standard's `then` handles more corner cases, but this is genuinely the shape.

## Senders and coroutines convert both ways

**Awaitables are senders.** A coroutine `task` can go straight to `sync_wait`, which expects a sender:

```cpp
task<int> read_socket(socket& s);          // a coroutine type

auto [n] = sync_wait(read_socket(sock)).value();
```

The `task` needs to know nothing about sender/receiver — the customization points recognize awaitables and adapt them. No extra allocation or synchronization for the adaptation.

**Senders are awaitables**, if the coroutine's promise opts in:

```cpp
task<void> read_both(socket& a, socket& b) {
    auto [x, y] = co_await when_all(read_socket(a), read_socket(b));
    //                    ^ when_all returns a sender, and we co_await it
}
```

Opting in is one base class:

```cpp
struct my_task_promise : with_awaitable_senders<my_task_promise> {
    // ... the usual promise machinery ...
};
```

So you can stay in sender land, or work entirely in coroutines:

```cpp
auto compute = [&](int arg) -> task<int> {
    co_await schedule(pool.get_scheduler());   // hop onto the pool
    co_return compute_intensive(arg);
};

auto [a, b, c] = sync_wait(when_all(compute(1), compute(2), compute(3))).value();
```

Which leads to the guidance the talk ends on: **if you provide an async API, return a sender.** That leaves the choice of coroutines-or-not with the caller, which is where it belongs.

## Cancellation across the coroutine boundary

Coroutines have only two exits, return and throw — there is no cancellation channel. So when an awaited sender completes via `set_done`:

> It behaves as though an uncatchable "exception" has been thrown.

The entire async stack of awaiting coroutine frames unwinds exactly as if an exception were propagating, destructors running in the same order — and `catch(...)` will not stop it. Mechanically, `with_awaitable_senders` maintains a linked list of coroutine frames; cancellation walks it and deletes each frame.

If you would rather not unwind everything, map cancellation into something a coroutine understands natively:

```cpp
// cancellation -> nullopt
std::optional<int> r = co_await done_as_optional(some_sender);   // now stopped_as_optional

// cancellation -> an exception of your choice
int v = co_await done_as_error(some_sender, my_cancelled{});     // now stopped_as_error
```

And when that cancellation reaches a sender boundary — you are awaiting a sender, not a coroutine, so there is no frame to delete — it is translated back into a `set_done` call. Senders and coroutines intermix freely and cancellation propagates through both.

This is also why the earlier `for(;;)` is not really infinite: awaiting a sender can exit via cancellation, which stops the coroutine immediately.

## Worth keeping from the Q&A

- **GPUs.** The vendor supplies the scheduler and the compiler. All P2300 algorithms have default implementations but are **customizable**, so passing a GPU scheduler to `sort` selects a GPU implementation. On unified-memory CPUs, generic code compiles for device with no host/device annotations, reaching ~90–95% of hand-tuned performance.
- **Does this replace `future`/`promise`?** No — it is a lower-level substrate. You could write an `as_future` that launches a sender and returns a handle; they did not propose it because `std::future` is "fairly broken." Expect most people to live in coroutines and higher-level abstractions built *on* sender/receiver, as ranges sit on iterators.
- **vs. ASIO/folly executors.** Those are a fire-and-forget `execute(function)` model with composability problems — the subject of part 2.

Part 2 covers structured concurrency, how cancellation is implemented, and an extended worked example.

---

**Sources**

- [Eric Niebler — A Tour of C++ Executors, part 1/2 (CppCon 2021, YouTube)](https://www.youtube.com/watch?v=xLboNIf7BTg)
- [P2300R10: `std::execution`](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html)
- [NVIDIA/stdexec — reference implementation](https://github.com/NVIDIA/stdexec)
- [libunifex — the experimental library this talk demos](https://github.com/facebookexperimental/libunifex)
