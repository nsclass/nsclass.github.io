---
layout: single
title: Mac - Install Ruby 3.1.2 on M1 processor
date: 2023-04-23 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - ruby
permalink: "2023/04/23/mac-m1-install-ruby-3"
---

Installing Ruby 3.1.2 for M1 Mac

```bash
$ arch -x86_64 rvm install 3.1.2 --with-openssl-dir=/usr/local/opt/openssl@3
```

[Stack Overflow](https://stackoverflow.com/questions/66645381/installing-ruby-with-ruby-install-causes-error-out-on-mac-m1)