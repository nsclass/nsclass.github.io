---
layout: single
title: "C++ - A Reflected `sendable` Concept Rejects Racy Thread Captures, Until the Spawning Thread Cheats (Tristan Brindle, ACCU 2026)"
date: 2026-11-24 14:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - concurrency
  - reflection
permalink: "2026/11/24/cpp-fearless-concurrency-sendable-tristan-brindle"
---

[Fearless Concurrency in C++ - Tristan Brindle - ACCU 2026](https://www.youtube.com/watch?v=-FP6tLlCxWE) ([slides](https://github.com/Digital-Medium/ACCU-On-Sea-Slides-2026/blob/main/Presentations/Fearless_Concurrency_in_Cpp.pdf), [code](https://github.com/tcbrindle/safer_concurrency))

Safe Rust can't have data races. It gets there with three tools: the `Send`/`Sync` marker traits, lock-owning types like `Mutex<T>`, and the borrow checker. C++ has no borrow checker, but C++26 reflection can provide the first two. **A `sendable` concept derived by reflection turns "this lambda captures a mutable reference" into a compile error at thread launch.** What it can't stop is the thread that does the spawning.

## Send + Sync collapsed into one `sendable`

In Rust, `Send` means a type is safe to pass *by value* to another thread, and `Sync` means it is safe to share *by const reference*. Brindle merges the two into a single `sendable` concept. Only a few types are Send but not Sync, and `std::unique_ptr` is the main one: a `const unique_ptr` still lets you mutate the pointee. C++26 `std::indirect` covers that case with deep const. Here is how the implementation below classifies common types. The first column is the talk's (table adapted from the slides); the second is what both reflection compilers actually report:

| Type | Talk | `sendable` |
|---|---|---|
| `int`, `std::vector<int>`, `std::string_view` | ✅ | ✅ |
| `std::span<int>` | ❌ mutable view | ❌ |
| `std::span<int const>` | ✅ | ✅ |
| `std::unique_ptr<int>` | Send only | ❌ |
| `std::shared_ptr<int>` | ❌ unsynchronised pointee | ❌ |
| `struct Person { std::string name; int age; }` | ✅ | ❌ in the repo, **✅ only with a `std::string` opt-in** |
| same, with `mutable std::string name` | Send only | ❌ |

The `Person` row is a correction to the slides. `std::string` stores a non-const `char*`, and Brindle's repo only opts `std::vector` in by hand, so `Person` is rejected. I checked this against the repo's own header on GCC 16.2. The header below adds a `basic_string` opt-in.

The rules mirror how Rust derives auto traits. Values are sendable. Pointers and references are sendable only when they point to const, sendable data. A class is sendable if its bases and members are, with no `mutable` members, and it must be `final` if it is polymorphic. Every listing below includes this header:

```cpp
// sendable.hpp -- trimmed from github.com/tcbrindle/safer_concurrency
#include <meta>
#include <thread>
#include <type_traits>
#include <string>
#include <utility>
#include <vector>

template <typename T> consteval bool is_sendable_impl();
template <typename T> constexpr bool is_sendable_v = is_sendable_impl<T>();
template <typename T> concept sendable = is_sendable_v<T>;

template <typename T>
consteval bool is_sendable_impl()
{
    using namespace std::meta;
    constexpr auto info = ^^T;

    if constexpr (not is_complete_type(info)) return false;
    if constexpr (is_const_type(info)) return is_sendable_v<typename[:remove_const(info):]>;
    if constexpr (is_fundamental_type(info) || is_enum_type(info)) return true;
    if constexpr (is_member_pointer_type(info)) return false;

    // T* and T& are sendable only if T is const and sendable (or a function)
    if constexpr (is_pointer_type(info) || is_reference_type(info)) {
        constexpr auto to = is_pointer_type(info) ? remove_pointer(info)
                                                  : remove_reference(info);
        if constexpr (is_function_type(to)) return true;
        else return is_const_type(to) && is_sendable_v<typename[:remove_const(to):]>;
    }

    if constexpr (is_class_type(info)) {
        if constexpr (is_polymorphic_type(info) && not is_final_type(info)) return false;
        constexpr auto ctx = access_context::unchecked();
        // GCC 16 shows no members for closures: state we can't see is not sendable
        constexpr std::size_t visible = nonstatic_data_members_of(info, ctx).size()
                                      + bases_of(info, ctx).size();
        if constexpr (visible == 0 && not std::is_empty_v<T>) return false;
        template for (constexpr auto base : define_static_array(bases_of(info, ctx)))
            if constexpr (not is_sendable_v<typename[:type_of(base):]>) return false;
        template for (constexpr auto m : define_static_array(nonstatic_data_members_of(info, ctx))) {
            if constexpr (is_mutable_member(m)) return false;          // const isn't const
            if constexpr (not is_sendable_v<typename[:type_of(m):]>) return false;
        }
        return true;
    }
    return false;
}

// Owning containers hold raw T* members, so they opt in by hand.
template <typename T, typename A>
constexpr bool is_sendable_v<std::vector<T, A>> = is_sendable_v<T>;
template <typename C, typename Tr, typename A>                   // not in the repo
constexpr bool is_sendable_v<std::basic_string<C, Tr, A>> = true;

template <typename Fn, typename... Args>
    requires sendable<std::decay_t<Fn>> && (sendable<std::decay_t<Args>> && ...)
[[nodiscard]] auto spawn_thread(Fn&& fn, Args&&... args) -> std::jthread
{
    return std::jthread(std::forward<Fn>(fn), std::forward<Args>(args)...);
}

// Run fn2 on a new thread and fn1 on this one; both must be sendable.
template <typename Fn1, typename Fn2>
    requires sendable<std::decay_t<Fn1>> && sendable<std::decay_t<Fn2>>
void in_parallel(Fn1&& fn1, Fn2&& fn2)
{
    auto thread = spawn_thread(std::forward<Fn2>(fn2));
    auto{fn1}();
    thread.join();
}
```

**`spawn_thread` constrains the callable as well as the arguments.** A lambda is just a class whose members are its captures, so the same reflection walk checks every capture with no extra code. The `visible == 0` guard is my addition; the GCC section below explains why it's needed.

## Case 1: const views pass, a mutable capture is rejected

```cpp
#include "sendable.hpp"
#include <print>

struct Person { std::string name; int age; };

int main() {
    std::string str = "Hello";

    auto t1 = spawn_thread([](auto sv) { std::println("{}", sv); },
                           std::string_view(str));                // OK: const view
    t1.join();

    auto t2 = spawn_thread([p = Person{str, 42}] { std::println("{} {}", p.name, p.age); });
    t2.join();                                                    // OK: owned copy

    // auto t3 = spawn_thread([&str] { str = "goodbye"; });       // error: no matching function for call to 'spawn_thread'
}
```

It prints `Hello` and `Hello 42`. Uncomment `t3` and clang-p2996 rejects it, because the closure's `std::string&` member is a reference to non-const data. This is the slide's "moment of truth", and it is the class of bug Rust's `thread::spawn` rejects.

## Case 2: the spawning thread can still race

```cpp
#include "sendable.hpp"
#include <print>
#include <span>

int main() {
    std::vector<int> vec{1, 2, 3, 4, 5};

    auto thread = spawn_thread([](auto span) { std::println("{}", span); },
                               std::span<int const>(vec));   // sendable: read-only view

    vec.resize(100);   // <-- the spawning thread frees the buffer the view points at
    thread.join();
}
```

Everything passed to the new thread is read-only, so the constraint is satisfied. But `main` still owns `vec` and reallocates it while the worker reads it. On Compiler Explorer, both compilers print different garbage on each run, e.g. `[75119, 0, -1665943680, 2109129641, 5]`. Locally, an ASan build reports **`heap-use-after-free`: a read in thread T1 of memory freed by thread T0**. Rust's borrow checker stops this by freezing `vec` while a shared borrow is alive. C++ has nothing like that, so `sendable` checks only one side of the handoff.

## Case 3: `in_parallel` puts the spawning thread under the same rule

The fix is to stop giving the caller a raw thread handle. `in_parallel(fn1, fn2)` runs `fn2` on a new thread and `fn1` on the current one, then joins. Both closures must be `sendable`, so whatever the current thread does before the join is checked too:

```cpp
#include "sendable.hpp"
#include <print>
#include <span>

int main() {
    std::vector<int> vec{1, 2, 3, 4, 5};

    // in_parallel([&vec] { vec.resize(100); },                  // error: no matching function for call to 'in_parallel'
    //             [span = std::span<int const>(vec)] { std::println("{}", span); });

    in_parallel([span = std::span<int const>(vec)] { std::println("sum {}", span[0] + span[4]); },
                [span = std::span<int const>(vec)] { std::println("{}", span); });
    vec.resize(100);   // fine: both threads have finished
}
```

It prints `sum 6` and `[1, 2, 3, 4, 5]` (the order of the two lines can vary). The rejected version is Case 2's bug. This is stricter than it needs to be: the current thread can't mutate *anything* captured, even data no worker touches. That's the price of not having a borrow checker. Brindle calls this `fork` on the slides; the repo names it `in_parallel`.

## Sharing mutable state: `synchronized<T>`

Mutable data can be shared if every access goes through a lock. As with Rust's `Mutex<T>`, bundle the value with its mutex so the only way in is with the lock held. The type has a `mutable` mutex member, so it opts in by hand:

```cpp
#include "sendable.hpp"
#include <mutex>
#include <print>

// A value bundled with its mutex: the only way in is with the lock held.
template <typename T>
class synchronized {
    T value_;
    mutable std::mutex mutex_;   // mutable member => opted in by hand below
public:
    explicit synchronized(T v) : value_(std::move(v)) {}
    auto with_lock(auto fn) { std::scoped_lock lock(mutex_); return fn(value_); }
};
template <typename T> constexpr bool is_sendable_v<synchronized<T>&> = sendable<T>;

int main() {
    synchronized<int> counter(0);
    auto work = [&counter] { for (int i = 0; i < 100'000; ++i) counter.with_lock([](int& n) { ++n; }); };

    in_parallel(work, work);                                   // OK: captures synchronized<int>&
    std::println("{}", counter.with_lock([](int n) { return n; }));   // prints 200000

    // int raw = 0;
    // in_parallel([&raw] { ++raw; }, [&raw] { ++raw; });      // error: no matching function for call to 'in_parallel'
}
```

A by-reference capture of `synchronized<int>` is allowed, but one of a plain `int` is not. Delete the opt-in line and `work` is rejected too. The repo's version also offers an `access()` guard that you can destructure; it follows the same idea as `boost::synchronized_value` and `folly::Synchronized`.

## GCC 16 can't see lambda captures

All of the above was compiled on Compiler Explorer's clang-p2996 (`-std=c++26 -freflection-latest`), the compiler Brindle demoed on. GCC 16.2 and GCC trunk (`-std=c++26 -freflection`) compile the same header, but **report zero non-static data members for every closure type**:

| Closure | clang-p2996 members | GCC 16.2 members |
|---|---|---|
| `[&str] { str = "x"; }` | 1 | 0 |
| `[str] { }` | 1 | 0 |
| `[p = &x] { ++*p; }` | 1 | 0 |

Without the `visible == 0` guard, every capturing lambda is therefore `sendable` on GCC, and Case 1's `[&str]` mutation compiles silently. The standard explicitly leaves it unspecified whether by-reference captures become members, so this isn't simply a GCC bug. With the guard, GCC errs the other way: any capturing lambda is rejected, even `[p = Person{...}]`, and only captureless lambdas with explicit arguments get through. Brindle's repo has no such guard. **On GCC, its check of captured state silently does nothing.**

## Summary

| Form | Behaviour | Verdict |
|---|---|---|
| `spawn_thread(f, std::string_view(s))` | const view passed as an argument | compiles, safe |
| `spawn_thread([&s] { s = ...; })` | mutable reference captured | rejected (clang); **accepted without the guard on GCC** |
| `spawn_thread(f, span<int const>(v)); v.resize(...)` | spawning thread mutates shared data | compiles, **heap-use-after-free** |
| `in_parallel([&v] {...}, ...)` | current thread checked as well | rejected |
| `in_parallel(work, work)` capturing `synchronized<int>&` | access only under the lock | compiles, prints 200000 |

- Reflection can derive Rust's auto-trait rules for a single `sendable` concept, so most types need no annotation. Owning containers that hold raw `T*`, such as `vector` and `string`, still need an opt-in.
- Constraining the *callable*, not just the arguments, is what catches captures, because a closure is just a class.
- A thread-spawning API can only check the new thread. Structured APIs like `in_parallel` that also constrain the spawning thread close the remaining gap, at the cost of being too strict.
- Whether reflection can see closure members is unspecified, and GCC 16 says it can't. Fail closed when you can't see a type's state.
- Globals, `const_cast` and `mutable` caches still bypass all of this. It reduces data races; it doesn't rule them out the way Rust does.
