---
layout: single
title: TypeScript - RequireOnly
date: 2023-02-24 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - typescript
permalink: "2023/02/24/typescript-require-only"
---

Very useful utility type definition when we need to define a type having partial mandatory properties in a type.

```typescript
type RequireOnly<T, P extends key of T> = Pick<T, P> & Partial<Omit<T, P>>
```

- Example

```typescript
type Task = {
    id: string;
    title: string;
    desc: string;
}

type DraftTask = RequireOnly<T, 'title'>
```

