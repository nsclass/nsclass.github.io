---
layout: single
title: Java - Structured Concurrency in JDK 21
date: 2023-07-13 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - java
permalink: "2023/07/13/java-structured concurrency"
---

As a part of loom project, JDK21 will support the structured concurrency to handle multiple concurrent tasks in a structured way.

```java
Response handle() throws ExecutionException, InterruptedException {
  try (var scope = StructuredTaskScope.ShutdownOnFailure()) {
    Future<String> user = scope.fork(() -> findUser());
    Future<String> fetchOrder = scope.fork(() -> fetchOrder());

    scope.join();
    scope.throwIfFailed()

    return Response(user.resultNow(), fetchOrder.resultNow());
  }
}
```