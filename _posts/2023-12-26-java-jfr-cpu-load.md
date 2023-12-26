---
layout: single
title: Java - Quick tip for checking CPU pressure with JFR
date: 2023-12-26 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - java
permalink: "2023/12/26/jfr-cpu-pressure"
---

A quick tip for checking CPU pressure with JFR in JDK21. It can support a JFR file recorded in JDK17.

```bash
jfr view thread thread-cpu-load [file]
```

[Youtube](https://www.youtube.com/watch?v=i0zWzIibr5Y)