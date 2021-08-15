---
layout: single
title: Stream Process - watermark
date: 2021-08-07 11:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - stream
permalink: "2021/08/07/stream-process-watermark"
---

Watermark is a fundamental concept on processing steaming data. Watermark will decide how much data will be frozen and safe to aggregate information.
Watermark is consists of two values which are the max seen event time and threshold on a specific processing time. Threshold value is a delay time which how much we can accumulate data to aggregate.

Because of threshold value, it will decide how frequently we can produce the results.

The following Youtube link is explaining how watermark works on streaming process for Spark.

[https://www.youtube.com/watch?v=XjlKGvUt2dY](https://www.youtube.com/watch?v=XjlKGvUt2dY)