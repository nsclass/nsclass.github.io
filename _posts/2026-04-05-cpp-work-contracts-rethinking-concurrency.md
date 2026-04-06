---
layout: single
title: "C++ - Work Contracts: Rethinking Task-Based Concurrency for Low Latency"
date: 2026-04-05 10:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - concurrency
permalink: "2026/04/05/cpp-work-contracts-rethinking-concurrency"
---
[Michael Maniscalco - Work Contracts: Rethinking Task-Based Concurrency and Parallelism for Low Latency C++ - CppCon 2024](https://www.youtube.com/watch?v=oj-_vpZNMVw)

In this CppCon 2024 talk, Michael Maniscalco (Principal Engineer at Lime Trading) introduces **Work Contracts** — a fundamentally different approach to task-based concurrency that achieves **40x-100x higher throughput** than traditional MPMC queue-based approaches under contention. The key insight: bring threads to tasks, not tasks to threads.

## The Problem with Traditional Task Queues

Traditional concurrency frameworks (thread pools with task queues, `std::async`, TBB, etc.) share a common architecture: tasks are pushed into a queue and worker threads dequeue them. This introduces several problems at scale:

1. **Queues do not scale well**: Even lock-free queues degrade under contention. Sub-queues introduce starvation, load balancing, and fairness issues.
2. **No inherent support for prioritization**: Priority queues add complexity and further degrade performance.
3. **Tight coupling of data and logic**: Queues force coupling tasks (logic + data) together because by the time a task reaches the front, you must know which logic to apply.
4. **Per-task allocation overhead**: Every task enqueue typically involves an allocation; every dequeue involves a deallocation.

Maniscalco's key philosophical point: "People get thread pools wrong all the time — they couple tasks, task containers, and thread pools, which should be separated."

## What is a Work Contract?

A work contract is a **lightweight, persistent, recurrent callable**. Unlike traditional fire-and-forget tasks, a contract is created once and can be repeatedly scheduled and executed with **zero allocation or deallocation** after creation.

### Work Contracts vs Traditional Queues

| Aspect | Traditional Queues | Work Contracts |
|---|---|---|
| Task lifecycle | Create, enqueue, dequeue, execute, destroy | Create once; schedule/execute/reschedule repeatedly |
| Memory allocation | Per-task allocation on enqueue | Zero allocation after contract creation |
| Data structure | MPMC queue (linked list or ring buffer) | Signal tree (hierarchical bit-packed atomic tree) |
| Scheduling cost | Enqueue with CAS contention | Wait-free O(1) atomic set on a leaf node |
| Selection cost | Dequeue with CAS contention | Lock-free, expected O(1), worst case O(log N) |
| Recurring tasks | Must re-enqueue a new task object | Call `this_contract::schedule()` — just sets a bit |
| Destruction | Implicit (task completes) | Deterministic async destruction with release callbacks |

## Three Decoupled Components

The work contracts ecosystem separates concerns into three independent components:

| Component | Role | Responsibility |
|---|---|---|
| **Work Contract** (Task) | The unit of work | Long-lived, stateful, self-scheduling callable |
| **Work Contract Group** (Scheduler) | Manages contracts | Signal-tree-based fair selection, lock-free |
| **Executor** (User-supplied) | Provides threads | Thread pool, dedicated thread, etc. — NOT part of the library |

The executor is intentionally **not** part of the library. Users supply their own threading model.

## The API

### Creating a Contract Group

Two flavors are available:

- `bcpp::work_contract_group` — non-blocking (lock-free polling, lowest latency)
- `bcpp::blocking_work_contract_group` — blocks with condition variable when idle

### Creating and Executing a Contract

```cpp
bcpp::work_contract_group group;

auto contract = group.create_contract(
    []() { /* work callback — executed each time contract is scheduled */ },
    []() { /* release callback — cleanup on destruction */ },
    [](std::exception_ptr) { /* optional exception handler */ }
);

contract.schedule();              // mark contract as ready
group.execute_next_contract();    // worker picks up and runs the contract
```

### Worker Thread Pattern

```cpp
std::jthread worker([&group](auto stopToken) {
    while (not stopToken.stop_requested())
        group.execute_next_contract();  // selects & runs next scheduled contract
});
```

### Self-Management from Within Callbacks

The `bcpp::this_contract` namespace provides thread-local access to the currently executing contract:

```cpp
bcpp::this_contract::schedule();   // reschedule the current contract
bcpp::this_contract::release();    // trigger async destruction
bcpp::this_contract::get_id();     // get contract identifier
```

### Stateful Contract with Self-Scheduling

Contracts support mutable state across executions — no allocation per invocation:

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
// Output: 3, 2, 1 (then contract is destroyed)
```

### Data Ingress Pattern

Pair a contract with a lock-free SPSC queue. The producer pushes data and schedules the contract; the contract pops and processes, rescheduling itself while data remains:

```cpp
bcpp::spsc_fixed_queue<int> queue(1024);
bcpp::work_contract_group group;

auto contract = group.create_contract([&queue]() {
    int value;
    if (queue.pop(value)) {
        if (value == -1) {
            this_contract::release();  // sentinel: done
            return;
        }
        process(value);
        this_contract::schedule();     // more data may be available
    }
});

// Producer side:
queue.push(42);
contract.schedule();  // wake up the consumer contract
```

## The Signal Tree: Core Innovation

The signal tree is a **hierarchical, bit-packed, lock-free tree** that replaces queues for task arbitration.

### Structure

```
          Root [count = total scheduled contracts]
         /                                        \
    Node [count]                             Node [count]
    /         \                              /         \
 Leaf [bits]   Leaf [bits]             Leaf [bits]   Leaf [bits]
 c0 c1 ... c63  c64 c65 ... c127      ...            ...
```

- **Leaf nodes**: Each bit represents one contract (1 = scheduled, 0 = idle). 64 contracts per leaf node.
- **Internal nodes**: Atomic counters holding the sum of their children, bit-packed into `std::atomic<uint64_t>`.
- Everything is **64-byte (cache-line) aligned**.

### Scheduling (Setting a Signal) — Wait-Free O(1)

1. Set the contract's leaf bit via atomic OR
2. Traverse upward from leaf to root, atomically incrementing each parent
3. Pure atomic operations — no CAS loops, no retries

### Selection (Finding Next Contract) — Lock-Free, Expected O(1)

1. Begin at root, atomically decrement by one
2. Traverse to a non-zero child, atomically decrement
3. Repeat until reaching a leaf and clearing its bit
4. The leaf index identifies which contract to execute

### Bias Flags for Fairness

Thread-local bias bits guide selection to different tree branches, preventing all workers from contending on the same path. This provides **inherent fairness with zero starvation** — every contract gets fair execution time.

## Performance Benchmarks

Tested on Ubuntu 24.04, GCC 13.2.0, 13th Gen Intel Core i9-13900HX with hyperthreading disabled, all 16 efficient cores isolated.

Compared against: **Boost Lock-Free**, **TBB `concurrent_queue`**, **MoodyCamel `ConcurrentQueue`**

### Throughput

Work contracts achieve:
- **Over 40x higher throughput** than the fastest MPMC queue at scale
- **Over 100x higher throughput** than the average MPMC queue at scale

### Fairness (Coefficient of Variation at 16 Cores)

| Contention Level | Metric | Boost Lock-Free | TBB | MoodyCamel | Work Contract |
|---|---|---|---|---|---|
| Low (~4.2us) | Task Fairness | <0.01 | <0.01 | 4.75 | **0.06** |
| Low (~4.2us) | Thread Fairness | 0.01 | <0.01 | 0.09 | **<0.01** |
| High (~17ns) | Task Fairness | <0.01 | <0.01 | 1.05 | **<0.01** |
| High (~17ns) | Thread Fairness | 0.07 | 0.13 | 0.03 | **<0.01** |
| Max (~1.5ns) | Task Fairness | <0.01 | <0.01 | 1.11 | **<0.01** |
| Max (~1.5ns) | Thread Fairness | 0.25 | 0.15 | 0.04 | **0.01** |

Work contracts consistently achieve the best fairness across all contention levels, for both task fairness and thread fairness.

## Key Design Decisions

1. **Fixed-size signal tree**: Capacity is set at construction. Trades moderate memory for predictable, deterministic latency — no dynamic allocation in hot paths.

2. **Contracts are not queues**: A contract is a persistent slot, not a transient message. This eliminates enqueue/dequeue overhead.

3. **Single-threaded contract execution**: Each contract executes on exactly one thread at a time, with no concurrent execution of the same contract — no explicit synchronization needed within a contract.

4. **Blocking vs non-blocking modes**: Non-blocking is pure lock-free polling (lowest latency but burns CPU). Blocking mode uses condition variables **only when the group is completely idle**.

5. **Scheduling coalescence**: Multiple calls to `schedule()` before execution coalesce into a single scheduling — the contract runs once, not N times.

## Resources

- **Source code**: [github.com/buildingcpp/work_contract](https://github.com/buildingcpp/work_contract) (MIT license, C++20)
- **Async networking library built on work contracts**: [github.com/buildingcpp/network](https://github.com/buildingcpp/network)
- **Requirements**: C++20, CMake 3.5+, POSIX threads
