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
[Eric Niebler - Working with Asynchrony Generally - CppEurope 2022](https://www.youtube.com/watch?v=xiaqNvqRB2E)

In this session, Eric Niebler explores the future of C++ asynchrony through the **Sender/Receiver** model (P2300), which has been accepted into the C++26 Standard. This model provides a standard way to represent and compose asynchronous operations, moving beyond the limitations of `std::future` and `std::promise`.

## Core Concepts of P2300

The Sender/Receiver framework is built on four main pillars:

### 1. Schedulers
A **scheduler** is a lightweight handle to an execution context (like a thread pool or GPU stream). It is a factory for senders that complete from a specific execution resource.

### 2. Senders
A **sender** is a description of asynchronous work to be sent for execution. Senders are lazy—they describe an operation but don't start it until connected to a receiver and started. They can be composed into task graphs using generic algorithms.

### 3. Receivers
A **receiver** is a generalized callback that consumes asynchronous results from a sender. It has three completion channels:
- `set_value`: Successful completion
- `set_error`: Failure during calculation or scheduling
- `set_stopped`: Operation ended before success or failure (cancellation)

### 4. Operation State
An **operation state** contains the state needed by an asynchronous operation. It is created by connecting a sender and receiver via `std::execution::connect`. Work is not enqueued until `start()` is called.

## Sender Factories

Sender factories create senders from non-sender parameters:

| Function | Purpose |
|----------|---------|
| `execution::just()` | Creates sender completing synchronously with provided arguments |
| `execution::just_error()` | Creates sender that completes with an error |
| `execution::just_stopped()` | Creates sender completing via `set_stopped` |
| `execution::read_env()` | Creates sender querying receiver's environment |
| `execution::schedule()` | Prepares task graph for execution on a scheduler |

## Sender Adaptors

Sender adaptors accept senders and return composed senders:

| Function | Purpose |
|----------|---------|
| `starts_on()` | Starts execution on provided scheduler's resource |
| `continues_on()` | Completes on provided scheduler's resource |
| `on()` | Transfers execution to scheduler, then back |
| `then()` | Chains function invocation with sender's values |
| `upon_error()` | Chains function invocation on error |
| `upon_stopped()` | Chains function invocation on stopped signal |
| `let_value()` | Invokes function with values, returns sender |
| `let_error()` | Invokes function with error, returns sender |
| `let_stopped()` | Invokes function with stop token, returns sender |
| `bulk()` | Multi-shot sender invoking function for each index |
| `split()` | Converts single-shot to multi-shot sender |
| `when_all()` | Completes when all input senders complete |
| `into_variant()` | Sends variant of tuples from possible completions |
| `stopped_as_optional()` | Maps stopped to `std::nullopt` |
| `stopped_as_error()` | Maps stopped channel to error |

## Sender Consumers

| Function | Purpose |
|----------|---------|
| `sync_wait()` | Blocks until sender completes, returns result |
| `start_detached()` | Starts sender without waiting for completion |

## Basic Example: Thread Pool with Concurrent Senders

```cpp
#include <stdexec/execution.hpp>
#include <exec/static_thread_pool.hpp>

int main()
{
    exec::static_thread_pool pool(3);
    auto sched = pool.get_scheduler();

    auto fun = [](int i) { return i * i; };

    auto work = stdexec::when_all(
        stdexec::starts_on(sched, stdexec::just(0) | stdexec::then(fun)),
        stdexec::starts_on(sched, stdexec::just(1) | stdexec::then(fun)),
        stdexec::starts_on(sched, stdexec::just(2) | stdexec::then(fun))
    );

    auto [i, j, k] = stdexec::sync_wait(std::move(work)).value();
    std::printf("%d %d %d\n", i, j, k);  // Output: 0 1 4
}
```

## Using `then` for Chaining Operations

The `then` adaptor chains a function invocation with a sender's values:

```cpp
namespace ex = stdexec;

ex::sender auto handle_classify_request(const http_request& req) {
    return ex::just(req)
         | ex::then(extract_image)
         | ex::then(do_classify)
         | ex::upon_error(on_classification_error)
         | ex::upon_stopped(on_classification_cancelled)
         | ex::then(to_response);
}
```

## HTTP Server Example with `let_value`

This comprehensive example demonstrates composing asynchronous operations using `let_value`, `let_error`, and `let_stopped`:

```cpp
#include <iostream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include <stdexec/execution.hpp>
#include "exec/start_detached.hpp"
#include "exec/static_thread_pool.hpp"

namespace ex = stdexec;

struct http_request {
    std::string url_;
    std::vector<std::pair<std::string, std::string>> headers_;
    std::string body_;
};

struct http_response {
    int status_code_;
    std::string body_;
};

template <ex::scheduler S>
auto schedule_request_start(S sched, int idx) -> ex::sender auto {
    auto url = std::string("/query?image_idx=") + std::to_string(idx);
    if (idx == 7)
        url.clear();  // Simulate invalid request
    http_request req{.url_ = std::move(url), .headers_ = {}, .body_ = {}};
    std::cout << "HTTP request " << idx << " arrived\n";
    return ex::just(std::move(req)) | ex::continues_on(std::forward<S>(sched));
}

auto send_response(http_response const& resp) -> ex::sender auto {
    std::cout << "Sending back response: " << resp.status_code_ << "\n";
    return ex::just();
}

auto validate_request(http_request const& req) -> ex::sender auto {
    std::cout << "validating request " << req.url_ << "\n";
    if (req.url_.empty())
        throw std::invalid_argument("No URL");
    return ex::just(req);
}

auto handle_request(http_request const& req) -> ex::sender auto {
    std::cout << "handling request " << req.url_ << "\n";
    return ex::just(http_response{.status_code_ = 200, .body_ = "image details"});
}

auto error_to_response(std::exception_ptr err) -> ex::sender auto {
    try {
        std::rethrow_exception(err);
    } catch (std::invalid_argument const& e) {
        return ex::just(http_response{.status_code_ = 404, .body_ = e.what()});
    } catch (std::exception const& e) {
        return ex::just(http_response{.status_code_ = 500, .body_ = e.what()});
    } catch (...) {
        return ex::just(http_response{.status_code_ = 500, .body_ = "Unknown error"});
    }
}

auto stopped_to_response() -> ex::sender auto {
    return ex::just(http_response{
        .status_code_ = 503,
        .body_ = "Service temporarily unavailable"
    });
}

int main() {
    exec::static_thread_pool pool{8};
    ex::scheduler auto sched = pool.get_scheduler();

    for (int i = 0; i < 10; i++) {
        ex::sender auto snd =
            schedule_request_start(sched, i)
            | ex::let_value(validate_request)
            | ex::let_value(handle_request)
            | ex::let_error(error_to_response)
            | ex::let_stopped(stopped_to_response)
            | ex::let_value(send_response);

        exec::start_detached(std::move(snd));
    }

    pool.request_stop();
    return 0;
}
```

### Key Differences: `then` vs `let_value`

- **`then`**: The callback returns a value directly
- **`let_value`**: The callback returns a **sender**, which is then flattened into the pipeline

## Using `when_all` for Concurrent Operations

```cpp
namespace ex = stdexec;

ex::sender auto sends_1 = ex::just(1);
ex::sender auto sends_abc = ex::just("abc");

ex::sender auto both = ex::when_all(sends_1, sends_abc);

ex::sender auto final = ex::then(both, [](auto... args) {
    std::cout << std::format("the two args: {}, {}", args...);
});
```

## Using `run_loop` with Schedulers

```cpp
#include <execution>
#include <string>
#include <thread>

using namespace std::literals;

int main()
{
    std::execution::run_loop loop;

    std::jthread worker([&](std::stop_token st) {
        std::stop_callback cb{st, [&]{ loop.finish(); }};
        loop.run();
    });

    // Factory: create sender with a value
    std::execution::sender auto hello = std::execution::just("hello world"s);

    // Adaptor: chain with function invocation
    std::execution::sender auto print =
        std::move(hello)
        | std::execution::then([](std::string msg) {
            return std::puts(msg.c_str());
        });

    // Get scheduler from run_loop
    std::execution::scheduler auto io_thread = loop.get_scheduler();

    // Adaptor: transfer execution context
    std::execution::sender auto work =
        std::execution::on(io_thread, std::move(print));

    // Consumer: synchronously wait for result
    auto [result] = std::this_thread::sync_wait(std::move(work)).value();

    return result;
}
// Output: hello world
```

## Writing a Custom Sender

Eric Niebler demonstrates wrapping a classic async C API with sender/receiver:

### Classic Async C API

```cpp
struct overlapped {
    // ...OS internals here...
};

using overlapped_callback = void(int status, int bytes, overlapped* user);

int read_file(FILE*, char* buffer, int bytes,
              overlapped* user, overlapped_callback* cb);
```

### Sender-Based Wrapper

{% raw %}
```cpp
namespace stdex = std::execution;

struct read_file_sender {
    using sender_concept = stdex::sender_t;

    using completion_signatures =
        stdex::completion_signatures<
            stdex::set_value_t(int, char*),
            stdex::set_error_t(int)>;

    auto connect(stdex::receiver auto rcvr) {
        return read_file_operation{{}, {}, pfile, buffer,
                                   size, std::move(rcvr)};
    }

    FILE* pfile;
    char* buffer;
    int size;
};
```
{% endraw %}

### Operation State Implementation

```cpp
template <class Receiver>
struct read_file_operation : overlapped, immovable {
    static void _callback(int status, int bytes, overlapped* data) {
        auto* op = static_cast<read_file_operation*>(data);
        if (status == OK)
            stdex::set_value(std::move(op->rcvr), bytes, op->buffer);
        else
            stdex::set_error(std::move(op->rcvr), status);
    }

    void start() noexcept {
        int status = read_file(pfile, buffer, size, this, &_callback);
        if (status != OK)
            stdex::set_error(std::move(rcvr), status);
    }

    FILE* pfile;
    char* buffer;
    int size;
    Receiver rcvr;
};
```

### Using with Coroutines

```cpp
exec::task<std::string> process_file(FILE* pfile) {
    std::string str;
    str.resize(MAX_BUFFER);

    auto [bytes, buff] =
        co_await async_read_file(pfile, str.data(), str.size());

    str.resize(bytes);
    co_return str;
}
```

## Key Advantages

- **Efficiency**: Avoids heap allocations and synchronization overhead often associated with `std::future`
- **Composition**: Rich set of algorithms (`then`, `when_all`, `let_value`, etc.) to compose complex async flows
- **Structured Concurrency**: Asynchronous operations have well-defined lifetimes, making error handling and cancellation robust
- **Generic Programming**: Write code agnostic of whether it runs on a thread pool, GPU, or I/O loop
- **Lazy Evaluation**: Work descriptions are built statically before execution occurs

## Conclusion

The Sender/Receiver model represents a significant shift in how we think about asynchrony in C++. By separating the description of work from its execution, it enables highly performant and portable concurrent code. With its acceptance into C++26, this becomes the standard approach for asynchronous programming in modern C++.

### Resources

- [NVIDIA stdexec - Reference Implementation](https://github.com/NVIDIA/stdexec)
- [P2300 Proposal](https://wg21.link/P2300)
- [What are Senders Good For, Anyway? - Eric Niebler](https://ericniebler.com/2024/02/04/what-are-senders-good-for-anyway/)
- [cppreference - Execution Control Library](https://en.cppreference.com/w/cpp/experimental/execution.html)
