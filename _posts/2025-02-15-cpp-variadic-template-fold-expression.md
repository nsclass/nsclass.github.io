---
layout: single
title: C++ - variadic template with fold expression
date: 2025-02-15 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2025/02/15/cpp-variadic-template-fold-expression"
---

C++ variadic template fold expression

```cpp
#include <iostream>
#include <utility>

// Function to print numbers using an index sequence
template <std::size_t... Indices>
void print_numbers(std::index_sequence<Indices...>) {
    ((std::cout << Indices << " "), ...);  // Fold expression (C++17)
}

int main() {
    print_numbers(std::make_index_sequence<11>{});  // Generates indices from 0 to 10
    return 0;
}
```
