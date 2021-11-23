---
layout: single
title: Install FZF with Ultimate vimrc configuration
date: 2021-11-23 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - fzf
permalink: "2021/11/23/install-fzf-ultimate-vimrc"
---

[Ultimate vimrc](https://github.com/amix/vimrc) supports to install the your own vim plugin.

By default ultimate vimrc does not include the fzf vim plugin so we have to clone the following two fzf repositories in my_plugins directory.

```bash
$ cd .vim_runtime
$ git clone https://github.com/junegunn/fzf.git ./my_plugins/fzf
$ git clone https://github.com/junegunn/fzf.vim.git my_plugins/fzf.vim
```
