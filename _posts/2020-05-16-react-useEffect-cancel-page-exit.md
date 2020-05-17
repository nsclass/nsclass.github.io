---
layout: single
title: React - useEffect to detect page exit
date: 2020-05-16 08:30:00.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- React
permalink: "2020/05/16/react-useEffect-page-exit"
---

We can detect the page exit in useEffect Hooks

```javascript
const [state, setState] = useState(null)

useEffect(() => {
  let cancelled = false
  // do something
  // if there is any async code in here, 
  // we can use the cancelled flag to detect whether user left this page

  return () => {cancelled = true}
}, [state])
```
