---
layout: single
title: Rust - Idiomatic Rust API design 
date: 2020-10-15 09:30:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - git`
permalink: "2020/10/15/rust-idiomatic-api-design"
---

Rust is great programming language because of default move semantic and trait system. Idiomatic Rust API is fully utilizing these concept to make it easy to use and looks elegant with zero overhead cost at runtime.

So it's crucial to understanding existing standard trait for Rust API design such as `From`, `Iterator`, `FromStr` etc and how trait allow us to extend the existing type.

The following links are useful resources to design idiomatic Rust API.
[https://rust-lang.github.io/api-guidelines/](https://rust-lang.github.io/api-guidelines/)
[https://deterministic.space/elegant-apis-in-rust.html](https://deterministic.space/elegant-apis-in-rust.html)
