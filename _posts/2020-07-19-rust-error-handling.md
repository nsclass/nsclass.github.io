---
layout: single
title: Rust - error handling with thiserror crate
date: 2020-07-19 07:30:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - rust
permalink: "2020/07/19/rust-error-handling-thiserror"
---

One of the most difficult decision to make on developing an application is how we can handle errors. The thiserror crate provide an easy way to handle errors for Rust application.

If we do not care of detailed error, anyhow can be one of candidate to consider too.
[https://github.com/dtolnay/anyhow](https://github.com/dtolnay/anyhow)

```rust
[dependencies]
thiserror = "1.0.20"
```

Defining an error enum.

```rust
use thiserror::Error;
#[derive(Debug, Error)]
pub enum Error {
    #[error(transparent)]
    ImageError(image::error::ImageError),

    #[error("not valid base64 image string")]
    NotValidBase64,
    #[error("failed to convert an image")]
    ImageConvertFailure,
    #[error("out of index on finding gaussian")]
    GaussianIndexError,

    #[error("failed to create a color quantization")]
    FailureColorQuantization,

    #[error("failed to generate a palette")]
    FailureGeneratePallette,

    #[error("unknown error")]
    Unknown,
}

```
