---
layout: single
title: Java - Recommended GC log options for Java 8 and Java 9
date: 2017-04-29 23:40:18.000000000 -05:00
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
  _oembed_ae5d6e8feb299491130260c9f4387c4b: "{{unknown}}"
  geo_public: '0'
  _publicize_job_id: '4521726365'
  _oembed_df142747436b8c8bf400fd0042855762: "{{unknown}}"
  _oembed_0faf22bcdc07391582e7fba299e493d5: "{{unknown}}"
  _oembed_1f371303067909e4e1f61ffdc0911414: "{{unknown}}"
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2017/04/29/java-recommended-gc-log-options-for-java-8-and-java-9/"
---

Java 8\
-XX:+PrintGCDetails\
-XX:+PrintReferenceGC\
-XX:+PrintTenuringDistribution\
-Xloggc:\
-XX:+PrintGCTimeStamps

Java 9\
-Xlog:gc\*\
,gc+ref=debug\
,gc+age=trace\
:file=\
:tags,uptime

Video:\
https://www.infoq.com/presentations/java-9-gc?utm_source=presentations_about_GarbageCollection&utm_medium=link&utm_campaign=GarbageCollection
