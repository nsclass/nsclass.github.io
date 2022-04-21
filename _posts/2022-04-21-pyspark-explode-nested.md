---
layout: single
title: Pyspark - explode the nested data
date: 2022-04-21 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - pyspark
permalink: "2022/04/21/pyspark-explode"
---

Pyspark can explode the nested structure in object

```python
import pyspark.sql.functions as fn

df = df_raw \
  .select('date', 'value', fn.explode(df_raw.groups).alias('group'))
```
