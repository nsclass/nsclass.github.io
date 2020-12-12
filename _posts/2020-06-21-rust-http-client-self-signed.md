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

`reqwest` is a HTTP client in Rust.
[https://github.com/seanmonstar/reqwest](https://github.com/seanmonstar/reqwest)

It supports to send a HTTP request for self signed certificate site as shown in below.

Full source code can be found from the below github including http server/client.

[https://github.com/nsclass/rust-https-server-client](https://github.com/nsclass/rust-https-server-client)

```rust
#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let res = reqwest::Client::builder()
        .danger_accept_invalid_certs(true)
        .build()
        .unwrap()
        .get("https://localhost:8088/")
        .send()
        .await?;

    println!("res: is {}", res.status());

    Ok(())
}
```
