---
layout: single
title: Java - Java application monitoring tools
date: 2017-05-08 08:07:04.000000000 -05:00
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
  geo_public: '0'
  _publicize_job_id: '4803723971'
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2017/05/08/java-java-application-monitoring-tools/"
---

jcmd: Prints basic class, thread, and VM information for a Java process\
Example)\
```
% jcmd <process_id> VM.uptime
% jcmd <process_id> VM.system_properties
% jcmd <process_id> VM.version
% jcmd <process_id> VM.command_line
% jcmd <process_id> VM.flags [-all]
% jcmd <process_id> Thread.print
% jcmd <process_id> GC.run // force to run full GC
% jcmd <process_id> GC.heap_dump /path/to/heap_dump.hprof // heap dump
```

jconsole: Provides a graphical view of JVM activities, including thread usage, class usage, and GC activities\
jhat: Reads and helps analyze memory heap dumps. This is a postprocessing utility\
jmap: Provides heap dumps and other information about JVM memory usage\
jinfo: Provides visibility into the system properties of the JVM, and allows some system properties to be set dynamically\
```
% jinfo -flags <process_id>
% jinfo -flag PrintGCDetails <process_id>
```

jstack: Dumps the stacks of a Java process

jstat: Provides information about GC and class-loading activities\
```
% jstat -compiler <process_id>
% jstat -printcompilation <process_id> <duration(ms)>
```

jvisualvm: A GUI tool to monitor a JVM, profile a running application, and analyze JVM heap dumps

jmap:\
```
% jmap -clstats : print out information about class loaders(Java 8)
% jmap -permstat : print out information about class loaders(Java 7)
% jmap -dump:live,file=/path/to/heap_dump.hprof <process_id> // heap dump
```
