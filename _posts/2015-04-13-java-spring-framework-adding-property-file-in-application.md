---
layout: single
title: Java - Spring framework - adding property file in application
date: 2015-04-13 10:01:12.000000000 -05:00
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
  _publicize_pending: '1'
  geo_public: '0'
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2015/04/13/java-spring-framework-adding-property-file-in-application/"
---

1\. Add the following code in applicationContext-config.xml

{% highlight wl linenos %} classpath\*:my.properties {% endhighlight %}

2\. get an instance of myPropertes in code

{% highlight wl linenos %} java.util.Properties properties = (java.util.Properties)ApplicationContextProvider.getApplicationContext().getBean("myProperties") {% endhighlight %}
