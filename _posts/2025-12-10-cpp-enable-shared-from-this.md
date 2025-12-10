---
layout: single
title: C++ - std::enable_shared_from_this
date: 2025-12-10 18:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2025/12/10/cpp-enable-shard-from-this"
---

# `std::enable_shared_from_this` Example (C++)

## ✅ Basic Example

```cpp
#include <iostream>
#include <memory>

class MyClass : public std::enable_shared_from_this<MyClass> {
public:
    void show() {
        std::cout << "this = " << this << "\n";

        // Create another shared_ptr to this object
        std::shared_ptr<MyClass> self = shared_from_this();
        std::cout << "shared_from_this().get() = " << self.get() << "\n";
    }
};

int main() {
    // Must be managed by shared_ptr
    std::shared_ptr<MyClass> obj = std::make_shared<MyClass>();
    obj->show();
}
```

### **Output**
```
this = 0x7f8e94004b40
shared_from_this().get() = 0x7f8e94004b40
```

---

## ❌ Incorrect Usage (Throws `std::bad_weak_ptr`)

```cpp
int main() {
    MyClass obj;  // ❌ not owned by shared_ptr
    obj.show();   // ❌ shared_from_this() will throw std::bad_weak_ptr
}
```

---

## 🧠 Why `enable_shared_from_this` Is Needed

If you try:

```cpp
std::shared_ptr<MyClass> self(this);  // ❌ do NOT do this
```

This creates a **second** `shared_ptr` control block → double delete → crash.

`shared_from_this()` uses the **existing** shared ownership safely.

---

## ⭐ Advanced Example: Returning `shared_ptr` from a Method

```cpp
#include <memory>
#include <iostream>

class Connection : public std::enable_shared_from_this<Connection> {
public:
    std::shared_ptr<Connection> getPtr() {
        return shared_from_this();
    }
};

int main() {
    auto c = std::make_shared<Connection>();
    auto c2 = c->getPtr();

    std::cout << c.use_count() << "\n";  // prints 2
}
```

---

## 🌟 Common Pattern in Networking / Async Code

```cpp
class Session : public std::enable_shared_from_this<Session> {
public:
    void start() {
        auto self = shared_from_this();  // keep object alive
        doRead();
    }

private:
    void doRead() {
        auto self = shared_from_this();
        // perform async operation using self...
    }
};
```