---
layout: single
title: TypeScript - type checking only and prettier format checking
date: 2022-06-10 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - typescript
permalink: "2022/06/10/type-checking-format-checking"
---

Run type script compiler to check types only.
Format checking with prettier

```json
{
  "format:check": "prettier --check \"src/**/*.{js,ts,tsx}\"",
  "format": "prettier --write \"src/**/*.{js,ts,tsx}\"",
  "typecheck": "tsc --noEmit"
}
```
