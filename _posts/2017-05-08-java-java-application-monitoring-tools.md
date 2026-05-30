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
{% highlight wl linenos %} % jcmd VM.uptime % jcmd VM.system_properties % jcmd VM.version % jcmd VM.command_line % jcmd VM.flags \[-all\] % jcmd Thread.print % jcmd GC.run // force to run full GC % jcmd GC.heap_dump /path/to/heap_dump.hprof // heap dump {% endhighlight %}

jconsole: Provides a graphical view of JVM activities, including thread usage, class usage, and GC activities\
jhat: Reads and helps analyze memory heap dumps. This is a postprocessing utility\
jmap: Provides heap dumps and other information about JVM memory usage\
jinfo: Provides visibility into the system properties of the JVM, and allows some system properties to be set dynamically\
{% highlight wl linenos %} % jinfo -flags % jinfo -flag PrintGCDetails {% endhighlight %}

jstack: Dumps the stacks of a Java process

jstat: Provides information about GC and class-loading activities\
{% highlight wl linenos %} % jstat -compiler % jstat -printcompilation {% endhighlight %}

jvisualvm: A GUI tool to monitor a JVM, profile a running application, and analyze JVM heap dumps

jmap:\
{% highlight wl linenos %} % jmap -clstats : print out information about class loaders(Java 8) % jmap -permstat : print out information about class loaders(Java 7) % jmap -dump:live,file=/path/to/heap_dump.hprof // heap dump {% endhighlight %}
