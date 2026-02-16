---
layout: single
title: C++ - Misusage of Exception
date: 2026-02-15 18:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2026/02/15/misusage-cpp-exception"
---

[Exceptionally Bad: The Misuse of Exceptions in C++ & How to Do Better - Peter Muldoon - CppCon 2023](https://www.youtube.com/watch?v=Oy-VTqz1_58)

The best example from the video by using std::variant and std::visit to handle various exception type with custom operations

C++17 with deduction guide
```cpp
#include <iostream>
#include <variant>
#include <expected>
#include <string>
#include <type_traits>

// --- PART 1: The Utility Class (from first image) ---
template<typename... Ts>
struct Overloaded : Ts... {
    using Ts::operator()...;
};

template<typename... Ts>
Overloaded(Ts&&...) -> Overloaded<std::decay_t<Ts>...>;

// --- Mock Definitions for context ---
struct Msg { std::string content; };
struct Info { int id; };

struct ExceptionBase { 
    virtual std::string what() const { return "Error occurred"; } 
    std::string msg_ = "Default message";
};

struct ExceptionOrderNotFound : ExceptionBase { std::string what() const override { return "Order Not Found"; } };
struct ExceptionIllegalCurrency : ExceptionBase { std::string what() const override { return "Illegal Currency"; } };
struct ExceptionInvalidClientId : ExceptionBase { std::string what() const override { return "Invalid Client ID"; } };

// Mock helper functions
void err_log(std::string m) { std::cout << "[LOG]: " << m << "\n"; }
bool send(Msg m) { std::cout << "Sending message...\n"; return true; }
bool send_error(std::string m) { std::cout << "Handling Error: " << m << "\n"; return false; }
bool send_warning(std::string m) { std::cout << "Handling Warning: " << m << "\n"; return false; }
bool handle_bad_client(std::string m) { std::cout << "Handling Bad Client: " << m << "\n"; return false; }

// --- PART 2: The Implementation (from second image) ---
using ExceptionProcessing = std::variant<
    ExceptionOrderNotFound,
    ExceptionIllegalCurrency, 
    ExceptionInvalidClientId
>;

using ExpectedProcessing = std::expected<Msg, ExceptionProcessing>;

ExpectedProcessing apply(const Info& data) {
    // For demonstration, returning an error variant
    return std::unexpected(ExceptionIllegalCurrency{});
}

bool process(const Info& data) {
    ExpectedProcessing result = apply(data);

    if (result.has_value()) {
        return send(*result);
    }

    // Using the utility class to "visit" the error variant
    auto visitor = Overloaded {
        [&](ExceptionIllegalCurrency& ex) { 
            err_log(ex.what()); 
            return send_error(ex.msg_); 
        },
        [&](ExceptionOrderNotFound& ex) { 
            err_log(ex.what()); 
            return send_warning(ex.msg_); 
        },
        [&](ExceptionInvalidClientId& ex) { 
            err_log(ex.what()); 
            return handle_bad_client(ex.msg_); 
        }
    };

    return std::visit(visitor, result.error());
}

int main() {
    Info myData{101};
    process(myData);
    return 0;
}
```

C++20 with Concept and it does not need type deduction because of Class Template Argument Deduction(CTAD)
```cpp
#include <iostream>
#include <variant>
#include <expected>
#include <string>
#include <type_traits>
#include <concepts>

// --- PART 1: The Utility Class (C++20 Simplified) ---
// In C++20, we no longer need the 'template deduction guide' 
// for aggregates like this.
template<typename... Ts>
struct Overloaded : Ts... {
    using Ts::operator()...;
};

// --- Mock Environment ---
struct Msg { std::string content; };
struct Info { int id; };

// Base concept to ensure our exceptions have the required interface
template<typename T>
concept IsException = requires(T t) {
    { t.what() } -> std::convertible_to<std::string>;
    { t.msg_ } -> std::convertible_to<std::string>;
};

struct ExceptionOrderNotFound   { std::string msg_ = "Order 404"; std::string what() const { return "Not Found"; } };
struct ExceptionIllegalCurrency { std::string msg_ = "USD Only";  std::string what() const { return "Invalid Currency"; } };
struct ExceptionInvalidClientId { std::string msg_ = "ID Error";  std::string what() const { return "Bad Client"; } };

// Mock side-effect functions
void err_log(std::string_view m) { std::cout << "[LOG]: " << m << "\n"; }
bool send(const Msg& m) { std::cout << "Success!\n"; return true; }

// --- PART 2: The Logic ---
using ExceptionProcessing = std::variant<
    ExceptionOrderNotFound,
    ExceptionIllegalCurrency, 
    ExceptionInvalidClientId
>;

using ExpectedProcessing = std::expected<Msg, ExceptionProcessing>;

ExpectedProcessing apply(const Info& data) {
    // Simulating a specific error
    return std::unexpected(ExceptionInvalidClientId{});
}

bool process(const Info& data) {
    auto result = apply(data);

    if (result.has_value()) {
        return send(result.value());
    }

    // C++20 Visitor using the simplified Overloaded struct
    auto visitor = Overloaded {
        // We can use a Template Lambda to handle multiple types with 
        // shared logic (logging) while still branching for specific actions.
        [&]<IsException T>(T& ex) {
            err_log(ex.what());
            
            // Compile-time branching (if constexpr) for specific types
            if constexpr (std::is_same_v<T, ExceptionOrderNotFound>) {
                std::cout << "Warning Level: Medium\n";
                return false;
            } else if constexpr (std::is_same_v<T, ExceptionInvalidClientId>) {
                std::cout << "Action: Blocking Client\n";
                return false;
            } else {
                std::cout << "Action: Generic Error Handle\n";
                return false;
            }
        }
    };

    return std::visit(visitor, result.error());
}

int main() {
    process({.id = 42}); // Using C++20 designated initializers
    return 0;
}
```