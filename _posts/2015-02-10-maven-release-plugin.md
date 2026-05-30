---
layout: single
title: Maven Release plugin
date: 2015-02-10 09:27:07.000000000 -06:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Java
- Programming
tags:
- maven
meta:
  _edit_last: '14827209'
  _publicize_pending: '1'
  geo_public: '0'
  _oembed_f75286f6a93e28b4f02c98005fbd8121: "{{unknown}}"
  _oembed_6cb1ab8b1fba00f87a3e8f047727721d: "{{unknown}}"
  _oembed_e1b6b1ce88ad7ce655dcde034b6a2867: "{{unknown}}"
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2015/02/10/maven-release-plugin/"
---

Useful commands\
{% highlight wl linenos %} 1. Prepare mvn release:prepare 2. Perform release mvn release:perform 3. Update develop version number mvn release:update-versions -DdevelopmentVersion={version} 4. Update version from released source. mvn versions:set -DnewVersion=1.0.CR-SNAPSHOT. 5. Batch release (non interactive) mvn -B release:prepare {% endhighlight %}

POM configuration

{% highlight wl linenos %} scm:svn:http://xxx/trunk ReleaseUniqueId UniqueReposityName file://///computer/directory/maven_release org.apache.maven.plugins maven-release-plugin 2.5.1 false see \#ticket true user pass http://xxx/tags {% endhighlight %}
