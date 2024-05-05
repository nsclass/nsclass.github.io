---
layout: single
title: Rust - Cancellation safety
date: 2024-05-05 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - rust
permalink: "2024/05/05/rust-cancellation-safety"
---

We need to aware of cancellation safety on using `select`.  Rust doc will describe the method the cancellation safety on IO operations.

[AsyncWriteExt::write_vectored](https://docs.rs/tokio/latest/tokio/io/trait.AsyncWriteExt.html#method.write_vectored)

```
Cancel safety
This method is cancellation safe in the sense that if it is used as the event in a tokio::select! statement and some other branch completes first, then it is guaranteed that no data was written to this AsyncWrite.
```
