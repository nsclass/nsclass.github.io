---
layout: single
title: Pyspark - create a new column with concatenating other columns
date: 2022-04-21 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - pyspark
permalink: "2022/04/21/pyspark-concat-json"
---

Pyspark can create a new column with concatenating other columns

```python
import pyspark.sql.functions as fn

df = df_raw \
  .withColumn('new_col', fn.concat_ws('_', df_raw.col1, df_raw.col2))
```

Pyspark can also create a json column with other columns

```python

import pyspark.sql.functions as fn
from pyspark.sql.functions import to_json, struct

json_columns = ["col1", "col2"]
df = df_raw \
  .withColumn('json', fn.to_json(fn.struct([df_raw[x] for x in json_columns])))
```

Pyspark create a json column with all other columns

```python

import pyspark.sql.functions as fn
from pyspark.sql.functions import to_json, struct

df = df_raw \
  .withColumn('json', fn.to_json(fn.col(*)))
```
