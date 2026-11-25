---
layout: single
title: "C++ - Mark the Thread Boundary with `send`, Then Hide the Pointers (Dave Rowland, C++Online 2025)"
date: 2026-11-24 18:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - concurrency
  - api-design
permalink: "2026/11/24/cpp-thread-safety-from-other-languages-dave-rowland"
---

[What Can C++ Learn About Thread Safety From Other Languages? - Dave Rowland - C++Online 2025](https://www.youtube.com/watch?v=SWmpd18QAao) ([slides](https://github.com/CppOnlineConference/CppOnline2025/blob/main/Presentations/What-can-Cpp-Learn-about-Thread-Safety-from-other-Languages.pdf), [code](https://github.com/drowaudio/scl))

Rust, Circle and Swift all make data races impossible to express. They do it by marking an **isolation boundary**: a thread may receive only values that are `send`, and may share only objects that are `sync`. C++ can spell that boundary with type traits today. But a boundary only helps if no pointer can sneak across it, and C++ has pointers everywhere. Rowland's answer is to hide them inside value types. (This is the talk Tristan Brindle recommends before his [reflection-based `sendable`](/2026/11/24/cpp-fearless-concurrency-sendable-tristan-brindle).) The scaffolding below is Rowland's `scl` library, trimmed and limited to C++23 traits:

```cpp
// scl.hpp -- C++23 send/sync, trimmed from github.com/drowaudio/scl
#include <atomic>
#include <memory>
#include <mutex>
#include <thread>
#include <type_traits>

// sync: safe to share. In C++23 only what the standard promises is race-free.
template <typename T> struct is_sync : std::false_type {};
template <typename T> struct is_sync<std::atomic<T>> : std::true_type {};
template <typename T> constexpr bool is_sync_v = is_sync<T>::value;

// No reflection: we can't look inside a closure, so any callable class is out.
template <typename T> concept callable_class = requires { &T::operator(); };

// send: safe to move to another thread. No lvalue refs, no object pointers, no lambdas.
template <typename T>
struct is_send : std::bool_constant<
    !std::is_lvalue_reference_v<T>
    && !(std::is_pointer_v<std::decay_t<T>> && !std::is_function_v<std::remove_pointer_t<std::decay_t<T>>>)
    && !callable_class<std::remove_cvref_t<T>>
    && (std::is_move_constructible_v<T> || std::is_function_v<std::remove_pointer_t<std::decay_t<T>>>)> {};
template <typename T>                                       // shared ownership: only of sync data
struct is_send<std::shared_ptr<T>> : std::bool_constant<is_sync_v<T>> {};
template <typename T> concept send = is_send<T>::value;

// P0290-style: the value is only reachable through apply(), which holds the lock.
template <typename T>
class synchronized_value {
    std::mutex mutex_;
    T value_;
public:
    template <typename... Args> explicit synchronized_value(Args&&... args)
        : value_(std::forward<Args>(args)...) {}
    friend decltype(auto) apply(auto&& fn, synchronized_value& sv) {
        std::scoped_lock lock(sv.mutex_);
        return fn(sv.value_);
    }
};
template <typename T> struct is_sync<synchronized_value<T>> : std::true_type {};

// A thread whose callable and arguments must all be send: the isolation boundary.
template <typename F, send... Args>
    requires send<std::decay_t<F>>
std::jthread safe_thread(F&& f, Args&&... args) {
    return std::jthread(std::forward<F>(f), std::forward<Args>(args)...);
}
```

## Case 1: `shared_ptr<synchronized_value<T>>` crosses the boundary

```cpp
#include "scl.hpp"
#include <print>
#include <string>
#include <vector>

void entry_point(std::shared_ptr<synchronized_value<std::string>> s, int tid) {
    apply([&](std::string& str) { str += "*"; std::println("{} {}", str, tid); }, *s);
}

static_assert(send<int> && send<std::string> && send<std::unique_ptr<int>>);
static_assert(!send<int&> && !send<const int&> && !send<int*>);
static_assert(!send<std::shared_ptr<std::string>>);                       // pointee not sync
static_assert(send<std::shared_ptr<synchronized_value<std::string>>>);    // pointee is sync
static_assert(!send<decltype([] {})>);                 // even a captureless lambda

int main() {
    auto s = std::make_shared<synchronized_value<std::string>>("Hello threads");
    std::vector<std::jthread> threads;
    for (int i = 0; i < 4; ++i)
        threads.push_back(safe_thread(entry_point, auto(s), auto(i)));    // OK: send

    // safe_thread(entry_point, s, 0);                     // error: lvalue shared_ptr& isn't send
    // safe_thread([s] { (void)s; });                      // error: lambdas are never send in C++23
}
```

It prints `Hello threads*` through `Hello threads****`, one line per thread, in whatever order the threads ran. TSan reports nothing. `auto(s)` (C++23 decay-copy) turns the lvalue into a prvalue, so the copy is what crosses. Both commented lines fail with clang's `no matching function for call to 'safe_thread'`. **There's a correction to the slides here.** Slide 39 says `shared_ptr<int>` and `shared_ptr<std::string>` are not send, but `scl`'s `is_send<shared_ptr<T>>` is only specialized for `sync T`. Every other `T` falls back to the primary template, where any move-constructible type counts as send. Rowland's own header reports `is_send_v<std::shared_ptr<std::string>> == true`. The header above fixes this by specializing for every `T` and returning `is_sync_v<T>`.

## Case 2: a leaked pointer walks straight through

A trait sees only the types that cross the boundary, not the aliases left behind. Rowland lists four holes: nested pointers, `this`, globals and leaked pointers. The last one needs no tricks at all:

```cpp
#include "scl.hpp"
#include <print>

struct Widget { int clicks = 0; };

void entry_point(std::unique_ptr<Widget> w) {
    ++w->clicks;                                          // writes w->clicks
}

int main() {
    auto owned = std::make_unique<Widget>();
    Widget* leaked = owned.get();                         // <-- a copy of the pointer stays behind

    auto t = safe_thread(entry_point, std::move(owned));  // OK: unique_ptr is send
    ++leaked->clicks;                                     // data race on the same int
    t.join();
    std::println("clicks = {}", leaked->clicks);          // UB: and the Widget is already freed
}
```

At `-O2` it prints a convincing `clicks = 2`. TSan reports `data race leak.cpp:7`, and an ASan build reports `heap-use-after-free`, because the thread's `unique_ptr` deleted the `Widget` before `main` read it. That's Rowland's point: **thread safety and lifetime safety are the same problem**. Rust's borrow checker refuses the `leaked` alias outright; C++ can only make the pointer harder to reach. C++26 reflection closes the nested-pointer and `this` holes: `is_send` can recurse into members, closures included, so lambdas no longer need a blanket ban. I ported slide 58 to the final P2996 API. On clang-p2996 the slide's verdicts hold (`node`, `[&i]`, `[this]` are rejected; `[i]` passes), but the recursion also rejects `std::string` and Case 1's own type unless they are opted in by hand. On GCC 16.2 every lambda passes, because GCC reports no closure members. libstdc++'s `shared_ptr` passes too, because slide 58 never checks base classes. [Brindle's version](/2026/11/24/cpp-fearless-concurrency-sendable-tristan-brindle) covers bases and has the same GCC caveat.

## Case 3: a copy-on-write value type has no pointer to leak

Swift's answer is to make the pointer an implementation detail. Rowland sketches metaclasses (`class person(mutex)`, `person(arc)`, `struct person(cow)`) that generate the wrapper. Metaclasses aren't in C++26, so here is roughly what `person(cow)` would expand to, written by hand:

```cpp
#include "scl.hpp"
#include <print>
#include <string>
#include <vector>

// Roughly what the proposed `struct person(cow)` metaclass would generate.
class person {
    struct data { std::string first; };
    std::shared_ptr<data> d_ = std::make_shared<data>();
    void copy_if_shared() { if (d_.use_count() > 1) d_ = std::make_shared<data>(*d_); }
public:
    std::string first_name() const { return d_->first; }        // readers share one buffer
    void set_first_name(std::string s) { copy_if_shared(); d_->first = std::move(s); }

    person* operator&() = delete;                    // no pointers to a person...
    void* operator new(std::size_t) = delete;        // ...and none on the heap
};
template <> struct is_send<person> : std::true_type {};    // the shared_ptr never escapes

void use_copy(person p, std::string name) {
    p.set_first_name(name);                          // copies first: this thread's own data
    std::println("thread: {}", p.first_name());
}

int main() {
    person p;
    p.set_first_name("Dave");
    {
        std::vector<std::jthread> threads;
        for (std::string name : {"Ann", "Bob", "Cy"})
            threads.push_back(safe_thread(use_copy, auto(p), std::move(name)));   // OK: send
    }
    std::println("main:   {}", p.first_name());     // prints Dave
}
```

Each thread prints its own name and `main` still prints `Dave`. TSan and ASan/UBSan stay quiet. Copies are cheap until someone writes, and **a write never touches data another `person` can see**. `&p` and `new person` are compile errors, but `std::addressof(p)` and plain references still work. Rowland admits that only a viral, compiler-checked "non-addressable" rule would close that gap. Hylo's mutable value semantics is the language-level version of the same idea.

## Case 4: catch races at runtime with a reader/writer count

TSan is the real detector, but it slows code down 5–15× and can't be combined with ASan, so it rarely runs on everyday builds. Rowland's lightweight alternative works per object: const member functions count as reads and non-const ones as writes, matching the standard library's own data-race guarantee for `const` calls:

```cpp
#include <atomic>
#include <chrono>
#include <cstdlib>
#include <print>
#include <thread>

struct check_state {
    std::atomic<std::size_t> num_readers{0};
    std::atomic<bool> is_writing{false};
};
[[noreturn]] void race(const char* what) { std::println("data race: {}", what); std::abort(); }

void read_started(check_state& s) {
    ++s.num_readers;                                 // publish first, then look
    if (s.is_writing) race("read during active write");
}
void write_started(check_state& s) {
    if (s.is_writing.exchange(true)) race("write during active write");
    if (s.num_readers > 0) race("write during active read");
}
void read_ended(check_state& s) { --s.num_readers; }
void write_ended(check_state& s) { s.is_writing = false; }

enum class check_type { read, write };
template <check_type T>
struct scoped_check {
    check_state& s;
    explicit scoped_check(check_state& st) : s(st) { T == check_type::read ? read_started(s) : write_started(s); }
    ~scoped_check() { T == check_type::read ? read_ended(s) : write_ended(s); }
};

// const functions are reads, non-const functions are writes.
class counter {
    int value_ = 0;
    mutable check_state check_;
public:
    int get() const { scoped_check<check_type::read> _(check_); return value_; }
    void slow_set(int v) {
        scoped_check<check_type::write> _(check_);
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        value_ = v;
    }
};

int main() {
    counter c;
    std::jthread r1([&] { for (int i = 0; i < 1000; ++i) c.get(); });   // readers overlap: fine
    std::jthread r2([&] { for (int i = 0; i < 1000; ++i) c.get(); });
    r1.join(); r2.join();
    std::println("concurrent reads: ok");

    std::jthread w([&] { c.slow_set(42); });
    std::this_thread::sleep_for(std::chrono::milliseconds(20));
    std::println("{}", c.get());                     // aborts: read during active write
}
```

It prints `concurrent reads: ok`, then `data race: read during active write`, and aborts; it behaved that way in 30 of 30 runs. The order matters: a reader increments *before* checking `is_writing`, and a writer sets `is_writing` *before* checking readers. With sequentially consistent atomics, whichever side goes second is guaranteed to see the other. Rowland would route `race()` through `contract_assert` or a `pre(...)` precondition, and attach the state to `std::` containers through Herb Sutter's extrinsic storage so the ABI doesn't change. It checks function entry and exit, not memory, so anything that returns a reference escapes it.

## Summary

| Tool | What it stops | What gets through |
|---|---|---|
| C++23 `send`/`sync` traits + `safe_thread` | lvalue refs, raw pointers, every lambda | leaked aliases, `this`, globals, nested pointers |
| C++26 reflection `send` | pointer members, `[&]`/`[this]` captures (clang) | everything on GCC's closures; `std::string` needs an opt-in |
| `synchronized_value<T>` | unlocked access | pointers you take out inside `apply` |
| copy-on-write value types | shared mutable state | references, `std::addressof` |
| reader/writer `check_state` | overlapping reads and writes at runtime | anything that escapes by reference |

- A thread-spawning API marks the isolation boundary. C++ can check it with traits, but only on the types that cross it.
- In `scl`, `shared_ptr<T>` is send for every `T`, not just sync ones. Specialize for all `T` and return `is_sync_v<T>`.
- Without borrows, thread safety needs lifetime safety, and that means hiding pointers inside value types: `synchronized_value`, arc and copy-on-write.
- Until the language can do this, a per-object reader/writer count catches races cheaply in ordinary builds, with no TSan run needed.
