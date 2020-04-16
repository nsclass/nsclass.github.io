---
layout: single
title: Python – list all file paths recursively
date: 2020-04-16 14:05:00.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Python
permalink: "2020/04/16/python-list-all-file-paths"
---

List all file paths recursively
```python
import os

def get_all_file_paths(path):
    # r=root, d=directories, f = files
    files = []
    for r, d, f in os.walk(path):
        for file in f:
            files.append(os.path.join(r, file))
    return files
```      
