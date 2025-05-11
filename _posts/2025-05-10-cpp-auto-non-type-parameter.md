---
layout: single
title: C++ - auto as a non-type parameter in template
date: 2025-05-10 18:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2025/05/10/cpp-auto-non-type-parameter"
---

C++17 and later: auto as a non-type template parameter

Starting from C++17, we can use auto as a non-type template parameter but only in certain contexts. Specifically, we can use auto to deduce the type of a non-type template parameter, like this:
```cpp
template <auto Value>
void function() {
}
```

In this case, Value is a non-type template parameter which type is deduced by the compiler based on the initializer expression. For example:
```cpp
function<5>(); // Value is deduced to be an int
function<'a'>(); // Value is deduced to be a char
```

C++20, we can use a lambda expression as a non-type template parameter like this:
```cpp
template <auto F>
void f() {
  F(5);
}

int main() {
  f<[](int x) { std::cout << x; }>(); // prints 5
}
```
