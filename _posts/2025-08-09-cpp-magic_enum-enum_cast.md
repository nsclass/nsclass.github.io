---
layout: single
title: C++ - magic_enum compile time checking for enum_cast
date: 2025-08-09 18:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2025/08/09/cpp-magic_enum-enum_cast"
---

enum_cast can detect wrong case in compile time by using a constexpr with static_assert

```cpp
constexpr auto c = magic_enum::enum_cast<Color>("Blue");
static_assert(c.has_value(), "Invalid Color name!");
```