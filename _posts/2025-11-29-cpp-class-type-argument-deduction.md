---
layout: single
title: C++ - class type argument deduction
date: 2025-11-29 18:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2025/11/29/cpp-class-type-argument-deduction"
---

The standard has the following CTAD(Class Type Argument Deduction) for array type

```cpp
template<class T, class... U>
array(T, U...) -> array<common_type_t<T, U...>, 1 + sizeof...(U)>;
```

We can use the following definition
```cpp
std::array arr{1, 2, 3};
```

This will become
```cpp
array<int, 3>
```
