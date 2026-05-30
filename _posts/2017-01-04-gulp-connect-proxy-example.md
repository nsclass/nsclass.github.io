---
layout: single
title: Gulp - connect proxy example
date: 2017-01-04 08:50:18.000000000 -06:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Programming
- Web
tags:
- gulp
meta:
  _edit_last: '14827209'
  _oembed_a3a5433ba5839fa1be40024b8f3befbe: "{{unknown}}"
  _oembed_ed03d4a507b5dd4ee80dd89324a75f9b: "{{unknown}}"
  geo_public: '0'
  _publicize_job_id: '372227800'
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2017/01/04/gulp-connect-proxy-example/"
---

It will avoid CORS problem during development.

```
var Proxy = require('gulp-connect-proxy');
...
// A local web server for dev convenience
gulp.task("server", function() {
	connect.server({
	  root: "./dist",
	  port: 22532,
          middleware: function (connect, opt) {
	      opt.route = '/proxy';
	      var proxy = new Proxy(opt);
	      return [proxy];
	  }
	});
});
```

Example of calling API\
```
return $http.get(
  'http://localhost:22532/proxy/external.host.com:8080/api/myservice/myid', 
  { params: { metricSelector: "hello2"} }
);
```

Gulp connect web site

https://www.npmjs.com/package/gulp-connect-proxy
