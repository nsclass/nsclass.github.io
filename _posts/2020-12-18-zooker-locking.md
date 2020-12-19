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

The following pseudo logic shows how ZooKeeper is supporting a lock.
```
void acquire_lock() {
  while (true) {
    if create('f', ephem=true) {
      return;
    }

    if exist('f', watch=true) {
      wait until file f has gone
    }
  }
}
```

Another way to lock with sequential file type in ZooKeeper.
```
void acquire_lock() {
  create seq('f')
  while (true) {
    list 'f*'
    if no lower #file
      return;
    
    if exists(lower file, watch=true) {
      wait
    }
  }
}
```