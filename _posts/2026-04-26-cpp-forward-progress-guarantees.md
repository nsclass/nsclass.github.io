---
layout: single
title: "C++ - Forward Progress Guarantees"
date: 2026-04-26 10:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - concurrency
permalink: "2026/04/26/cpp-forward-progress-guarantees"
---
[Forward Progress Guarantees in C++ - Olivier Giroux - CppNow 2023](https://www.youtube.com/watch?v=g9Rgu6YEuqY)

In this CppNow 2023 talk, Olivier Giroux — a veteran GPU architect of over 20 years, ISO C++ committee member of over 10 years, and chair of the concurrency and parallelism subgroup — presents a comprehensive overview of forward progress guarantees in C++. The central thesis: **without forward progress, most synchronization is meaningless**. Unless you are writing purely serial code, you are implicitly making assumptions about forward progress.

## Why Forward Progress Matters

Consider a simple mutex-based critical section:

```cpp
std::mutex m;

void thread_a() {
    m.lock();
    // critical section
    m.unlock();
}

void thread_b() {
    m.lock();
    // critical section
    m.unlock();
}
```

Thread B waiting on the mutex assumes that Thread A **will eventually release it**. But what if the scheduler never runs Thread A again? Without a forward progress guarantee, Thread B could wait forever — not because of a bug in your code, but because the runtime provides no assurance that Thread A will ever be scheduled.

Forward progress guarantees are the contract between your code and the execution environment that makes synchronization work.

## The Three Levels of Forward Progress

The C++ standard ([intro.progress]) defines three tiers of forward progress guarantees, each strictly stronger than the next:

### 1. Concurrent Forward Progress

> The implementation ensures that the thread will eventually make progress for as long as it has not terminated.

This is the strongest guarantee. A thread with concurrent forward progress **will be scheduled and make progress** regardless of what other threads are doing. This is what you typically expect from threads created by `std::thread` or `std::jthread` on general-purpose operating systems.

### 2. Parallel Forward Progress

A thread with parallel forward progress is not required to make progress until it executes its **first step**. Once it does, it then provides concurrent forward progress guarantees.

This accommodates task-based execution models (like thread pools) where a thread may process tasks sequentially in arbitrary order. A task sitting in a queue has no progress guarantee — but once it starts executing, it will be allowed to complete.

### 3. Weakly Parallel Forward Progress

> The implementation does not ensure that the thread will eventually make progress.

This is the weakest tier. Threads with weakly parallel guarantees **cannot be relied upon to advance independently**. This means:
- They cannot enter critical sections or take locks, because the thread holding the lock may never be scheduled again
- They are suitable only for lock-free or wait-free algorithms

The key insight: **synchronization patterns that work under stronger guarantees may deadlock under weaker ones**.

## Lock-Free Progress Hierarchy

Orthogonal to thread-level progress guarantees, C++ defines progress guarantees for atomic operations:

### Wait-Free
Every call completes in a **finite number of steps**, regardless of other threads. This is the strongest guarantee — no thread can be starved.

```cpp
// Wait-free: always completes in one step
std::atomic<int> counter{0};
void increment() {
    counter.fetch_add(1, std::memory_order_relaxed);  // single atomic RMW
}
```

### Lock-Free
When one or more lock-free operations run concurrently, **at least one is guaranteed to complete**. The system as a whole makes progress, but individual threads may be starved.

```cpp
// Lock-free: system progresses, but individual push may retry
void push(std::atomic<Node*>& head, Node* node) {
    node->next = head.load(std::memory_order_relaxed);
    while (!head.compare_exchange_weak(
        node->next, node,
        std::memory_order_release,
        std::memory_order_relaxed)) {
        // CAS failed — another thread succeeded (progress was made)
    }
}
```

### Obstruction-Free
If only **one unblocked thread** executes a lock-free operation (all others suspended), it is guaranteed to complete. This is the weakest non-blocking guarantee — it says nothing about progress under contention.

| Guarantee | System Progress | Per-Thread Progress | Bounded Steps |
|---|---|---|---|
| Wait-Free | Yes | Yes | Yes |
| Lock-Free | Yes | No | No |
| Obstruction-Free | Only in isolation | Only in isolation | Only in isolation |

## Blocking with Forward Progress Guarantee Delegation

One of the more subtle mechanisms in the standard is **forward progress guarantee delegation**. When a thread P blocks while waiting for a set of threads S:

> The implementation shall ensure that the forward progress guarantees provided by at least one thread of execution in S is at least as strong as P's.

This means if a thread with concurrent forward progress blocks on a thread pool task (weakly parallel), the runtime must temporarily **strengthen** the guarantee of at least one thread in the pool to prevent deadlock. Once all threads in S terminate, P unblocks.

This is how `std::async` with `launch::async` policy works — the returned future's destructor blocks, and the runtime must ensure the async task actually runs to completion.

## The Oversubscription Problem

When you have more threads than hardware cores (oversubscription), the OS scheduler must time-slice. Under oversubscription:

- Threads with **concurrent forward progress** are still guaranteed to eventually run — the OS preemptively schedules them
- Threads with **parallel forward progress** that have started their first step are similarly guaranteed
- Threads with **weakly parallel forward progress** may starve indefinitely if the scheduler never picks them

This becomes critical when lock-based code runs in oversubscribed environments. If Thread A holds a lock and gets preempted, and the scheduler keeps running threads that are waiting for that lock, you get **starvation** — not a deadlock (the lock is available in principle), but effectively no progress.

## The Roach Motel Problem

Giroux describes an important mental model: execution can be thought of as **"as-if isolated for a finite time."** The compiler and hardware can reorder and optimize operations freely within regions bounded by synchronization points.

The "roach motel" analogy: operations can be **moved into** a synchronized region (between acquire and release) but not **out of** it. This is a direct consequence of the acquire/release memory model, and it interacts with forward progress because:

1. A thread must eventually **reach** its release operation (forward progress)
2. Other threads must eventually **observe** the effects (memory visibility)

Without the first guarantee, the second is meaningless.

## Gaps in the C++ Standard

A significant portion of the talk addresses areas where the C++ specification lacks clarity:

1. **Implementation-defined guarantees**: Whether `std::thread` provides concurrent forward progress is technically implementation-defined, though general-purpose implementations are expected to provide it

2. **Trivial infinite loops**: The standard treats `while(true) {}` as undefined behavior (the compiler may assume all loops terminate). Proposal P2809R3 addresses allowing trivial infinite loops as defined behavior

3. **Interaction with execution policies**: Parallel algorithms (`std::for_each(std::execution::par, ...)`) create threads with parallel forward progress — understanding this is crucial for avoiding deadlocks in parallel algorithm bodies

## Practical Implications

### When writing lock-based code
Ensure your threads have at least **parallel forward progress guarantees** (they will after their first step). Avoid holding locks across operations that might depend on weakly-parallel threads making progress.

### When writing lock-free code
Your algorithms work under **any** forward progress tier — this is why lock-free data structures are essential in contexts like signal handlers, GPU kernels, and real-time systems where scheduling guarantees are weak.

### When using thread pools
Tasks submitted to a thread pool may only have **weakly parallel** guarantees until they start executing. Never have a running task block waiting for a queued task in the same pool — this can deadlock if the pool has a fixed number of threads.

```cpp
// DANGER: potential deadlock in a fixed-size thread pool
auto future = pool.submit([&pool]() {
    // This task blocks waiting for another task in the same pool
    auto inner = pool.submit([]() { return 42; });
    return inner.get();  // may deadlock if pool is fully occupied
});
```

### When using `std::async`
`std::async(std::launch::async, ...)` creates a thread with concurrent forward progress. The returned future's destructor will block, relying on forward progress guarantee delegation to ensure the async task completes.

## Key Takeaways

1. **Forward progress is a prerequisite for synchronization.** Without it, mutexes, condition variables, and futures are all meaningless constructs.

2. **Know your guarantee tier.** `std::thread`/`std::jthread` typically provide concurrent forward progress. Thread pools and parallel algorithms may provide weaker guarantees.

3. **Lock-free algorithms are universally safe** because they don't depend on any particular thread being scheduled — they only require that *some* thread makes progress.

4. **Oversubscription degrades progress.** When threads exceed cores, even concurrent forward progress comes with higher latency. Lock-free designs shine here.

5. **The standard has gaps.** Forward progress guarantees are partially implementation-defined, and the interaction with infinite loops remains an area of active standardization work (P2809R3).

6. **Forward progress guarantee delegation is your safety net** for blocking operations across guarantee tiers — but you must structure your code so the runtime can actually provide the delegation.
