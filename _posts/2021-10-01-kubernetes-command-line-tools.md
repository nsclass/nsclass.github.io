---
layout: single
title: Kubernetes command line tools(kubectl, kubectx, kubens, stern)
date: 2021-10-01 19:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - Kubernetes
permalink: "2021/10/01/kubernetes-command-line-tools"
---

kubectl

- Kubernetes official client
- `brew install kubectl`

kubectx

- Kubectx is helpful for multi-cluster installations, where you need to switch context between one cluster and another.
- `brew install kubectx`
- [https://github.com/ahmetb/kubectx](https://github.com/ahmetb/kubectx)

kubens

- This script allows you to easily switch between Kubernetes namespaces
- This script is installed with `kubectx`

stern

- A tool to display the tail end of logs for multiple containers and pods
- `brew install stern`
- [https://github.com/wercker/stern](https://github.com/wercker/stern)
