---
layout: single
title: Node for input/output example
date: 2024-03-01 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - javascript
permalink: "2024/03/01/node-input-output"
---

Example of getting input and output from system in Node

```js
import readline from 'node:readline'

const rl = readline.createInterface({
  input: process.input,
  output: process.output
})

rl.question('$ ', async (input) => {
  console.log(input);

})
```
