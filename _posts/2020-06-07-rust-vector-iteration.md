---
layout: single
title: Rust vector iteration
date: 2020-06-07 09:30:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - Rust
permalink: "2020/06/07/rust-vector-iteration"
---

The following example shows difference of iterating vector items between for and with iter() method

```rust
let vs = vec![1, 2, 3];
for (v : vs) {
  // consumes v, owned v
}
```

```rust
let vs = vec![1, 2, 3];
for (v : vs.iter()) {
  // borrows vs, & v
}
```

```rust
let vs = vec![1, 2, 3];
for (v : vs.into_iter()) {
  // this is equivalent to for (v: vs)
}
```

```rust
let vs = vec![1, 2, 3];
for (v : &vs) {
  // this is equivalent to vs.iter()
}
```
