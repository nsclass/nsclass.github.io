---
layout: single
title: Thundering Herd Issue with Cache
date: 2021-01-10 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - Distributed Application
permalink: "2021/01/10/thundering-herd-cache"
---
Thundering herd is a performance problem. When using a cache, if the cache item is expired or evicted by any cache eviction logic, many clients can try to call the slow API to read a missing item at same time. It will cause the system down in high traffic situation such as Black Friday sales.

In order to prevent this issue, the cache server should provide a leased tag for the first contacted client so that other arrived clients will be back off to read again. Meantime the first client will call the slow function to read data from database or other system then it will update data into cache server. After setting the latest dat in cache server, the leased tag will be removed so that other many waiting clients can get the new data from cache server.
