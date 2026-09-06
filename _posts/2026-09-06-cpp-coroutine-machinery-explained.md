---
layout: single
title: "C++ - How a Coroutine Actually Works: Return Type, Promise, Awaiter, and the Frame"
date: 2026-09-06 14:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - coroutines
permalink: "2026/09/06/cpp-coroutine-machinery-explained"
---

A C++20 coroutine is an ordinary-looking function whose body contains `co_await`, `co_yield`, or `co_return`. There is no `coroutine` keyword, no base class to derive from, and no library type you must return. Instead, the compiler takes the *names* it finds on types **you** supply and wires them into a state machine it generates for you.

That division of labour is the whole subject. Once you can say which line is yours, which line the compiler wrote, and which object owns the memory, coroutines stop being mysterious — they become a small protocol with about ten member functions in it.

This post builds that protocol from the bottom up: first a coroutine that returns nothing, then one that `co_return`s a value, then a `co_yield` generator producing Fibonacci numbers. Along the way we look hard at the piece people get wrong most often — the coroutine frame's lifetime, and why `final_suspend()` should almost always return `suspend_always`.

## The three types, and who supplies what

Three types are in play, and each answers a different question:

| Type | Example name | Answers |
|---|---|---|
| **Return type** | `Generator<T>` | How does the caller drive and observe this coroutine? |
| **Promise type** | `Generator<T>::promise_type` | How does the body behave, and where do its values live? |
| **Awaiter** | `std::suspend_always` | At this suspension point: do we stop, who runs next, what is the expression worth? |

All three are *yours*. What the compiler and the standard library contribute is much smaller than most people expect:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  YOU WRITE                                                                   │
│    • the return type       Generator<T>     names the promise, owns the frame│
│    • the promise type      promise_type     compiler hooks + value storage   │
│    • awaiters (optional)   YieldAwaiter     what each suspension point does  │
│    • the coroutine body    co_await / co_yield / co_return                   │
└──────────────────────────────────────────────────────────────────────────────┘
                       │  compiler looks up names on the types you supplied
                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  THE COMPILER GENERATES                                                      │
│    • the coroutine frame: layout, size, allocation (or elision of it)        │
│    • the split of your body into resume points — the state machine           │
│    • calls to your promise hooks, at fixed places, in a fixed order          │
│    • two hidden functions per coroutine: its resume() and its destroy()      │
└──────────────────────────────────────────────────────────────────────────────┘
                       │  exposes the frame through one type-erased pointer
                       ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  <coroutine> GIVES YOU (essentially four things)                             │
│    • std::coroutine_handle<P>   resume() / done() / destroy() / promise()    │
│    • std::suspend_always, std::suspend_never   the two trivial awaiters      │
│    • std::coroutine_traits<R, Args...>         how R::promise_type is found  │
│    • std::noop_coroutine()                     a handle for "resume nobody"  │
└──────────────────────────────────────────────────────────────────────────────┘
```

Note what is *not* in the library column: there is no `std::coroutine`, no scheduler, no allocator policy, no task type (until C++23's `std::generator`, and C++26's `std::execution`). C++20 shipped the language mechanism and left every policy decision to you. That is why writing the types by hand once is worth the effort.

## Step 1: the smallest coroutine that compiles

Start with a coroutine that produces nothing at all. The only requirement is that the body contains one of the three keywords:

```cpp
#include <coroutine>
#include <exception>
#include <iostream>

struct FireAndForget {
    struct promise_type {
        FireAndForget get_return_object() noexcept { return {}; }
        std::suspend_never initial_suspend() noexcept { return {}; }
        std::suspend_never final_suspend() noexcept { return {}; }
        void return_void() noexcept {}
        void unhandled_exception() { std::terminate(); }
    };
};

FireAndForget hello() {
    std::cout << "body: start\n";
    co_await std::suspend_never{};
    std::cout << "body: end\n";
}

int main() {
    std::cout << "main: calling\n";
    hello();
    std::cout << "main: returned\n";
}
```

```
$ clang++ -std=c++20 -O2 fire.cpp -o fire && ./fire
main: calling
body: start
body: end
main: returned
```

Five members, and every one of them is mandatory:

- **`get_return_object()`** — builds the object the caller receives. It runs *before* your body.
- **`initial_suspend()`** — returns an awaiter that decides whether the body starts immediately. `suspend_never` here means eager: the body runs as part of the call.
- **`final_suspend()`** — returns an awaiter evaluated after the body finishes. It must be `noexcept`. This is the lifetime decision, and the next section is entirely about it.
- **`return_void()` or `return_value(T)`** — a promise supplies exactly one. `return_void` matches `co_return;` and falling off the end.
- **`unhandled_exception()`** — the compiler wraps your body in `catch (...)` and calls this.

Miss the promise entirely and the diagnostic is direct:

```cpp
struct NotACoroutineType {};
NotACoroutineType f() { co_return; }
```

```
error: this function cannot be a coroutine:
       'std::coroutine_traits<NotACoroutineType>' has no member named 'promise_type'
```

That error names the real rule. The compiler does not look at your return type `R` directly; it instantiates `std::coroutine_traits<R, Args...>`, whose primary template exposes `R::promise_type`. A nested `promise_type` is just the convenient spelling. For a return type you don't own — `int`, say, or a third-party handle — you specialize `coroutine_traits` instead.

This `FireAndForget` is also the one shape where `final_suspend()` returning `suspend_never` is correct: nobody keeps a handle, nobody reads a result, and the coroutine cleans itself up when the body ends. Hold that thought.

## The rewrite the compiler performs

Every coroutine body is transformed into roughly this:

```cpp
{
    frame* f = /* promise_type::operator new, or global ::operator new, or elided */;
    promise_type& p = f->promise;

    R ret = p.get_return_object();          // (a) before anything in your body
    co_await p.initial_suspend();           // (b) first chance to suspend
    try {
        /* your body, with co_await / co_yield / co_return rewritten */   // (c)
    } catch (...) {
        p.unhandled_exception();            // (d)
    }
    co_await p.final_suspend();             // (e) after the body, before cleanup
    /* if not suspended at (e): destroy locals, promise, params; free the frame */
}
```

`ret` is returned to the caller at the *first suspension* — not at the end. That is the fundamental inversion: a coroutine call returns twice-ish, once when it first parks and once (in effect) whenever it parks again.

Instrumenting a real promise makes the order concrete. Here is a lazy Fibonacci computation whose promise prints every hook the compiler calls:

```cpp
struct Lazy {
    struct promise_type {
        int value{};

        Lazy get_return_object() {
            std::cout << "  [promise] get_return_object\n";
            return Lazy{std::coroutine_handle<promise_type>::from_promise(*this)};
        }
        std::suspend_always initial_suspend() noexcept {
            std::cout << "  [promise] initial_suspend -> suspend_always\n";
            return {};
        }
        std::suspend_always final_suspend() noexcept {
            std::cout << "  [promise] final_suspend -> suspend_always\n";
            return {};
        }
        void return_value(int v) noexcept {
            std::cout << "  [promise] return_value(" << v << ")\n";
            value = v;
        }
        void unhandled_exception() { throw; }
    };
    /* ... handle + RAII, shown in the next section ... */
};

Lazy fib(int n) {
    std::cout << "  [body] running\n";
    int a = 0, b = 1;
    for (int i = 0; i < n; ++i)
        a = std::exchange(b, a + b);
    co_return a;
}

int main() {
    std::cout << "main: call fib(10)\n";
    Lazy task = fib(10);
    std::cout << "main: nothing computed yet\n";
    int v = task.get();
    std::cout << "main: get() = " << v << '\n';
    std::cout << "main: done() = " << std::boolalpha << task.h.done() << '\n';
}
```

```
$ clang++ -std=c++20 -O2 lazy.cpp -o lazy && ./lazy
main: call fib(10)
  [promise] get_return_object
  [promise] initial_suspend -> suspend_always
main: nothing computed yet
  [body] running
  [promise] return_value(55)
  [promise] final_suspend -> suspend_always
main: get() = 55
main: done() = true
```

Read the trace against the rewrite: `get_return_object` and `initial_suspend` run inside the call to `fib(10)`; because `initial_suspend` says `suspend_always`, the call returns there and `[body] running` doesn't appear until `get()` resumes the frame. `return_value(55)` stores the result into the promise, `final_suspend` parks the frame with that result still in it, and only then can `main` read `55` and see `done() == true`.

## Step 2: `co_return` a value, and the handle that reaches it

`return_value(55)` wrote into the promise. The caller needs a way to read it, and that is what `std::coroutine_handle` is for:

```cpp
struct Lazy {
    struct promise_type { /* as above */ };

    std::coroutine_handle<promise_type> h;

    explicit Lazy(std::coroutine_handle<promise_type> hh) noexcept : h{hh} {}

    Lazy(const Lazy&)            = delete;      // a frame has exactly one owner
    Lazy& operator=(const Lazy&) = delete;
    Lazy(Lazy&& o) noexcept : h{std::exchange(o.h, {})} {}
    Lazy& operator=(Lazy&& o) noexcept {
        if (this != &o) {
            if (h) h.destroy();
            h = std::exchange(o.h, {});
        }
        return *this;
    }
    ~Lazy() { if (h) h.destroy(); }

    int get() {
        if (!h.done()) h.resume();
        return h.promise().value;
    }
};
```

`std::coroutine_handle<P>` is a pointer wrapper — `sizeof` a `void*`, trivially copyable, **non-owning**. It offers exactly the operations that matter:

| Operation | Meaning | Precondition |
|---|---|---|
| `resume()` | continue the body at its suspension point | suspended, and **not** at final suspend |
| `done()` | has it reached final suspend? | suspended |
| `destroy()` | destroy locals + promise + params, free the frame | suspended |
| `promise()` | reference to the promise inside the frame | frame alive |
| `from_promise(p)` | recover the handle from a promise reference | — |
| `address()` / `from_address()` | type-erase to `void*` and back | — |

Because the handle owns nothing, *something* must. That something is the return type — the only object the caller actually holds:

```
   caller's stack                           heap (or elided into the caller's frame)
 ┌────────────────────────┐               ┌──────────────────────────────────────┐
 │ Lazy task              │               │ COROUTINE FRAME                      │
 │  ┌───────────────────┐ │  points to    │   resume fn ptr  ──► body part 2..n  │
 │  │ handle h    ●─────┼─┼──────────────►│   destroy fn ptr                     │
 │  └───────────────────┘ │               │   suspend index (where to resume)    │
 │                        │               │   promise_type promise  ◄── promise()│
 │  ~Lazy()               │ owns/destroys │   parameters (copied into the frame) │
 │    h.destroy()  ───────┼──────────────►│   locals alive across a suspension   │
 └────────────────────────┘               └──────────────────────────────────────┘
```

The copy operations are deleted for a concrete reason. `coroutine_handle` copies happily — it is a pointer — so `auto b = a;` on a naive return type gives two objects whose destructors both call `destroy()` on the same frame. Move-only with a nulled source is the minimum viable ownership.

## Resource management: the frame is the whole story

The frame holds your parameters (copied in by value — references stay references, which is a classic dangling trap), your locals that live across a suspension, the promise, and the compiler's bookkeeping. Everything about coroutine lifetime is a question about *that block of memory*.

### Where it comes from, and when it goes away

By default the compiler allocates it with `::operator new`. If the promise declares `operator new`/`operator delete`, those are used instead — which makes the frame observable:

```cpp
struct Ticks {
    struct promise_type {
        int current{};

        void* operator new(std::size_t n) {
            std::printf("  frame alloc: %zu bytes\n", n);
            return ::operator new(n);
        }
        void operator delete(void* p, std::size_t n) noexcept {
            std::printf("  frame free:  %zu bytes\n", n);
            ::operator delete(p, n);
        }
        /* get_return_object, initial/final_suspend, yield_value, return_void, ... */
    };
    /* ... */
};

Ticks counter() {
    Noisy guard{"guard"};              // prints on construction and destruction
    for (int i = 0;; ++i)
        co_yield i;
}

int main() {
    std::printf("create\n");
    {
        Ticks t = counter();
        std::printf("pull: %d\n", t.next());
        std::printf("pull: %d\n", t.next());
        std::printf("leaving scope while suspended\n");
    }
    std::printf("done\n");
}
```

```
$ clang++ -std=c++20 -O0 ticks.cpp -o ticks && ./ticks
create
  frame alloc: 40 bytes
  ctor guard
pull: 0
pull: 1
leaving scope while suspended
  dtor guard
  frame free:  40 bytes
done
```

Two things are worth pulling out of that output.

**Destroying a suspended coroutine is orderly, not a leak.** The `counter()` body is an infinite loop; it never returns. When `t` goes out of scope, `~Ticks()` calls `h.destroy()`, which runs the destructors of everything in scope at the suspension point — hence `dtor guard` — then destroys the promise and the parameters and frees the frame. A coroutine you abandon mid-flight is fine, *provided somebody destroys it*.

**The allocation is not guaranteed.** The same program at `-O2`:

```
$ clang++ -std=c++20 -O2 ticks.cpp -o ticks && ./ticks
create
  ctor guard
pull: 0
pull: 1
leaving scope while suspended
  dtor guard
done
```

No allocation at all. This is HALO (coroutine heap allocation elision): when the compiler can prove the frame's lifetime is nested inside the caller's, it puts the frame in the caller's stack frame. It is an optimization, never a guarantee — but it is why generators in tight loops are not automatically a performance disaster.

### Why `final_suspend()` should return `suspend_always`

Look at the rewrite once more:

```cpp
co_await p.final_suspend();
/* if control gets past here, the frame destroys itself and is freed */
```

If `final_suspend()` returns `suspend_never`, the coroutine does not park at the end — it runs off the end of the rewrite and **frees its own frame from inside `resume()`**. Every handle anyone else is holding becomes dangling at that instant, including the one in your return type.

Take the working `Lazy` and change one word:

```cpp
std::suspend_never final_suspend() noexcept { return {}; }   // <-- the bug
```

```
$ clang++ -std=c++20 -O0 -g -fsanitize=address lazy_bad.cpp -o lazy_bad && ./lazy_bad
==81556==ERROR: AddressSanitizer: heap-use-after-free on address 0x603000001c40
READ of size 4 at 0x603000001c40 thread T0
    #0 in Lazy::get() lazy_bad.cpp:45           <-- reading h.promise().value
    #1 in main lazy_bad.cpp:61

freed by thread T0 here:
    #0 in operator delete(void*)
    #1 in fib(int) (.resume) lazy_bad.cpp:49    <-- the coroutine freed its own frame
    #2 in std::coroutine_handle<Lazy::promise_type>::resume() const
    #3 in Lazy::get() lazy_bad.cpp:44
```

That stack frame `fib(int) (.resume)` is the compiler-generated resume function — the coroutine deleted itself while `Lazy::get()` was standing on it. And the program isn't done yet: `~Lazy()` then calls `destroy()` on the same freed frame, a double free.

Side by side:

```
   final_suspend() → suspend_always          final_suspend() → suspend_never
   ────────────────────────────────          ───────────────────────────────
   body ends                                 body ends
   return_value(55) → promise                return_value(55) → promise
   PARK at final suspend                     frame destroyed and freed
     (frame + promise stay alive)              (from inside resume(), by itself)
   resume() returns to the caller            resume() returns to the caller

   h.done()    → true                        h.done()    → use-after-free
   h.promise() → 55                          h.promise() → use-after-free
   ~Lazy() → h.destroy() → frame freed       ~Lazy() → h.destroy() → double free
```

So the rule is simply: **if anything outside the frame will touch the handle after the body completes, `final_suspend()` must suspend.** In practice that covers nearly everything you would write:

- a generator, because the consumer calls `done()` to end its loop;
- a lazy task, because the caller reads the result out of the promise;
- an async task, because its awaiting continuation must be resumed *from* the final suspend point;
- anything whose return type calls `destroy()` in a destructor — that destructor must find a frame still there.

`suspend_never` at final suspend is correct only for a genuinely detached, fire-and-forget coroutine that nobody holds a handle to and nobody observes — the `FireAndForget` at the top of this post. If you are unsure which case you are in, you are in the first one.

Three related lifetime facts:

- **`done()` and `promise()` are only meaningful because the frame survived.** `done()` is defined as "suspended at the final suspend point", so a coroutine that never parks there can never truthfully answer it.
- **Resuming a coroutine suspended at final suspend is undefined behaviour.** Parking there means "finished", not "ready to continue". Destroying it, though, is exactly right — and required, since suspending at final suspend hands the cleanup obligation to whoever owns the handle. That is the trade `suspend_always` makes: the frame stays valid, and you promise to free it.
- **An exception from `unhandled_exception()` still leaves you a frame.** If `unhandled_exception()` itself exits via an exception (as with `void unhandled_exception() { throw; }`), the coroutine is considered suspended at its final suspend point and the exception propagates out of `resume()`. The frame is still there and still needs `destroy()` — which is one more argument for holding it in an RAII type rather than calling `destroy()` by hand.

## Step 3: `co_yield` and the Fibonacci generator

Everything so far used `co_return`, which produces one value. `co_yield` produces many, and it introduces no new machinery at all — it is defined as:

```cpp
co_yield e;      // means exactly:  co_await promise.yield_value(e);
```

Two separable jobs in one expression: `yield_value`'s *body* stores the value where the caller can read it, and `yield_value`'s *return type* is an awaiter that decides whether to stop there. Return `suspend_always` and you have a generator; return `suspend_never` and you have a function that quietly overwrites a variable in a loop forever.

Here is the whole thing, with a range-`for` interface:

```cpp
#include <coroutine>
#include <cstdint>
#include <iostream>
#include <utility>

template <typename T>
struct Generator {
    struct promise_type {
        T current{};
        std::exception_ptr error{};

        Generator get_return_object() {
            return Generator{std::coroutine_handle<promise_type>::from_promise(*this)};
        }
        std::suspend_always initial_suspend() noexcept { return {}; }
        std::suspend_always final_suspend() noexcept { return {}; }

        std::suspend_always yield_value(T v) noexcept {   // store, then stop
            current = std::move(v);
            return {};
        }
        void return_void() noexcept {}
        void unhandled_exception() noexcept { error = std::current_exception(); }
    };

    using handle = std::coroutine_handle<promise_type>;
    handle h;

    explicit Generator(handle hh) noexcept : h{hh} {}
    Generator(const Generator&)            = delete;
    Generator& operator=(const Generator&) = delete;
    Generator(Generator&& o) noexcept : h{std::exchange(o.h, {})} {}
    Generator& operator=(Generator&& o) noexcept {
        if (this != &o) { if (h) h.destroy(); h = std::exchange(o.h, {}); }
        return *this;
    }
    ~Generator() { if (h) h.destroy(); }

    struct iterator {
        handle h;
        bool operator==(std::default_sentinel_t) const noexcept { return h.done(); }
        iterator& operator++() {
            h.resume();
            if (h.done() && h.promise().error) std::rethrow_exception(h.promise().error);
            return *this;
        }
        const T& operator*() const noexcept { return h.promise().current; }
    };

    iterator begin() {
        h.resume();                                    // run up to the first co_yield
        if (h.done() && h.promise().error) std::rethrow_exception(h.promise().error);
        return iterator{h};
    }
    std::default_sentinel_t end() const noexcept { return {}; }
};

Generator<std::uint64_t> fibonacci() {                 // infinite
    std::uint64_t a = 0, b = 1;
    while (true) {
        co_yield a;
        a = std::exchange(b, a + b);
    }
}

Generator<std::uint64_t> fibonacci_upto(std::uint64_t limit) {   // finite
    std::uint64_t a = 0, b = 1;
    while (a <= limit) {
        co_yield a;
        a = std::exchange(b, a + b);
    }
}

int main() {
    int n = 0;
    for (auto v : fibonacci()) {                       // pull 12, then walk away
        std::cout << v << ' ';
        if (++n == 12) break;
    }
    std::cout << '\n';

    for (auto v : fibonacci_upto(100))                 // runs to completion
        std::cout << v << ' ';
    std::cout << '\n';
}
```

```
$ clang++ -std=c++20 -O2 gen.cpp -o gen && ./gen
0 1 1 2 3 5 8 13 21 34 55 89
0 1 1 2 3 5 8 13 21 34 55 89
```

Compare this to writing the same generator by hand. The state you would have had to hoist into member variables — `a`, `b`, and *which line we were on* — are ordinary locals and an implicit resume index inside the frame. The algorithm keeps its shape; that is the entire point of the feature.

A few details in there are doing real work:

**`begin()` resumes once.** Because `initial_suspend()` is `suspend_always`, the coroutine is parked at the top when `fibonacci()` returns. Something must run it up to the first `co_yield` before the first dereference, and `begin()` is that something.

**The sentinel is `done()`.** `fibonacci_upto` ends by falling off the end of its body, which calls `return_void()`, then parks at final suspend with `done() == true`. Only then does `iterator == default_sentinel` become true and the loop stop. This is precisely the read that `suspend_never` at final suspend would have made a use-after-free.

**`break` out of the infinite generator is safe.** The range-`for` binds the `Generator` temporary to a reference for the duration of the loop; leaving the loop early destroys it, `~Generator()` calls `destroy()`, and the frame — parked inside `while (true)` — is torn down with its locals, exactly as `Noisy guard` demonstrated.

**Exceptions travel through the promise.** `unhandled_exception()` stashes rather than rethrows here, because it runs on the coroutine's side of the boundary; the iterator rethrows on the consumer's side, where the `try`/`catch` actually is.

Since C++23 the library ships `std::generator<T>`, which is this type with the corners filed off — recursive `co_yield` of nested ranges, allocator support, proper reference semantics (libstdc++ has it from GCC 14; libc++ does not ship it yet). Reach for that in production; write this one once to know what it is doing.

## The awaiter: the extension point

`suspend_always` and `suspend_never` have appeared throughout, doing nothing. Time to look at what they actually are:

```cpp
struct suspend_always {
    bool await_ready() const noexcept { return false; }        // false -> do suspend
    void await_suspend(std::coroutine_handle<>) const noexcept {}   // return to the resumer
    void await_resume() const noexcept {}                      // the expression is void
};
```

That is the entire type; `suspend_never` is the same with `await_ready()` returning `true`. Every awaiter has these three members, and the interesting ones differ only in what `await_suspend` does with the handle it is handed:

```
co_await e
   │
   ├─ if the promise has await_transform:  e = promise.await_transform(e)
   ├─ if the result has operator co_await: awaiter = e.operator co_await()
   │  otherwise:                           awaiter = e
   ▼
awaiter.await_ready()
   │  true  ────────────────────────────────► skip suspension, go straight to resume
   │  false
   ▼
[ locals and the resume index are saved; the coroutine is now SUSPENDED ]
   │
   ▼
awaiter.await_suspend(handle_to_this_coroutine)
   │  void  or  true  ───► return control to whoever called resume()
   │  false           ───► resume this coroutine immediately (the "no, never mind" path)
   │  coroutine_handle h2 ─► resume h2 instead, as a tail call (symmetric transfer)
   ▼
[ ... time passes; someone calls handle.resume() ... ]
   │
   ▼
awaiter.await_resume()   ────► its return value IS the value of the co_await expression
```

Two consequences worth internalizing.

**`await_suspend` is called *after* the coroutine is suspended**, with a handle to it. That is what makes asynchrony possible: you can store that handle in a callback, hand it to a thread pool, or park it in an epoll registration, and the coroutine simply stays parked until someone resumes it — possibly on a different thread.

**`await_resume()`'s return value is the value of the `co_await` expression.** The awaiter is the channel running *back into* the coroutine body, not just a stop sign.

### Symmetric transfer, and how a task chain manages its frames

The `coroutine_handle` return flavour of `await_suspend` is how coroutines call each other without growing the stack. Here is a `Task` that is itself awaitable, running the same Fibonacci recursively:

```cpp
struct Task {
    struct promise_type;
    using handle = std::coroutine_handle<promise_type>;

    struct FinalAwaiter {                       // returned by final_suspend()
        bool await_ready() const noexcept { return false; }        // always park
        std::coroutine_handle<> await_suspend(handle h) noexcept {
            auto cont = h.promise().continuation;
            return cont ? cont : std::noop_coroutine();            // hand off, or stop
        }
        void await_resume() const noexcept {}
    };

    struct promise_type {
        std::uint64_t value{};
        std::coroutine_handle<> continuation{};   // who is waiting on me

        Task get_return_object() { return Task{handle::from_promise(*this)}; }
        std::suspend_always initial_suspend() noexcept { return {}; }
        FinalAwaiter final_suspend() noexcept { return {}; }
        void return_value(std::uint64_t v) noexcept { value = v; }
        void unhandled_exception() { throw; }
    };

    handle h;
    explicit Task(handle hh) noexcept : h{hh} {}
    Task(const Task&) = delete;
    Task(Task&& o) noexcept : h{std::exchange(o.h, {})} {}
    ~Task() { if (h) h.destroy(); }

    // Task is also an awaiter, so one task can co_await another.
    bool await_ready() const noexcept { return false; }
    std::coroutine_handle<> await_suspend(std::coroutine_handle<> caller) noexcept {
        h.promise().continuation = caller;      // remember who to resume at the end
        return h;                               // and run the callee now, as a tail call
    }
    std::uint64_t await_resume() const noexcept { return h.promise().value; }

    std::uint64_t run() { h.resume(); return h.promise().value; }
};

Task fib(int n) {
    if (n < 2) co_return n;
    auto a = co_await fib(n - 1);
    auto b = co_await fib(n - 2);
    co_return a + b;
}

int main() { std::cout << fib(25).run() << '\n'; }
```

```
$ clang++ -std=c++20 -O2 task.cpp -o task && ./task
75025
```

Trace the frame lifetimes, because this is where all three concepts meet:

1. `fib(n - 1)` creates a frame and returns a `Task` temporary. Nothing has run — `initial_suspend` is `suspend_always`.
2. `co_await` on that temporary calls `Task::await_suspend`, which records the parent as the callee's `continuation` and returns the callee's handle. The compiler resumes it as a tail call, so a 25-deep recursion does not build a 25-deep native stack.
3. The callee finishes, `return_value` stores into *its* promise, and `FinalAwaiter::await_suspend` returns the parent's handle — the parent resumes, again by tail call, from inside the callee's final suspend point. The callee is now parked, frame intact.
4. The parent's `await_resume()` reads `h.promise().value` **out of the still-parked callee frame**. This is only legal because `final_suspend()` suspended.
5. The `Task` temporary dies at the end of the full expression, `~Task()` calls `destroy()`, and the callee's frame goes away.

`std::noop_coroutine()` covers the top of the chain: the outermost task has no continuation, and `await_suspend` must return *some* handle, so it returns one whose `resume()` does nothing and immediately returns to `run()`'s caller.

## Putting it back together

The full map, on one page:

```
         YOUR CODE                              THE FRAME (compiler-generated)
 ┌─────────────────────────────────┐      ┌────────────────────────────────────────────┐
 │ Generator<T>   RETURN TYPE      │      │  resume fn ptr / destroy fn ptr            │
 │   • names promise_type ─────────┼─────►│  suspend index                             │
 │   • holds coroutine_handle ●────┼─────►│  promise_type promise                      │
 │   • ~Generator() → destroy()    │      │    ├─ get_return_object()   (a)            │
 │   • begin()/next() → resume()   │      │    ├─ initial_suspend()     (b)            │
 │                                 │      │    ├─ yield_value()         (c)            │
 │                                 │      │    ├─ return_value()        (c)            │
 │                                 │      │    ├─ unhandled_exception() (d)            │
 │                                 │      │    ├─ final_suspend()       (e)            │
 │                                 │      │    └─ current / error ← data channel       │
 │                                 │      │  parameters (copied by value)              │
 │                                 │      │  locals live across suspensions            │
 └─────────────────────────────────┘      └────────────────────────────────────────────┘

   the caller observes the frame only through the handle:
       h.promise().current   h.done()   h.resume()   h.destroy()

   every co_await / co_yield consults an AWAITER:
       await_ready()  →  await_suspend(handle)  →  await_resume()
```

One line each:

- The **return type** is what the caller holds. It names the promise and it *owns the frame* — nothing else does.
- The **promise** is what the compiler measures your body against. Its hooks run at fixed points, and it is where values cross the boundary.
- The **awaiter** is what a suspension point evaluates to: `await_ready` decides whether to stop, `await_suspend` decides who runs next, `await_resume` decides what the expression is worth.
- The **frame** is the resource. Somebody must `destroy()` it exactly once, which is why `final_suspend()` must keep it alive long enough for that somebody to do it.

## Pitfalls worth memorizing

**Reference parameters dangle.** Parameters are copied into the frame, but a `const T&` parameter copies the *reference*. If the coroutine suspends and the caller's temporary dies, the reference is dangling on resume. Take by value in coroutines, or pass ownership.

**Falling off the end without `return_void` is silently undefined.** `co_return expr;` with no `return_value` is a clean compile error, but a promise with *neither* `return_void` nor `return_value` whose body runs to the closing brace compiles without a diagnostic and is UB. Always define one.

**Never resume a coroutine that is `done()`.** Guard every `resume()` with `done()` for a finite coroutine, or the first pull past the end walks off the final suspend point.

**A raw `coroutine_handle` in your return type needs deleted copies.** Two handles, two destructors, one frame, one double free.

**`final_suspend()` must be `noexcept`,** and it should return `suspend_always` (or a custom awaiter that also always suspends, like `FinalAwaiter` above) in every design where anyone observes the coroutine after it finishes.

**Don't assume the frame is on the heap, or that it isn't.** HALO is real and helps, but it is an optimization. If you need a hard bound, give the promise a custom `operator new` — that also lets you count what is actually allocated.

## References

- [Coroutines — cppreference](https://en.cppreference.com/w/cpp/language/coroutines)
- [`[dcl.fct.def.coroutine]` — coroutine definitions, working draft](https://eel.is/c++draft/dcl.fct.def.coroutine)
- [`[expr.await]` — the `co_await` expression](https://eel.is/c++draft/expr.await)
- [`std::coroutine_handle` — cppreference](https://en.cppreference.com/w/cpp/coroutine/coroutine_handle)
- [`std::generator` — cppreference](https://en.cppreference.com/w/cpp/coroutine/generator)
- [Lewis Baker — Understanding operator co_await](https://lewissbaker.github.io/2017/11/17/understanding-operator-co-await)
- [Lewis Baker — C++ Coroutines: Understanding Symmetric Transfer](https://lewissbaker.github.io/2020/05/11/understanding_symmetric_transfer)
- [My earlier post — The Three Types Behind a Coroutine](/2026/09/04/cpp-coroutine-fibonacci-generator)
