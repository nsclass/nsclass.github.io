---
layout: single
title: "C++ - Work Contracts in Action: Advancing High-Performance, Low-Latency Concurrency"
date: 2026-04-05 14:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - concurrency
permalink: "2026/04/05/cpp-work-contracts-in-action"
---
[Michael Maniscalco - Work Contracts in Action: Advancing High-Performance, Low-Latency Concurrency in C++ - CppCon 2025](https://www.youtube.com/watch?v=5ghAa7B5bF0)

This is the follow-up to Maniscalco's [CppCon 2024 introductory talk](https://www.youtube.com/watch?v=oj-_vpZNMVw) on Work Contracts. While the 2024 talk introduced the signal tree data structure and benchmarks, this 2025 talk shifts from **theory to practice** — walking through integration strategies, optimization techniques, and building a real-world **Multicast Queue (MCQ)** IPC system for low-latency networking.

## Quick Recap: Work Contract Fundamentals

A work contract is a persistent, self-scheduling callable managed by a signal tree. Three decoupled components:

- **Work Contract**: The unit of work — long-lived, stateful, self-scheduling
- **Work Contract Group**: The scheduler — signal-tree-based, lock-free, fair selection
- **Executor**: User-supplied threads — NOT part of the library

Key properties:
- Scheduling is **wait-free O(1)** (atomic bit set)
- Selection is **lock-free, expected O(1)** (tree traversal)
- **Zero allocation** after contract creation
- **Scheduling coalescence**: duplicate `schedule()` calls merge into one execution
- **Single-threaded execution guarantee** per contract — no explicit synchronization needed

## Work Contract Lifecycle

```
create() --> idle --schedule()--> scheduled --[selected]--> executing --> idle
               |                                              |
               +--release()-----------------------------------> finalize --> destroyed
```

A contract cycles between idle and executing as long as it's scheduled. Calling `release()` triggers deterministic finalization — the release callback runs exactly once, then the contract is destroyed.

## Progressive API Examples

### Basic Execution

```cpp
bcpp::work_contract_group group;

auto contract = group.create_contract(
    []() { std::cout << "working\n"; },     // work callback
    []() { std::cout << "released\n"; },    // release callback
    work_contract::initial_state::scheduled);

group.execute_next_contract();  // prints "working"
contract.release();             // schedules finalization
group.execute_next_contract();  // prints "released"
```

### Stateful Self-Scheduling Contract

Contracts support mutable functors that maintain state across executions:

```cpp
struct countdown {
    int n;
    void operator()() noexcept {
        if (n > 0)
            std::cout << n-- << '\n';
        this_contract::schedule();
        if (n <= 0)
            this_contract::release();
    }
};

bcpp::work_contract_group group;
auto c = group.create_contract(
    countdown{3},
    work_contract::initial_state::scheduled);

while (c.is_valid())
    group.execute_next_contract();
// Output: 3, 2, 1
```

### Exception Handling

The three-callback model provides structured error handling:

```cpp
auto contract = group.create_contract(
    []() {
        throw std::runtime_error("something failed");
    },
    []() { /* release callback */ },
    [](std::exception_ptr ep) {
        try { std::rethrow_exception(ep); }
        catch (std::exception const& e) {
            std::cerr << "caught: " << e.what() << '\n';
        }
    }
);
```

## Case Study: Multicast Queue IPC System

The core of the 2025 talk is building a real-world **Multicast Queue (MCQ)** — a shared-memory ring buffer for inter-process communication, exactly the kind of component used in high-frequency trading systems.

### MCQ Architecture

```
  Producer Process
       |
       v
  ┌─────────────────────────────────┐
  │  Shared Memory Ring Buffer      │
  │  (single writer, wraps around)  │
  └──────┬──────────┬───────────────┘
         |          |
    Consumer 1   Consumer 2  ...  Consumer N
    (own read    (own read        (own read
     position)    position)        position)
```

**Design characteristics:**
- **SPMC** (Single-Producer, Multiple-Consumer) pattern
- Each consumer maintains its own independent read position
- Messages can be **lost** if a consumer gets "lapped" (overwritten data) — by design, for lowest latency
- Loss handler callback reports the sequence range of lost messages

### MCQ Socket with Work Contracts

```cpp
class mcq_socket {
public:
    using message_handler = std::function<void(std::span<char const>)>;
    using loss_handler = std::function<void(std::uint64_t, std::uint64_t)>;

    mcq_socket(std::string_view shmPath,
               message_handler,
               loss_handler,
               work_contract_group& wcg);

private:
    void receive();

    // Called by poller when data is detected
    void on_select() noexcept { workContract_.schedule(); }

    mcq_consumer    mcqConsumer_;
    message_handler messageHandler_;
    loss_handler    lossHandler_;
    work_contract   workContract_;
};
```

### Self-Scheduling Receive

The contract processes available messages and reschedules itself while data remains:

```cpp
void mcq_socket::receive() {
    std::array<char, 2048> buf;
    std::span message(buf.data(), buf.size());
    auto bytesRemaining = mcqConsumer_.pop(message);

    if (not message.empty())
        messageHandler_(message);

    if (bytesRemaining > 0)
        this_contract::schedule();  // more data available
}
```

## The Poller Pattern

The talk introduces an important architectural pattern: separating **I/O detection** from **data processing**.

```
  ┌─────────────────┐         ┌──────────────────────────┐
  │  Poller Thread  │         │  Worker Thread Pool      │
  │                 │         │                          │
  │  poll() detects │ ──────> │  execute_next_contract() │
  │  data available │schedule │  runs contract callback  │
  │                 │         │                          │
  └─────────────────┘         └──────────────────────────┘
```

- **Poller thread**: Calls `mcqPoller.poll()` to detect data availability, triggers `workContract_.schedule()`
- **Worker threads**: Call `workContractGroup.execute_next_contract()` to process data

This separation allows the poller to remain lightweight and responsive while heavy processing is distributed across worker threads.

## Scaling to N Consumers with M Workers

The real power emerges when combining multiple MCQ sockets with a shared work contract group:

```cpp
bcpp::work_contract_group workContractGroup;
mcq_poller mcqPoller;

// Create N consumer sockets, all sharing the same contract group
std::vector<std::unique_ptr<mcq_socket>> sockets(num_sockets);
for (auto& socket : sockets)
    socket = std::make_unique<mcq_socket>(
        "path_to_shm",
        [](auto message) { /* process message */ },
        [](auto begin, auto end) { /* handle loss */ },
        workContractGroup,
        mcqPoller);

// Create M worker threads
std::vector<std::jthread> workers(num_workers);
for (auto& worker : workers)
    worker = std::jthread([&](std::stop_token stopToken) {
        while (not stopToken.stop_requested())
            workContractGroup.execute_next_contract();
    });

// Poller thread drives scheduling
while (not exit)
    mcqPoller.poll();

// Graceful shutdown
for (auto& worker : workers) {
    worker.request_stop();
    worker.join();
}
```

All N consumer sockets share a single `work_contract_group`. The signal tree automatically distributes work across M worker threads with fair, lock-free selection. Adding more consumers or workers requires no architectural changes — just adjust the numbers.

## Signal Tree Recap: Why This Scales

The signal tree is what makes this architecture possible:

| Operation | Complexity | Mechanism |
|---|---|---|
| Scheduling (poller triggers) | Wait-free O(1) | Atomic bit set + parent increments |
| Selection (worker picks task) | Lock-free, expected O(1) | Tree traversal with CAS |
| Fairness | Inherent | Thread-local bias flags distribute selection |

### Benchmark Highlights (from CppCon 2024)

- **40x-100x higher throughput** than MPMC queues under contention
- Near-zero coefficient of variation for both task and thread fairness
- Scales linearly with number of cores

### Cache Performance

The signal tree's fixed-size, cache-line-aligned layout minimizes cross-core cache traffic. Unlike queues where every enqueue/dequeue bounces cache lines between cores, contracts only touch shared state during scheduling (one atomic OR) and selection (tree traversal).

## Key Takeaways

1. **Separate I/O detection from processing.** The poller pattern keeps the detection path lightweight while distributing processing across worker threads via work contracts.

2. **Work contracts excel at recurring, stateful tasks.** The MCQ socket naturally fits the contract model — it processes messages repeatedly without per-invocation allocation.

3. **Scheduling coalescence prevents thundering herds.** If multiple data arrivals trigger `schedule()` before the contract executes, they coalesce into a single execution that drains all available data.

4. **The architecture scales by changing numbers, not design.** Adding consumers or workers requires no structural changes — the signal tree handles fair distribution automatically.

5. **Loss is acceptable for lowest latency.** The MCQ deliberately trades message guarantee for latency — consumers that fall behind lose messages rather than slowing the producer. The loss handler provides observability.

## Resources

- **Work Contract library**: [github.com/buildingcpp/work_contract](https://github.com/buildingcpp/work_contract) (MIT license, C++20)
- **Networking library built on work contracts**: [github.com/buildingcpp/network](https://github.com/buildingcpp/network)
- **CppCon 2024 introductory talk**: [YouTube](https://www.youtube.com/watch?v=oj-_vpZNMVw)
