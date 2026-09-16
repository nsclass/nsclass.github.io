---
layout: single
title: "C++ - C++23's Quiet Features Fix Everyday Traps (Nicolai Josuttis, ACCU on Sea 2026)"
date: 2026-09-13 14:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - ranges
  - api-design
permalink: "2026/09/13/cpp-taming-cpp23-nicolai-josuttis"
---

[Taming C++23 - The Things About C++23 You Do Not Know - Nicolai M. Josuttis - ACCU on Sea 2026](https://www.youtube.com/watch?v=IVee1JXbrQE) ([slides](https://github.com/Digital-Medium/ACCU-On-Sea-Slides-2026))

Most of C++23's lesser-known additions fix traps that earlier standards left in ordinary code: the wrong constructor, a view that won't go into a vector, an argument that aliases what it modifies, a `const` overload written twice. This post covers six items from the talk, and every listing compiles and runs on Apple clang 21.

## `mdspan`: two indexes, and sizes in the type only where they vary

```cpp
#include <cstddef>
#include <mdspan>
#include <print>

using std::dynamic_extent, std::extents, std::mdspan;

void print(auto m) {
    for (std::size_t r = 0; r < m.extent(0); ++r) {
        for (std::size_t c = 0; c < m.extent(1); ++c)
            std::print("{:3}", m[r, c]);        // <-- two indexes, one operator[]
        std::println();
    }
}

int main() {
    int data[12] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12};

    mdspan rows{data, 3, 4};                                  // 3 rows of 4, both sizes at runtime
    mdspan<int, extents<std::size_t, dynamic_extent, 4>> r{data, 3};  // row length in the type
    mdspan<int, extents<std::size_t, 3, 4>> fixed{data};      // everything in the type

    std::println("{} {} {}", sizeof(rows), sizeof(r), sizeof(fixed));  // prints 24 16 8

    print(rows);                                              // 1 2 3 4 / 5 6 7 8 / ...
    print(mdspan<int, std::dextents<std::size_t, 2>, std::layout_left>{data, 3, 4});  // 1 4 7 10 / ...
}
```

`m[r, c]` is the new C++23 multidimensional subscript operator, and your own classes can have one too. **Each static extent is one less member**: a fully fixed `mdspan` is only a pointer. The layout policy is part of the declaration, so code that handles row-major and column-major data differs only in that one line.

## `std::expected` chains the way `optional` does

```cpp
#include <charconv>
#include <expected>
#include <limits>
#include <print>
#include <string>

std::expected<int, std::string> to_int(const std::string& s) {
    int value{};
    auto [end, ec] = std::from_chars(s.data(), s.data() + s.size(), value);
    if (ec != std::errc{} || end != s.data() + s.size()) return std::unexpected("not a number: " + s);
    return value;
}

std::expected<unsigned, std::string> square(int i) {
    unsigned long long sq = 1ULL * i * i;
    if (sq > std::numeric_limits<unsigned>::max()) return std::unexpected("overflow: " + std::to_string(i));
    return static_cast<unsigned>(sq);
}

int main() {
    for (std::string input : {"12", "abc", "70000"}) {
        auto r = to_int(input).and_then(square)            // string -> int -> unsigned
                              .transform([](unsigned u) { return u + 1; });
        if (r) std::println("ok:    {}", *r);              // prints ok:    145
        else   std::println("error: {}", r.error());       // prints error: not a number: abc
    }                                                      //        error: overflow: 70000
}
```

`optional` tells you *that* something failed, and `expected` also carries *why*. `and_then` skips the remaining steps after the first error, and the value type can change at each step. **The error type must stay the same** across the chain.

## Braces pick the wrong constructor, and `from_range` says what you mean

```cpp
#include <array>
#include <print>
#include <vector>

int main() {
    std::array data{47, 11, 8, 15};

    std::vector v1(data.begin(), data.end());    // vector<int>, 4 elements
    std::vector v2{data.begin(), data.end()};    // <-- vector<iterator>, 2 elements

    std::println("{} {}", v1.size(), v2.size()); // prints 4 2
    // std::println("{}", v2);                   // error: iterators are not formattable

    std::vector v3(std::from_range, data);       // C++23: says what it means
    std::println("{}", v3);                      // prints [47, 11, 8, 15]
}
```

With class template argument deduction, braces prefer the `initializer_list` constructor, so `v2` holds two iterators. On libc++ that's a `vector<int*>`, and the first sign of trouble is a formatter error one line later. The `std::from_range` tag leaves no room for that.

The tag also fixes a problem that is worse:

```cpp
#include <print>
#include <ranges>
#include <string>
#include <vector>

namespace vw = std::views;

int main() {
    auto v = vw::iota(1, 100)
           | vw::filter([](int i) { return i % 3 == 0; })
           | vw::drop(3)
           | vw::take(8)
           | vw::transform([](int i) { return std::to_string(i) + "s"; });

#ifdef CXX20_WAY
    std::vector<std::string> coll(v.begin(), v.end());     // error: begin() and end() differ in type
#endif
    std::vector<std::string> coll(std::from_range, v);     // C++23: fine
    auto copy = v | std::ranges::to<std::vector>();        // same thing, as a pipeline step

    std::println("{}", coll);   // prints ["12s", "15s", "18s", "21s", "24s", "27s", "30s", "33s"]
    std::println("{}", copy == coll);                      // prints true
}
```

The iterator-pair constructor dates from C++98 and needs `begin()` and `end()` to have the same type. `take` over a non-random-access range (here the output of `filter`) returns a sentinel for `end()`, so its end type differs. **Remove either `filter` or `take` and the iterator-pair version compiles again**, so whether it builds depends on which views are in the pipeline. `from_range` doesn't care.

## `views::zip` sorts parallel containers together

```cpp
#include <algorithm>
#include <print>
#include <ranges>
#include <string>
#include <tuple>
#include <vector>

int main() {
    std::vector<std::string> first{"Brad", "Tina", "James"};
    std::vector<std::string> last {"Pitt", "Turner", "Dean"};

    std::ranges::sort(std::views::zip(first, last),       // elements are tuple<string&, string&>
                      [](const auto& a, const auto& b) {
                          return std::get<1>(a) < std::get<1>(b);  // order by last name
                      });

    std::println("{}", first);   // prints ["James", "Brad", "Tina"]
    std::println("{}", last);    // prints ["Dean", "Pitt", "Turner"]
}
```

The zip's elements are **tuples of references**, so when `sort` swaps an element it swaps the underlying strings in both vectors. Neither vector is copied.

## `auto(x)`: pass a copy when the argument aliases the target

```cpp
#include <print>
#include <string>
#include <vector>

void replace_prefix(std::vector<std::string>& coll,
                    const std::string& prefix, const std::string& replacement) {
    for (auto& s : coll)
        if (s.starts_with(prefix))
            s.replace(0, prefix.size(), replacement);
}

int main() {
    std::vector<std::string> a{"tmp", "tmp/a", "tmp/b"};
    replace_prefix(a, a[0], ".");         // <-- prefix aliases a[0], which becomes "." first
    std::println("{}", a);                // prints [".", "tmp/a", "tmp/b"]

    std::vector<std::string> b{"tmp", "tmp/a", "tmp/b"};
    replace_prefix(b, auto(b[0]), ".");   // C++23: pass a temporary copy
    std::println("{}", b);                // prints [".", "./a", "./b"]
}
```

This isn't UB, and the sanitizers stay quiet. It's simply wrong output, because the prefix changes during the loop. `auto(x)` gives you a prvalue copy in place, without a named temporary. A `string_view` parameter has the same problem, since it is a reference too.

## Deducing `this`: one overload instead of two, and lambdas that recurse

```cpp
#include <cstddef>
#include <print>
#include <vector>

class grid {
    std::size_t cols_;
    std::vector<int> cells_;
public:
    grid(std::size_t rows, std::size_t cols) : cols_{cols}, cells_(rows * cols) {}

    decltype(auto) operator[](this auto&& self, std::size_t r, std::size_t c) {  // one overload...
        return self.cells_[r * self.cols_ + c];   // ...int& or const int&, depending on self
    }
};

int main() {
    grid g{2, 3};
    g[1, 2] = 42;                                 // non-const: returns int&

    const grid& cg = g;
    std::println("{}", cg[1, 2]);                 // const: returns const int&, prints 42
    // cg[1, 2] = 0;                              // error: assigning to const int&

    auto fib = [](this auto self, int n) -> int { // the lambda finally has a name for itself
        return n < 2 ? n : self(n - 1) + self(n - 2);
    };
    std::println("{}", fib(20));                  // prints 6765
}
```

An explicit object parameter turns the implicit `*this` into a deduced template parameter, so `const` and non-`const` access become a single function. For a lambda, `self` is the closure. That replaces the old `std::function` forward-declaration workaround, and a copied lambda still calls its own copy.

## Summary

| Trap | C++23 fix |
|---|---|
| `vector{b, e}` deduces `vector<iterator>` | `std::vector v(std::from_range, r)` |
| iterator-pair constructor rejects non-common views | `from_range` / `ranges::to` |
| nested `if`s around fallible steps | `expected::and_then` / `transform` |
| hand-written index math for 2-D data | `mdspan` + `m[r, c]` |
| sorting parallel containers | `ranges::sort(views::zip(a, b), ...)` |
| argument aliases what the function modifies | `auto(x)` |
| duplicated `const`/non-`const` overloads | `this auto&& self` |

- Construct containers from ranges with `std::from_range`. It avoids the brace trap and the sentinel trap at once.
- Use `expected` when the caller needs the reason for a failure, and chain the calls rather than nesting `if`s.
- When an argument might alias the object being modified, pass `auto(x)`.
- Deducing `this` is mostly for library writers, except for recursive lambdas, which anyone can use.
