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

Johannes Kalmbach develops the QLever RDF and SPARQL graph database, written in C++20. A customer paid to have part of it downgraded to C++17 — coroutines included. Doing that by hand means writing out, explicitly, everything the compiler normally synthesizes behind `co_yield` and `co_await`.

Which makes the talk the clearest available answer to a question most C++ programmers never get a straight answer to: **what code does the compiler actually generate for a coroutine?**

This post is the lowering, in code. The listings below are reconstructed from the talk's slides; Kalmbach himself called them slideware, simplified in places "to not have the syntax that C++ has, but the syntax we would sometimes wish that C++ had."

## What gets replaced

Four moving parts, treated very differently by the rewrite:

| Part | Fate |
|---|---|
| The coroutine body | Rewritten by hand into a state machine, **per coroutine** |
| The compiler-synthesized frame | Rewritten by hand, **per coroutine** |
| The promise type | **Unchanged** — the new infrastructure consumes it as-is |
| `std::coroutine_handle` | Generic replacement, **written once** |

The promise type surviving untouched is what makes the whole thing tractable. `initial_suspend`, `final_suspend`, `yield_value`, `return_void`, `unhandled_exception` all keep working exactly as written.

## Example A: an iota generator, lowered

The input:

```cpp
Generator<int> iota(int start, int end) {
    while (start < end) {
        co_yield start++;
    }
}
```

The output — a frame class carrying the parameters, storage for the awaiter, and a `resume` function that is one big switch-and-goto state machine:

```cpp
Generator<int> iota(int start, int end) {
    struct Frame : CoroFrameBase<Frame, Generator<int>::promise_type> {
        // 1. Function parameters live in the frame, not on a stack.
        int start;
        int end;

        // 2. Storage for the awaiter that co_yield produces.
        CoroStorage<std::suspend_always, true> awaiter_1;

        CoroHandle<> resumeImpl() {
            // 3. Dispatch to wherever we suspended last time.
            switch (suspendIndex) {
                case 0: break;                      // implicit start
                case 1: goto suspend_label_1;
            }

            while (start < end) {
                CO_YIELD(1, awaiter_1, start++);
            }

            // 4. Falling off the end of a coroutine is not falling off
            //    the end of a function: there is an implicit co_return.
            CO_RETURN_VOID();
        }
    };
    return Frame::ramp(start, end);
}
```

Three things to notice.

**Suspension index 0 always exists.** Every coroutine has an implicit suspension point before its first statement, because `initial_suspend` may suspend there. Real suspension points are numbered from 1.

**`goto` is available because nobody uses it.** No one writes `goto` inside a coroutine body, so the mechanism is free for the rewriter to commandeer.

**`resumeImpl` returns a handle, not `void`.** That is for symmetric transfer, below.

## The core: what `co_await` expands to

This is the listing everything else hangs off. `await_suspend` has three legal return types, and each means something different:

```cpp
#define CO_AWAIT_MAY_RETURN(awaiter)                                       \
    if (!CO_GET(awaiter).await_ready()) {                                  \
        auto handle = CoroHandle<PromiseType>::from_promise(promise);      \
        using Ret = decltype(CO_GET(awaiter).await_suspend(handle));       \
                                                                           \
        if constexpr (std::is_void_v<Ret>) {                               \
            /* void: suspend unconditionally, return to the caller */      \
            CO_GET(awaiter).await_suspend(handle);                         \
            return CoroHandle<>{};                                         \
                                                                           \
        } else if constexpr (std::is_same_v<Ret, bool>) {                  \
            /* bool: suspend only if it says so */                         \
            if (CO_GET(awaiter).await_suspend(handle)) {                   \
                return CoroHandle<>{};                                     \
            }                                                              \
            /* false: fall through, no suspension happened */              \
                                                                           \
        } else {                                                           \
            /* handle: symmetric transfer -- suspend, but resume THAT      \
               coroutine instead of returning to the caller */             \
            return CO_GET(awaiter).await_suspend(handle);                  \
        }                                                                  \
    }                                                                      \
    /* await_ready() was true: no suspension, fall straight through */
```

An empty returned handle means *return control to the caller*. A non-empty one means *resume this next*. That convention is what lets symmetric transfer work without the mandatory tail-call optimization real compilers rely on:

> If you're not the compiler, it's a little bit harder to enforce tail call optimization in all cases.

## `co_yield` and `co_return`

`co_yield x` is not one operation — it is a promise call, a placement-new, an await, a resume-side call, and a destruction:

```cpp
#define CO_YIELD(index, awaiter, ...)                                      \
    suspendIndex = (index);                                                \
    /* the promise decides what yielding means */                          \
    CO_INIT(awaiter, (promise.yield_value(__VA_ARGS__)));                  \
    CO_AWAIT_MAY_RETURN(awaiter);   /* may return out of resumeImpl */     \
                                                                           \
    suspend_label_##index:;         /* resumption lands here */            \
                                                                           \
    CO_GET(awaiter).await_resume();                                        \
    awaiter.destroy()               /* explicit: it survived a suspension */
```

`co_return` calls into the promise, destroys every local still alive at that point — hence the variadic tail — marks the coroutine done, and awaits the final suspend:

```cpp
#define CO_RETURN_VOID(...)                                                \
    promise.return_void();                                                 \
    CO_DESTROY_ALL(__VA_ARGS__);    /* locals still in scope */            \
    vtable.resume = nullptr;        /* the done() convention */            \
    return finalSuspendAndMaybeDestroy()
```

```cpp
CoroHandle<> finalSuspendAndMaybeDestroy() {
    CO_INIT(finalAwaiter, (promise.final_suspend()));
    CO_AWAIT_MAY_RETURN(finalAwaiter);

    // If final_suspend did NOT suspend, the frame is torn down right here
    // and the handle is dangling from this point on.
    CO_GET(finalAwaiter).await_resume();
    finalAwaiter.destroy();
    deleteFrame();
    return CoroHandle<>{};
}
```

## The coroutine handle

Type erasure via two function pointers — the same shape GCC and Clang use:

```cpp
struct CoroVTable {
    CoroHandle<> (*resume)(void*);   // not void: symmetric transfer
    void         (*destroy)(void*);
};

template <typename Promise = void>
class CoroHandle {
    CoroVTable* vtable_ = nullptr;   // one pointer: lightest possible handle

public:
    CoroHandle() = default;
    explicit CoroHandle(CoroVTable* v) : vtable_(v) {}

    explicit operator bool() const { return vtable_ != nullptr; }

    // Convention: a null resume pointer means "finished, do not resume".
    bool done() const { return vtable_->resume == nullptr; }

    void destroy() const { vtable_->destroy(vtable_); }

    void resume() const {
        // Trampoline: keep resuming whatever we are handed until
        // somebody returns an empty handle (= back to the caller).
        CoroHandle<> next = vtable_->resume(vtable_);
        while (next) {
            next = next.vtable_->resume(next.vtable_);
        }
    }
```

Getting from a handle to the promise object, and back, is pointer arithmetic — legal only because the frame lays the two out adjacently:

```cpp
    static constexpr std::size_t promiseOffset() {
        constexpr std::size_t a = alignof(Promise);
        return (sizeof(CoroVTable) + a - 1) / a * a;
    }

    Promise& promise() const {
        auto* p = reinterpret_cast<std::byte*>(vtable_) + promiseOffset();
        return *std::launder(reinterpret_cast<Promise*>(p));
    }

    static CoroHandle from_promise(Promise& pr) {
        auto* p = reinterpret_cast<std::byte*>(std::addressof(pr)) - promiseOffset();
        return CoroHandle{reinterpret_cast<CoroVTable*>(p)};
    }
};
```

Kalmbach is candid about the standing of this:

> I'm sure there's something that is, according to the standard, not guaranteed for types that are not simple enough. But in practice it works. You can `static_assert` that this is correct.

## The frame base class

CRTP over the concrete frame. The first two members must stay adjacent and first, or the offset arithmetic above breaks:

```cpp
template <typename Derived, typename Promise>
struct CoroFrameBase {
    using PromiseType = Promise;

    // ---- layout-critical: CoroHandle navigates between these two ----
    CoroVTable vtable{&resumeThunk, &destroyThunk};
    Promise    promise{};
    // -----------------------------------------------------------------

    int suspendIndex = 0;

    // Every coroutine has an initial and a final suspend point.
    CoroStorage<decltype(std::declval<Promise&>().initial_suspend()), true> initialAwaiter;
    CoroStorage<decltype(std::declval<Promise&>().final_suspend()),   true> finalAwaiter;

    void deleteFrame() {
        auto* self = static_cast<Derived*>(this);
        self->~Derived();
        promiseDeallocate<Promise>(self);
    }
```

### `ramp` — everything that happens when a coroutine is called

```cpp
    template <typename... Args>
    static auto ramp(Args&... args) {
        // 1. Allocate. Customizable: the promise may supply an allocator,
        //    and it gets to see the coroutine's arguments (your first
        //    parameter might BE a memory resource). Passed by reference --
        //    they must not be moved from, they are stored in the frame next.
        void* mem = promiseAllocate<Promise>(sizeof(Derived), args...);

        // 2. Construct the frame in that buffer.
        auto* frame = ::new (mem) Derived{args...};

        // 3. Ask the promise for the thing the caller receives.
        auto returnObject = frame->promise.get_return_object();

        // 4. Await the initial suspend point.
        CO_INIT(frame->initialAwaiter, (frame->promise.initial_suspend()));
        if (frame->initialSuspendSuspended()) {
            return returnObject;    // lazy coroutine: body has not run
        }

        // 5. Eager coroutine: run the body until it suspends on its own,
        //    THEN hand the return object back.
        CoroHandle<>{&frame->vtable}.resume();
        return returnObject;
    }
```

### `resume` — the generic half

The base can only handle suspension index 0. Everything else it delegates to the derived frame, because only the derived frame knows what the body looks like:

```cpp
    static CoroHandle<> resumeThunk(void* p) {
        auto* self = static_cast<Derived*>(reinterpret_cast<CoroFrameBase*>(p));
        try {
            if (self->suspendIndex == 0) {
                CO_GET(self->initialAwaiter).await_resume();
                self->initialAwaiter.destroy();
            }
            return self->resumeImpl();          // into the state machine

        } catch (...) {
            // No real stack unwinding is available to us, so unwind by hand.
            self->destroyLocalsOnUnhandledException();

            // MUST be called from inside the handler: the promise may want
            // std::current_exception().
            self->promise.unhandled_exception();

            self->vtable.resume = nullptr;      // the coroutine is done
            return self->finalSuspendAndMaybeDestroy();
        }
    }
```

### `destroy`

Which objects are alive depends on where the coroutine is suspended:

```cpp
    static void destroyThunk(void* p) {
        auto* self = static_cast<Derived*>(reinterpret_cast<CoroFrameBase*>(p));

        if (CoroHandle<>{&self->vtable}.done()) {
            // suspended at final_suspend: only the final awaiter remains
            self->finalAwaiter.destroy();
        } else if (self->suspendIndex == 0) {
            // suspended at initial_suspend: only the initial awaiter
            self->initialAwaiter.destroy();
        } else {
            // suspended in the middle: only the derived frame knows
            self->destroyLocals();
        }
        self->deleteFrame();
    }
};
```

## Local variables: `CoroStorage`

Locals that survive a suspension need manual lifetime management. The storage type takes **two** template parameters, and the second one is the interesting one:

```cpp
template <typename Ref, bool IsOwning>
class CoroStorage {
    using Value  = std::remove_reference_t<Ref>;
    // Owning: hold the object. Non-owning: hold a pointer to one.
    using Stored = std::conditional_t<IsOwning, Value, Value*>;

    alignas(Stored) std::byte buffer_[sizeof(Stored)];

    Stored* ptr() {
        // std::launder is genuinely required here: the address holds a
        // Stored, but `buffer_` names an array of bytes.
        return std::launder(reinterpret_cast<Stored*>(buffer_));
    }

public:
    void* raw() { return static_cast<void*>(buffer_); }

    // Returns a PROXY by value, not the reference directly -- see below.
    struct Proxy { Ref ref; };

    Proxy get() {
        if constexpr (IsOwning) {
            return Proxy{static_cast<Ref>(*ptr())};
        } else {
            return Proxy{static_cast<Ref>(**ptr())};
        }
    }

    void destroy() { ptr()->~Stored(); }
};
```

**Why two parameters?** Because reference-ness and ownership are independent. A `const&` or `&&` local bound to a temporary *is* a reference, but it also has to keep that temporary alive — lifetime extension, which you now implement yourself:

```cpp
const std::string& x = getString();   // owning: must extend the temporary
CoroStorage<const std::string&, true>  x_storage;

std::string&& y = getStringRef();     // non-owning: nothing to extend
CoroStorage<std::string&&, false>      y_storage;
```

**Why does `get()` return a proxy by value?** To preserve value category. If `CO_GET(x)` were a function call returning `std::string&&`, then `doSomething(CO_GET(x))` would move — where the original code, passing a named rvalue-reference variable, would copy unless you wrote `std::move`. Reading `.ref` off a proxy restores the original behavior.

**Why macros instead of an `emplace` member function?** Two reasons:

```cpp
#define CO_INIT(storage, ...)                                              \
    do {                                                                   \
        if constexpr (storage.isOwning) {                                  \
            /* No parens or braces here -- the CALLER supplies them. */    \
            ::new (storage.raw()) storage_value_t<decltype(storage)>       \
                __VA_ARGS__;                                               \
        } else {                                                           \
            ::new (storage.raw()) storage_value_t<decltype(storage)>*      \
                (::std::addressof __VA_ARGS__);                            \
        }                                                                  \
    } while (false)

#define CO_GET(storage) (storage.get().ref)
```

First, **copy elision**: placement-new directly from a function call gets guaranteed elision; a forwarding `emplace` cannot reproduce that. Second, **initialization syntax** — the macro takes raw tokens so the caller chooses the punctuation, because these are not the same object:

```cpp
std::string x(97, 'b');   // 97 copies of 'b'
std::string y{97, 'b'};   // "ab"
```

## Example B: a coroutine with locals

```cpp
Generator<std::string> prefixed(Range strings, std::string prefix) {
    for (auto it = strings.begin(); it != strings.end(); ++it) {
        co_yield prefix + *it;
    }
}
```

Lowered — note that the **temporary** `prefix + *it` needs a slot too:

```cpp
Generator<std::string> prefixed(Range strings, std::string prefix) {
    struct Frame : CoroFrameBase<Frame, Generator<std::string>::promise_type> {
        Range       strings;
        std::string prefix;

        CoroStorage<Range::iterator, true>  it_storage;
        CoroStorage<Range::iterator, true>  end_storage;
        CoroStorage<std::string, true>      tmp_storage;   // the temporary!
        CoroStorage<std::suspend_always, true> awaiter_1;

        CoroHandle<> resumeImpl() {
            switch (suspendIndex) {
                case 0: break;
                case 1: goto suspend_label_1;
            }

            CO_INIT(it_storage,  (strings.begin()));
            CO_INIT(end_storage, (strings.end()));

            while (CO_GET(it_storage) != CO_GET(end_storage)) {
                CO_INIT(tmp_storage, (prefix + *CO_GET(it_storage)));

                CO_YIELD(1, awaiter_1, CO_GET(tmp_storage));

                // The temporary's scope ends at the bottom of the loop body.
                tmp_storage.destroy();
                ++CO_GET(it_storage);
            }

            CO_RETURN_VOID(it_storage, end_storage);   // still-live locals
        }

        void destroyLocals() {
            // Suspended at index 1: the awaiter and the temporary are alive.
            awaiter_1.destroy();
            tmp_storage.destroy();
            it_storage.destroy();
            end_storage.destroy();
        }
    };
    return Frame::ramp(strings, prefix);
}
```

That temporary is the historically dangerous case:

> This expression `prefix + *it` creates a temporary string which is then yielded, and this temporary string we also have to keep alive until the suspension returns control to us. This was also where in initial implementations all the bugs were — also in the compilers.

## Example C: exceptions

```cpp
Generator<int> parse(Range strings) {
    try {
        for (auto it = strings.begin(); it != strings.end(); ++it) {
            co_yield std::stoi(*it);     // may throw
        }
    } catch (const std::exception& e) {
        log(e.what());
    }
}
```

Two problems. **You cannot `goto` into a `try` block** — "not even with non-portable ASM goto tricks." And there is no stack unwinding to piggyback on.

The first is solved with a two-stage jump: land *before* the try, enter it normally, then a second switch inside dispatches to the real label. The second is solved with a liveness flag per local:

```cpp
struct Frame : CoroFrameBase<Frame, Generator<int>::promise_type> {
    Range strings;

    CoroStorage<Range::iterator, true> it_storage;
    CoroStorage<Range::iterator, true> end_storage;
    CoroStorage<std::suspend_always, true> awaiter_1;

    // Hand-rolled unwinding state.
    bool it_live = false;
    bool end_live = false;
    bool awaiter_1_live = false;

    void destroyLocalsOnUnhandledException() {
        // Reverse construction order. Cannot short-circuit: with nested
        // scopes, a later variable may be live while an earlier one is not.
        if (awaiter_1_live) { awaiter_1.destroy();   awaiter_1_live = false; }
        if (end_live)       { end_storage.destroy(); end_live = false; }
        if (it_live)        { it_storage.destroy();  it_live = false; }
    }

    CoroHandle<> resumeImpl() {
        switch (suspendIndex) {
            case 0: break;
            case 1: goto before_try;      // NOT into the try block
        }

    before_try:
        try {
            try {
                // Second dispatch, now that we are legally inside.
                switch (suspendIndex) {
                    case 0: break;
                    case 1: goto suspend_label_1;
                }

                CO_INIT_X(it_storage,  it_live,  (strings.begin()));
                CO_INIT_X(end_storage, end_live, (strings.end()));

                while (CO_GET(it_storage) != CO_GET(end_storage)) {
                    CO_YIELD_X(1, awaiter_1, awaiter_1_live,
                               std::stoi(*CO_GET(it_storage)));
                    ++CO_GET(it_storage);
                }

                CO_DESTROY_UNCONDITIONALLY(it_storage, it_live);
                CO_DESTROY_UNCONDITIONALLY(end_storage, end_live);

            } catch (...) {
                // Inner try: destroy this scope's locals, then rethrow.
                // Split in two so multiple catch clauses don't duplicate it.
                destroyLocalsOnUnhandledException();
                throw;
            }
        } catch (const std::exception& e) {
            log(e.what());       // the user's catch clause, essentially as-is
        }

        CO_RETURN_VOID();
    }
};
```

`CO_INIT_X` is `CO_INIT` plus setting the flag; `CO_DESTROY_UNCONDITIONALLY` destroys and clears it. The catch clause itself needs almost no rewriting — because C++20 forbids `co_await` and `co_yield` inside a catch block, which is the one place the rewriter gets a free pass.

## What cannot be rewritten

- **Lambdas as locals** — the closure type cannot be named, so no buffer can be declared. Rewrite as an explicit closure struct first.
- **Range-based `for`** — has hidden locals. Rewrite to an explicit iterator loop first.
- **Complex expressions in `co_yield`** — multiple temporaries whose destruction order is unspecified and varies by compiler. Hoist to a named variable on the previous line.
- **By-value function parameters** — fundamentally impossible.

The last one is structural. A by-value parameter's temporary must live to the end of the enclosing *full expression*, not until the function returns, and it is materialized by the caller — invisible to source-to-source rewriting:

> If you have a function that takes a string by value, and a function that does the same thing but takes a string by rvalue reference, they boil down to the exact same assembly — because this difference is done by the call side and not by the function.

So a function taking `std::string` by value and returning a `string_view` into it is legal, works as long as the caller uses it before the semicolon — and cannot be reproduced. In a coroutine that semicolon can arrive after a suspension and a great deal of unrelated work.

## Going off-standard

Once you do the lowering yourself, nothing forces you to reproduce C++20 semantics. Stock coroutines pay for an allocation and for type erasure that blocks inlining — and HALO, in Kalmbach's experience, is unreliable and almost never fires. But at rewrite time the frame type is known, so put the frame *in* the handle:

```cpp
// Instead of: CoroHandle<Promise> holding a type-erased vtable pointer
template <typename Frame>
class ConcreteCoroHandle {
    Frame frame_;      // the whole frame, by value. No allocation.
};

// Instead of: Generator<int>
Generator<int, ConcreteFrame> g = iota(0, 10);
```

Exactly how ranges already work — every `transform_view` has a different type because it is templated on its function. Crucially this changes the infrastructure only; the per-coroutine body rewriting is unchanged.

The result: an `iota` generator compiling to **the same assembly as hand-written `std::ranges` code**. On Clang. GCC still refuses, and he does not yet know why.

## Automating it

The rules are mechanical — see a local, check the type, check whether it is a temporary materialization, add a frame member, replace the initialization with `CO_INIT` and every access with `CO_GET`. So he wrote a libclang tool that does it.

> If you think of it, it's some kind of very elaborate reflection. You see what is there and you make something other from it, but according to rules.

Templates forced one design decision: you cannot rewrite at definition time, because with dependent types you cannot answer *is this a temporary?* So the tool rewrites **concrete template instantiations**, explicit or implicit. It also only handles `co_yield` of a single variable, following from the evaluation-order problem above.

The maintenance workflow is the part that makes this an engineering practice rather than a stunt. **The C++20 source stays the single source of truth.** Nobody edits the generated C++17. CI runs the rewriter and checks the output compiles. A bug is either in the C++20 code or in the rewriter — the generated code is only ever a symptom.

---

Writing this out by hand makes visible everything the compiler does silently: the frame layout with its layout-critical first two members, the switch-and-goto dispatch, the placement-new lifetime bookkeeping for locals *and* temporaries, the by-hand unwinding, the value-category preservation a naive `get()` would destroy, and the three-way branch on `await_suspend`'s return type that makes symmetric transfer work.

It also ends on the right line:

> I really got to appreciate C++20 while I was getting rid of it.
