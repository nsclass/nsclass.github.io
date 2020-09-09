---
layout: single
title: Lamport clock
date: 2020-09-09 07:30:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - rust
permalink: "2020/09/09/lamport-clock"
---

In distributed system, clock can be skewed so if system is relying on wall clock or local clock, it will face unexpected results such as overwriting an existing value from a wrong system.

Lamport clock will solve this problem.

```
Tmax = hightest version which have seen.

Final version = max(Tmax + 1, realtime clock)
```
