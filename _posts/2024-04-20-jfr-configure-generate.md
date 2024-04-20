---
layout: single
title: Java - JFR create a new configuration from existing one
date: 2024-04-20 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - java
permalink: "2024/04/20/jfr-create-configuration"
---

Creating a new custom(custom.jfc) JFR configuration from the existing profile.jfc

```bash
jfr configure \
  --input profile.jfc \
  +custom.jfr.MyEvent#enabled=true \
  --output custom.jfc
```

We can use `custom.jfc` on collecting JFR.

```bash
jcmd <pid> JFR.start settings=custom.jfc
```
