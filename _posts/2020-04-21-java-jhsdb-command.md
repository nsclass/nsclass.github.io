---
layout: single
title: Java - jhsdb command
date: 2020-04-21 15:00:00.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Java
permalink: "2020/04/21/jhsdb-command"
---

jhsdb is a tool which can attach a Java process or launch a postmortem debugger to analyze the content of a core dump from a crashed Java Virtual Machine (JVM).

Java 14
[https://docs.oracle.com/en/java/javase/14/docs/specs/man/jhsdb.html](https://docs.oracle.com/en/java/javase/14/docs/specs/man/jhsdb.html)

Java 9
[https://docs.oracle.com/javase/9/tools/jhsdb.htm#JSWOR-GUID-0345CAEB-71CE-4D71-97FE-AA53A4AB028E](https://docs.oracle.com/javase/9/tools/jhsdb.htm#JSWOR-GUID-0345CAEB-71CE-4D71-97FE-AA53A4AB028E)


Show java heap summary
```bash
$ jhsdb jmap --pid 25224 --heap
```

Result
```bash
Debugger attached successfully.
Server compiler detected.
JVM version is 11.0.5+10-LTS

using thread-local object allocation.
Garbage-First (G1) GC with 16 thread(s)

Heap Configuration:
   MinHeapFreeRatio         = 40
   MaxHeapFreeRatio         = 70
   MaxHeapSize              = 51539607552 (49152.0MB)
   NewSize                  = 1363144 (1.2999954223632812MB)
   MaxNewSize               = 30920409088 (29488.0MB)
   OldSize                  = 5452592 (5.1999969482421875MB)
   NewRatio                 = 2
   SurvivorRatio            = 8
   MetaspaceSize            = 21807104 (20.796875MB)
   CompressedClassSpaceSize = 1073741824 (1024.0MB)
   MaxMetaspaceSize         = 17592186044415 MB
   G1HeapRegionSize         = 16777216 (16.0MB)

Heap Usage:
G1 Heap:
   regions  = 3072
   capacity = 51539607552 (49152.0MB)
   used     = 8750376136 (8345.008979797363MB)
   free     = 42789231416 (40806.99102020264MB)
   16.97796423298617% used
G1 Young Generation:
Eden Space:
   regions  = 278
   capacity = 8489271296 (8096.0MB)
   used     = 4664066048 (4448.0MB)
   free     = 3825205248 (3648.0MB)
   54.940711462450594% used
Survivor Space:
   regions  = 2
   capacity = 33554432 (32.0MB)
   used     = 33554432 (32.0MB)
   free     = 0 (0.0MB)
   100.0% used
G1 Old Generation:
   regions  = 243
   capacity = 43016781824 (41024.0MB)
   used     = 4052755656 (3865.0089797973633MB)
   free     = 38964026168 (37158.99102020264MB)
   9.421336241705742% used
```