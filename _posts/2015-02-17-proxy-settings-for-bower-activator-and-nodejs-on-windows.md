---
layout: single
title: Proxy Settings for Bower, Activator and Nodejs on Windows
date: 2015-02-17 10:14:13.000000000 -06:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Programming
tags: []
meta:
  _edit_last: '14827209'
  _publicize_pending: '1'
  geo_public: '0'
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2015/02/17/proxy-settings-for-bower-activator-and-nodejs-on-windows/"
---

1\. Bower\
- create a file .bowerrc in C:\Users\userId directory.\
- content example\
```
{
	"proxy":"http://user:pass@host:portId",
	"https-proxy":"http://user:pass@host:portId"
}
```

2\. Activator\
- create a file c:\Users\userId\\activator\activatorconfig.txt\
- conent example\
```
# This are the proxy settings we use for activator
-Dhttp.proxyHost=proxy-host
-Dhttp.proxyPort=port
# Here we configure the hosts which should not go through the proxy.  You should include your private network, if applicable.
-Dhttp.nonProxyHosts="localhost|127.0.0.1"
# These are commented out, but if you need to use authentication for your proxy, please fill these out.
-Dhttp.proxyUser=username
-Dhttp.proxyPassword=pass
```

3\. Nodejs\
- create a file c:\Users\userId\\npmrc\
- context example\
```
proxy=http://userId:pass@host:portNumber
```
