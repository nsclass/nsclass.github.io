---
layout: single
title: Minimal Mistake – Enabling code block line number with markdown
date: 2020-04-15 07:13:00.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Markdown
permalink: "2020/04/15/mininmal-mistak-jekyll-markdown-codeblock"
---

By adding the following configuration in _config.yml file, we can see the code block line number
```yml
kramdown:
  syntax_highlighter_opts:
    block:
      line_numbers: true
```      
