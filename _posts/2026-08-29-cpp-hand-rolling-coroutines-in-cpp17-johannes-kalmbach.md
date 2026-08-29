---
layout: single
title: "C++ - No Compiler Required: Hand-Rolling C++20 Coroutines in C++17 (Johannes Kalmbach, C++Now 2026)"
date: 2026-08-29 16:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - coroutines
  - metaprogramming
permalink: "2026/08/29/cpp-hand-rolling-coroutines-in-cpp17-johannes-kalmbach"
---

[Johannes Kalmbach - No Compiler Required: Hand-Rolling C++20 Coroutines in C++17 - C++Now 2026](https://www.youtube.com/watch?v=WabG-ku-Osk)

Johannes Kalmbach opens by puncturing his own title:

> My name is Johannes Kalmbach, and as you are now all here, of course we are going to require a compiler.

He is a PhD student at Freiburg, in what he hopes is the final year, and he develops the QLever RDF and SPARQL graph database — an open-source project written liberally in C++20, everything except modules. Recently he and his collaborators founded a small company to sell commercial support for it.

Then a customer request arrived.

If you have maintained an open-source project you know the genre. Every so often someone asks whether you have considered rewriting it in Rust. This one asked whether they could have it in an older C++ standard. A few weeks later the ask sharpened into an actual business proposal: not C++14 but C++17, not the whole codebase but part of it, and with the customer contributing engineering resources. For a newly founded company, that is a yes.

The migration as a whole is a story for another day. This talk is about the coroutines.

## The solution they actually shipped, and why it nagged

The pragmatic answer was to replace each generator by hand. Write a function that returns the next value each time it is called and a `nullopt` when it is finished, inherit from a base class that turns that single `get()` into all the iterator boilerplate needed to be a proper input range, done.

It works. The project shipped. Kalmbach is not entirely satisfied, for two reasons.

The first is readability. In the C++20 generator world an enormous amount of boilerplate is handled by the compiler and you never see it. Rewriting by hand drags all of it back into the light.

The second is worse:

> Some bugs arose in this rewriting. The reason behind this was that mostly this rewrite was done by external developers from our partner company, and as those obviously in their day jobs are not really working on C++20, they also are not that familiar with the details of coroutine semantics. And you need to understand something — even if you migrate *from* something, you also have to understand the details of the thing you're migrating from. And in C++, object lifetimes is always one of the first things where things can go wrong.

That is the sentence the rest of the talk is built on. Migrating away from a feature requires understanding it *better*, not less. Every implicit lifetime rule the compiler was enforcing silently is now your problem, and you will not be told when you get one wrong.

So he asked whether there was a better way — meaning more generic, and ideally automatic, since their approach required looking at every coroutine individually and inventing a bespoke solution for each. He ran experiments. He fell, in his words, into a very deep rabbit hole. The talk is what he found in there.

## What has to be replaced, and what does not

The machinery around a C++20 coroutine has four moving parts, and the rewrite treats them very differently.

**The coroutine itself** — a function body containing `co_yield`, `co_await`, or `co_return`, plus a return type that tells the compiler what those keywords mean.

**The compiler-synthesized state machine.** The compiler takes the body and produces a coroutine frame: the promise object, the function parameters, the local variables that must survive suspension (C++20 coroutines are stackless, so these live in the frame rather than on a stack), and the concrete resume and destroy functions. This is the piece that must be rebuilt by hand, individually, for every single coroutine — because it depends entirely on the body.

**The coroutine type and its promise type.** Good news here: the promise types can stay *unchanged*. The replacement infrastructure is built to consume them as-is. Everything the promise specifies — `initial_suspend`, `final_suspend`, `yield_value`, `return_void`, `unhandled_exception` — keeps working.

**`std::coroutine_handle`.** The library type that lets outside code resume a suspended frame, destroy it, and reach the promise object inside. This needs a generic replacement, written once.

So the work splits cleanly: write the infrastructure once, then do the state machine per coroutine. Which is precisely why automating the per-coroutine part is the endgame.

## Example A: lowering an iota generator

The simplest possible starting point — a generator with function parameters, no local variables, and a single `co_yield`:

```cpp
Generator<int> iota(int start, int end) {
    while (start < end) {
        co_yield start++;
    }
}
```

The hand-lowered version introduces a local frame class using CRTP over a base that holds everything common to all frames:

```cpp
Generator<int> iota(int start, int end) {
    struct Frame : CoroFrameBase<Frame, Generator<int>::promise_type> {
        // function parameters, stored in the frame
        int start;
        int end;

        // storage for the awaiter produced by the co_yield
        CoroStorage<std::suspend_always, true> awaiter_0;

        CoroHandle<> resume_impl() {
            switch (suspendIndex) {
                case 0: break;               // implicit start
                case 1: goto suspend_label_1;
            }

            while (start < end) {
                MY_CO_YIELD(1, awaiter_0, start++);
                suspend_label_1:;
            }

            MY_CO_RETURN();
        }
    };
    return Frame::ramp(start, end);
}
```

Two details carry the whole design.

The **switch-and-goto cascade** at the top is how resumption works. Every coroutine has at least two suspension points — index 0 is the implicit one at the very beginning, since a coroutine may suspend before running a single statement — plus one per `co_yield` or `co_await`. On resume, you switch on a stored index and jump to the matching label. Kalmbach's justification for `goto` is disarming: nobody writes `goto` inside a real coroutine body, so the mechanism is free for the taking.

And **falling off the end of a coroutine is not falling off the end of a function.** There is an implicit `co_return` with real work behind it, which is why the body ends in a macro rather than nothing.

## The macros, and the three flavors of `await_suspend`

`co_yield x` is not one operation. It calls `yield_value(x)` on the promise, which returns an awaiter; that awaiter is placement-new'd into the frame's buffer; the awaiter is awaited, which may return control to the caller; on resume you land at the label, call `await_resume()` on the awaiter, and then explicitly destroy it. Everything that survives a suspension has its lifetime managed by hand.

The `co_await` expansion follows cppreference closely, and the interesting part is the three return types `await_suspend` may have:

- **`void`** — suspend unconditionally and return control to whoever is above you on the stack.
- **`bool`** — a runtime decision. `true` means suspended, behave as in the `void` case; `false` means carry on without suspending.
- **A coroutine handle** — **symmetric transfer.** Suspend this coroutine, but instead of returning to the caller, resume the returned coroutine directly. Control hands off sideways.

Symmetric transfer is the reason for a design choice visible throughout the infrastructure: the internal resume functions never return `void`, they return a coroutine handle. An empty handle means *return to the caller*; a non-empty one means *resume this next*. The handle's public `resume()` then runs a trampoline loop, resuming whatever it is handed until it gets an empty handle back.

Real compilers do this differently, via the mandatory tail-call optimization the standard requires for symmetric transfer. Kalmbach's reasoning is practical:

> If you're not the compiler, it's a little bit harder to enforce tail call optimization in all cases.

For readers who want the full picture on symmetric transfer, he points at Lewis Baker's writing as the compact overview of everything worth knowing.

`co_return` calls `return_void()` or `return_value(x)` on the promise, marks the coroutine as done, destroys every local still alive at that point — hence its variadic argument list — and then awaits the final suspend.

## The coroutine handle, rebuilt

The replacement handle is a type-erased pointer to a pair of function pointers, one to resume and one to destroy:

```cpp
template <typename Promise = void>
class CoroHandle {
    struct VTable {
        CoroHandle<> (*resume)(void*);
        void (*destroy)(void*);
    };
    VTable* vtable_ = nullptr;
    // ...
};
```

This mirrors what GCC and Clang actually do — two function pointers stored in the frame, providing the type erasure a handle fundamentally requires. Storing a pointer to the vtable rather than the two pointers directly costs an indirection and buys the lightest possible handle: a single pointer.

`done()` uses the same convention the real implementations use: setting the resume function pointer to null means *this coroutine has finished, you may not resume it*.

The genuinely sketchy part is `promise()` and `from_promise()`. Getting from a handle to the promise object inside the frame, and back again, is done by laying the vtable member and the promise object adjacent in the frame and doing offset and alignment arithmetic between them. Kalmbach is refreshingly honest about the standing of this:

> I'm sure there's something that is, according to the standard, not guaranteed for types that are not simple enough. But in practice it works. You can `static_assert` that this is correct.

He adds that there is probably a missing `std::launder` after the `reinterpret_cast` too.

## The ramp function

Setting up a coroutine — the "ramp", to use the usual term — is a fixed sequence:

1. **Allocate the frame.** Coroutines are stackless, so the state goes on the heap or wherever your allocator says. This is customizable, because the promise type can supply a custom allocation function, and that function receives the coroutine's arguments. An audience member asks why the arguments get passed to allocation at all; the answer is that your first parameter might *be* an allocator or a memory resource. Note that these arguments are passed by reference and must not be moved from — they still have to be stored in the frame afterwards.
2. **Placement-new the frame** into that buffer.
3. **Call `get_return_object()`** on the promise, and hold the result on the stack.
4. **Await the initial awaiter.**

Step four splits. If the initial suspend suspends, you return the return object immediately. If it does not, you run the coroutine body until it suspends of its own accord, and *then* return the return object. Both paths hand the same object back to the caller; they differ only in how much of the body has run first.

## Local variables: the `CoroStorage` problem

Example B is where it gets real — a generator that prefixes each string in a range:

```cpp
Generator<std::string> prefixed(Range strings, std::string prefix) {
    for (auto it = strings.begin(); it != strings.end(); ++it) {
        co_yield prefix + *it;
    }
}
```

The iterator and the end iterator live across the suspension, so they go in the frame. But there is a subtler one, and Kalmbach flags it as the historically dangerous case:

> This expression `prefix + *it` creates a temporary string which is then yielded, and this temporary string we also have to keep alive until the suspension returns control to us. This was also where in initial implementations all the bugs were — also in the compilers — these things that we have to keep alive that are not super obvious.

Locals become `CoroStorage` members, initialized with a `CO_INIT` macro and accessed through a `CO_GET` macro. And `CoroStorage` takes **two** template parameters, which is the design's most interesting wrinkle:

```cpp
template <typename Ref, bool IsOwning>
class CoroStorage { /* ... */ };
```

Why two? Because reference-ness and ownership are independent. A `const&` or `&&` local initialized from a temporary *is* a reference, but it also has to keep that temporary alive — C++'s lifetime extension rule, which you now have to implement by hand. So `IsOwning` decides whether the buffer holds an object or merely a pointer to one, independently of whether the variable is a reference.

Underneath is an aligned buffer, a `reinterpret_cast`, and — this being one of the two genuine use cases for it — a `std::launder`, because the address holds an object but the member's declared type is a character buffer.

Kalmbach then poses three design questions to the room, and they are good ones.

**Why does `get()` return a proxy object by value holding the reference as a data member, instead of returning the reference directly?** Because value category has to be preserved exactly. If `CO_GET(x)` were a function call returning an rvalue reference, then passing it to a function would apply move semantics — where the original code, with a plain named rvalue-reference variable, would not have moved without an explicit `std::move`. The proxy restores the original behavior. Asked whether this ever bit him in real code, he concedes the concrete example looks artificial, but points out that in generic code `auto&&` deduction means anything can happen.

**Why a placement-new macro instead of an `emplace`-style member function?** Two reasons, and the audience supplies both. Copy elision: initializing from a function that returns an object directly gets guaranteed elision with placement new, which a forwarding `emplace` cannot reproduce. And initialization syntax, which the macro sidesteps entirely by grabbing raw tokens and letting the caller supply the punctuation. The example is the classic:

```cpp
std::string x(97, 'b');   // 97 copies of 'b'
std::string y{97, 'b'};   // "ab"
```

Parentheses and braces are not interchangeable, so the rewriter must not choose for you. As one attendee summarized it: you're just grabbing tokens and looping them in — if it compiles, it's fine.

## Exceptions, and the two nested try blocks

Example C puts a `co_yield` inside a `try` block, with `std::stoi` as the thing that might throw. Two problems appear at once.

**You cannot `goto` into a `try` block.** Not with any trick:

> Not even with non-portable ASM goto tricks will it let you do this, and for good reasons, because it will probably never work.

The workaround is a two-stage jump. Jump to a label immediately *before* the try block, enter the try block normally, and then a second switch *inside* the try dispatches to the actual suspension label.

**You have to do your own stack unwinding.** Exceptions can escape from any subexpression, and the locals must be destroyed in reverse construction order. The compiler's real implementation cooperates with the platform's unwinder; a source-to-source rewrite cannot. So the frame carries one `bool` per local recording whether it is currently within its lifetime, plus a function that walks them in reverse and destroys the live ones.

That function cannot short-circuit. Nested scopes mean liveness is not monotone — variables declared later may still be alive while earlier ones in an inner scope have already been destroyed. So every flag gets checked, every time. Kalmbach's defense is that this only runs on the exception path, "and in the exception case we are used to some overhead as C++ developers."

There are two nested try blocks rather than one. The inner one destroys the scope's locals and rethrows; the outer holds the user's actual catch clauses. Splitting them avoids duplicating the destruction code across multiple catch clauses.

And the catch clauses themselves need almost no rewriting at all — because C++20 forbids `co_await` and `co_yield` inside a catch block. It is the one place where nothing has to be done.

The exception path in the base class has an ordering requirement worth noting: the promise's `unhandled_exception()` must be called from *inside* the catch handler, so that the active exception is still available to it. Then the coroutine is marked done, and the final suspend is awaited — because `final_suspend` runs after a throw just as it runs after a return.

## What cannot be rewritten

Some limitations are mechanical annoyances:

- **Lambdas as locals.** You cannot name the closure type, so you cannot declare a buffer for it. Workaround: rewrite the lambda as an explicit closure struct first. More boilerplate, no conceptual problem.
- **Range-based for loops.** They have hidden local variables. Rewrite to an explicit iterator loop first.
- **Complex expressions in `co_yield`.** Multiple temporaries whose destruction order is unspecified and varies between compilers. Workaround: hoist the value into a named variable on the preceding line and yield that. Kalmbach notes this is exactly where the early GCC coroutine bugs lived, and says the exercise gave him sympathy for why.

One limitation is fundamental, and it produced the sharpest exchange of the talk. **A by-value function parameter cannot be handled.** The temporary backing it must live until the end of the enclosing *full expression*, not until the function returns — and that object is materialized by the caller, invisible to any source-to-source rewrite. His illustration of why this is structural:

> If you have a function that takes a string by value, and a function that does the same thing but takes a string by rvalue reference, they boil down to the exact same assembly — because this difference is done by the call side and not by the function.

So the case you cannot reproduce is a function that takes a parameter by value and relies on it outliving the call: taking a `std::string` by value and returning a `string_view` into it. It looks obviously dangling and it is nevertheless perfectly valid, so long as the caller uses the result before the semicolon. And in a coroutine, that semicolon can arrive very late — after a suspension, after everyone else has done a great deal of work.

Kalmbach's position on this is that such functions are legal but you should not write them. The room's verdict was blunter: if you write this, you should hope you are junior enough that someone is still reviewing your code.

## Going off-standard, on purpose

Here the talk turns. Once you are doing the lowering yourself, nothing forces you to reproduce C++20 semantics.

Stock coroutines are slow for two compounding reasons: the frame requires an allocation, and the handle is fundamentally type-erased. HALO — heap allocation elision — exists in theory but Kalmbach's experience is that it is unreliable and almost never fires without generalization. And the type erasure blocks inlining, so a trivial `iota` generator carries enough overhead that you would not put it in a tight loop.

But the frame type is known at the point of the rewrite. So make the handle store the whole frame rather than a type-erased pointer, template it on the frame type, and template the generator on the frame too — `Generator<int, ConcreteFrame>` instead of `Generator<int>`. The analogy he offers is that this is exactly how ranges already work: every `transform_view` has a different type, because it is templated on the function it transforms.

The critical property is that this changes the infrastructure only. The per-coroutine body rewriting stays identical — you change the thing you write once, not the thing you write every time.

The result, after some tuning of the generator class: the `iota` generator compiles to **the same assembly as hand-written `std::ranges` code**. On Clang. GCC still refuses to do all the optimizations and he has not yet worked out why.

Asked whether a big stack buffer plus a custom allocator would get there instead, he separates the two problems. Custom allocation solves the allocation — genuinely useful if your constraint is an embedded system with no heap. It does not solve the inlining, because the compiler still cannot see through the indirection into your buffer. If the goal is boiling an `iota` down to a few instructions in a couple of registers, allocation was never the whole story.

## Automating it: libclang, and a note about reflection

Everything above is tedious, error-prone, and — crucially — *mechanical*. See a local variable, check the type, check whether it is a temporary materialization, add a frame member, replace the initialization with `CO_INIT` and every access with `CO_GET`. Rule-based transformations are what tools are for.

Kalmbach frames this as a reflection question:

> If you think of it, it's some kind of very elaborate reflection. You see what is there and you make something other from it, but according to rules.

The open question is whether C++ reflection should ever expose this much — essentially the entire AST and then some. He is not holding his breath, and an attendee makes the counterpoint that if reflection could do everything, there would never be another core language change and everything would become a library. Filed under philosophical, to be continued offline.

What exists today is libclang. So he wrote a tool. It uses AST matchers to find coroutines and rewrites them into the C++17 form.

**Templates** forced a design decision. You cannot rewrite a template at definition time, because with dependent types you cannot answer the questions that matter — is this a temporary or not? You can chase it through cascades of `decltype`, and Kalmbach is not convinced it is possible even then. So the tool rewrites **concrete template instantiations** instead, explicit or implicit. Those have concrete types and rewrite normally. The other restriction, following from the evaluation-order problem, is that it only handles `co_yield` of a single variable — ideally an lvalue with no additional temporary.

The demo is a struct with a templated non-static member function that is a coroutine and uses exceptions — everything from the earlier examples plus a `this` pointer. Run CMake to produce a compilation database, run the tool, and out comes a file that compiles under `-std=c++17 -pedantic` with sanitizers on. The original coroutine is left behind inside an `#ifdef`. The output parses two numbers, hits the string `potato`, throws, catches, logs `what()`, and breaks. The address sanitizer stays quiet.

He is careful about how much to claim, which is why the demo runs in the last five minutes rather than the first:

> This tool is far from complete. That's why I only showed you in the last five minutes, because that's not the main point I'm telling you.

## The workflow that makes this maintainable

The best question of the Q&A is the one every maintainer will ask: what happens when you find a bug in the *converted* code?

The answer is the piece that turns this from a stunt into an engineering practice. **The C++20 source stays the single source of truth.** Nobody edits the generated C++17. Continuous integration runs the rewriter and then checks that the output compiles under C++17. A bug is either in the C++20 code, where you fix it, or in the rewriter, where you fix it — the C++17 code is only ever a symptom.

An attendee summarizes it neatly: you ship your client a build artifact that happens to be C++17 source, and your build process guarantees it can always be produced. Kalmbach confirms, and adds the honest caveat that this workflow is currently running as a proof of concept for a much simpler transformation — rewriting `using enum` — while roughly 98% of the actual coroutine migration was done by hand.

Two other practical notes. The tool is expensive to run, because libclang effectively performs half a compilation; on a large codebase in CI, the pragmatic move is to grep for `co_yield` and `co_await` first and only run the tool on files that match. And on whether the per-variable liveness bools could be avoided by opening a try block after each initialization — he is unconvinced, since you would need a jump cascade for every variable, and prefers the cheaper outs: opt out entirely via `noexcept`, and skip tracking for trivially destructible types, where the bool costs more than the destructor it is guarding.

Did the migration succeed? Yes. The parts of QLever the customer cares about now build with the subset of C++17 that GCC 8 supports. And there is a chance it was all temporary — the customer is discussing a toolchain update, which would let Kalmbach undo half a year of work, sunk cost fallacy fully acknowledged.

---

The talk is a deep-dive into machinery most C++ programmers are content never to see, and it earns the trip. Lowering coroutines by hand makes visible exactly what the compiler is doing for you: the frame layout, the switch-and-goto state machine, the placement-new lifetime bookkeeping, the manual unwinding, the value-category preservation that a naive `get()` would silently destroy. It also stakes out the boundary — by-value parameters cannot be reproduced by source-to-source rewriting, full stop — and then shows the upside of being off-standard, with a generator that optimizes down to hand-written ranges once you drop the type erasure the standard forces on you.

And it ends on the line the whole exercise deserves:

> I really got to appreciate C++20 while I was getting rid of it.
