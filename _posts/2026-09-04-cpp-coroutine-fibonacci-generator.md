---
layout: single
title: "C++ - The Three Types Behind a Coroutine: Return Type, Promise, Awaitable"
date: 2026-09-04 14:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - coroutines
permalink: "2026/09/04/cpp-coroutine-fibonacci-generator"
---

C++20 coroutines have no `coroutine` keyword and no base class. What you get instead is a set of names the compiler looks up on types *you* supply. Learning coroutines is mostly learning which three types those are, and what each one is responsible for.

An infinite Fibonacci generator is small enough to hold all three at once:

```cpp
#include <coroutine>
#include <format>
#include <iostream>
#include <utility>

using namespace std;

struct Fib {
    struct promise_type {
        int current;
        Fib get_return_object() { return Fib{coroutine_handle<promise_type>::from_promise(*this)}; }
        suspend_always initial_suspend() noexcept { return {}; }
        suspend_always final_suspend() noexcept { return {}; }
        suspend_always yield_value(int v) noexcept { current = v; return {}; }
        void unhandled_exception() { throw; }
    };

    coroutine_handle<promise_type> h;
    ~Fib() { h.destroy(); }

    int next() { h.resume(); return h.promise().current; }
};

Fib generate() {
    int prev = 1;
    int next = 2;
    while (true) {
        co_yield prev;
        prev = exchange(next, prev + next);
    }
}

int main() {
    auto fib = generate();
    for (int i = 0; i < 10; ++i)
        cout << format("{} ", fib.next());
    cout << '\n';
}
```

```
$ clang++ -std=c++20 -O2 fib.cpp -o fib && ./fib
1 2 3 5 8 13 21 34 55 89
```

Every symbol in that file belongs to one of three roles:

| Role | Here | Whose side it's on | Answers |
|---|---|---|---|
| **Return type** | `Fib` | the caller | how do I drive this thing? |
| **Promise type** | `Fib::promise_type` | the coroutine | how does the body behave? |
| **Awaitable** | `suspend_always` | each suspension point | do we stop here, and what happens next? |

They are strictly separate jobs, and the confusion people hit almost always comes from collapsing two of them. Take them one at a time.

## 1. The return type — `Fib`

`generate()` is a coroutine because its body contains `co_yield`. Nothing about `Fib` says "coroutine". What `Fib` does is name the promise:

```cpp
struct Fib {
    struct promise_type { /* ... */ };
};
```

When the compiler sees a coroutine body, it computes `std::coroutine_traits<Fib>::promise_type`. The primary template's default is the nested `Fib::promise_type`, which is why the nested-struct spelling works. If that name doesn't exist, the function is ill-formed — you get a compile error instead of a normal function.

So the return type has exactly two responsibilities:

**It carries the promise type.** Either as a nested `promise_type`, or by specializing `std::coroutine_traits` for return types you don't own.

**It is the caller's handle onto a running coroutine.** That's the rest of `Fib`:

```cpp
coroutine_handle<promise_type> h;
~Fib() { h.destroy(); }

int next() { h.resume(); return h.promise().current; }
```

`std::coroutine_handle` is a thin, non-owning pointer to the coroutine frame with three operations that matter: `resume()` to continue the body, `done()` to ask whether it reached final suspend, and `destroy()` to free the frame. Since it's non-owning, *somebody* has to own it — and that somebody is the return type. `Fib`'s destructor is the entire ownership story.

`h.promise()` is the bridge back to the second role: it's how the caller reads what the body produced.

Note the return type is built *before* the body runs — that's `get_return_object()`, and it's a promise member, not a `Fib` member, which brings us to role two.

## 2. The promise type — `Fib::promise_type`

The promise lives inside the coroutine frame, alongside the parameters and locals. It is not a `std::promise` and has nothing to do with futures. It is a bundle of hooks the compiler calls at fixed points in a rewrite it performs on your body:

```cpp
{
    frame* f = /* operator new, or elided */;
    promise_type& p = f->promise;

    Fib ret = p.get_return_object();      // (a) before the body
    co_await p.initial_suspend();         // (b)
    try {
        /* your body, with co_yield rewritten */   // (c)
    } catch (...) {
        p.unhandled_exception();          // (d)
    }
    co_await p.final_suspend();           // (e)
}
```

Match each hook to its member:

**`get_return_object()`** — step (a). Runs before a single line of your body. The caller needs a handle before the coroutine has a chance to suspend, so the return object is constructed first and handed back at the first suspension. `coroutine_handle::from_promise(*this)` is the standard trick: the promise knows its own address, and the frame layout lets the implementation recover the frame from it.

**`initial_suspend()`** — step (b), and it decides the coroutine's personality. `suspend_always` means the body has *not* started when `generate()` returns; you get a coroutine parked at the top and nothing computes until someone resumes. That's exactly what a lazy generator wants. A task type that should start running eagerly returns `suspend_never` here instead.

**`yield_value(int v)`** — step (c). More on this below; it's where `co_yield` lands.

**`unhandled_exception()`** — step (d). The compiler wraps your body in a `try`/`catch(...)`. This one rethrows, so the exception propagates out of whoever called `resume()`.

**`final_suspend()`** — step (e). Returning `suspend_always` here means the frame stays alive after the body ends. That is a hard requirement for this design: `h.done()` and `h.promise()` are only valid to call because the frame still exists. Return `suspend_never` and the frame self-destructs at the end of the body, making both reads use-after-free.

Two members are absent and worth noticing. There's no `return_void()` or `return_value(T)` — a promise needs exactly one — and this compiles only because `while (true)` never falls off the end of the body. Add a `break` and the program becomes ill-formed.

The promise is also where the *data* lives:

```cpp
int current;
```

The coroutine writes it, the caller reads it through `h.promise().current`. That single `int` is the whole channel between the two.

The locals are separate. `prev` and `next` live in the frame too, but as ordinary locals — the compiler preserves them across suspension without you declaring a single member variable or writing a `switch` on a state enum. That's the payoff: the state machine keeps the shape of the algorithm.

(The frame is heap-allocated by default, though the compiler may elide it when the coroutine's lifetime is bounded by the caller's. Counting with a replaced `operator new`, this example allocates once at `-O0` and zero times at `-O2`.)

## 3. The awaitable — `suspend_always`

An awaitable is whatever you can `co_await`. After a couple of lookup steps the compiler ends up with an *awaiter*, and an awaiter is any type with these three members:

```cpp
struct suspend_always {
    bool await_ready() const noexcept { return false; }        // false → suspend
    void await_suspend(coroutine_handle<>) const noexcept {}   // do nothing, return to caller
    void await_resume() const noexcept {}                      // produce nothing on resume
};
```

That's the entire type. `suspend_never` is the same struct with `await_ready()` returning `true`. There is no magic in either — they are the two degenerate awaiters, and every interesting one differs only in what `await_suspend` does with the handle it's given.

The three members split the work cleanly:

- **`await_ready()`** — a fast path. `true` means "the result is already available, don't bother suspending."
- **`await_suspend(h)`** — called *after* the frame is suspended, with a handle to it. Returning `void` (or `true`) means control goes back to the caller of `resume()`. This is where an async awaiter would stash `h` in a callback or hand it to a scheduler. Here it does nothing, which is precisely what a generator wants: suspend, and let the consumer decide when to come back.
- **`await_resume()`** — runs on resumption, and **its return value is the value of the whole `co_await` expression**.

Awaitables appear in three places in the original code, and it's worth seeing they're all the same mechanism: the two returned by `initial_suspend()` and `final_suspend()`, which the compiler `co_await`s in the rewrite above, and the one returned by `yield_value()`.

Because that last one is the interesting case:

### `co_yield` is not a third keyword's worth of machinery

`co_yield e` is defined as `co_await promise.yield_value(e)`. That's the whole rule. So this line:

```cpp
suspend_always yield_value(int v) noexcept { current = v; return {}; }
```

does two separable things. The body — `current = v` — publishes the value into the promise where the caller can reach it. The *return type* — `suspend_always` — is what makes it a suspension point rather than an ordinary function call. Change that return type to `suspend_never` and `co_yield` keeps storing values while never stopping, which for an infinite loop means it hangs.

### Making the awaitable do something

Since `await_resume()`'s return value is the value of the `co_yield` expression, an awaiter is also the channel running *back into* the coroutine. Swap `suspend_always` for a custom awaiter and `co_yield` starts producing a value the body can read:

```cpp
struct Fib {
    struct promise_type;

    struct YieldAwaiter {
        promise_type* p;
        bool await_ready() const noexcept { return false; }
        void await_suspend(coroutine_handle<>) const noexcept {}
        int await_resume() const noexcept;          // hands a value back into the body
    };

    struct promise_type {
        int current;
        int step = 1;                               // set by the caller before resuming

        Fib get_return_object() { return Fib{coroutine_handle<promise_type>::from_promise(*this)}; }
        suspend_always initial_suspend() noexcept { return {}; }
        suspend_always final_suspend() noexcept { return {}; }
        YieldAwaiter yield_value(int v) noexcept { current = v; return YieldAwaiter{this}; }
        void unhandled_exception() { throw; }
    };

    coroutine_handle<promise_type> h;
    ~Fib() { h.destroy(); }

    int next(int step) {
        h.promise().step = step;
        h.resume();
        return h.promise().current;
    }
};

int Fib::YieldAwaiter::await_resume() const noexcept { return p->step; }

Fib generate() {
    int prev = 1;
    int next = 2;
    while (true) {
        int step = co_yield prev;                   // co_yield now has a value
        for (int i = 0; i < step; ++i)
            prev = exchange(next, prev + next);
    }
}

int main() {
    auto fib = generate();
    cout << format("{} ", fib.next(1));
    cout << format("{} ", fib.next(1));
    cout << format("{} ", fib.next(3));             // skip three ahead
    cout << format("{} ", fib.next(1));
    cout << '\n';
}
```

```
$ clang++ -std=c++20 -O2 aw.cpp -o aw && ./aw
1 2 8 13
```

After yielding `2`, a step of 3 advances past 3 and 5 to land on 8. Nothing about the promise's role changed and nothing about the return type's role changed — only the awaiter, and it turned a one-way generator into a two-way conversation. That is the whole reason awaitables are a separate concept: they're the extension point that async libraries build on, and `suspend_always` is just the case where the extension does nothing.

## Putting the three back together

Read the original file once more with the roles labelled:

```cpp
struct Fib {                                    // RETURN TYPE: names the promise, owns the frame
    struct promise_type {                       // PROMISE: the compiler's hooks + the data channel
        int current;                            //   ↳ what the caller reads
        Fib get_return_object() { ... }         //   ↳ builds the return type, before the body
        suspend_always initial_suspend() ...    //   ↳ AWAITABLE: lazy start
        suspend_always final_suspend() ...      //   ↳ AWAITABLE: keep the frame alive at the end
        suspend_always yield_value(int v) ...   //   ↳ store the value, and AWAITABLE: stop here
        void unhandled_exception() { throw; }   //   ↳ the catch(...) around your body
    };
    coroutine_handle<promise_type> h;           // non-owning pointer to the frame
    ~Fib() { h.destroy(); }                     // ...so the return type owns it
    int next() { h.resume(); return h.promise().current; }   // drive + read
};
```

A working mental model, in one line each:

- The **return type** is what the caller holds; it owns the frame and names the promise.
- The **promise** is what the coroutine body is measured against; the compiler calls its members at fixed points, and it carries the values across the boundary.
- The **awaitable** is what a suspension point evaluates to; `await_ready` decides whether to stop, `await_suspend` decides who runs next, `await_resume` decides what the expression is worth.

## Two things this example gets away with

Worth flagging so the pattern isn't copied verbatim into a library.

`Fib` holds a raw `coroutine_handle` and destroys it unconditionally, but suppresses no copies. `coroutine_handle` copies happily — it's a pointer wrapper — so `auto b = a;` compiles and both destructors call `destroy()` on the same frame. A handle-owning return type needs deleted copies, a move that nulls the source, and a null check before destroying.

And `next()` calls `resume()` unconditionally. Resuming a coroutine that's suspended at its final suspend point is undefined behaviour; a finite generator built this way walks straight off the end. The guard is `h.done()` — valid here only because `final_suspend()` returns `suspend_always`.

Since C++23 the library ships `std::generator<T>`, which is this shape with those corners filed off (libstdc++ has it from GCC 14; libc++ doesn't ship it yet). It's worth writing the three types by hand once anyway — `std::generator` is opaque until you know what its promise and its awaiters are doing.

## References

- [Coroutines — cppreference](https://en.cppreference.com/w/cpp/language/coroutines)
- [`[dcl.fct.def.coroutine]` — coroutine definitions, current working draft](https://eel.is/c++draft/dcl.fct.def.coroutine)
- [`[expr.await]` — the `co_await` expression](https://eel.is/c++draft/expr.await)
- [`std::coroutine_handle` — cppreference](https://en.cppreference.com/w/cpp/coroutine/coroutine_handle)
- [Lewis Baker — Understanding operator co_await](https://lewissbaker.github.io/2017/11/17/understanding-operator-co-await)
