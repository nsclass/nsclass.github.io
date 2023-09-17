---
layout: single
title: SpringBoot - @SpringBootTest annotation
date: 2023-09-17 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - spring
permalink: "2023/09/17/spring-boot-test-annotation"
---

`@SpringBootTest` annotation will search entire beans which @SpringBootApplication defines in ApplicationContext so it requires to have all dependent component up and running such as database etc. So this annotation will be the best for integration tests.

`@SpringBootTest` will use the mock servlet for testing Web components. If we want to launch a real HTTP serer such as Tomcat, we have to provide the following parameter.

```java
@SpringBootTest(webEnvironment = WebEnvironment.RANDOM_PORT)
```

