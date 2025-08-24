---
layout: single
title: C++ - Immediately Invoked Lambda Expression
date: 2025-08-23 18:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2025/08/23/cpp-immediately-invoked-lambda-express"
---

Immediately Invoked Lambda Expression technique on initialize the singleton

```cpp
IPersistentProvider* instance = null

IPersistentProvider& get_provider() {
  static bool init = [] {
    if (!instance) {
      static SpecificProvider provider;
      instance = &provider;
    }
    return true;
  }();

  return instance;
}
```
