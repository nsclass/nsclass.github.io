---
layout: single
title: Flame Graph - Cassandra and Java applications 
date: 2020-04-19 09:00:00.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Java
permalink: "2020/04/19/flame-graph-java-applications"
---

The following article show how to generate the flame graph for Cassandra performance but it is using a generic tools to generate flame graph any Java application.

Simple command to generate a flamegraph with an async profiler
```bash
./profiler.sh -d <duration> -f flamegraph.svg -s -o svg <pid> && \
open flamegraph.svg  -a "Google Chrome"
```

[https://thelastpickle.com/blog/2018/01/16/cassandra-flame-graphs.html](https://thelastpickle.com/blog/2018/01/16/cassandra-flame-graphs.html)

More flame graph related links
[http://www.brendangregg.com/flamegraphs.html](http://www.brendangregg.com/flamegraphs.html)

Flame graph for Java applications
[https://medium.com/97-things/firing-on-all-engines-f33e340c3374](https://medium.com/97-things/firing-on-all-engines-f33e340c3374)

Intellij support the flame graph with JFR and Yourkit
[https://plugins.jetbrains.com/plugin/10305-flameviewer](https://plugins.jetbrains.com/plugin/10305-flameviewer)

Async profiler
[https://github.com/jvm-profiling-tools/async-profiler](https://github.com/jvm-profiling-tools/async-profiler)

