---
layout: single
title: "C++ - Beyond Sequential Consistency: Unlocking Hidden Performance Gains"
date: 2026-04-04 10:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - concurrency
permalink: "2026/04/04/cpp-beyond-sequential-consistency"
---
[Christopher Fretz - Beyond Sequential Consistency: Unlocking Hidden Performance Gains - CppCon 2025](https://www.youtube.com/watch?v=6AnHbZbLr2o)

In this CppCon 2025 talk, Christopher Fretz from Bloomberg Engineering demonstrates how choosing the right C++ memory ordering on atomics can yield **over 50x throughput improvement** using a single-producer, single-consumer (SPSC) lock-free ring buffer as a running example. The talk progresses through four optimization levels, from naive `seq_cst` to a cached-index design that reduces cross-core cache misses by over 10,000x.

## C++ Memory Orderings Overview

C++11 introduced six memory orderings for `std::atomic` operations. The key ones covered in this talk:

| Memory Order | Used On | Guarantee |
|---|---|---|
| `seq_cst` (default) | Loads & Stores | Total ordering agreed upon by all threads. Safest but slowest |
| `acquire` | Loads | Prevents subsequent operations from being reordered before this load |
| `release` | Stores | Prevents prior operations from being reordered after this store |
| `acq_rel` | Read-Modify-Write | Combined acquire + release for RMW operations |
| `relaxed` | Loads & Stores | Only guarantees atomicity. No ordering fences |

### Fences and Barriers

- **Compiler fences** (`std::atomic_signal_fence`): Prevent the compiler from reordering instructions
- **Runtime fences** (`std::atomic_thread_fence`): Constrain CPU pipeline reordering
- Three types: **store fence** (prevents store-store reordering), **load fence** (prevents load-load reordering), **full fence** (prevents all reordering)

### x86 vs ARM Memory Models

- **x86_64** is strongly ordered: loads are never reordered with other loads, stores are never reordered with other stores. Acquire/release semantics are essentially "free" — no extra instructions needed. The penalty comes only from `seq_cst`, which requires a `lock add` full fence instruction.
- **ARM64** is weakly ordered: requires explicit `ldar` (load-acquire) and `stlr` (store-release) instructions. Without proper memory ordering, data races manifest as real bugs, not just theoretical UB.

## The SPSC Ring Buffer: Four Optimization Levels

### Level 1: Naive (seq_cst)

The starting point uses default `seq_cst` ordering on all atomic operations:

```cpp
struct ring_buffer {
    static constexpr std::size_t capacity = 32'768;

    ring_buffer() : next_producer_record(0), next_consumer_record(0) {}

    inline void push(int64_t record) noexcept;
    inline int64_t pop() noexcept;

    std::atomic<std::size_t> next_producer_record;
    std::atomic<std::size_t> next_consumer_record;
    std::array<int64_t, capacity> data;
};
```

Every load and store uses `seq_cst` by default, generating expensive `lock add` instructions on x86 for every store operation.

### Level 2: Relaxed (acquire/release)

The natural optimization for producer-consumer: the producer does a **release-store** after writing data, and the consumer does an **acquire-load** before reading data.

```cpp
inline void ring_buffer::push(int64_t record) noexcept {
    std::size_t spin_counter = 0;
    std::size_t producer = next_producer_record.load(std::memory_order::acquire);
    while (!has_space(producer))
        sleep(spin_counter);

    data[map_index(producer)] = record;
    next_producer_record.store(producer + 1, std::memory_order::release);
}

inline int64_t ring_buffer::pop() noexcept {
    std::size_t spin_counter = 0;
    std::size_t consumer = next_consumer_record.load(std::memory_order::acquire);
    while (!has_data(consumer))
        sleep(spin_counter);

    auto record = data[map_index(consumer)];
    next_consumer_record.store(consumer + 1, std::memory_order::release);
    return record;
}
```

The **release-store** on the producer index guarantees that the data write to `data[map_index(producer)]` is visible before the index update. The **acquire-load** on the consumer side guarantees it sees the data after observing the updated index.

### Level 3: Fast (cache-line alignment)

When producer and consumer indexes sit on the **same cache line**, every write by one thread invalidates the other thread's cached copy. This is called **false sharing** — the MESI protocol causes "cache line bouncing" with expensive cross-core coherency traffic.

The fix: align each atomic to its own cache line.

```cpp
struct ring_buffer {
    static constexpr std::size_t capacity = 32'768;
    static constexpr std::size_t cache_line_size =
        std::hardware_destructive_interference_size;

    alignas(cache_line_size) std::atomic<std::size_t> next_producer_record;
    alignas(cache_line_size) std::atomic<std::size_t> next_consumer_record;
    alignas(cache_line_size) std::array<int64_t, capacity> data;
};
```

> **Note:** AppleClang does not provide `std::hardware_destructive_interference_size` — you may need a fallback constant. Interestingly, on Apple M3, the optimal alignment was found to be 64 bytes even though the actual cache line size is 128 bytes.

### Level 4: Cached Index (the big win)

The key insight: each thread can **cache the other thread's index locally** so it doesn't have to read a cross-core cache line on every iteration. The cached value is only refreshed when the local copy indicates the queue might be full (producer) or empty (consumer).

```cpp
struct ring_buffer {
    static constexpr std::size_t capacity = 32'768;
    static constexpr std::size_t cache_line_size =
        std::hardware_destructive_interference_size;

    alignas(cache_line_size) std::atomic<std::size_t> next_producer_record;
    alignas(cache_line_size) std::atomic<std::size_t> producer_consumer_cache;
    alignas(cache_line_size) std::atomic<std::size_t> next_consumer_record;
    alignas(cache_line_size) std::atomic<std::size_t> consumer_producer_cache;
    alignas(cache_line_size) std::array<int64_t, capacity> data;
};
```

The producer only reads the consumer's real index when its cached copy says the queue is full. Most of the time, it operates entirely on core-local cache lines.

## Performance Benchmarks (x86_64, 8-byte records)

| Queue Variant | Throughput | Cycles/Record |
|---|---|---|
| Naive (seq_cst) | ~10M records/sec | ~260 cycles |
| Relaxed (acq/rel) | ~170M records/sec | ~15 cycles |
| Fast (+ cache aligned) | ~220M records/sec | ~12 cycles |
| Cached Index | ~570M records/sec | ~4.5 cycles |

**Overall improvement: ~57x from Naive to Cached Index.**

### Effect of Record Size (x86_64)

| Record Size | Fast Queue | Cached Index Queue |
|---|---|---|
| 64 bytes | ~72M/sec | ~110M/sec |
| 128 bytes | ~48M/sec | ~65M/sec |
| 256 bytes | ~25M/sec | ~28M/sec |
| 1024 bytes | ~3M/sec | ~3M/sec |

As record size grows, the data copy cost dominates and the cached index advantage narrows.

### Cache Performance Counters

The `perf stat` results tell the real story:

- **Fast queue**: 32.238% cache miss rate (664M cache misses out of 2B cache references)
- **Cached Index queue**: 0.001% cache miss rate (54K cache misses out of 4.4B cache references)

The cached index optimization reduces cross-core cache misses by **over 10,000x**.

## The Danger of `volatile`: The UB Queue

The talk also demonstrates a dangerous experiment — replacing `std::atomic` with `volatile`:

```cpp
struct ubqueue {
    alignas(cache_line_size) std::size_t volatile next_producer_record;
    alignas(cache_line_size) std::size_t volatile next_consumer_record;
    alignas(cache_line_size) std::array<int64_t, num_records> data;
};
// Uses std::atomic_signal_fence(std::memory_order::acq_rel) as compiler-only fence
```

This **appears to work on x86** due to its strong memory model, but it is **undefined behavior** and **crashes immediately on ARM**. The lesson: `volatile` is NOT a substitute for `std::atomic`.

## Multi-Consumer Broadcast: Relaxed Reads

For a single-producer, multi-consumer broadcast scenario, `relaxed` reads become useful. The collector scans all consumer indexes to find the slowest one:

```cpp
inline void ring_buffer::collect() noexcept {
    std::size_t slowest = std::numeric_limits<std::size_t>::max();
    for (auto const& considx : consumer_indexes) {
        if (considx.next_consumer_record < slowest) {
            slowest = considx.next_consumer_record.load(
                std::memory_order::relaxed);
        }
    }
    slowest_consumer_record.store(slowest, std::memory_order::release);
}
```

### Multi-Consumer Broadcast Benchmarks (8 consumers, x86_64)

| Queue Variant | Throughput |
|---|---|
| Naive (seq_cst) | ~1M records/sec |
| Relaxed (acq/rel) | ~25M records/sec |
| Fast (+ cache aligned) | ~110M records/sec |

## Key Takeaways

1. **Start with `seq_cst`, then optimize where benchmarks prove it matters.** The default memory model does an excellent job of correctness.

2. **Acquire/release is the most common useful relaxation.** For producer-consumer patterns, it maps naturally: release after writing data, acquire before reading.

3. **Always align atomics to separate cache lines** using `alignas(std::hardware_destructive_interference_size)` when accessed by different threads. False sharing is a silent performance killer.

4. **Cache remote indexes locally** to avoid cross-core cache line reads in hot loops. This technique (from a 2009 paper) is not implemented by Folly or Boost lock-free queues, presenting an optimization opportunity.

5. **`fetch_add` and CAS on x86 always emit a full fence** (`lock` prefix) regardless of the memory ordering you request — you cannot avoid the fence cost for read-modify-write operations on x86.

6. **Benchmark on your target platform.** x86 and ARM behave very differently, and even within a platform, results can be surprising.
