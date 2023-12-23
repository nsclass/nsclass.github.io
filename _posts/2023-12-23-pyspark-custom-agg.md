---
layout: single
title: PySpark - Custom aggregation count in groupBy
date: 2023-12-23 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - pyspark
permalink: "2023/12/23/custom-aggregation-count"
---

PySpark custom aggregation count example in groupBy.

```py
  cnt_cond = lambda cond: F.sum(F.when(cond, 1).otherwise(0))
  df.groupBy(df.date).agg(F.avg(df.price).alias('avg'),
                          cnt_cond(df.include == 'true').alias('count_cnd')) \
                          .show()
```

[Github code](https://github.com/nsclass/pyspark-app/blob/main/src/unittest/python/pyspark_tests.py#L42-L45)
