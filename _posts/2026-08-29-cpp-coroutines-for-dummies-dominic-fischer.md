---
layout: single
title: "C++ - Coroutines for Dummies (Dominic Fischer, C++Now 2026)"
date: 2026-08-29 14:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - coroutines
  - concurrency
permalink: "2026/08/29/cpp-coroutines-for-dummies-dominic-fischer"
---

[Dominic Fischer - Coroutines for Dummies - C++Now 2026](https://www.youtube.com/watch?v=apLDto3FUVA)

Dominic Fischer works on platform security at Bloomberg, where five years of IO-heavy C++ workloads made coroutines a professional necessity rather than a curiosity. He wrote a four-or-five-part internal series called *Coroutines for Dummies* to explain them to colleagues, it went over well, and C++Now got part one.

The framing is set out honestly in the first two minutes:

> This isn't going to be a comprehensive deep dive. I'm not going to comb through the spec telling you every nook and cranny. My goal in this 90-minute session is just to show you the minimum you need to get started, and empower you with enough information to then go read cppreference yourself and have a clue what you're actually looking at.

Followed immediately by the disclaimer that gets the biggest laugh of the talk:

> I'm kind of showing you how to juggle knives without telling you that you're holding knives. So don't just go write some coroutine code and ship it to production immediately.

There is even a notation for it. When a slide oversimplifies, it carries a Pinocchio emoji — the long-nose asterisk, meaning *there is more to this story and I am not telling it right now*.

## What a coroutine actually is

Strip away every C++ specific and the definition is one line: **a coroutine is a function that can suspend its execution and be resumed later.**

A regular function prints "hello", prints "hi", prints "how are you", returns. You call it, it runs to completion, control comes back. No smoke, no mirrors.

A coroutine inserts suspension points between those statements. Print "hello", suspend. Go do something else. Come back, resume — print "hi", suspend. Go do something else. Resume — print "how are you", done.

Fischer then shows what that looks like if you write it by hand in C++20-less C++, which is the single most clarifying slide in the talk:

```cpp
struct Coroutine {
    int stage = 0;

    void resume() {
        switch (stage) {
            case 0: std::println("hello");       break;
            case 1: std::println("hi");          break;
            case 2: std::println("how are you"); break;
            default: assert(false);
        }
        ++stage;
    }
};

Coroutine do_the_coroutine() { return Coroutine{}; }

int main() {
    auto c = do_the_coroutine();
    c.resume();
    c.resume();
    c.resume();
}
```

That is it. A little integer tracking which stage of execution you are in. While a `resume()` call is active the coroutine is running; between `resume()` calls it is suspended. In the gaps, you go do whatever you like.

Writing this by hand is tedious, which is exactly the point. C++20 coroutines are a deal where you write something that *looks like* straight-line code and the compiler writes the state machine for you.

That framing recurs at the end of the talk, in response to an audience question about how coroutines compare to async runtimes in other languages:

> C++ coroutines are just about making state machines, and then we use those state machines to organize our asynchronous work.

There is no scheduler in the standard. No event loop. No runtime. Just state machines, and whatever you build on top.

## The three keywords, and the signature problem

A function is a coroutine when its body uses `co_await`, `co_yield`, or `co_return`. If you see one of those keywords, it is a coroutine. If you do not, it is not. Full stop.

The implication is worth sitting with:

> If you look at the signature of a function alone, without seeing the body, you actually cannot tell that the function is a coroutine. You just can't tell.

You can look at the return type, see something that smells asynchronous, and take an educated guess. That is all. And guesses can be invalidated by an implementation change you never see.

One more rule: inside a coroutine you cannot use plain `return`. It is `co_return` or nothing.

Fischer's own ranking of the three keywords is unambiguous — `co_await` is the one that matters:

> Once you understand how `co_await` works, I think you're set. Everything else is just minutiae built on top of it.

## Awaitables: three methods and nothing else

`co_await` takes an expression on the right, optionally produces a value on the left. The expression must resolve to an **awaitable** — informally, something you can wait for. An HTTP response. A SQL query. A timer. Things whose completion your process fundamentally does not control:

> Nobody can control time. As of filming.

Formally, an awaitable is any struct or class with three methods:

```cpp
struct MyAwaitable {
    bool await_ready();
    void await_suspend(std::coroutine_handle<> handle);
    MyResult await_resume();
};

// used as:
MyResult result = co_await MyAwaitable{...};
```

- **`await_ready`** is the compiler asking *do you have the result right now?* Usually no — the request has not even been sent. But if you have a cache in front of the store and the value is already there, you can answer yes and skip the entire suspension machinery. It is a fast-path optimization, nothing more.
- **`await_suspend`** is called *after* the compiler has suspended the coroutine. The awaitable now owns the responsibility of resuming it later — when the response arrives, when the timer fires.
- **`await_resume`** returns the result. Its return type is precisely what `co_await` evaluates to; the value passes straight through.

## The coroutine handle is a glorified callback

The formal definition of `std::coroutine_handle` — "a pointer to the coroutine" — is, as Fischer notes, useless to a beginner. So he builds the intuition from callbacks instead, which everyone has suffered through.

Take an asynchronous key-value store:

```cpp
void load_from_store(std::string key, std::function<void(std::string)> cb);

void load_callback(std::string key, std::string value) {
    std::println("{} -> {}", key, value);
}

void do_the_thing() {
    std::string key = "Dominic";
    load_from_store(key, std::bind(load_callback, key, std::placeholders::_1));
}
```

Notice the detail that carries the whole analogy: **the callback only gives you the value, never the key.** So you have to `std::bind` a copy of the key to keep it alive.

Why? Because `load_from_store` returns immediately, `do_the_thing` exits, and `key` is destroyed — but you still need it later, when the callback fires. You are manually preserving local state across a suspension point.

That is exactly what the compiler does when it suspends a coroutine. And so:

> You can picture the return value of that `std::bind` call as basically the same thing as what a coroutine handle is. The coroutine handle is basically like a glorified callback — just some way to make the coroutine continue.

## What the compiler generates for `co_await`

With that in hand, the desugaring is readable. For `MyResult result = co_await awaitable;` the compiler produces roughly:

```cpp
auto&& awaitable = /* the expression */;

if (!awaitable.await_ready()) {
    // compiler suspends the coroutine here
    // (imagine the std::bind capturing all the local state)
    auto handle = /* handle to this coroutine */;
    awaitable.await_suspend(handle);
    // coroutine stops running; control returns to the caller
    // ... later, someone calls handle.resume() and we continue here
}

MyResult result = awaitable.await_resume();
```

An audience member asks whether control ever loops back to re-check `await_ready`. It does not — it is checked exactly once. Ready means fall through; not ready means suspend, resume, fall through. There is no polling loop.

The suspended state is, in Fischer's image, like hitting a breakpoint in a debugger. Everything just holds there while other code runs.

## Writing an awaitable, and the assert that is not paranoia

Wrapping the callback API into an awaitable:

```cpp
struct AwaitableLoad {
    std::string key;
    std::optional<std::string> result;

    explicit AwaitableLoad(std::string k) : key(std::move(k)) {}

    bool await_ready() { return false; }

    void await_suspend(std::coroutine_handle<> handle) {
        load_from_store(key, [this, handle](std::string value) {
            result = std::move(value);   // store BEFORE resuming
            handle.resume();
        });
    }

    std::string await_resume() {
        assert(result.has_value());
        return *result;
    }
};

void do_the_thing() {   // now a coroutine
    std::string key = "Dominic";
    std::string value = co_await AwaitableLoad(key);
    std::println("{} -> {}", key, value);
}
```

`await_ready` returns `false` because the request has not been sent yet. `await_suspend` is where the work actually starts — once the compiler has told you the coroutine is parked, now is as good a time as any.

The `assert` is not decoration. Swap the two lines inside the callback so `handle.resume()` runs before `result` is stored, and the assert fires. Every single time:

> This is not a case of "this might be a race condition where some event loop somewhere is going to eventually call the coroutine, at which point maybe you've stored the result by then." No. Immediately when you call `handle.resume()`, inside that stack frame, the coroutine continues. So `await_resume` is happening *inside* the `resume()` call.

Resumption is synchronous and reentrant. That single fact rules out a whole category of bugs.

And note what disappeared from `do_the_thing`: the manual state preservation. No `std::bind`, no capturing the key. The compiler does it.

## Why this is worth the boilerplate

Fischer is careful about the reaction the big awaitable struct might provoke:

> If you're using coroutines in actual production, you're not going to be writing these gigantic awaitables. Any half-decent coroutine library will have this inside it for you. You'd only have to write the code at the bottom.

The payoff is visible the moment you need more than one operation. Load ten keys sequentially, because you do not want to overwhelm the store:

```cpp
for (const auto& key : keys) {
    values.push_back(co_await AwaitableLoad(key));
}
```

A for loop. That is the whole thing.

Do the same with the raw callback API and you are threading a vector through a chain of callbacks — probably a span, an index, a "load the next one when this one finishes" continuation, a final callback to collect the result. And that is just a loop. Try an `if`. Try recursion.

> Nice and simple, like you do with your synchronous blocking code.

## The two standard awaitables

The standard library provides exactly two, and both are trivial.

`std::suspend_never` never suspends. `await_ready` returns `true`, so `await_suspend` is never called — you could put `std::terminate` in it and never find out. `await_resume` does nothing.

> You can pretty much think of `co_await std::suspend_never{}` as a no-op. The compiler could just remove it and it would make no difference.

`std::suspend_always` always suspends. Never ready, discards the handle in `await_suspend`, does nothing on resume.

Which prompts the obvious worry — does that not mean your coroutine gets stuck forever? Fischer:

> Yes. If you're thinking that, you're on the right track.

(Asterisk: there are other ways to resume a coroutine. Dummies do not need to know about them yet.)

## The promise type

The return type of a coroutine has to satisfy some conditions. Minimally, it needs a nested member type called `promise_type`, and that type supplies the customization points:

```cpp
struct MyCoroutine {
    struct promise_type {
        MyCoroutine get_return_object() { return MyCoroutine{}; }
        std::suspend_never initial_suspend() { return {}; }
        std::suspend_never final_suspend() noexcept { return {}; }
        void return_void() {}
        void unhandled_exception() {}
    };
};
```

This is where you decide the semantics of your coroutine — eager or lazy, what may be yielded, what may be returned, what happens on an exception.

**`get_return_object`** is a factory, near enough a constructor. The compiler allocates a fresh `promise_type` — with `new`, and yes, that is a heap allocation by default — then calls `get_return_object` to build the thing the caller receives, and returns it as soon as possible, typically at the first real suspension point.

**`initial_suspend`** is inserted immediately before the body you wrote. This is the eager/lazy switch. Return `suspend_never` and the call vanishes, so the body runs immediately — an eager coroutine. Return `suspend_always` and the coroutine parks before executing a single line of your code, and it is on you to decide when to start it — a lazy coroutine.

**`final_suspend`** is inserted at the very end of the body, after a return *or* a throw. It runs either way.

**`return_void` / `return_value`** are what `co_return` becomes. Bare `co_return` calls `return_void`; `co_return x` calls `return_value(x)`. You must define exactly one, not both. And the parameter type of `return_value` is what fixes the set of things your coroutine is permitted to return — take an `int` and you may only `co_return` integers.

**`unhandled_exception`** — imagine the entire body wrapped in a try/catch. Anything thrown lands here, which is where you propagate it to the right place: to the parent coroutine, if you subscribe to structured concurrency. And `final_suspend` still runs afterwards, regardless.

## The demos, which are really an audience quiz

The back half is live Compiler Explorer with the audience predicting outputs. The questions are simple by design and the answers stack into a working model.

**Change `initial_suspend` to `suspend_always`.** Nothing prints at all. Not "some of it" — nothing. `initial_suspend` fires before the first line of the body, the coroutine parks there, and nothing in the program ever resumes it. An audience member gets this immediately: it suspends, and there is nothing resuming it.

**Comment out the `co_return`.** It stops compiling — the function now falls off the end of a non-void function. But the deeper answer comes from the audience and Fischer flags it as the important one: *with no `co_return`, it is not a coroutine at all.* None of the promise type machinery applies. Removing one keyword changes what kind of thing the function is.

**Is a function that calls a coroutine and returns its result itself a coroutine?**

```cpp
MyCoroutine do_something_else() {
    return do_something();   // do_something IS a coroutine
}
```

The best answer of the session, from the audience:

> In practical terms for the caller, it effectively behaves like a coroutine, because the return value is returned from a coroutine. But it is not itself a coroutine.

No `co_await`, no `co_yield`, no `co_return` in the body. It is a proxy function, and Fischer notes people do trip over this.

**Change `final_suspend` to `suspend_always`.** The output does not change — because `final_suspend` runs at the very end, after the entire body has already executed. But the behaviour does change, and the audience gets there: **the coroutine frame leaks.**

That is the actual distinction. `suspend_never` in `final_suspend` gives you automatic cleanup — the frame is destroyed when the coroutine falls off the end. `suspend_always` keeps the frame alive after the body has finished, and you must destroy it yourself.

Which sounds like a pure downside until the closing Q&A, where the use case lands. With a lazy task type you need to pull the return value out of the frame *after* the body has completed but *before* the frame dies. Suspending at `final_suspend` holds the frame open long enough to steal the value, then you explicitly destroy it. The mechanism: grab the handle inside `get_return_object`, store it in the return object, call `destroy()` in that object's destructor. Generators want it too — it lets you unconditionally free the frame at the end, without checking whether the generator ran to completion or stopped somewhere in the middle.

## Threads, and where the first line actually runs

The second demo replaces the fake awaitable with one that genuinely sleeps, spawning a thread per sleep and detaching it. (Wasteful, acknowledged, slideware.) Then it prints thread IDs.

The instructive result is not that the sleep threads differ. It is that **the first line printed from inside the coroutine carries the main thread's ID.**

> When I call `do_something`, the first part of the coroutine runs directly in the main thread. Only after the first `co_await` on `my_sleep` is a new thread created, at which point the coroutine is resumed inside that new thread.

A coroutine starts on whatever thread called it. It resumes on whatever thread called `resume()`. Nothing about a coroutine implies a thread hop — the hop comes from the awaitable, or the scheduler underneath it.

The same demo produces the best exchange of the session. Fischer asks where a print statement placed after the coroutine call in `main` will appear in the output, expecting "after the first coroutine line." He gets that answer, and then gets corrected twice — the timing is a race, and the outputs could interleave. He takes it well:

> Initially when I planned this question I was going to say it's going to be 0-1, 0-1, 0-1. But after the last demo with you guys calling me out on my race conditions, I'm not going to make that statement.

The one thing that *is* guaranteed: everything before the first `co_await` runs synchronously on the caller's thread, so it must come out before `main` continues. After that, all bets are off.

The final demo swaps the thread-per-sleep for a real scheduler — one `jthread`, a queue of tasks ordered by expiry — and runs two coroutines through it concurrently. Their output interleaves, on a single thread, which is the whole point of the exercise.

## On allocations and scaling

Asked whether coroutines hold up under heavy IO-bound traffic, Fischer separates the concerns cleanly. Scaling is a library problem, not a language-feature problem:

> All coroutines do for you is give you a way to orchestrate the states. It doesn't necessarily impede nor improve performance. All it really does is help you organize it in an easier-to-handle way.

The one legitimate performance worry is the allocation per coroutine frame. Two mitigations:

**HALO** — heap allocation elision optimization. If the compiler can convince itself the coroutine is created in a scope, destroyed at the end of that scope, and never moved anywhere interesting, it can put the frame on the stack. Fischer's caveat, from a check a few months prior: compilers are *very* sensitive about when they will do this, and you generally need at least `-O2`/`-O3` to see it at all.

**Custom allocators.** Supply your own, back it with a local buffer, and multiple coroutines can reuse the same space instead of each paying for a fresh allocation.

## What to actually use

The closing question is the practical one: if I want coroutines today and I do not want to write awaitables, what do I use?

The C++26 answer is `std::execution`'s `task`, which is coming. For right now, the recommendation is **Folly** — Meta's library — as the most stable, best-maintained coroutine implementation currently available, with the caveat that it does not look like what the standard is going to look like.

---

This was part one of a four-or-five-part series, and it stops exactly where the interesting part begins: everything shown is a single standalone coroutine. Coroutines calling and awaiting each other — the thing you actually do in production — is part three, and Fischer hopes to present it at some future conference.

What part one delivers is the model. A coroutine is a state machine the compiler writes for you. `co_await` desugars into three method calls on an awaitable. The coroutine handle is a callback with a fancier name. The promise type is where you choose the semantics. Suspension is synchronous and reentrant, so ordering inside `await_suspend` is a correctness question, not a race. And the standard gives you none of the runtime — no scheduler, no event loop, nothing but the state machine and whatever you or your library build on it.

That is enough to go read cppreference and know what you are looking at. Which was the stated goal, and it lands.
