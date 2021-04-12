---
layout: single
title: Distributed caches common issues and solution idea
date: 2021-04-11 17:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - zookeeper
permalink: "2021/04/11/distributed-cache-issues-solution"
---
In order to build distributed caches, we need to solve the following three problems.

1. Cache coherence
2. Atomicity
3. Crash recovery

## Cache coherence
- This can be solved by introducing a lock server.

## Atomicity
- Distributed transaction will solve this problem by using a lock server.

## Crash recovery
- Write Ahead Log mechanism will provide a solution for crash recovery.
- Every operation should have version information to prevent unexpected recovery result such as restoring already removed items.
