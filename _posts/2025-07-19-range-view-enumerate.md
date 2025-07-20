---
layout: single
title: C++ - enumerate with ranges library
date: 2025-07-19 18:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2025/07/19/cpp-ranges-view-enumerate"
---

C++’s Ranges library enables enumeration of containers with access to both indices and elements.

✅ Option 1: Standard C++23 (No enumerate, use zip + iota)
```cpp
#include <iostream>
#include <map>
#include <ranges>
#include <utility> // for std::as_const

int main() {
    std::map<std::string, int> scores = {
        {"Alice", 90},
        {"Bob", 85},
        {"Charlie", 78}
    };

    // Enumerate using iota + zip
    for (auto [index, pair] : std::views::zip(std::views::iota(0), std::as_const(scores))) {
        std::cout << index << ": " << pair.first << " => " << pair.second << '\n';
    }

    return 0;
}
```

✅ Option 2: Using range-v3’s views::enumerate
```cpp
#include <range/v3/all.hpp>
#include <iostream>
#include <map>

int main() {
    std::map<std::string, int> scores = {
        {"Alice", 90},
        {"Bob", 85},
        {"Charlie", 78}
    };

    for (auto [index, pair] : ranges::views::enumerate(std::as_const(scores))) {
        std::cout << index << ": " << pair.first << " => " << pair.second << '\n';
    }

    return 0;
}
```