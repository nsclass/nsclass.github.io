---
layout: single
title: "C++ - Working with Asynchrony Generally (Sender/Receiver)"
date: 2026-02-24 10:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - asynchrony
permalink: "2026/02/24/cpp-working-with-asynchrony-sender-receiver"
---
[Eric Niebler - Working with Asynchrony Generally and AMA at CppEurope 2022](https://www.youtube.com/watch?v=xiaqNvqRB2E)

In this session, Eric Niebler explores the future of C++ asynchrony through the **Sender/Receiver** model (proposed in P2300), which is aimed at C++26. This model provides a standard way to represent and compose asynchronous operations, moving beyond the limitations of `std::future` and `std::promise`.

### Core Concepts of P2300

The Sender/Receiver framework is built on three main pillars:

1.  **Schedulers**: Handles the "where" and "when" of execution. It is a lightweight handle to an execution context (like a thread pool).
2.  **Senders**: Represents the "work" to be done. Senders are lazy; they describe an operation but don't start it until they are connected to a receiver and started.
3.  **Receivers**: Handles the completion of the work. A receiver has three channels:
    *   `set_value`: Successful completion.
    *   `set_error`: Failure.
    *   `set_stopped`: Cancellation.

### Chaining Operations

One of the strengths of this model is the ability to chain operations using pipeable algorithms, similar to C++20 Ranges.

```cpp
auto snd = execution::schedule(my_scheduler)
    | execution::then([] {
        return 42;
    })
    | execution::then([](int i) {
        return i * 2;
    });

// Start the work and wait for the result
auto [result] = this_thread::sync_wait(snd).value();
```

### Key Advantages

*   **Efficiency**: Avoids the heap allocations and synchronization overhead often associated with `std::future`.
*   **Composition**: Provides a rich set of algorithms (`then`, `transfer`, `when_all`, `let_value`, etc.) to compose complex async flows.
*   **Structured Concurrency**: Ensures that asynchronous operations have a well-defined lifetime, making error handling and cancellation more robust.
*   **Generic Programming**: Allows writing code that is agnostic of whether it runs on a thread pool, a GPU, or an I/O loop.

### Conclusion

The Sender/Receiver model represents a significant shift in how we think about asynchrony in C++. By separating the description of work from its execution, it enables highly performant and portable concurrent code.
