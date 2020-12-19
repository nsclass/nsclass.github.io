---
layout: single
title: ZooKeeper - Lock Support
date: 2020-12-18 19:30:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - ZooKeeper
permalink: "2020/12/18/zookeeper-lock-support"
---

The following example shows how ZooKeeper is supporting a lock.

```
while (true) {
  if create('f', ephem=true) {
    return;
  }

  if exist('f', watch=true) {
    wait until file f has gone
  }
}
```
