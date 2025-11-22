---
layout: single
title: C++ - std::piecewise_constructor to avoid temporary object creation
date: 2025-11-22 18:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2025/11/22/cpp-piecewise_constructor"
---

This constructs both elements in place, preventing unnecessary temporaries.


```cpp
#include <iostream>
#include <map>
#include <tuple>
#include <string>

struct Key {
    std::string name;
    int id;

    Key(std::string n, int i) : name(std::move(n)), id(i) {
        std::cout << "Key constructed\n";
    }
};

struct Value {
    double score;
    int level;

    Value(double s, int l) : score(s), level(l) {
        std::cout << "Value constructed\n";
    }
};

int main() {
    std::map<Key, Value> m;

    m.emplace(
        std::piecewise_construct,
        std::forward_as_tuple("Alice", 1),      // Key constructor args
        std::forward_as_tuple(98.5, 3)          // Value constructor args
    );

    std::cout << "Map size = " << m.size() << "\n";
}
```
```cpp
#include <iostream>
#include <tuple>
#include <utility>
#include <string>

struct A {
    A(int x, int y) { 
        std::cout << "A(" << x << ", " << y << ")\n"; 
    }
};

struct B {
    B(std::string s) { 
        std::cout << "B(" << s << ")\n"; 
    }
};

int main() {
    std::pair<A, B> p(
        std::piecewise_construct,
        std::forward_as_tuple(10, 20),      // Arguments for A
        std::forward_as_tuple("hello")      // Arguments for B
    );
}
```