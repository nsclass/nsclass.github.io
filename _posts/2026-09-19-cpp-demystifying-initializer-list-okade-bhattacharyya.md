---
layout: single
title: "C++ - std::initializer_list is a view of a temporary const array (Okade & Bhattacharyya, ACCU on Sea 2026)"
date: 2026-09-19 14:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - memory
  - api-design
permalink: "2026/09/19/cpp-demystifying-initializer-list-okade-bhattacharyya"
---

[Demystifying C++ initializer_list - Design, Behavior, and Best Practices](https://www.youtube.com/watch?v=NuJcFNbrdIg) ([slides](https://github.com/Digital-Medium/ACCU-On-Sea-Slides-2026/blob/main/Presentations/Demystifying_Cpp_initializer_list.pdf))

`std::initializer_list<T>` is not a container. It is a pointer and a length pointing at a compiler-generated array of **`const T`** that dies at the end of the full-expression. Almost every surprise it produces — the extra copies, the dangling reads, the constructor you did not ask for — falls out of that one sentence.

## What the compiler actually builds

```cpp
#include <cstdio>
#include <initializer_list>
#include <type_traits>

struct A {
  int v;
  A(int v) : v(v) { printf("A(%d)\n", v); }
  ~A()            { printf("~A(%d)\n", v); }
};

void take(std::initializer_list<A> l) {
  static_assert(std::is_same_v<decltype(l.begin()), const A*>);  // <-- array of const A
  printf("size=%zu  sizeof(list)=%zu\n", l.size(), sizeof(l));
}

int main() {
  take({1, 2, 3});
  puts("back in main");
}
```

```
A(1)
A(2)
A(3)
size=3  sizeof(list)=16
~A(3)
~A(2)
~A(1)
back in main
```

The standard spells the transformation out as roughly `const A __a[3] = {A{1}, A{2}, A{3}};` followed by a list built from `__a`. You can read all of it off the output: three constructions before the call, sixteen bytes of list (two pointers), and three destructions at the closing `;`. Because the list is this cheap, **pass it by value** — that is what the standard library does, and `std::move` on one only copies the two pointers anyway.

## `const` elements mean copy, never move

```cpp
#include <cstdio>
#include <memory>
#include <vector>

struct A {
  A(int)          { puts("A(int)"); }
  A(const A&)     { puts("A(const A&)"); }
  A(A&&) noexcept { puts("A(A&&)"); }
  ~A()            { puts("~A()"); }
};

int main() {
  puts("-- vector<A> v{1, 2, 3}");
  { std::vector<A> v{1, 2, 3}; }

  puts("-- reserve + emplace_back");
  { std::vector<A> v; v.reserve(3);
    v.emplace_back(1); v.emplace_back(2); v.emplace_back(3); }

  // std::vector<std::unique_ptr<int>> u{std::make_unique<int>(1)};
  //   error: call to implicitly-deleted copy constructor of 'std::unique_ptr<int>'
}
```

```
-- vector<A> v{1, 2, 3}
A(int)
A(int)
A(int)
A(const A&)
A(const A&)
A(const A&)
~A() x6
-- reserve + emplace_back
A(int)
A(int)
A(int)
~A() x3
```

`begin()` returns `const A*`, so the container has no way to move out of the backing array. **Construction through an `initializer_list` is never in place**: build the array, then copy it element by element. For `int` or `string_view` that is free; for `std::string` it doubles the allocations, and for a move-only type it does not compile at all. The commented-out line is the `unique_ptr` case — the diagnostic points at `construct_at` with `_Args = <const std::unique_ptr<int>&>`.

## The `initializer_list` constructor is considered first, alone

```cpp
#include <cstdio>
#include <initializer_list>
#include <string>
#include <vector>

struct Bag {
  Bag(int, double)                 { puts("Bag(int, double)"); }
  Bag(std::initializer_list<bool>) { puts("Bag(initializer_list<bool>)"); }
};

struct Bag2 {
  Bag2(int, double)                        { puts("Bag2(int, double)"); }
  Bag2(std::initializer_list<std::string>) { puts("Bag2(initializer_list<string>)"); }
};

int main() {
  const std::vector<int> a(2, 3);  // <-- two elements, both 3
  const std::vector<int> b{2, 3};  // <-- two elements, 2 and 3
  printf("a = %d %d\nb = %d %d\n", a[0], a[1], b[0], b[1]);

  const std::string s1(5, 'c');    // <-- "ccccc"
  const std::string s2{5, 'c'};    // <-- two chars: '\5' and 'c'
  printf("s1 = %s (%zu)\ns2 = %s (%zu)\n", s1.c_str(), s1.size(), s2.c_str(), s2.size());

  const Bag p(1, 1.0);             // parens: ordinary overload resolution
  // const Bag q{1, 1.0};          // error: type 'double' cannot be narrowed to 'bool'

  const Bag2 r{1, 1.0};            // <-- int/double do not convert to string, so phase 1 finds nothing
  (void)p; (void)r;
}
```

```
a = 3 3
b = 2 3
s1 = ccccc (5)
s2 = ^Ec (2)
Bag(int, double)
Bag2(int, double)
```

[over.match.list] runs overload resolution in two phases. Phase 1 considers **only** the initializer-list constructors; the rest of the constructors are looked at in phase 2, and only if phase 1 found nothing viable. So `Bag q{1, 1.0}` never reaches the exact-match `Bag(int, double)`: `int` and `double` both convert to `bool`, `initializer_list<bool>` is viable, and then narrowing makes it an error. Clang says `type 'double' cannot be narrowed to 'bool' in initializer list`, GCC 15.1 says `narrowing conversion of '1.0e+0' from 'double' to 'bool'`. `Bag2` differs only in the element type: nothing converts to `std::string`, phase 1 comes up empty, and `Bag2(int, double)` wins. **Adding an `initializer_list` constructor to an existing class silently rewrites every braced call site.**

## The backing array dies before you finish reading it

```cpp
#include <cstdio>
#include <initializer_list>

struct Holder {
  Holder(std::initializer_list<int> l) : list_(l) {}  // <-- stores a view of a dying array
  void print() const {
    for (const int i : list_) printf("%d ", i);
    puts("");
  }
  std::initializer_list<int> list_;
};

int main() {
  Holder h{1, 2, 3};
  h.print();  // <-- backing array died at the end of the previous statement
}
```

At `-O2` this prints `1 2 3` and exits 0; the stack slot simply has not been reused yet. Built with `-fsanitize=address` it reports `stack-use-after-scope` in `Holder::print()`. The same trap in return position is at least diagnosed: `std::initializer_list<int> GetList() { return {1, 2, 3}; }` gets `warning: returning address of local temporary object [-Wreturn-stack-address]`. **Never store an `initializer_list` as a member and never return one** — treat it strictly as a parameter type.

## Where it earns its keep: compile-time tables

{% raw %}
```cpp
#include <algorithm>
#include <initializer_list>
#include <string_view>

struct Recipe {
  std::string_view name;
  std::initializer_list<std::initializer_list<std::string_view>> steps;  // <-- no allocation
};

constexpr Recipe kRecipes[]{
    {"Pancakes", {{"Mix flour", "sugar", "baking powder"},
                  {"Whisk eggs", "milk"},
                  {"Cook", "flip", "serve"}}},
    {"Tea",      {{"Boil water"},
                  {"Add tea leaves", "steep"},
                  {"Add milk", "sugar", "serve"}}},
};

constexpr bool HasIngredient(std::string_view recipe, std::string_view ingredient) {
  const auto* r = std::ranges::find(kRecipes, recipe, &Recipe::name);
  return r != std::end(kRecipes) &&
         std::ranges::any_of(r->steps, [&](const auto& step) {
           return std::ranges::contains(step, ingredient);
         });
}

int main() {
  static_assert(HasIngredient("Tea", "sugar"));
  static_assert(!HasIngredient("Tea", "flour"));
  static_assert(HasIngredient("Pancakes", "flip"));
}
```
{% endraw %}

A `std::vector<std::vector<std::string>>` of constant data costs a heap allocation per row at startup and can never be `constexpr`. Nested `initializer_list` gives ragged rows with no allocation and no runtime work — the `static_assert`s prove the whole lookup folds at compile time. The lifetime rule still applies — this is safe only because the arrays back a `constexpr` object with static storage duration — so the talk keeps the pattern to types local to one translation unit.

## C++26: the backing array may live in static storage

```cpp
#include <cstdio>
#include <initializer_list>

void f(std::initializer_list<int> a, std::initializer_list<int> b) {
  printf("shared backing array: %s\n", a.begin() == b.begin() ? "yes" : "no");
}

void h() {
  int local = 0;
  std::initializer_list<int> il = {1, 2, 3};
  const long d = (const char*)il.begin() - (const char*)&local;  // <-- stack, or far away?
  printf("distance from stack local: %ld\n", d < 0 ? -d : d);
}

int main() { f({1, 2, 3}, {1, 2, 3}); h(); }
```

| Compiler | shared array | distance from the stack |
|---|---|---|
| Apple clang 21, `-std=c++23` and `-std=c++2c` | no | 4 bytes — on the stack |
| GCC 15.1, `-std=c++23` and `-std=c++26` | no | ~10<sup>14</sup> bytes — static storage |

P2752R3 permits (does not require) the compiler to put a constant backing array in static storage and to let separate lists share one array. GCC already places it statically; Clang still builds it on the stack, which is what makes `std::vector<char> v = { #embed "2mb-image.png" };` a 2 MB stack allocation today. Two other C++26 changes from the talk: `il.empty()` and `il.data()` become members, and the `std::begin`/`std::end` overloads for `initializer_list` are removed (P3016R6) as redundant. **Neither the members nor list sharing is implemented yet** in Apple clang 21, Homebrew clang 23.1, or GCC 15.1. The `std::span(initializer_list)` constructor was added by P2447R6 and then removed again before C++26 shipped, because it changed the meaning of `std::span<void* const>{a, 0}` from size 0 to size 2; P4190R0 proposes restoring it in C++29.

## Summary

| Use | Cost | Verdict |
|---|---|---|
| `f(std::initializer_list<string_view>)` parameter | one stack array, pointer copies | the intended use |
| `constexpr` nested lists as a lookup table | none, folds at compile time | best case |
| `vector<A> v{a, b, c}` for an allocating `A` | array + one copy per element | use `reserve` + `emplace_back` |
| `vector<unique_ptr<T>> v{...}` | — | does not compile, elements are `const` |
| member variable or return value | dangling pointer | undefined behaviour, never do it |

- The list is two pointers into a temporary `const` array. Pass it by value; `std::move` on it moves nothing.
- Elements are `const`, so containers copy them. `initializer_list` construction is never in place — prefer `reserve` + `emplace_back`, `set::emplace`, `map::emplace`.
- Braces change overload resolution: initializer-list constructors are matched in a phase of their own, before every other constructor is even considered.
- The backing array dies at the end of the full-expression. Parameter only — not a member, not a return type.
- For constant data it is the cheapest ragged container C++ has, and C++26 lets the compiler hoist its array into static storage.
