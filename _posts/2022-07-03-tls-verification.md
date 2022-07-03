---
layout: single
title: TLS verification with openssl command
date: 2022-07-03 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - TLS
permalink: "2022/07/03/tls-verification"
---

openssl command to verify TLS connection

```bash
$ openssl s_client -state -CAfile root.ca.crt -connect igvita.com:443
```

[Networking 101 - TLS](https://hpbn.co/transport-layer-security-tls/)
