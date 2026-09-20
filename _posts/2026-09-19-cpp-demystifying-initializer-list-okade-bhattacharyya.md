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

## Why it is costly: two constructions per element

{% raw %}
```cpp
#include <compare>
#include <cstdio>
#include <map>
#include <set>
#include <vector>

struct A {
  static inline int ctor = 0, copy = 0, move = 0;
  int v;
  A(int v) : v(v)            { ++ctor; }
  A(const A& o) : v(o.v)     { ++copy; }
  A(A&& o) noexcept : v(o.v) { ++move; }
  auto operator<=>(const A&) const = default;
};

void report(const char* what) {
  printf("%-30s ctor=%d copy=%d move=%d\n", what, A::ctor, A::copy, A::move);
  A::ctor = A::copy = A::move = 0;
}

int main() {
  { std::vector<A> v{1, 2, 3}; }                               report("vector<A>{1, 2, 3}");
  { std::vector<A> v; v.reserve(3);
    v.emplace_back(1); v.emplace_back(2); v.emplace_back(3); } report("vector reserve + emplace_back");

  { std::set<A> s{1, 2}; }                                     report("set<A>{1, 2}");
  { std::set<A> s; s.emplace(1); s.emplace(2); }               report("set emplace");

  { std::map<int, A> m{{1, 1}, {2, 2}}; }                      report("map<int, A>{{1,1}, {2,2}}");
  { std::map<int, A> m; m.emplace(1, 1); m.emplace(2, 2); }    report("map emplace");
}
```
{% endraw %}

```
vector<A>{1, 2, 3}             ctor=3 copy=3 move=0
vector reserve + emplace_back  ctor=3 copy=0 move=0
set<A>{1, 2}                   ctor=2 copy=2 move=0
set emplace                    ctor=2 copy=0 move=0
map<int, A>{{1,1}, {2,2}}      ctor=2 copy=2 move=0
map emplace                    ctor=2 copy=0 move=0
```

One copy per element, in every container, and not a single move. Three things combine to produce that. The backing array is materialized in full before the container's constructor runs, so every element is built there first. `begin()` hands back `const T*`, so the container has no way to move out of it. And the constructor signature is `vector(initializer_list<T>)` — the arguments were collapsed into finished `T` objects before the call, so there is nothing left to perfect-forward. **Construction through a braced list is never in place**: one construction, one copy and one destruction per element, where `emplace` costs one construction.

For `int` or `string_view` the copy is a register move and none of this matters. For anything that allocates — `std::string`, a nested container — it doubles the allocations. For a move-only type it does not compile at all: `std::vector<std::unique_ptr<int>> u{std::make_unique<int>(1)};` fails inside `construct_at` with `_Args = <const std::unique_ptr<int>&>`.

| Instead of | Use | Note |
|---|---|---|
| `vector<A> v{1, 2, 3}` | `v.reserve(3)` then `emplace_back` | without `reserve` the three `emplace_back`s cost 3 moves to reallocate |
| `set<A> s{1, 2}` | `s.emplace(1)` | |
| `map<int, A> m{ {1, 1} }` | `m.emplace(1, 1)` | for a multi-argument mapped type `m.emplace(k, B{...})` still costs a move; only `emplace(piecewise_construct, forward_as_tuple(k), forward_as_tuple(a, b))` is fully in place |

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

A `std::vector<std::vector<std::string>>` of constant data costs a heap allocation per row at startup and can never be `constexpr`. Nested `initializer_list` gives ragged rows with no allocation and no runtime work — the `static_assert`s prove the whole lookup folds at compile time. The lifetime rule still applies — this is safe only because the arrays back a `constexpr` object with static storage duration — so the talk keeps the pattern to types local to one translation unit. C++26 (P2752R3) extends the idea to ordinary lists by *permitting* the compiler to give the backing array static storage — GCC 15.1 already does, Apple clang 21 still builds it on the stack four bytes from the neighbouring local.

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
