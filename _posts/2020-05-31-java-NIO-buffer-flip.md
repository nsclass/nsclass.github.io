---
layout: single
title: Java NIO flip buffer
date: 2020-05-31 09:30:00.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Java
permalink: "2020/05/31/java-nio-flip-buffer"
---

The flip function in Buffer is equivalent to the following operation.

```java
buffer.limit(buffer.position()).position(0);
```
