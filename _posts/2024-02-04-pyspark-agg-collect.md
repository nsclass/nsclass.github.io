---
layout: single
title: PySpark - groupby then concatenate values to list
date: 2024-02-04 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - pyspark
permalink: "2024/02/04/pyspark-groupby-collect"
---

PySpark example to groupby then concatenate values to list in a separated column.

```python
# 1. Create the DF

df = sc.parallelize([(1, [1, 2, 3]), (1, [4, 5, 6]) , (2,[2]),(2,[3])]).toDF(["store","values"])

+-----+---------+
|store|   values|
+-----+---------+
|    1|[1, 2, 3]|
|    1|[4, 5, 6]|
|    2|      [2]|
|    2|      [3]|
+-----+---------+

# 2. Group by store

df = df.groupBy("store").agg(F.collect_list("values"))

+-----+--------------------+
|store|collect_list(values)|
+-----+--------------------+
|    1|[[1, 2, 3], [4, 5...|
|    2|          [[2], [3]]|
+-----+--------------------+

# 3. finally.... flat the array

df = df.withColumn("flatten_array", F.flatten("collect_list(values)"))

+-----+--------------------+------------------+
|store|collect_list(values)|     flatten_array|
+-----+--------------------+------------------+
|    1|[[1, 2, 3], [4, 5...|[1, 2, 3, 4, 5, 6]|
|    2|          [[2], [3]]|            [2, 3]|
```