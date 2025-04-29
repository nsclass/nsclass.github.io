---
layout: single
title: C++ - std::type_identity_t
date: 2025-04-28 18:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2025/04/28/type_identity_t"
---

`std::type_identity_t` was introduced in C++20. Main purpose of this type alias has the following reasons.

- In C++, when you pass types around (especially templates), the compiler sometimes changes them automatically (for example, arrays decay to pointers, references collapse, qualifiers get lost).
- std::type_identity_t preserves the type exactly as it is.
- It also delays type deduction — making the compiler treat something as if it doesn’t know yet what the final type will be — useful in advanced template programming.

```cpp
template <typename T>
void foo(T)

template <typename T>
void bar(std::type_identity_t<T>);

foo(5); // T is deduced to be int
bar(5); // Error: cannot deduce T
```

We need to specify the type explicitly for bar
```cpp
bar<int>(5); // OK
```
