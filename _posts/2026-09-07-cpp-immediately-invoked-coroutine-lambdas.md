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

A lambda that is a coroutine, invoked on the spot, is the closest thing C++ has to an inline `async` block:

```cpp
co_await [&] () -> task<void> {
    auto db = co_await pool.acquire();
    co_await db.write(request.id, request.body);
}();
```

It compiles, it reads like the synchronous code it replaces, and it dangles.

## Why capturing by reference breaks

A coroutine frame copies parameters **as declared**. A reference parameter is copied as a reference, so the frame ends up pointing at something it does not own — Core Guideline CP.53.

A lambda hides one of those parameters. The closure is a class, `operator()` is the coroutine, and its implicit object parameter is `const closure&`:

```cpp
struct closure {
    db_pool&   pool;
    request_t& request;

    task<void> operator()() const { /* body */ }   // implicit param: const closure&
};

co_await closure{pool, request}();                 // temporary
```

So the frame holds a **pointer to the closure** and nothing else. The closure is a temporary that dies at the end of the full-expression; the coroutine outlives it. Every capture dangles on resume.

Capturing by value does not help — the copy lives in the closure, which is the object that dies:

```cpp
co_await [request] () -> task<void> {   // copied into the closure...
    co_await log(request.id);           // ...and the frame still only has a pointer to it
}();
```

That is Core Guideline CP.51: *do not use capturing lambdas that are coroutines*, enforced by clang-tidy's `cppcoreguidelines-avoid-capturing-lambda-coroutines`.

## The fix: capture by value, take the closure by value

C++23's deducing `this` (P0847) turns the closure into a real parameter. Take it **by value** and it gets copied into the coroutine frame, captures and all:

```cpp
co_await [request] (this auto self) -> task<void> {
    co_await log(request.id);      // resolves to self.request — owned by the frame
}();
```

Inside the body you still name captures directly; the compiler rewrites them as member accesses on `self`. The temporary closure can die whenever it likes.

Two rules come with it:

```cpp
co_await [&] (this auto self) -> task<void> { ... }();     // still UB: copying a
                                                            // reference gives a reference
co_await [this] (this auto self) -> task<void> { ... }();   // frame owns the pointer,
                                                            // not the object
```

`this auto self` only buys you something if the captures are by value. And clang-tidy stops checking once it sees an explicit object parameter, so `[&](this auto self)` is a lint-clean dangle.

## Wrap it in a macro

The safe form has a fixed shape, so make it the only shape anyone types:

```cpp
#define CO_SCOPE(...) co_await [__VA_ARGS__] (this auto self) -> ::task<void>

task<void> handle_request(connection& conn) {
    auto request = co_await conn.read_request();

    CO_SCOPE(request) {
        auto db = co_await pool.acquire();
        co_await db.write(request.id, request.body);
    }();

    co_await conn.send(response_ok);
}
```

The capture list is explicit and by value, `this auto self` cannot be forgotten, and "did they get the lifetime right?" becomes a grep instead of a review question.

## Summary

- A coroutine frame copies parameters as declared — references stay references (CP.53).
- A lambda's implicit object parameter is a reference, so a capturing lambda coroutine hides that bug (CP.51).
- Capture **by value**, and take the closure **by value** with `this auto self`, so the frame owns everything.
- Wrap it in a macro so the safe form is the easy one.
