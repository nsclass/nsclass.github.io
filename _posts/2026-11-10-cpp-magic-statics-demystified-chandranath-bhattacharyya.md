---
layout: single
title: "C++ - Magic Statics: One Acquire Load to Initialize, a Destructor After main to Pay For (Chandranath Bhattacharyya, C++Now 2026)"
date: 2026-11-10 14:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - concurrency
  - memory
permalink: "2026/11/10/cpp-magic-statics-demystified-chandranath-bhattacharyya"
---

[C++ Magic Statics Demystified - History, Internals, Pitfalls, and Optimizations - Chandranath Bhattacharyya - C++Now 2026](https://www.youtube.com/watch?v=kV6TbuRMIVg) ([slides](https://github.com/boostcon/cppnow_presentations_2026/blob/main/Presentations/Cpp_Magic_Statics_Demystified.pdf))

Before C++11, the only correct way to lazily build a shared object was double-checked locking with an atomic pointer and carefully chosen memory orders. Since C++11, a function-local `static` with a runtime initializer is thread-safe: one thread runs the initializer, the others wait, and every later call costs one acquire load. That's the good news. The bad news is the rest of the bill: a guard variable, a lock on the slow path, a destructor that runs after `main`, and on Windows a TLS slot in every thread. **The cheapest static is one the compiler can build at compile time, so it needs no guard at all.**

Everything below was compiled with Apple clang (libc++abi) at `-std=c++23 -O2` and run; GCC 15.1 results are from Compiler Explorer.

## What the compiler actually writes

On every non-Windows Clang/GCC target, the compiler lowers the static to calls into the Itanium C++ ABI. Below is the slide's lowering, written out by hand. It links against the real runtime functions, so you can run it:

```cpp
#include <cstdint>
#include <cstdio>
#include <new>
#include <string>

extern "C" int __cxa_guard_acquire(std::uint64_t*);
extern "C" void __cxa_guard_release(std::uint64_t*);
extern "C" void __cxa_guard_abort(std::uint64_t*);
extern "C" int __cxa_atexit(void (*)(void*), void*, void*);
extern "C" void* __dso_handle;

std::string ComputeName() { return "computed once, at first call"; }

// What `static const std::string name = ComputeName();` becomes (Itanium ABI).
std::uint64_t guard_for_name = 0;  // byte 0: "done" flag; rest: init state + thread id
alignas(std::string) unsigned char storage_for_name[sizeof(std::string)];

const std::string& GetName() {
  auto* guard_byte = reinterpret_cast<std::uint8_t*>(&guard_for_name);
  if (__atomic_load_n(guard_byte, __ATOMIC_ACQUIRE) == 0) {  // <-- the whole fast path
    if (__cxa_guard_acquire(&guard_for_name)) {              // 1 = this thread initializes
      try {
        new (storage_for_name) std::string(ComputeName());
        __cxa_atexit([](void* p) { static_cast<std::string*>(p)->~basic_string(); },
                     storage_for_name, &__dso_handle);       // destructor runs after main
        __cxa_guard_release(&guard_for_name);                // sets guard byte to 1, wakes waiters
      } catch (...) {
        __cxa_guard_abort(&guard_for_name);                  // next caller retries
        throw;
      }
    }
  }
  return *std::launder(reinterpret_cast<std::string*>(storage_for_name));
}

int main() {
  std::printf("%s\n", GetName().c_str());
  std::printf("guard byte = %d\n", *reinterpret_cast<std::uint8_t*>(&guard_for_name));  // prints 1
}
```

The guard is 64 bits (32 on ARM). **Byte 0 is a "done" flag, kept separate from the init-state byte**, so once initialization is complete, the fast path is one acquire load and a compare. On x86-64 that load is a plain `mov`. All the waiting happens inside `__cxa_guard_acquire`. MSVC uses Mike Burrows' epoch algorithm instead: no atomics, but it compares the guard with a thread-local epoch. The trade-offs (table adapted from the slides):

| | MSVC / clang-cl | Itanium, global mutex (macOS) | Itanium, futex (Linux) |
|---|---|---|---|
| Fast path | 1 TLS load + 1 guard load | 1 atomic acquire load | 1 atomic acquire load |
| Atomics per guard | 0 | 1 | 3 |
| Global lock + condvar | yes | yes | no |
| TLS per thread | 1 int | 0 | 0 |
| Recursive init | **deadlock** | abort (non-ARM) | abort (non-ARM) |
| Cross-static spurious wakeups | yes | yes | no |

The shared global condition variable is why the first two columns get spurious wakeups. When static C finishes initializing, the broadcast also wakes every thread still waiting on static A.

The "recursive init" row is what happens when an initializer reaches its own static again, which is undefined behaviour. libc++abi stores the initializing thread's ID in the guard and aborts with `__cxa_guard_acquire detected recursive initialization`. GCC's runtime throws `__gnu_cxx::recursive_init_error`, which ends in `terminate` (both verified). MSVC keeps no thread ID, so according to the talk, that thread just waits on itself forever.

An initializer that throws is never cached: `__cxa_guard_abort` resets the guard, and the next thread to arrive runs the initializer again. The slide's demo has four threads and a constructor that throws twice. Two threads catch the exception, two get the object, and exactly one destructor runs after `main`. I reproduced that on both Clang and GCC.

## Destruction happens after `main`, in reverse completion order

Each magic static with a non-trivial destructor registers a `__cxa_atexit` handler right after it's constructed. Those handlers and your own `std::atexit` handlers share one LIFO queue:

```cpp
#include <cstdio>
#include <cstdlib>

struct A {
  A() { std::puts("A()"); }
  ~A() { std::puts("~A()"); }
  static const A& Get() { static const A a; return a; }
};

struct B {
  B() { A::Get(); std::puts("B()"); }  // A finishes constructing before B does
  ~B() { std::puts("~B()"); }
  static const B& Get() { static const B b; return b; }
};

int main() {
  std::atexit([] { std::puts("atexit handler registered before B"); });
  B::Get();
  std::atexit([] { std::puts("atexit handler registered after B"); });
  std::puts("main returns");
}
```

```text
A()
B()
main returns
atexit handler registered after B
~B()
~A()
atexit handler registered before B
```

`A` finished constructing before `B`, so `B` is destroyed first. Your handlers fit into the same order based on when they were registered. That's the whole rule, and it's also the problem. Code that runs after `main` costs shutdown time and binary size (one destructor thunk per static), and it can touch globals that are already gone. Clang's `-Wexit-time-destructors` flags every such static.

## When nothing needs cleaning up, don't destroy it

Most process-lifetime caches don't need a destructor. The crude fix is `static const auto* p = new T(...)`, which leaks but never grows. A wrapper says the same thing more clearly:

```cpp
#include <cstdio>
#include <new>
#include <string>
#include <utility>

// A minimal absl::NoDestructor: constructs T in place, never destroys it.
template <class T>
class NoDestructor {
 public:
  template <class... Args>
  explicit NoDestructor(Args&&... args) { new (storage_) T(std::forward<Args>(args)...); }
  const T& operator*() const { return *std::launder(reinterpret_cast<const T*>(storage_)); }

 private:
  alignas(T) unsigned char storage_[sizeof(T)];  // trivially destructible wrapper
};

std::string ComputeName() { return std::string(40, 'x'); }

const std::string& GetName() {
  static const NoDestructor<std::string> name(ComputeName());  // still a magic static, no dtor
  return *name;
}

int main() { std::printf("%zu\n", GetName().size()); }  // prints 40
```

It is still a magic static, so initialization is still lazy and guarded, but it registers no `atexit` handler. Built with `-Wexit-time-destructors -Wglobal-constructors` it is clean, and ASan reports nothing (LeakSanitizer doesn't count memory still reachable from a static). In real code, use `absl::NoDestructor` or Chromium's `base::NoDestructor`. When you do need cleanup in a fixed order, the talk's suggestion is an explicit registry object on `main`'s stack (Chromium's `AtExitManager`) instead of relying on the order of exit-time destructors.

## The best magic static is one that doesn't exist

A static whose initializer is a constant expression gets constant initialization. The compiler emits no guard, no lock and no destructor. Three common types swap one-for-one:

| Runtime static | Compile-time replacement | Watch out for |
|---|---|---|
| `std::string` | `std::string_view` | not null-terminated |
| `std::vector<T>` | `std::array` returned as `std::span<const T>` | span keeps the size out of the signature |
| `std::map` / `std::set` | sorted `std::array` (Chromium's `MakeFixedFlatMap`; `std::flat_map` is `constexpr` in C++26) | fixed contents |

```cpp
#include <algorithm>
#include <array>
#include <cstdio>
#include <span>
#include <string_view>
#include <utility>

// A sorted array with binary-search lookup: a tiny stand-in for Chromium's MakeFixedFlatMap.
template <class K, class V, std::size_t N>
struct FixedFlatMap {
  std::array<std::pair<K, V>, N> items;
  constexpr const V* find(const K& key) const {
    auto it = std::ranges::lower_bound(items, key, {}, &std::pair<K, V>::first);
    return it != items.end() && it->first == key ? &it->second : nullptr;
  }
};

template <class K, class V, std::size_t N>
consteval auto MakeFixedFlatMap(std::pair<K, V> (&&items)[N]) {
  FixedFlatMap<K, V, N> map{std::to_array(std::move(items))};
  std::ranges::sort(map.items, {}, &std::pair<K, V>::first);
  return map;
}

std::string_view GetDefaultName() {
  static constexpr std::string_view kName{"this is a long string!!!"};  // was std::string
  return kName;
}

std::span<const int> GetDefaultValues() {
  static constexpr std::array kValues{1, 2, 3};  // was std::vector; span hides the 3
  return kValues;
}

constexpr const auto& GetErrorMessages() {
  static constexpr auto kMessages = MakeFixedFlatMap<int, std::string_view>(
      {{500, "Internal Server Error"}, {400, "Bad Request"}, {404, "Not Found"}});  // was std::map
  return kMessages;
}

static_assert(*GetErrorMessages().find(404) == "Not Found");  // looked up at compile time

int main() {
  std::printf("%.*s | %zu values | %s\n", int(GetDefaultName().size()), GetDefaultName().data(),
              GetDefaultValues().size(), GetErrorMessages().find(400)->data());
}
```

The "before" versions of these three functions produce three `-Wexit-time-destructors` warnings, plus four `__cxa_guard_acquire` and four `__cxa_atexit` calls in the `-O2` assembly. This file has **zero of each**, and the `static_assert` shows the map lookup works at compile time. The same file compiles on GCC 15.1 and MSVC. Two details matter: a `static constexpr` local inside a `constexpr` function is legal only since C++23, and the return type is `auto` because the map's type includes `N`. The slides use the same tricks on user types: `std::string` members become `std::string_view`, and a `std::vector` member becomes `std::initializer_list`, which works only for file-local tables because it doesn't own its backing array.

## Summary

| Form | Init cost after first call | Exit-time cost | Verdict |
|---|---|---|---|
| Magic static, non-trivial dtor | 1 acquire load (Itanium) / TLS + load (MSVC) | `atexit` thunk after `main` | fine for lazy, thread-shared state |
| Magic static + `NoDestructor` / leak | same | none | default for process-lifetime caches |
| `static constexpr` / `constinit` | none (no guard) | none | use it whenever the data is known at build time |

- A magic static is compiler-generated double-checked locking. An initializer that throws is retried by the next caller. Once initialized, it costs one acquire load (Itanium) or a TLS read plus a load (MSVC). Recursive initialization aborts on Clang and GCC and deadlocks on MSVC.
- Destructors run after `main`, in reverse order of when construction *completed*, mixed with `atexit` handlers in the same LIFO queue.
- Turn on `-Wexit-time-destructors` and `-Wglobal-constructors`. Fix the warnings with `string_view`, `array` + `span`, sorted-array maps, or `NoDestructor` when the data really is dynamic.
- If a slow initializer would end up on the UI thread, don't use a magic static at all. Initialize it eagerly or on a background thread.
