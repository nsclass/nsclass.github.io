---
layout: single
title: C++ - Class template argument deduction guide
date: 2025-08-24 18:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2025/08/24/cpp-class-template-argument-deduction-guide"
---
A deduction guide tells the compiler how to deduce template arguments when you construct an object without explicitly specifying them.

```cpp
#include <iostream>
#include <string>

template <typename T>
struct Box {
    T value;
    Box(T v) : value(v) {}
};

// Deduction guide
Box(const char*) -> Box<std::string>;

int main() {
    Box b1(42);         // deduces Box<int>
    Box b2("hello");    // normally deduces Box<const char*>
                        // but deduction guide forces -> Box<std::string>

    std::cout << b1.value << "\n";  // 42
    std::cout << b2.value << "\n";  // hello
}
```

✅ Without the guide, "hello" would make a Box<const char*>.
✅ With the guide, the compiler redirects deduction to Box<std::string>.