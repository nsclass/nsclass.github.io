---
layout: single
title: LLM - key terms 
date: 2025-09-14 18:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - cpp
permalink: "2025/09/14/llm-key-terms
---

Key terms from [Reasoning Engine by Gulli](https://docs.google.com/document/d/1WUk_A3LDvRJ8ZNvRG--vhI287nDMR-VNM4YOV8mctbI/edit?tab=t.0)

- Attention: A mechanism that allows a neural network to weigh the importance of different parts of an input sequence.
- Auto-regressive: A model that generates a sequence one token at a time, where each new token is conditioned on the previously generated tokens.
- Context Window: The fixed maximum number of tokens a Transformer model can process at once.
- Cross-Attention: The attention mechanism in the decoder that attends to the output of the encoder, linking the input and output sequences.
- Decoder: The part of the Transformer that generates the output sequence.
- Encoder: The part of the Transformer that processes the input sequence to create a contextualized representation.
- Fine-Tuning: The process of adapting a pre-trained model to a specific task using a smaller, labeled dataset.
- Hallucination: The tendency of a language model to generate confident but factually incorrect or nonsensical information.
- In-Context Learning: The ability of a large language model to perform a task based on a few examples provided in its prompt, without any weight updates.
- LLM (Large Language Model): A very large neural network, typically a Transformer, trained on vast amounts of text data.
- Masked Language Modeling (MLM): A self-supervised pre-training objective where the model learns to predict masked tokens in a sequence.
- Multi-Head Attention: A mechanism that runs multiple attention calculations in parallel to capture different types of relationships in the data.
- PEFT (Parameter-Efficient Fine-Tuning): A set of techniques (like LoRA) for adapting a large model by training only a small fraction of its parameters.
- Positional Encoding: Information about the position of tokens in a sequence that is added to the input embeddings.
- Pre-training: The initial, computationally intensive phase of training a model on a massive, unlabeled dataset.
- Prompt: The input text given to a language model to elicit a response.
- RAG (Retrieval-Augmented Generation): A technique that combines a language model with an external knowledge base to improve the factuality of its outputs.
- RLHF (Reinforcement Learning from Human Feedback): A technique for aligning a model with human preferences by using a reward model trained on human-ranked responses.
- Self-Attention: An attention mechanism where a sequence processes itself, allowing every token to attend to every other token.
- Token: A unit of text, which can be a word, a subword, or a character, that is used as input to the model.
- Transfer Learning: A machine learning paradigm where a model trained on one task is repurposed for a second, related task.