---
layout: single
title: Windows Performance count - select process with process id
date: 2015-07-28 12:08:00.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Performance
- Programming
tags: []
meta:
  _edit_last: '14827209'
  geo_public: '0'
  _publicize_job_id: '13155231297'
author:
  login: acrocontext
  email:  
  display_name: acrocontext
  first_name: ''
  last_name: ''
permalink: "/2015/07/28/windows-performance-count-select-process-with-process-id/"
---

If you have process having same name, it will be really difficult to collect performance counter. Here is a solution for this by modifying the registry key.

Click Start, click Run, type regedit, and then click OK.\
Locate and then click the following registry subkey:

HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\PerfProc\Performance\
On the Edit menu, click New, and then click DWORD Value.\
Right-click New Value \#1, click Rename, and then type ProcessNameFormat to name the new value.\
Right-click ProcessNameFormat, and then click Modify.\
In the Data value box, type one of the following values, and then click OK:

1: Disables PID data. This value is the default value.\
2: Enables PID data.

Exit Registry Editor.
