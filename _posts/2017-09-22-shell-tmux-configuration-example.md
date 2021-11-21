---
layout: single
title: SHELL - tmux configuration example
date: 2017-09-22 22:19:11.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - Programming
  - tmux
tags: []
meta:
  _edit_last: "14827209"
  geo_public: "0"
  _publicize_job_id: "9551195662"
author:
  login: acrocontext
  email:
  display_name: acrocontext
  first_name: ""
  last_name: ""
permalink: "/2017/09/22/shell-tmux-configuration-example/"
---

```bash
# Make mouse useful in copy mode
# setw -g mode-mouse on
# Allow mouse to select which pane to use
# set -g mouse-select-pane on
set -g terminal-overrides 'xterm*:smcup@:rmcup@'
# Set ability to capture on start and restore on exit window data when running an application
setw -g alternate-screen on
# Lower escape timing from 500ms to 50ms for quicker response to scroll-buffer access.
set -s escape-time 50
set-option -g history-limit 5000
```

Tmux switcher with fzf

[https://eioki.eu/2021/01/12/tmux-and-fzf-fuzzy-tmux-session-window-pane-switcher](https://eioki.eu/2021/01/12/tmux-and-fzf-fuzzy-tmux-session-window-pane-switcher)

Display session name

```bash
#!/usr/bin/env bash

# customizable
LIST_DATA="#{session_name} #{window_name} #{pane_title} #{pane_current_path} #{pane_current_command}"
FZF_COMMAND="fzf-tmux -p --delimiter=: --with-nth 4 --color=hl:2"

# do not change
TARGET_SPEC="#{session_name}:#{window_id}:#{pane_id}:"

# select<Plug>PeepOpenane
LINE=$(tmux list-panes -a -F "$TARGET_SPEC $LIST_DATA" | $FZF_COMMAND) || exit 0
# split the result
args=(${LINE//:/ })
# activate session/window/pane
tmux select-pane -t ${args[2]} && tmux select-window -t ${args[1]} && tmux switch-client -t ${args[0]}
```
