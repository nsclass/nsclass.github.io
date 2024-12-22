---
layout: single
title: C++ - unique_ptr for custom resource
date: 2024-12-22 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2024/12/22/cpp-unique_ptr-custom-resource"
---

Using unique_ptr for a custom resource such as opening a file.

```cpp
auto fp = unique_ptr<FILE, decltype(&fclose)>{fopen("sample.txt", r), &fclose};
```
