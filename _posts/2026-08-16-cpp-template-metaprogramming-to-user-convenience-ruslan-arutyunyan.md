---
layout: single
title: "C++ - From Template Metaprogramming to User Convenience: API Design Stories (Ruslan Arutyunyan, C++Now 2026)"
date: 2026-08-16 14:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - templates
  - api-design
permalink: "2026/08/16/cpp-template-metaprogramming-to-user-convenience-ruslan-arutyunyan"
---

[Ruslan Arutyunyan - From Template Metaprogramming to User Convenience: API Design Stories - C++Now 2026](https://www.youtube.com/watch?v=fPo_Tff-L5Y)

This is a **zero-slides talk** — or almost. Ruslan Arutyunyan, a lead developer at Intel and chair of **SG1** (concurrency and parallelism), spends ninety minutes live-coding in front of an advanced C++Now audience, with the room interrupting constantly. What comes out is two real API design stories from **oneTBB**, both about the same underlying tension:

> The users want to write the obvious thing. The language says the obvious thing is a non-deduced context.

Both stories end in working production code. Neither ends in a fully generic solution, and Arutyunyan is upfront about that.

> **Note on reflection.** During the talk's review process, someone suggested this material is obsolete now that C++26 has reflection. Arutyunyan's answer: TBB still supports **C++11**, and users don't switch language versions on a library author's schedule. The techniques stay relevant for anyone who can't demand C++26 from their callers.

## Story 1: generating a constructor with exactly N parameters

TBB has `blocked_range` — nothing to do with C++20 ranges; it predates C++11. It carries a `begin`, an `end`, and a **grain size** telling the parallel algorithms the smallest divisible chunk. There's a 1D version, a 2D version, a 3D version, and then a customer asked for 4D. Rather than keep going, the team wrote `blocked_nd_range`.

The starting constructor is the obvious variadic one:

```cpp
template <typename T, unsigned N>
class blocked_nd_range {
public:
    template <typename... Args>
    blocked_nd_range(const Args&... args) : my_dims{args...} {}
private:
    std::array<blocked_range<T>, N> my_dims;
};

blocked_nd_range<int, 2> r(blocked_range<int>(0, 10),
                           blocked_range<int>(0, 20));   // works
```

(In real TBB there are `enable_if`s pinning `sizeof...(Args) == N` and keeping the one-argument case from hijacking the copy constructor. He skips them to save screen space.)

What users actually want to write is this:

```cpp
blocked_nd_range<int, 2> r({0, 10}, {0, 20});   // does not compile
```

**Why it fails** — answered from the audience, correctly and immediately: a braced-init-list has *no type* until overload resolution and template argument deduction have finished, so it cannot contribute to deducing `Args`. It's a non-deduced context. It *could* have been made to deduce as `std::initializer_list`, but C++ didn't go that way.

### Attempt 1: `std::initializer_list`

The team's actual first move. It's a dead end for several reasons at once:

- You'd need *multiple* `initializer_list`s — one per dimension — and packs of them don't behave.
- Passing four values where `blocked_range` takes at most three fails **silently at runtime**, with no way to report it.
- It would force `blocked_range` to be **default constructible**, which it isn't and which no customer asked for. Designing the class around the convenience constructor is the tail wagging the dog.
- Barry Revzin's objection: the types are wrong anyway. `blocked_range` takes two `T`s and a `size_t`; an `initializer_list` is homogeneous.

The room's verdict on `initializer_list` in general got a laugh: *"It's almost always a bad solution."*

### Attempt 2: `std::array`, and the three-brace problem

```cpp
blocked_nd_range(const std::array<blocked_range<T>, N>& dims) : my_dims(dims) {}
```

Nothing is deduced here — `T` and `N` come from the class instantiation — so all that's needed is for the argument to be constructible. It compiles. The call site is the problem:

{% raw %}
```cpp
blocked_nd_range<int, 2> r{{{{0, 10}, {0, 20}}}};
```
{% endraw %}

Arutyunyan admits he originally got there by adding braces until the compiler stopped complaining, in 2018, when he'd just started with modern C++. But the count is explainable, and he explains it with pseudo-code: the layers are the brace for **`blocked_nd_range`**, the brace for **`std::array`**, and the brace for the **C array inside `std::array`** — plus the innermost braces that become the `blocked_range`s themselves.

### Attempt 3: a raw C array + `std::to_array`

Drop one level of abstraction, drop one level of braces:

```cpp
blocked_nd_range(const blocked_range<T> (&dims)[N]) : my_dims(std::to_array(dims)) {}
```

Better — but still wrong for the *common* case. The constructor now takes **one object**, so even users passing two plain `blocked_range`s are forced to wrap them in an extra brace pair. Fixing the exotic case broke the ordinary one.

### The solution: manufacture a pack from `index_sequence`

Step back and say what you actually want: a constructor with **exactly N parameters, each of type `blocked_range<T>`**. In C++17 there's no reflection to generate that, so you conjure the pack out of an `index_sequence` — using a primary template that is never defined and a partial specialization that does all the work.

```cpp
template <typename T, typename Idx>
class blocked_nd_range_impl;                       // never defined

template <typename T, std::size_t... Is>
class blocked_nd_range_impl<T, std::index_sequence<Is...>> {
    // the index value is ignored — we only want the pack's *length*
    template <std::size_t>
    using arg_type = blocked_range<T>;
public:
    blocked_nd_range_impl(arg_type<Is>... args) : my_dims{args...} {}
private:
    std::array<blocked_range<T>, sizeof...(Is)> my_dims;
};
```

The trick is that `arg_type<Is>...` **discards the indices entirely** and maps a pack of length N onto N parameters of the type you wanted. `make_index_sequence` is doing nothing but supplying a pack of the right length — a point Arutyunyan makes explicitly later: *"we use it only to deduce a pack, that's all."*

An audience member proposed a default template argument on the class instead — `typename Idx = std::make_index_sequence<N>` — which works, but leaves a knob users can grab and misuse. Hide it behind an alias instead:

```cpp
template <typename T, unsigned N>
using blocked_nd_range = blocked_nd_range_impl<T, std::make_index_sequence<N>>;
```

Now `N` disappears from the implementation class as well (it's `sizeof...(Is)`), and the call site is the one users wanted from the start:

```cpp
blocked_nd_range<int, 2> r({0, 10}, {0, 20});
blocked_nd_range<int, 2> r2(blocked_range<int>(0, 10), {0, 20});   // mixing is fine
```

This shipped as experimental, and it works all the way back to C++11 (modulo hand-rolling `make_index_sequence`).

### Then C++17 arrived, and with it a chicken-and-egg problem

Class template argument deduction should let users drop `<int, 2>` entirely. But the deduction guide needs `N`, and generating the constructor needs `N` *first*. Worse, two structural problems block any guide at all:

1. **You can't write a deduction guide for an alias template** in C++17 — that's a C++20 feature.
2. The primary template is undefined, and deduction only ever looks at the primary.

So the alias becomes a struct that inherits:

```cpp
template <typename T, unsigned N>
struct blocked_nd_range : blocked_nd_range_impl<T, std::make_index_sequence<N>> {
private:
    using base = blocked_nd_range_impl<T, std::make_index_sequence<N>>;
    using base::base;    // inherited ctors keep the *base's* access, not this one's
};
```

The `private` there is deliberate mischief, and it drew the expected "got to be public" from the room. It isn't: for **inheriting constructors**, the access specifier on the using-declaration is ignored — the constructors keep the accessibility they had in the base. The audience enjoyed that one.

### The deduction guide: a parameter pack of C arrays

Here's the piece Arutyunyan bet at least some of the room had never seen:

```cpp
template <typename T, std::size_t... Ns>
blocked_nd_range(const T (&...)[Ns]) -> blocked_nd_range<T, sizeof...(Ns)>;
```

That parameter is a **pack of C arrays** — `const T (&...)[Ns]` — expanded by the array-bound pack `Ns`, with no separate `...` needed on the parameter itself. When he first saw this on cppreference his reaction was *"nobody would ever need that."* And here we are.

Deducing a single `T` for all of them is intentional: he could decompose into head and tail and verify they match, but why, when the compiler will enforce it for free.

The mechanism is worth stating plainly, because it's why the whole thing hangs together. **Deduction guides are separate from constructors, and run first.** Phase one uses whatever you wrote at the call site to deduce `T` and `N` — here the braced-init-lists are read as C arrays purely as a *proxy* for that deduction. Phase two then requires the same arguments to match some real constructor, unambiguously — and by then the N-parameter constructor has been generated. Gašper Ažman pointed out that `std::initializer_list` would serve equally well as the proxy; both work, both carry the same limitation.

Verifying it actually deduces something, rather than merely compiling, is done with a deliberate error on `decltype`:

```cpp
blocked_nd_range r({0, 10}, {0, 20});
decltype(r)::nonexistent x;   // error message prints blocked_nd_range<int, 2>
```

Add a third dimension and the message says `3`. Make the values unsigned and it says `unsigned int`. Asked whether this works on every compiler: yes — it's production code in TBB, and he's just demonstrating on GCC.

**The limitation** he can't remove: every value must have the same type, because they all feed one `T`. `blocked_range`'s grain size is `std::size_t`, so `{0, 10, 2u}` breaks the guide. The escape hatch is ordinary — spell out the template arguments explicitly and you're back to the general constructor. And an iterator-typed `T` (`const char*`, say) can't work either, since the grain size genuinely needs to be a number; you could constrain to random-access-and-sized and compute it, but that would be *"torturing the original class."*

### Failing loudly instead of confusingly

Four values in a dimension will pass the deduction guide and then fail on constructor matching — technically a compile error, but not a readable one. So put the check where the user can see it:

```cpp
template <std::size_t... Ns>
struct n_checker {
    static_assert(((Ns == 2 || Ns == 3) && ...),
                  "each dimension takes exactly 2 or 3 values");
    static constexpr std::size_t value = sizeof...(Ns);
};

template <typename T, std::size_t... Ns>
blocked_nd_range(const T (&...)[Ns]) -> blocked_nd_range<T, n_checker<Ns...>::value>;
```

Asked why not `enable_if` or a constraint, the room converged on the same answer, and it's the most transferable lesson in the talk. A SFINAE failure produces *"I couldn't find an overload"* followed by a pile of candidates the user has to reason through — and, as Barry put it, none of which have anything to do with what they thought they were asking for. A hard error says **"right here, you messed up."** Four values in a dimension is never going to become correct later, so don't leave the door open for it. The cost is compile time, and that trade is the library author's to make.

## Story 2: deduction guides for function-like objects

Same origin — TBB's **flow graph**, an asynchronous graph API that long predates `std::execution`. The `function_node` has an input type, an output type, and a type-erased callable:

```cpp
template <typename Input, typename Output>
class function_node {
public:
    template <typename F>
    function_node(F f);
};

function_node<int, int> fn([](int x) { return 3; });
```

The engineer originally assigned the deduction guide reported back that determining a lambda's signature at compile time is **impossible**. It isn't — and the disproof is one line, because `std::function` obviously does it.

### Decomposing `&F::operator()`

A lambda is an object; what you want is the signature of its call operator. Take its address, then match on the type:

```cpp
template <typename Sig> struct params;              // undefined primary

template <typename Out, typename C, typename In>
struct params<Out (C::*)(In) const> {
    using input  = std::decay_t<In>;
    using output = std::decay_t<Out>;
};

template <typename F>
using signature = params<decltype(&F::operator())>;

template <typename F>
function_node(F) -> function_node<typename signature<F>::input,
                                  typename signature<F>::output>;
```

The one deliberate bug he planted was the missing `const` — a lambda's `operator()` is const unless declared `mutable` — and the room caught it instantly. Supporting `mutable` lambdas means **duplicating the specialization** without the `const`. There's no way around that; it's exactly why `std::function`'s implementation carries a wall of specializations for every combination of `const`, `volatile`, ref-qualifier, and (since C++17, when it became part of the type) `noexcept`.

A wonderful aside for anyone who has stared at those signatures: in `Ret(Args......)`, the **first three dots are the pack expansion and the last three are the C ellipsis**, and the standard doesn't require a comma between them. (It does now — cppreference has some updating to do.)

The `decay_t` is deliberate: TBB requires plain types in the template arguments, no `const`, no references. And to catch the mismatch early, the guide asserts that the deduced parameter is either the input by value or `const Input&` — L-value-qualified parameters aren't supported, for reasons that are probably historical or lifetime-related.

### The "clearly impossible" case: an overloaded `operator()`

The same engineer came back and said decomposing lambdas was fair, but a callable with **two** `operator()` overloads was definitely impossible — `&F::operator()` is ambiguous, and which one did you mean?

Arutyunyan's response: *"it's probably too early to give up."*

C++ has a rule for taking the address of an overloaded function: if the **target** — a variable's type, an assignment, or **a function parameter** — is specific enough, it resolves the overload for you. There are no variables here. But there *is* a fact about the API worth exploiting: `function_node` supports exactly **one** argument. Never zero, never two. That's the hint.

```cpp
template <typename Out, typename In>
struct params {
    using input  = std::decay_t<In>;
    using output = std::decay_t<Out>;
};

// the parameter type IS the hint: "the unary one, please"
template <typename Out, typename C, typename In>
auto deduce_unary(Out (C::*)(In) const) -> params<Out, In>;

template <typename Out, typename C, typename In>
auto deduce_unary(Out (C::*)(In)) -> params<Out, In>;

template <typename F>
using signature = decltype(deduce_unary(&F::operator()));
```

Passing `&F::operator()` as an argument to `deduce_unary` places it in a context where the parameter type — a pointer to a member function of exactly one parameter — picks the right overload. The binary overload is simply not viable, and the ambiguity evaporates. Gašper's follow-up landed too: with `deduce_unary` returning `params` directly, the intermediate `signature` struct disappears entirely.

Someone in the room immediately asked the obvious next question: what about **two unary overloads**, one taking `short` and one taking `double`? That one is genuinely impossible, and not for a technical reason. As the room sharpened it: it isn't which hint you'd use, it's **which result the user wanted**. You'd be guessing on their behalf, and you'd sometimes guess wrong.

### Where it stops

**Generic lambdas don't work.** Neither does any templated `operator()` — even one where the parameter *count* is obviously fixed and unambiguous. Arutyunyan went looking for the reason and found a bare statement in the standard with no rationale: taking the address of a function template is a **non-deduced context**. That's the whole explanation.

The closing Q&A sketched two futures. **`decltype(call)`**, a proposal with a paper and an implementation and reportedly close to landing, would allow the template-versus-non-template disambiguation. And **reflection** can enumerate the call operators and pick the unary one, ignoring the templated ones — though it still can't resolve two unary overloads, because nothing can.

## Takeaways

Three techniques:

1. **Generate a constructor with a chosen number of parameters** by conjuring a pack from `index_sequence` and discarding the indices. An undefined primary template plus a partial specialization is the only expansion context you get — which is exactly why the same trick can't be applied to the deduction guide.

2. **Deduce from braced-init-lists** via a pack of C arrays (or an `initializer_list`), treating it purely as a proxy for `T` and `N`. The guide runs first and independently; the real constructor is matched afterward.

3. **Deduce from function-like objects** by decomposing `&F::operator()`, resolving overloaded call operators by exploiting an arity constraint the API already guarantees.

The through-line: each of these ships an API where the *ordinary* call site is the short one, the *unusual* one still works by spelling out template arguments, and the *wrong* one produces an error pointing at the mistake rather than at the library. Metaprogramming complexity absorbed by the author so it never reaches the user.

> *"Never give up, by the way. When you think it's impossible, the solution might be just around the corner."*
