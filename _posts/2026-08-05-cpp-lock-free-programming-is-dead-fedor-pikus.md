---
layout: single
title: "C++ - Lock-free Programming is Dead, Long Live Lock-free Programming! (Fedor Pikus, C++Now 2026)"
date: 2026-08-05 14:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - concurrency
permalink: "2026/08/05/cpp-lock-free-programming-is-dead-fedor-pikus"
---

[Fedor G Pikus - Lock-free Programming is Dead, Long Live Lock-free Programming! - C++Now 2026](https://www.youtube.com/watch?v=UdKqfQ3a_sY)

In 2017 Fedor Pikus gave a CppCon talk on lock-free programming. It wasn't controversial — it was an educational talk restating what everyone already believed: lock-free code is hard to write, so you concentrate it in the most critical places, encapsulate it, and reserve it for the points of **highest contention**.

Almost ten years later the machinery hasn't fundamentally changed. C++ added a few things, but nothing radical. The hardware, however, has. And Pikus opens this talk with a confession:

> "Me and everybody else was — appears to be — almost 100% wrong."

The talk is structured in three acts, ending with a working multi-producer/multi-consumer queue and a handful of last-minute discoveries he hadn't had time to fully investigate. Below is the argument, act by act.

> **About the speaker.** Fedor Pikus is a Chief Engineering Scientist at Siemens EDA, a long-time CppCon/C++Now speaker, and the author of *The Art of Writing Efficient Programs*. His benchmarks for this talk are on GitHub, and he repeatedly invites you to rerun them yourself.

## The vocabulary, briefly

- **Wait-free** — every thread always makes progress. No waiting, no loops. `fetch_add` is the canonical example.
- **Lock-free** — multiple threads attempt progress, at least one succeeds. Losers retry, but the program as a whole always advances. `compare_exchange` is the usual tool.
- **Lock-based** — one thread holds the lock, everyone else waits. At most one thread progresses, and even *that* isn't guaranteed: the lock holder can be preempted.

By this hierarchy, lock-free ought to beat lock-based under contention. At most one thread makes progress with a lock, so it should be the slowest thing on the chart.

## Act 0: the benchmark that starts the trouble

To compare all three fairly you need an operation expressible in every style. Pikus picks **incrementing an integer**:

```cpp
// wait-free
x.fetch_add(1, std::memory_order_relaxed);

// lock-free: a CAS loop over the same integer.
// Pointless in real life -- or so you would think.
int old = x.load(std::memory_order_relaxed);
while (!x.compare_exchange_weak(old, old + 1, std::memory_order_relaxed)) {}

// lock-based: a spin lock around a plain int
{ std::lock_guard guard(spinlock); ++plain_int; }
```

The results on an Intel x86 machine, plotting average increment time against thread count:

- **Spin lock** — fastest, by a wide margin.
- **`fetch_add`** — slower.
- **CAS loop** — slower still.
- **`std::mutex`** — worst, but nobody expected otherwise for this workload.

Is this an x86 quirk? No.

- **Apple M3 Pro (24 cores)** — at high thread counts, `std::mutex` actually beats `fetch_add`. (That's a compliment to whoever wrote that `std::mutex`; the spin lock is still far faster than either.)
- **NVIDIA Grace** (ARM server) — looks essentially like the Intel chart. Graviton likewise.

So it isn't an ARM-vs-x86 story. Under high contention, **spin locks outperform atomics**, and lock-free CAS is slower than wait-free `fetch_add`.

### Wait-free doesn't mean it scales

The other thing to notice: *nothing* on those charts scales. Everyone gets slower as threads are added — including the wait-free case. But if wait-free means all threads always make progress, how can it fail to scale?

Because "wait-free" is a **computer-science definition about algorithmic steps, not clock ticks**. At the algorithmic level everybody advances. At the hardware level there is still exclusion — only one thing modifies the data at a time, or you'd have data races. A single atomic increment instruction demonstrably gets slower under contention.

### Proving it's the cache line, not the data

The working hypothesis: the expense is **acquiring exclusive access to the cache line**, not touching the shared value. There's a neat hardware trick to separate the two, exploiting the fact that a cache line (64 bytes) is bigger than an `int` (4 bytes):

```cpp
// true sharing: every thread hammers the same atomic
std::atomic<int>* p = new std::atomic<int>(0);

// false sharing: separate atomics, adjacent in an array,
// so (for small thread counts) they land on the same cache line
std::atomic<int>* a = new std::atomic<int>[N];
// thread i touches a[i]
```

If you spread the indices far enough apart that no two threads share a line, you get **perfect scaling** — that case is trivial. The interesting case is false sharing, and the chart is stark: for small thread counts, the false-sharing curve is **identical** to the true-sharing curve. It costs exactly the same to increment *your own private integer that happens to sit on a shared cache line* as it does to increment the genuinely shared one.

The conclusion: **modifying any data on a cache line requires exclusive access to that whole line.** Wait-free is a constant number of *instructions*, not constant *time* — the instructions themselves get longer.

Read-only access is the exception; it needs no cache locking. That carves out a genuine niche for lock-free programming that we'll come back to.

## Act 1: what a good spin lock actually looks like

If spin locks are winning, it's worth seeing the spin lock. Two details carry all the weight.

```cpp
class Spinlock {
    std::atomic<int> flag{0};   // 0 = unlocked, 1 = locked
public:
    void lock() {
        for (int i = 0; ; ++i) {
            if (flag.load(std::memory_order_relaxed) == 0 &&      // pre-read!
                flag.exchange(1, std::memory_order_acquire) == 0)
                return;
            if (i == kProbes) { yield_to_scheduler(); i = 0; }    // back off!
        }
    }
    void unlock() { flag.store(0, std::memory_order_release); }
};
```

**1. Pre-read before you exchange.** The exchange is a read-modify-write; it needs the line exclusive. On modern CPUs a writer gets exclusivity via **RFO — read-for-ownership** — a special read that requires every other core to acknowledge that it invalidated its copy. Those acknowledgements take real time, and the reason is literally the speed of light: modern dies are big enough that crossing them matters.

If you skip the pre-read and go straight to `exchange`, **every failing thread invalidates the cache line on every other core**, including the one that actually holds the lock. A plain read, by contrast, is satisfied in the *shared* state. Threads that are going to fail anyway stop stealing the line from the thread that will succeed.

Note that this option simply **doesn't exist for atomics**: `fetch_add` and `compare_exchange` are both modifying instructions. You cannot probe a cache line without taking it exclusive. The lock can. That is a real, structural advantage for locks.

**2. Back off aggressively when you fail.** The subtler problem — and Pikus notes it gets much less attention — is **unlocking**. Unlock is one unconditional store, so it looks free. But here's the protocol:

1. You acquire: your line goes to *modified*, everyone else *invalid*.
2. Another thread politely pre-reads the flag. Its read pulls your line from *modified* down to *shared*.
3. Now you want to unlock — which is a write — so you need exclusivity again. **A second RFO.**

Unlocks are slow precisely because well-behaved readers keep stealing the line back. Worse, you can effectively prevent the lock holder from ever unlocking by hammering it with reads. Backing off — sleeping after repeated failures — fixes that: fewer readers means fewer acknowledgements to wait for, so the unlock's RFO completes faster. And unlocks need to be fast, because they're the only way anyone else makes progress.

**How many pre-reads?** One isn't enough. A read is much cheaper than RFO propagation — on x86 you can do about **eight reads** in the time it takes an RFO to come back. If you give up sooner, you'll abandon a lock you were destined to win. Eight is his empirical number; four is too few, sixteen starts to degrade, and the peak is broad. Measure on your hardware.

**Apple silicon is different.** It uses a power-efficient multi-level hierarchical directory instead of the fast, power-hungry coherency machinery in x86/Grace/Graviton. Longer interconnect latency, so atomics lose to locks even more badly there.

### So why don't we just use locks?

The usual list, and it's still valid: deadlock, livelock, **preemption** (a descheduled lock holder blocks everyone — this one matters for the rest of the talk), starvation (the releasing thread is well-positioned to immediately reacquire), and convoying. None of these can happen to lock-free code. That's what you're buying.

## Act 2: using locks the lock-free way

Point one was "locks win at high contention." Point two is that there's a **third option** beyond lock-based and lock-free — and to find it, look at an atomic maximum.

```cpp
// Lock-based: EVERY comparison happens under the lock.
{
    std::lock_guard guard(lock);
    if (n > max) max = n;
}

// Lock-free: there is no hardware max instruction, so CAS loop.
// Note the comparison does not involve the CAS -- if no update is
// needed, the expensive part never runs.
int old = max.load(std::memory_order_relaxed);
while (n > old && !max.compare_exchange_weak(old, n, std::memory_order_relaxed)) {}
```

Two very different workloads matter here:

- **Frequent updates** — the value keeps climbing, so you update almost every time.
- **Rare updates** — you hit the lifetime maximum early and then almost never write again.

For **rare updates, CAS wins decisively** and the spin lock doesn't improve at all. The reason is obvious once stated: in the CAS version the *comparison* doesn't involve the CAS, so if you never update you never do the expensive thing. In the lock version, every comparison happens **under the lock**.

That's not locks being bad. That's us using them wrong. The fix:

```cpp
// double-checked locking: the read path never touches the lock
if (n > max.load(std::memory_order_relaxed)) {     // fast path, lock-free
    std::lock_guard guard(lock);                    // slow path only
    if (n > max.load(std::memory_order_relaxed))    // recheck under the lock
        max.store(n, std::memory_order_relaxed);
}
```

The guarded variable is *also* atomic. You read it atomically, and if no update is needed you never take the lock — **it doesn't matter how expensive the thing you don't do is.** If an update is needed, you take the lock and recheck, because someone may have bumped the max in the meantime.

(An audience question caught the memory ordering: `relaxed` is only fine here because the maximum is never used to publish anything else. Any real use would need acquire/release, precisely because there's a code path that skips the mutex entirely and therefore doesn't inherit its barriers.)

Now the results flip in your favor on **both** workloads:

- **Rare updates** — same as CAS. You never pay for the lock you don't take.
- **Frequent updates** — the **spin lock wins**, because frequent updates *are* high contention, and locks win at high contention.

Pikus's framing of how to arrive at this style is memorable: **you have to think about how you'd write it lock-free, and then not write it lock-free.**

> **Lock-free-style programming with locks:** shrink the critical section to cover only state *modification*, usually by making some guarded variables atomic. The read-only path runs purely on atomics and never touches the lock; only the modifying path locks.

### Rewriting the received wisdom

The traditional view had three parts:

1. Lock-free code is hard to write. ✅ Still true.
2. You must use lock-free for the most critical code. ❌
3. The most critical code is high contention with frequent updates to shared data. ❌

Two out of three are wrong. Genuine remaining niches for lock-free: workloads that are **mostly read-only** (RCU-style), and cases where you can get away with **cheaper barriers** than a lock provides — a lock gives you acquire at the top and release at the bottom, i.e. a full bidirectional barrier, and RCU never needs one.

## Act 3: the surprise — locks poison the code around them

Here's the experience Pikus asks the room about, and gets nods for: you write a lock-free data structure, benchmark it, genuinely beat the spin lock — and then you drop it into the real program and the **whole program gets slower**.

What the microbenchmarks miss is that **synchronization steals resources from the other threads doing the actual work**. Real programs touch shared data *in service of* something else: the task queue is contended at its endpoints, but the point isn't cycling the queue, it's executing the tasks that come out.

So the model becomes:

```cpp
// Vary N: the ratio of thread-local work to shared work.
for (int i = 0; i < N; ++i) {
    // thread-local payload: a chain of sin() on stack variables
    v = std::sin(v);
    benchmark::DoNotOptimize(v);
}
increment_shared();     // <- fetch_add / CAS loop / spin lock
```

The metric is the number of *useful math iterations* completed in five seconds — throughput of the payload, not the synchronization. Then swap `increment_shared` between the three implementations and normalize to `fetch_add`. **At maximum contention** (100 shared iterations per 1 parallel iteration) there's no news: the spin lock delivers ~2.5× the overall throughput of atomics. `std::mutex` is bad; we knew that.

**At low contention there is very much news.** At a ratio of 100 parallel iterations per *one* shared increment, the spin lock is **substantially slower overall** — around 4× at the sharpest point on the Grace chart. At 1000:1 you can still see it. Only around 10,000:1 does everything converge.

Sit with the arithmetic for a second. A spin lock executed **once per hundred iterations** of expensive math cannot itself account for a 4× slowdown. Uncontended spin locks are not that slow. Something else is going on.

### To the profilers

Pikus did most of this with VTune and `perf` on Intel (better counters), and repeated the key parts on AMD and ARM.

- **Branch misprediction?** No. Counts are low, and the spin lock's branch is essentially perfectly predicted at low contention.
- **Backend stalls?** Yes. Atomic increment ~60 billion, CAS about the same, **spin lock roughly double**.

Digging into which backend stalls:

| Counter | `fetch_add` | CAS | Spin lock |
|---|---|---|---|
| **Store-buffer-full stalls** | ~never | ~never | **the culprit** |
| **Reorder-buffer stalls** | higher | higher | *lower* |

The **store buffer** sits between the execution units and L1: every write lands there first. If it fills, the CPU can't execute stores and stalls.

On **x86**, `exchange` is a full memory fence, so the load-store unit halts and waits for the store buffer to **drain**. That's the stall. Meanwhile `fetch_add` and CAS operate on a *single* shared variable — control and data are **fused into the same location**, so the dependency is one the CPU already knows how to reason about.

The reorder-buffer numbers being *lower* for the spin lock is not good news, it's confirmation. The ROB stalls when the CPU executes instructions so fast it can't retire them quickly enough — that's what shoving pure math into a CPU looks like, and **you want that to happen**. The spin lock stalls on the store buffer instead, so the ROB never gets a chance to fill.

**On ARM** the store buffer can commit to L1 in any order, not retirement order — yet low contention still favors atomics. The mechanism there is the **dark side of speculative execution**: the branch predictor is right essentially every time, execution proceeds speculatively and out of order, but **instruction retirement is still in program order**. If you reach the retirement point while still in speculative context, you stall on the ROB. Normally the buffers are sized so this never happens — but contended CAS and atomic exchange have long enough latency that it does. ARM has a `stall_backend` counter that shows it.

### The underlying explanation

With an atomic, the synchronization and the data are **the same variable**. The CPU sees an ordinary data dependency and knows exactly how to flow unrelated instructions around it.

With a lock, the flag and the guarded variable are **two different locations** with no data dependency between them — nothing points from one to the other. The ordering is real, but it's expressed only through **barriers**. And the CPU appears to have no way to reason through an implicit, barrier-expressed dependency. Its only tool is the blunt one: hold the pipeline, drain everything before, stall everything after, execute in order, restart.

Pikus is careful to attribute it to the **pair**, not the instruction. It's acquire-at-the-top plus release-at-the-bottom — the *existence of a critical section*, bounded from both sides — that the machine can't see through. Building your spin lock out of CAS instead of exchange doesn't rescue it; it's slightly worse.

## Building the queue

Armed with "spin locks at high contention, atomics at low contention," Pikus builds an **MPMC queue** — deliberately *not* lock-free.

The revised rule of thumb is itself unusual. Conventional advice says at low contention it doesn't matter, use whatever's easiest. The new advice: use lock-free at **medium** contention, and pick deliberately at both ends.

The design is a power-of-two ring buffer with head and tail indices:

- **Head and tail are two separate high-contention domains.** Producers fight over the tail, consumers over the head, and there is no reason for the two groups to fight each other — so they live on **separate cache lines**, each protected by a **spin lock**.
- The lock is held only long enough to claim a slot and bump the index, then released immediately. After that you own an **exclusive slot**, and contention on any individual slot is **low** — so the slot uses **atomics**.
- Each slot holds an **atomic key**. One key value is reserved (e.g. null, if the queue carries pointers). Constructing the value isn't atomic, but the **atomic store of the key is what publishes the slot** to consumers.

```cpp
struct Slot {
    std::atomic<Key> key{kReserved};   // kReserved == "empty"; the store
                                       // of a real key PUBLISHES the slot
    std::atomic<bool> busy{false};     // only for the wraparound race
    Value value;                       // construction is NOT atomic
};

// Head and tail are separate high-contention domains: producers fight
// over one, consumers over the other, and they should never fight
// each other -- so, separate cache lines, each with its own spin lock.
alignas(64) Spinlock tail_lock;  alignas(64) size_t tail;
alignas(64) Spinlock head_lock;  alignas(64) size_t head;
alignas(64) Slot slots[kCapacity];        // kCapacity is a power of two

void push(Key k, Value v) {
    size_t i;
    {
        std::lock_guard guard(tail_lock);   // HIGH contention -> spin lock
        i = tail++;                         // claim a slot, then get out
    }
    Slot& s = slots[i & (kCapacity - 1)];

    // We now own this slot exclusively. Contention on any INDIVIDUAL
    // slot is low -> atomics.
    s.busy.store(true, std::memory_order_relaxed);
    s.value = std::move(v);                  // not atomic, and need not be
    s.key.store(k, std::memory_order_release);   // <- publishes the slot
}
```
- A separate `busy` flag handles one exotic race: a producer that laps the entire ring and comes back to fight for a slot another producer is still constructing. (Asked why `key` and `busy` aren't packed into one atomic and hit with a single CAS: because he wanted to allow pointer-sized keys without a double-width CAS, and packing into low bits means bit manipulation. In key-only mode `busy` isn't needed at all.)

**Throughput** results across Granite Rapids, AMD Zen 5, and Grace, versus a field of well-known lock-free queues: at two threads a queue that's effectively SPSC-with-MPMC-safety wins, but at **large thread counts the hybrid queue outperforms everybody**. (On Grace, as with NUMA, you'll want multiple queues per cache domain if you're using all the cores.)

**Latency** is where he has to be honest, and this is the strongest part of the talk. His queue is lock-based; it *should* lose in the tail — the only question is where the tail begins and what the average costs you.

- **Average** — tracks throughput; his queue wins.
- **95th percentile** — the field pulls closer.
- **99th** — the gap narrows further.
- **99.9th and beyond** — some lock-free queues beat it. **Preemption is real**, and no amount of tuning fixes it.

One concrete comparison, at the median: his queue peaks around **320 ns**; the lock-free queue he singled out peaks around **82,000 ns**. At 99.9% they're roughly tied — and at the true maximum, the lock-free queue has a genuinely better bound.

His framing of that trade is exactly right: *"I'm not saying look how much better it is. These are the factors for your application."* If tail latency is what you sell, you can't use a lock-based queue. If it isn't, you've been paying a lot for a guarantee you don't need.

(Latency here is push-to-pop, timed with `rdtsc`, on a queue deliberately kept **near-empty** — latency on a full queue just measures capacity. There's also a ping-pong test for the truly-empty case.)

## The last-minute surprises

Four things Pikus discovered while preparing the talk and didn't have time to fully chase:

**1. Don't put the lock and the guarded data on the same cache line.** This one delighted him because it contradicts near-universal advice. His own reasoning predicted it: if a well-behaved thread pre-reads the flag, it drags your line from *exclusive* down to *shared* — and now the integer you're the only writer of needs a second RFO. He reports the exact thought process: *"But everybody knows that this is true. Therefore I cannot be right."* Then he benchmarked it, and separating them is faster. There's a crossover — at genuinely low contention, where RFOs are rare and cache misses are constant, sharing the line wins again. And in the context of the actual queue (as opposed to the pure microbenchmark) his quick test was **inconclusive**: maybe 15% more throughput at very high contention, but losses in other regimes.

**2. Intel's next-line prefetch.** Cache lines are 64 bytes, but Intel aggressively pulls in the adjacent line when you touch one. It shows up in some of these benchmarks; unexplored.

**3. AMD's near-memory atomics (Zen 4+).** Everything above about coherency protocols changes: if you `fetch_add` a line you don't own, instead of issuing an RFO you send a request to the **memory controller**, which has its own ALU. It performs the increment, invalidates every L1/L2 copy so L3 is the sole owner, and if you want the result back you get **eight bytes in a packet** — not a cache line. It's observable, and it makes some of these benchmarks look very strange on machines that have it. It doesn't apply to CAS, which still needs ordinary coherence.

**4. Back-off inside a CAS loop.** What if the aggressive back-off that rescues the spin lock were injected into a CAS loop?

```cpp
int old = x.load(std::memory_order_relaxed);
for (int i = 0; !x.compare_exchange_strong(old, old + 1); ++i) {
    //                          ^^^^^^ strong, not weak -- required here
    if (i == kProbes) { yield_to_scheduler(); i = 0; }   // the spin lock's trick
}
```
 On most systems: no difference, or slightly worse — which is presumably why nobody does it. **On Apple silicon**, at high contention, the CAS loop jumped to about half the spin lock's throughput: still losing to the spin lock by ~50%, but roughly **10× better than `fetch_add`**. (If you try this, you must use **strong** CAS, not weak.)

## Three things to take away

1. **Locks work better at high contention — if you do them right.** Pre-read with enough retries to let the RFOs come home, and back off aggressively, because the hidden cost of a lock is in its *release*, and you don't want other cores stealing the exclusive state from the only thread that can unlock.

2. **Lock-based code gets better when you inject atomics into the read-only path.** Shrink the critical section to modification only. It doesn't matter how expensive the lock is if you don't take it.

3. **Lock-based code poisons the code around it at low contention** — not because the lock is slow, but because the barrier pair disrupts the CPU's execution pipeline. Profilers on Intel, AMD, and ARM all confirm it, for slightly different reasons. And the poison is potent: **one lock per hundred iterations is enough to measurably degrade everything else the CPU is doing.**

Which leaves the practical inversion: the high-contention domain that lock-free programming was traditionally reserved for now belongs to well-written locks, while the **low-contention path we never bothered to think about is where atomics genuinely matter**. That's exactly backwards from the 2017 advice — including his own.

Pikus ends on the right note for a talk like this: *"It's always possible that I screwed up somewhere, and that's why I'm here showing this to you."* The benchmarks are on GitHub. Run them on your hardware.

> *"I'm afraid that I made a mistake. I'm also afraid that I didn't."*
