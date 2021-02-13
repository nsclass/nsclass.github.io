---
layout: single
title: Rust - Tower library
date: 2021-02-13 09:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - rust
permalink: "2021/02/13/rust-tower-library"
---
Rust Tower library provides an abstraction mechanism for network communication with asynchronous request/response.
In Rust, in order to define the trait with async feature, `async-trait` macro should be used and it will add overhead by allocating a memory. Tower library will address this issue while supporting the back pressure.

[https://github.com/tower-rs/tower](https://github.com/tower-rs/tower)