---
layout: single
title: "C++ - After Reflection: The Runtime Story (Saksham Sharma, C++Now 2026)"
date: 2026-08-15 14:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - reflection
permalink: "2026/08/15/cpp-after-reflection-runtime-story-saksham-sharma"
---

[Saksham Sharma - After Reflection: The Runtime Story - C++Now 2026](https://www.youtube.com/watch?v=bUmt9K1o1d0)

Reflection is merged into **C++26**, and as of the week of this talk it ships in a production release of GCC. It's genuinely transformative — we can now inspect and generate code at compile time, enabling abstractions we couldn't previously imagine.

Saksham Sharma opens by pointing at the word doing all the work in that sentence:

> We can only understand the code **we've already written** at compile time. And here's the twist — the user's reality is **runtime**, not compile time.

There was a talk running in the same slot called *Until Reflection*. This one is titled *After Reflection*. As he puts it: clearly there are two types of people.

The thesis is a provocation aimed squarely at a C++Now audience: **domain-specific languages are not meaningfully different from full-blown programming languages, and we should stop pretending otherwise.** We should make C++ a system in which writing DSLs is easy — and the talk builds one, end to end, to prove the point.

> **About the speaker.** Saksham Sharma works at a New York-based high-frequency trading firm (recently relocated to Chicago), writing C++ for low-latency trading systems and C++/Python for higher-throughput research systems. This is his seventh conference talk, and by his own count every one of them has been about Python and C++.

## The runtime problem

C and C++ are the bedrock of high-performance numerical software, but look at how that software is actually *used*:

| Library | Implementation | User writes |
|---|---|---|
| **NumPy** (30+ years) | C | Python |
| **CUDA** | C++ | C++ kernels |
| **PyTorch** | C++ / libtorch | Python |
| **JAX** | C++ / libjax | Python |
| **pandas** | Python + Cython → C++ | Python |
| **polars** | …Rust, sadly | Python |

The common thread is that **the entire input to these libraries arrives at runtime**. The user's code shows up long after libtorch was compiled. You don't know what computation they want, and there's no standard answer in C++ for how to parse code that appears at runtime.

And even if you *did* know the code, the specialization can't be prepaid. Two axes make that intractable:

- **Data** — types, and sizes. Your kernel may compile better when the matrix dimension is a power of two. Now you need two variants.
- **Machines** — different GPUs, GPU families, vendors.

Keep multiplying variants and you're shipping a 10 GB `.so`. Not fun.

So a host-language ecosystem targeting this space needs a specific set of building blocks: accept computation **after the program has started**, **preserve its structure** (if it's a graph, keep it a graph), **specialize** it for a chosen target, **compile** it, **load and resolve** the symbols, and expose a **safe, typed callable interface**.

## What reflection does and doesn't give us

A quick refresher on the C++26 feature. This snippet — one of Sharma's favorites, from P2996 — generates a command-line options parser from a struct's data members, something that used to be an entirely manual chore:

```cpp
// enumerate the members of a struct at compile time and generate the parser
template <typename Opts>
auto parse_options(std::span<std::string_view> args) -> Opts;
```

The user writes a plain struct, optionally with annotations (say, adding `-f` as shorthand for `--file`), and it works. **That struct is a DSL.** The user expresses intent; we decide what to do with it. Function signatures are parseable too — parameter types, return type, `noexcept` — all inspectable and printable.

Other languages have something similar, just not at compile time. Sharma's standing example is Python, where you can reach into a class's layout, modify it, and even swap out what a function does at runtime via a decorator. Powerful, but entirely runtime.

C++ figured out the compile-time story nicely. The gap is everything that comes after.

## A survey of DSLs, and where the graph comes from

Four systems, each solving the runtime problem differently:

**PyTorch** — users write Python; the library converts it to a graph; `torch.compile` lowers that graph to something executable without Python in the loop.

**JAX** — same principle, different lowering. A `@jax.jit` decorator captures the computation into a graph and converts it to the **XLA** IR, which then targets GPU or TPU.

**Numba** — the odd one out, and "kind of crazy that it even works." It reads Python **bytecode**, maps it back to an internal representation, and emits LLVM. It works remarkably well as long as you stick to Python and NumPy. Its graph contains loop and return nodes — a hint that it's aimed at *imperative* code, where the first two are functional.

**CUDA stream graphs** — the closest to C++. Launching kernels one at a time wastes cycles, so CUDA lets you `cudaStreamBeginCapture`, make your kernel calls *without actually executing them*, end the capture, and instantiate a reusable graph object. That's graph capture in C++ at runtime. Painful — but still far better than making users hand-build graph nodes and wire them together with pointers.

The motivating hypotheticals: give a lab of scientists a simulator that runs their computation optimally without the Python runtime overhead — and, because you *understand* their code, hand them visualization and profiling for free. Or game developers who'd rather not recompile the entire engine.

The concrete target for the talk is a **state-estimation problem from autonomous robotics** — matrix multiplications, transposes, and conditionals inside a loop. The goal: write it in C++ *or* Python, understand it completely, and be able to flip one boolean to get per-operation timings with source locations attached.

## Why not write a parser?

The obvious approach: invent a DSL syntax, write a parser, generate C++ as a build step, link it in. Which means teaching users your toolchain and its dependencies.

Sharma's own history with this is the argument against it. He wrote a Go compiler during his undergrad using **Flex** and **Yacc**, and shows the code: *"I don't know about you, but this makes very little sense to me 10 years later."*

> An audience member, immediately: *"I wrote a generator for C++. You should use mine. It's much better."*
> Sharma: *"Okay — so that's good to know, because this is not fun."*

The runtime alternatives are no better: ask users for JSON (limiting), invoke Flex/Yacc at runtime (horrific), or build a runtime graph of operations where every node costs you a virtual call.

**So what does Python do?** You ship a C++ library with Python bindings, the user's Python code constructs a graph of objects, and you interpret it. No lexer, no parser. Lower it to LLVM, XLA, MLIR — whatever you like.

> **The hot take:** the traditional design of DSLs in C++ pushes us toward parser work, and that parser becomes technical debt specific to your one use case. Python is *already* a DSL parser. Let's borrow the idea, port it into C++, and mainstream it.

There's a side benefit that's easy to undersell: as long as users are writing C++ or Python rather than JSON, they **inherit their editor**. Jump-to-definition, completion, type checking — no new tooling required.

## Tracing: evaluation over symbolic values

The technique JAX calls **tracers**, and the heart of the talk. You don't parse the function — you *run* it with proxy values.

Put a decorator on a function, pass in tracer objects instead of real numbers, and the prints inside won't show numbers; they'll show tracer objects. Every arithmetic operation and function call produces a **new** proxy value that records what was done to get there.

An audience exchange cut right to it:

> *"You keep saying you parse graphs. Why do you parse graphs at all? You have a data structure for graphs."*
> *"There's essentially no parsing. Yes, there is a data structure — that's the trick here."*

The mechanism is just **operator overloading**: adding two graph nodes yields a third graph node that records the addition. Inputs are proxies, outputs are proxies, and any file reads or dynamic decisions in between happen *at trace time* — so if a config file says "add, don't subtract," the resulting graph contains an add.

```cpp
// The whole mechanism is operator overloading over proxy values.
// Nothing computes; every operation RECORDS a new node.
struct Tracer {
    NodeId id;
};

Tracer operator*(Tracer a, Tracer b) {
    return Tracer{graph.add_node(Op::Mul, a.id, b.id)};   // records, not computes
}
Tracer operator+(Tracer a, Tracer b) {
    return Tracer{graph.add_node(Op::Add, a.id, b.id)};
}

// Import a foreign function by reflecting its signature -- this records a
// "call this, with this signature" node without calling anything yet.
auto dgemv = graph.import<&cblas_dgemv>();
```

The two front ends produce the *same* graph from line-for-line identical code:

```cpp
// C++
for (int i = 0; i < n; ++i) result = custom_runtime_func(a, b);
```

```python
# Python
for i in range(n): result = custom_runtime_func(a, b)
```

The C++ and Python versions of the target code are **line-for-line identical** apart from the loop syntax. And a foreign-function import mechanism lets the graph reference something like `dgemv` (double-precision general matrix-vector multiply, from the BLAS family, via CBLAS) — recording a node that says "call this function with this signature," without calling it yet. Reflection is what makes capturing that signature pleasant.

Tracing is, in one line: **evaluation over symbolic values.** That's the whole practical answer to DSL front-end parsing.

### Honest limitations

- **Control flow cannot depend on traced values.** A C++ `if` on a proxy value doesn't work — you need an explicit `where`-style conditional node that selects between branches.
- **External calls must be bounded by effects.** The standard functional-language answer applies: make users pass their state in as a parameter.
- **Aliasing.** Asked about alias analysis, Sharma is straightforward that the treatment is simplistic — these are languages without aliasing, and at runtime aliases resolve anyway. Duplicate nodes get handled later, by deduplication.

### Why keep the graph in C++?

Because it's a **reusable internal boundary**, agnostic to the front end. Write a graph-to-GPU converter once and it serves both Python and C++ users.

Couldn't we use an existing IR? Other IRs are more expressive — they let you state where memory allocation happens, and so on. But that's exactly the problem. Sharma quotes the JAX designers approvingly on their own IR: *not all Python programs can be expressed with this IR, but many scientific programs can.* True, and yet the IR is still too low-level for users to want to write by hand. **MLIR** shares this talk's goal almost word for word — reusable, extensible compiler infrastructure, addressing fragmentation — and is likewise too low-level, because you're still describing memory management.

These IRs aren't meant for humans. You lower *into* them. What this graph captures is user-friendly **intent** — simple and lossy on purpose. (With the obligatory nod to the XKCD comic about inventing the 15th competing standard.)

## Backend #1: lower to C++ and shell out to the compiler

The first attempt, and Sharma admits it was tempting: make **C++ itself the IR** and the **C++ compiler the IR compiler**.

Walk the graph, deduplicate it, generate C++ source for each operation as a string, and let the compiler handle dead-code elimination, register allocation, temporaries, and vectorization for free. Then `clang` the file, `dlopen` it, look up the symbol, and call it.

The rendering approach carries through the rest of the talk: maintain a **context** mapping each node's unique ID to what you've learned about it — scalar or vector, dimensionality, type, length. Then loop over the topologically sorted graph:

```cpp
// context: node id -> what we know about it (scalar/vector, dims, type, length)
Context ctx;

for (NodeId id : topological_order(graph)) {
    const Node& n = graph[id];
    switch (n.op) {
    case Op::Literal:
        out += std::format("int node{} = {};\n", id, n.literal);
        ctx.record(id, std::format("node{}", id), Kind::Scalar);
        break;
    case Op::Mul:
        // ctx supplies the NAMES of already-emitted results
        out += std::format("int node{} = {} * {};\n",
                           id, ctx.name(n.lhs), ctx.name(n.rhs));
        ctx.record(id, std::format("node{}", id), Kind::Scalar);
        break;
    // ...
    }
}
```

Topological sorting is what makes this work: you always discover a node before you use it. Then `clang` the file, `dlopen` it, and look up the symbol.

It runs. It also means you need a **C++ compiler present at runtime**, manual symbol import/export, and a **filesystem** — and, as Sharma notes, C++ famously doesn't acknowledge that a filesystem exists, so you can't standardize anything that depends on one.

## Backend #2: LLVM ORC

The production-grade answer. **ORC** stands for *On-Request Compilation* — a real JIT backend with lazy compilation, proper symbol resolution, and, crucially, **structure** where the previous approach was ad hoc. Everything happens **in memory**. It's what replaced the decade-old MCJIT.

The model:

- **`LLJIT`** owns the JIT stack in memory, accepts IR in several forms, materializes it to machine code, and resolves symbols.
- **JIT dynamic libraries** each own a chunk of code. **Order of addition matters** — if library 1 defines symbols used by library 2, add 1 first.
- **Materialization units** are how you inject code into a dylib.
- **Resource trackers** attach to materialization units and give you garbage collection: when jitted code is no longer needed, you can remove it.

```cpp
auto jit = llvm::orc::LLJITBuilder().create();
auto& dylib = (*jit)->getMainJITDylib();

// ORDER MATTERS: imports must be added before the code that uses them.
(*jit)->addIRModule(dylib, make_imports_module());
(*jit)->addIRModule(dylib, llvm::orc::ThreadSafeModule(std::move(mod), std::move(ctx)));

// Bind imports: ORC hands you a mangler; you supply mangled-name -> pointer.
auto mangle = llvm::orc::MangleAndInterner(es, (*jit)->getDataLayout());
dylib.define(llvm::orc::absoluteSymbols({
    { mangle("cblas_dgemv"), llvm::orc::ExecutorSymbolDef(
          llvm::orc::ExecutorAddr::fromPtr(&cblas_dgemv), {}) },
}));

// Everything compiles in memory. You just get a pointer back.
auto sym = (*jit)->lookup("graph_dsl_run");
auto* run = sym->toPtr<void(*)(double*, double*)>();
```

Building the module means specializing for the **target triple** and data layout, then filling in basic blocks — each of which must end in exactly one terminating instruction:

```cpp
auto mod = std::make_unique<llvm::Module>("graph_dsl", *ctx);
mod->setTargetTriple(tm->getTargetTriple().str());   // arch-vendor-os-env
mod->setDataLayout(tm->createDataLayout());

auto* fn = llvm::Function::Create(fnTy, llvm::Function::ExternalLinkage,
                                  "graph_dsl_run", mod.get());
auto* entry = llvm::BasicBlock::Create(*ctx, "entry", fn);
builder.SetInsertPoint(entry);
```

The filling-in code looks strikingly like the C++-generation code: same context object, same loop over graph nodes, minus the string rendering.

### Emitting loops

The interesting part, because vector inputs with runtime-dynamic sizes need real loops. Sharma writes an `emit_index_loop` helper that takes a **lambda** invoked once per iteration, receiving the element index — so the binary-operation code stays simple and just calls `builder.CreateStore(...)` inside the lambda.

```cpp
// The binary-op code stays simple: it just calls a store inside the lambda.
emit_index_loop(builder, len, [&](llvm::Value* index) {
    auto* l = builder.CreateLoad(ty, builder.CreateGEP(ty, lhs, index));
    auto* r = builder.CreateLoad(ty, builder.CreateGEP(ty, rhs, index));
    builder.CreateStore(builder.CreateFMul(l, r),
                        builder.CreateGEP(ty, dst, index));
});
```

Inside the helper you build the loop by hand:

```cpp
void emit_index_loop(llvm::IRBuilder<>& b, llvm::Value* len, auto body) {
    auto* fn   = b.GetInsertBlock()->getParent();
    auto* pre  = b.GetInsertBlock();
    auto* head = llvm::BasicBlock::Create(ctx, "loop.header", fn);
    auto* bodyB= llvm::BasicBlock::Create(ctx, "loop.body",   fn);
    auto* exit = llvm::BasicBlock::Create(ctx, "loop.exit",   fn);

    b.CreateBr(head);                       // 1. unconditionally into the header
    b.SetInsertPoint(head);

    // 2. A phi node's value depends on HOW you reached it. Coming from the
    //    preheader, the index is 0.
    auto* index = b.CreatePHI(b.getInt64Ty(), 2, "i");
    index->addIncoming(b.getInt64(0), pre);

    // 3. condition -> body or exit
    b.CreateCondBr(b.CreateICmpULT(index, len), bodyB, exit);

    b.SetInsertPoint(bodyB);
    body(index);                            // 4. the caller's lambda

    // 5. the back edge: the second way you can arrive at the phi
    auto* next = b.CreateAdd(index, b.getInt64(1));
    b.CreateBr(head);
    index->addIncoming(next, b.GetInsertBlock());

    b.SetInsertPoint(exit);                 // 6. done
}
```

The payoff: **2D loops come free** by calling `emit_index_loop` recursively. Conditionals are simpler still:

```cpp
// parse left, right, condition -- then one instruction
auto* result = builder.CreateSelect(cond, lhs, rhs);
// if cond is a vector, wrap the whole thing in an index loop
```

**Binding imports** is easy with ORC: it hands you a mangling lambda, you mangle your function names, and you supply a symbol map from mangled name to function pointer. Done.

### The payoff: free profiling

Because the system *understands* the computation, flipping a boolean injects instrumentation instructions before and after every function call in the lowered IR. Suddenly you can see that matrix multiplications took ~70 ms total while transposes took ~13 ms — attributed per operation, with source locations.

This is the thing you fundamentally **cannot** do with eager code. There, you have to ask the user to instrument their own program. Here it's one boolean and zero user effort.

## Backend #3: an Apple GPU, over a weekend

Having built the LLVM path, Sharma tried something on a whim: retarget the same DSL to the GPU in his Mac. It turned out not to be much harder.

Apple's **MPS Graph** (Metal Performance Shaders) is the target, written in **Objective-C++**. The user-facing change is a **single decorator**: `@cpu` becomes `@gpu`. Same graph, same Python, same C++.

Verifying parity is trivial — build the graph once, compile it for both targets, assert the results match.

The Objective-C++ experience gets a genuinely funny detour. Sharma had never written it before:

> *"Everything is an object somehow, and you do message passing instead of structured object-oriented programming. The code is very unreadable to me. I had to ask AI to explain how to write this code multiple times."*

An audience member asked what an `NSObject*` actually is — a smart pointer? *"Good question. I don't know."* But the tests all passed on the GPU.

The point isn't Metal. It's that the graph is **not tied to any IR**. Different optimizations, different backends, different front ends — which is exactly what a good graph DSL should deliver. On the state-estimation benchmark the GPU version runs much faster than the CPU version, though only at ~60% utilization, which he's frank about not having tuned further: *"I'm not a GPU engineer."*

## One optimization, and why LLVM didn't do it

Since everything is a single graph, graph-level optimizations are available. Sharma demonstrates the simplest useful one.

In the state-estimation code, the transition matrix is **transposed inside a loop that runs 12 times** — the same transpose, twelve times over.

**Node deduplication** is the fix, and it's the template for most graph optimizations:

```cpp
Graph dedup(const Graph& old) {
    Graph out;
    std::unordered_map<Signature, NodeId> seen;
    std::unordered_map<NodeId, NodeId> rewritten;

    for (NodeId id : topological_order(old)) {          // always inputs-first
        Node n = old[id];
        for (auto& arg : n.args) arg = rewritten.at(arg);   // rewrite inputs

        // Signature = op + rewritten args. Deliberately EXCLUDES the source
        // location, so identical operations written in two places still merge.
        Signature sig = hash(n.op, n.args);

        auto [it, inserted] = seen.try_emplace(sig, NodeId{});
        if (inserted) it->second = out.add(n);
        rewritten[id] = it->second;
    }
    return out;
}
```

Result on the benchmark: **148 nodes down to 105**.

The GPU numbers barely moved. Sharma's first hypothesis was that MPS Graph had already spotted the repetition — then he used his own profiler and corrected himself: transposes just aren't expensive on that GPU.

The best question of the session followed: **why doesn't LLVM's common subexpression elimination handle this already?** The answer is precise and worth remembering — the transpose is an **external function call**, so LLVM can't prove hoisting it out of the loop is safe, because it might have side effects. Asked whether he'd tried tagging it with the right attributes (`pure`, and friends) so LLVM could reason about it, Sharma says plainly that he hadn't, and that it would likely work. *"Once you have LLVM, you have all the optimizations for free."*

He's similarly candid closing out the section: the Metal code is partly AI-generated and not production grade; not every graph op is meaningful on every backend (matrix multiply may mean nothing on a limited FPGA); and **the graph is a common parsing layer, not a miracle optimizer.** You still have to do the compiler work.

## Type safety across the boundary

Why hasn't type safety come up until now? Because in-memory JIT gives it to you by construction — you generated the code with a known signature in the same address space, so barring a bug in your own lowering, the pointer you get back is the type you expect.

Two places still need attention:

**At graph construction.** When a user reflects a function into the graph, embed the expected signature in the node. Reflection makes this easy — that's the whole point.

**At load/JIT time**, but only if you **serialize**. Cache a compiled `.so` to disk and load it later and you inherit the classic hazard: an application loading three modules built at three different times, one against an older API. There's no simple load-time detection, and you segfault.

Sharma has been pushing this idea for years — talks at CppCon and C++Now, plus a paper he's reviving as part of this work. The requirement is modest: a **standardizable way to express the signature of a struct or function on an API boundary**. Recurse over the members, serialize everything into a hash or JSON or map, do it diligently, and you have a true signature per type.

The API he likes best isn't a single symbol lookup but a **symbol map**:

```cpp
// Instead of: dlsym("compute") and HOPING the pointer matches your cast.
// Expose a list, and match on signature:
struct SymbolEntry {
    std::string_view signature;   // serialized from reflection
    void*            fn;
};
extern "C" SymbolEntry compute_symbol_map[];

// Loop it; find the entry whose signature is the one you want.
// If someone changes compute() from double to float, they ADD an entry
// rather than breaking every downstream consumer.
```

Two audience challenges landed here, and Sharma conceded both gracefully:

- **"Why not just mangle the name, like C++ already does?"** He initially objects that mangling doesn't let users load the older overload — the questioner points out that's precisely how overloading works. *"Okay, that is an interesting point."* It would eliminate the indirection and the load-time hit, at the cost of a clean error message when nothing matches.
- **Inexact overload matches** (conversions, a dropped `const`) would need a runtime symbol map, looping signatures to find the closest and generating a runtime cast wrapper — workable, but you'd have to enumerate which mismatches are safe, case by case.

## Where does this belong?

Not in the standard, mostly. The DSL and the IR **belong in libraries**. What might be worth standardizing is narrower: **boundary descriptions** for structs and functions, some **annotations** to make source-generating jitted functions easier, and perhaps a **typed `dlopen`**.

There's one wish he can't have. In Python, the entire UX is a decorator on a function. In C++ you're stuck calling `compile(...)`-style functions instead, because doing it with an annotation would require code generation plus symbol renaming at compile time. He found papers discussing something similar; it isn't an easy problem, and he doesn't expect it soon. *"It's ugly, but it is what it is."*

## What this talk actually argues

Strip away the implementation and the claim is simple. Reflection gave C++ the ability to understand code at compile time, and that's a real advance — but the code arriving from users arrives *later*, and the traditional C++ answer has been to write a parser and accept the technical debt.

Tracing makes the parser unnecessary. Operator overloading over proxy values captures the user's intent as a graph, in either C++ or Python, with no new syntax and no lost editor tooling. From there the graph is just an IR you own: deduplicate it, lower it to C++ source, LLVM IR, or Metal, JIT it with ORC, and hand back a typed callable — with profiling injected on a boolean.

> **Runtime DSLs are just programming languages. We're doing all the work anyway. Let's treat them as such.**
