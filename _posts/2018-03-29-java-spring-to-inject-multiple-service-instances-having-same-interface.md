---
layout: single
title: Java - Spring to inject multiple service instances having same interface
date: 2018-03-29 09:08:02.000000000 -05:00
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
  _publicize_job_id: '16252011298'
  timeline_notification: '1522332483'
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2018/03/29/java-spring-to-inject-multiple-service-instances-having-same-interface/"
---

Create service for multiple name providers\
{% highlight wl linenos %} interface NameProvider { String name(); } @Service public class SomeName implement NameProvider { public String name() { return "SomeName"; } } @Service public class AnotherName implement NameProvider { public String name() { return "AnotherName"; } } {% endhighlight %}

NameService class can inject multiple NameProviders with the following constructor injection.\
{% highlight wl linenos %} @Service public class NameService { private List nameProviders; NameService(List nameProviders) { this.nameProviders = nameProviders; } } {% endhighlight %}
