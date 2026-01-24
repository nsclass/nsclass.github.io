---
layout: single
title: C++ - Pointer vs Reference
date: 2026-01-24 18:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2026/01/24/cpp-pointer-vs-reference"
---

This table comes from [Back to Basics: Forwarding References - How to Forward Parameters in Modern C++ - Mateusz Pusz 2023](https://www.youtube.com/watch?v=0GXnfi9RAlU)

| POINTER                          | REFERENCE                                     |
|----------------------------------|-----------------------------------------------|
| Objects                          | Alias (not an object)                         |
| Always occupy memory             | May not occupy storage                        |
| Arrays of pointers are legal     | No arrays of references                       |
| Pointers to pointers legal       | References or pointers to references not allowed |
| Pointers to `void` legal         | No references to `void`                       |
| May be uninitialized             | Must be initialized                           |
| Can be reassigned after initialization | Immutable                               |
| Can be cv-qualified              | Can't be cv-qualified                         |
