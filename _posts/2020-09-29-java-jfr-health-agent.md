---
layout: single
title: Java - JFR start/dump and health reporting agent
date: 2020-09-29 09:30:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - java
permalink: "2020/09/29/java-jfr-health-reporting"
---

From JDK 11, the following command will start recording JFR
```bash
$ jcmd [pid] JFR.start duration=60s filename=myrecording.jfr
```

Dump recording
```bash
$ jcmd JFR.dump
```

Details can be found from below.
[https://docs.oracle.com/javacomponents/jmc-5-4/jfr-runtime-guide/run.htm#JFRUH177](https://docs.oracle.com/javacomponents/jmc-5-4/jfr-runtime-guide/run.htm#JFRUH177)

There is a nice agent which can report the health of Java application at realtime but it requires Java 14.

[https://github.com/flight-recorder/health-report](https://github.com/flight-recorder/health-report)
