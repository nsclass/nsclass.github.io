---
layout: single
title: Java - Guidance of using wildcard in generic
date: 2017-10-27 19:54:07.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Java
- Programming
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2017/10/27/java-guidance-of-using-wildcard-in-generic/"
---
# Do not use bounded wildcard as a return value
This will force client to use wildcard types

# PECS(Produce Extends Consumer Super)
```java
public void pushAll(Collection<? extends E> src) {
  for (E e : src) {
    push(e)
  }
}
```

```java
public void popAll(Collections<? super E> dst) {
  while (!isEmpty()) {
    dst.add(pop())
  }
}
```

# The basic guidance of using wildcard in Java generic
https://docs.oracle.com/javase/tutorial/java/generics/wildcardGuidelines.html
