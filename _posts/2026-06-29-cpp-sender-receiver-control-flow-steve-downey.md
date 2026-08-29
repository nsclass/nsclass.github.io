---
layout: single
title: "C++ - Implementing Control Flow with Sender/Receiver (Steve Downey)"
date: 2026-06-29 10:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - asynchrony
permalink: "2026/06/29/cpp-sender-receiver-control-flow-steve-downey"
---

[Steve Downey - Using the C++ Sender/Receiver Framework: Implement Control Flow for Async Processing](https://www.youtube.com/watch?v=xXncLUD-4bA)

Most introductions to C++26 [`std::execution`](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html) (P2300) stop at "here are the algorithms." Downey asks a harder question: **can you build all of structured programming out of senders?** Sequence, selection, iteration, recursion. The answer is yes, and the code is the argument.

Examples use `stdexec::` from NVIDIA's reference implementation, which mirrors `std::execution::`. Downey compiles his slide deck, so these ran.

## The model: CPS with three channels

A receiver is a continuation. In continuation-passing style, a function that would return a value instead takes a callback and passes the value forward:

```
        A -> B          // direct style
   (A, B -> R) -> R     // continuation-passing style
```

A sender is a *description* of work that will eventually call one of three channels on its receiver: **value**, **error**, or **stopped** (cancellation). Downey's summary: senders are **"three monads in a trench coat"** — one stacked over each channel.

The three monadic operations have names you already know:

| Monad | Sender algorithm | Takes a function returning… |
|---|---|---|
| `pure` / `return` | `just` | (lifts a plain value) |
| `fmap` | `then` | a **value** |
| `bind` (`>>=`) | `let_value` | a **sender** |

And senders are **lazy**. Composing builds a structure; nothing runs until `sync_wait` connects a receiver and starts it.

## Sequence

```cpp
#include <stdexec/execution.hpp>
#include <exec/static_thread_pool.hpp>

int main() {
    exec::static_thread_pool pool{8};
    auto sch = pool.get_scheduler();

    auto work = stdexec::schedule(sch)          // hook to start async work
              | stdexec::then([] {
                    std::print("hello world\n");
                    return 13;
                })
              | stdexec::then([](int arg) {
                    return arg + 42;
                });

    // Nothing has run yet. sync_wait bridges back to the synchronous world.
    auto [i] = stdexec::sync_wait(std::move(work)).value();
    std::print("{}\n", i);                       // 55
    return 0;
}
```

The brackets in `auto [i]` are because the value channel is variadic — `sync_wait` hands back a tuple of everything sent, even when that is one thing.

Each `then` is a functor map: take the value off the value channel, transform it, put the result back. **Sequencing is function composition.**

## Fork/join: `when_all`

```cpp
auto square = [](int x) { return x * x; };

auto work = stdexec::when_all(
    stdexec::on(sch, stdexec::just(0) | stdexec::then(square)),
    stdexec::on(sch, stdexec::just(1) | stdexec::then(square)),
    stdexec::on(sch, stdexec::just(2) | stdexec::then(square))
);

auto [i, j, k] = stdexec::sync_wait(std::move(work)).value();   // 0, 1, 4
```

`just` lifts a value into a sender — the constant function, the `pure` of this monad. `on` says *run this over there*, so the three branches can land on three different pool threads. Execution order is nondeterministic; **result** order is fixed by structure, so `i`, `j`, `k` always correspond to the three arguments in order.

## Selection: `let_value` is the whole point

This is where `then` runs out. To choose *which sender runs* based on a runtime value, you need bind:

```cpp
auto work = stdexec::just(i, j)
          | stdexec::let_value([=](int i, int j) {
                return tst(i > j, seven_sender, eleven_sender);
            });
```

`then` cannot do this. A function passed to `then` returns a *value*; the graph downstream is already fixed. A function passed to `let_value` returns a *sender*, chosen at execution time.

Both branches must have one type, so `tst` unifies them. Downey shows two versions:

```cpp
// Type-erasing version: works for any two senders, costs an indirection.
template <stdexec::sender L, stdexec::sender R>
auto tst(bool condition, L left, R right)
    -> any_sender_of<stdexec::set_value_t(int)>
{
    return condition ? any_sender_of<stdexec::set_value_t(int)>{left}
                     : any_sender_of<stdexec::set_value_t(int)>{right};
}

// Variant version: we know there are exactly two types, so keep them visible.
template <stdexec::sender L, stdexec::sender R>
auto tst(bool condition, L left, R right) -> variant_sender<L, R> {
    return condition ? variant_sender<L, R>{left}
                     : variant_sender<L, R>{right};
}
```

Note `stdexec::sender L` rather than `auto` — sender is a concept, and constraining it moves the error to the mistake instead of somewhere else in the program.

An attendee asks the obvious question: why not just branch inside the lambda? Downey's answer is the reason this matters:

> Because I'm building up a chain of senders. If these were more interesting, creating them as senders lets me cancel that work — whereas if I just had a branch, I can't cancel in the middle of a sender.

A plain `if` runs as ordinary synchronous code: no cancellation point, no chance to say *this branch goes on the GPU and that one uses SIMD locally*. And mechanically, you would have to `decltype` both branch expressions into one type anyway — which is exactly what `tst` is doing.

**`then` transforms values; `let_value` chooses futures.**

## Recursion: factorial

```cpp
auto fac(int n) -> any_int_sender {
    if (n == 0) {
        return stdexec::just(1);                                  // base case
    }
    return stdexec::just(n - 1)
         | stdexec::let_value([](int k) { return fac(k); })        // recurse
         | stdexec::then([n](int k) { return k * n; });            // combine
}

auto [r] = stdexec::sync_wait(fac(10)).value();                    // 3628800
```

`any_int_sender` is type-erased because recursion needs one concrete return type and the honest type here is infinite.

Downey is blunt that this is a bad factorial — "it's even more terrible than the standard recursive function." The chain is built dynamically as it runs, and `let_value` keeps the sender feeding it alive, so you accumulate the whole stack. Capturing `n` by value is what keeps this merely expensive rather than a lifetime bug; capture by reference and every prior frame must stay alive.

The point is not efficiency, it is expressiveness: sequence + selection + recursion is the Böhm–Jacopini set. Once you have those three, you have all structured control flow.

## Tree recursion becomes parallelism

```cpp
auto fib(int n) -> any_int_sender {
    if (n < 2) {
        return stdexec::just(n);
    }
    return stdexec::when_all(
               stdexec::on(default_scheduler(), fib(n - 1)),
               stdexec::on(default_scheduler(), fib(n - 2)))
         | stdexec::then([](int a, int b) { return a + b; });
}
```

Two recursive calls forked with `when_all`, joined with `then`. Downey is gleeful about how bad this is: exponential, and spreading it over threads *ruins locality* so adding threads made it slower. `fib(37)` consumed **4.8 GB**. Valgrind and ASan were both happy — it is correct, just awful.

## Iteration: fold

```cpp
// left fold over iota(1, 10000), summing with +
auto work = fold_left(std::views::iota(1, 10000), 0, std::plus<>{});
auto [sum] = stdexec::sync_wait(std::move(work)).value();   // 49995000
```

Each step uses `let_value` to inspect the accumulator and current position and produce *either* the next iteration's sender or a `just` holding the final result. Because each step is a sender, the loop can suspend, move schedulers, or be cancelled between iterations.

Downey's note on why this matters, and why you still shouldn't:

> Once you have fold you have almost every algorithm. Fold is a universal algorithm generator. It's usually the worst way of writing an algorithm — but because everything is a fold, if you can do folds you can do everything else.

It will also exhaust your heap, since the chain is allocated as it grows. A trampoline scheduler could discard completed frames as it goes.

## Backtracking: pass the failure continuation as a parameter

The most interesting example. Depth-first search takes *where to go if this subtree fails* as an argument:

```cpp
auto search_tree(auto test,               // predicate on a node
                 node* n,                 // current node
                 auto sched,              // where to run
                 stdexec::sender auto fail)   // what to do if we dead-end
    -> any_node_sender
{
    if (n == nullptr) {
        return fail;                       // dead end: take the continuation
    }
    if (test(n)) {
        return stdexec::just(n);           // found it
    }
    // Search left; if left fails, its failure continuation is "search right".
    return search_tree(test, n->left, sched,
                       search_tree(test, n->right, sched, fail));
}
```

The `fail` sender is threaded down the recursion, so at each node you already hold the sender describing where to resume. That automatically threads and linearizes the tree.

This is where CPS pays off, and it is also inversion of control — the failure policy is supplied by the caller, not baked into the algorithm.

## The other two channels

Downey stays on the value channel deliberately: the error and stopped channels work the same way, so `let_error` and `let_stopped` are bind on a different channel. What is worth knowing:

- An error need not be an exception. You can **send** one onto the error channel directly; a thrown exception is caught and placed there for you.
- Adapters cross channels in both directions, like a patch bay. His recovery example: could not reach the assigned server, move the error back onto the value channel, proceed with "I'll try the other one." `stopped_as_optional` / `stopped_as_error` translate cancellation.
- **stopped is strictly cancellation** — "I was asked to cancel, and now I'm letting you know I'm done." Not a pause, and repurposing it as a value channel misleads everyone.

Also worth noting for later: **coroutines are senders.** What a coroutine returns to hand you its eventual value *is* a sender, which is why a future `std::task` plugs straight into this framework. Asked why he did not write these examples as coroutines, Downey says he did not want to explain coroutines at the same time.

## "Can is not Should"

The closing caveat, which he repeats several times:

> Knowing that you can is not how you should do it.

Senders earn their complexity when you need **throughput** (overlapping I/O, real parallelism) or **interruptibility** (structured cancellation). For straight-line synchronous logic, ordinary code is clearer. And when you need an algorithm, write the algorithm — the general-purpose ones look complicated because they handle every corner case, and yours probably does not have to.

---

**Sources**

- [Steve Downey — Using the C++ Sender/Receiver Framework (YouTube)](https://www.youtube.com/watch?v=xXncLUD-4bA)
- [Slides: C++Now 2023 Async Control Flow — Steve Downey](https://sdowney.org/posts/index.php/2024/05/18/slides-from-cnow-2023-async-control-flow/)
- [std::execution, Sender/Receiver, and the Continuation Monad — Steve Downey](https://sdowney.org/posts/index.php/2021/10/03/stdexecution-sender-receiver-and-the-continuation-monad/)
- [P2300R10: `std::execution`](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2024/p2300r10.html)
- [NVIDIA/stdexec — reference implementation](https://github.com/NVIDIA/stdexec)
