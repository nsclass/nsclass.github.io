---
layout: single
title: C++ - Deducing this feature
date: 2025-12-24 18:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2025/12/24/cpp-deducing-this"
---

C++23 introducing a new feature called deducing this. This is solving the following issues.

1. The following code can be a single template function
```cpp
struct Test {
    void fn() & { /* called on lvalue */ }
    void fn() const & { /* called on const lvalue */ }
    void fn() && { /* called on rvalue */ }
};
```

C++23
```cpp
struct Test {
    template <typename Self>
    void fn(this Self&& self) {}
};
```

2. CRTP (Curiously Recurring Template Pattern)
Before C++23
```cpp
template <typename Derived>
struct Base {
    void interface() {
        // Must cast 'this' to the Derived type manually
        static_cast<Derived*>(this)->implementation();
    }
};

struct Derived : Base<Derived> {
    void implementation() { 
        // Actual logic here 
    }
};
```

C++23
```cpp
struct Base {
    template <typename Self>
    void interface(this Self&& self) {
        // 'self' is automatically the Derived type!
        self.implementation();
    }
};

struct Derived : Base {
    void implementation() {
        // Actual logic here
    }
};
```

3. Mixing example

```cpp
#include <iostream>
#include <string>

struct NameLogger {
    template <typename Self>
    void logName(this Self&& self) {
        // Accessing self.name works because 'self' is the derived object
        std::cout << "Log: " << self.name << std::endl;
    }
};

struct User : NameLogger {
    std::string name = "Alice";
};

struct Product : NameLogger {
    std::string name = "Laptop";
};

int main() {
    User u;
    Product p;
    u.logName(); // Deduces Self as User
    p.logName(); // Deduces Self as Product
}
```

4. Const Propagation

Before C++23
```cpp
struct Database {
    std::string data;

    // 1. Version for mutable objects
    std::string& getValue() { return data; }

    // 2. Version for const objects (identical logic!)
    const std::string& getValue() const { return data; }
};
```

C++23
```cpp
#include <type_traits>

struct Database {
    std::string data = "Hello World";

    template <typename Self>
    auto& getValue(this Self&& self) {
        // If 'self' is const, this returns const std::string&
        // If 'self' is mutable, this returns std::string&
        return self.data;
    }
};
```

Why Self&& is used specifically
You might wonder why we use the "forwarding reference" syntax (&&). This allows the function to handle four different scenarios with one piece of code:

| Caller Type                 | Self Deduced As  | Return Type (auto&)           |
|-----------------------------|------------------|-------------------------------|
| Database db;                | Database&        | std::string&                  |
| const Database cdb;         | const Database&  | const std::string&            |
| std::move(db); (rvalue)     | Database         | std::string&&                 |
| const rvalue                | const Database   | const std::string&&           |

5. Lambda 

Before C++23
```cpp
// The "Old" Clunky Way
auto factorial = [](auto self, int n) -> int {
    return (n <= 1) ? 1 : n * self(self, n - 1);
};
factorial(factorial, 5); // You have to pass it to itself!
```

C++23
```cpp
// The C++23 Way
auto factorial = [](this auto self, int n) -> int {
    return (n <= 1) ? 1 : n * self(n - 1);
};

std::cout << factorial(5); // Clean call!
```
