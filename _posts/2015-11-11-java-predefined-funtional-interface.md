---
layout: single
title: Java - Predefined funtional interface
date: 2015-11-11 10:36:26.000000000 -06:00
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
  _publicize_job_id: '16734344768'
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2015/11/11/java-predefined-funtional-interface/"
---

1\. Void return and zero paramter\
Use Runnable

{% highlight wl linenos %} void runTask(Runnable task) { task.run(); } runTask(()-\> { // do something }); {% endhighlight %}

2\. Return value and zero paramter\
Use Supply

{% highlight wl linenos %} public T runTask(Supply task) { return task.get(); } Integer res = runTask(()-\> { Integer value; // do something return value; }); {% endhighlight %}

3\. Return void and 1 parameter\
Use Consumer

{% highlight wl linenos %} public void runTask(Consumer task, T value) { return task.accept(value); } Integer value; runTask((Integer x)-\> { // do something }, value); {% endhighlight %}

4\. Generic case\
Use Action0, Action1, Action2 ...
