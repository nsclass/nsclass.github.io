---
layout: single
title: Git Merge Command
date: 2020-05-23 22:30:00.000000000 -05:00
type: post
parent_id: '0'
published: true
password: ''
status: publish
categories:
- Git
permalink: "2020/05/23/git-merge-command"
---

Git commands when merge conflicts happened.

We can abort merging with the following command
```bash
$ git merge --abort
```

Resolving merge conflict with merge tool
```bash
$ git mergetool
```

Adding all changes after resolving merge conflicts with merge tool.
```bash
$ git add -A
```

With the following command, we can finish the merge conflict.
```bash
$ git merge --continue
```
