---
layout: single
title: Zookeeper - znode types
date: 2021-04-08 07:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - zookeeper
permalink: "2021/04/08/zookeeper-znode-types"
---
Zookeeper has a znode to describe the hierarchical accessing data such as `kafka/node001`

znode has the following types.

```
regular
ephemeral
sequential
```
ephemeral znode will be removed automatically if zookeeper cannot reach the client. Client can create a znode as regular or sequential with ephemeral true of false.