---
layout: single
title: "C++ - Catching Bugs Early: Validating C++26 Contracts with Static Analysis"
date: 2026-05-22 10:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - static-analysis
permalink: "2026/05/22/cpp-contracts-static-analysis"
---
[Catching Bugs Early: Validating C++ Contracts with Static Analysis - Mike Fairhurst & Peter Martin - CppCon 2025](https://www.youtube.com/watch?v=3DDqDKaKmio)

In this CppCon 2025 talk, **Mike Fairhurst** (GitHub) and **Peter Martin** (Bloomberg's Product Security Team Leader) present joint research from GitHub and Bloomberg on using static analysis to validate the new C++26 contracts feature *before the code ever runs*. The central question: if C++26 finally gives us a way to write `pre()`, `post()`, and `contract_assert()` directly in our code, can tools catch contract violations at analysis time — without waiting for runtime?

The short answer: **yes, in a surprisingly large fraction of cases** — their prototype validated 95% of contract-guarded call sites in a real Bloomberg codebase, in roughly 24 ms per call.

## C++26 Contracts: A Quick Primer

C++26 (per P2900) introduces three new language keywords for **contract assertions** that make API expectations explicit and machine-checkable:

| Keyword | Where it lives | What it expresses |
|---|---|---|
| `pre(...)` | function declaration | Precondition at function entry |
| `post(...)` | function declaration | Postcondition at normal function exit |
| `contract_assert(...)` | function implementation | Internal assertion within a function |

In practice this looks like:

```cpp
// foo.h
int divide(int a, int b) pre(b != 0);
int abs(int x) post(r : r >= 0);
void step(double dt);

// foo.cpp
int divide(int a, int b) { return a / b; }
int abs(int x) { return x < 0 ? -x : x; }
void step(double dt) {
    // ...
    contract_assert(dt > 0.0);
    // ...
}
```

The standard defines **four evaluation semantics** that determine when checks run and what happens on a violation:

- **`ignore`** — no checking
- **`observe`** — report, then continue
- **`enforce`** — report, then terminate
- **`quick-enforce`** — simply terminate

Crucially, contract assertions are **not intended for control flow or error handling** — they are redundant checks. The standard even makes variables referenced from the predicate implicitly `const`, so a contract can't accidentally mutate program state.

## Why Static Validation Matters

Consider a function with a simple precondition:

```cpp
std::string format_hour(int hour)
    pre(hour >= 0 && hour < 23)
{
    return std::to_string(hour) + ":00";
}
```

Some call sites are trivially analyzable:

```cpp
format_hour(1);   // always valid
format_hour(24);  // always invalid
if (std::rand() == 0) {
    format_hour(24);  // sometimes invalid
}
```

But real-world code is messier:

```cpp
int main(int argc, char* argv[]) {
    int hour = std::atoi(argv[1]);
    std::string formatted = format_hour(hour);  // may violate
}
```

Adding a range check above the call site makes the contract provably satisfied:

```cpp
if (hour < 0 || hour > 23) {
    std::cerr << "Error: Hour must be between 0 and 23\n";
    return 1;
}
std::string formatted = format_hour(hour);  // contract satisfied
```

The motivation for catching this at analysis time rather than runtime is stark: **the cost of fixing a bug is roughly 30× higher in production than during development** (NIST, 2002). Static validation pushes detection as far left in the lifecycle as possible.

## The Static Analysis Problem

The speakers are upfront about the boundary of what's possible:

> **This is not formal verification.**

You cannot statically prove that *every* contract assertion will hold — predicates may depend on runtime state. The goal is more pragmatic: classify call sites into three buckets:

1. **Cases we can always verify** without running the program
2. **Cases that require context** we don't have, and so can't verify
3. **Cases where we can infer** validity with enough deductive reasoning

A useful tool needs to be **optimistic and not noisy** (prefer true positives at the cost of some false negatives) rather than strict and exhaustive. False positives erode developer trust faster than missed bugs.

## Tool 1: CodeQL — Querying Code Like a Database

GitHub's CodeQL treats source code as a queryable database. An extractor turns the codebase into a relational schema (expressions, statements, types, call graphs, control flow), and queries written in the QL language run against it.

A trivial CodeQL query — find every function call and its target — fits in under 100 characters:

```ql
import cpp

from FunctionCall fc, Function f
where fc.getTarget() = f
select fc, f
```

CodeQL exposes four key dimensions of the program:

- **Type information** — classes, structs, primitives
- **Syntax tree** — operators, operands, blocks
- **Control flow graph** — conditions, loops, exits
- **Call graph** — call sites, overload resolution

For contract validation, the most useful CodeQL feature is its **range analysis library** (`semmle.code.cpp.rangeanalysis.SimpleRangeAnalysis`), which can derive lower and upper bounds for integer expressions throughout the program.

A simple range-based contract violation predicate looks like:

```ql
predicate parameterContractViolation(Parameter p, int lb, int ub) {
    exists(MacroInvocation mi, ComparisonOperation cmp |
        mi.getMacroName() = "assert" and
        cmp = mi.getAGeneratedElement() and
        cmp.getLeftOperand() = p.getAnAccess() and
        cmp.getOperator() = ">" and
        lb <= cmp.getRightOperand().getValue().toInt()
    )
    or
    ...
}
```

## What Contracts Can and Cannot Do

The C++26 contract specifier has interesting properties from an analysis perspective:

| Capability | Implication for static analysis |
|---|---|
| **Cannot mutate inputs** (implicit `const`) | Greatly simplifies reasoning |
| **Can call functions** | Predicates may be arbitrarily complex |
| **Can allocate memory** | Tremendous challenge for analysis |
| **Can have undefined behavior** | ¯\\\_(ツ)\_/¯ |

So this is valid C++26 (though inadvisable):

```cpp
int f(int x)
    pre (x++)  // invalid — x is const in this context
    pre (memcpy(malloc(10), f, sizeof(x)) == rand())  // valid, albeit unhinged
    post (r : r++)  // invalid — r is const
{
    // ...
}
```

## Tool 2: Z3 — When CodeQL Isn't Enough

CodeQL's range analysis handles simple bounds, but it struggles with non-trivial logical relationships:

```cpp
assert(base != 0 || power != 0);
assert(day <= 28 || month != 2);
assert(length != 0 || ptr == NULL);
assert(min <= max);
```

For these, the team reaches for **Z3**, Microsoft Research's SMT (Satisfiability Modulo Theories) solver. Z3 takes a logical formula and either finds a model that satisfies it or proves no such model exists.

A trivial Z3 query in SMT-LIB looks like:

```scheme
(declare-const x Int)
(declare-const y Int)
(assert (= (* x x) (* y 3)))
(check-sat)
(get-model)
; sat
; ((define-fun y () Int 3)
;  (define-fun x () Int (- 3)))
```

### Why a CodeQL Query Needs Z3

CodeQL is a logical query language, but it has two important limitations for contract validation:

- **Dynamic logic** — being able to call Z3 from a CodeQL query is almost like adding `eval()` to the analysis
- **Optimization differences** — Z3 is optimized to find *any* satisfying model, while CodeQL is intended to find *every* match

### Translating C++ to SMT

The team's pipeline turns C++ source into SMT-LIB constraints. For:

```cpp
void f(int x) {
    /*@ requires @*/
    assert(x > 0);
    ...
}
void g() {
    ...
    f(y);
    ...
}
```

CodeQL extracts the contract from the callee:

```scheme
(declare-const valueType_x Int)
(define-fun precondition_1 () Bool
    (> valueType_x 0))
```

…and the inferred range of arguments at the call site:

```scheme
(assert (<= valueType_x 256))
(assert (>= valueType_x 0))
```

A final query asks Z3 whether the *negation* of the precondition is reachable under the call-site constraints:

```scheme
(assert (not (and precondition_1 precondition_2 precondition_3)))
(check-sat)
(get-model)
```

If Z3 returns `sat`, it has found a counter-example — a witness violation. If `unsat`, the contract is provably satisfied at this site.

### What Translates Cleanly to SMT

Not every C++ operation maps to SMT theory equally well:

| C++ construct | Range analysis | SMT support |
|---|---|---|
| `+`, `-` | Full | Full |
| `?:`, `&&`, `\|\|`, `!` | Full | Full |
| `*` | Limited | Full |
| `/` | None | Partial |
| Bitwise (`&`, `\|`, `<<`, `>>`, `~`) | Limited | None |
| Function calls, arrays, derefs (`()`, `[]`, `*`) | None | None |

Pointer dereferences, arbitrary function calls, and bitwise operations remain hard frontiers.

## Case Study: Validating Contracts on Bloomberg's BDE

C++26 contracts aren't in production code yet, so the team needed a proxy. They picked **BDE** (Basic Development Environment) — Bloomberg's open-source foundational C++ library, with ~1.8k stars on GitHub. BDE has two conventions that approximate C++26 contracts:

1. **Doxygen-style "behavior is undefined unless …"** comments on declarations — semantically close to `pre(...)`, but not compiler-readable.
2. **`BSLS_ASSERT` macros** at the top of function implementations — a family of build-flag-configurable assertion macros that mirror C++26's evaluation semantics:

```cpp
int Calendar::getNextBusinessDay(Date *nextBusinessDay,
                                  const Date& date,
                                  int nth) const
{
    BSLS_ASSERT(nextBusinessDay);
    BSLS_ASSERT(Date(9999, 12, 31) > date);
    BSLS_ASSERT(isInRange(date + 1));
    BSLS_ASSERT(0 < nth);
    // ...
}
```

The team inferred contracts from these `BSLS_ASSERT` statements.

### The "Spec Database" Logistical Problem

CodeQL sees what the compiler sees — typically the user's source plus *library headers* (not library source). But `BSLS_ASSERT` statements live in BDE's **source files**, not headers. This wouldn't be a problem for real C++26 contracts (which live on function declarations in headers), but it forced the team to design a workaround: a one-time analysis of the library produces a **"spec database"** — SMT-encoded contracts associated with library functions — that the per-program analysis then consumes.

This separation is itself an interesting architectural insight: library vendors could ship spec databases alongside binaries.

### The Numbers

The team identified ~6,200 candidate projects calling BDE date functions, then selected the top 1% of unique callers for diversity — 62 CodeQL databases. After restricting to contracts based on simple arithmetic/logical expressions over numeric and boolean types (covering ~33% of BDE Date functions — 79 contracts on 59 functions), they analyzed 2,849 call sites.

The result:

| Metric | Value |
|---|---|
| Call sites validated as in-contract | **95%** |
| Possible violations (unverifiable) | **5%** |
| Average execution time per call site | **24 ms** |

They also injected synthetic bugs into previously-validated code — both out-of-contract values assigned in conditional paths and values modified inside loops — and the analysis successfully flagged them. The technique catches real violations, not just trivial ones.

## False Positives: The Two Common Patterns

Since the initial evaluation, the team identified two recurring causes of false positives:

### 1. Unconstrained Ranges

```cpp
void f(int x) {
    g(x);  // g has a contract; x is unconstrained, falls back to full type range
}
```

When range analysis only has type information (no narrowing guard), the tool assumes the full range of `int` and flags many calls as potentially violating.

### 2. Contract Forwarding

```cpp
void f(int x) {
    BSLS_ASSERT(x < 10);  // upstream caller is "forwarding" the contract
    g(x);
}
```

Here `f` is itself asserting its precondition before forwarding to `g`. The range analysis was not using contract assertions as facts when the failure didn't exit the program — a fixable limitation.

## Future Work: Going Deeper with SSA

The team is exploring a more powerful analysis backed by **Static Single Assignment** form. SSA rewrites variables so each is assigned exactly once, making data flow explicit:

```cpp
// Original
int f(int param) {
    int x = 0;
    if (param < 10) {
        x += param;
    }
    return x;
}

// SSA form
f_ssa(param0) {
    x0 = 0
    if (param0 < 10) {
        param1 = param0
        x1 = x0 + param1
    }
    x2 = x0 or x1   // phi node
    return x2
}
```

### Bound Provenance

A key insight from extending range analysis: not all bounds are equally trustworthy. They tag each lower/upper bound with a **provenance**:

- **Type range** (confidence: very low) — only type info constrains the bound
- **Bounded** (confidence: medium) — the bound is constrained by a guard condition
- **Widened** (confidence: low) — the bound was widened to the nearest power of two for performance

This provenance lets the analysis make better decisions about when to trust an inference versus when to bail out.

### SSA → SMT Compilation

An SSA program translates almost mechanically into SMT-LIB, with phi nodes becoming disjunctions:

```scheme
(declare-const param0 Int)
(declare-const x0 Int)
(assert (= x0 0))
(declare-const cond1 Bool)
(assert (= cond1 (< param0 10)))
(declare-const x1 Int)
(assert (= x1 (+ x0 param0)))
(declare-const x2 Int)
(assert (or (and (= x2 x0) (not cond1))
            (and (= x2 x1) cond1)))
```

This gives the SMT solver the full data-flow picture, not just call-site snapshots.

## Try It Yourself

The team has **open-sourced the project** at [github.com/advanced-security/codeql-contracts-smt-z3](https://github.com/advanced-security/codeql-contracts-smt-z3). They acknowledge known bugs around missing constraints, invalid SMT, and incorrect SMT, and welcome bug reports and pull requests.

## Key Takeaways

1. **C++26 contracts are checkable both at runtime *and* statically.** The four evaluation semantics (`ignore`, `observe`, `enforce`, `quick-enforce`) handle the runtime side; static analysis handles the "catch it before it ever runs" side.

2. **You cannot statically verify every contract** — but you can verify a large, useful subset. Bloomberg/GitHub measured 95% on a real codebase.

3. **CodeQL + Z3 is a powerful combination.** CodeQL extracts structured facts from C++ code; Z3 handles the logical reasoning CodeQL cannot. The integration effectively gives CodeQL a dynamic logic capability.

4. **Library specs may need to ship separately from headers.** Today's prototype works around this with a "spec database"; C++26's `pre(...)` syntax on declarations sidesteps the problem entirely.

5. **Bound provenance matters.** Range analysis is more useful when the tool knows *why* it believes a bound holds — type vs. guard vs. widening — so the SMT layer can weight evidence accordingly.

6. **Write contracts now.** Even if the toolchain isn't fully mature, the tooling will improve — and contracts written today become statically checkable as the analyzers catch up. As the speakers close: *"Write contracts! The tooling will only get better and better."*
