---
layout: single
title: Langchain-js with llama cpp for embeddings and prompt example
date: 2024-03-31 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - ai
permalink: "2024/03/31/langchain-js-llama-cpp-embeddings-prompt"
---

Langchain JS example with Llama cpp for embeddings and prompt.

```ts
import 'dotenv/config'
import { LlamaCpp } from '@langchain/community/llms/llama_cpp'
import { LlamaCppEmbeddings } from '@langchain/community/embeddings/llama_cpp'
import { ChatPromptTemplate } from '@langchain/core/prompts'
import { StringOutputParser } from '@langchain/core/output_parsers'
import { MemoryVectorStore } from 'langchain/vectorstores/memory'

const LLAMA_MODEL_LOCAL_PATH = process.env.LLAMA_PATH || ''

async function streamingResponse(model: LlamaCpp) {
  const prompt = 'Tell me a short story about a happy Llama.'
  const stream = await model.stream(prompt)
  for await (const chunk of stream) {
    console.log(chunk)
  }
}

async function memoryVectorStore(modelPath: string) {
  const embeddings = new LlamaCppEmbeddings({
    modelPath,
  })
  const vectorStore = await MemoryVectorStore.fromTexts(
    ['Hello world', 'Bye bye', 'hello nice world'],
    [{ id: 2 }, { id: 1 }, { id: 3 }],
    embeddings,
  )

  const resultOne = await vectorStore.similaritySearch('hello world', 1)
  console.log(resultOne)
}

await memoryVectorStore(LLAMA_MODEL_LOCAL_PATH)

async function prompt(modelPath: string) {
  const model = new LlamaCpp({
    modelPath,
    temperature: 0.7,
  })

  const prompt = ChatPromptTemplate.fromMessages([
    ['human', 'Tell me a short joke about {topic}'],
  ])

  const outputParser = new StringOutputParser()
  const chain = prompt.pipe(model).pipe(outputParser)

  const response = await chain.invoke({
    topic: 'ice cream',
  })

  console.log(response)
}

await prompt(LLAMA_MODEL_LOCAL_PATH)
```