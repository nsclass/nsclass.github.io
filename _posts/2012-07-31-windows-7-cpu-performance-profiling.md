---
layout: single
title: Windows 7 CPU performance profiling example
date: 2012-07-31 08:04:47.000000000 -05:00
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
    22:50:38";}
  _oembed_87bb364505f35730efbce57346c67cea: "{{unknown}}"
  _oembed_c791d0029b6ce17971d707fed048353f: "{{unknown}}"
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2012/07/31/windows-7-cpu-performance-profiling/"
---

\
@echo off\
set \_NT_SYMBOL_PATH=f:\src\Debug\\srv\*c:\WebSymbol\*http://msdl.microsoft.com/downloads/symbols

xperf -on Latency -stackwalk profile

echo.\
echo Performance Trace started.\
echo.\
echo When done with profile actions,

pause

echo.\
xperf -d Trace.etl

echo.\
start xperfview Trace.etl\

On windows 64 bits, the following registry should be added to record the call stack.

\
`REG ADD "HKLM\System\CurrentControlSet\Control\Session Manager\Memory Management" -v DisablePagingExecutive -d 0x1 -t REG_DWORD -f`\
