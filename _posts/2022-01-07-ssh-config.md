---
layout: single
title: SSH configuration for Remote Connection
date: 2022-01-07 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - ssh
permalink: "2022/01/07/ssh-configuration"
---

The following steps will show how to config ssh connection.

- generate the ssh keys

```bash
$ ssh-keygen -t rsa -P ""
```

- add a new remote host configuration
  Let's assume that we have the following host IP and username on a remote server
  IP: 192.168.64.2
  user: ubuntu

```bash
$ cd ~.ssh
$ touch config
```

Add the following contents in the config file.

```
Host ubuntu
    Hostname 192.168.64.2
    User ubuntu
```

- configure the authorization in a remote server

copy the public key from the local host. You can find the public key from the below command.

```bash
$ cat ~.ssh/id_rsa.pub
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC9vmTjzHpBVLZMn5IlFs/DOIIjZWUUDh0ohewfA6cDpAxpZI3QjR07pmU7xU6qny1vLokl19hi0sMpVUKYsX/c8gmgoxCjRK0SQcxICnLy4UTu6aNRHrONRsnd+z/JiEI0JMSU4gTKaS1GYyuWLB7fHHiT8OmmuleKOC18SXyOIi1CKjInt7E1omSf2ezbYVl7qpeA1ywHcER5OSVrNxntQTtAVuR6i/dZi3aUvTT8S2w7CeWJLcKw21l9EieAXh1Nn/hQVBUrDUCfSl4GTwS2cfKW4F3gS8JH/5xS3z53ABKkljxEOUou1kLZTUHoyxOaw9EGL/9mFwdmVlOynbNt OpenShift-Key
```

connect the remote server and change the directory to .ssh

```bash
$ ssh ubunto@192168.64.2
$ cd .ssh
```

if `authorized_keys` file does not exist, you can create it with a touch command

```bash
$ touch authorized_keys
```

copy the public key in the authorized_keys file. you will see the following item once you copied it correctly.

```bash
$ cat authorized_keys
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC9vmTjzHpBVLZMn5IlFs/DOIIjZWUUDh0ohewfA6cDpAxpZI3QjR07pmU7xU6qny1vLokl19hi0sMpVUKYsX/c8gmgoxCjRK0SQcxICnLy4UTu6aNRHrONRsnd+z/JiEI0JMSU4gTKaS1GYyuWLB7fHHiT8OmmuleKOC18SXyOIi1CKjInt7E1omSf2ezbYVl7qpeA1ywHcER5OSVrNxntQTtAVuR6i/dZi3aUvTT8S2w7CeWJLcKw21l9EieAXh1Nn/hQVBUrDUCfSl4GTwS2cfKW4F3gS8JH/5xS3z53ABKkljxEOUou1kLZTUHoyxOaw9EGL/9mFwdmVlOynbNt OpenShift-Key
```

- connect the remote server
  Now, you can connect the remote server with the following command. It will not ask you user/password anymore.

```
$ ssh ubuntu
```

You can find more details about ssh config example from the below link.
[SSH config](https://linuxize.com/post/using-the-ssh-config-file/)
