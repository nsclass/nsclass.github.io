---
layout: single
title: Linux Container - Base Technologies
date: 2020-07-03 09:30:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - Container
permalink: "2020/07/03/linux-container-base-technology"
---

As we all know, Docker didn't invent a new technology for Linux container. But they provided a really convenient way to utilize the existing Linux container technologies on running a Linux application in a container environment.

Linux container is made of the following three technologies.

- chroot: change root, chroot will allow the command to have a new root

```
# chroot /new-root bash
```

- unshare: namespace, namespace will isolate the process from other processes so that process cannot see other processes

```
# unshare --mount --uts --ipc --net --pid --fork --user --map-root-user chroot /new-root bash
# mount -t proc none /proc # process namespace
# mount -t sysfs none /sys # filesystem
# mount -t tmpfs none /tmp # filesystem
```

- cgroup: control group, cgroup will limit to access the resource usages for the process so that the isolated process cannot consume all CPU, memory etc

```
# cgcreate -g cpu,memory,blkio,devices,freezer:/sandbox
# cgclassify -g cpu,memory,blkio,devices,freezer:sandbox <PID>
```

- The following command will list tasks associated to the sandbox cpu group, we should see the above PID

  ```
  # cat /sys/fs/cgroup/cpu/sandbox/tasks
  ```

More details can be found from the below links.

[https://github.com/btholt/projects-for-complete-intro-to-containers](https://github.com/btholt/projects-for-complete-intro-to-containers)

[https://ericchiang.github.io/post/containers-from-scratch/](https://ericchiang.github.io/post/containers-from-scratch/)
