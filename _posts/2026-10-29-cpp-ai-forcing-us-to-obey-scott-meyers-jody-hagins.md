---
layout: single
title: "C++ - One Right Way to Call It: Interfaces Neither Humans Nor AI Can Misuse (Jody Hagins, C++Now 2026)"
date: 2026-10-29 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - api-design
  - ai
permalink: "2026/10/29/cpp-ai-forcing-us-to-obey-scott-meyers-jody-hagins"
---

[AI is Forcing us to Obey Scott Meyers - Jody Hagins - C++Now 2026](https://www.youtube.com/watch?v=CiaZq4kCH08) ([slides](https://github.com/boostcon/cppnow_presentations_2026/blob/main/Presentations/AI_is_Forcing_us_to_Obey_Scott_Meyers.pdf))

Scott Meyers' rule is to make interfaces easy to use correctly and hard to use incorrectly. Hagins argues that with AI generating code, the rule is now mandatory: **when exactly one call compiles, humans and models both get it right**. When several calls compile and some of them are wrong, a model will eventually write one of the wrong ones. The compiler is the one reviewer that checks every line, so make misuse a compile error.

## 24 ways to call `process`, and all of them compile

```cpp
#include <cstdint>
#include <print>

void process(std::uint64_t bid_price, std::uint64_t ask_price,
             std::uint32_t bid_qty, std::uint32_t ask_qty)
{
    std::println("bid {}@{}  ask {}@{}", bid_qty, bid_price, ask_qty, ask_price);
}

int main()
{
    std::uint64_t bidp = 100000, askp = 100100;
    std::uint32_t bidq = 100, askq = 200;

    process(bidp, askp, bidq, askq);   // right
    process(askp, bidp, askq, bidq);   // crossed book, compiles silently
    process(bidq, askq, bidp, askp);   // prices narrowed into uint32 params, compiles silently
}
```

With four arguments there are 4! = 24 orders, and every one compiles cleanly under `-Wall -Wextra`. `-Werror -Wconversion` rejects any order that puts a 64-bit price into a 32-bit quantity, but that still leaves 4. One of them is the crossed book above.

## Strong types get you to 4; semantic types get you to 1

I compiled all 24 orders against each version of the signature (Clang 21, `-std=c++23`):

| Parameters | Orders that compile | with `-Werror -Wconversion` |
|---|---|---|
| `uint64_t, uint64_t, uint32_t, uint32_t` | 24 | 4 |
| `Price, Price, Quantity, Quantity` | 4 | 4 |
| `BidPrice, AskPrice, BidQuantity, AskQuantity` | **1** | **1** |

`Price` and `Quantity` only buy you what `-Wconversion` already did. The types have to carry the *meaning* (bid vs. ask), not just the unit:

```cpp
#include <cstdint>
#include <print>
#include <utility>

enum class BidPrice    : std::uint64_t {};
enum class AskPrice    : std::uint64_t {};
enum class BidQuantity : std::uint32_t {};
enum class AskQuantity : std::uint32_t {};

void process(BidPrice bid_price, AskPrice ask_price,
             BidQuantity bid_qty, AskQuantity ask_qty)
{
    std::println("bid {}@{}  ask {}@{}", std::to_underlying(bid_qty), std::to_underlying(bid_price),
                 std::to_underlying(ask_qty), std::to_underlying(ask_price));
}

int main()
{
    BidPrice bidp{100000};
    AskPrice askp{100100};
    BidQuantity bidq{100};
    AskQuantity askq{200};

    process(bidp, askp, bidq, askq);       // the only order that compiles
    // process(askp, bidp, askq, bidq);    // error: no matching function for call to 'process'
    // BidPrice oops{bidq};               // error: cannot initialize BidPrice with BidQuantity
}
```

Hagins' advice is to wrap values in their semantic types **where they enter the system**, for example while decoding the wire format. After that they stay typed for free, while putting types on naked values later means touching every call site.

## `std::string::replace`: one call, two meanings

The standard library has the same problem. `basic_string::replace` has 14 overloads, and two of them take the same four arguments and do different things:

```cpp
#include <print>
#include <string>

int main()
{
    std::string const with{"abcdef"};
    std::string s1 = "XYZ", s2 = "XYZ";

    s1.replace(0, 1, with, 2);       // 4th arg is pos2: take with[2..]
    s2.replace(0, 1, "abcdef", 2);   // 4th arg is n2: take the first 2 chars

    std::println("{}", s1);   // prints cdefYZ
    std::println("{}", s2);   // prints abYZ
}
```

With a `std::string` the fourth argument is a start position (`pos2`). With a string literal it is a length (`n2`). Swapping one argument type for a near-equivalent changes the result, and nothing warns.

## `bool` accepts almost anything

```cpp
#include <print>
#include <string_view>

int foo(bool b) { return b * 42; }
int foo(std::string_view) { return 99; }

int main()
{
    std::println("{}", foo("false"));                  // prints 42: const char* -> bool beats -> string_view
    std::println("{}", foo([] { return false; }));     // prints 42: lambda -> function pointer -> bool
}
```

A string literal converts to `bool` (a standard conversion), which beats `string_view` (a user-defined conversion). A non-capturing lambda converts to a function pointer and then to `true`, so a forgotten `()` on an immediately invoked lambda still compiles. Clang's `-Wall` (`-Wpointer-bool-conversion`) and GCC's `-Wall` (`-Waddress`) do flag the lambda case. Neither says anything about `foo("false")`.

The fix is a `Bool` type that nothing converts to implicitly. The talk generates one with Hagins' [Atlas](https://github.com/jodyhagins/Atlas) tool; this is a hand-written equivalent:

```cpp
// bool.hpp
#pragma once
#include <concepts>

class Bool {                                   // a strong bool: nothing converts to it implicitly
    bool value_ = false;
public:
    static Bool const yes, no;
    constexpr explicit Bool(std::same_as<bool> auto b) : value_(b) {}   // only an actual bool
    constexpr explicit operator bool() const { return value_; }          // only in if / && / !
    friend constexpr bool operator==(Bool, Bool) = default;
};
inline constexpr Bool Bool::yes{true}, Bool::no{false};
```

```cpp
#include "bool.hpp"
#include <print>
#include <string_view>

int foo(Bool b) { return b ? 42 : 0; }
int foo(std::string_view) { return 99; }

int main()
{
    std::println("{}", foo("false"));          // prints 99
    std::println("{}", foo(Bool::yes));        // prints 42
    // foo([] { return false; });              // error: no matching function for call to 'foo'
    // foo(1);                                 // error: no matching function for call to 'foo'
}
```

## `std::vector`'s constructors depend on the brackets

```cpp
#include <print>
#include <string>
#include <vector>

int main()
{
    std::vector<int> a(100, 0);           // 100 zeros
    std::vector<int> b{100, 0};           // two elements: 100, 0
    std::vector<int> u{3};                // one element: 3
    std::vector<std::string> v{3};        // three empty strings
    std::println("{} {} {} {}", a.size(), b.size(), u.size(), v.size());   // prints 100 2 1 3
}
```

`size_t` and `int` convert into each other, and braces prefer the `initializer_list` constructor whenever it is viable. The result: `(100, 0)` and `{100, 0}` build different vectors, and `{3}` means "one element" for `int` but "three elements" for `std::string`. The slides wrap `std::vector` so that each meaning has its own spelling:

```cpp
#include "bool.hpp"
#include <cstddef>
#include <initializer_list>
#include <print>
#include <string>
#include <utility>
#include <vector>

enum class VectorSize : std::size_t {};
struct InitList { explicit InitList() = default; };
inline constexpr InitList init_list{};

template <typename T>
requires (not std::same_as<bool, std::remove_cv_t<T>>)   // no Vector<bool>
class Vector {
    std::vector<T> unsafe;
public:
    using size_type = VectorSize;

    explicit Vector(size_type n, T const & value = T()) : unsafe(std::to_underlying(n), value) {}
    explicit Vector(InitList, std::initializer_list<T> il) : unsafe(il) {}

    [[nodiscard]] Bool is_empty() const { return Bool(unsafe.empty()); }
    [[nodiscard]] size_type size() const { return size_type(unsafe.size()); }
    [[nodiscard]] T value_at(size_type i) const { return unsafe.at(std::to_underlying(i)); }
};

int main()
{
    Vector<int> a(VectorSize{100}, 0);              // 100 zeros, and it says so
    Vector<int> b(init_list, {100, 0});             // two elements, and it says so
    Vector<std::string> v(VectorSize{3});
    // Vector<int> u{3};                            // error: no matching constructor
    // Vector<int> c(100, 0);                       // error: no matching constructor
    // Vector<bool> flags(VectorSize{8});           // error: constraints not satisfied
    std::println("{} {} {}", std::to_underlying(a.size()), std::to_underlying(b.size()),
                 v.is_empty() ? "empty" : "not empty");   // prints 100 2 not empty
}
```

The size is a `VectorSize`, so it can't be confused with an element. An initializer list needs an explicit `init_list` tag. `Vector<bool>` is rejected by a constraint, and `is_empty()` returns `Bool`.

## Beyond call sites

Two more parts of the talk follow from the same rule. **Don't return pointers, references or iterators**, because their lifetime isn't managed. The slides' `SlotMap` returns versioned keys instead, and its `use(key, callback)` only lends the element inside the callback, so a stale key becomes a checked "not found" instead of a use-after-free.

The last third of the talk applies the idea to architecture: Dennis Ritchie's STREAMS, rebuilt at compile time as small modules that each handle one message type and pass on everything else. Hagins found that models write these small modules reliably; the slides show a MOLD feed decoder built that way.

## Summary

| Interface | Wrong calls that compile | Fix |
|---|---|---|
| `process(uint64_t, uint64_t, uint32_t, uint32_t)` | 23 (3 with `-Wconversion`) | one semantic type per parameter |
| `string::replace(pos, n, x, k)` | `k` means `pos2` or `n2` depending on `x` | separate, named operations |
| `foo(bool)` | string literals, pointers, lambdas | a `Bool` with an explicit constructor |
| `vector<int>{3}` vs `(3)` | both, with different meanings | a strong size type and a tagged list constructor |

- **Count the calls that compile.** If more than one order or spelling compiles, assume one day someone, human or model, will use the wrong one.
- **Strong types aren't enough; make them semantic.** `Price` stops a quantity mix-up; `BidPrice` stops a bid/ask mix-up.
- **Implicit conversions are the main way wrong calls get in** (`bool`, `size_t`/`int`, `initializer_list`). Turn on `-Werror -Wconversion`, and remove the conversions from your own types.
- **Make the compiler your first test.** If a misuse can't compile, no reviewer, human or model, has to catch it.
