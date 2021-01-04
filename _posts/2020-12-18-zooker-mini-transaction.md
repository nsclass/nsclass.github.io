---
layout: single
title: ZooKeeper - Mini Transaction Support
date: 2020-12-18 19:30:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - ZooKeeper
permalink: "2020/12/18/zookeeper-mini-transaction"
---

ZooKeeper mini transaction logic

The following pseudo code shows how to increase value x with version number information.

```
while (true) {
  x, v = getData('f')
  if setData('f', x + 1, v)
    break
}
```
