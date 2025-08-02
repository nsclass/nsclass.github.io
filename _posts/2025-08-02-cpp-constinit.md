---
layout: single
title: C++ - constint
date: 2025-08-02 18:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2025/08/02/cpp-constinit"
---

C++20 introduced the `constinit` which will initialize the value at compile time but still you can modify it at runtime

### 📝 Difference from `constexpr`

| Keyword     | Compile-time init | Constant after init | Usable in constant expressions |
|-------------|-------------------|----------------------|-------------------------------|
| `constexpr` | ✅                | ✅                   | ✅                            |
| `constinit` | ✅                | ❌                   | ❌                            |


```cpp
#include <iostream>

constinit int global_id = 42;  // Compile-time initialized

int get_initial_value() {
    return 100;
}

// This would be an error because get_initial_value() is not constexpr
// constinit int another = get_initial_value(); // ❌ Error

int main() {
    std::cout << "global_id = " << global_id << "\n";

    // You can still modify it
    global_id += 1;
    std::cout << "global_id (after increment) = " << global_id << "\n";

    return 0;
}
```