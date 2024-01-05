---
layout: single
title: TypeScript - Nullish expression
date: 2024-01-05 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - typescript
permalink: "2024/01/05/typescript-nullish-expression"
---
For the following type, we want to get `val.value` but if it is null or undefined, it should be 10.

```ts
type Value = {
  value? = 0 | 10 | 20
}

const val : Value = 0
```

For this solution, the following expression is always better

```ts
const res = val.value ?? 10
```

than 

```ts
const res = val.value || 10
```

This is because if `val.value = 0`, it will return 10, which is not intended.
