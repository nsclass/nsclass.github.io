---
layout: single
title: C++ - decltype example
date: 2025-06-04 18:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2025/06/04/cpp-decltype-example"
---

The following code is trying to make a reference to avoid the copy
```cpp
auto& element = *pos;
```

then we will always receive a reference to the element, but the program will fail if the iterator’s operator* returns a value. To address this problem, we can use decltype so that the value- or reference-ness of the iterator’s operator* is preserved:
```cpp
decltype(*pos) element = *pos;
```
or
```cpp
decltype(auto) element = *pos;
```
