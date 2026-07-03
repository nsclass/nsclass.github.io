---
layout: single
title: "C++ - A Tour of C++ Executors, Part 2 (Eric Niebler, CppCon 2021)"
date: 2026-07-03 10:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - asynchrony
permalink: "2026/07/03/cpp-tour-of-executors-niebler-part2"
---

[Eric Niebler - Working with Asynchrony Generically: A Tour of C++ Executors (part 2/2) - CppCon 2021](https://www.youtube.com/watch?v=6a0zzUBUNW4)

[Part 1](/2026/06/30/cpp-tour-of-executors-niebler-part1) laid out the four concepts — scheduler, sender, receiver, operation state — and showed how a composite operation nests like Russian dolls and executes outside-in. Part 2 is where the design *pays off*. Niebler argues that sender/receiver isn't just a callback model with extra steps: it's **structured concurrency**, and structure is precisely what makes cooperative cancellation tractable. The back half of the talk is one extended, slightly unhinged worked example — a program that hooks the whole system's keyboard and plays Model M clicky sounds — built up sender by sender.

> **A note on names.** Same caveats as part 1. The cancellation completion was `set_done` and is now **`set_stopped`**; `done_as_optional` is now **`stopped_as_optional`**; the C++23 target slipped to **C++26**. `std::stop_token` is unchanged. I use the talk's spellings and flag the modern ones.

## Structured concurrency: in the beginning was `goto`

Niebler opens with Nathaniel Smith's essay *"Go Statement Considered Harmful."* The analogy drives the whole section. **Structured** control-flow constructs — a conditional, a loop, a function call — have a **single entry and a single exit**, which lets you treat them as a black box. `goto` is *unstructured*: it can jump anywhere, so you can't reason about it locally.

His claim: most async models are the `goto` of concurrency.

```cpp
// Fire-and-forget, like ASIO / Networking TS executors
void compute_helper_async();
void compute_async(Executor ex) {
    /* ... */
    ex.execute(&compute_helper_async);   // spawn helper, then... keep going
    /* ... */                            // no single exit — the work is detached
}
```

`execute(function)` spawns work and returns immediately. The spawned work has no join point — it's a `goto` into another context. You can't put a scope around it, can't know when it's done, can't safely give it a reference to a local. That's the composability problem part 1 promised to explain.

## Coroutines — and senders — are structured

A coroutine `co_await` is the opposite:

```cpp
task<int>  compute_helper_async();
task<void> compute_async() {
    /* ... */
    int i = co_await compute_helper_async();   // single entry, single exit
    /* ... */
}
```

The callee's activation is **wholly nested** within the caller's. And because it nests:

- Activations nest. Scopes nest. Lifetimes of locals nest.
- **RAII works.**
- It's safe to pass locals **by reference** to a callee — no dynamic allocation, no reference counting:

```cpp
task<int> compute_helper_async(int& data);
task<void> compute_async() {
    int data = 0;
    int i = co_await compute_helper_async(data);   // &data outlives the callee
}
```

Then the key slide: **sender/receiver is *also* structured concurrency.** Look back at the `when_all` tree from part 1 — the nested senders, receivers, and operation states. Those nested op states *are* nested lifetimes. Activations nest, scopes nest, RAII works, and (crucially) the parent op state can hold state that child operations borrow by reference, because the parent's lifetime strictly encloses the children's. No allocation required, exactly like the coroutine case.

## No detached computation, so concurrency must be joined

The rule that makes this hold together: **no detached computation allowed.** Every operation completes by calling exactly one of `set_value` / `set_error` / `set_done` on its receiver — and that completion propagates *back up* through the nesting. A parent operation cannot complete until its children have completed. There is no way to "leak" a running computation past its enclosing scope.

Niebler makes the danger concrete with a synchronous analogy:

```cpp
int compute_helper(int& data);
void compute() {
    int data = 0;
    int result = compute_helper(data);
    /* ... */
}
// What if compute() could return *after* calling compute_helper()
// but *before* compute_helper() returned? -> dangling reference to `data`.
```

That's absurd for synchronous calls, and it should be equally absurd for async ones. Hence: **concurrency must be joined.** When one branch of a `when_all` fails with `set_error`, the framework doesn't just abandon the siblings — it **requests they stop**, waits for each to finish (via `set_done` or `set_error`), and only then completes the whole. Which lands on the thesis of the entire second half:

> In structured concurrency, deep support for **cooperative cancellation** is essential for good performance.

If you can't cancel the siblings promptly when one branch fails, "join" means "wait for work whose result you're going to throw away." Cancellation is what makes structure cheap.

## Cancellation in sender/receiver

It's built on C++20's `std::stop_token`. The calling side:

- declares a `std::stop_source` and calls `get_token()`,
- passes the token to an async operation when launching it,
- calls `request_stop()` when it wants the operation to stop early.

The async side can either **poll** the token (`stop_requested()`) or **register a callback** (`std::stop_callback`) to fire when stop is requested.

In sender/receiver terms, the token rides along with the *receiver*. Some senders own a `stop_source`; when they `connect` down into their children, the wrapped receivers carry a `stop_token`. A child operation that wants to be interruptible asks its receiver for that token (`get_stop_token(receiver)`) and registers a stop callback. The whole thing is a **three-way handshake**:

```
   Caller  --"please stop"-->  OpState
   OpState --"I've stopped"-->  Receiver (via set_done)
```

Niebler's framing of who does what is the part to remember:

- **Orchestrating cancellation is the job of the algorithms, not the user.** You don't wire up stop tokens by hand; `when_all`, `stop_when`, etc. do it.
- **Only algorithms that introduce concurrency need to handle cancellation.** A pass-through like `then` doesn't touch it.
- Cancellation is **asynchronous, cooperative, and best-effort** — no guarantee an operation stops promptly, or at all.
- Common patterns are captured in **dedicated algorithms**, e.g. `unifex::stop_when()`.

```cpp
// stop_when(task, condition) -> sender
//   runs both; when one finishes it cancels the other;
//   completes with task's result once both are done.
sender auto work_loop =
    unifex::stop_when(
        unifex::repeat_effect( processInput() ),   // do work forever...
        userInterrupt()                             // ...until this fires
    );
```

## The extended example: a Model M keyboard simulator

The mission, delivered with a straight face after a story about a beloved clicky keyboard: **write a program that monitors the entire system for keyboard events and plays Model M clicky sounds.** The strategy decomposes cleanly into senders:

1. Model a **key click** as a sender.
2. Model **keyboard input** as a *range* of senders.
3. Model **Ctrl-C** (interrupt) as a sender.
4. Asynchronously transform the range of clicks into noises **until the interrupt sender completes**.

### Step 1 — a key click is a sender

Assume a C-style callback API for keyboard input. Bridge it to a sender via a global slot holding the currently-pending completion:

```cpp
// Type-erased receiver waiting for a keyclick:
struct pending_completion {
    virtual void complete(char) = 0;
    virtual ~pending_completion() {}
};
std::atomic<pending_completion*> pending_completion_{nullptr};

// The system's keyboard callback:
static void on_keyclick(char ch) {
    if (auto* current = pending_completion_.exchange(nullptr))
        current->complete(ch);
}
```

The sender is trivial; the work lives in the operation state, whose `start()` publishes itself into the global slot, and whose `complete()` finishes the receiver:

```cpp
struct keyclick_sender : _sender_of<char> {
    auto connect(unifex::receiver_of<char> auto rec) {
        return keyclick_operation{std::move(rec)};
    }
};
keyclick_sender read_keyclick() { return {}; }

template <unifex::receiver_of<char> Rec>
struct keyclick_operation : pending_completion {
    Rec rec_;
    void complete(char ch) override final {
        if (ch == CTRL_C) unifex::set_done(std::move(rec_));   // interrupt -> cancel
        else              unifex::set_value(std::move(rec_), ch);
    }
    void start() noexcept {
        auto* previous = pending_completion_.exchange(this);   // enqueue
        assert(previous == nullptr);
    }
};
```

Note the shape from part 1 realized in miniature: `connect` builds the op state wrapping the receiver; `start` enqueues; completion calls exactly one of `set_value`/`set_done`. (Niebler also shows a tidier version using `unifex::create_simple<char>` that folds the op state into a lambda — same idea, less boilerplate.)

### Step 2 — keyboard input is a *range* of senders

Here's the payoff of "everything is a sender": a range of them composes with `std::views`.

```cpp
auto keyclicks() {
    return std::views::iota(0u)                       // infinite range...
         | std::views::transform([](auto) {
               return read_keyclick();                // ...of keyclick senders
           });
}

unifex::task<void> echo_keyclicks() {
    for (auto keyclick : keyclicks()) {
        char ch = co_await std::move(keyclick);
        printf("Read a character! %c\n", ch);
    }
}
```

What happens on Ctrl-C? The keyclick sender completes with `set_done`. Inside a coroutine (from part 1) that's an **uncatchable "exception"** that unwinds the awaiting frames; `sync_wait` catches it and returns an empty optional — so the loop just ends. If you want to *handle* it rather than unwind, wrap each sender with `done_as_optional` (today's `stopped_as_optional`) to turn cancellation into a `nullopt`:

```cpp
unifex::task<void> echo_keyclicks() {
    for (auto keyclick : keyclicks()) {
        std::optional<char> ch =
            co_await unifex::done_as_optional(std::move(keyclick));
        if (ch) printf("Read a character! %c\n", *ch);
        else  { printf("Interrupt!\n"); break; }
    }
}
```

Niebler flags that `done_as_optional` can be applied either as a sender adaptor (inside the `co_await`) or as a **range** transform over the senders themselves — `keyclicks() | std::views::transform(unifex::done_as_optional)`. But that's a *synchronous* range adaptor operating on the senders, not on their eventual results. His forward-looking observation: **asynchronous ranges beg asynchronous range adaptors** — a whole reactive-streams layer waiting to be built on this foundation.

### Step 3 — Ctrl-C is a sender

A platform-specific `ctrl_c_handler` (using `SetConsoleCtrlHandler` on Windows) that registers/unregisters in its constructor/destructor, and exposes `.event()` returning a sender that completes when Ctrl-C is pressed — same "publish yourself into a global slot" pattern as the keyclick sender:

```cpp
int main() {
    ctrl_c_handler ctrl_c;
    unifex::sync_wait(
        ctrl_c.event() | unifex::then([]{ printf("Got Ctrl-C\n"); })
    );
}
```

### Step 4 — join them with `stop_when`

Now combine the click loop and the interrupt into one structured operation. `stop_when` sends a stop request to its child (the echo loop) when its trigger (the Ctrl-C event) fires:

```cpp
int main() {
    register_keyboard_callback(on_keyclick);
    ctrl_c_handler ctrl_c;
    unifex::sync_wait(
        echo_keyclicks() | unifex::stop_when(ctrl_c.event())
    );
}
```

Because the stop condition is now *external*, the special Ctrl-C handling can come out of `keyclick_operation::complete`. But there's a catch, and it's the pedagogical heart of the whole example:

> **Q: Why doesn't this work?**
> **A: `stop_when` sends a stop request, but the keyclick operation isn't *listening* for one.**

Requesting stop does nothing unless the interruptible operation registered a stop callback. So we make it listen:

```cpp
struct cancel_keyclick {                       // runs when stop is requested
    void operator()() const noexcept {
        if (auto* current = pending_completion_.exchange(nullptr))
            current->cancel();
    }
};

template <unifex::receiver_of<char> Rec>
struct keyclick_operation : pending_completion {
    Rec rec_;
    std::optional<stop_callback_for_t<Rec, cancel_keyclick>> on_stop_{};

    void complete(char ch) override final { unifex::set_value(std::move(rec_), ch); }
    void cancel()          override final { unifex::set_done(std::move(rec_)); }

    void start() noexcept {
        // register with the receiver's stop token — the one stop_when drives
        on_stop_.emplace(unifex::get_stop_token(rec_), cancel_keyclick{});
        auto* previous = pending_completion_.exchange(this);
        assert(previous == nullptr);
    }
};
```

`get_stop_token(rec_)` pulls the stop token that `stop_when` threaded down through the receiver chain; the `stop_callback` fires `cancel_keyclick`, which completes the outstanding operation with `set_done`. Now Ctrl-C promptly unwinds the click loop through the proper cancellation path. Niebler labels this slide **"Here be dragons"** — writing interruptible algorithms *is* the hard part, but note it's the *algorithm author's* job, done once, not the user's.

The rest, he says, is "a boat-load of nasty platform-specific hackery" — hooking Windows events and actually playing the clicky sounds (the full-fat version is Kirk Shoop's).

## Where it's headed

Niebler closes with the roadmap. `std::execution` (P2300), then targeted at C++23, would bring the concepts, customization points, a handful of fundamental async algorithms, coroutine integration, and integration with the C++17 parallel algorithms. Beyond that: more standard algorithms (mined from libunifex), a `timed_scheduler` concept and `timeout()`, portable access to a **system scheduler** (Windows Thread Pool / GCD), a manual event-loop scheduler, and a **nursery** for spawning-then-joining work. And the higher layers: coroutine types deeply integrated with sender/receiver and ranges (`std::task`, `std::generator`, `std::async_generator`), fully async parallel algorithms, and eventually **async ranges** (reactive streams) with their own adaptors.

*(Watching in 2026: P2300 landed in C++26 rather than C++23, but the shape of this roadmap is exactly what shipped and what's still being built on top.)*

## Takeaways

- **Sender/receiver is structured concurrency.** Nested operation states give you nested lifetimes: RAII works, and children can borrow parents' locals by reference with no allocation — just like `co_await`.
- **Fire-and-forget `execute(fn)` is the `goto` of async** — no single exit, no join point, no safe place to put a scope. That's the composability failure sender/receiver fixes.
- **No detached computation**: every operation completes back up through its parent, so **concurrency must be joined** — which makes **cooperative cancellation essential**, not optional.
- Cancellation rides on `std::stop_token`; the **algorithms** orchestrate it (only those introducing concurrency need to), it's **cooperative and best-effort**, and patterns like `stop_when` package it.
- The worked example shows the real cost model: bridging a callback API to a sender is easy; making an operation **interruptible** (register a stop callback on the receiver's token, complete with `set_done`) is the "here be dragons" part — but it's the algorithm author's job, paid once.
- The endgame is a layered stack — coroutines and async ranges built on sender/receiver, exactly as ranges sit on iterators.

If you've read part 1, this is the half that shows *why* the machine was built the way it was. Watch them back to back.

---

**Sources**

- [Eric Niebler — A Tour of C++ Executors, part 2/2 (CppCon 2021, YouTube)](https://www.youtube.com/watch?v=6a0zzUBUNW4)
- [Slides — Working with Asynchrony Generically (CppCon 2021)](https://github.com/CppCon/CppCon2021)
- [Demo code (Eric Niebler + Kirk Shoop)](https://github.com/ericniebler/executors_demo_code_cppcon_2021)
- [P2300R10: `std::execution`](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html)
- ["Notes on structured concurrency, or: Go statement considered harmful" — Nathaniel J. Smith](https://vorpus.org/blog/notes-on-structured-concurrency-or-go-statement-considered-harmful/)
- [libunifex — the experimental library this talk demos](https://github.com/facebookexperimental/libunifex)
