---
layout: single
title: tmux switcher with fzf
date: 2017-09-22 22:19:11.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - tmux
tags: []
permalink: "/2017/09/22/tmx-fzf-switcher/"
---

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

Tmux key binding configuration

```
# Key binding
bind-key ` run-shell -b $HOME/.local/bin/tmux-fzf-switcher.sh
```
