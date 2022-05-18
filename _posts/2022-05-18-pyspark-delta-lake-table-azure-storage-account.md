---
layout: single
title: Pyspark - Delta Lake Table from Azure Storage Account
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

Reading data from Azure Storage Account.

```python
folder = "folder"
storageAccount = "storageAccount"
container = "container"
sasToken = "sasToken"

storageAccountKey = f"fs.azure.sas.{container}.{storageAccount}.blob.core.windows.net"
conf = f"https://{storageAccount}.blob.core.windows.net/{container}?{sasToken}"
spark.conf.set(storageAccountKey, conf)

path = f"wasbs://{container}@{storageAccount}.blob.core.windows.net/{folder}"
table = spark.sql(f"SELECT * FROM delta.`{path}`")
display(table)
```
