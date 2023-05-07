---
layout: single
title: Gradle - BOM project
date: 2023-05-07 08:00:00.000000000 -05:00
type: post
parent_id: "0"
published: true
password: ""
status: publish
categories:
  - gradle
permalink: "2023/05/07/gradle-bom-project"
---

Gradle supports BOM project to define all dependencies.

[Java Platform plugin](https://docs.gradle.org/current/userguide/java_platform_plugin.html#java_platform_plugin)

```groovy
plugins {
    id 'java-platform'
}

dependencies {
    constraints {
        api 'org.slf4j:slf4j-api:1.7.30'
        api 'org.slf4j:slf4j-simple:1.7.30'
        api 'junit:junit:4.12'

        runtime 'org.postgresql:postgresql:42.2.5'
    }
}
```

[Gradle BOM in Medium article](https://medium.com/mwm-io/generate-bill-of-material-bom-with-maven-publish-plugin-f30b44ab5436)