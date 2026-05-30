---
layout: single
title: C++ - Simple thread example of a string message processor
date: 2016-03-22 08:43:03.000000000 -05:00
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
  _publicize_job_id: '20991275935'
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2016/03/22/c-simple-thread-example-of-a-string-message-processor/"
---

{% highlight wl linenos %} class StringMessageProcessor { public: StringMessageProcessor() { m_exit = false; m_messageArrived = false; } ~StringMessageProcessor() { m_thread.join(); } void SetHandler(std::function msgHandler) { std::unique_lock lock(m_condvarMutex); m_msgHandler = msgHandler; } void Start() { boost::thread thread(\[this\] { while (!m_exit) { std::unique_lock lock(m_condvarMutex); m_condvar.wait(lock, \[this\] { return m_exit \|\| m_messageArrived;}); if (!m_exit) { std::vector data; auto queueSize = m_msgQueue.size(); while (m_msgQueue.size() \> 0) { data.push_back(m_msgQueue.front()); m_msgQueue.pop(); } lock.unlock(); for (auto const& msg: data) { m_processor-\>processItem(msg, queueSize); } } } }); m_thread.swap(thread); } void Stop() { { std::lock_guard lk(m_condvarMutex); m_exit = true; } m_condvar.notify_all(); } bool PushMessage(std::string const& msg) { std::lock_guard lk(m_condvarMutex); m_msgQueue.push(msg); m_messageArrived = true; m_condvar.notify_one(); return true; } private: boost::thread m_thread; std::mutex m_condvarMutex; std::condition_variable m_condvar; bool m_exit; bool m_messageArrived; std::queue m_msgQueue; std::function m_msgHandler; }; {% endhighlight %}
