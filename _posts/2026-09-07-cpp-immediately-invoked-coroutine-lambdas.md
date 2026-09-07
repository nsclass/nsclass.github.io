---
layout: single
title: "C++ - Immediately Invoked Coroutine Lambdas: Lifetime Pitfalls and Best Practices (Jonathan Müller, ACCU 2025)"
date: 2026-09-07 14:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - coroutines
  - lambda
permalink: "2026/09/07/cpp-immediately-invoked-coroutine-lambdas"
---

[Jonathan Müller - Immediately Invoked Coroutine Lambdas in C++23: Lifetime Pitfalls and Best Practices - ACCU 2025 Short Talks](https://www.youtube.com/watch?v=mF2YMIKZUMg)

A lambda that is a coroutine, invoked on the spot, is the closest thing C++ has to an inline `async` block. It compiles, it reads like the synchronous code it replaces, and it dangles.

Every example below is a complete program on top of this one scaffolding — a minimal lazy `task`, small enough to read in ten seconds:

```cpp
// scaffolding.hpp
#include <coroutine>
#include <exception>
#include <print>
#include <string>
#include <utility>

struct task {
    struct promise_type {
        task get_return_object() {
            return task{std::coroutine_handle<promise_type>::from_promise(*this)};
        }
        std::suspend_always initial_suspend() noexcept { return {}; }
        std::suspend_always final_suspend() noexcept { return {}; }
        void return_void() {}
        void unhandled_exception() { std::terminate(); }
    };

    std::coroutine_handle<promise_type> handle;

    explicit task(std::coroutine_handle<promise_type> h) : handle(h) {}
    task(task&& other) noexcept : handle(std::exchange(other.handle, {})) {}
    ~task() { if (handle) handle.destroy(); }

    void resume() { handle.resume(); }
};
```

`initial_suspend()` returns `suspend_always`, so the body does not run until someone calls `resume()`. That is what a real async task does too — it runs later, on a scheduler — and "later" is where the bug lives.

## Case 1: capture by reference — undefined behaviour

```cpp
#include "scaffolding.hpp"

int main() {
    std::string message = "hello";

    task t = [&message] () -> task {
        std::println("{}", message);   // reads through a destroyed closure
        co_return;
    }();                               // <-- the closure temporary dies here

    t.resume();                        // UB
}
```

Note what is *not* the problem: `message` is alive for the whole of `main`. The object that died is the **closure**, and the frame reaches `message` by going through it.

Here is why. A lambda is a class, and its `operator()` is the coroutine:

```cpp
#include "scaffolding.hpp"

struct closure {
    std::string& message;

    task operator()() const {          // implicit object parameter: const closure&
        std::println("{}", message);
        co_return;
    }
};

int main() {
    std::string message = "hello";
    task t = closure{message}();       // temporary destroyed at this ';'
    t.resume();                        // UB
}
```

A coroutine frame copies its parameters **as declared**. The implicit object parameter is `const closure&` — a reference — so the frame stores a pointer to the closure and nothing else. Spelled out as an ordinary function, the violation is obvious:

```cpp
task body(const closure& self) {       // by reference -> frame stores a pointer
    std::println("{}", self.message);
    co_return;
}
```

That is Core Guideline **CP.53**: parameters to coroutines should not be passed by reference. The lambda just hides the parameter.

## Case 2: capture by value — still undefined behaviour

```cpp
#include "scaffolding.hpp"

int main() {
    std::string message = "hello";

    task t = [message] () -> task {    // copied into the closure...
        std::println("{}", message);   // ...and the frame still only points at the closure
        co_return;
    }();                               // <-- copy destroyed here, with the closure

    t.resume();                        // UB
}
```

By-value capture moves the dangling object; it does not remove the indirection. The frame's pointer to the closure is just as dead as before.

On Apple clang 21 with libc++, case 1 built at `-O2` traps and case 2 prints an empty line — two different symptoms from the same mistake, neither of them a message about lifetimes. Under `-fsanitize=address` both are caught cleanly as `stack-use-after-scope`.

This is Core Guideline **CP.51** (*do not use capturing lambdas that are coroutines*), and clang-tidy's `cppcoreguidelines-avoid-capturing-lambda-coroutines` exists because the compiler will not tell you.

## Case 3: the C++23 fix — capture by value, take the closure by value

Deducing `this` (P0847) turns the closure into a real parameter. Take it **by value** and it is copied into the frame like any other by-value parameter:

```cpp
#include "scaffolding.hpp"

int main() {
    std::string message = "hello";

    task t = [message] (this auto self) -> task {
        std::println("{}", message);   // resolves to self.message — owned by the frame
        co_return;
    }();                               // closure temporary dies here; the frame has its own copy

    t.resume();                        // prints "hello"
}
```

Inside the body you still name captures directly — the compiler rewrites those as member accesses on the explicit object parameter. Written out by hand, the frame now owns everything:

```cpp
task body(closure self) { /* ... */ }  // by value -> frame owns a copy
```

## Case 4: `[&]` plus `this auto self` — a lint-clean dangle

Copying the closure copies each member. A member of reference type stays a reference to the original:

```cpp
#include "scaffolding.hpp"

task make() {
    std::string message = "hello";

    return [&message] (this auto self) -> task {
        std::println("{}", message);   // self.message is still &message
        co_return;
    }();
}                                      // <-- 'message' destroyed here

int main() {
    task t = make();
    t.resume();                        // UB
}
```

The frame safely owns a dangling reference. `this auto self` only buys you something if the captures are by value.

This one is the worst of the five to debug. clang-tidy stops checking the moment it sees an explicit object parameter, so the lint is silent by design. And because the dangling read is now *after a return* rather than after a scope, plain `-fsanitize=address` misses it too — it happily prints `hello`. You need `ASAN_OPTIONS=detect_stack_use_after_return=1` before anything complains. The same applies to `[this]`: the frame owns a copy of the pointer, not of the object.

## Case 5: wrap the safe form in a macro

The correct form has a fixed shape, so make it the only shape anyone types:

```cpp
#include "scaffolding.hpp"

#define CO_SCOPE(...) [__VA_ARGS__] (this auto self) -> ::task

task handle_request(std::string request, int id) {
    task t = CO_SCOPE(request, id) {
        std::println("handling {} (#{})", request, id);
        co_return;
    }();

    t.resume();
    co_return;
}

int main() {
    task t = handle_request("GET /", 7);
    t.resume();
}
```

The capture list is explicit and by value, `this auto self` cannot be forgotten, and "did they get the lifetime right?" becomes a grep instead of a review question.

## Summary

| Form | Captures live in | Verdict |
|---|---|---|
| `[&x] () -> task` | closure temporary | **UB** |
| `[x] () -> task` | closure temporary | **UB** — copy is in the wrong object |
| `[x] (this auto self) -> task` | the coroutine frame | safe |
| `[&x] (this auto self) -> task` | frame owns the reference, not `x` | **UB**, and lint-clean |
| `[this] (this auto self) -> task` | frame owns the pointer, not the object | safe only if the object outlives the task |

- A coroutine frame copies parameters as declared — references stay references (CP.53).
- A lambda's implicit object parameter is a reference, so a capturing lambda coroutine hides that bug (CP.51).
- Capture **by value**, and take the closure **by value** with `this auto self`.
- Wrap it in a macro so the safe form is the easy one.
