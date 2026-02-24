---
layout: single
title: C++ - Type erasure
date: 2026-02-23 18:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2026/02/23/cpp-type-erasure"
---
[Duck Typing, the C++ Way: How Type Erasure Bends the Rules - Sarthak Sehgal - CppCon 2025](https://www.youtube.com/watch?v=HkoQAjwMyOc)

### `std::function` (Variadic Template Specialization)

To make the type-erased `function` wrapper work for *any* signature, we forward-declare a primary template and provide a partial specialization that splits the signature into a return type (`R`) and a variadic parameter pack (`Args...`).

```cpp
#include <memory>
#include <utility>
#include <stdexcept>

// 1. Primary template (forward declaration)
template <typename Signature>
class function;

// 2. Partial specialization for a function signature returning R and taking Args...
template <typename R, typename... Args>
class function<R(Args...)> {

    // Concept: Abstract base class using the variadic arguments
    struct Concept {
        virtual ~Concept() = default;
        virtual R operator()(Args... args) const = 0;
        virtual std::unique_ptr<Concept> clone() const = 0;
    };

    // Model: Concrete implementation that holds the callable
    template <typename F>
    struct Model : Concept {
        F callable;
        
        Model(F f) : callable(std::move(f)) {}
        
        // Overrides the concept's operator() and perfectly forwards the arguments
        R operator()(Args... args) const override { 
            return callable(std::forward<Args>(args)...); 
        }
        
        std::unique_ptr<Concept> clone() const override { 
            return std::make_unique<Model>(*this); 
        }
    };

    std::unique_ptr<Concept> pimpl;

public:
    function() = default;

    // Templated constructor captures the concrete callable 'F'
    // (In C++20, you would typically add `requires std::invocable<F, Args...>` here)
    template <typename F>
    function(F f) : pimpl(std::make_unique<Model<F>>(std::move(f))) {}
    
    // Copy constructor using the clone pattern
    function(const function& other) {
        if (other.pimpl) {
            pimpl = other.pimpl->clone();
        }
    }
    
    // The user-facing function call operator
    R operator()(Args... args) const {
        if (!pimpl) {
            throw std::bad_function_call(); // Throw if the function is empty
        }
        return (*pimpl)(std::forward<Args>(args)...);
    }
};
```

### `std:;shared_ptr` 

```cpp
// Non-templated base class for the control block
struct ControlBlockBase {
    size_t ref_count;
    virtual ~ControlBlockBase() = default;
};

// Templated derived class storing the precise type and deleter
template <typename Y, typename Deleter>
struct ControlBlock : ControlBlockBase {
    Y* ptr;
    Deleter d;
    
    ControlBlock(Y* p, Deleter deleter) : ptr(p), d(deleter) {}
    
    ~ControlBlock() override {
        d(ptr); // Invokes the deleter with the correct type
    }
};

// The shared_ptr wrapper
template <typename T>
class shared_ptr {
    T* ptr;
    ControlBlockBase* control_block;

public:
    template <typename Y, typename Deleter>
    shared_ptr(Y* p, Deleter d) {
        ptr = p;
        control_block = new ControlBlock<Y, Deleter>(p, d);
    }
    
    ~shared_ptr() {
        // When ref_count hits 0:
        delete control_block; // Virtual destructor cleans up the correct ControlBlock
    }
};
```

### `std::any` 

```cpp
class any {
    void* data = nullptr;
    void (*deleter)(void*) = nullptr;

public:
    // Templated constructor knows the concrete type 'T'
    template <typename T>
    any(T value) {
        data = new T(std::move(value));
        
        // Capture the exact destruction logic
        deleter = [](void* ptr) {
            delete static_cast<T*>(ptr);
        };
    }

    ~any() {
        if (deleter && data) {
            deleter(data);
        }
    }
};
```