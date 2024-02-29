---
layout: single
title: PySpark dataframe to Opensearch
date: 2024-02-29 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - PySpark
permalink: "2024/02/29/pyspark-opensearch"
---

https://github.com/opensearch-project/opensearch-hadoop/issues/153#issuecomment-1551501905


- Launch PySpark with an open search
```
pyspark --jars /home/nknize/Downloads/opensearch-hadoop-3.0.0-SNAPSHOT.jar
```

```python
from pyspark.sql import SparkSession
sparkSession = SparkSession.builder.appName("pysparkTest").getOrCreate()
df = sparkSession.createDataFrame([(1, "value1"), (2, "value2")], ["id", "value"])
df.show()
df.write\
    .format("org.opensearch.spark.sql")\
    .option("inferSchema", "true")\
    .option("opensearch.nodes", "127.0.0.1")\
    .option("opensearch.port", "9200")\
    .option("opensearch.net.http.auth.user", "admin")\
    .option("opensearch.net.http.auth.pass", "admin")\
    .option("opensearch.net.ssl", "true")\
    .option("opensearch.net.ssl.cert.allow.self.signed", "true")\
    .option("opensearch.batch.write.retry.count", "9")\
    .option("opensearch.http.retries", "9")\
    .option("opensearch.http.timeout", "18000")\
    .mode("append")\
    .save("pyspark_idx")
```
