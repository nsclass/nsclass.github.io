---
layout: single
title: C++ - static_pointer_cast
date: 2025-05-24 18:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2025/05/24/cpp-static_pointer_cast"
---

C++11 introduce the `static_pointer_cast` which will allow to case the `shared_ptr` to another type without runtime checking.

- static_pointer_cast
Casts a `shared_ptr` to a different type without checking the type at runtime.

- dynamic_pointer_cast

Casts a `shared_ptr` to a different type and checks the type at runtime. If the cast fails, return a null pointer.
