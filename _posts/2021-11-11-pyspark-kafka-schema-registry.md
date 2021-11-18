---
layout: single
title: PySpark and Kafka with Schema registry
date: 2021-11-11 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - python
permalink: "2021/11/11/pyspark-kafka-schema-registry"
---

PySpark and Kafka with Schema registry

```python
schema_registry_url = "http://localhost:8081"
bootstrap_servers = "localhost:9092"
topic_name = "topic-name"

from confluenct_kafaka.schema_registry import SchemaRegistryClient

schema_registry_conf = { "url": schema_registry_rul}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

schema_key = schema_registry_client.get_latest_version(f"{topic_name}-key")
schema_value = schema_registry_client.get_latest_version(f"{topic_name}-value")
```

```python
import pyspark.sql.functions as fn
from pyspark.sql.types import StringType

binary_to_string = fn.udf(lambda x: str(int.from_bytes(x, byteorder='big')), StringType())
starting_offset - "earliest"

kafka_raw = spark \
  .readStream \
  .format("kafka") \
  .option("kafka.bootstrap.servers", bootstrap_servers) \
  .option("subscribe", topic_name) \
  .option("startingOffsets", starting_offset) \
  .option("failOnDataLoss", "false") \
  .load()
```

```python

from pyspark.sql.avro.functions import from_avro, to_avro

from_avro_options = { "mode" : "PERMISSIVE"}

kafka_raw_df = kafka_raw \
  .withColumn('key', fn.expr("substring(key, 6, length(value) - 5))") \
  .withColumn('keySchemaId', binary_to_string(fn.expr("substring(key, 2, 4)"))) \
  .withColumn('topicBinaryValue', fn.expr("substring(value, 6, length(value) - 5")) \
  .withColumn('topicValue', from_avro('topicBinaryValue', schema_value.schema.schema_str, from_avro_options))
```

Explode example if the value has multiple array in the JSON string

```python

kafka_df = kafka_raw_df \
  .select('timestamp', fn.explode(kafka_raw_df.topicValue.items).alias(item))
```

Generating a new column from the existing column in JSON

```python

json_columns = ["prop1", "prop2"]

kafka_df = kafka_df \
  .withColumn('key', fn.concat_ws("_", kafka_df.prop1, kafka_df.prop2)) \
  .withColumn('value', fn.to_json(fn.struct([kafka_df[x] for x in json_columns])))
```

Write back to another topic in Kafka

```python

kafka_df \
  .writeStream \
  .option("kafka.bootstrap.servers", bootstrap_servers) \
  .option("checkpointLocation", "tmp/test") \
  .option("topic", "another-topic") \
  .outputMode("update") \
  .start()
```
