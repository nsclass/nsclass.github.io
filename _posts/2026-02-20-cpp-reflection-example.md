---
layout: single
title: C++ - Reflection example
date: 2026-02-20 18:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2026/02/20/cpp26-reflection-example"
---
[Practical Reflection With C++26 - Barry Revzin - CppCon 2025](https://www.youtube.com/watch?v=ZX_z6wzEOG0)

C++ Data oriented programming with reflection
```cpp
#include <experimental/meta> // Experimental reflection header
#include <vector>
#include <cstddef>

template <class T>
class SoaVector {
    // 1. Declare the nested struct that will hold our data
    struct Storage;

    // 2. The consteval block executes at compile-time to "reflect" on T
    consteval {
        std::vector<std::meta::info> specs;

        // Loop through all non-static data members of the template type T
        for (auto m : nonstatic_data_members_of(^^T)) {
            // For each member in T, add a pointer of that type to our Storage
            specs.push_back(data_member_spec(
                add_pointer(type_of(m)), 
                {.name = identifier_of(m)}
            ));
        }

        // Add the bookkeeping members to the Storage struct
        specs.push_back(data_member_spec(^^std::size_t, {.name = "size_"}));
        specs.push_back(data_member_spec(^^std::size_t, {.name = "capacity_"}));

        // 3. Define the 'Storage' struct using the collected specifications
        define_aggregate(^^Storage, specs);
    }

    // Instantiate the dynamically generated Storage struct
    Storage storage_ = {};
};
```