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

Jonathan Müller maintains think-cell's core libraries — their range library, their JSON parser — and is assistant chair for `std::ranges` on the C++ committee. This is a five-minute lightning talk, and it spends those five minutes on exactly one pattern:

```cpp
co_await [&] () -> task<void> {
    // ...
}();
```

A lambda that is a coroutine, invoked on the spot. It is the closest thing C++ has to an inline `async` block, it shows up all over async codebases, and it has a failure mode that compiles cleanly, passes review, and crashes in production.

## The pattern, and why people reach for it

Coroutines are all-or-nothing at function granularity. If you want to `co_await` something, the enclosing function has to be a coroutine, which means the enclosing function's caller has to deal with a `task<T>` instead of a `T`. That colouring propagates outward until somebody blocks.

An immediately invoked coroutine lambda is the escape hatch for the *inner* half of that problem — a block of async code you want to run right here without giving it a name, a signature, and a place in the header:

```cpp
task<void> handle_request(connection& conn) {
    auto request = co_await conn.read_request();

    // "run these three awaits as a unit, right here"
    co_await [&] () -> task<void> {
        auto db = co_await pool.acquire();
        co_await db.write(request.id, request.body);
        co_await db.commit();
    }();

    co_await conn.send(response_ok);
}
```

You get a scoped async block. No new named function, no plumbing of five locals through a parameter list, captures by reference like any other lambda. It reads exactly like the synchronous code it replaces.

That last sentence is the trap. It does not behave like the synchronous code it replaces.

## What actually lives in a coroutine frame

The whole bug follows from one rule, so it is worth stating precisely.

When a coroutine is called, the compiler allocates a frame and **copies the parameters into it**. Locals declared in the body live there too, as do temporaries that have to survive a suspension point. The frame outlives the call expression — that is the point of a coroutine.

But "copies the parameters" means copies them *as declared*. A parameter of reference type is copied as a reference:

```cpp
task<void> log_it(std::string  by_value)  { co_await sink.write(by_value); }  // safe
task<void> log_it(const std::string& by_ref) { co_await sink.write(by_ref); } // frame stores a pointer
```

The second frame holds a pointer to a string it does not own. If the caller's string dies while the coroutine is suspended, the resume touches freed memory. This is Core Guideline **CP.53: parameters to coroutines should not be passed by reference** — the oldest coroutine footgun there is.

Now: where do a lambda's captures live?

## The lowering

A lambda is a class. `[&]` captures become members of the closure type, and `operator()` is a member function:

```cpp
// co_await [&] () -> task<void> { ... }();
// is roughly:

struct __closure {
    connection& conn;
    request_t&  request;
    db_pool&    pool;

    task<void> operator()() const {
        auto db = co_await pool.acquire();
        co_await db.write(request.id, request.body);
        co_await db.commit();
    }
};

co_await __closure{conn, request, pool}();
```

`operator()` is a coroutine. Its parameters get copied into the frame. Its parameter list is empty — except for the implicit object parameter, which is `const __closure&`.

**A reference.**

So the frame contains a pointer to the closure object and nothing else. Not `conn`. Not `request`. Not `pool`. Every capture is reached by dereferencing that pointer, at every resume, for the entire life of the coroutine. Write it out with an explicit parameter and the CP.53 violation is unmissable:

```cpp
task<void> body(const __closure& self) {   // <-- by reference. frame stores a pointer.
    auto db = co_await self.pool.acquire();
    co_await db.write(self.request.id, self.request.body);
    co_await db.commit();
}
```

The closure object is a temporary. It dies at the end of the full-expression that created it. The coroutine, in general, does not.

## Capturing by value does not fix it

The first instinct is to swap `[&]` for `[=]` or an explicit by-value list. It changes nothing about the shape of the problem:

```cpp
co_await [request] () -> task<void> {   // request is copied...
    co_await log(request.id);           // ...into the closure, not into the frame
}();
```

The copy lives in `__closure`. The frame still holds only a pointer to `__closure`. When the temporary closure is destroyed, the copy is destroyed with it, and the frame's pointer dangles just as thoroughly as before. By-value capture moves the dangling object; it does not remove the indirection.

This is why the Core Guidelines rule is blunt — **CP.51: do not use capturing lambdas that are coroutines** — and why clang-tidy ships `cppcoreguidelines-avoid-capturing-lambda-coroutines`, which fires on *any* capture list that is not empty.

## Why "immediately invoked" usually survives — and why that is the dangerous part

Here is the nuance that makes this pattern worth a talk rather than a lint rule.

Temporaries live to the end of the full-expression. And when a coroutine suspends in the middle of a full-expression, the temporaries of that full-expression are stored in *its* frame so they survive the suspension. So in the original example:

```cpp
co_await [&] () -> task<void> { /* ... */ }();
```

the closure temporary is materialised inside `handle_request`'s frame, and it lives until the `co_await` completes — which is after the inner coroutine has finished. The captures stay valid the whole time. **The strictly immediate form is fine.**

That is precisely what makes it dangerous. The pattern works, people learn it works, and then they make a small edit that looks like a refactor and is actually a lifetime change:

```cpp
// 1. Hoist it into a variable "for readability"
auto t = [&] () -> task<void> { /* ... */ }();   // closure temporary dies at this ';'
co_await t;                                       // resumes into freed memory

// 2. Fire and forget
spawn([&conn, req] () -> task<void> {             // closure dies at the ';'
    co_await conn.send(process(req));             // the task is still suspended somewhere
}());

// 3. Run several at once
co_await when_all(
    [&] () -> task<void> { co_await a(); }(),     // both closures are temporaries of this
    [&] () -> task<void> { co_await b(); }());    // full-expression — this one is actually OK,
                                                  // until someone stores the vector of tasks

// 4. Hand it to a scheduler that outlives the scope
executor.post([&] () -> task<void> { /* ... */ }());
```

Cases 1, 2 and 4 are undefined behaviour. Case 3 is fine. Nothing in the syntax distinguishes them, the compiler says nothing, and the difference is invisible to a reviewer who is reading the block for what it does rather than for when its temporary dies.

C++23 quietly removed one member of this family. `for (auto x : [&] () -> generator<int> { ... }())` was UB before P2718R0, because the closure temporary died before the first iteration; C++23 extends the lifetime of every temporary in the range-initialiser to the end of the loop. One special case fixed, in one construct, by a language change. The general problem remained.

## The C++23 fix: an explicit object parameter, by value

Deducing `this` (P0847) lets a lambda name its own closure as a real parameter. Take it **by value**:

```cpp
co_await [request, &conn] (this auto self) -> task<void> {
    co_await log(request.id);      // resolves to self.request
    co_await conn.send(ok);        // resolves to self.conn  -- still a reference!
}();
```

`self` is an ordinary by-value parameter of a coroutine, so it is copied into the coroutine frame. The captures are members of `self`, so the *frame owns them*. Inside the body you still name captures directly — the standard rewrites those id-expressions as member accesses on the explicit object parameter — but they now resolve to the frame's copy, not to a temporary in the caller's scope.

The closure temporary can die whenever it likes. The frame has its own.

This is exactly why clang-tidy's `avoid-capturing-lambda-coroutines` check does **not** flag lambdas with an explicit object parameter: the captures have been decoupled from the closure's lifetime.

## Two things `this auto self` does not fix

The check going quiet is not the same as the code being correct.

**Reference captures are copied as references.** Copying the closure into the frame copies each member. A member of reference type stays a reference to the original:

```cpp
co_await [&] (this auto self) -> task<void> {   // lint is happy
    co_await use(local);                         // 'local' is still &local
}();                                             // dangles the moment the enclosing scope goes
```

`this auto self` only helps if the captures are by value. `[&]` plus deducing `this` is a lint-clean dangle.

**Pointers are copied as pointers.** Capturing `this` copies the pointer, not the object:

```cpp
co_await [this] (this auto self) -> task<void> {
    co_await member_.flush();     // this->member_, and 'this' may be long gone
}();
```

The frame safely owns a copy of a pointer to a destroyed object. Owning your captures is a statement about the closure's members, not about what they transitively refer to. The usual coroutine lifetime discipline — the object must outlive the task, and somebody has to guarantee that — still applies.

## Making it look like a language feature

Müller's closing suggestion is to stop writing the incantation by hand. The safe form has a fixed shape, so wrap it:

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

It is a macro, with everything that implies, and the trailing `();` is still there. But it makes the by-value explicit object parameter non-optional, and it turns "did they remember `this auto self`?" from a code-review question into a grep. For a construct whose failure mode is silent, that trade is usually worth taking.

## Summary

| Form | Captures live in | Verdict |
|---|---|---|
| `co_await [&]{...}()` — awaited in the same full-expression | closure temporary, kept alive by the awaiting frame | works, but one refactor from UB |
| `auto t = [&]{...}(); co_await t;` | closure temporary, already destroyed | **UB** |
| `spawn([&]{...}())` / `post(...)` / stored task | closure temporary, already destroyed | **UB** |
| `[=]` or by-value capture list | closure temporary, already destroyed | **UB** — the copy is in the wrong object |
| `[x, y](this auto self)` | the coroutine frame | safe |
| `[&](this auto self)` | frame owns the references; referents do not | **UB** — lint-clean and still wrong |
| `[this](this auto self)` | frame owns the pointer; pointee does not | safe only if the object outlives the task |

The rules that fall out of five minutes:

1. **A coroutine frame copies parameters as declared.** References and pointers stay references and pointers. (CP.53)
2. **A lambda's implicit object parameter is a reference**, so a capturing lambda coroutine is a CP.53 violation you cannot see. (CP.51)
3. **Take the closure by value with `this auto self`** and the frame owns the captures.
4. **Capture by value as well**, or step 3 buys you nothing.
5. Turn on `cppcoreguidelines-avoid-capturing-lambda-coroutines`, and remember it stops watching the moment you add an explicit object parameter.

Sources: [talk on YouTube](https://www.youtube.com/watch?v=mF2YMIKZUMg) · [ACCU 2025 archive entry](https://accu.programmingarchive.com/video/immediately-invoked-coroutine-lambdas-in-c23-lifetime-pitfalls-and-best-practices-jonathan-muller-accu-2025-short-talks/) · [clang-tidy: cppcoreguidelines-avoid-capturing-lambda-coroutines](https://clang.llvm.org/extra/clang-tidy/checks/cppcoreguidelines/avoid-capturing-lambda-coroutines.html) · [Raymond Chen: a capturing lambda can be a coroutine, but you have to save your captures while you still can](https://devblogs.microsoft.com/oldnewthing/20211103-00/?p=105870)
