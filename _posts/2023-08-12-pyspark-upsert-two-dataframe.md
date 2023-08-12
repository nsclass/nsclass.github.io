---
layout: single
title: PySpark - upsert two dataframe
date: 2023-08-12 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - pyspark
permalink: "2023/08/12/pyspark-upsert-two-dataframe"
---

The following PySpark code will upsert target dataframe with source dataframe even though source column is null when key column matched.

```python

from typing import List
from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def upsert(target: DataFrame, source: DataFrame, columns: List[str]) -> DataFrame:

  # assuming the first column is a key column for outer join
  key_column = columns[0]

  # if key_column matched, it will take a value from source,
  # if not matched, it will take a value from source if not null,
  # otherwise it will take a value from target
  replace_f = (F.when(F.col("target." + key_column) == F.col("source." + key_column), F.col("source." + col))
                .otherwise(F.coalesce("source." + col, "target." + col)).alias(col) for col in columns)
  
  result_df = target.alias("target") \
              .join(source.alias("source"), on = [key_column], how = "outer") \
              .select(*(replace_f)) \
              .distinct()
  
  return result_df
```

