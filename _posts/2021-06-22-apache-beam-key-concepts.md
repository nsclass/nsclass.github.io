---
layout: single
title: Apache Beam Key Concepts
date: 2021-06-22 07:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - apache beam
permalink: "2021/06/22/apache-beam-key-concepts"
---

Apache Beam has the following key concepts.

1. Pipeline

- Modeling processing data

2. PCollection

- Immutable dataset

3. PTransform

- Various transforming functions

  - ParDo
  - GroupBy
  - Combine
  - Flatten
  - Partition

4. Side Input

- Additional data to support transformation

5. Runner

- Selecting platform to run logics such as Spark, Flink and etc

6. Windowing

- Defining time windows - What

7. Triggers

- When aggregation will run - When

8. Schema

- Defining data format
