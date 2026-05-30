---
layout: single
title: WinDbg example for debugging reference count of COM object
date: 2010-07-19 22:22:49.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Programming
tags: []
meta:
  _edit_last: '14827209'
  _wp_old_slug: ''
  tagazine-media: a:7:{s:7:"primary";s:0:"";s:6:"images";a:0:{}s:6:"videos";a:0:{}s:11:"image_count";s:1:"0";s:6:"author";s:8:"14827209";s:7:"blog_id";s:8:"14365184";s:9:"mod_stamp";s:19:"2010-07-19
    22:22:49";}
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2010/07/19/windbg-example-for-debugging-reference-count-of-com-object/"
---

One of the hardest things is debugging a reference count leak. COM objects lifetime depends on the reference count (read here for more...). So each client of a COM object must call AddRef on the IUnknown interface when going to use it and it must call Release when done. If any client (and there might be many many of a single one) violates this rule you get into severe trouble.

Scenarios\
1.) Number of Release calls = Number of AddRef calls\
This is the normal scenario: As soon as no client needs the server object anymore it is getting destroyed

2.) Number of Release calls \> Number of AddRef calls\
If Release is called one time too often another client might crash because the server get's destroyed too early - bad thing here is that you see the crash in some place but this does not tell you where is root cause is located. All you know is which objects reference count has been corrupted.

3.) Number of AddRef calls \> Number of Release calls\
If AddRef is called one time too often the reference count never reaches 0 and hence the server object never get's destroyed. This is causing memory leaks and also might cause resource leaks. The effect of this scenario is much less obvious: You might see memory increasing over time and/or performance degrade and/or resources to be locked when they should be unlocked again.

Finding the place where the unbalanced AddRef/Release occurred might be like finding the needle in the hay. I did research in the Google reachable web but didn't find a good tool available that really assist's in this task. Luckily Sara Ford described in this post the first step you need to take in order to get the data necessary to drill down into the problem.

Somehow I didn't manage to set the trace points in Visual Studio 2005 (can anybody tell me how to set a break point on a single objects AddRef, Release methods?) so I launched my beloved WinDbg.

First I created script to create me an xml snippet for an event that alters the ref count (I didn't find a better name so I called it ToXml.txt and placed it into my scripts folder):

.printf "--\>\n%d\n\<!--\n"

Then I placed a break point on the server objects constructor

bp MyServer!CMyClass::CMyClass

When the breakpoint hit, I stepped out + into CComCreator::CreateInstance and then stepped over the p-\>SetVoid(pv); call in this class.\
(I think it should be possible to set a breakpoint directly at MyServer!ATL::CComCreator\<ATL::CComObject \>::CreateInstance+0xb1, but I didn't try...)

Now I gathered the address of m_dwRef by:

0:000\> ?? &(p-\>m_dwRef)\
long \* 0x110d724c

Next thing to do is setting the data breakpoint by:

ba w4 0x110d724c "\$\$\>a\<C:/windbg/scripts/ToXml.txt 0f084cb4;gc"

(you might need to change the path 'C:/windbg/scripts/')

With .logopen we make sure that we directly write all events into an logfile:

.logopen c:\temp\Events.xml

Now let the application run with 'g' or and do whatever creates your ref counting problem.

When done break into and close the log with .logclose.

At this point we are half the way through. The Events.xml we created is not valid xml. You need to add

at the end.
