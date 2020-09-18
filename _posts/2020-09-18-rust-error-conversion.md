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
