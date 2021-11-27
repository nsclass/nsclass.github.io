---
layout: single
title: Install FZF/LSP with Ultimate vimrc configuration
date: 2021-11-23 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - fzf
permalink: "2021/11/23/install-fzf-lsp-ultimate-vimrc"
---

[Ultimate vimrc](https://github.com/amix/vimrc) supports to install your own vim plugins.

By default ultimate vimrc does not include the fzf/lsp vim plugin so we have to clone the following fzf/lsp repositories in my_plugins directory.

- FZF installation

  ```bash
  $ cd .vim_runtime
  $ git clone https://github.com/junegunn/fzf.git ./my_plugins/fzf
  $ git clone https://github.com/junegunn/fzf.vim.git my_plugins/fzf.vim
  ```

- LSP plugin installation

  Since Ultimate vim rc includes the ale, we need to install vim-lsp-ale plugin too.

  ```bash
  $ git clone https://github.com/prabirshrestha/vim-lsp.git my_plugins/vim-lsp
  $ git clone https://github.com/mattn/vim-lsp-settings.git my_plugins/vim-lsp-settings
  $ git clone https://github.com/rhysd/vim-lsp-ale.git my_plugins/vim-lsp-ale
  ```
