---
layout: single
title: Linux - Network settings for high traffic generating application
date: 2019-04-14 12:46:33.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Linux
- Programming
tags: []
meta:
  _edit_last: '14827209'
  geo_public: '0'
  _publicize_job_id: '29757139162'
  timeline_notification: '1555263994'
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2019/04/14/linux-network-settings-for-high-traffic-generating-application/"
---

/etc/sysctl.conf

CENT OS example\
```
# sysctl -w net.core.wmem_default=262144
```

\# default socket memory buffer per a socker\
net.core.wmem_default=131072(128KB)\
net.core.rmem_default=131072(128KB)

\# max socker memory buffer per a socker\
net.core.wmem_max=2097152(2MB)\
net.core.rmem_max=2097152(2MB)

\# tcp buffer size (min, default, max) 4KB, 64KB, 2MB\
net.ipv4.tcp_wmem=4096 65536 2048000

\# enable TCP window scaling: client can transfer data more efficiently, it will be buffered in server side.\
net.ipv4.tcp_window_scaling=1

\# allow to accept simultaneous connections\
net.ipv4.tcp_max_syn_backlog=1024
