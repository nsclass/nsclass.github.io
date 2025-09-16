---
layout: single
title: C++ - String cache for enum
date: 2025-08-31 18:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2025/08/31/cpp-string-cache-enum"
---

String cache example for enum type

```cpp
#include <iostream>
#include <string>
#include <array>
#include "magic_enum.hpp" // header-only reflection library

enum class Type { animal, other, bird, count };

const std::string& to_string(Type t, bool help) {
    // Total cache size = enum_count * 2 (because of bool flag)
    static std::array<std::string, magic_enum::enum_count<Type>() * 2> cache = [] {
        std::array<std::string, magic_enum::enum_count<Type>() * 2> arr{};
        for (std::size_t i = 0; i < magic_enum::enum_count<Type>(); ++i) {
            auto base = std::string(magic_enum::enum_name(static_cast<Type>(i)));

            arr[i * 2 + 0] = base + " no problem"; // bool == false
            arr[i * 2 + 1] = base + " help";       // bool == true
        }
        return arr;
    }();

    return cache[static_cast<std::size_t>(t) * 2 + (help ? 1 : 0)];
}

void function(const std::string& str) {
    std::cout << str << '\n';
}

int main() {
    Type type = Type::bird;
    function(to_string(type, true));   // "bird help"
    function(to_string(type, false));  // "bird no problem"
}
```