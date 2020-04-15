---
layout: single
title: Sublime - matching multiple lines with regex
date: 2020-03-27 12:45:22.000000000 -05:00
parent_id: '0'
published: true
password: ''
status: publish
categories: []
tags: []
meta:
  _edit_last: '14827209'
  geo_public: '0'
  _publicize_job_id: '42298852630'
  timeline_notification: '1585331123'
author:
  login: acrocontext
  email: nsclass@hotmail.com
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2020/03/27/sublime-matching-multiple-lines-with-regex/"
---
<p>Start with (?s)<br />
{% highlight wl linenos %}
(?s)\[sometag\](.*?)\[\/sometag\]
{% endhighlight %}

