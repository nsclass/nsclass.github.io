---
layout: single
title: Cassandra - Partition Key, Clustering key
date: 2016-11-26 07:37:44.000000000 -06:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- cassandra
- Programming
tags: []
meta:
  _edit_last: '14827209'
  geo_public: '0'
  _publicize_job_id: '29305137315'
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2016/11/26/cassandra-partition-key-clustering-key/"
---

Partition Key: It will be hashed and saved across nodes.\
Clustering Key: It will group in the same partition key.

PRIMARY KEY((partion key), clustering key)\
Example)\
create table User(\
email text,\
name text,\
desc text,\
user_id uuid\
PRIMARY KEY((email), name, user_id)\
) WITH CLUSTERING ORDER BY (name DESC, user_id ASC);

Primary Key: email\
Clustering Key: name, user_id

Reason of adding a user_id is to ensure the uniqueness of primary key.
