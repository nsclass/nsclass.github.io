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