---
layout: single
title: C# WCF instance configuration
date: 2013-07-08 15:40:56.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- ".NET"
- Programming
tags: []
meta:
  _edit_last: '14827209'
  _publicize_pending: '1'
  tagazine-media: a:7:{s:7:"primary";s:0:"";s:6:"images";a:0:{}s:6:"videos";a:0:{}s:11:"image_count";i:0;s:6:"author";s:8:"14827209";s:7:"blog_id";s:8:"14365184";s:9:"mod_stamp";s:19:"2013-07-08
    05:56:39";}
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2013/07/08/c-wcf-instance-configuration/"
---

WCF has the confusing mechanism for management of instance on RPC call. The following separating shows an example of this situation. If you are more interested in this, you can find details from the book called Programming WCF Services 3rd edition.

1\. InstanceContextMode\
{% highlight wl linenos %} public enum InstanceContextMode { PerCall, PerSession, Single } \[ServiceBehavior(InstanceContextMode = InstanceContextMode.PerSession)\] class MyService : IMyContract {...} {% endhighlight %}

2\. SessionMode\
{% highlight wl linenos %} public enum SessionMode { Allowed, Required, NotAllowed } \[ServiceContract(SessionMode = SessionMode.Allowed)\] interface IMyContract {...} {% endhighlight %}

3\. Binding\
BasicHttpBinding cannot support Session mode. But NetTcpBinding and NetNamedPipeBinding can support this.

Therefor if you want to have PerCall InstanceContextMode, it is recommended that Session mode should be NotAllowed as shown the following example. Also you can use this strategy for PerSession InstanceContextMode with considering the WCF bindings.

{% highlight wl linenos %} \[ServiceContract(SessionMode = SessionMode.NotAllowed)\] interface IMyContract {...} \[ServiceBehavior(InstanceContextMode = InstanceContextMode.PerCall)\] class MyService : IMyContract {...} {% endhighlight %}

The following table summarize the combination of above cases.

|  |  |  |  |
|----|----|----|----|
| Binding | Session mode | Context mode | Instance mode |
| Basic | Allowed/NotAllowed | PerCall/PerSession | PerCall |
| TCP, IPC | Allowed/Required | PerCall | PerCall |
| TCP, IPC | Allowed/Required | PerSession | PerSession |
| WS (no Message security, no reliability) | NotAllowed/Allowed | PerCall/PerSession | PerCall |
| WS (no Message security, no reliability) | Allowed/Required | PerSession | PerSession |
| WS (no Message security, no reliability) | NotAllowed | PerCall/PerSession | PerCall |
