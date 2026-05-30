---
layout: single
title: C++ - A nice example measuring funtion execution time with C++11
date: 2015-09-18 07:56:00.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- C++
- Programming
tags:
- C++11
meta:
  _edit_last: '14827209'
  geo_public: '0'
  _publicize_job_id: '14895711581'
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2015/09/18/c-a-nice-example-measuring-funtion-execution-time-with-c11/"
---

{% highlight wl linenos %} \#include \#include template struct measure { template static typename TimeT::rep execution(F&& func, Args&&... args) { auto start = std::chrono::system_clock::now(); std::forward(func)(std::forward(args)...); auto duration = std::chrono::duration_cast\< TimeT\> (std::chrono::system_clock::now() - start); return duration.count(); } }; int main() { std::cout \<\< measure\<\>::execution(functor(dummy)) \<\< std::endl; } {% endhighlight %}
