---
layout: single
title: Java - Difference between Set and Set<?>
date: 2021-04-06 07:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - java
permalink: "2021/04/06/java-difference-set-vs-wildcard-set"
---
What is difference between `Set` and `Set<?>`

Main benefit of using wildcard `Set<?>` is that it can guarantee the safety of collection. It will preserve invariant of wildcard collection but raw type collection will allow to add different types in collection. However `Set<?>` also allows to add `null` value.

`Set<?>` is preventing from corrupting collection's type invariant.