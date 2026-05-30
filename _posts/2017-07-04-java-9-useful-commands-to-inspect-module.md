---
layout: single
title: Java 9 - useful commands to inspect Module
date: 2017-07-04 23:59:06.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Java
- Programming
tags: []
meta:
  _edit_last: '14827209'
  geo_public: '0'
  _publicize_job_id: '6759340606'
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2017/07/04/java-9-useful-commands-to-inspect-module/"
---

List modules\
```
$ java --list-modules
$ java --list-modules java.base
```

Diagnostic module dependencies\
```
$ java -Xdiag:resolver -p mods [module name]/[class package path]
$ jar --file [jar path] --print-module-descriptor
```
