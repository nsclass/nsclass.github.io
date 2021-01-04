---
layout: single
title: Git - adding a tag with the latest commit date
date: 2020-10-13 09:30:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - git
permalink: "2020/10/13/git-tag-commit-date"
---

Adding a git tag with the latest commit date.
```bash
$ GIT_COMMITTER_DATE=$(git log -n1 --pretty=%aD) git tag -a -m "Release 0.0.1" 0.0.1
$ git push --tags
```