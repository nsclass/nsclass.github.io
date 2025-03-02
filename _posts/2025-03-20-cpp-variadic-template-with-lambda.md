---
layout: single
title: C++ - variadic template with lambda
date: 2025-03-02 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2025/03/02/cpp-variadic-template-with-lambda"
---

C++ variadic template with lambda

```cpp
#include <iostream>
#include <tuple>

auto createTuple() {
  return []<size_t, ...Is>(std::index_sequence<Is...> /**/) {
    return std::make_tuple([](size_t val) {
      return val;
    }(Is)...);
  }(std::make_index_sequence<10>{});
}

int main() {
    auto myTuple = createTuple();
    std::apply([](auto&&... args) {
      ((std::count << args << ", "), ...);
    }, myTuple);
    return 0;
}
```
