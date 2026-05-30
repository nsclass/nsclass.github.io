---
layout: single
title: How do I flash my window caption and taskbar button manually?
date: 2008-05-15 11:20:44.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Code
tags: []
meta:
  spaces_8e963f1d044baa6ea177d10f0c6ccc02_permalink: http://cid-f610c86c6d82b8a2.users.api.live.net/Users(-715851972732602206)/Blogs('F610C86C6D82B8A2!116')/Entries('F610C86C6D82B8A2!173')?authkey=bau8ZqLz*pg%24
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2008/05/15/how-do-i-flash-my-window-caption-and-taskbar-button-manually/"
---

<div id="msgcns!F610C86C6D82B8A2!173" class="bvMsg">

<div>

Commenter Jonathan Scheepers [<u>wonders about those programs that flash their taskbar button indefinitely</u>](http://blogs.msdn.com/oldnewthing/pages/407234.aspx#513263), overriding the default flash count set by `SysteParametersInfo(SPI_SETFOREGROUNDFLASHCOUNT)`.

The `FlashWindowEx` function and its simpler precursor `FlashWindow` let a program flash its window caption and taskbar button manually. The window manager flashes the caption automatically (and Explorer follows the caption by flashing the taskbar button) if a program calls `SetForegroundWindow` when it doesn't have permission to take foreground, and it is that automatic flashing that the `SPI_SETFOREGROUNDFLASHCOUNT` setting controls.

For illustration purposes, I'll demonstrate flashing the caption manually. This is generally speaking not recommended, but since you asked, I'll show you how. And then promise you won't do it.

Start with the scratch program and make this simple change:

    void
    OnSize(HWND hwnd, UINT state, int cx, int cy)
    {
      if (state == SIZE_MINIMIZED) {
        FLASHWINFO fwi = { sizeof(fwi), hwnd,
                           FLASHW_TIMERNOFG | FLASHW_ALL };
        FlashWindowEx(&fwi);
      }
    }

Compile and run this program, then minimize it. When you do, its taskbar button flashes indefinitely until you click on it. The program responds to being minimzed by calling the `FlashWindowEx` function asking for everything possible (currently the caption and taskbar button) to be flashed until the window comes to the foreground.

Other members of the `FLASHWINFO` structure let you customize the flashing behavior further, such as controlling the flash frequency and the number of flashes. and if you really want to take control, you can use `FLASHW_ALL` and `FLASHW_STOP` to turn your caption and taskbar button on and off exactly the way you want it. (Who knows, maybe you want to send a message in Morse code.)

</div>

</div>
