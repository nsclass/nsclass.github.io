---
layout: single
title: React - Form handler example
date: 2020-05-16 09:30:00.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- React
permalink: "2020/05/16/react-form-handler-example"
---

The following example shows the basic form submit handling with React

```javascript
import React from "react"
import axios from "axios"

const Form = ({reloadPage}) => {
  const [text, setText] = useState('')

  const handleSubmit = async event => {
    event.preventDefault()

    const config = {
      headers: {
        "Content-type": "application/json"
      }
    }

    const {data} = await axios.post("/url", JSON.parse(text), config)
    setText('')
    reloadPage()
  }

  return (
    <form onSubmit={handleSubmit}>
      <label>Text</label>
      <input type="text" value={text} onChange={e => setText(e.target.value)}>
      <button>submit</button>
    </form>
  )
}

```
