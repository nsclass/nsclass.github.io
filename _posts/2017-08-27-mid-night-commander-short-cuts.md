---
layout: single
title: Mid night commander short cuts
date: 2017-08-27 04:58:41.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Etc
tags: []
meta:
  _edit_last: '14827209'
  geo_public: '0'
  _publicize_job_id: '8663940676'
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2017/08/27/mid-night-commander-short-cuts/"
---

MC commands\
----- Esc -----\
Quick change directory: Esc + c\
Quick change directory history: Esc + c and then Esc + h\
Quick change directory previous entry: Esc + c and then Esc + p\
Command line history: Esc + h\
Command line previous command: Esc + p\
View change: Esc + t (each time you do this shortcut a new directory view will appear)\
Print current working directory in command line: Esc + a\
Switch between background command line and MC: Ctrl + o\
Search/Go to directory in active panel: Esc + s / Ctrl + s then start typing directory name\
Open same working directory in the inactive panel: Esc + i\
Open parent working directory in the inactive panel: Esc + o\
Go to top of directory in active pane: Esc + v / Esc + g\
Go to bottom of directory in active pane: Esc + j / Ctrl + c\
Go to previous directory: Esc + y\
Search pop-up: Esc + ?\
----- Ctrl -----\
Refresh active panel: Ctrl + r\
Selecting files and directories: Ctrl + t\
Switch active inactive panels: Ctrl + i\
Switch active inactive panels content: Ctrl + u\
Execute command / Open a directory: Ctrl + j\
----- F -----\
F1: help\
F2: user menu\
F3: read file / open directory\
F4: edit file\
F5: copy file or direcotry\
F6: move file or directory\
F7: create directory\
F8: delete file / directory\
F9: open menu bar\
F10: exit MC

----- Utils -----

next-page, C-v\
move the selection bar one page down.

prev-page, Alt-v\
move the selection bar one page up.

Alt-o If the currently selected file is a directory, load that directory on the other panel and moves the selection to the next file. If the currently selected file is\
not a directory, load the parent directory on the other panel and moves the selection to the next file.

Alt-i make the current directory of the current panel also the current directory of the other panel. Put the other panel to the listing mode if needed. If the current\
panel is panelized, the other panel doesn't become panelized.

C-PageUp, C-PageDown\
only when supported by the terminal: change to ".." and to the currently selected directory respectively.

Alt-y moves to the previous directory in the history, equivalent to clicking the with the mouse.

Alt-Shift-h, Alt-H\
displays the directory history, equivalent to depressing the 'v' with the mouse.

Alt-t toggle the current display listing to show the next display listing mode. With this it is possible to quickly switch to brief listing, long listing, user defined\
listing mode, and back to the default.

C-\\ (control-backslash)\
show the directory hotlist and change to the selected directory.\
Ctrl-x, H: Add a current directory in the hotlist.

Alt-g, Alt-r, Alt-j\
used to select the top file in a panel, the middle file and the bottom one, respectively.

Alt-s(Ctrl-s) search a file name in the current panel

Alt-Shift-?: Find a file in the sub directories.
