---
layout: single
title: Server islands to speed up web site
date: 2024-08-03 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - javascript
permalink: "2024/08/03/server-islands"
---

Another interesting framework called server islands to improve web rendering speed

[Youtube - Server Islands](https://www.youtube.com/watch?v=uBxehYwQox4)

Basic idea is to send the html part first which does not require any dynamic logic then send the part which requires dynamic logic such as `Suspense` in below example.

```js
<main>
  <h1>Hello</h1>

  <Suspense callback = "loading...">
    <SlowComponent />
  </Suspense>

</main>
```
