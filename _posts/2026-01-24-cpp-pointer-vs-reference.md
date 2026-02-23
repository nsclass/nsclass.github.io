---
layout: single
title: C++ - Pointer vs Reference
date: 2026-01-24 18:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2026/01/24/cpp-pointer-vs-reference"
---
[Back to Basics: Forwarding References - How to Forward Parameters in Modern C++ - Mateusz Pusz 2023](https://www.youtube.com/watch?v=0GXnfi9RAlU)

### Forwarding References (Universal References)

In modern C++, a "forwarding reference" (a term coined by Scott Meyers as "universal reference") is a special type of reference that can bind to both lvalues and rvalues while preserving their value category. This is the foundation of **Perfect Forwarding**.

A forwarding reference is denoted by `T&&` where `T` is a **deduced template type**, or `auto&&`.

```cpp
template<typename T>
void wrapper(T&& arg) { // 'arg' is a forwarding reference
    // ...
}
```

### Reference Collapsing Rules

To make forwarding references work, C++ follows "Reference Collapsing" rules when deduction occurs:

- `&`  + `&`  -> `&`
- `&`  + `&&` -> `&`
- `&&` + `&`  -> `&`
- `&&` + `&&` -> `&&`

Essentially, if any part is an lvalue reference (`&`), the result collapses to an lvalue reference. Only `&&` + `&&` results in an rvalue reference.

### Perfect Forwarding with `std::forward`

The goal of perfect forwarding is to pass an argument to another function such that the receiving function receives the exact same value category (lvalue or rvalue) that was passed to the wrapper.

We use `std::forward<T>(arg)` to achieve this. Unlike `std::move`, which always casts to an rvalue, `std::forward` conditionally casts to an rvalue only if the original argument was an rvalue.

```cpp
void target(int& x) { /* called for lvalues */ }
void target(int&& x) { /* called for rvalues */ }

template<typename T>
void wrapper(T&& arg) {
    target(std::forward<T>(arg)); // Preserves value category
}
```

### Why Do We Need This?

Without forwarding references and `std::forward`, we would have to write multiple overloads (one for `const T&`, one for `T&&`, etc.) for every function that just wants to "pass through" its arguments. Perfect forwarding solves the "exponential overload explosion" problem.

### Summary Table: Pointers vs. References

| POINTER                          | REFERENCE                                     |
|----------------------------------|-----------------------------------------------|
| Objects                          | Alias (not an object)                         |
| Always occupy memory             | May not occupy storage                        |
| Arrays of pointers are legal     | No arrays of references                       |
| Pointers to pointers legal       | References or pointers to references not allowed |
| Pointers to `void` legal         | No references to `void`                       |
| May be uninitialized             | Must be initialized                           |
| Can be reassigned after initialization | Immutable                               |
| Can be cv-qualified              | Can't be cv-qualified                         |

### Key Takeaways

1.  **Forwarding Reference != Rvalue Reference:** `T&&` is only a forwarding reference if `T` is being deduced. If `T` is a concrete type (e.g., `void f(int&&)`), it is a strict rvalue reference.
2.  **Use `std::forward` with Forwarding References:** Always use `std::forward<T>(arg)` when passing a forwarding reference to another function.
3.  **Use `std::move` with Rvalue References:** If you know for sure you have an rvalue reference, use `std::move`.
4.  **Reference Collapsing:** Understand that `T` will be deduced as `int&` if an lvalue is passed, and `int` if an rvalue is passed.
