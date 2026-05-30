---
layout: single
title: C++ - Transforming C asynchronous function to C++ future
date: 2017-02-10 03:29:21.000000000 -06:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- C++
- Programming
tags: []
meta:
  _edit_last: '14827209'
  geo_public: '0'
  _publicize_job_id: '1677863595'
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2017/02/10/c-transforming-c-asynchronous-function-to-c-future/"
---

C API definition to read data from a file in asynchronous way.\
{% highlight wl linenos %} void async_read_completed_callback(void\* pUserData, char cont\* pBuffer, int size); void async_read_data(char const\* pFilePath, void(\*callback)(void\* pUserData, char cont\* pBuffer, int size)); {% endhighlight %}

C++ implementation by using future\
{% highlight wl linenos %} void read_data_callback_wrapper(void\* pUserData, char const\* pBuffer, int size) { std::promise\> promiseVar = std::promise\> (reinterpret_cast\>\*\>(user_data)); std::vector data; for (int idx = 0; idx \< size; ++idx) { data.push_back(pBuffer\[idx\]); } promiseVar.set_value(data); } std::future\> read_data_in_cpp(char const\* pPath) { std::unique_ptr\>\> promiseVar = std::make_unique\>\>(); std::future\> futureRes = promiseVar-\>get_future(); async_read_data(pPath, reinterpret_cast(promiseVar.get()), read_data_callback_wrapper); promiseVar.release(); return futureRes; } {% endhighlight %}
