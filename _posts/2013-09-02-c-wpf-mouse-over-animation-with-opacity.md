---
layout: single
title: C# WPF - mouse over animation with opacity
date: 2013-09-02 15:42:04.000000000 -05:00
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
  tagazine-media: a:7:{s:7:"primary";s:0:"";s:6:"images";a:0:{}s:6:"videos";a:0:{}s:11:"image_count";i:0;s:6:"author";s:8:"14827209";s:7:"blog_id";s:8:"14365184";s:9:"mod_stamp";s:19:"2013-09-02
    05:42:04";}
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2013/09/02/c-wpf-mouse-over-animation-with-opacity/"
---

Resource XML.\
{% highlight wl linenos %} <style x:key="FadeOutButton" targettype="{x:Type Button}">
            <setter property="Template">
                <setter.value>
                    <controltemplate targettype="Button">
                        <border background="Transparent">
                            <contentpresenter></contentpresenter>
                        </border>
                    </controltemplate>
                </setter.value>
            </setter>
            <style.triggers>
                <eventtrigger routedevent="Control.MouseEnter">
                    <beginstoryboard>
                        <storyboard>
                            <doubleanimation duration="0:0:0.2" to="1" storyboard.targetproperty="Opacity"></doubleanimation>
                        </storyboard>
                    </beginstoryboard>
                </eventtrigger>
                <eventtrigger routedevent="Control.MouseLeave">
                    <beginstoryboard>
                        <storyboard>
                            <doubleanimation duration="0:0:0.2" to="0.4" storyboard.targetproperty="Opacity"></doubleanimation>
                        </storyboard>
                    </beginstoryboard>
                </eventtrigger>
            </style.triggers>
        </style> {% endhighlight %}

Button XML.\
{% highlight wl linenos %} {% endhighlight %}
