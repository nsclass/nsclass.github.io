---
layout: single
title: C++ - Concept example
date: 2025-04-28 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2025/04/28/cpp-concept-example"
---

C++20 introduced `concept`. The following code shows the sample example of using concept

```cpp
#include <concepts>
#include <iostream>
#include <vector>

// Define a concept that expects a .size() member function
template<typename T>
concept HasSize = requires(T a) {
    { a.size() } -> std::convertible_to<std::size_t>;
};

// Use the concept to constrain a function
void print_size(const HasSize auto& container) {
    std::cout << "Size is: " << container.size() << '\n';
}

int main() {
    std::vector<int> vec = {1, 2, 3, 4, 5};
    print_size(vec);  // OK! vector has size()

    std::string str = "hello";
    print_size(str);  // OK! string also has size()

    // int x = 5;
    // print_size(x); // Compile-time error! int doesn't have size()
}
```
