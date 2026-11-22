---
layout: single
title: "Safe Systems Programming Without References: Mutable Value Semantics in Hylo (Dave Abrahams, IWACO 2026)"
date: 2026-11-15 14:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - memory
  - rust
  - hylo
permalink: "2026/11/15/mutable-value-semantics-hylo-dave-abrahams"
---

[Safe Systems Programming with Mutable Value Semantics \| Dave Abrahams \| Keynote at IWACO 2026](https://www.youtube.com/watch?v=op51SyyPJmw)

Pointers are only part of the problem with references. A reference also quietly removes a guarantee your code depends on: **that two variables are independent**. Abrahams argues that safe languages don't need first-class references at all. Mutable value semantics (MVS), which means mutation with no sharing, gives you local reasoning, thread safety and speed. Hylo is a language built entirely on that idea.

The C++ listings were compiled with clang (`-std=c++23 -O2`, plus an ASan/UBSan build), the Rust with `rustc 1.96`, and the Hylo with Godbolt's `hylotrunk` compiler.

## Value semantics means independent variables

```cpp
#include <print>
#include <vector>

int main() {
    std::vector<int> x{1, 2, 3};
    std::vector<int> y = x;   // a copy: y is independent of x
    y.push_back(4);
    std::println("x.size()={} y.size()={}", x.size(), y.size());  // prints 3 4
}
```

Here a `vector` behaves just like an `int`. C++, Rust and Swift work this way. In Python, Java, C#, JavaScript and Kotlin the same code would leave `x` and `y` **entangled**, because arrays and user-defined types are references there while `int` is not. That breaks the regularity generic code depends on.

## Case 1: pass by value — correct

```cpp
#include <print>

using BigInt = long long;  // stand-in for an expensive-to-copy big integer

// Offsets x by delta.
void offset(BigInt& x, BigInt delta) { x += delta; }

// Offsets x by 2 * delta.
void offset_twice(BigInt& x, BigInt delta) {
    offset(x, delta);
    offset(x, delta);
}

int main() {
    BigInt x = 3;
    offset_twice(x, x);       // x += 2 * 3
    std::println("{}", x);    // prints 9
}
```

Both functions do what their comments say. Then a code reviewer notices that `BigInt` is expensive to copy.

## Case 2: "pass big types by `const&`" — a different program

```cpp
#include <print>

using BigInt = long long;  // stand-in for an expensive-to-copy big integer

// "Avoid the copy" -- the standard C++ code-review advice.
void offset(BigInt& x, BigInt const& delta) { x += delta; }

void offset_twice(BigInt& x, BigInt const& delta) {
    offset(x, delta);         // x and delta are the same object: x becomes 6
    offset(x, delta);         // ...so this adds 6, not 3
}

int main() {
    BigInt x = 3;
    offset_twice(x, x);
    std::println("{}", x);    // prints 12
}
```

It prints 12 at `-O2`, and the ASan/UBSan build stays silent because there is no UB to find. The code is well defined; it just no longer matches its specification. C++ treats `T` → `const T&` as a semantics-preserving optimization, but **the copy was what guaranteed `x` and `delta` were independent**. To fix the spec you would need a precondition ("`x` and `delta` must not alias"). Really it would have to say that `x` is independent of *every* object in the program. Nobody writes that. We just assume reference parameters don't alias, because the real meaning of references is too complicated to keep in our heads.

The same thinking covers the rest of the talk's list against references: spooky action at a distance, defensive copying, re-entrant code that sees broken invariants, and data races. In each one, a local mutation has effects somewhere you can't see.

## Rust rejects it, but its "references" aren't really references

```rust
fn offset(x: &mut i64, delta: &i64) { *x += *delta; }

fn offset_twice(x: &mut i64, delta: &i64) {
    offset(x, delta);
    offset(x, delta);
}

fn main() {
    let mut x = 3;
    let d = x;                  // i64 is Copy
    offset_twice(&mut x, &d);
    println!("{x}");            // prints 9
    // offset_twice(&mut x, &x);  // error[E0502]: cannot borrow `x` as immutable because it is also borrowed as mutable
}
```

The borrow checker forbids the aliasing call, so `&mut i64` really is unique. Abrahams' point is that this works because Rust references are so restricted. You can't build shared mutable cycles out of them, or shared mutable anything. Those are exactly the shapes that value semantics forbids. Safe Rust is really doing value semantics, under a name that suggests the full and confusing reference model.

Rust also pays a price for making them first-class types. Once a function can *return* a reference, its signature has to say which argument the result borrows from:

```rust
fn choose(v: &Vec<i32>, dice: &mut u32) -> &i32 {  // error[E0106]: missing lifetime specifier
    *dice += 1;
    &v[*dice as usize % v.len()]
}
fn main() {}
```

`rustc` suggests `fn choose<'a>(v: &'a Vec<i32>, dice: &'a mut u32) -> &'a i32`, which ties the result to `dice` as well. That is the most conservative fix, and it's more restrictive than needed (the right answer gives only `v` the `'a`). As the talk puts it, the compiler doesn't know what you mean; elision only hides the lifetimes in the simplest cases.

## Hylo: `let`, `inout`, `sink`, and no reference types

Hylo keeps Rust's access rules but never turns them into types. Copies are always explicit (`.copy()`). A `var` initialization consumes its source. `let` is a read-only binding with no copy, and `inout` is an exclusive mutable binding. Parameters use the same conventions, with `let` as the default.

```hylo
fun offset(_ x: inout Int, by delta: Int) {   // delta is `let`: read-only, never copied
  &x += delta
}

fun offset_twice(_ x: inout Int, by delta: Int) {
  offset(&x, by: delta)
  offset(&x, by: delta)
}

public fun main() {
  var x = 3
  let d = x.copy()
  offset_twice(&x, by: d)
  print(x)                    // prints 9
  // offset_twice(&x, by: x)  // error: illegal immutable access
}
```

The other two rules give these errors on Godbolt's Hylo trunk:

```hylo
public fun main() {
  var s = "hello"
  var t = s                   // consumes s
  print(s)                    // error: use of consumed object
}
```

```hylo
public fun main() {
  var s = "hello"
  let t = s                   // a let binding: s must stay constant while t lives
  &s = "bye"                  // error: illegal mutable access
  print(t)
}
```

The type of `t` is plain `String`, not `&String`. Once a program compiles, you can read it purely as values flowing in and out of variables. An `inout` binding takes the value out and puts it back after its last use.

## Projections instead of returned references

What about the main use of a returned reference, reaching into part of a value? Hylo uses **subscripts that `yield`**. The code before the `yield` is the *ramp*. The caller then uses the yielded value (the *plateau*), and afterwards the callee resumes to run the *slide*. Because control always comes back, a projection can yield a value **that doesn't exist in memory**. Here is the old bit-vector problem:

```hylo
subscript bit(_ n: Int, in words: inout Array<Int>): Bool {
  inout {
    let w = n / 64                       // ramp: find the word and the mask
    let mask = 1 << (n % 64)
    var b = (words[w] & mask) != 0
    yield &b                             // plateau: the caller holds a real Bool
    if b { &words[w] |= mask }           // slide: write it back into the word
    else { &words[w] &= ~mask }
  }
}

public fun main() {
  var words = Array<Int>()
  &words.append(0)
  &words.append(0)
  &bit[70, in: &words] = true            // looks like assigning a Bool...
  print(words[1])                        // prints 64: bit 6 of word 1 is set
  &bit[70, in: &words] = false
  print(words[1])                        // prints 0
}
```

C++ has to fake the same thing with a proxy object, and the proxy leaks:

```cpp
#include <print>
#include <vector>

int main() {
    std::vector<bool> bits(128);
    auto b = bits[70];        // not a bool: a std::vector<bool>::reference proxy
    b = true;                 // writes through to bits
    std::println("{}", bits[70]);  // prints true
    // bool& r = bits[70];    // error: non-const lvalue reference cannot bind to a temporary
}
```

Hylo compiles a projection into higher-order functions, so a binding is only ever passed *down* the call stack and lifetime safety holds trivially. In C++ terms, that is roughly:

```cpp
#include <cstdint>
#include <print>
#include <vector>

// A projection as a higher-order function: the callee runs ramp -> body -> slide.
template <class F>
void with_bit(std::vector<std::uint64_t>& words, std::size_t n, F body) {
    auto& w = words[n / 64];                  // ramp
    auto mask = std::uint64_t{1} << (n % 64);
    bool b = (w & mask) != 0;
    body(b);                                  // plateau: the caller sees a plain bool
    if (b) w |= mask; else w &= ~mask;        // slide: write it back
}

int main() {
    std::vector<std::uint64_t> words(2);
    with_bit(words, 70, [](bool& b) { b = true; });
    std::println("{}", words[1]);             // prints 64
}
```

The slide is also where a thread-safe cache unlocks its mutex. An escaping reference can't do that, because control never comes back. The costs: Hylo assumes a projection depends on *all* of its arguments, and you can't store a projection. The team's bet is that the remaining cases are rare enough to leave to unsafe library code.

## Graphs don't need references either

```cpp
#include <print>
#include <vector>

// A graph as a value: edges are indices, not pointers.
struct Graph {
    std::vector<std::vector<int>> adj;
    int add_node() { adj.emplace_back(); return int(adj.size()) - 1; }
    void add_edge(int a, int b) { adj[a].push_back(b); }
};

int main() {
    Graph g;
    int a = g.add_node(), b = g.add_node(), c = g.add_node();
    g.add_edge(a, b); g.add_edge(b, c); g.add_edge(c, a);  // a cycle, no shared_ptr

    Graph h = g;              // copying the graph copies the whole structure
    h.add_edge(a, c);
    std::println("{} {}", g.adj[a].size(), h.adj[a].size());  // prints 1 2
}
```

A cyclic structure is just an adjacency list: an array of arrays of indices. Racordon's work on doubly linked lists showed that index-based structures built on safe containers lose no performance, since better locality pays for the index lookups. And the graph algorithm sits in one place, not spread across methods of connected objects.

## Summary

| Form | Aliasing possible? | Cost |
|---|---|---|
| C++ `const T&` parameter | Yes, silently (Case 2 prints 12) | Unwritten "no alias" precondition on every call |
| C++ pass by value | No | A copy, sometimes expensive |
| Rust `&T` / `&mut T` | No, rejected with E0502 | References as types: lifetimes, `Deref`, elision rules |
| Hylo `let` / `inout` | No, "illegal immutable access" | No stored projections; coarse dependency tracking |

- A reference parameter breaks the independence guarantee that a copy gave you, and the compiler and sanitizers won't say a word.
- Pure FP recovers local reasoning by banning mutation. MVS recovers it by banning *sharing* instead, so you keep in-place updates.
- Safe Rust references already have value semantics; making them first-class types is where lifetime complexity comes from.
- Hylo's projections (`subscript` + `yield`) cover the "return a reference to a part" use case. They can also project values that aren't stored anywhere, like a real `Bool` inside a bit vector.
- Represent relationships with indices into values (adjacency lists), not pointers between objects.
