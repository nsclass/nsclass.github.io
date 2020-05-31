---
layout: single
title: Java NIO flip/compact functions in Buffer class
date: 2020-05-31 09:30:00.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Java
permalink: "2020/05/31/java-nio-flip-compact-buffer"
---

# flip function
The flip function in Buffer is equivalent to the following operation which means that it will set limit with current position and set current position to zero.

```java
buffer.limit(buffer.position()).position(0);
```

The rewind function will set the current position to zero but it does not change the limit value.
So rewind can be used to reread the data from the beginning.

If the flip is called twice, it will make the size zero. The current position will be zero and limit will be zero too.

# compact function

The compact function will be used to resume the filling from the draining mode.

```java
ByteBuffer buffer = ByteBuffer.allocate(10);

// filling
for (int idx = 0; idx <= 5; ++idx) {
  buffer.put((byte)idx);
}

buffer.flip();

// drain start
for (int idx = 0; idx <= 3; ++idx) {
  buffer.get();
}

// resume filling
buffer.compact(); // position will be 3, limit will be 10 again

// buffer contents will be as following.
// NOP means a not initialized value.
// position: 3
// limit: 10
// capacity: 10
// 04, 05, 02, 03, 04, 05,NOP,NOP,NOP,NOP,
```
