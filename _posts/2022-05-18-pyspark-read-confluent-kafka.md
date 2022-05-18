---
layout: single
title: Pyspark - Reading from Confluent Kafka
date: 2022-05-18 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - pyspark
permalink: "2022/05/18/pyspark-confluent-kafka"
---

In order to use confluent schema registry, the following python package should be installed in a spark cluster

```
confluent-kafka[avro,json,protobuf]>=1.4.2
```

[Confluent Kafka with Pyspark](https://www.confluent.io/blog/consume-avro-data-from-kafka-topics-and-secured-schema-registry-with-databricks-confluent-cloud-on-azure/)

```python
import pyspark.sql.functions as fn
from confluent_kafka.schema_registry import SchemaRegistryClient

schema_registry_conf = { url: 'http://localhost:8081'}
schema_registry_client = SchemaRegistryClient(schema_registry_conf)

topic = "topic"

schema_key = schema_registry.client.get_latest_version(f"{topic}-key")
schema_value = schema_registry.client.get_latest_version(f"{topic}-value")

df = (
   spark
  .readStream
  .format("kafka")
  .option("kafka.bootstrap.servers", confluentBootstrapServers)
  .option("kafka.security.protocol", "SASL_SSL")
  .option("kafka.sasl.jaas.config", "kafkashaded.org.apache.kafka.common.security.plain.PlainLoginModule required username='{}' password='{}';".format(confluentApiKey, confluentSecret))
  .option("kafka.ssl.endpoint.identification.algorithm", "https")
  .option("kafka.sasl.mechanism", "PLAIN")
  .option("subscribe", confluentTopicName)
  .option("startingOffsets", "earliest")
  .option("failOnDataLoss", "false")
  .load()
  .withColumn('key', fn.col("key").cast(StringType()))
  .withColumn('fixedValue', fn.expr("substring(value, 6, length(value)-5)"))
  .withColumn('fixedValue', from_avro('fixedValue', schema_value.schema.schema_str))
  .select(fn.col("fixedValue.*"))
)
```
