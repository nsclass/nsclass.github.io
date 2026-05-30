---
layout: single
title: Windbg - command types
date: 2013-10-13 22:59:18.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Programming
tags: []
meta:
  _edit_last: '14827209'
  _publicize_pending: '1'
  _oembed_623c75d4ce5d61d70d990a9d15e26f98: "{{unknown}}"
  geo_public: '0'
  _oembed_d20e658c51a670d70edcf1f5f3973a18: "{{unknown}}"
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2013/10/13/windbg-command-types/"
---

### Windbg has the following command types

- Native commands: it starts without any prefix
  - vertaget, k, ~, s, lm, lmv m \*clr\*
- Meta commands(.): it starts with '.'
  - .load, .chain, .prefer_dml 1(available .NET4)
  - .exr -1 =\> dd poi(addr) =\> !pe
  - Print all exceptions: .foreach (ex {!dumpheap -type Exception -short}){.echo "\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*";!pe \${ex} }
- Extension commands(!): it starts with '!'
  - !help, !peb
  - List exceptions in dump file: !dumpheap -type Exception

### Loading the right version of sos.dll

The following command will ensure that the debugger to load the extension "sos.dll" from the same place that clr.dll was loaded. That ensures that you get the right version of SOS (it should be the one that matches the clr you are using)\
Notes: SOS stands for Son of Strike from (Drill Into .NET Framework Internals to See How the CLR Creates Runtime Objects: http://msdn.microsoft.com/en-us/magazine/cc163791.aspx#S5)

- .NET4
  {% highlight wl linenos %} .loadby sos.dll clr {% endhighlight %}
- .NET2
  {% highlight wl linenos %} .loadby sos.dll mscoworks {% endhighlight %}

### Channel9 MSDN show

http://channel9.msdn.com/Shows/Defrag-Tools/Defrag-Tools-14-WinDbg-SOS

### More examples

- version\
  vertarget\
  \|\
  \|\|\
  .sympath\
  .srcpath\
  .exepath\
  .extpath\
  .chain\
  !analyze -v\
  .bugcheck\
  !error\
  ~\
  ~NNs\
  \~~\[TID\]s\
  ~\*k\
  ~\*r\
  !process 0 17\
  !threads\
  !findstack\
  !uniqstack\
  !peb\
  !teb\
  k=\
  dps\
  dpu\
  dpa\
  dpp\
  .reload /f\
  .reload /user\
  !gle\
  !tls\
  !address -summary\
  !address\
  !vprot\
  !mapped_file\
  ~\*kv\
  ~\
  \~~\[TID\]s\
  !cs\
  !locks\
  dv\
  dt\
  !sos.dumpstack\
  !sos.dumpstackobjects / !sos.dso\
  !sos.dumpobj / !sos.do\
  !sos.printexception / !sos.pe\
  .frame\
  .f+\
  .f-\
  .load\
  .unload\
  .loadby\
  .chain\
  lm / lmm / lmvm\
  .extmatch\
  .prefer_dml 1\
  .lines\
  .ecxr\
  .cls
