---
layout: single
title: Linearizability
date: 2020-12-24 20:30:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - Distributed Application
permalink: "2020/12/24/linearizability"
---
Linearizability

Execution history is linearizable if total order of operations which matches real for non concurrent operations and each read see the most recent write in order.

Basically, after writing a value then try to read it immediately, user should see the most recent write.
In terms of this definition, Cassandra is not a linearizable database because user might see the old written value when reading data immediately after a write.
With local quorum consistency level for read/write, Cassandra will minimize this issue but it cannot prevent completely.

Raft consensus algorithm solves this problem by logging commands in order with a single master for reading and writing.