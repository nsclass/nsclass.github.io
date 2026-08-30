---
layout: single
title: "C++ - std::launder: When Is It Actually Required?"
date: 2026-08-30 14:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - memory
permalink: "2026/08/30/cpp-std-launder-when-is-it-required"
---

`std::launder` has a reputation for being the most-cited, least-understood function in the standard library. It compiles to nothing. It changes no bits. It exists purely to tell the optimizer *"the object at this address is not the one you think it is — go look again."*

The name is the joke: you hand it a pointer of dubious provenance and it hands you back a clean one.

```cpp
#include <new>

template<class T>
[[nodiscard]] constexpr T* launder(T* p) noexcept;   // <new>, since C++17
```

Its mandates are short — `T` may not be a function type or `void` — and the runtime cost is exactly zero instructions. (`[[nodiscard]]` arrived in C++20; the C++17 declaration is otherwise identical.) Everything interesting is in the preconditions.

## The one rule that generates every case

Almost every `launder` question reduces to a single concept in `[basic.life]`: **transparent replacement**. When you end an object's lifetime and build a new one in the same storage, the standard asks whether the old pointers, references, and *names* automatically follow along to the new object. If they do, the object was transparently replaced and there is nothing to launder. If they do not, every one of those old pointers is stale, and `std::launder` is the only supported way to get a usable one.

In C++20 and C++23 the conditions are (the working draft rewords them again — more on that in Case 5):

> An object `o1` is transparently replaceable by an object `o2` if:
>
> - the storage that `o2` occupies exactly overlays the storage that `o1` occupied, and
> - `o1` and `o2` are of the same type (ignoring the top-level cv-qualifiers), and
> - `o1` is not a const, complete object, and
> - neither `o1` nor `o2` is a potentially-overlapping subobject, and
> - either `o1` and `o2` are both complete objects, or `o1` and `o2` are direct subobjects of objects `p1` and `p2`, respectively, and `p1` is transparently replaceable by `p2`.

Read that as a checklist: each bullet that can fail is one of the cases below. One case is not about replacement at all — it's the one where you never had a pointer to the object in the first place — and it is the only one most people will ever write on purpose. That's Case 2.

## Case 1 — the complete object is const

This is the standard's own example, and the case that has survived every subsequent relaxation of the rules.

```cpp
#include <new>
#include <cstdio>

struct X { int n; };

int main() {
    const X* p = new const X{3};

    ::new (const_cast<X*>(p)) const X{5};   // storage reuse

    int b = p->n;                  // UB — p still designates the old object
    int c = std::launder(p)->n;    // OK — 5

    std::printf("b=%d c=%d\n", b, c);
}
```

The third bullet fails: `*p` is a const complete object, so it is not transparently replaceable. `p` keeps pointing at the object that died, and `p->n` is undefined behaviour.

Why does the standard care so much about const here? Because const on a *complete* object is the one place where the compiler is allowed to treat a value as immutable for the whole program. `const X x{3};` at namespace scope can go in read-only memory; a load from it can be constant-folded once and reused forever. The rule exists so the optimizer keeps that licence.

Note that the reuse itself is only legal because the object has dynamic storage duration. Ending the lifetime of a const object with static, thread, or automatic storage duration and building something else there is undefined no matter how much laundering you apply.

## Case 2 — a typed pointer out of raw storage

Here is the case that shows up in real code, and the reason `std::launder` was worth standardising. You have a byte buffer and you placement-new into it:

```cpp
alignas(T) std::byte buf_[sizeof(T)];

::new (static_cast<void*>(buf_)) T(args...);
```

Placement new hands back a perfectly good `T*`. If you keep it, you are done — no laundering, ever. But storage-embedding types like `optional`, `variant`, and every small-buffer-optimised function wrapper deliberately *do not* keep it, because a cached pointer costs a whole pointer of space in every object. They recompute it from the buffer instead:

```cpp
T* p = reinterpret_cast<T*>(buf_);
```

And that pointer does not point at the `T`. `reinterpret_cast` between object pointer types is defined as a round trip through `void*`, and `static_cast<T*>` from `void*` only lands on an object of type `T` if one is *pointer-interconvertible* with the object already at that address. `buf_[0]` is a `std::byte`, which is not pointer-interconvertible with a `T`. The cast yields the right address with the wrong provenance, and dereferencing it is undefined.

`std::launder` is the fix, and it is why the function has the shape it does:

```cpp
#include <new>
#include <cstddef>
#include <utility>

template <class T>
class Box {
    alignas(T) std::byte buf_[sizeof(T)];
    bool engaged_ = false;

public:
    template <class... A>
    void emplace(A&&... a) {
        reset();
        ::new (static_cast<void*>(buf_)) T(std::forward<A>(a)...);
        engaged_ = true;
    }

    T& operator*() {
        return *std::launder(reinterpret_cast<T*>(buf_));
    }

    void reset() {
        if (engaged_) {
            std::launder(reinterpret_cast<T*>(buf_))->~T();
            engaged_ = false;
        }
    }

    ~Box() { reset(); }
};
```

Every access recomputes the pointer from `buf_` and launders it. That is the whole trick, and it is what your standard library is doing under the hood.

The alternative, if you would rather not think about any of this, is a union member — `union { T value_; };` — where naming `value_` after a placement new into it is well defined without laundering. That is the more common implementation strategy today precisely because it sidesteps the question.

## Case 3 — the new object has a different type

The second bullet — *same type* — fails whenever you destroy an object and build something else in its storage. The polymorphic version is the one that actually bites, because a stale pointer means a stale vptr, and a stale vptr means the compiler may devirtualise to the wrong override.

```cpp
#include <new>
#include <memory>

struct Base { virtual const char* name() const = 0; virtual ~Base() = default; };
struct D1 final : Base { const char* name() const override { return "D1"; } };
struct D2 final : Base { const char* name() const override { return "D2"; } };

static_assert(sizeof(D1) == sizeof(D2) && alignof(D1) == alignof(D2));

const char* bad(D1* p) {
    std::destroy_at(p);
    ::new (p) D2;
    return p->name();      // UB — p designates a dead D1, and D1 is final, so
}                          // the call is resolved statically to D1::name()

const char* good(D1* p) {
    std::destroy_at(p);
    Base* q = ::new (p) D2;                      // keep what placement new returned
    return q->name();                            // OK
}
```

This one is not theoretical. `D1` is `final`, so `p->name()` is not a virtual call at all — the compiler resolves it statically to `D1::name()` and never loads the vptr:

```
$ clang++ -std=c++20 -O0 case3.cpp -o c3 && ./c3
bad=D1 good=D2
```

Same answer at `-O1`, `-O2` and `-O3`, because devirtualising a call through a `final` type is a language-level entitlement rather than an optimisation — there is no optimisation level at which it goes away. The call went to the override of an object that no longer exists.

Laundering could recover a usable pointer here, since a `Base` subobject really is alive at that address. But this is the case where laundering is the wrong answer to the right question: the pointer you need was already sitting in the return value of the placement new. Use it.

## Case 4 — replacing a base class subobject

The last bullet is the recursive one, and it is what rules out swapping out a base class subobject on its own. `[ptr.launder]` calls this out by name:

> If a new object is created in storage occupied by an existing object of the same type, a pointer to the original object can be used to refer to the new object unless its complete object is a const object **or it is a base class subobject**; in the latter cases, this function can be used to obtain a usable pointer to the new object.

```cpp
struct Base { int n; };
struct Derived : Base { int m; };

void replace_base(Derived& d) {
    Base* b = &d;

    std::destroy_at(b);
    ::new (b) Base{7};      // a *complete* Base now lives in a base subobject's storage

    int x = b->n;                 // UB — subobject replaced by a complete object
    int y = std::launder(b)->n;   // OK — 7
}
```

The old `Base` is a direct subobject of `d`; the new one is a complete object. Neither branch of the last bullet applies, so there is no transparent replacement.

Worth being blunt about this one: laundering `b` fixes the *pointer*, but it does nothing for `d` itself, whose lifetime ended the moment you reused a subobject's storage. This case appears in the standard because the object model has to define it, not because it is a technique. If you find yourself here, restructure.

The same reasoning covers the fourth bullet, potentially-overlapping subobjects — a `[[no_unique_address]]` member or a base that may share bytes with a sibling can never be transparently replaced, because the compiler cannot know which bytes it owns.

## Case 5 — const and reference members, and why the advice you've read is stale

This is the example that dominates search results:

```cpp
struct X { const int n; };

X* p = new X{3};
::new (p) X{5};
int b = p->n;                 // ???
```

In **C++17** this is undefined behaviour and you need `std::launder(p)->n`. N4659's `[basic.life]/8.3` required that the original type

> is not const-qualified, and, if a class type, does not contain any non-static data member whose type is const-qualified or a reference type

**C++20 deleted that clause.** The rewritten "transparently replaceable" definition only disqualifies a const *complete* object, and handles members through the recursive last bullet: `o1.n` and `o2.n` are corresponding direct subobjects whose parents are transparently replaceable, so they are transparently replaceable too. The same goes for reference members. Under C++20 and later, that snippet is fine without laundering.

The working draft goes further still, restating the rule so that the const question is asked only of the complete object or of `mutable` members. The direction of travel is consistent: the set of situations requiring `std::launder` has been shrinking with every revision since it was introduced.

Which is worth knowing, because a great deal of `std::launder` advice on the internet — including sample code that sprinkles it over every const member — was written against C++17 and has quietly expired.

## What launder cannot do

`std::launder` finds an object. It does not create one, and it does not move one.

**It is not a type-punning tool.**

```cpp
int i = 42;
float f = *std::launder(reinterpret_cast<float*>(&i));   // UB — no float lives here
```

The precondition requires an object whose type is *similar to* `T` to be alive at that address. There is no `float` there, laundered or otherwise. Use `std::bit_cast` or `std::memcpy`.

**It does not begin lifetimes.** Reading a struct out of a buffer you filled from a socket is the perennial version of this:

```cpp
std::byte buf[N];
recv(fd, buf, N, 0);
Header* h = std::launder(reinterpret_cast<Header*>(buf));   // still UB
```

No `Header` object has ever begun its lifetime in `buf`. C++20's implicit-lifetime types cover part of this when the bytes come from an allocation function or `memcpy`; C++23's `std::start_lifetime_as` is the tool built for exactly this job. `std::launder` is not.

**It does not extend reachability, and it does not manufacture arrays.** The third precondition — *all bytes of storage that would be reachable through the result are reachable through `p`* — means you cannot launder your way into a bigger object than the one your argument could already see. A byte is reachable through a pointer to `Y` if it lies inside an object pointer-interconvertible with `Y`, or inside the immediately enclosing array object if `Y` is an element.

`launder` returns a pointer to *one* object. It does not create the enclosing array that pointer arithmetic would need:

```cpp
struct Elem { int v; };

alignas(Elem) std::byte buf[3 * sizeof(Elem)];
for (int i = 0; i < 3; ++i)
    ::new (buf + i * sizeof(Elem)) Elem{i};

Elem* e = std::launder(reinterpret_cast<Elem*>(buf));
int a = e->v;      // OK — 0
int b = e[1].v;    // UB — three Elem objects exist, but no Elem[3] array object does
```

A plain `std::byte` array is not one of the operations that implicitly creates objects — that list is `operator new`, `malloc`, `memcpy`, and friends — so there is no array of `Elem` here to walk, and no spelling of `launder` conjures one.

This is also precisely why `alignas(T) std::byte buf_[sizeof(T)]` in Case 2 does work: `buf_[0]` is an element of `buf_`, so the immediately enclosing array makes `sizeof(T)` bytes reachable, which is exactly what the result needs.

**It does not launder `void*` or function pointers** — the mandates reject both — and it does not repair a dangling pointer, a misaligned address, or a use-after-free.

## When you don't need it

A short checklist, because the correct answer is usually "you don't":

- **You kept the pointer placement new returned.** It always points at the new object. This alone covers most in-place construction code.
- **Same type, non-const complete object, no potentially-overlapping subobject.** Transparently replaceable in C++20+, including with const and reference members. Old pointers, references, and names all follow.
- **Replacing an array element in place.** `::new (&arr[1]) Elem{20}` transparently replaces the element; `arr[1]` still names it.
- **You used a union member instead of a byte buffer.** Naming the active member after placement-newing into it is well defined.
- **You're just using `std::optional`, `std::variant`, or `std::vector`.** Your standard library already did the laundering.

## The uncomfortable part

Case 3 breaks loudly and reproducibly. The others do not. Running Cases 1, 4, and 5 on Apple Clang 21 (arm64), at every optimisation level from `-O0` to `-O3`, gives the answer you would naively expect every time:

```
$ clang++ -std=c++20 -O3 case1.cpp -o c1 && ./c1
b=5 c=5
```

The `b=5` is the undefined one, and it is "right". The compiler is entitled to constant-fold that load and doesn't — the const-object aliasing machinery simply isn't reaching for it here.

That split is the whole problem. When the compiler can see a static answer, as with a `final` class, it takes it immediately and your test fails on the first run. When the licence depends on subtler aliasing reasoning, you get latent undefined behaviour of the worst kind: it passes every test you have, on every compiler you use, until the day someone enables LTO, upgrades a toolchain, or inlines your function into a caller that gives the optimizer one more fact to work with — and a load gets hoisted above a placement new in code nobody is looking at.

The reason to write `std::launder` is not that your program is visibly broken. It's that the standard already handed the optimizer permission to break it, and when that permission gets exercised is entirely up to the vendor.

Zero instructions is a cheap price for closing that door.

## References

- [`std::launder` — cppreference](https://en.cppreference.com/w/cpp/utility/launder)
- [`[basic.life]` — object lifetime, current working draft](https://eel.is/c++draft/basic.life)
- [`[ptr.launder]` — pointer optimization barrier](https://eel.is/c++draft/ptr.launder)
- [P0137R1 — Core Issue 1776: Replacement of class objects containing reference members](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2016/p0137r1.html)
- [P0532R0 — On `launder()`, Nicolai Josuttis](https://www.open-std.org/jtc1/sc22/wg21/docs/papers/2017/p0532r0.pdf)
