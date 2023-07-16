---
layout: single
title: PySpark - Development Environment with Dev Container
date: 2023-07-15 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - pyspark
permalink: "2023/07/15/pyspark-dev-container"
---

It's hard to setup the Spark cluster to run PySpark job locally or CI system. The following github repository will show how we can use dev container feature in VS code to setup Spark cluster in container environment and running PySpark jobs in unit tests.

We can load a file from a mounted directory and perform any operation with Spark dataframe.

```python
spark = SparkSession \
            .builder \
            .master("spark://spark:7077") \
            .config("spark.driver.host", "pyspark-app") \
            .appName('pyspark-app') \
            .getOrCreate()


df = spark.read.csv("/mounted-data/src/unittest/data/crash_catalonia.csv")
row_count = df.count();
```
[PySpark in Dev Container](https://github.com/nsclass/pyspark-devcontainer)
