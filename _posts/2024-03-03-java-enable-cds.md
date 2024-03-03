---
layout: single
title: Java - enabling CDS steps
date: 2024-03-02 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - java
permalink: "2024/03/03/java-enable-cds"
---

Enable CDS steps.

### Manual steps

```
java -XX:DumpLoadedClassList=hello.classlist -jar hello HelloWorld
```

```
java -Xshare:dump -XX:SharedClassListFile=hello.classlist -XX:SharedArchiveFile=hello.jsa
```

```
java -Xshare:on -XX:SharedArchiveFile=hello.jsa hello HelloWorld
```

### Training steps

This will be available in JDK21

```
java -XXArchiveClassesAtExit=hello.jsa -jar hello HelloWorld
```

```
java -XX:SharedArchiveFile=hello.jsa hello HelloWorld
```

#### Auto generate
```
java -XX:+AutoCreateSharedArchive  -XX:SharedArchiveFile=hello.jsa -jar hello HelloWorld
```
