---
layout: single
title: Pessimistic Distributed Transaction
date: 2021-04-12 17:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - distributed
permalink: "2021/04/12/distributed-transaction"
---
Pessimistic distributed transaction will use the following concepts to achieve ACID(Atomic, Consistency, Isolation, Durable).

1. Two phase locking
2. Two phase commits

## Two phase locking
- Lock object before using it
- Hold the lock until it finished the transaction

## Two phase commits
- Prepare commit will log all required modification and changes in write ahead logs.
- Perform commit will apply all changes to the database.
