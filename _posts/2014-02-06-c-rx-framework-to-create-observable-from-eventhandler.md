---
layout: single
title: C# - Rx framework to create Observable from EventHandler
date: 2014-02-06 11:39:06.000000000 -06:00
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
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2014/02/06/c-rx-framework-to-create-observable-from-eventhandler/"
---

The following code shows how to create IObserable object from EventHandler delegator.

{% highlight wl linenos %} public CustomEventArg : EventArg { public int Value { get; set; } } public class CustomOtherClass { public event EventHandler OnCustEvent; } public class Test { private IObservable m_obEvent; private CustomOtherClass m_other = new CustomOtherClass(); public IObservable ObserverCustomEvent { get { return m_obEvent; } } Test() { m_obEvent = Obserable.FromEvent, CustomEventArg\>(h =\> { EventHandler handler = (sender, e) =\> { h(e); } return handler; }, f =\> m_other.OnCustomEvent += f, f =\> m_other.OnCustomEvent -= f); } } {% endhighlight %}
