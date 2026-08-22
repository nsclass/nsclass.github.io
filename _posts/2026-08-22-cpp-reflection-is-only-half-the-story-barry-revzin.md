---
layout: single
title: "C++ - Reflection Is Only Half the Story (Barry Revzin, C++Now 2026 Keynote)"
date: 2026-08-22 14:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
  - reflection
  - metaprogramming
permalink: "2026/08/22/cpp-reflection-is-only-half-the-story-barry-revzin"
---

[Barry Revzin - Reflection Is Only Half the Story - C++Now 2026 Keynote](https://www.youtube.com/watch?v=DZTkT1Cq_aY)

Reflection is the headline feature of C++26 — arguably the most significant addition to the language in many standards. Barry Revzin, a senior C++ developer at Jump Trading and the author of dozens of committee papers across C++20, C++23, and C++26, opens his C++Now keynote by granting all of that, and then immediately points at what's missing:

> C++26 gives us reflection. But reflection primarily only lets us **observe**. The important next question is: what might it look like if we were to **generate**?

That's the whole talk. The observation half landed in C++26. The generation half is still an open design problem, and Revzin spends ninety minutes surveying the design space — starting with C macros, detouring through Swift and Rust, and ending without a definitive answer but with much better questions.

## The guideline: no raw code

Start with the list of things reflection lets us do better: formatting, serialization, structured arrays, command-line argument parsing, foreign language bindings, hashing, and — finally — enum to string.

Look closely at that list and something jumps out. **Every one of those is something we could already do.** You can write all of it by hand. We don't want to, because we want code that writes code for us. Not because it feels elite (although Revzin concedes that it does), but because it's extremely practical for general software engineering.

The motivating example is a config type with a string and an int. You want to print it, so you write a formatter. The code isn't long or complicated, and it's easy to teach. (Revzin suggests AI tooling can produce it reliably; an audience member disagrees — *"I find it's terrible at it."*)

The problem isn't the formatter's length or complexity. **It's that the formatter has to exist at all.** Config types change constantly over an application's lifetime. Add a member, forget to update the formatter and the YAML serializer, and everything still compiles and runs — you just have an incomplete representation of your application in your logs forever.

With reflection, you slap an annotation on the type, and one specialization of `formatter` looks for that annotation and does the default member-wise thing. All those hand-written formatters go away.

This leads to a guideline Revzin proposes for the future, in the spirit of Sean Parent's *no raw loops*:

> **No raw code.**

Parent doesn't mean never write a loop. He means recognize when what you're really writing is an algorithm, and use the algorithm. Same idea here: when you're writing formatters and serializers — code that *should* be generated from code that already exists — recognize that it's incidental, not business logic, and generate it.

We're not there yet. So how do we get to the flying cars? Revzin's approach is to take several steps backward first.

## Step one backward: C preprocessor macros

C macros get a bad rap in the community, "and that's because **they're really bad**."

The list of sins is familiar:

- **No scoping.** You never know whether code you wrote is invoking a macro. This is why every standard library implementation is littered with those ugly reserved identifiers.
- **No understanding of language semantics.** The preprocessor runs before template instantiation and knows nothing about templates. Pass a template argument with a comma in it and the macro thinks you handed it two or three arguments.

But set those aside, and macros are *still* underwhelming, because they have **no control flow**. You can conditionally define a macro, but inside a definition you can't condition, loop, pattern match, or recurse. None of the things you learn in week one of a new language.

Revzin's analogy is sharp:

> If someone told you they were a Rust expert but didn't know how to write a for loop, you'd be highly skeptical. If someone told you they were a C expert but didn't know how to approximate a for loop in a C macro — you'd be like, "yeah, me neither."

And yet control flow is genuinely useful, so people build it anyway. Revzin shows the macro in his own codebase: excessively parenthesized, name much longer than shown, and it generates members with conditional initializers, a function to iterate over all members (approximating reflection), and a hook to build a formatter. Every individual transformation is trivial. The macro is incredibly complicated and very hard to write. And when you typo `Sring` instead of `String`, the compiler helpfully hands you thousands of lines of preprocessor expansion stack that have nothing to do with the typo.

They use it anyway, because it's useful.

He's hardly the first to notice. Guy L. Steele and Richard Gabriel wrote, over 30 years ago in the second edition of *History of Programming Languages*, that by comparison to Lisp macros the C preprocessor is completely anemic — substitution and token concatenation only — and that Lisp users find this laughable. Their question is the one Revzin returns to all talk: **why settle for anything less than a full programming language?**

C has control flow. The preprocessor doesn't.

## Step two: class templates, and control flow by accident

When people wanted to parameterize types in C++, they started with macros. Revzin shows the original `vector` implementation from Cfront — a header that predates his birth by a few weeks, and predates `const` and namespaces in C++.

Class templates were the answer, and they're obviously better at parameterizing types. But they still have no `if`, no `for`, only top-level pattern matching and recursion (nothing in the body), and no way to group declarations the way functions do.

That's not surprising: **class templates were never designed to be a general-purpose code generation facility.** But life finds a way.

- `enable_if` is how you write a conditional member. It has "if" in the name, so we can squint at it — but this is not how conditionals are written anywhere else in the language.
- Loops are worse. For `tuple`, you want a member per type in the pack. Member packs don't exist. You can expand a pack in the base class list, but you can't have duplicate base classes, or scalar/pointer/reference bases. So you generate a list of base classes with a meta function, then need a helper in the middle to unpack that list for you.

> This is a very strange way to write a loop. Where is the loop in this code? You just have to know that it exists.

Boost.MP11 is great, Revzin says, but it isn't how he wants to think when he's coding.

## How reflection nearly went the other way

The reflection we ended up with wasn't the obvious destination. When work started, template metaprogramming was *the* way to solve problems, so building reflection on top of it seemed logical. The original static reflection paper had a reflection operator returning a unique type, with a library of meta functions to template-metaprogram around it. Familiar to everyone.

Then David Vandevoorde wrote a paper arguing for reflecting **values** instead, with a line Revzin clearly enjoys: let's design with modern C++ in mind and leave the template metaprogramming shackles of the past behind. *"And it rhymes, so you know it's a true statement."*

That kicked off years of discussion with Louis Dionne about the actual design space — type-based or value-based, and if values, should the reflection operator always return the same type or vary by what's reflected? The organizing principle that emerged:

> **Metaprogram by design, not by accident.**

That led to P1240 (scalable reflection), which established the single `meta::info` type, which led to P2996, the design adopted for C++26. Some of these papers are separated by many years, and there were good reasons to have wanted something else. So: did we end up in the right spot?

### The evidence: writing `is_structural` twice

Type traits used to be the compiler's exclusive territory, because only the compiler could see class internals. Reflection lets you write your own. Revzin needed `is_structural` — the trait for types usable as constant (formerly non-type) template parameters — and implemented it both ways.

The **C++26 reflection version** is a near-literal transcription of the core language wording. A type is structural if it's scalar, an lvalue reference, or a class type with certain properties. The only genuinely awkward part is that the core language's "class type" includes unions while the library's `is_class` excludes them, so you have to spell out both.

For the class case, you look at base classes and non-static data members — together, the subobjects — and since both sub-bullets check a property shared by *all* subobjects, one `ranges::all_of` handles it. `subobjects_of` has a precondition that it only accepts class-type reflections, but that's fine: it's guarded by the class-type check, and the call is only ever *evaluated* when that check passes.

```cpp
// Sketch of the shape: ordinary C++ control flow over reflections
consteval auto is_structural(std::meta::info type) -> bool {
  return is_scalar_type(type)
      || is_lvalue_reference_type(type)
      || ((is_class_type(type) || is_union_type(type))
          && std::ranges::all_of(subobjects_of(type), /* public, non-mutable,
                                    structural after removing extents */));
}
```

It took a couple of minutes to write, and the only bugs were typos. The reason it's easy:

> This is just C++ code. I'm traversing a data structure that happens to deal with reflection, but that's incidental. I can use my same ranges algorithms in the same way I deal with any tree or vector or map.

And there's no prescribed style. Use ranges, use a different ranges library, use raw loops — whatever fits your codebase.

The **type-based metaprogramming version** looks nothing like it. `get_subobjects` has a precondition that it can't be *instantiated* with a non-class reflection, so instead of a boolean guard you need a guarded partial specialization. The result is a disjunction, but nothing about the code says so:

> How can you tell that this is a disjunction, and that these are my main categories? You just have to know that's what it means. And you also have to just know that this is complete — that I don't intend there to be any other specializations.

It's a different mode of thinking: step one, figure out how to solve the problem; step two, figure out how to fit that solution into the box.

A function-style variant using Boost.MP11 is more concise, but exposes the other issue: he uses `mp_for_each` because it's the only algorithm taking a lambda (which he needs for recursion). There's no `mp_all_of` taking a lambda. **He wants an `all_of` and approximates it with a `for_each`.** It works and gives the right answer, "but it doesn't bring me joy."

### The two models, side by side

| | Template metaprogramming | Reflection programming |
|---|---|---|
| Conditions | partial/explicit specializations | `if`, `&&`, `\|\|` |
| Preconditions | defer *instantiation* | defer *evaluation* |
| Toolbox | dedicated metaprogramming libraries | the standard algorithms you already use |

Deferring evaluation is much easier than deferring instantiation, because you can just use conditionals.

The core issue is the last row. Metaprogramming libraries are good and useful, but they're a whole new thing existing to solve one problem in one domain. With reflection you reuse the algorithms and data structures you already know; you learn the reflection bits and nothing else.

Borrowing again from Steele and Gabriel: **template metaprogramming is an anemic functional sublanguage.** Revzin has nothing against functional programming — but compare TMP to Haskell and we're missing everything that makes functional programming pleasant. Reflection programming can use *most* of C++, and that "most" grows every standard. Nobody is going to bolt a functional language onto the TMP world.

> Template metaprogramming was **discovered**. Reflection was **designed**. Reflection programming really is just regular programming that happens to operate on reflections.

## So what should code generation look like?

Whatever shape it takes, Revzin's high-order bid is already clear: **it should be C++, not a new sublanguage with its own domain and limitations.**

To find candidate answers, he turns to two "programming language luminaries": Igor Stravinsky ("a good composer does not imitate, he steals") and Tom Lehrer, who advised plagiarizing — *only be sure always to call it research.*

C++ is not the first language to think about source code generation. Lisp came up earlier but is too different to borrow from directly. The two worth studying are **Swift and Rust**: newer than C++, influenced by C++ (particularly its mistakes), well designed, and well regarded by their communities.

At a high level they share a lot:

- Both are **definition checked** — if a template compiles, it works for all instantiations. Not strictly about code generation, but worth holding in mind.
- Both use **macro systems** for code generation (Rust has two).
- **Macro invocations are visually distinct.** You always know you're looking at one.
- Both have two forms: an expression/declaration form that injects code, and a **decorator form** attached to an existing declaration — the analogue of a C++ attribute or annotation.

### Rust: tokens in, tokens out

`#[derive(Debug)]` on a struct makes it printable member-wise; `println!` is itself a macro, marked by the trailing `!`.

What `derive(Debug)` literally does: look up a function implementing the macro and pass it **the tokens it's attached to**. No semantic analysis. The function's job is to produce other tokens that get injected.

This is purely a token layer. If the struct were generic, those tokens come through too — **the macro operates on the template itself, not on any instantiation.** Which is an interesting thing to consider from a C++ perspective, where templates are barely parseable to begin with. In Rust, it's just how things work.

The implementation parses the token stream into a syntax tree, pattern matches to pull out the fields (Rust's enums make this pleasant), and for each field generates a small piece of syntax via `quote!`. In the abstract, `.field(...)` isn't a valid Rust expression — you can't start an expression that way. **That's fine. Nothing is syntax checked yet.** These are just tokens. The full token set is assembled with interpolation for the type name, and the syntax isn't checked until the macro is invoked and the compiler slurps up the injected tokens.

Which is a little surprising for a fully definition-checked language. But that's the system.

### The push/pull difference that actually matters

Compare the two approaches on the same problem. In C++, the reflection of `config` comes in — the compiler has fully parsed and analyzed the type. In Rust, it's token parsing all the way; you can see that the type of `name` is `String`, but you can't ask anything about `String` or make decisions based on its properties.

But the more interesting difference is directional:

- **C++ is a pull model.** A specialization of `formatter` checks for the presence of the annotation. It's *looking for* the thing.
- **Rust's `derive` is a push model.** It injects the implementation of `Debug` directly into the codebase.

These mostly mean the same thing — **except when they don't.** Suppose another partial specialization of `formatter` also matches `config`; the standard library has one that matches ranges. If your annotated config type happens to be a range, you now have two matching partial specializations. Which wins? **Neither. It's ambiguous, and there's nothing you can do about it.**

The only escapes are for `config` to take steps so the other specializations don't match, or for every other specialization of `formatter` to know about the annotation and reject it. Neither is a complete solution.

> We really do want to move to the push-based model for cases like this, because the user's intent is obvious. I wrote this annotation because I want *this* formatter. I don't care about anything else that happens to match.

### Swift: strings, mostly

Swift's `@Debug` follows similar logic, but the function receives **the syntax tree** rather than raw tokens, and returns syntax — which, notably, is constructed **from a string**.

The implementation conforms to the `ExtensionMacro` protocol with a function whose signature is daunting ("to be honest, I don't know what most of these parameters mean"), of which one parameter matters: the declaration being attached to. From there you require it to be a struct, walk its members, and `compactMap` to keep only the variables.

Handling every real case is work — multiple declarations per line, computed properties, destructuring-like syntax — but Revzin's point is that these are *handleable*, because **it's just data structure manipulation in regular Swift**. You end up with an array of strings: the member names. Then you build up the syntax to inject, and Swift's string facilities make things like joining with a comma pleasant — "unlike some other languages that I'm familiar with."

The cost: nothing is checked at definition time. You're building a string. If you get a name wrong, nothing catches it until injection. And like C macros, if the injected code needs parentheses to be correct, **you have to write the parentheses yourself.** Unlike C macros, it's real Swift code doing the building.

An audience member pushes on this: isn't it really just a Python codegen script that globs strings together, only in the target language? And what are the *advantages* of push over pull, beyond late syntax checking? Revzin separates the questions: the advantage of push is that **you reliably get the customization you want**, instead of juggling competing specializations — a problem C++ has inherently, since we lack a real language-level customization mechanism. How you produce the syntax is an independent axis.

### What C++ can and can't steal

| | Swift | Rust declarative | Rust procedural |
|---|---|---|---|
| Input | parsed expressions / AST | a pattern you supply | tokens, you're on your own |
| Output | string or AST | tokens | tokens |
| Checking | late | late | late |
| Power | full Swift function | substitution + repetition | full Rust function |

Both are purely additive — no mutation of existing code. Swift requires you to **declare what names your macro will inject**, which is nice for tooling; Rust is anything-goes. And because both are ultimately string-to-string or token-to-token, **the macros are easy to test**: you assert on the output.

Revzin's read for C++:

- **The token/string/AST *input* model probably doesn't work for us.** Rust and Swift are parseable. C++ is "maybe not." Passing raw tokens of a whole class template is unlikely to pan out. **We have reflection — lean on the compiler to parse and hand us a reflection.**
- **The raw syntax *output* model is appealing.** That's the half worth stealing.

## Thought experiment #1: `tuple_cat` with token sequences

`tuple_cat`'s specification is daunting — eight variables, superscripts *and* subscripts — but the algorithm isn't complicated. Produce a `tuple` whose types come from the tuple elements of each argument in order, and whose expressions are the corresponding calls to `get`.

Given a one-tuple, a pair, and a three-element array, you walk each argument, walk that argument's elements, and build up the result. That's the algorithm.

Step two is fitting it into something that works. The best approach Revzin knows — credited to Peter Dimov — is: number your arguments; for each, produce the sequence of indices into it; extend the outer list to match the inner list's length. You end up with two integer lists of the same length (six, for this example), and that pair lets you do **a single pack expansion** to produce the whole result at once. You want one pack expansion because we don't have iteration, and building tuples piecewise would multiply copies and moves.

Getting there requires a meta function converting a tuple to its type list (wrapping `tuple_element_t` because it takes an `int` and MP11 wants types), plus a good deal more metaprogramming for the inner and outer lists. C++26 improves it — structured bindings and packs let `inner` and `outer` be actual constexpr integer lists rather than type lists — so you can finally write `tuple_cat` as one function template with no indirection. Except for the three alias templates up front, since local alias templates don't exist.

> This doesn't really resemble the original algorithm. But it works.

Now borrow Rust's idea of raw token sequences. Build two vectors — one of reflections for the types, one of token sequences for the expressions — using **two ordinary nested loops**. The inner one produces something like a `std::get<K>` call on the I-th argument, with `K` and `I` interpolated into the token sequence. Then `substitute` (which *is* in C++26) forms the return type, the expressions get joined with commas (which is *not* in C++26), and the whole return statement is injected.

```cpp
// Proposed syntax only — token sequences are not in C++26 and may never ship.
std::vector<std::meta::info> types;
std::vector<std::meta::info> elements;   // token sequences
for (auto [i, r] : std::views::enumerate(arg_types))
  for (std::size_t k = 0; k < tuple_size(r); ++k) {
    types.push_back(tuple_element(k, r));
    elements.push_back(^^{ std::get<\(k)>(std::get<\(i)>(args)) });
  }
```

Revzin is explicit that this is a thought experiment: token sequences are proposed, not standardized, and may never be in any C++.

Why he prefers it isn't the length:

> I don't like it because it's shorter. It *is* shorter, but that's a consequence of the real reason — **it's simpler.** I know what algorithm I want, and I just do that.

And once you're writing regular C++, you can iteratively build things up — impossible in the TMP world — and the review conversation shifts from "what are all these MP11 algorithms, is this even debuggable?" to "shouldn't that loop be `views::enumerate`?" (Probably, yes.)

### The audience pushes back, hard

This section drew the most sustained questioning of the talk, and it's worth recording because the objections are real.

**Why backslash for interpolation?** You need *some* interpolation syntax, and it can't clash with anything valid in C++, since you must be able to inject any valid C++. Rust uses `#`; the preprocessor has already claimed that. Backslash happens to be available.

**Why not just return a vector of tokens, Rust-style?** That's essentially the same model — `queue_injection` takes the token sequence rather than returning it. Just a question of the technique's shape.

**Is the injection ultimately splicing?** For a reflection representing a type, what you want essentially always is *that type* — a pseudo-token meaning "you already know what this is, don't make me spell it out." The rare case where you want the reflection itself can wrap it in `reflect_constant`. Syntax weight matters here: make the common case light.

**Why not strings, with `std::format`?** Two problems. Tokens are easier on the compiler — lexed once on the way in, done — whereas strings must be re-lexed. And more importantly, **C++ string facilities aren't good enough.** Our main one is `format`, which uses braces for interpolation — so injecting C++ code means escaping braces constantly, and it stops looking like C++. Token sequences also get syntax highlighted when you paste them in. For C++, strings look strictly worse.

**Why tokens at all — why not describe the AST directly?** This is the sharpest challenge, raised by more than one person. Revzin's answer: to get to a syntax tree you need a notion of how to parse this, and C++ is very difficult to parse. What benefit would the extra machinery buy? He's skeptical there's much — you can't check much at that point anyway, and C++ is *worse* than Rust and Swift on how much is checkable. Framed as a standardization question: you'd have to standardize either the set of C++ tokens or the C++ syntax tree, **and no two compilers have the same syntax tree.** (The counter, fairly made: it would be an abstraction across compilers, not any one implementation's.)

**And the strongest objection**, from an attendee who accepts the input side entirely: C++ is not only difficult to parse, **it is difficult to generate.** If you hold reflections of expressions and want to produce their product, you have to think about whether one uses a bit-shift operator so you need parentheses. Introduce variables and you have to worry about name collisions. *"I'm going to make mistakes."* The analogy offered: SQL — a language designed for humans, generated by computers — where people make exactly these mistakes routinely.

Revzin moves on in the interest of time rather than answering, which is honest but leaves the objection standing.

## Thought experiment #2: push-based formatting via annotations

Back to formatting, and the push/pull problem. We have annotations, so the path forward is probably to use them: rather than passing tokens or AST into the annotation, **get a callback when the type is complete, with a reflection representing it.** Revzin thinks this is the more viable long-term model for C++.

The implementation requires the annotated entity to be a type, walks its non-static data members, and builds up the corresponding `format_to` calls — assembling the `.name={}` string literal and formatting the object. A `list_builder` helper handles inserting the `", "` delimiter between tokens (the first way he thought of; there are others). Then you inject an **explicit specialization** of `formatter` into namespace `std` — perfectly reasonable, since namespaces are open.

Because it's an explicit specialization, **the competing-specialization problem disappears entirely.** That's push-based formatting.

Asked whether he can actually compile the code he's showing: yes.

Asked what happens for classes and structs, which are closed rather than open like namespaces: `queue_injection` injects into the context you're currently in, so while you're building a class you can inject into it. But the `@Debug` annotation is handed the *completed* class, and **classes are immutable** — it cannot inject into it. Mutation is a whole class of problems the talk deliberately skips. The likely shape of an answer is the metaclass model, which wasn't mutation either: take the type, hide it somewhere, and produce a new type from scratch with the changes.

## The hard part: expression macros

The pinnacle of the code injection problem is macros — expression macros specifically.

Revzin thinks the C++ community over-generalizes from its bad experience with C macros to "all macros are bad everywhere." People who've used languages with *good* macros like them, because macros are useful. Swift and Rust both have very good ones.

### Swift's typed macros

Swift's canonical example — the one Xcode generates when you add a new macro — is `stringify`, which takes an expression and returns a tuple of its value and its source text. Exactly the kind of thing a function cannot do.

What's interesting is that **it's typed**. The declaration looks like a Swift function template; the only real difference is the keyword `macro` instead of `func`, plus a role annotation marking it as an expression macro. The arguments are parsed by the compiler on the way in and fully type checked — yet it's still a macro, so you control the resulting expression.

A `log` macro shows why that matters: if debug logging is disabled, you want the argument **never evaluated**. The implementation wraps the message in a closure. It takes work to get to that laziness, but you get there. Add `#file` and `#line` invocations — injected as strings, then evaluated at injection — and you get source location for free.

The consequence of requiring arguments to be parseable Swift: **you can't invent arbitrary syntax.** There's a C++ proposal for an implication operator; an `implies(a, b)` macro with lazy evaluation of `b` is easy. But if you want `a => b` specifically, you can't — that's not a valid Swift expression. You *could* define such an operator only for use in the macro and have the macro enforce the shape, but that feels weird and Revzin doubts anyone does it. The idiomatic escape is **make it a string** and parse it in the macro. Swift leans on this — there's a generate-boilerplate macro that takes a string of substitutions.

On the strongly positive side: Swift's standard library has a `predicate` macro where the lambda is fully type checked by the compiler — validating that `t.price` and `t.symbol` exist — and then **generates a completely different, serializable structure** from it. Readable predicate in source, serializable object at runtime, ready to store as JSON or ship to another application. That's a genuinely cool capability.

### Rust: do whatever you want

Rust's declarative macros take the opposite philosophy. You write a **pattern** to match input tokens against, and inject tokens built from the match. It isn't purely token-based: when you match an expression `$e`, you get the whole expression syntax node — so the precedence and parenthesization worries people raised earlier **don't arise**.

Arbitrary syntax is trivial here. Want `expr => expr` for `implies`? Write that pattern. Done. Writing DSLs this way is idiomatic in Rust:

- A multiplication-support macro can be invoked as `(U8 * NonZeroU8) -> U16` rather than taking four bare types, purely so the grouping is visible to the reader — even when it's only invoked three times, right there in the same file.
- Macros can have multiple patterns. `vec!` has two, plus a repetition primitive.
- You can build a Python-style dict literal — though not with Python's colon, because Rust expressions can contain colons and the compiler couldn't parse it. A fat arrow works, since expressions can't contain one.
- The most striking example: Tokio's `select!`, which picks among concurrent branches. **The syntax inside the invocation is not valid Rust and is completely meaningless as Rust** — and it's an extremely expressive way to write that code.

Rust's second system, procedural macros, is tokens in and tokens out, and it's on you to parse them. There's a library for that: you declare a type describing what you're looking for (expression, fat arrow, expression), implement how it parses from a token stream, then write a function that parses and returns tokens. Same result, more code.

Comparing them: the declarative version is far less code and the pattern is right there, clearly visible. But procedural macros are **just normal Rust functions**, so you can do arbitrarily complicated things. It isn't obvious the declarative approach wins.

The example that settles it is SQLx's `query!` macro. You write a SQL query, and the resulting rows have **named, typed fields** — `id` as `i64`, `name` and `email` as strings — accessed as identifiers, not string lookups. The library isn't guessing that `id` is probably an int. **At compile time, the macro connects to your database** (or something approximating it), validates the query, and looks up the actual types. Typo `id2` and you get a compile error, because there's no `id2`.

That is not achievable with pure token substitution and pasting. Having a full function available lets you do more things.

Revzin's summary of declarative macros is affectionate but pointed: they're closer to C macros than to functions — substitution and repetition — but they're *"what C macros could be if C macros were awesome."* Hygienic, scoped, grouped by AST nodes, no parenthesization worries. Still limited.

## What should C++ macros look like? (No answer)

Here Revzin is candid that he doesn't have much of an answer, so he works through examples to see what they teach.

**Forwarding.** A `FWD(x)` macro is in a lot of codebases — some people have several. Some use it to avoid instantiating `std::forward` for compile speed; Revzin likes it because **forwarding is a unary operation**, and `std::forward<T>(x)` is binary even though `T` is derivable from `x` almost always. Wrong arity. You could implement it type-based (type in, expression out), token-sequence-returning, or all-tokens (trivial, since you consume the entire input).

> What can we learn from forwarding? I don't think we can learn anything from forwarding. Any option basically works fine.

**Assert.** Going from one argument to two sounds minor. It's an enormous increase in complexity, **because counting expressions in C++ is hard.** Consider `call(a < b, c > (d))`. As a C macro, that's unconditionally two arguments. As real C++, **it depends on the types** — one expression or two.

> If we're going to have a new and better macro system, it had better parse this correctly based on what the code actually is. Otherwise, what are we even doing?

In a typed model, easy: declare the macro to take two expressions. In a token-sequence model, you suddenly need a parsing library and a whole set of abstractions for pulling expressions out of tokens — "maybe someone like Zach will come along and give us a library" — or you allow macro parameters to be declared as **kinds of grammar** and parse that way. Revzin doesn't know what that looks like.

**Boost.Lambda2-style operator definitions.** Defining many unary and binary function objects via macros. You could write a different macro per shape — or get cute and pass an expression *shaped like the use*, which neatly distinguishes `*x` (dereference) from `x * y` (multiplication), both of which are just `*` otherwise. Type-based, you can't do this at all except by passing strings, which is underwhelming. Rust manages it declaratively, and Revzin shows it: not so bad, but it gets complicated fast, and complex patterns get hard for users to read.

**Assert with context.** You want more than two expressions — a format string with additional information. Trivial with a variadic template in a type-based model. Much harder with token sequences.

**Terse lambdas.** Revzin has complained before about lambda verbosity. The flexibility is genuinely valuable for complex cases, but sorting points by `x` shouldn't cost that much syntax. This **cannot work in any type-based macro model.** With token sequences, sure: walk the tokens, find the identifiers, pick the largest one, derive the arity from it, generate the parameters, and inject the argument as the body.

So which way? Type-based handles assert-with-context cleanly and fails at terse lambdas. Token-based does terse lambdas and struggles with counting expressions. Revzin's slide shows paths going in every direction, some heading off into space:

> This undersells the difficulty. It's a pretty difficult problem — but one it'd be pretty cool to have a good solution for, because **people still use C macros for a lot of things, since C macros are so useful**, and it'd be nice to replace that with better technology.

Asked whether we must choose one — why not support both, taking a token sequence when you need generality and parsed types when you need power — Revzin lays out the tradeoff without resolving it. Token input is obviously the most general and handles all possible inputs. But how complicated are those implementations to write and understand? **Type-based is easier both for compiler implementers and for users**, because we've all written functions and function templates. Both have real benefits and real costs, and he doesn't claim more insight than that.

### The parsing problem, dissected

The closing audience discussion is the most technically dense stretch of the talk, and it circles one issue.

You can't parse C++ tokens without the symbol table — the existence of `typename` proves it. **Is `a<b>(c)` a template instantiation or two comparisons?** You cannot know without knowing what `a` is. So pure token input requires parsing that is contextual and correct, or the solution is bad.

Would an AST help, since it tells you how things were parsed? Maybe — but **not every C++ implementation even has an AST.** Anything standardizable would have to be very high level. "Expression" is viable. Narrower than that — binary operator, cast expression, assignment expression — and how precise do you want the grammar to be? It becomes a much harder problem.

One attendee argues C++26 is already doing this in the small: we query things about AST elements (we just don't call them that), and `define_aggregate` injects into the AST programmatically without tokens. Revzin half-concedes — none of those facilities ever talk about *specific elements of syntax* — but takes the point that some of this already happens without token streams.

Another attendee notes that compile-time parsing libraries already exist and both AST macro examples could be implemented at compile time in C++ today. **What's missing is the generation part.** But he draws a line: if you want to reflect on a function body, get a token stream, and parse it — parsing C++ at compile time from a token stream is, in his opinion, infeasible.

Revzin's counter: the compiler already parses C++ from a token stream, so we have an existence proof. The question isn't possibility but **how you make it easy to use** and how the right context gets threaded through. The rejoinder lands: the parser needs type information, and that's the hard part in C++.

> If only we had a parseable language, this would solve a lot of problems. But I think that ship has sailed a few decades ago.

And the alternative — hooking into the compiler's own parser — just relocates the problem: you'd need consistent parse results across all compilers, which means a **standard intermediate representation** anyway.

The last exchange is the sharpest. Someone points out that Rust derive macros being token-to-token is technically true but practically misleading: **everyone uses `proc-macro2`, which parses tokens into an AST and lets you output an AST.** Almost everyone operates entirely in AST-to-AST space, with token conversion only at the boundaries.

> What you hear here is people saying: I don't want to parse C++ from tokens. I want a library to do it.

To which someone else responds, decisively:

> Boy, oh boy, I do not want to embed the entirety of Clang into everything I have, just to use token generation.

## The conclusion

Revzin notes the shape of the journey with some amusement: this is C++Now, everyone came to learn about the cutting edge of C++, and he spent the time talking about C and then showing a great deal of Swift and Rust code — "notably not C++."

But the detour is the contribution. Looking at how languages fairly similar to ours made their choices is how you get better instincts for our own.

His personal position, stated as a position and not a conclusion: **token sequences are currently the most viable path for C++.** Reflection handles the input side; raw syntax handles the output side.

But the specific mechanism matters less than the principle, and this is what the whole keynote builds to:

> However source code generation ends up looking, **it must allow all of C++.** I don't want another discovered sublanguage with its own algorithms and its own domain libraries. Source code generation in Rust looks like Rust. Source code generation in Swift looks like Swift. I want source code generation in C++ to look like C++.

The closing Q&A has one more genuinely good challenge. If you were solving this today with an external two-step code generator — a script reading your struct and emitting a formatter, printer, serializer — **you would not write that script in C++.** C++ is a terrible language for writing compilers. So do we really want all of C++?

Revzin's answer goes back to why class templates beat macros in the first place. With macros you have a phase problem: one macro to declare your type, another to use it. Class templates removed it — deep inside a function template you just write `vector<T>`, with no place an external generator could have run. Reflection makes producing types on the fly far easier and far more interesting.

> I want these random types I'm producing on the fly to be formattable. Where in this process can I make them formattable, if not within C++?

External generators solve plenty of problems just fine. But for the core functionality, being outside the language adds enormous friction.

The follow-up — wouldn't you want a better language for the *string handling*, too? — leads to the talk's most practical aside. Revzin doesn't think strings are the right answer regardless, but he wants **basic string facilities**: `split`, `join`, `trim`. Swift joins with a separator by typing `.joined(separator:)` and not thinking about it. In C++, the moment you propose `split`, the conversation becomes "what does it return, and shouldn't it be lazy?" — when most string work happens in program configuration, where allocating a `vector<string>` is completely fine and five extra milliseconds of startup is irrelevant.

> I wonder how many versions of string split that just return a vector of string exist in the wild.
> **Thousands.**
> Well — that sounds like existing practice to me.

Asked about making runtime code generation syntax resemble compile-time code generation syntax, he's disarmingly brief: *"I've got nothing to offer there yet. Right now we just generate strings, and it sucks."*

---

C++26's reflection is a real achievement, and Revzin's `is_structural` comparison makes the case better than any abstract argument could: reflection programming is just programming, using the algorithms you already know, and template metaprogramming never was. But observation without generation gets you halfway. The other half is unresolved — token sequences versus typed macros, what's checkable and when, whether C++'s unparseability sinks the token approach, and whether generating C++ is as error-prone as generating SQL.

No answers yet. Much better questions.
