---
layout: single
title: Rust - AsRef usage
date: 2020-10-11 09:30:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - rust
permalink: "2020/10/11/rust-asref-usage"
---

`AsRef` is useful for generic function on accepting specific reference such as `str` or `Path`.
Please see the below example.
```rust
fn format_str(s: str) {
  
}

fn format_string(s: String) {

}
```

Above two function can be replaced by the below a single function with generic type which implement `str` reference.
```rust
fn format<S: AsRef<str>> (s: S) {
  let s_ref = s.as_ref()
}
```

[https://doc.rust-lang.org/std/convert/trait.AsRef.html](https://doc.rust-lang.org/std/convert/trait.AsRef.html)
[https://www.philipdaniels.com/blog/2019/rust-api-design/](https://www.philipdaniels.com/blog/2019/rust-api-design/)
