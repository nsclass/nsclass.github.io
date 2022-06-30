---
layout: single
title: TypeScript - mapping between event name and event type
date: 2022-06-30 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - typescript
permalink: "2022/06/30/typescript-mapping-event-name-event-type"
---

Type script for mapping between event name and event type

```typescript
function htmlEventMap<K extends keyof HTMLElementEventMap>(
  eventName: K,
  callback: (event: HTMLElementEventMap[k]) => void
) {
  console.log(eventName)
}

function elementEventMap<K extends keyof ElementEventMap>(
  eventName: K,
  callback: (event: ElementEventMap[k]) => void
) {
  console.log(eventName)
}
```
