---
layout: single
title: Rust - Index, mut Index operator example
date: 2019-01-06 04:57:54.000000000 -06:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - Programming
  - Rust
tags: []
meta:
  _edit_last: "14827209"
  geo_public: "0"
  _publicize_job_id: "26228789762"
  timeline_notification: "1546772274"
author:
  login: acrocontext
  email:
  display_name: acrocontext
  first_name: ""
  last_name: ""
permalink: "/2019/01/06/rust-index-mut-index-operator-example/"
---

```rust
use std::ops::{Index, IndexMut};
#[derive(Debug)]
pub struct ImageArray2 {
    data: Vec<u8>,
    rows: usize,
    cols: usize,
}
impl ImageArray2 {
    pub fn new(rows: usize, cols: usize) -> ImageArray2 {
        let data = Vec::with_capacity(rows * cols);
        ImageArray2 {
            data: data,
            rows: rows,
            cols: cols,
        }
    }
}
impl Index<usize> for ImageArray2 {
    type Output = [u8];
    fn index(&self, index: usize) -> &Self::Output {
        &self.data[index * self.cols .. (index + 1) * self.cols]
    }
}
impl IndexMut<usize> for ImageArray2 {
    fn index_mut(&mut self, index: usize) -> &mut Self::Output {
        &mut self.data[index * self.cols .. (index + 1) * self.cols]
    }
}
```
