---
layout: single
title: Java - Task polling example with Java 8
date: 2017-06-14 22:49:09.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Java
- Programming
tags:
- java
meta:
  _edit_last: '14827209'
  geo_public: '0'
  _publicize_job_id: '6100230031'
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2017/06/14/java-task-polling-example-with-java-8/"
---

```java
public void completionService(ExecutorService executor) {
    CompletionService<CustomTaskResult> completionService =
        new ExecutorCompletionService<CustomTaskResult>(executor);
    completionService.submit(() => {
        // to something
    });
    Future<CustomTaskResult> future = null
    while ((future = completionService.poll()) != null) {
    	// do something
    }
}
```
