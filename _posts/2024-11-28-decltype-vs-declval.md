---
layout: single
title: C++ - decltype vs declval
date: 2024-11-28 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - web
permalink: "2024/11/28/decltype-vs-declval"
---

### Comparing decltype vs declval in C++

|Feature|std::decltype|std::declval
|-------|-------------|-------------
|Purpose|Deduces the type of an expression.|Simulates an instance of a type.
|Operation|Works on actual expressions.|Works purely on type information.
|Evaluation|Does not evaluate the expression.|Does not create any object; pure utility.
|Common Use|Type deduction of expressions.|Type deduction for inaccessible instances.
|Header|Built into the language.|<utility>
