---
layout: single
title: Java - Dropwizard http request accessing log customizing example
date: 2020-03-18 15:09:08.000000000 -05:00
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
  _publicize_job_id: '41944244961'
  timeline_notification: '1584562149'
author:
  login: acrocontext
  email: nsclass@hotmail.com
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2020/03/18/java-dropwizard-http-request-accessing-log-customizing-example/"
---
<p>Dropwizard can allow to access the attributes in a request as shown in below example.<br />
Full layout logback format details can be found from <a href="http://logback.qos.ch/manual/layouts.html">http://logback.qos.ch/manual/layouts.html</a></p>
{% highlight wl linenos %}
server:
  rootPath: /test/services/rest
  requestLog:
    appenders:
    - type: file
      currentLogFilename: ./logs/requests.log
      archivedLogFilenamePattern: ./logs/requests-%d.log
      archivedFileCount: 5
      timeZone: UTC
      logFormat: "%h %l %u [%t{dd/MMM/yyyy:HH:mm:ss Z,UTC}] %reqAttribute{attributeName} \"%r\" %s %b \"%i{Referer\"%ier-Agent}\"
{% endhighlight %}
