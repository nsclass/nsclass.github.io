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

### Comprehensive Example

In the final part of his talk, Eric demonstrates how to use a thread pool to run multiple asynchronous tasks concurrently and wait for their results.

```cpp
#include <stdexec/execution.hpp>
#include <exec/static_thread_pool.hpp>
#include <iostream>

namespace ex = stdexec;

int main() {
    // 1. Create a thread pool with 3 worker threads
    exec::static_thread_pool pool(3);
    auto sched = pool.get_scheduler();

    // 2. Define a function for our asynchronous work
    auto work = [](int i) {
        return ex::just(i)
             | ex::then([](int i) {
                 std::cout << "Task " << i << " on thread: " 
                           << std::this_thread::get_id() << std::endl;
                 return i * i;
             });
    };

    // 3. Compose multiple tasks to run concurrently using when_all
    // Each task is scheduled on the thread pool using 'on'
    auto all_tasks = ex::when_all(
        ex::on(sched, work(1)),
        ex::on(sched, work(2)),
        ex::on(sched, work(3))
    );

    // 4. Monadic composition with let_value
    // let_value allows us to start a new asynchronous operation 
    // using the result of a previous one.
    auto work_with_monad = std::move(all_tasks)
        | ex::let_value([](int i, int j, int k) {
            return ex::just(i + j + k);
        });

    // 5. Explicitly transfer execution back to another context (optional)
    // Here we transfer the final result calculation back to the pool
    auto final_work = ex::transfer(std::move(work_with_monad), sched)
        | ex::then([](int total) {
            std::cout << "Final calculation on thread: " 
                      << std::this_thread::get_id() << std::endl;
            return total;
        });

    // 6. Synchronously wait for the final result
    auto [total] = ex::sync_wait(std::move(final_work)).value();

    std::cout << "Total: " << total << std::endl;

    return 0;
}
```

### Key Advantages

*   **Efficiency**: Avoids the heap allocations and synchronization overhead often associated with `std::future`.
*   **Composition**: Provides a rich set of algorithms (`then`, `transfer`, `when_all`, `let_value`, etc.) to compose complex async flows.
*   **Structured Concurrency**: Ensures that asynchronous operations have a well-defined lifetime, making error handling and cancellation more robust.
*   **Generic Programming**: Allows writing code that is agnostic of whether it runs on a thread pool, a GPU, or an I/O loop.

### Conclusion

The Sender/Receiver model represents a significant shift in how we think about asynchrony in C++. By separating the description of work from its execution, it enables highly performant and portable concurrent code.
