---
layout: single
title: Rust - HTTPS client for self signed certificate
date: 2020-06-22 09:30:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - Rust
permalink: "2020/06/22/rust-https-self-signed-certificate"
---

`reqwest` is one of the best HTTP client in Rust.
[https://github.com/seanmonstar/reqwest](https://github.com/seanmonstar/reqwest)

It supports to send a HTTP request for self signed cerificate site as shown in below.

```rust
fn main() {
    let res = reqwest::Client::builder()
        .danger_accept_invalid_certs(true)
        .build()
        .unwrap()
        .get("https://invalidcert.site.com")
        .send()
        .unwrap();

    println!("res: is {}", res.status());
}
```
