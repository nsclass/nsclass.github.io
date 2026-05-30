---
layout: single
title: Tomcat - logging all HTTP traffic with Logback
date: 2014-11-05 09:31:44.000000000 -06:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories: []
tags: []
meta:
  _edit_last: '14827209'
  _publicize_pending: '1'
  geo_public: '0'
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2014/11/05/tomcat-logging-all-http-traffic-with-logback/"
---

1\. Install logback in a tomcat\lib folder\
logback-access-1.1.2.jar\
logback-core-1.1.2.jar

2\. Create a logback-access.xml in a tomcat\conf foler\
Example)\
{% highlight wl linenos %} c:/logs/logback.log cg-logback.%d{yyyy-MM-dd}.log.zip %fullRequest%n%n%fullResponse {% endhighlight %}

3\. Modify server.xml in a tomcat/conf folder\
Example)\
{% highlight wl linenos %} {% endhighlight %}

4\. Modify web.xml to register filer\
Example)\
{% highlight wl linenos %} TeeFilter ch.qos.logback.access.servlet.TeeFilter TeeFilter /\* {% endhighlight %}
