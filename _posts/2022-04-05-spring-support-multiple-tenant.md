---
layout: single
title: Spring - Supporting multiple tenant for JDBC
date: 2022-04-05 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - rust
permalink: "2022/04/05/spring-multiple-tenant"
---

Josh Long showed us another very nice Spring tips for supporting multiple tenants with JDBC.
Spring provide the `AbstractRoutingDataSource` to support multiple JDBC connection based on tenant Id.

[AbstractRoutingDataSource](https://spring.io/blog/2022/03/23/spring-tips-multitenant-jdbc)

[Multiple JDBC data source github](https://github.com/spring-tips/multitenant-jdbc)
