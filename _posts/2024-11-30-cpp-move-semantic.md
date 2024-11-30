---
layout: single
title: C++ - virtual destructor disable move semantic
date: 2024-11-30 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2024/11/30/cpp-move-semantic"
---

### Declaring virtual destructor will disable move sematic

[Basic Move Semantic](https://www.youtube.com/watch?v=Bt3zcJZIalk)

```cpp
class Customer {
  protected:
    std::string name;
  public:
    virtual ~Customer() = default; // this will disable the move semantic
}
```
