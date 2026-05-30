---
layout: single
title: Windows 7 memory profiling example
date: 2012-07-31 08:06:24.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Programming
- Windows
tags: []
meta:
  _edit_last: '14827209'
  tagazine-media: a:7:{s:7:"primary";s:0:"";s:6:"images";a:0:{}s:6:"videos";a:0:{}s:11:"image_count";i:0;s:6:"author";s:8:"14827209";s:7:"blog_id";s:8:"14365184";s:9:"mod_stamp";s:19:"2012-08-05
    22:51:02";}
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2012/07/31/windows-7-memory-profiling-example/"
---

\
@echo off\
set \_NT_SYMBOL_PATH=F:\src\Release\\srv\*c:\WebSymbol\*http://msdl.microsoft.com/downloads/symbols

xperf -on base\
xperf -start heapsession -heap -pids %1 -stackwalk HeapAlloc+HeapRealloc -BufferSize 512 -MinBuffers 128 -MaxBuffers 512

echo.\
echo Performance Trace started.\
echo.\
echo When done with profile actions,

pause

xperf -stop heapsession -d heap.etl\
xperf -d main.etl\
xperf -merge main.etl heap.etl result.etl

echo.\
start xperfview result.etl\

usage: script.cmd \[pid\]
