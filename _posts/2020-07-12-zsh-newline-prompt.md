---
layout: single
title: Zsh - adding a new line in a prompt
date: 2020-07-12 09:30:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - zsh
permalink: "2020/07/12/zsh-newline-prompt"
---

The following example will show how to add a newline in zsh prompt

```bash
 export NEWLINE=$'\n'
 export PROMPT='%(?:%{%}➜ :%{%}➜ ) %{$fg[cyan]%}%~%{$reset_color%}                           $(git_prompt_info)${NEWLINE}$ '
```

Example

```zsh
➜  ~/dev/src/rust/rust-cell git:(master) ✗
$
```
