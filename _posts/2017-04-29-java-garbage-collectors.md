---
layout: single
title: Java - Garbage collectors
date: 2017-04-29 22:38:13.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Java
- Programming
tags: []
meta:
  _edit_last: '14827209'
  _oembed_d20bb17290966b91a5c2711863ee6005: "{{unknown}}"
  geo_public: '0'
  _publicize_job_id: '4520229577'
  _oembed_c70fbba4cd6333895fb5b65f80b68716: "{{unknown}}"
  _oembed_e8001316a4b5b99f349972c636ce6c32: "{{unknown}}"
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2017/04/29/java-garbage-collectors/"
---

1\. Serial\
-XX:+UseSerialGC JVM

2\. Parallel\
default

3\. CMS(Current Markup Sweep)\
-XX:+USeParNewGC

4\. G1\
–XX:+UseG1GC

Note: Java8 and G1 collector can optimize the string intern with the following option\
-XX:+UseStringDeduplicationJVM

More information regarding G1:\
https://www.infoq.com/articles/G1-One-Garbage-Collector-To-Rule-Them-All
