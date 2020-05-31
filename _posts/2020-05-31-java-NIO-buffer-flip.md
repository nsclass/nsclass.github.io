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

The flip function in Buffer is equivalent to the following operation which means that it will set limit with current position and set current position to zero.

```java
buffer.limit(buffer.position()).position(0);
```

The rewind function will set the current position to zero but it does not change the limit value.
So rewind can be used to reread the data from the beginning.

