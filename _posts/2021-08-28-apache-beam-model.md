---
layout: single
title: Apache Beam Model
date: 2021-08-28 09:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - apache beam
permalink: "2021/08/28/apache-beam-model"
---

What: sum, average or machine learning? used to be done with classic batch processing.
Where: windowing with event time such as fixed, sliding or session.
When: triggering with a water mark for input completeness but it can trigger multiple times based on each use case.
How: accumulation mode, discarding or accumulating previous window.
