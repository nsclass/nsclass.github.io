---
layout: single
title: Java 8 - general practice using Optional
date: 2017-07-02 23:56:57.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Java
- Programming
tags:
- optional
meta:
  _edit_last: '14827209'
  geo_public: '0'
  _publicize_job_id: '6696349631'
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2017/07/02/java-8-general-practice-using-optional/"
---

0\. Never, ever use null for an Optional variable.\
1. Optional should be only used as a return value.\
: never use it for a field in Class and a method parameter.\
never use it in collections

2\. Never try to call .get() method on an Optional.\
: if it is a situation to get a value, ifPresent, map and orElse() family can solve this problem .

3\. Remember Optional is not Serializable.

Note)\
Java 9 will introduce the following new method\
```
Optional.stream()
Optional.ifPresentOrElse()
Optional.or()
```
