---
layout: single
title: React - Testing custom hooks
date: 2022-12-25 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - data
permalink: "2022/12/25/react-testing-custom-hook"
---

React testing library provide a way to test a custom hook by using `renderHook` from `@testing-library/react`.

[Github code](https://github.com/nsclass/ns-svg-converter/blob/master/ns-svg-converter-react/src/__tests__/ImageDropZone.test.jsx)

```js
import { expect, test } from "@jest/globals"
import { renderHook } from "@testing-library/react"
import { useImageDropZone } from "../hooks/useImageDropZone"

test("should render useImageDropZone", async () => {
  const { result } = renderHook(() => useImageDropZone())
  const [filename, fileContent, ImageDropZone] = result.current
  expect(ImageDropZone).toBeDefined()
})
```
