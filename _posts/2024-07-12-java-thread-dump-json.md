---
layout: single
title: Java - thread dump in JSOn format
date: 2024-07-12 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - java
permalink: "2024/07/12/java-thread-dump"
---

Java thread dump with JSON

```bash
jcmd <pid> Thread.dump_to_file -format json <filename>
```
