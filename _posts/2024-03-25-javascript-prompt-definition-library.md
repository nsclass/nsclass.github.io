---
layout: single
title: Prompt definition library in JavaScript
date: 2024-03-25 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - javascript
permalink: "2024/03/25/javascript-prompt-definition"
---

The following library will help on defining the prompt for AI.

ZOD, Langchain

[Github code example](https://github.com/Hendrixer/fullstack-ai-nextjs/blob/main/util/ai.ts)

```js
import {
  StructuredOutputParser,
  OutputFixingParser,
} from 'langchain/output_parsers'
import { z } from 'zod'

const parser = StructuredOutputParser.fromZodSchema(
  z.object({
    mood: z
      .string()
      .describe('the mood of the person who wrote the journal entry.'),
    subject: z.string().describe('the subject of the journal entry.'),
    negative: z
      .boolean()
      .describe(
        'is the journal entry negative? (i.e. does it contain negative emotions?).'
      ),
    summary: z.string().describe('quick summary of the entire entry.'),
    color: z
      .string()
      .describe(
        'a hexidecimal color code that represents the mood of the entry. Example #0101fe for blue representing happiness.'
      ),
    sentimentScore: z
      .number()
      .describe(
        'sentiment of the text and rated on a scale from -10 to 10, where -10 is extremely negative, 0 is neutral, and 10 is extremely positive.'
      ),
  })
)
```
