---
layout: single
title: "C++ - I Fixed Move Semantics (Jason Turner, C++ Online)"
date: 2026-07-26 10:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - move-semantics
permalink: "2026/07/26/cpp-i-fixed-move-semantics-jason-turner"
---

[Jason Turner - I Fixed Move Semantics - C++ Online](https://www.youtube.com/watch?v=TJhMGS9sRlw)

The title is deliberate clickbait — Jason Turner says so himself in the first minute. He has not submitted anything to the committee, he doesn't expect you to use his solution, and the "fix" is really a thought experiment. But like all of his talks, the goal isn't to sell a library. It's to make you think differently the next time you write C++. And the vehicle for that is one of the most reliably confusing corners of the language: rvalue references, `std::move`, and forwarding references.

Turner is a C++ trainer, and over the years he's watched the same confusion play out in room after room. This talk is his attempt to name *what* is actually broken about move semantics — not to complain, but to show that a **stronger type** can make the whole mess safe and self-documenting. That last idea is the real payload of the talk.

> **A note on the setup.** This was delivered live at C++ Online with the audience answering in Discord, so the talk is structured as a long series of "which function gets called here?" quizzes. I've kept that spirit — most sections below are a small puzzle followed by the answer, because that's exactly where the confusion lives.

## What is `&&`?

Turner opens with six characters on a slide and a question: what is this?

```cpp
a && b
```

You genuinely cannot know. `&&` has (at least) three meanings in C++:

- **logical AND** — `a && b`
- **rvalue reference** — `int&& r = ...`
- **forwarding reference** — `template <class T> void f(T&& x)`

And the single `&` has three of its own: lvalue reference, bitwise-and, and the address-of operator. This ambiguity isn't a footnote — it's the seed of the whole problem. The same token means radically different things depending on context, and humans are bad at tracking context.

> A bit of history: Scott Meyers named the two-ampersand deduced form a **"universal reference"** in *Effective Modern C++*. After he retired, the community effectively overruled him and settled on **"forwarding reference"**, which is now the standard term.

## References are not objects

A quick but load-bearing aside:

- A **reference is not an object**. It literally refers to another object, and creating an invalid reference is itself undefined behavior.
- A **pointer is an object** that may or may not point at something. You don't hit UB until you dereference an invalid one.
- An **object** is anything that is not `void`, not a function, and not a reference.

The consequence that matters later: **you cannot rebind a reference.**

```cpp
int x = 1;
int& y = x;   // y refers to x, forever
int z = 5;
y = z;        // this assigns 5 into x — it does NOT make y refer to z
++z;          // only z changes now
std::print("{}", x);   // prints 10 in Turner's version — x, not a rebinding
```

Once a reference has a name, it's stuck to its referent. Hold onto that.

## `std::move` is just a cast

Here's the first quiz. Does this compile?

```cpp
int x = 42;
int&& y = x;   // ?
```

**No.** An rvalue reference can only bind to an rvalue, and `x` is an lvalue. This is the entire reason `std::move` exists:

```cpp
int&& y = std::move(x);              // OK
int&& y = static_cast<int&&>(x);     // exactly equivalent
```

`std::move` **is not a move.** It is an explicit cast to an rvalue reference type. That's all. It doesn't move anything, touch anything, or generate any code — it changes the *type* of the expression so that overload resolution picks a different function.

So why do we have it at all? **The entire point of `std::move` is overload resolution** — selecting which version of a function to call, by casting the argument to an rvalue reference.

```cpp
void f(const T&);   // (1)
void f(T&&);        // (2)

T x;
f(x);                          // A -> (1) const lvalue ref
f(std::move(x));               // B -> (2) rvalue ref
f(static_cast<T&>(x));         // C -> (1) pointless lvalue cast
```

## `const` quietly defeats `move`

Now make the object `const` and run the same game:

```cpp
const auto x = 42;
f(x);              // const lvalue ref
f(std::move(x));   // STILL const lvalue ref!
```

`std::move` on a `const` object gives you a `const T&&` — a const rvalue reference. There is no move constructor that takes `const T&&`, so it happily decays to `const T&` and you get a **copy**, silently. You asked to move and the language handed you a copy without a word of complaint. Const rvalue references are almost never something you write on purpose, yet here's the language producing one behind your back.

## The core brokenness: a named rvalue reference is an lvalue

This is the crux of the whole talk. Consider:

```cpp
void g(std::string&& s) {   // s is an rvalue reference...
    std::string other = s;  // ...but this is a COPY
}
```

`s` has a name. **Anything with a name is an lvalue.** So even though `s` is *of type* rvalue-reference-to-string, the expression `s` is an lvalue and binds to the *copy* constructor, not the move constructor. To actually move it you have to cast it back to an rvalue — again:

```cpp
void g(std::string&& s) {
    std::string other = std::move(s);   // now it moves
}
```

Turner's verdict, after teaching this a hundred-plus times: this is *the* single most common mistake he sees with rvalues and moves. Most developers don't realize (a) that `move` is only about overload resolution, and (b) that a named rvalue reference must be `move`d *again* to actually move. The terminology fights you at every step. There is a **250-page book** (Nicolai Josuttis's *C++ Move Semantics*) written about this one feature. That, Turner argues, is the smell of something broken.

## The destructor trap

One more landmine before the fix. Which constructor runs for `a` and `b`?

```cpp
struct Widget {
    ~Widget() = default;   // just mentioning the destructor...
};

Widget src;
Widget a = src;              // copy
Widget b = std::move(src);   // copy!  (not a move)
```

Declaring the destructor — even `= default` — **suppresses the implicit generation of the move operations** (this is "the table" of special-member-function rules). So `Widget` has no move constructor at all. You call `std::move`, and it dutifully casts to an rvalue reference... which then binds to the copy constructor, because that's the only thing available. Again: move that silently isn't a move.

## Why we even want moves

To be fair to the feature, Turner grounds it. The reason move operations matter:

```cpp
struct Buffer {
    Data* data;
    // copy must deep-copy the pointed-to data (expensive)
    // move can just steal the pointer and null out the source (cheap)
};
```

Move construction lets you transfer ownership of an expensive resource instead of duplicating it. That's the whole value proposition — and it's genuinely useful. Which makes the ergonomics all the more frustrating. And whether it's worth it is type-dependent: an `std::array<int, N>` by rvalue reference buys you nothing (the ints live in the array's own storage), but an `std::array<std::string, N>` has N pointers worth stealing.

## The fundamental problem: implicit conversions

So what's the root cause? Turner has a running theme across all his talks, and it holds here too:

> It's always implicit conversions.

The problem is that an **rvalue reference implicitly converts to a const lvalue reference** (and a const rvalue reference does too). That implicit decay is what turns your intended move into a silent copy in every example above. The language never tells you no — it just quietly does the weaker thing.

His fix, in one phrase: **stronger types.**

## `moving_reference<T>` — a reference that refuses to lie

Imagine a magical type. Call it `moving_reference<T>`. It should:

- **refuse to compile** if you try to bind it to an lvalue
- **compile** when bound to an rvalue
- **automatically move-construct** on assignment/initialization — no second `std::move`
- **refuse to compile** if you try to move a `const` object
- **refuse to compile** for a type that has no move constructor

That's the wishlist — and it maps exactly onto every failure mode from the earlier sections. The astonishing part is how little code it takes:

```cpp
template <class T>
class moving_reference {
    T* ptr_;   // store a pointer, not a reference — generally the better choice
public:
    constexpr explicit moving_reference(T&& obj) noexcept
        : ptr_(&obj) {}

    // the whole trick: implicit conversion back to an rvalue reference
    constexpr operator T&&() const noexcept {
        return static_cast<T&&>(*ptr_);   // note: static_cast, not std::move
    }

    // delete the lvalue overload so lvalues are rejected with a clear message
    moving_reference(T&) = delete;
};
```

Two pieces do all the work: **a constructor that takes `T&&`**, and **an implicit conversion operator back to `T&&`**. Because the constructor only accepts a non-const rvalue reference, lvalues and const objects are rejected at the call site. Because the conversion yields an rvalue, assigning *from* a `moving_reference` binds to the move constructor automatically — no repeated `std::move`, no silent copy.

A few notes from the talk:

- The conversion uses `static_cast`, deliberately **not** `std::move` — there's no reason to make the type depend on `<utility>`.
- The `= delete` overloads aren't strictly necessary; they exist to give the user a **better error message**. C++26's *delete with a reason* (`= delete("...")`) makes that message even nicer.
- This works all the way back to **C++11** — no concepts required. C++17/20/26 just layer on extra safety checks and better diagnostics.

### The `is_move_constructible` gotcha

There's one subtlety in enforcing "refuse types that can't move." You'd reach for `std::is_move_constructible`, but that trait **lies**: it asks "is this constructible from an rvalue reference?" — and a type that only has a copy constructor answers *yes*, because `const T&` happily binds an rvalue. Turner has watched arguments break out at CppCon over this.

So the talk borrows a Stack Overflow technique — a probe type with implicit conversions to **both** candidate parameter types, so that a type having both operations makes the call ambiguous:

```cpp
// Implicitly converts to both. If T has BOTH a copy and a move constructor,
// the call below is ambiguous -> substitution fails, which is the signal.
template <typename T>
struct detect_move_construction {
    operator const T&();   // would match the copy constructor
    operator T&&();        // would match the move constructor
};

template <typename T>
concept exclusively_copyable_or_movable =
    requires { T(detect_move_construction<T>{}); };

template <typename T>
concept has_move_constructor =
    std::is_move_constructible_v<T> && !exclusively_copyable_or_movable<T>;
```

Turner's own caveats: an MSVC bug means his real version probes the *assignment* operator rather than construction, and he admits on stage there is no time to unpack it — "we don't have time to unpack all this, but it does work." Treat the above as the shape, not a drop-in.

## Now do it again for forwarding references

The second half applies the same idea to **forwarding references**. First, the refresher. A forwarding reference is a *template-deduced* reference that can become any of four types — non-const lvalue ref, const lvalue ref, non-const rvalue ref, const rvalue ref — depending on the argument:

```cpp
template <class T> void f(T&& x);   // forwarding reference
void g(auto&& x);                    // ALSO a forwarding reference
```

`auto&&` is *exactly* the same as the template form — the standard explicitly says `auto` deduction follows template type deduction. But `&&` only means "forwarding reference" when the type is **actually being deduced right here**:

```cpp
template <class T>
void h(std::vector<T>&& x);   // NOT a forwarding reference — T is deduced,
                              // but the parameter type is a plain rvalue ref
```

A fun debugging trick Turner shows: declare a function template, *don't implement it*, call it with various value categories, and read the linker/compiler errors in Compiler Explorer — they'll spell out exactly which reference type got deduced on each line.

The pain point is `std::forward`. It's a **conditional cast**: forward an lvalue-ref as an lvalue (→ copy), forward an rvalue-ref as an rvalue (→ move). The catch is that this logic **must be threaded by hand through every level of the call chain**. Forget one `std::forward` and you silently get a copy. It's boilerplate, and it's error-prone.

## `forwarding_reference<T>` — forwarding that propagates itself

Same move as before: imagine a stronger type.

```cpp
void f1(auto&& x);
void f2(forwarding_reference<...> x) { f1(x); }   // no std::forward needed
void take(forwarding_reference<...> x)  { f2(x); } // it just propagates
```

The implementation is the same two pieces as before, plus deduction guides:

```cpp
template <typename T>
class forwarding_reference {
    T* ptr_;
public:
    constexpr explicit forwarding_reference(T&& obj) noexcept : ptr_(&obj) {}

    [[nodiscard]] constexpr operator T&&() const noexcept {
        return static_cast<T&&>(*ptr_);
    }
};

// The guides pick the specialization from the argument's value category --
// this is what makes the wrapper remember what it was constructed from.
template <typename T> forwarding_reference(T&)  -> forwarding_reference<T&>;
template <typename T> forwarding_reference(T&&) -> forwarding_reference<T>;
```

Once a value is wrapped in a `forwarding_reference`, it **carries its own value category through the call chain**. You pass it from `take` to `f2` to `f1` and the correct copy-or-move happens at the end — *without* writing `std::forward` at every hop. The auto-forwarding "fell out of the design," as Turner puts it. It does need a **deduction guide** to pick the right specialization from an lvalue vs. rvalue argument, which is why this half requires **C++17** (whereas `moving_reference` backports to C++11).

### A bonus fix: the greedy constructor

This type also cures a classic footgun. A constructor taking a forwarding reference is a "universal constructor" that greedily hijacks copies, moves, and conversions from *anything*:

```cpp
struct BadTimes {
    template <class T> BadTimes(T&&);   // eats copy, move, and everything else
};
```

By taking a `forwarding_reference<T>` parameter instead, you can **sink a value by forwarding reference without getting in the way of the real copy and move constructors**. Turner tripped over the details live (the copy constructor is stubbornly still there in some formulations), which honestly reinforces the point: the built-in machinery is hard to get right, and the wrapper type does the right thing for you.

## Safety, as a stronger type

Because these are real class types, you can decorate them with *every* safety tool the language offers:

- **`explicit`** and **`[[nodiscard]]`** everywhere — you can't accidentally create one and drop it, or pull the value out and ignore it.
- **Clang's `[[clang::lifetimebound]]`** — applied conditionally when the compiler supports it. This lets the wrapper catch a returned dangling reference with a real warning ("address of stack memory ... is returned"), giving you a reference type that is in some cases *safer than a built-in reference*. (As of C++26, returning a plain reference to a local is an error anyway.)

The takeaway: a user-defined reference type is a place you can hang guarantees that the built-in `&&` simply has nowhere to put.

## Open questions and honest limits

Turner is candid about what he couldn't solve. The best one, from the audience: **can we stop a reference from being used twice?**

- **Pointer tagging** (stashing a "used" bit in the low bits of the pointer) fails — machines are byte-addressable, so you can legitimately have a reference to a member of a byte array with no spare bits.
- **Null-the-pointer-on-move** and assert makes the **`constexpr` case worse** — he realized this *while driving* — because it would let a `constexpr` moving reference hold a null pointer and defer UB to runtime, whereas the current design just fails to compile.
- **Reference counting** the number of takes would work for debugging but doubles the size of a reference and adds overhead.
- A **debug-build-only layout change** to count takes was possible but he disliked it too.

No clean answer — but, he notes, this type is "worthy of every keyword and attribute you have." Throw everything at it.

## Takeaways

1. **Avoid `move` when you can.** If you are about to `std::move` an object straight into a function call, pass the object directly instead — do not create the intermediate you are going to immediately move from.

2. **The real lesson is not about move semantics.** `&&` is overloaded three ways, implicit conversions decay it to `const T&`, and named rvalue references betray you. A purpose-built type that refuses to convert implicitly makes all of that safe and readable. Next time you identify a problem, reach for a **stronger type** — that pattern generalizes far beyond move semantics.
