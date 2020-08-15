---
layout: single
title: Rust - Iterator delegation
date: 2020-08-14 22:30:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - rust
permalink: "2020/08/14/rust-iterator-delegation"
---

Often, container structure having a single vector field needs to expose an iterator. The following code shows how to achieve this in a simple way.

## Iterator

```rust
pub struct ImagePathTrace {
    trace_paths: Vec<[f64; 7]>,
}

impl ImagePathTrace {
    pub fn values(&self) -> std::slice::Iter<'_, [f64; 7]> {
        self.trace_paths.iter()
    }
}
```

## Rayon Parallel Iterator

```rust
use rayon::{prelude::*, slice::Iter};

#[derive(Debug, Default, Clone)]
pub struct BatchInterpolation {
    batch_inter_nodes: Vec<InterpolationNodeList>,
}

impl BatchInterpolation {
    pub fn new(batch_inter_nodes: Vec<InterpolationNodeList>) -> Self {
        Self { batch_inter_nodes }
    }

    pub fn par_values(&self) -> Iter<InterpolationNodeList> {
        self.batch_inter_nodes.par_iter()
    }
}
```

## Github Source Code

Full source code can be found from the following url.
[https://github.com/nsclass/rust-svg-converter](https://github.com/nsclass/rust-svg-converter)

## More Detailed Explanation

[https://depth-first.com/articles/2020/06/22/returning-rust-iterators/](https://depth-first.com/articles/2020/06/22/returning-rust-iterators/)
