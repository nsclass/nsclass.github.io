---
layout: single
title: Mac OSX NVCAP
date: 2009-07-08 13:46:38.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Mac OSX
tags: []
meta:
  spaces_8e963f1d044baa6ea177d10f0c6ccc02_permalink: http://cid-f610c86c6d82b8a2.users.api.live.net/Users(-715851972732602206)/Blogs('F610C86C6D82B8A2!116')/Entries('F610C86C6D82B8A2!263')?authkey=bau8ZqLz*pg%24
  _oembed_5256053a34209f2929e1aba11dc7e761: "{{unknown}}"
  _oembed_dd2824caaa85c682ddf2efc6047a1862: "{{unknown}}"
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2009/07/08/mac-osx-nvcap/"
---

URL: <http://nvinject.free.fr/forums/viewtopic.php?t=214>

 

Thanks to Arti and the lot of experiments we've been doing last weeks on hackintoshes and PowerPC Macintoshes with NVIDIA cards, NVCAP is now mostly mastered. As I've said <a href="http://nvinject.free.fr/forums/viewtopic.php?t=193" target="_blank">here</a>, NVCAP can't fix everything, but it is necessary to get proper display detection on VGA and DVI outputs. TV out and laptops' displays may require further hacking...

Anyway, first I'll show what are the important part in NVCAP and how they work :

04000000 0000xx00 xx000000 00000000 00000000

the bold bytes define output channels. They are using a "bitmap" setting to define which output is used on which channel, and there's actually not so many possibilities for usual cards.

Most cards are using 4 or 5 outputs :

1/ DVI - 2/ VGA, 3/ VGA, 4/ TV out\
1/ DVI - 2/ VGA, 3/ DVI - 4/ VGA, 5/ TV out

Later I'll show how this is defined in a PC NVIDIA ROM for GeForce 5/6/7/8 series.

\- so most dual DVI cards will have channels using this settings (5 different outputs) :

channel 1 :\
DVI + VGA --\> bitmap 0 0 0 1 1 --\> hex 03\
channel 2 :\
DVI + VGA + TV --\> bitmap 1 1 1 0 0 --\> hex 1c

or

channel 1 :\
DVI + VGA + TV --\> bitmap 1 0 0 1 1 --\> hex 13\
channel 2 :\
DVI + VGA + TV --\> bitmap 0 1 1 0 0 --\> hex 0c

TV output is usually defined a the last entry in the output definitions in VGA ROM, that's why it is using the last position (5th position on dual DVI cards, or 4th position on DVI + VGA cards)

\- for DVI + VGA cards (4 different outputs) :

channel 1 :\
DVI + VGA --\> bitmap 0 0 1 1 --\> hex 03\
channel 2 :\
VGA + TV --\> bitmap 1 1 0 0 --\> hex 0c

or

channel 1 :\
DVI + VGA + TV--\> bitmap 1 0 1 1 --\> hex 0b\
channel 2 :\
VGA --\> bitmap 0 1 0 0 --\> hex 04\
(as you can see, TV out is on last available postition, so 4th position for 4 available outputs)

or

channel 1 :\
VGA --\> bitmap 0 0 0 1 --\> hex 01\
channel 2 :\
DVI + VGA + TV --\> bitmap 1 1 1 0 --\> hex 0e\
or

channel 1 :\
VGA + TV --\> bitmap 1 0 0 1 --\> hex 09\
channel 2 :\
DVI + VGA --\> bitmap 0 1 1 0 --\> hex 06

The main difference with windows behaviour is that Windows NVIDIA drivers are able to dynamically define which channel to use for TV output, whereas OS X drivers use a fixed position for TV out, NVCAP being defined in VGA ROM and saved in IOreg. This setting is not able to change in OS X once drivers are loaded.

So usual NVCAP for standard cards would be :

dual DVI cards :

04000000 00000300 0c000000 00000000 00000000 --\> disabling 5th position, no TV output.\
04000000 00001300 0c000000 00000000 00000000 --\> 5th position for TV out set on channel 1, TV out available when no other display is connected on channel 1.\
04000000 00000300 1c000000 00000000 00000000 --\> 5th position for TV out set on channel 2, TV out available when no other display is connected on channel 2.

DVI + VGA cards :

04000000 00000100 06000000 00000000 00000000 --\> disabling 4th position, no TV output, only 1 output on channel 1 and DVI + VGA on channel 2\
04000000 00000300 04000000 00000000 00000000 --\> disabling 4th position, no TV output, only 1 output on channel 2 and DVI + VGA on channel 1\
04000000 00000300 0e000000 00000000 00000000 --\> VGA only on channel 1, 4th position for TV out set on channel 2, TV out available when no other display is connected on channel 2.\
04000000 00000900 06000000 00000000 00000000 --\> VGA only on channel 1, 4th position for TV out set on channel 1, TV out available when no other display is connected on channel 1 (DVI + VGA on channel 2 using position 2 and 3, bitmap 0 1 1 0)

Laptops usually have first channel using only 1 output for internal panel, on position 1, and depending on how many other outputs are available, second channel can use positions 2, 3, and 4 :\
04000000 00000100 02000000 00000000 00000000\
04000000 00000100 06000000 00000000 00000000\
04000000 00000100 0e000000 00000000 00000000

more about the VGA ROM output definitions later...

