---
layout: single
title: Linux - useful commands to inspect performance utilization
date: 2017-05-08 07:52:01.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Linux
- Programming
tags: []
meta:
  _edit_last: '14827209'
  geo_public: '0'
  _publicize_job_id: '4803401739'
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2017/05/08/linux-useful-commands-to-inspect-performance-utilization/"
---

Memory utilization\
{% highlight wl linenos %} vmstat 1 \[/cpde\] Disk utilization \[code lang="C"\] iostat -xm 5 {% endhighlight %}

Network utilization tool\
{% highlight wl linenos %} nicstat {% endhighlight %}

Network connection status\
{% highlight wl linenos %} netstat {% endhighlight %}

Note, Windows has the following equivalent command for above purpose\
{% highlight wl linenos %} typeperf {% endhighlight %}
