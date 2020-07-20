---
layout: single
title: Rust - Cargo whatfeatures
date: 2020-07-20 07:30:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - rust
permalink: "2020/07/20/rust-whatfeatures"
---

Cargo whatfeatures can display features, versions and dependencies of crates

[https://libraries.io/cargo/cargo-whatfeatures](https://libraries.io/cargo/cargo-whatfeatures)

Install

```rust
cargo install cargo-whatfeatures
```

Examples

```rust
$ cargo whatfeatures serde
serde = 1.0.114
└─ features
  ├─ default
  │ └─ std
  ├─ alloc
  ├─ derive
  ├─ rc
  ├─ std (default)
  └─ unstable
```
