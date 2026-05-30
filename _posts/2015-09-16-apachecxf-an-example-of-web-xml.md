---
layout: single
title: ApacheCXF - an example of web.xml
date: 2015-09-16 07:51:12.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Programming
- Web
tags:
- Apache CXF
meta:
  _edit_last: '14827209'
  geo_public: '0'
  _publicize_job_id: '14822321870'
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2015/09/16/apachecxf-an-example-of-web-xml/"
---

{% highlight wl linenos %}

contextConfigLocation classpath:config/applicationContext.xml Application Name index.jsp CXFServlet org.apache.cxf.transport.servlet.CXFServlet CXFServlet /services/\* org.springframework.web.context.ContextLoaderListener {% endhighlight %}
