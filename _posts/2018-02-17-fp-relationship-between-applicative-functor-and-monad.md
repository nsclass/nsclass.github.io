---
layout: single
title: FP - Relationship between Applicative Functor and Monad
date: 2018-02-17 14:52:42.000000000 -06:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Functional Programming
- Programming
tags: []
meta:
  _edit_last: '14827209'
  geo_public: '0'
  _publicize_job_id: '14851395994'
  timeline_notification: '1518900763'
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2018/02/17/fp-relationship-between-applicative-functor-and-monad/"
---

Applicative Functor has the following two properties.

Pure: create a functor from value.\
Apply: a function taking arguments which are a Functor having a function and a Pure. This function will return the Functor after applying the function inside the first Functor with a value from a Pure by unwrapping.

Example)\
{% highlight wl linenos %} Optional apply(Optional\> f, Optional v) { if (f & v) { return Optional(\*f (\*v)); } return Optional(nullptr); } {% endhighlight %}

Java example)\
{% highlight wl linenos %} Optional apply(Optional\> f, Optional v) { return f.flatMap(a -\> v.map(a(v)) } {% endhighlight %}

Monad is the Applicative Functor with joining to flat the returning Functor.\
So Monad is Applicative Functor with a join.\
Join: flattening the Functor

Join Example)\
{% highlight wl linenos %} Optional join(Optional\> v) { if (v) { return \*v; } return Optional(nullptr); } {% endhighlight %}

Monad C++ definition:\
{% highlight wl linenos %} template Monad <u>bind(Monad m, std::function(T)\> f) { return join(apply(pure(f), m)); } {% endhighlight %}</u>
