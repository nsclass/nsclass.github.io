---
layout: single
title: Rust - Error Conversion
date: 2020-09-18 07:30:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - rust
permalink: "2020/09/18/rust-error-conversion"
---

Rust does not have an exception mechanism for error handling they provided the following two types.

```rust
enum Option<T> {
  Some(T),
  None
}

enum Result<T, E> {
  Ok(T),
  Err(E)
}
```

So often user needs to convert errors for using many libraries because each library will provide a different error type on handling errors.

Let's have a look below example.

```rust
enum LibError {
  GeneralError,
  UnknownErr
}
enum MyAppError {
  Error(String)
}
```

```rust
fn foo() -> Result<String, MyAppError> {
  let lib_result = lib_func();
  let app_result = match lib_result {
    Ok(lib_res) => format!("final result: {}", lib_res),
    Err(err) => {
      match err {
        LibError::GeneralError => return Err(MyAppError::Error("General error".to_string())),
        LibError::UnknownErr => return Err(MyAppError::Error("Unknown error".to_string())),
      }
    }
  }
  Ok(app_result)
}
```

Above code is very annoying to have match clause for every error case so we can use the `From<T>` trait to simplify it.

```rust
trait From<T> {
  fn from(value: T) -> Self;
}

impl From<LibError> for MyAppError {
  fn from(value: LibError) -> Self {
      match value {
        LibError::GeneralError => return Err(MyAppError::Error("General error".to_string())),
        LibError::UnknownErr => return Err(MyAppError::Error("Unknown error".to_string())),
      }
  }
}
```

Then we can use the following code for error.

```rust
fn foo() -> Result<String, MyAppError> {
  let lib_result = lib_func()?;
  Ok(format!("final result: {}", lib_res))
}
```

Actually, complier will expand the above code like this.

```rust
fn foo() -> Result<String, MyAppError> {
  let lib_result = lib_func() {
    Ok(lib_result) => lib_result,
    Err(error) => return Err(From::from(error)),
  }
  Ok(format!("final result: {}", lib_res))
}
```

Defining application specific error enum type is another hustle so there are some libraries to remove duplicated work.

`thiserror` is for library project. `anyhow` or `eyre` for application project.

`thiserror` example on defining a custom error type.

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

    #[error("maximum supported number of quantization color is 256")]
    NotSupportedNumberOfColorForQuantization,

    #[error("failed to generate layers")]
    LayerGenerationFailure,

    #[error("failed to generate scan paths")]
    ScanPathGenerationFailure,

    #[error("failed to generate batch interpolation list")]
    BatchInterpolationGenerationFailure,

    #[error("failed image path tracing")]
    ImagePathTracingFailure,

    #[error("failed to generate svg string")]
    FailureGeneratingSvgString,

    #[error("unknown error")]
    Unknown,
}
```
